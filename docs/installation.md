Installation
Zielpfad bei Debian/Proxmox-Testinstallation
Bei einer AVNav-Installation ueber Debian-Paket liegt das Datenverzeichnis typischerweise unter:
```text
/var/lib/avnav
```
Das Plugin wird installiert nach:
```text
/var/lib/avnav/plugins/logbuch
```
Installation
```bash
mkdir -p /var/lib/avnav/plugins/logbuch

cp logbuch/plugin.py /var/lib/avnav/plugins/logbuch/
cp logbuch/plugin.js /var/lib/avnav/plugins/logbuch/
cp logbuch/plugin.css /var/lib/avnav/plugins/logbuch/

chown -R avnav:avnav /var/lib/avnav/plugins/logbuch
chmod -R 755 /var/lib/avnav/plugins/logbuch

systemctl restart avnav
```
Pruefen
```bash
journalctl -u avnav -n 100 --no-pager | grep -i logbuch
```
Erwartete Ausgabe enthaelt ungefaehr:
```text
loaded /var/lib/avnav/plugins/logbuch/plugin.py as user-logbuch
Logbuch plugin started
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
logbuch plugin loaded
```
Direkt pruefen
```text
http://AVNAV-IP:8080/plugins/user-logbuch/plugin.js
```
