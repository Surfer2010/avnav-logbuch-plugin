# Installation und Update ohne Git

Dieses Projekt kann auf einem AVNav-System auch ohne Git installiert oder aktualisiert werden.

Dafür gibt es:

```text
tools/install_or_update.sh
Standard-Update vom main-Branch
wget https://raw.githubusercontent.com/Surfer2010/avnav-logbuch-plugin/main/tools/install_or_update.sh -O install_or_update.sh
chmod +x install_or_update.sh
./install_or_update.sh
Update von einem bestimmten Branch

Beispiel:

./install_or_update.sh --branch fix/responsive-overlay-input-button
Installation in einen bestimmten Zielpfad
./install_or_update.sh --target /home/pi/avnav/data/plugins/logbuch
Ohne Neustart installieren
./install_or_update.sh --no-restart
Was das Script macht
AVNav-Datenverzeichnis erkennen
bestehendes Plugin sichern
avnav_server.xml sichern
GitHub-ZIP herunterladen
Plugin-Dateien nach AVNav kopieren
Python-Syntax prüfen
AVNav neu starten
Backup-Pfad

Backups werden hier abgelegt:

/home/pi/avnav/data/plugin-backups

oder bei Debian-Paketinstallation:

/var/lib/avnav/plugin-backups
Rollback

Beispiel:

rm -rf /home/pi/avnav/data/plugins/logbuch
cp -a /home/pi/avnav/data/plugin-backups/logbuch.backup.YYYY-MM-DD-HHMMSS /home/pi/avnav/data/plugins/logbuch
sudo systemctl restart avnav
Prüfung
tail -n 100 /home/pi/avnav/data/log/avnav.log | grep -i logbuch
curl http://localhost:8080/plugins/user-logbuch/plugin.js | head

