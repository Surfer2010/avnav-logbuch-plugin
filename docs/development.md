Entwicklung
Grundidee
Das Plugin besteht aus drei Hauptdateien:
```text
plugin.py   Server-Teil
plugin.js   AVNav-Frontend-Widget
plugin.css  Styling fuer Overlay und Button
```
plugin.py
Aufgaben:
Plugin bei AVNav registrieren
API-Endpunkte bereitstellen
Logbucheintraege entgegennehmen
Eintraege als JSONL-Datei speichern
plugin.js
Aufgaben:
Widget in AVNav registrieren
Logbuch-Button anzeigen
Overlay/Popup oeffnen
Quick-Buttons bereitstellen
Freitext erfassen
Eintrag per API an plugin.py senden
plugin.css
Aufgaben:
Overlay gestalten
Eingabemaske gestalten
Buttons und Statusanzeige formatieren
Entwicklungsablauf
Nach Aenderungen an einer Datei:
```bash
cp logbuch/plugin.js /var/lib/avnav/plugins/logbuch/
cp logbuch/plugin.py /var/lib/avnav/plugins/logbuch/
cp logbuch/plugin.css /var/lib/avnav/plugins/logbuch/
systemctl restart avnav
```
Browser hart neu laden:
```text
Strg + F5
```
Logs ansehen
```bash
journalctl -u avnav -f
```
Oder AVNav-Log direkt:
```bash
tail -f /var/lib/avnav/log/avnav.log
```
Git-Workflow
Aenderungen pruefen:
```bash
git status
git diff
```
Aenderungen uebernehmen:
```bash
git add .
git commit -m "Add initial logbook widget"
```
Version markieren:
```bash
git tag v0.1.0
git push origin v0.1.0
```
Zurueck zu funktionierender Version:
```bash
git log --oneline
git checkout <commit-id>
```
