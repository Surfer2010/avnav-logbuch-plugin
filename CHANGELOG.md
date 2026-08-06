## 2.0.2

### Korrigiertes Release-Paket

- Exportwerkzeuge werden vollständig unter `logbuch/tools/` paketiert
- ZIP-Prüfung kontrolliert alle benötigten Exportskripte
- `exportlib` und `renderers` werden als Teil des Plugins ausgeliefert
- Legacy-Loader verwendet einen versionsbezogenen Cache-Buster
- Mobile Scroll- und Schalterkorrekturen sind Bestandteil des Releases


### Cockpitbedienung

- Große und gut lesbare Motor- und Segel-Schalter
- Vergrößerte Touchflächen für die Bedienung an Bord
- Stabile Dialoggröße beim Aktualisieren der Einträge
- Nachfrage zum Ausschalten des Motors beim Setzen der Segel

### Festmachen als Location

- Einzelner Button „Festmachen“ mit großem Anker-Symbol
- Speicherung als positionsgebundene Location
- Location-Typ `anchor`
- Location-Bezeichnung `Festmachen`
- Keine Veränderung eines dauerhaften Ankerzustands
- Historische Ereignisse `anchor_down` und `anchor_up` bleiben lesbar
- Unterstützung in Logbuchansicht und Exporten

### Behobene Issues

- #41 Overlay-Schieberegler
- #42 Anker als Location statt Event
- #47 Motor ausschalten beim Setzen der Segel

## [1.9.0] - 2026-07-20

### Added

- On-demand HTML-Tagesexport mit DIN-A4-Layout
- Statische SVG-Karte mit Online-Kacheln und Offline-Fallback
- Gemeinsame Statistik- und Navigationsengine für HTML und KMZ
- Automatische Tests für Navigation, Karte und HTML-Export

### Changed

- Tages- und Törn-KMZ verwenden die gemeinsame Exportdatenbasis
- Release-Paket enthält die vollständigen Exportwerkzeuge
