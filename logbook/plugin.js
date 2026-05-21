console.log("logbook plugin loaded");

/*
 * AVNav Logbook Frontend
 *
 * Diese Datei registriert ein AVNav-Widget.
 * Das Widget zeigt einen Button "Logbuch".
 * Beim Klick öffnet sich ein Overlay mit:
 * - Quick-Buttons für Motor, Segel und Anker
 * - Freitextfeld für Anmerkungen
 * - Anzeige der letzten Logbucheinträge
 *
 * Die eigentliche Speicherung passiert serverseitig in plugin.py.
 * Dieses Frontend ruft dafür die API-Endpunkte des Plugins auf:
 *
 *   AVNAV_BASE_URL + "/api/add"
 *   AVNAV_BASE_URL + "/api/list"
 *
 * AVNAV_BASE_URL wird von AVNav automatisch gesetzt.
 * Bei deinem User-Plugin ist das z. B.:
 *
 *   /plugins/user-logbook
 */

var logbookWidget = {
    /*
     * Eindeutiger Widget-Name innerhalb von AVNav.
     * Dieser Name erscheint beim Hinzufügen des Widgets.
     */
    name: "logbook_EntryWidget",

    /*
     * storeKeys liest Werte aus dem AVNav-internen Datenspeicher.
     * Diese Werte werden an renderHtml(props) übergeben.
     *
     * gps.lat / gps.lon werden hier nicht direkt gespeichert.
     * Die finale Position wird serverseitig in plugin.py gelesen.
     * Trotzdem sind die Werte hier nützlich, um später im Widget
     * eine aktuelle Position anzeigen zu können.
     */
    storeKeys: {
        lat: "nav.gps.lat",
        lon: "nav.gps.lon"
    },

    /*
     * Beschriftung des Widgets in AVNav.
     */
    caption: "Logbuch",

    /*
     * initFunction wird von AVNav einmal pro Widget-Instanz aufgerufen.
     * Hier registrieren wir Event-Handler für Klicks.
     */
    initFunction: function(context) {

        /*
         * Dieser Event-Handler wird vom Widget-Button aufgerufen.
         * Er öffnet das Overlay.
         */
        context.eventHandler.openLogbook = function(ev) {

            /*
             * AVNav nutzt eigene Klick- und Touch-Logik.
             * Deshalb verhindern wir Standardverhalten und Event-Bubbling.
             */
            if (ev) {
                ev.preventDefault();
                ev.stopPropagation();
            }

            openLogbookOverlay();
        };
    },

    /*
     * renderHtml erzeugt den sichtbaren Inhalt des Widgets.
     *
     * Wichtig:
     * AVNav-Widget-Events werden über avnav.api.templateReplace
     * mit dem registrierten Event-Handler verbunden.
     */
    renderHtml: function(props) {

        var template =
            '<div class="widgetData logbookWidgetData">' +
                '<button type="button" class="logbookOpenButton" onclick="${openLogbook}">' +
                    'Logbuch' +
                '</button>' +
            '</div>';

        return avnav.api.templateReplace(template, {
            openLogbook: this.eventHandler.openLogbook
        });
    }
};

/*
 * Widget bei AVNav registrieren.
 * Erst dadurch kann es im Layout hinzugefügt werden.
 */
avnav.api.registerWidget(logbookWidget);

/*
 * Öffnet das Logbuch-Overlay.
 */
function openLogbookOverlay() {

    /*
     * Falls bereits ein Overlay offen ist, wird es zuerst entfernt.
     * Damit vermeiden wir doppelte Dialoge.
     */
    var existing = document.getElementById("logbookOverlay");
    if (existing) {
        existing.remove();
    }

    /*
     * Overlay-Container erzeugen.
     * Das eigentliche Styling kommt aus plugin.css.
     */
    var overlay = document.createElement("div");
    overlay.id = "logbookOverlay";

    /*
     * HTML des Popups.
     * Keine Template-Strings, damit die Datei auch in älteren Browsern robust läuft.
     */
    overlay.innerHTML =
        '<div class="logbookBox">' +

            '<div class="logbookHeader">' +
                '<h2>Logbucheintrag</h2>' +
                '<button type="button" id="logbookCloseTop" class="logbookCloseButton">×</button>' +
            '</div>' +

            '<div class="logbookSectionTitle">Motor</div>' +
            '<div class="logbookGroup">' +
                '<button type="button" data-type="motor_on">Motor an</button>' +
                '<button type="button" data-type="motor_off">Motor aus</button>' +
            '</div>' +

            '<div class="logbookSectionTitle">Segel</div>' +
            '<div class="logbookGroup">' +
                '<button type="button" data-type="sail_set">Segel setzen</button>' +
                '<button type="button" data-type="sail_down">Segel einholen</button>' +
            '</div>' +

            '<div class="logbookSectionTitle">Anker</div>' +
            '<div class="logbookGroup">' +
                '<button type="button" data-type="anchor_down">Anker ab</button>' +
                '<button type="button" data-type="anchor_up">Anker auf</button>' +
            '</div>' +

            '<div class="logbookSectionTitle">Anmerkung</div>' +
            '<textarea id="logbookText" placeholder="Freitext / Bemerkung"></textarea>' +

            '<div class="logbookActions">' +
                '<button type="button" id="logbookSaveManual">Anmerkung speichern</button>' +
                '<button type="button" id="logbookClose">Schließen</button>' +
            '</div>' +

            '<div id="logbookStatus" class="logbookStatus">Bereit</div>' +

            '<div class="logbookSectionTitle">Letzte Einträge</div>' +
            '<div id="logbookEntries" class="logbookEntries">Lade Einträge...</div>' +

        '</div>';

    document.body.appendChild(overlay);

    /*
     * Klick auf dunklen Hintergrund schließt das Overlay.
     * Klicks innerhalb der Box sollen es nicht schließen.
     */
    overlay.addEventListener("click", function(e) {
        if (e.target === overlay) {
            overlay.remove();
        }
    });

    var box = overlay.querySelector(".logbookBox");
    if (box) {
        box.addEventListener("click", function(e) {
            e.stopPropagation();
        });
    }

    /*
     * Quick-Buttons verbinden.
     * Jeder Button trägt seinen Ereignistyp in data-type.
     */
    overlay.querySelectorAll("button[data-type]").forEach(function(btn) {
        btn.addEventListener("click", function(e) {
            e.preventDefault();
            e.stopPropagation();

            saveLogbookEntry(btn.getAttribute("data-type"));
        });
    });

    /*
     * Manueller Eintrag ohne Quick-Button.
     */
    document.getElementById("logbookSaveManual").addEventListener("click", function(e) {
        e.preventDefault();
        e.stopPropagation();

        saveLogbookEntry("manual");
    });

    /*
     * Schließen-Buttons.
     */
    document.getElementById("logbookClose").addEventListener("click", function(e) {
        e.preventDefault();
        e.stopPropagation();
        overlay.remove();
    });

    document.getElementById("logbookCloseTop").addEventListener("click", function(e) {
        e.preventDefault();
        e.stopPropagation();
        overlay.remove();
    });

    /*
     * Beim Öffnen sofort die letzten Einträge laden.
     */
    loadLogbookEntries();
}

/*
 * Speichert einen Logbucheintrag über die Plugin-API.
 */
function saveLogbookEntry(type) {

    var textField = document.getElementById("logbookText");
    var status = document.getElementById("logbookStatus");

    var text = "";
    if (textField) {
        text = textField.value || "";
    }

    if (status) {
        status.innerText = "Speichere...";
    }

    /*
     * plugin.py akzeptiert type und text als Query-Parameter.
     * Die GPS-Position wird serverseitig aus AVNav gelesen.
     */
    var url =
        AVNAV_BASE_URL +
        "/api/add?type=" +
        encodeURIComponent(type) +
        "&text=" +
        encodeURIComponent(text);

    fetch(url)
        .then(function(response) {
            return response.json();
        })
        .then(function(data) {

            if (data.status === "OK") {
                if (status) {
                    status.innerText = "Gespeichert: " + readableEventType(type);
                }

                /*
                 * Nach erfolgreichem Speichern wird das Textfeld geleert.
                 * Dadurch ist klar, dass der Eintrag übernommen wurde.
                 */
                if (textField) {
                    textField.value = "";
                }

                /*
                 * Historie aktualisieren.
                 */
                loadLogbookEntries();

                console.log("logbook saved", data);
            } else {
                if (status) {
                    status.innerText = "Fehler: " + (data.message || "unbekannt");
                }
                console.error("logbook save error", data);
            }
        })
        .catch(function(err) {
            if (status) {
                status.innerText = "Fehler beim Speichern";
            }
            console.error("logbook request error", err);
        });
}

/*
 * Lädt die letzten Einträge aus der JSONL-Datei über plugin.py.
 */
function loadLogbookEntries() {

    var target = document.getElementById("logbookEntries");
    if (!target) {
        return;
    }

    target.innerHTML = "Lade Einträge...";

    fetch(AVNAV_BASE_URL + "/api/list?limit=10")
        .then(function(response) {
            return response.json();
        })
        .then(function(data) {

            if (data.status !== "OK") {
                target.innerHTML = "Einträge konnten nicht geladen werden.";
                return;
            }

            renderLogbookEntries(data.entries || []);
        })
        .catch(function(err) {
            target.innerHTML = "Fehler beim Laden der Einträge.";
            console.error("logbook list error", err);
        });
}

/*
 * Rendert die letzten Logbucheinträge in das Overlay.
 */
function renderLogbookEntries(entries) {

    var target = document.getElementById("logbookEntries");
    if (!target) {
        return;
    }

    if (!entries.length) {
        target.innerHTML = "Noch keine Einträge vorhanden.";
        return;
    }

    /*
     * Neueste Einträge zuerst anzeigen.
     */
    var html = "";
    entries.slice().reverse().forEach(function(entry) {

        var time = entry.timestamp || "";
        var type = readableEventType(entry.event_type || "manual");
        var text = escapeHtml(entry.text || "");
        var position = "";

        if (entry.lat !== null && entry.lat !== undefined && entry.lon !== null && entry.lon !== undefined) {
            position = " · " + entry.lat + ", " + entry.lon;
        }

        html +=
            '<div class="logbookEntry">' +
                '<div class="logbookEntryMeta">' +
                    escapeHtml(time) + ' · ' + escapeHtml(type) + escapeHtml(position) +
                '</div>' +
                '<div class="logbookEntryText">' +
                    (text || "&nbsp;") +
                '</div>' +
            '</div>';
    });

    target.innerHTML = html;
}

/*
 * Übersetzt interne Event-Typen in lesbare deutsche Bezeichnungen.
 */
function readableEventType(type) {

    var labels = {
        motor_on: "Motor an",
        motor_off: "Motor aus",
        sail_set: "Segel gesetzt",
        sail_down: "Segel eingeholt",
        anchor_down: "Anker ab",
        anchor_up: "Anker auf",
        manual: "Manueller Eintrag"
    };

    return labels[type] || type || "Unbekannt";
}

/*
 * Kleine HTML-Escaping-Funktion.
 * Wichtig, damit Freitext nicht als HTML ausgeführt wird.
 */
function escapeHtml(value) {

    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
