Installation
Zielpfad bei Debian/Proxmox-Testinstallation
Bei einer AVNav-Installation ueber Debian-Paket liegt das Datenverzeichnis typischerweise unter:
```text
/var/lib/avnav
```
Das Plugin wird installiert nach:
```text
/var/lib/avnav/plugins/logbook
```
Installation
```bash
mkdir -p /var/lib/avnav/plugins/logbook

cp logbook/plugin.py /var/lib/avnav/plugins/logbook/
cp logbook/plugin.js /var/lib/avnav/plugins/logbook/
cp logbook/plugin.css /var/lib/avnav/plugins/logbook/

chown -R avnav:avnav /var/lib/avnav/plugins/logbook
chmod -R 755 /var/lib/avnav/plugins/logbook

systemctl restart avnav
```
Pruefen
```bash
journalctl -u avnav -n 100 --no-pager | grep -i logbook
```
Erwartete Ausgabe enthaelt ungefaehr:
```text
loaded /var/lib/avnav/plugins/logbook/plugin.py as user-logbook
Logbook plugin started
```
Frontend pruefen
Im Browser:
```text
http://AVNAV-IP:8080
```
Dann Entwicklerkonsole oeffnen:
```text
F12 -> Console
```
Erwartete Ausgabe:
```text
logbook plugin loaded
```
Direkt pruefen
```text
http://AVNAV-IP:8080/plugins/user-logbook/plugin.js
```
