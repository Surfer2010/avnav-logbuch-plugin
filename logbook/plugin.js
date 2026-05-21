console.log("logbook plugin loaded");

/*
 * AVNav Logbook Frontend
 *
 * Wichtig:
 * AVNav nutzt globale Tastatur- und Touch-Handler.
 * Deshalb stoppen wir im Overlay alle relevanten Events,
 * damit Texteingaben nicht die AVNav-Oberfläche steuern.
 */

var logbookWidget = {
    name: "logbook_EntryWidget",

    storeKeys: {
        lat: "nav.gps.lat",
        lon: "nav.gps.lon"
    },

    caption: "Logbuch",

    renderHtml: function(props) {
        return (
            '<div class="widgetData logbookWidgetData">' +
                '<button type="button" class="logbookOpenButton" data-logbook-open="1">' +
                    'Logbuch' +
                '</button>' +
            '</div>'
        );
    }
};

avnav.api.registerWidget(logbookWidget);

/*
 * Globaler Klick-Handler für den Logbuch-Button.
 */
document.addEventListener("click", function(ev) {
    var target = ev.target;

    if (!target) {
        return;
    }

    if (target.getAttribute("data-logbook-open") === "1") {
        ev.preventDefault();
        ev.stopPropagation();
        openLogbookOverlay();
    }
}, true);

/*
 * Stoppt Events innerhalb des Overlays.
 *
 * Hintergrund:
 * Ohne diese Sperre können Tastatureingaben im Textfeld gleichzeitig
 * AVNav-Shortcuts auslösen. Das führt dazu, dass einzelne Buchstaben
 * nicht im Textfeld erscheinen oder die AVNav-Seite wechselt.
 */
function stopOverlayEvent(ev) {
    if (!ev) {
        return;
    }

    ev.stopPropagation();
}

/*
 * Öffnet das Logbuch-Overlay.
 */
function openLogbookOverlay() {
    var existing = document.getElementById("logbookOverlay");
    if (existing) {
        existing.remove();
    }

    var overlay = document.createElement("div");
    overlay.id = "logbookOverlay";

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
            '<textarea id="logbookText" placeholder="Freitext / Bemerkung" autocomplete="off" autocorrect="off" autocapitalize="sentences" spellcheck="false"></textarea>' +

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
     * Alle wichtigen Events im Overlay abfangen.
     * Capture=true sorgt dafür, dass wir sie möglichst früh stoppen.
     */
    [
        "keydown",
        "keypress",
        "keyup",
        "input",
        "beforeinput",
        "compositionstart",
        "compositionupdate",
        "compositionend",
        "click",
        "dblclick",
        "mousedown",
        "mouseup",
        "touchstart",
        "touchend",
        "pointerdown",
        "pointerup",
        "wheel"
    ].forEach(function(eventName) {
        overlay.addEventListener(eventName, stopOverlayEvent, true);
    });

    /*
     * Klick auf dunklen Hintergrund schließt das Overlay.
     * Weil wir stopPropagation nutzen, prüfen wir direkt auf target === overlay.
     */
    overlay.addEventListener("click", function(e) {
        if (e.target === overlay) {
            e.preventDefault();
            overlay.remove();
        }
    });

    /*
     * Textfeld explizit fokussieren.
     * Dadurch landet die Tastatur-Eingabe direkt im Feld.
     */
    var textField = document.getElementById("logbookText");
    if (textField) {
        setTimeout(function() {
            textField.focus();
        }, 100);
    }

    /*
     * Quick-Buttons verbinden.
     */
    overlay.querySelectorAll("button[data-type]").forEach(function(btn) {
        btn.addEventListener("click", function(e) {
            e.preventDefault();
            saveLogbookEntry(btn.getAttribute("data-type"));
        });
    });

    /*
     * Manueller Eintrag.
     */
    document.getElementById("logbookSaveManual").addEventListener("click", function(e) {
        e.preventDefault();
        saveLogbookEntry("manual");
    });

    /*
     * Schließen-Buttons.
     */
    document.getElementById("logbookClose").addEventListener("click", function(e) {
        e.preventDefault();
        overlay.remove();
    });

    document.getElementById("logbookCloseTop").addEventListener("click", function(e) {
        e.preventDefault();
        overlay.remove();
    });

    loadLogbookEntries();
}

/*
 * Speichert einen Logbucheintrag über plugin.py.
 */
function saveLogbookEntry(type) {
    var textField = document.getElementById("logbookText");
    var status = document.getElementById("logbookStatus");

    var text = textField ? (textField.value || "") : "";

    if (status) {
        status.innerText = "Speichere...";
    }

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

                if (textField) {
                    textField.value = "";
                    textField.focus();
                }

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
 * Lädt die letzten Einträge.
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
 * Rendert Historie.
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
 * Interne Eventnamen lesbar machen.
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
 * Freitext sicher als HTML darstellen.
 */
function escapeHtml(value) {
    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
