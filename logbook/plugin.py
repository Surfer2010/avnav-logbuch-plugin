# AVNav Logbook Plugin
# Stores digital logbook events as JSONL and optionally writes to InfluxDB v2.

from __future__ import absolute_import

import json
import os
import time
import datetime
import threading
import traceback

try:
    # Optional, only used by IDEs. AVNav provides this at runtime.
    from avnav_api import AVNApi  # noqa: F401
except Exception:
    pass


class Plugin(object):
    LOG_STATUS = 'logbook.status'
    LOG_COUNT = 'logbook.count'
    LAST_EVENT = 'logbook.lastEvent'

    @classmethod
    def pluginInfo(cls):
        return {
            'description': 'Digitales Logbuch: Zeitstempel, GPS-Position, Freitext und Schnellbuttons.',
            'data': [
                {'path': cls.LOG_STATUS, 'description': 'Logbook plugin status'},
                {'path': cls.LOG_COUNT, 'description': 'Number of logbook entries in current runtime'},
                {'path': cls.LAST_EVENT, 'description': 'Last logbook event type'},
            ]
        }

    def __init__(self, api):
        self.api = api
        self.lock = threading.Lock()
        self.count = 0
        self.base_dir = self._get_base_dir()
        self.log_dir = self._get_config('logDir', os.path.join(self.base_dir, 'logbook'))
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
            self.api.log('Logbook plugin started, log_dir=%s' % self.log_dir)
            self.api.setStatus('Logbook', 'running')
            self.api.addData(self.LOG_STATUS, 'running')
            self.api.addData(self.LOG_COUNT, self.count)
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

    def _get_position(self):
        lat = None
        lon = None
        candidates = [
            ('gps.lat', 'gps.lon'),
            ('gps.latitude', 'gps.longitude'),
            ('nav.gps.lat', 'nav.gps.lon'),
            ('navigation.position.latitude', 'navigation.position.longitude'),
        ]
        for lat_key, lon_key in candidates:
            try:
                lat = self.api.getSingleValue(lat_key)
                lon = self.api.getSingleValue(lon_key)
                if lat is not None and lon is not None:
                    return self._to_float(lat), self._to_float(lon)
            except Exception:
                pass
        return None, None

    def _to_float(self, value):
        try:
            if isinstance(value, dict) and 'value' in value:
                value = value.get('value')
            return float(value)
        except Exception:
            return None

    def _sanitize_text(self, text):
        if text is None:
            return ''
        text = str(text)
        text = text.replace('\r', ' ').replace('\n', ' ').strip()
        if len(text) > 1000:
            text = text[:1000]
        return text

    def _build_entry(self, event_type, text, lat=None, lon=None):
        if lat is None or lon is None:
            gps_lat, gps_lon = self._get_position()
            if lat is None:
                lat = gps_lat
            if lon is None:
                lon = gps_lon
        return {
            'timestamp': self._now_utc(),
            'event_type': event_type or 'manual',
            'text': self._sanitize_text(text),
            'lat': self._to_float(lat),
            'lon': self._to_float(lon),
            'source': 'avnav-logbook-plugin'
        }

    def _append_jsonl(self, entry):
        if not os.path.isdir(self.log_dir):
            os.makedirs(self.log_dir)
        path = self._today_file()
        line = json.dumps(entry, ensure_ascii=False, sort_keys=True)
        with open(path, 'a') as f:
            f.write(line.encode('utf-8') if False else line)
            f.write('\n')
        return path

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
            if entry.get('lat') is not None:
                fields.append('lat=%s' % entry.get('lat'))
            if entry.get('lon') is not None:
                fields.append('lon=%s' % entry.get('lon'))
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
        entry = self._build_entry(event_type, text, lat, lon)
        with self.lock:
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
            'influx': {'enabled': self.influx_enabled, 'ok': influx_ok, 'message': influx_msg}
        }

    def _get_arg(self, args, name, default=None):
        if args is None:
            return default
        value = args.get(name, default)
        if isinstance(value, list):
            return value[0] if len(value) else default
        return value

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
                    'influxEnabled': self.influx_enabled
                }

            if url in ('list', 'api/list'):
                limit = int(self._get_arg(args, 'limit', 50))
                return self._list_entries(limit)

            return {'status': 'ERROR', 'message': 'unknown request: %s' % url}
        except Exception as e:
            self.api.error('Logbook API error: %s\n%s' % (str(e), traceback.format_exc()))
            return {'status': 'ERROR', 'message': str(e)}

    def _list_entries(self, limit):
        path = self._today_file()
        entries = []
        if os.path.exists(path):
            with open(path, 'r') as f:
                lines = f.readlines()[-limit:]
            for line in lines:
                try:
                    entries.append(json.loads(line))
                except Exception:
                    pass
        return {'status': 'OK', 'file': path, 'entries': entries}
