# AVNav Logbuch Plugin
# Stores digital logbuch events as JSONL and optionally writes to InfluxDB v2.
#
# Main goals:
# - create timestamped logbuch entries
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
    LOG_STATUS = 'logbuch.status'
    LOG_COUNT = 'logbuch.count'
    LAST_EVENT = 'logbuch.lastEvent'
    MOTOR_STATE = 'logbuch.motor'
    SAIL_STATE = 'logbuch.sail'
    ANCHOR_STATE = 'logbuch.anchor'

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
                {'path': cls.LOG_STATUS, 'description': 'Logbuch plugin status'},
                {'path': cls.LOG_COUNT, 'description': 'Number of logbuch entries in current runtime'},
                {'path': cls.LAST_EVENT, 'description': 'Last logbuch event type'},
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
        self.log_dir = self._get_config(
            'logDir',
            os.path.join(self.base_dir, 'logbuch')
        )
        self.track_dir = self._get_config(
            'trackDir',
            os.path.join(self.base_dir, 'tracks')
        )

        # Die Export-Tools werden durch tools/install_or_update.sh hier installiert.
        self.tools_dir = self._get_config('toolsDir', os.path.join(self.base_dir, 'logbuch-tools'))

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

        # Register editable parameters with AVNav.
        # Even with an empty parameter list this enables runtime
        # enable/disable support and prepares future configuration options.
        if hasattr(self.api, 'registerEditableParameters'):
            self.api.registerEditableParameters([], self._editable_parameters_changed)


    def _list_logbook_days(self):
        """Listet vorhandene Logbuchtage, neuester Tag zuerst."""
        days = []

        try:
            filenames = os.listdir(self.log_dir)
        except OSError:
            return days

        prefix = 'logbuch-'
        suffix = '.jsonl'

        for filename in filenames:
            if not filename.startswith(prefix) or not filename.endswith(suffix):
                continue

            date_value = filename[len(prefix):-len(suffix)]

            try:
                datetime.datetime.strptime(date_value, '%Y-%m-%d')
            except ValueError:
                continue

            path = os.path.join(self.log_dir, filename)
            count = 0

            try:
                with open(path, 'r', encoding='utf-8') as handle:
                    for line in handle:
                        if line.strip():
                            count += 1
            except (OSError, UnicodeError):
                continue

            parsed_date = datetime.datetime.strptime(
                date_value,
                '%Y-%m-%d'
            ).date()

            today = datetime.datetime.now().date()
            yesterday = today - datetime.timedelta(days=1)

            weekday_names = (
                'Mo',
                'Di',
                'Mi',
                'Do',
                'Fr',
                'Sa',
                'So',
            )

            if parsed_date == today:
                title = 'Heute'
                weekday = ''
            elif parsed_date == yesterday:
                title = 'Gestern'
                weekday = ''
            else:
                title = parsed_date.strftime('%d.%m.%Y')
                weekday = weekday_names[parsed_date.weekday()]

            days.append({
                'date': date_value,
                'count': count,
                'title': title,
                'weekday': weekday
            })

        days.sort(key=lambda item: item['date'], reverse=True)
        return days

    def _read_logbook_day(self, date_value):
        """Liest die JSONL-Einträge eines bestimmten Tages."""
        try:
            datetime.datetime.strptime(date_value, '%Y-%m-%d')
        except (TypeError, ValueError):
            return []

        path = os.path.join(
            self.log_dir,
            'logbuch-%s.jsonl' % date_value
        )

        entries = []

        try:
            with open(path, 'r', encoding='utf-8') as handle:
                for line in handle:
                    line = line.strip()

                    if not line:
                        continue

                    try:
                        entries.append(json.loads(line))
                    except (TypeError, ValueError):
                        continue
        except OSError:
            return []

        return entries

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

    def _editable_parameters_changed(self, new_params):
        try:
            self.api.log("Editable parameters changed: %s" % str(new_params))
        except Exception:
            pass

    def stop(self):
        try:
            self.api.setStatus('Logbook', 'stopped')
        except Exception:
            pass

    def run(self):
        try:
            if not os.path.isdir(self.log_dir):
                os.makedirs(self.log_dir)

            if hasattr(self.api, "registerUserApp"):
                app_url = self.api.getBaseUrl() + "/index.html"
                app_icon = os.path.join("icons", "logbook.svg")

                try:
                    self.api.registerUserApp(
                        app_url,
                        app_icon,
                        title="Logbuch",
                        name="logbuch-view",
                        shortText="Logbuch",
                        longText="Digitales Logbuch",
                    )
                except TypeError:
                    self.api.registerUserApp(
                        app_url,
                        app_icon,
                        "Logbuch",
                    )

            self._rebuild_state_from_log()

            self.api.log('Logbuch plugin started, log_dir=%s' % self.log_dir)
            self.api.setStatus('Logbook', 'running')
            self.api.addData(self.LOG_STATUS, 'running')
            self.api.addData(self.LOG_COUNT, self.count)
            self._publish_state()

        except Exception as e:
            self.api.error('Logbuch plugin startup error: %s' % str(e))
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

    def _normalize_timestamp(self, value=None):
        # Ohne übergebenen Wert wird der aktuelle UTC-Zeitstempel verwendet.
        if value is None or str(value).strip() == '':
            return self._now_utc()

        value = str(value).strip()

        try:
            if value.endswith('Z'):
                parsed = datetime.datetime.strptime(
                    value,
                    '%Y-%m-%dT%H:%M:%SZ'
                )
                parsed = parsed.replace(tzinfo=datetime.timezone.utc)
            else:
                parsed = datetime.datetime.fromisoformat(value)

                # Zeitstempel ohne Zeitzone werden als UTC behandelt.
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=datetime.timezone.utc)

            parsed = parsed.astimezone(datetime.timezone.utc)

            return (
                parsed.replace(tzinfo=None, microsecond=0).isoformat()
                + 'Z'
            )

        except (TypeError, ValueError):
            raise ValueError(
                'invalid timestamp format, expected ISO 8601'
            )

    def _log_file(self, timestamp=None):
        normalized = self._normalize_timestamp(timestamp)
        day = normalized[:10]

        return os.path.join(
            self.log_dir,
            'logbuch-%s.jsonl' % day
        )

    def _today_file(self):
        return self._log_file()

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

    def _timestamp_datetime(self, value):
        normalized = self._normalize_timestamp(value)

        return datetime.datetime.strptime(
            normalized,
            '%Y-%m-%dT%H:%M:%SZ'
        ).replace(tzinfo=datetime.timezone.utc)

    def _read_avt_points(self, timestamp):
        normalized = self._normalize_timestamp(timestamp)
        path = os.path.join(
            self.track_dir,
            normalized[:10] + '.avt'
        )

        points = []

        if not os.path.exists(path):
            return points, path

        try:
            with open(path, 'r', encoding='utf-8') as handle:
                for line in handle:
                    line = line.strip()

                    if not line or line.startswith('#'):
                        continue

                    parts = line.split(',')

                    if len(parts) < 5:
                        continue

                    try:
                        point_time = self._timestamp_datetime(parts[0])
                        point = {
                            'timestamp': point_time,
                            'lat': float(parts[1]),
                            'lon': float(parts[2]),
                            'cog': float(parts[3]),
                            'sog': float(parts[4]),
                        }

                        if len(parts) > 5:
                            point['distance'] = self._to_float(parts[5])

                        points.append(point)
                    except (TypeError, ValueError):
                        continue
        except OSError:
            return [], path

        points.sort(key=lambda item: item['timestamp'])
        return points, path

    def _interpolate_angle(self, first, second, fraction):
        if first is None or second is None:
            return first if fraction < 0.5 else second

        difference = ((second - first + 180.0) % 360.0) - 180.0
        return (first + difference * fraction) % 360.0

    def _resolve_track_position(self, timestamp):
        target = self._timestamp_datetime(timestamp)
        points, path = self._read_avt_points(timestamp)

        unknown = {
            'lat': None,
            'lon': None,
            'sog': None,
            'cog': None,
            'heading': None,
            'position_source': 'unknown',
            'track_file': path,
            'track_time_distance': None,
        }

        if not points:
            return unknown

        previous = None
        following = None

        for point in points:
            if point['timestamp'] == target:
                return {
                    'lat': point.get('lat'),
                    'lon': point.get('lon'),
                    'sog': point.get('sog'),
                    'cog': point.get('cog'),
                    'heading': None,
                    'position_source': 'avt_exact',
                    'track_file': path,
                    'track_time_distance': 0,
                }

            if point['timestamp'] < target:
                previous = point
                continue

            following = point
            break

        if previous is not None and following is not None:
            total_seconds = (
                following['timestamp'] - previous['timestamp']
            ).total_seconds()

            if 0 < total_seconds <= 1800:
                elapsed_seconds = (
                    target - previous['timestamp']
                ).total_seconds()

                fraction = elapsed_seconds / total_seconds

                return {
                    'lat': previous['lat']
                           + (following['lat'] - previous['lat']) * fraction,
                    'lon': previous['lon']
                           + (following['lon'] - previous['lon']) * fraction,
                    'sog': previous.get('sog')
                           + (
                               following.get('sog') - previous.get('sog')
                           ) * fraction
                           if previous.get('sog') is not None
                           and following.get('sog') is not None
                           else None,
                    'cog': self._interpolate_angle(
                        previous.get('cog'),
                        following.get('cog'),
                        fraction
                    ),
                    'heading': None,
                    'position_source': 'avt_interpolated',
                    'track_file': path,
                    'track_time_distance': int(
                        min(elapsed_seconds, total_seconds - elapsed_seconds)
                    ),
                }

        candidates = [
            point for point in (previous, following)
            if point is not None
        ]

        if candidates:
            nearest = min(
                candidates,
                key=lambda point: abs(
                    (point['timestamp'] - target).total_seconds()
                )
            )
            distance = abs(
                (nearest['timestamp'] - target).total_seconds()
            )

            if distance <= 900:
                return {
                    'lat': nearest.get('lat'),
                    'lon': nearest.get('lon'),
                    'sog': nearest.get('sog'),
                    'cog': nearest.get('cog'),
                    'heading': None,
                    'position_source': 'avt_nearest',
                    'track_file': path,
                    'track_time_distance': int(distance),
                }

        return unknown

    def _apply_track_position(self, entry):
        position = self._resolve_track_position(entry.get('timestamp'))

        entry['lat'] = position.get('lat')
        entry['lon'] = position.get('lon')
        entry['sog'] = position.get('sog')
        entry['cog'] = position.get('cog')
        entry['heading'] = position.get('heading')
        entry['position_source'] = position.get(
            'position_source',
            'unknown'
        )

        details = dict(entry.get('details') or {})
        details['track_file'] = position.get('track_file')
        details['track_time_distance'] = position.get(
            'track_time_distance'
        )
        entry['details'] = details

        return entry

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

    def _build_entry(
        self,
        event_type,
        text,
        lat=None,
        lon=None,
        timestamp=None
    ):
        nav = self._get_navigation_data()

        if lat is not None:
            nav['lat'] = self._to_float(lat)

        if lon is not None:
            nav['lon'] = self._to_float(lon)

        return {
            'schema_version': 1,
            'id': str(uuid.uuid4()),
            'timestamp': self._normalize_timestamp(timestamp),
            'event_type': event_type or 'manual',
            'text': self._sanitize_text(text),
            'lat': nav.get('lat'),
            'lon': nav.get('lon'),
            'position_source': 'live' if nav.get('lat') is not None and nav.get('lon') is not None else 'unknown',
            'sog': nav.get('sog'),
            'cog': nav.get('cog'),
            'heading': nav.get('heading'),
            'state': dict(self.state),
            'details': {},
            'source': 'avnav-logbuch-plugin'
        }

    def _normalize_entry(self, entry):
        if not isinstance(entry, dict):
            return None

        normalized = dict(entry)

        normalized.setdefault('schema_version', 0)
        normalized.setdefault('event_type', 'manual')
        normalized['text'] = self._sanitize_text(normalized.get('text'))
        normalized.setdefault('state', {})
        normalized.setdefault('details', {})
        normalized.setdefault('source', 'unknown')

        if not isinstance(normalized.get('state'), dict):
            normalized['state'] = {}

        if not isinstance(normalized.get('details'), dict):
            normalized['details'] = {}

        if not normalized.get('position_source'):
            if normalized.get('lat') is not None and normalized.get('lon') is not None:
                normalized['position_source'] = 'live'
            else:
                normalized['position_source'] = 'unknown'

        if not normalized.get('id'):
            seed = json.dumps(
                normalized,
                ensure_ascii=False,
                sort_keys=True,
                separators=(',', ':'),
                default=str
            )
            normalized['id'] = str(
                uuid.uuid5(uuid.NAMESPACE_URL, 'avnav-logbuch:' + seed)
            )

        return normalized

    def _entry_sort_key(self, entry):
        """Erzeugt einen stabilen chronologischen Sortierschlüssel."""
        timestamp = str(entry.get('timestamp') or '')
        entry_id = str(entry.get('id') or '')
        return timestamp, entry_id

    def _load_all_entries(self):
        """Lädt alle gültigen Logbucheinträge chronologisch sortiert."""
        entries = []

        if not os.path.isdir(self.log_dir):
            return entries

        prefix = 'logbuch-'
        suffix = '.jsonl'

        for filename in sorted(os.listdir(self.log_dir)):
            if not filename.startswith(prefix) or not filename.endswith(suffix):
                continue

            date_value = filename[len(prefix):-len(suffix)]

            try:
                datetime.datetime.strptime(date_value, '%Y-%m-%d')
            except (TypeError, ValueError):
                continue

            path = os.path.join(self.log_dir, filename)

            try:
                with open(path, 'r', encoding='utf-8') as handle:
                    for line_number, line in enumerate(handle, 1):
                        line = line.strip()

                        if not line:
                            continue

                        try:
                            entry = self._normalize_entry(json.loads(line))
                        except Exception as error:
                            try:
                                self.api.error(
                                    'Invalid logbook entry in %s line %s: %s'
                                    % (path, line_number, str(error))
                                )
                            except Exception:
                                pass
                            continue

                        if entry is not None:
                            entries.append(entry)

            except (OSError, UnicodeError) as error:
                try:
                    self.api.error(
                        'Unable to read logbook file %s: %s'
                        % (path, str(error))
                    )
                except Exception:
                    pass

        entries.sort(key=self._entry_sort_key)
        return entries

    def _entry_date(self, entry):
        """Bestimmt den Dateinamen-Tag eines Eintrags aus seinem Zeitstempel."""
        timestamp = self._normalize_timestamp(entry.get('timestamp'))
        return timestamp[:10]

    def _save_all_entries(self, entries):
        """
        Schreibt die vollständige Historie neu.

        Die Einträge werden chronologisch sortiert, nach Tagen gruppiert und
        zunächst in temporäre Dateien geschrieben. Erst danach werden die
        bisherigen Tagesdateien ersetzt.
        """
        if not os.path.isdir(self.log_dir):
            os.makedirs(self.log_dir)

        normalized_entries = []

        for entry in entries:
            normalized = self._normalize_entry(entry)

            if normalized is None:
                continue

            normalized['timestamp'] = self._normalize_timestamp(
                normalized.get('timestamp')
            )
            normalized_entries.append(normalized)

        normalized_entries.sort(key=self._entry_sort_key)

        grouped = {}

        for entry in normalized_entries:
            date_value = self._entry_date(entry)
            grouped.setdefault(date_value, []).append(entry)

        prefix = 'logbuch-'
        suffix = '.jsonl'
        existing_paths = []

        for filename in os.listdir(self.log_dir):
            if not filename.startswith(prefix) or not filename.endswith(suffix):
                continue

            date_value = filename[len(prefix):-len(suffix)]

            try:
                datetime.datetime.strptime(date_value, '%Y-%m-%d')
            except (TypeError, ValueError):
                continue

            existing_paths.append(os.path.join(self.log_dir, filename))

        temporary_paths = {}
        written_paths = []

        try:
            for date_value, day_entries in grouped.items():
                final_path = os.path.join(
                    self.log_dir,
                    'logbuch-%s.jsonl' % date_value
                )
                temporary_path = final_path + '.tmp'

                with open(temporary_path, 'w', encoding='utf-8') as handle:
                    for entry in day_entries:
                        handle.write(
                            json.dumps(
                                entry,
                                ensure_ascii=False,
                                sort_keys=True
                            )
                        )
                        handle.write('\n')

                    handle.flush()
                    os.fsync(handle.fileno())

                temporary_paths[final_path] = temporary_path

            for final_path, temporary_path in temporary_paths.items():
                os.replace(temporary_path, final_path)
                written_paths.append(final_path)

            written_set = set(written_paths)

            for old_path in existing_paths:
                if old_path not in written_set and os.path.exists(old_path):
                    os.unlink(old_path)

        except Exception:
            for temporary_path in temporary_paths.values():
                try:
                    if os.path.exists(temporary_path):
                        os.unlink(temporary_path)
                except Exception:
                    pass
            raise

        return {
            'entries': normalized_entries,
            'files': sorted(written_paths)
        }

    def _empty_state(self):
        return {
            'motor': False,
            'sail': False,
            'anchor': False,
        }

    def _known_event_types(self):
        return set(
            ['manual', 'trip_start', 'trip_end']
            + list(self.START_EVENTS.keys())
            + list(self.END_EVENTS.keys())
        )

    def _find_entry(self, entry_id, entries=None):
        """Sucht einen Eintrag anhand seiner stabilen ID."""
        entry_id = str(entry_id or '').strip()

        if not entry_id:
            return None, None

        if entries is None:
            entries = self._load_all_entries()

        for index, entry in enumerate(entries):
            if str(entry.get('id') or '') == entry_id:
                return index, entry

        return None, None

    def _warning_signature(self, warning):
        return (
            str(warning.get('entry_id') or ''),
            str(warning.get('code') or ''),
            str(warning.get('state_name') or ''),
            str(warning.get('event_type') or ''),
        )

    def _new_history_warnings(self, before, after):
        """
        Liefert nur Warnungen, die durch eine Aenderung neu entstanden sind.

        Bereits vorhandene Inkonsistenzen in alten Logbuchdateien blockieren
        dadurch keine neuen Eintraege oder Korrekturen.
        """
        before_signatures = set(
            self._warning_signature(item)
            for item in before
        )

        return [
            item for item in after
            if self._warning_signature(item) not in before_signatures
        ]

    def _validate_history(self, entries):
        """
        Prueft die chronologische Ereignishistorie.

        Inkonsistenzen werden als Warnungen zurueckgegeben. Die Funktion
        veraendert weder Eintraege noch Dateien.
        """
        warnings = []
        state = self._empty_state()
        seen_ids = set()

        normalized_entries = []

        for raw_entry in entries:
            entry = self._normalize_entry(raw_entry)

            if entry is None:
                continue

            try:
                entry['timestamp'] = self._normalize_timestamp(
                    entry.get('timestamp')
                )
            except ValueError:
                warnings.append({
                    'code': 'invalid_timestamp',
                    'entry_id': str(entry.get('id') or ''),
                    'timestamp': entry.get('timestamp'),
                    'event_type': entry.get('event_type'),
                    'message': 'Ungueltiger Zeitstempel.',
                })
                continue

            normalized_entries.append(entry)

        normalized_entries.sort(key=self._entry_sort_key)

        for entry in normalized_entries:
            entry_id = str(entry.get('id') or '')
            event_type = str(entry.get('event_type') or 'manual')
            timestamp = entry.get('timestamp')

            if entry_id in seen_ids:
                warnings.append({
                    'code': 'duplicate_id',
                    'entry_id': entry_id,
                    'timestamp': timestamp,
                    'event_type': event_type,
                    'message': 'Doppelte Eintrags-ID: %s' % entry_id,
                })
            else:
                seen_ids.add(entry_id)

            if event_type not in self._known_event_types():
                warnings.append({
                    'code': 'unknown_event_type',
                    'entry_id': entry_id,
                    'timestamp': timestamp,
                    'event_type': event_type,
                    'message': 'Unbekannter Eventtyp: %s' % event_type,
                })
                continue

            if event_type in self.START_EVENTS:
                state_name = self.START_EVENTS[event_type]

                if state.get(state_name):
                    warnings.append({
                        'code': 'duplicate_start',
                        'entry_id': entry_id,
                        'timestamp': timestamp,
                        'event_type': event_type,
                        'state_name': state_name,
                        'message': '%s ist zu diesem Zeitpunkt bereits aktiv.'
                                   % self.STATE_LABELS[state_name]['on'],
                    })

                state[state_name] = True

            elif event_type in self.END_EVENTS:
                state_name = self.END_EVENTS[event_type]

                if not state.get(state_name):
                    warnings.append({
                        'code': 'end_without_start',
                        'entry_id': entry_id,
                        'timestamp': timestamp,
                        'event_type': event_type,
                        'state_name': state_name,
                        'message': '%s ist zu diesem Zeitpunkt bereits inaktiv.'
                                   % self.STATE_LABELS[state_name]['off'],
                    })

                state[state_name] = False

        return warnings

    def _recalculate_states(self, entries):
        """
        Sortiert die Historie und berechnet fuer jeden Eintrag den Zustand
        nach Anwendung dieses Ereignisses neu.
        """
        normalized_entries = []

        for raw_entry in entries:
            entry = self._normalize_entry(raw_entry)

            if entry is None:
                continue

            entry['timestamp'] = self._normalize_timestamp(
                entry.get('timestamp')
            )
            normalized_entries.append(entry)

        normalized_entries.sort(key=self._entry_sort_key)

        state = self._empty_state()

        for entry in normalized_entries:
            event_type = entry.get('event_type')

            if event_type in self.START_EVENTS:
                state[self.START_EVENTS[event_type]] = True

            elif event_type in self.END_EVENTS:
                state[self.END_EVENTS[event_type]] = False

            entry['state'] = dict(state)

        return normalized_entries

    def _refresh_runtime_state(self, entries=None):
        """
        Aktualisiert den im Plugin veroeffentlichten Zustand aus der gesamten
        Historie. Der Zustand wird nicht mehr am UTC-Tageswechsel zurueckgesetzt.
        """
        if entries is None:
            entries = self._load_all_entries()

        entries = self._recalculate_states(entries)

        if entries:
            self.state = dict(entries[-1].get('state') or self._empty_state())
        else:
            self.state = self._empty_state()

        today = datetime.datetime.utcnow().strftime('%Y-%m-%d')

        self.count = sum(
            1 for entry in entries
            if str(entry.get('timestamp') or '').startswith(today)
        )

        self._publish_state()

        try:
            self.api.addData(self.LOG_COUNT, self.count)

            if entries:
                self.api.addData(
                    self.LAST_EVENT,
                    entries[-1].get('event_type')
                )
        except Exception:
            pass

        return entries

    def _save_history_change(
        self,
        old_entries,
        new_entries,
        force=False
    ):
        """
        Validiert, berechnet und speichert eine geaenderte Historie.
        """
        old_warnings = self._validate_history(old_entries)
        new_warnings = self._validate_history(new_entries)
        introduced_warnings = self._new_history_warnings(
            old_warnings,
            new_warnings
        )

        hard_warnings = [
            warning for warning in introduced_warnings
            if warning.get('code') in (
                'unknown_event_type',
                'invalid_timestamp',
                'duplicate_id',
            )
        ]

        if hard_warnings:
            return {
                'status': 'ERROR',
                'message': hard_warnings[0].get('message'),
                'warnings': hard_warnings,
                'requires_force': False,
            }

        if introduced_warnings and not force:
            return {
                'status': 'WARNING',
                'message': introduced_warnings[0].get('message'),
                'warnings': introduced_warnings,
                'requires_force': True,
            }

        recalculated = self._recalculate_states(new_entries)
        save_result = self._save_all_entries(recalculated)
        self._refresh_runtime_state(recalculated)

        return {
            'status': 'OK',
            'entries': recalculated,
            'files': save_result.get('files', []),
            'warnings': introduced_warnings,
            'all_warnings': new_warnings,
            'state': dict(self.state),
        }

    def _update_entry(
        self,
        entry_id,
        event_type=None,
        text=None,
        timestamp=None,
        lat=None,
        lon=None,
        force=False
    ):
        with self.lock:
            entries = self._load_all_entries()
            index, original = self._find_entry(entry_id, entries)

            if original is None:
                return {
                    'status': 'ERROR',
                    'message': 'Eintrag nicht gefunden: %s' % entry_id,
                }

            updated = dict(original)

            if event_type is not None:
                event_type = str(event_type).strip() or 'manual'

                if event_type not in self._known_event_types():
                    return {
                        'status': 'ERROR',
                        'message': 'Unbekannter Eventtyp: %s' % event_type,
                    }

                updated['event_type'] = event_type

            if text is not None:
                updated['text'] = self._sanitize_text(text)

            timestamp_changed = False

            if timestamp is not None:
                try:
                    normalized_timestamp = self._normalize_timestamp(timestamp)
                    timestamp_changed = (
                        normalized_timestamp
                        != self._normalize_timestamp(
                            original.get('timestamp')
                        )
                    )
                    updated['timestamp'] = normalized_timestamp
                except ValueError as error:
                    return {
                        'status': 'ERROR',
                        'message': str(error),
                    }

            if lat is not None:
                updated['lat'] = self._to_float(lat)

            if lon is not None:
                updated['lon'] = self._to_float(lon)

            if updated.get('lat') is not None and updated.get('lon') is not None:
                if lat is not None or lon is not None:
                    updated['position_source'] = 'manual'
            elif lat is not None or lon is not None:
                updated['position_source'] = 'unknown'

            if timestamp_changed and lat is None and lon is None:
                updated = self._apply_track_position(updated)

            updated = self._normalize_entry(updated)
            entries[index] = updated

            result = self._save_history_change(
                self._load_all_entries(),
                entries,
                force=force
            )

            if result.get('status') != 'OK':
                result['entry'] = updated
                return result

            _, saved_entry = self._find_entry(entry_id, result['entries'])

            return {
                'status': 'OK',
                'message': 'Eintrag aktualisiert.',
                'entry': saved_entry,
                'warnings': result.get('warnings', []),
                'all_warnings': result.get('all_warnings', []),
                'state': dict(self.state),
                'files': result.get('files', []),
            }

    def _delete_entry(self, entry_id, force=False):
        with self.lock:
            old_entries = self._load_all_entries()
            index, original = self._find_entry(entry_id, old_entries)

            if original is None:
                return {
                    'status': 'ERROR',
                    'message': 'Eintrag nicht gefunden: %s' % entry_id,
                }

            new_entries = list(old_entries)
            del new_entries[index]

            result = self._save_history_change(
                old_entries,
                new_entries,
                force=force
            )

            if result.get('status') != 'OK':
                result['entry'] = original
                return result

            return {
                'status': 'OK',
                'message': 'Eintrag geloescht.',
                'deleted': original,
                'warnings': result.get('warnings', []),
                'all_warnings': result.get('all_warnings', []),
                'state': dict(self.state),
                'files': result.get('files', []),
            }

    def _append_jsonl(self, entry):
        if not os.path.isdir(self.log_dir):
            os.makedirs(self.log_dir)

        path = self._log_file(entry.get('timestamp'))
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
                    entry = self._normalize_entry(json.loads(line))
                    if entry is not None:
                        entries.append(entry)
                except Exception:
                    pass

        return entries

    def _rebuild_state_from_log(self):
        # Der aktuelle Zustand wird aus der gesamten Historie rekonstruiert.
        self._refresh_runtime_state(self._load_all_entries())

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

            measurement = 'avnav_logbuch'
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

    def _save_entry(
        self,
        event_type,
        text,
        lat=None,
        lon=None,
        force=False,
        timestamp=None,
        resolve_position=False
    ):
        event_type = str(event_type or 'manual').strip()

        if event_type not in self._known_event_types():
            return {
                'status': 'ERROR',
                'message': 'Unbekannter Eventtyp: %s' % event_type,
                'requires_force': False,
            }

        try:
            entry = self._normalize_entry(
                self._build_entry(
                    event_type,
                    text,
                    lat,
                    lon,
                    timestamp
                )
            )

            if resolve_position:
                entry = self._apply_track_position(entry)
        except ValueError as error:
            return {
                'status': 'ERROR',
                'message': str(error),
                'requires_force': False,
            }

        with self.lock:
            old_entries = self._load_all_entries()
            new_entries = list(old_entries)
            new_entries.append(entry)

            result = self._save_history_change(
                old_entries,
                new_entries,
                force=force
            )

            if result.get('status') != 'OK':
                result['entry'] = entry
                result['event_type'] = event_type
                result['state'] = dict(self.state)
                return result

            _, saved_entry = self._find_entry(
                entry.get('id'),
                result.get('entries', [])
            )

        influx_ok, influx_msg = self._write_influx(saved_entry)

        return {
            'status': 'OK',
            'entry': saved_entry,
            'file': self._log_file(saved_entry.get('timestamp')),
            'files': result.get('files', []),
            'warnings': result.get('warnings', []),
            'all_warnings': result.get('all_warnings', []),
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

                if 'No logbuch file found' in job['stderr']:
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

    def _parse_logbuch_timestamp(self, value):
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

                            timestamp = self._parse_logbuch_timestamp(
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

                force = self._as_bool(
                    self._get_arg(args, 'force', 'false')
                )
                timestamp = self._get_arg(args, 'timestamp', None)
                resolve_position = self._as_bool(
                    self._get_arg(args, 'resolve_position', 'false')
                )

                self.api.log(
                    "DEBUG api/add args=%s timestamp=%r"
                    % (repr(args), timestamp)
                )

                return self._save_entry(
                    event_type,
                    text,
                    lat,
                    lon,
                    force,
                    timestamp,
                    resolve_position
                )

            if url in (
                'entry/update',
                'api/entry/update',
                'updateEntry',
                'api/updateEntry'
            ):
                entry_id = self._get_arg(
                    args,
                    'id',
                    self._get_arg(args, 'entry_id', '')
                )

                if not entry_id:
                    return {
                        'status': 'ERROR',
                        'message': 'Eintrags-ID fehlt.'
                    }

                force = self._as_bool(
                    self._get_arg(args, 'force', 'false')
                )

                return self._update_entry(
                    entry_id=entry_id,
                    event_type=self._get_arg(args, 'event_type', None),
                    text=self._get_arg(args, 'text', None),
                    timestamp=self._get_arg(args, 'timestamp', None),
                    lat=self._get_arg(args, 'lat', None),
                    lon=self._get_arg(args, 'lon', None),
                    force=force
                )

            if url in (
                'entry/delete',
                'api/entry/delete',
                'deleteEntry',
                'api/deleteEntry'
            ):
                entry_id = self._get_arg(
                    args,
                    'id',
                    self._get_arg(args, 'entry_id', '')
                )

                if not entry_id:
                    return {
                        'status': 'ERROR',
                        'message': 'Eintrags-ID fehlt.'
                    }

                force = self._as_bool(
                    self._get_arg(args, 'force', 'false')
                )

                return self._delete_entry(
                    entry_id=entry_id,
                    force=force
                )

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

            if url in ('summary', 'api/summary'):
                return {
                    'status': 'OK',
                    'days': self._list_logbook_days()
                }

            if url in ('day', 'api/day'):
                date_value = self._get_arg(args, 'date', '')

                if not date_value:
                    return {
                        'status': 'ERROR',
                        'message': 'date required'
                    }

                try:
                    datetime.datetime.strptime(date_value, '%Y-%m-%d')
                except (TypeError, ValueError):
                    return {
                        'status': 'ERROR',
                        'message': 'invalid date format, expected YYYY-MM-DD'
                    }

                entries = self._read_logbook_day(date_value)

                return {
                    'status': 'OK',
                    'date': date_value,
                    'count': len(entries),
                    'entries': entries
                }

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
