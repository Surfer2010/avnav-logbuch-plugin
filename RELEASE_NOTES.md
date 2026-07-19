# v1.8.0

## Neue Funktionen

- Logbucheinträge können direkt in der Detailansicht dupliziert werden
- Neue Einträge können vor oder nach einem bestehenden Eintrag eingefügt werden
- Duplizierte Einträge erhalten beim Speichern eine neue eindeutige ID
- Eingefügte Einträge können vor dem Speichern vollständig bearbeitet werden
- Beim Ändern des Zeitstempels wird die Position anhand der AVNav-Trackdatei neu bestimmt

## Positionsbestimmung

- Positionsdaten werden aus den AVNav-AVT-Trackdateien gelesen
- Exakte Trackpunkte werden direkt übernommen
- Zwischen benachbarten Trackpunkten kann die Position interpoliert werden
- Alternativ kann ein zeitlich naher Trackpunkt verwendet werden
- Einträge werden auch dann gespeichert, wenn keine Trackposition verfügbar ist
- Fehlende Positionen werden eindeutig als `unknown` gekennzeichnet

## Historie und Status

- Neue und bearbeitete Einträge werden in die chronologische Historie einsortiert
- Motor-, Segel- und Ankerstatus werden nach Änderungen vollständig neu berechnet
- Ungültige Statusfolgen erzeugen weiterhin eine Warnung
- Das erzwungene Speichern trotz Warnung bleibt möglich

## Benutzeroberfläche

- Neue Aktionen:
  - Duplizieren
  - Davor einfügen
  - Danach einfügen
- Gemeinsames Bearbeitungsformular für neue, duplizierte und vorhandene Einträge
- Anzeige, dass für neue Einträge beim Speichern eine neue ID erzeugt wird

## Technische Änderungen

- Neuer AVT-Parser im Backend
- Positionsauflösung und Winkelinterpolation für Kursdaten
- Erweiterung der Add-API um die optionale Positionsauflösung
- Erneute Positionsbestimmung beim Ändern eines Zeitstempels
