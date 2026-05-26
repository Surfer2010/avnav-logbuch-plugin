# AVNav Logbook Plugin
# Stores digital logbook events as JSONL and optionally writes to InfluxDB v2.
#
# Main goals:
# - create timestamped logbook entries
# - attach current AVNav navigation data
# - store robust local JSONL files
# - validate runtime states for motor, sail and anchor
# - keep optional InfluxDB output prepared

from __future__ import absolute_import

import json
import os
import time
import datetime
import threading
import traceback
import subprocess
import uuid

try:
    from avnav_api import AVNApi  # noqa: F401
except Exception:
    pass


class Plugin(object):
    LOG_STATUS = 'logbook.status'
    LOG_COUNT = 'logbook.count'
    LAST_EVENT = 'logbook.lastEvent'
    MOTOR_STATE = 'logbook.motor'
    SAIL_STATE = 'logbook.sail'
    ANCHOR_STATE = 'logbook.anchor'

    START_EVENTS = {
        'motor_on': 'motor',
        'sail_set': 'sail',
        'anchor_down': 'anchor',
    }

    END_EVENTS = {
        'motor_off': 'motor',
        'sail_down': 'sail',
        'anchor_up': 'anchor',
    }

    STATE_LABELS = {
        'motor': {
            'on': 'Motor läuft',
            'off': 'Motor aus',
            'start_event': 'motor_on',
            'end_event': 'motor_off',
        },
        'sail': {
            'on': 'Segel gesetzt',
            'off': 'Segel eingeholt',
            'start_event': 'sail_set',
            'end_event': 'sail_down',
        },
        'anchor': {
            'on': 'Anker ab',
            'off': 'Anker auf',
            'start_event': 'anchor_down',
            'end_event': 'anchor_up',
        },
    }

    @classmethod
    def pluginInfo(cls):
        return {
            'description': 'Digitales Logbuch mit Statusprüfung, Zeitstempel, GPS, SOG, COG, Heading und Freitext.',
            'data': [
                {'path': cls.LOG_STATUS, 'description': 'Logbook plugin status'},
                {'path': cls.LOG_COUNT, 'description': 'Number of logbook entries in current runtime'},
                {'path': cls.LAST_EVENT, 'description': 'Last logbook event type'},
                {'path': cls.MOTOR_STATE, 'description': 'Current motor state'},
                {'path': cls.SAIL_STATE, 'description': 'Current sail state'},
                {'path': cls.ANCHOR_STATE, 'description': 'Current anchor state'},
            ]
        }

    def __init__(self, api):
        self.api = api
        self.lock = threading.Lock()
        self.count = 0

        # Asynchrone Export-Jobs.
        # Key: job_id
        # Value: Statusinformationen zum laufenden oder abgeschlossenen Export.
        self.export_jobs = {}

        # Runtime state.
        # False bedeutet: aus / eingeholt / oben.
        # True bedeutet: an / gesetzt / unten.
        self.state = {
            'motor': False,
            'sail': False,
            'anchor': False,
        }

        self.base_dir = self._get_base_dir()
        self.log_dir = self._get_config('logDir', os.path.join(self.base_dir, 'logbook'))

        # Die Export-Tools werden durch tools/install_or_update.sh hier installiert.
        self.tools_dir = self._get_config('toolsDir', os.path.join(self.base_dir, 'logbook-tools'))

        # Testwerte für LXC ohne echtes GPS.
        self.test_lat = self._get_config('testLat', '')
        self.test_lon = self._get_config('testLon', '')
        self.test_sog = self._get_config('testSog', '')
        self.test_cog = self._get_config('testCog', '')
        self.test_heading = self._get_config('testHeading', '')

        self.influx_enabled = self._as_bool(self._get_config('influxEnabled', 'false'))
        self.influx_url = self._get_config('influxUrl', '')
        self.influx_org = self._get_config('influxOrg', '')
        self.influx_bucket = self._get_config('influxBucket', '')
        self.influx_token = self._get_config('influxToken', '')

        self.api.registerRequestHandler(self.handleApiRequest)

        if hasattr(self.api, 'registerRestart'):
            self.api.registerRestart(self.stop)

    def _get_config(self, name, default):
        try:
            value = self.api.getConfigValue(name)
            if value is None or value == '':
                return default
            return value
        except Exception:
            return default

    def _get_base_dir(self):
        try:
            return self.api.getDataDir()
        except Exception:
            return os.path.expanduser('~/avnav/data')

    def _as_bool(self, value):
        return str(value).strip().lower() in ('1', 'true', 'yes', 'on', 'ja')

    def stop(self):
        try:
            self.api.setStatus('Logbook', 'stopped')
        except Exception:
            pass

    def run(self):
        try:
            if not os.path.isdir(self.log_dir):
                os.makedirs(self.log_dir)

            self._rebuild_state_from_log()

            self.api.log('Logbook plugin started, log_dir=%s' % self.log_dir)
            self.api.setStatus('Logbook', 'running')
            self.api.addData(self.LOG_STATUS, 'running')
            self.api.addData(self.LOG_COUNT, self.count)
            self._publish_state()

        except Exception as e:
            self.api.error('Logbook plugin startup error: %s' % str(e))
            self.api.setStatus('Logbook', 'error')

            try:
                self.api.addData(self.LOG_STATUS, 'error')
            except Exception:
                pass

        while True:
            try:
                if hasattr(self.api, 'shouldStopMainThread') and self.api.shouldStopMainThread():
                    break
            except Exception:
                pass

            time.sleep(2)

    def _now_utc(self):
        return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + 'Z'

    def _today_file(self):
        day = datetime.datetime.utcnow().strftime('%Y-%m-%d')
        return os.path.join(self.log_dir, 'logbook-%s.jsonl' % day)

    def _to_float(self, value):
        try:
            if isinstance(value, dict) and 'value' in value:
                value = value.get('value')
            if value is None or value == '':
                return None
            return float(value)
        except Exception:
            return None

    def _get_single_value(self, keys):
        for key in keys:
            try:
                value = self.api.getSingleValue(key)
                value = self._to_float(value)

                if value is not None:
                    return value
            except Exception:
                pass

        return None

    def _get_navigation_data(self):
        lat = self._get_single_value(['gps.lat', 'gps.latitude', 'nav.gps.lat', 'navigation.position.latitude'])
        lon = self._get_single_value(['gps.lon', 'gps.longitude', 'nav.gps.lon', 'navigation.position.longitude'])
        sog = self._get_single_value(['gps.speed', 'nav.gps.speed', 'navigation.speedOverGround', 'navigation.speedThroughWater'])
        cog = self._get_single_value(['gps.track', 'nav.gps.track', 'navigation.courseOverGroundTrue', 'navigation.courseOverGroundMagnetic'])
        heading = self._get_single_value(['gps.heading', 'nav.gps.heading', 'navigation.headingTrue', 'navigation.headingMagnetic'])

        if lat is None:
            lat = self._to_float(self.test_lat)
        if lon is None:
            lon = self._to_float(self.test_lon)
        if sog is None:
            sog = self._to_float(self.test_sog)
        if cog is None:
            cog = self._to_float(self.test_cog)
        if heading is None:
            heading = self._to_float(self.test_heading)

        return {
            'lat': lat,
            'lon': lon,
            'sog': sog,
            'cog': cog,
            'heading': heading
        }

    def _sanitize_text(self, text):
        if text is None:
            return ''

        text = str(text)
        text = text.replace('\r', ' ').replace('\n', ' ').strip()

        if len(text) > 1000:
            text = text[:1000]

        return text

    def _build_entry(self, event_type, text, lat=None, lon=None):
        nav = self._get_navigation_data()

        if lat is not None:
            nav['lat'] = self._to_float(lat)

        if lon is not None:
            nav['lon'] = self._to_float(lon)

        return {
            'timestamp': self._now_utc(),
            'event_type': event_type or 'manual',
            'text': self._sanitize_text(text),
            'lat': nav.get('lat'),
            'lon': nav.get('lon'),
            'sog': nav.get('sog'),
            'cog': nav.get('cog'),
            'heading': nav.get('heading'),
            'state': dict(self.state),
            'source': 'avnav-logbook-plugin'
        }

    def _append_jsonl(self, entry):
        if not os.path.isdir(self.log_dir):
            os.makedirs(self.log_dir)

        path = self._today_file()
        line = json.dumps(entry, ensure_ascii=False, sort_keys=True)

        with open(path, 'a') as f:
            f.write(line)
            f.write('\n')

        return path

    def _read_today_entries(self):
        path = self._today_file()
        entries = []

        if not os.path.exists(path):
            return entries

        with open(path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    entries.append(json.loads(line))
                except Exception:
                    pass

        return entries

    def _rebuild_state_from_log(self):
        # Beim Neustart wird der aktuelle Status aus der heutigen JSONL-Datei rekonstruiert.
        self.state = {
            'motor': False,
            'sail': False,
            'anchor': False,
        }

        entries = self._read_today_entries()
        self.count = len(entries)

        for entry in entries:
            event_type = entry.get('event_type')

            if event_type in self.START_EVENTS:
                self.state[self.START_EVENTS[event_type]] = True

            if event_type in self.END_EVENTS:
                self.state[self.END_EVENTS[event_type]] = False

    def _publish_state(self):
        try:
            self.api.addData(self.MOTOR_STATE, 'on' if self.state['motor'] else 'off')
            self.api.addData(self.SAIL_STATE, 'on' if self.state['sail'] else 'off')
            self.api.addData(self.ANCHOR_STATE, 'on' if self.state['anchor'] else 'off')
        except Exception:
            pass

    def _validate_event(self, event_type):
        # Manuelle Einträge und Törn-Marker verändern keinen Zustand und sind immer erlaubt.
        if event_type in ('manual', 'trip_start', 'trip_end'):
            return True, ''

        # Start-Events dürfen nur ausgeführt werden, wenn der Zustand noch aus ist.
        if event_type in self.START_EVENTS:
            state_name = self.START_EVENTS[event_type]

            if self.state.get(state_name):
                return False, '%s ist bereits aktiv.' % self.STATE_LABELS[state_name]['on']

            return True, ''

        # End-Events dürfen nur ausgeführt werden, wenn der Zustand vorher aktiv ist.
        if event_type in self.END_EVENTS:
            state_name = self.END_EVENTS[event_type]

            if not self.state.get(state_name):
                return False, '%s ist bereits inaktiv.' % self.STATE_LABELS[state_name]['off']

            return True, ''

        # Unbekannte Eventtypen verhindern wir bewusst.
        return False, 'Unbekannter Eventtyp: %s' % event_type

    def _apply_event_to_state(self, event_type):
        if event_type in self.START_EVENTS:
            self.state[self.START_EVENTS[event_type]] = True

        if event_type in self.END_EVENTS:
            self.state[self.END_EVENTS[event_type]] = False

        self._publish_state()

    def _write_influx(self, entry):
        if not self.influx_enabled:
            return False, 'disabled'

        if not (self.influx_url and self.influx_org and self.influx_bucket and self.influx_token):
            return False, 'missing influx config'

        try:
            import urllib.parse
            import urllib.request

            measurement = 'avnav_logbook'
            event_type = str(entry.get('event_type') or 'manual').replace(' ', '_').replace(',', '_')

            fields = []

            for key in ['lat', 'lon', 'sog', 'cog', 'heading']:
                if entry.get(key) is not None:
                    fields.append('%s=%s' % (key, entry.get(key)))

            text = str(entry.get('text') or '').replace('\\', '\\\\').replace('"', '\\"')
            fields.append('text="%s"' % text)

            line = '%s,event_type=%s %s' % (measurement, event_type, ','.join(fields))

            url = self.influx_url.rstrip('/') + '/api/v2/write?' + urllib.parse.urlencode({
                'org': self.influx_org,
                'bucket': self.influx_bucket,
                'precision': 's'
            })

            req = urllib.request.Request(url, data=line.encode('utf-8'), method='POST')
            req.add_header('Authorization', 'Token %s' % self.influx_token)
            req.add_header('Content-Type', 'text/plain; charset=utf-8')

            urllib.request.urlopen(req, timeout=3).read()

            return True, 'ok'

        except Exception as e:
            return False, str(e)

    def _save_entry(self, event_type, text, lat=None, lon=None):
        valid, message = self._validate_event(event_type)

        if not valid:
            return {
                'status': 'ERROR',
                'message': message,
                'event_type': event_type,
                'state': dict(self.state)
            }

        entry = self._build_entry(event_type, text, lat, lon)

        with self.lock:
            self._apply_event_to_state(event_type)
            entry['state'] = dict(self.state)

            path = self._append_jsonl(entry)
            self.count += 1

            try:
                self.api.addData(self.LOG_COUNT, self.count)
                self.api.addData(self.LAST_EVENT, entry.get('event_type'))
            except Exception:
                pass

        influx_ok, influx_msg = self._write_influx(entry)

        return {
            'status': 'OK',
            'entry': entry,
            'file': path,
            'state': dict(self.state),
            'influx': {
                'enabled': self.influx_enabled,
                'ok': influx_ok,
                'message': influx_msg
            }
        }

    def _compact_date(self, value):
        # Akzeptiert YYYY-MM-DD oder YYYYMMDD und gibt YYYYMMDD zurück.
        value = str(value or '').strip()

        if value == '':
            value = datetime.datetime.utcnow().strftime('%Y-%m-%d')

        if len(value) == 8 and value.isdigit():
            return value

        return datetime.datetime.strptime(value, '%Y-%m-%d').strftime('%Y%m%d')

    def _dash_date(self, value):
        # Akzeptiert YYYY-MM-DD oder YYYYMMDD und gibt YYYY-MM-DD zurück.
        value = str(value or '').strip()

        if value == '':
            value = datetime.datetime.utcnow().strftime('%Y-%m-%d')

        if len(value) == 8 and value.isdigit():
            return datetime.datetime.strptime(value, '%Y%m%d').strftime('%Y-%m-%d')

        datetime.datetime.strptime(value, '%Y-%m-%d')
        return value

    def _start_export_job(self, job_type, command, output_file):
        # Export-Jobs laufen bewusst asynchron, damit AVNav/WebUI nicht blockiert.
        job_id = str(uuid.uuid4())

        job = {
            'id': job_id,
            'type': job_type,
            'status': 'RUNNING',
            'started': self._now_utc(),
            'finished': None,
            'command': command,
            'outputFile': output_file,
            'returnCode': None,
            'stdout': '',
            'stderr': '',
            'message': ''
        }

        self.export_jobs[job_id] = job

        thread = threading.Thread(
            target=self._run_export_job,
            args=(job_id,),
        )

        thread.daemon = True
        thread.start()

        return job

    def _run_export_job(self, job_id):
        job = self.export_jobs.get(job_id)

        if job is None:
            return

        try:
            self.api.log('Logbook export job started: %s' % job_id)

            proc = subprocess.Popen(
                job['command'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.tools_dir,
            )

            stdout, stderr = proc.communicate()

            job['returnCode'] = proc.returncode
            job['stdout'] = stdout.decode('utf-8', 'replace')
            job['stderr'] = stderr.decode('utf-8', 'replace')
            job['finished'] = self._now_utc()

            if proc.returncode == 0:
                job['status'] = 'OK'
                job['message'] = 'Export fertig.'
            else:
                job['status'] = 'ERROR'

                if 'No logbook file found' in job['stderr']:
                    job['message'] = 'Keine Logbucheinträge für diesen Tag.'
                elif 'GPX file not found' in job['stderr']:
                    job['message'] = 'Keine GPX-Trackdatei für diesen Tag.'
                else:
                    job['message'] = 'Export fehlgeschlagen.'

            self.api.log('Logbook export job finished: %s status=%s' % (job_id, job['status']))

        except Exception as e:
            job['status'] = 'ERROR'
            job['message'] = str(e)
            job['stderr'] = traceback.format_exc()
            job['finished'] = self._now_utc()

            try:
                self.api.error('Logbook export job error: %s\n%s' % (str(e), traceback.format_exc()))
            except Exception:
                pass

    def _export_kmz_async(self, date_value):
        date_dash = self._dash_date(date_value)
        date_compact = self._compact_date(date_value)

        script = os.path.join(self.tools_dir, 'export_additional_kmz.py')
        output_file = os.path.join(self.base_dir, 'overlays', '%s_logbuch.kmz' % date_compact)

        if not os.path.exists(script):
            return {
                'status': 'ERROR',
                'message': 'Export script not found: %s' % script
            }

        command = [
            'python3',
            script,
            '--date',
            date_dash,
            '--avnav-data',
            self.base_dir
        ]

        job = self._start_export_job('daily-kmz', command, output_file)

        return {
            'status': 'OK',
            'message': 'KMZ export started.',
            'job': job
        }

    def _export_trip_kmz_async(self, from_date, to_date):
        from_dash = self._dash_date(from_date)
        to_dash = self._dash_date(to_date)

        from_compact = self._compact_date(from_date)
        to_compact = self._compact_date(to_date)

        script = os.path.join(self.tools_dir, 'export_trip_kmz.py')
        output_file = os.path.join(self.base_dir, 'overlays', '%s-%s_toern_logbuch.kmz' % (from_compact, to_compact))

        if not os.path.exists(script):
            return {
                'status': 'ERROR',
                'message': 'Export script not found: %s' % script
            }

        command = [
            'python3',
            script,
            '--from-date',
            from_dash,
            '--to-date',
            to_dash,
            '--avnav-data',
            self.base_dir
        ]

        job = self._start_export_job('trip-kmz', command, output_file)

        return {
            'status': 'OK',
            'message': 'Trip KMZ export started.',
            'job': job
        }

    def _parse_logbook_timestamp(self, value):
        try:
            if not value:
                return None

            return datetime.datetime.strptime(
                str(value).replace('Z', ''),
                '%Y-%m-%dT%H:%M:%S'
            )
        except Exception:
            return None

    def _read_trip_marker_events(self):
        markers = []

        try:
            files = []

            if os.path.isdir(self.log_dir):
                for name in os.listdir(self.log_dir):
                    if name.endswith('.jsonl'):
                        files.append(os.path.join(self.log_dir, name))

            files.sort()

            for path in files:
                try:
                    with open(path, 'r') as f:
                        for line in f:
                            line = line.strip()

                            if not line:
                                continue

                            try:
                                entry = json.loads(line)
                            except Exception:
                                continue

                            event_type = entry.get('event_type')

                            if event_type not in ('trip_start', 'trip_end'):
                                continue

                            timestamp = self._parse_logbook_timestamp(
                                entry.get('timestamp')
                            )

                            if timestamp is None:
                                continue

                            markers.append({
                                'timestamp': timestamp,
                                'timestampText': entry.get('timestamp'),
                                'event_type': event_type,
                                'entry': entry,
                                'file': path
                            })

                except Exception:
                    pass

            markers.sort(key=lambda item: item['timestamp'])
            return markers

        except Exception:
            return []

    def _find_current_trip_range(self):
        markers = self._read_trip_marker_events()

        last_start = None

        for marker in markers:
            if marker.get('event_type') == 'trip_start':
                last_start = marker

        if last_start is None:
            return None, None, 'Kein Törn Start gefunden.'

        end_marker = None

        for marker in markers:
            if (
                marker.get('event_type') == 'trip_end'
                and marker.get('timestamp') >= last_start.get('timestamp')
            ):
                end_marker = marker
                break

        from_date = last_start['timestamp'].strftime('%Y-%m-%d')

        if end_marker is not None:
            to_date = end_marker['timestamp'].strftime('%Y-%m-%d')
            message = 'Törn Start bis Törn Ende.'
        else:
            to_date = datetime.datetime.utcnow().strftime('%Y-%m-%d')
            message = 'Törn Start bis heute.'

        return from_date, to_date, message

    def _export_current_trip_kmz_async(self):
        from_date, to_date, message = self._find_current_trip_range()

        if not from_date or not to_date:
            return {
                'status': 'ERROR',
                'message': message
            }

        result = self._export_trip_kmz_async(from_date, to_date)

        if result.get('status') == 'OK':
            result['message'] = message
            result['from'] = from_date
            result['to'] = to_date

        return result

    def _export_status(self, job_id=None):
        if job_id:
            job = self.export_jobs.get(job_id)

            if job is None:
                return {
                    'status': 'ERROR',
                    'message': 'unknown job id: %s' % job_id
                }

            return {
                'status': 'OK',
                'job': job
            }

        jobs = list(self.export_jobs.values())
        jobs.sort(key=lambda item: item.get('started') or '', reverse=True)

        return {
            'status': 'OK',
            'jobs': jobs[:20]
        }

    def _get_arg(self, args, name, default=None):
        if args is None:
            return default

        value = args.get(name, default)

        if isinstance(value, list):
            return value[0] if len(value) else default

        return value

    def _list_entries(self, limit):
        entries = self._read_today_entries()
        return {
            'status': 'OK',
            'file': self._today_file(),
            'entries': entries[-limit:],
            'state': dict(self.state)
        }

    def handleApiRequest(self, url, handler, args):
        try:
            if url in ('add', 'api/add'):
                event_type = self._get_arg(args, 'event_type', self._get_arg(args, 'type', 'manual'))
                text = self._get_arg(args, 'text', '')
                lat = self._get_arg(args, 'lat', None)
                lon = self._get_arg(args, 'lon', None)

                return self._save_entry(event_type, text, lat, lon)

            if url in ('status', 'api/status'):
                return {
                    'status': 'OK',
                    'count': self.count,
                    'logDir': self.log_dir,
                    'influxEnabled': self.influx_enabled,
                    'state': dict(self.state),
                    'testLat': self.test_lat,
                    'testLon': self.test_lon
                }

            if url in ('list', 'api/list'):
                limit = int(self._get_arg(args, 'limit', 50))
                return self._list_entries(limit)

            if url in ('exportKmz', 'api/exportKmz'):
                date_value = self._get_arg(args, 'date', '')
                return self._export_kmz_async(date_value)

            if url in ('exportTripKmz', 'api/exportTripKmz'):
                from_date = self._get_arg(args, 'from', self._get_arg(args, 'fromDate', ''))
                to_date = self._get_arg(args, 'to', self._get_arg(args, 'toDate', ''))

                if not from_date or not to_date:
                    return {
                        'status': 'ERROR',
                        'message': 'from/to date required'
                    }

                return self._export_trip_kmz_async(from_date, to_date)

            if url in ('exportCurrentTripKmz', 'api/exportCurrentTripKmz'):
                return self._export_current_trip_kmz_async()

            if url in ('exportStatus', 'api/exportStatus'):
                job_id = self._get_arg(args, 'job', self._get_arg(args, 'jobId', None))
                return self._export_status(job_id)


            return {
                'status': 'ERROR',
                'message': 'unknown request: %s' % url
            }

        except Exception as e:
            self.api.error('Logbook API error: %s\n%s' % (str(e), traceback.format_exc()))

            return {
                'status': 'ERROR',
                'message': str(e)
            }
