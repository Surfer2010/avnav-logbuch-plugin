console.log("logbuch plugin loaded");

/*
 * AVNav Logbuch Frontend
 *
 * Funktionen:
 * - AVNav Widget mit Logbuch-Button
 * - Overlay mit Quick-Buttons
 * - Freitextfeld
 * - letzte Einträge
 * - sichtbare Warnungen bei ungültigen Aktionen
 */

var logbuchWidget = {
    name: "logbuch_b_popup",

    storeKeys: {
        lat: "nav.gps.lat",
        lon: "nav.gps.lon"
    },

    caption: "Logbuch",

    renderHtml: function(props) {
        return (
            '<div class="widgetData logbuchWidgetData">' +
                '<button type="button" class="logbookOpenButton" data-logbook-open="1">' +
                    'Logbuch' +
                '</button>' +
            '</div>'
        );
    }
};

avnav.api.registerWidget(logbuchWidget);

function logbuchIconSvg(iconName) {
    var icons = {
        "motor-an":
            '<svg viewBox="0 0 64 64" class="logbuchDirectSvg">' +
            '<path d="M18 28h6v-8h18v6h6c4 0 7 3 7 7v10c0 4-3 7-7 7h-6v5H24v-5h-6c-4 0-7-3-7-7V33c0-4 3-5 7-5z"/>' +
            '<rect x="25" y="12" width="15" height="7" rx="2"/>' +
            '<rect x="5" y="31" width="7" height="15" rx="2"/>' +
            '<rect x="55" y="31" width="5" height="15" rx="2"/>' +
            '</svg>',

        "motor-aus":
            '<svg viewBox="0 0 64 64" class="logbuchDirectSvg">' +
            '<path d="M18 28h6v-8h18v6h6c4 0 7 3 7 7v10c0 4-3 7-7 7h-6v5H24v-5h-6c-4 0-7-3-7-7V33c0-4 3-5 7-5z"/>' +
            '<rect x="25" y="12" width="15" height="7" rx="2"/>' +
            '<rect x="5" y="31" width="7" height="15" rx="2"/>' +
            '<rect x="55" y="31" width="5" height="15" rx="2"/>' +
            '<path d="M9 58 L58 9" class="logbuchDirectStroke"/>' +
            '</svg>',

        "segel-hoch":
            '<svg viewBox="0 0 64 64" class="logbuchDirectSvg">' +
            '<path d="M15 50h28c-2 5-7 7-14 7s-12-2-14-7z"/>' +
            '<path d="M28 12v37h-15c3-14 8-26 15-37z"/>' +
            '<path d="M31 16v33h15c-2-12-7-23-15-33z"/>' +
            '<path d="M51 48V22" class="logbuchDirectStroke"/>' +
            '<path d="M42 31l9-9 9 9" class="logbuchDirectStroke"/>' +
            '</svg>',

        "segel-runter":
            '<svg viewBox="0 0 64 64" class="logbuchDirectSvg">' +
            '<path d="M14 50h29c-2 5-7 7-15 7s-12-2-14-7z"/>' +
            '<path d="M26 31v18H13c2-7 6-13 13-18z"/>' +
            '<path d="M51 20v26" class="logbuchDirectStroke"/>' +
            '<path d="M42 37l9 9 9-9" class="logbuchDirectStroke"/>' +
            '</svg>',

        "anker-ab":
            '<svg viewBox="0 0 64 64" class="logbuchDirectSvg">' +
            '<circle cx="25" cy="10" r="6" fill="none" class="logbuchDirectStroke"/>' +
            '<path d="M25 16v31" class="logbuchDirectStroke"/>' +
            '<path d="M16 25h18" class="logbuchDirectStroke"/>' +
            '<path d="M14 34c0 13 8 20 11 20s11-7 11-20" fill="none" class="logbuchDirectStroke"/>' +
            '<path d="M8 39l7-4 2 8" />' +
            '<path d="M42 39l-7-4-2 8" />' +
            '<path d="M51 23v28" class="logbuchDirectStroke"/>' +
            '<path d="M42 42l9 9 9-9" class="logbuchDirectStroke"/>' +
            '</svg>',

        "anker-auf":
            '<svg viewBox="0 0 64 64" class="logbuchDirectSvg">' +
            '<circle cx="25" cy="10" r="6" fill="none" class="logbuchDirectStroke"/>' +
            '<path d="M25 16v31" class="logbuchDirectStroke"/>' +
            '<path d="M16 25h18" class="logbuchDirectStroke"/>' +
            '<path d="M14 34c0 13 8 20 11 20s11-7 11-20" fill="none" class="logbuchDirectStroke"/>' +
            '<path d="M8 39l7-4 2 8" />' +
            '<path d="M42 39l-7-4-2 8" />' +
            '<path d="M51 51V23" class="logbuchDirectStroke"/>' +
            '<path d="M42 32l9-9 9 9" class="logbuchDirectStroke"/>' +
            '</svg>'
    };

    return icons[iconName] || "";
}

var logbuchActionWidgets = [
    { name: "logbuch_b_motor_an", caption: "Motor an", type: "motor_on", icon: "motor-on" },
    { name: "logbuch_b_motor_aus", caption: "Motor aus", type: "motor_off", icon: "motor-off" },
    { name: "logbuch_b_segel_hoch", caption: "Segel hoch", type: "sail_set", icon: "sail-set" },
    { name: "logbuch_b_segel_runter", caption: "Segel runter", type: "sail_down", icon: "sail-down" },
    { name: "logbuch_b_anker_ab", caption: "Anker ab", type: "anchor_down", icon: "anchor-down" },
    { name: "logbuch_b_anker_auf", caption: "Anker auf", type: "anchor_up", icon: "anchor-up" }
];

logbuchActionWidgets.forEach(function(widget) {
    avnav.api.registerWidget({
        name: widget.name,
        caption: widget.caption,

        renderHtml: function(props) {
            return (
                '<div class="widgetData logbuchDirectWidgetData" title="' + escapeHtml(widget.caption) + '">' +
                    '<button type="button" class="logbuchDirectButton" data-logbook-direct="' + widget.type + '" aria-label="' + escapeHtml(widget.caption) + '">' +
                        '<img class="logbuchDirectIcon" src="' + iconPath(widget.icon) + '" alt="">' +
                    '</button>' +
                '</div>'
            );
        }
    });
});


document.addEventListener("click", function(ev) {
    var target = ev.target;

    if (!target) {
        return;
    }

    if (target.getAttribute("data-logbook-open") === "1") {
        ev.preventDefault();
        ev.stopPropagation();
        openLogbuchOverlay();
        return;
    }

    var directType = target.getAttribute("data-logbook-direct");

    if (!directType && target.closest) {
        var directButton = target.closest("[data-logbook-direct]");
        if (directButton) {
            directType = directButton.getAttribute("data-logbook-direct");
        }
    }

    if (directType) {
        ev.preventDefault();
        ev.stopPropagation();
        saveDirectLogbuchEntry(directType);
    }
}, true);

function stopKeyboardEvent(ev) {
    if (!ev) {
        return;
    }

    ev.stopPropagation();
}

function iconPath(name) {
    return AVNAV_BASE_URL + "/icons/" + name + ".png";
}

function setLogbuchStatus(message, level) {
    var status = document.getElementById("logbuchStatus");

    if (!status) {
        return;
    }

    status.className = "logbuchStatus logbuchStatus-" + (level || "info");
    status.innerText = message || "";
}

function openLogbuchOverlay() {
    var existing = document.getElementById("logbuchOverlay");
    if (existing) {
        existing.remove();
    }

    var overlay = document.createElement("div");
    overlay.id = "logbuchOverlay";

    overlay.innerHTML =
        '<div class="logbuchBox">' +

            '<div class="logbuchHeader">' +
                '<h2>Logbucheintrag</h2>' +
                '<button type="button" id="logbookCloseTop" class="logbookCloseButton">×</button>' +
            '</div>' +

            '<div class="logbuchMainLayout">' +

                '<div class="logbuchInputPane">' +

                    '<div class="logbuchSectionTitle">Motor</div>' +
                    '<div class="logbuchGroup">' +
                        logbuchButton("motor_on", "Motor an", "motor-on", "logbuchMotorOn") +
                        logbuchButton("motor_off", "Motor aus", "motor-off", "logbuchMotorOff") +
                    '</div>' +

                    '<div class="logbuchSectionTitle">Segel</div>' +
                    '<div class="logbuchGroup">' +
                        logbuchButton("sail_set", "Segel setzen", "sail-set", "logbuchSailOn") +
                        logbuchButton("sail_down", "Segel einholen", "sail-down", "logbuchSailOff") +
                    '</div>' +

                    '<div class="logbuchSectionTitle">Anker</div>' +
                    '<div class="logbuchGroup">' +
                        logbuchButton("anchor_down", "Anker ab", "anchor-down", "logbuchAnchorOn") +
                        logbuchButton("anchor_up", "Anker auf", "anchor-up", "logbuchAnchorOff") +
                    '</div>' +

                '</div>' +

                '<div class="logbuchHistoryPane">' +

                    '<div id="logbuchStatus" class="logbuchStatus logbuchStatus-info">Bereit</div>' +

                    '<div class="logbuchExportRow">' +

                        '<button type="button" id="logbookExportToday" class="logbuchMiniButton">' +
                            'KMZ Heute' +
                        '</button>' +

                        '<button type="button" id="logbookExportTrip" class="logbuchMiniButton">' +
                            'Törn Export' +
                        '</button>' +

                        '<button type="button" id="logbookTripStart" class="logbuchMiniButton">' +
                            'Törn Start' +
                        '</button>' +

                        '<button type="button" id="logbookTripEnd" class="logbuchMiniButton">' +
                            'Törn Ende' +
                        '</button>' +

                    '</div>' +

                    '<div class="logbuchSectionTitle logbookHistoryTitle">Anmerkung / Freitext</div>' +

                    '<div class="logbuchTextRow">' +

                        '<textarea id="logbookText" placeholder="Freitext / Bemerkung eingeben..." autocomplete="off" autocorrect="off" autocapitalize="sentences" spellcheck="false"></textarea>' +

                        '<button type="button" id="logbookSaveManual" class="logbookVerticalSave">' +
                            '<span>Speichern</span>' +
                        '</button>' +

                    '</div>' +

                    '<div class="logbuchSectionTitle">Letzte Einträge</div>' +
                    '<div id="logbuchEntries" class="logbuchEntries">Lade Einträge...</div>' +

                '</div>' +

            '</div>' +

        '</div>';

    document.body.appendChild(overlay);

    [
        "keydown",
        "keypress",
        "keyup",
        "input",
        "beforeinput",
        "compositionstart",
        "compositionupdate",
        "compositionend"
    ].forEach(function(eventName) {
        overlay.addEventListener(eventName, stopKeyboardEvent, true);
    });

    overlay.addEventListener("click", function(e) {
        if (e.target === overlay) {
            e.preventDefault();
            e.stopPropagation();
            overlay.remove();
        }
    }, false);

    var box = overlay.querySelector(".logbuchBox");
    if (box) {
        box.addEventListener("click", function(e) {
            e.stopPropagation();
        }, false);
    }

    var textField = document.getElementById("logbookText");
    // Kein automatischer Fokus:
    // Auf Tablets würde sonst sofort die Bildschirmtastatur öffnen.

    overlay.querySelectorAll("button[data-type]").forEach(function(btn) {
        btn.addEventListener("click", function(e) {
            e.preventDefault();
            e.stopPropagation();
            saveLogbuchEntry(btn.getAttribute("data-type"));
        }, false);
    });

    document.getElementById("logbookSaveManual").addEventListener("click", function(e) {
        e.preventDefault();
        e.stopPropagation();
        saveLogbuchEntry("manual");
    }, false);
    document.getElementById("logbookCloseTop").addEventListener("click", function(e) {
        e.preventDefault();
        e.stopPropagation();
        overlay.remove();
    }, false);

    document.getElementById("logbookExportToday").addEventListener("click", function(e) {
        e.preventDefault();
        e.stopPropagation();
        exportTodayKmz();
    }, false);

    document.getElementById("logbookExportTrip").addEventListener("click", function(e) {
        e.preventDefault();
        e.stopPropagation();
        exportTripKmz();
    }, false);

    document.getElementById("logbookTripStart").addEventListener("click", function(e) {
        e.preventDefault();
        e.stopPropagation();
        saveLogbuchEntry("trip_start");
    }, false);

    document.getElementById("logbookTripEnd").addEventListener("click", function(e) {
        e.preventDefault();
        e.stopPropagation();
        saveLogbuchEntry("trip_end");
    }, false);

    loadLogbuchEntries();
}

function logbuchButton(type, label, iconName, extraClass) {
    return (
        '<button type="button" class="logbuchToggleButton ' + extraClass + '" data-type="' + type + '">' +
            '<img class="logbuchButtonIcon" src="' + iconPath(iconName) + '" alt="">' +
            '<span class="logbuchButtonLabel">' + escapeHtml(label) + '</span>' +
        '</button>'
    );
}



function saveDirectLogbuchEntry(type) {
    var url =
        AVNAV_BASE_URL +
        "/api/add?type=" +
        encodeURIComponent(type) +
        "&text=";

    fetch(url)
        .then(function(response) {
            return response.json();
        })
        .then(function(data) {
            if (data.status === "OK") {
                console.log("direct logbuch saved", type, data);
                return;
            }

            console.warn("direct logbuch warning", data);
        })
        .catch(function(err) {
            console.error("direct logbuch error", err);
        });
}

function saveLogbuchEntry(type) {
    var textField = document.getElementById("logbookText");
    var text = textField ? (textField.value || "") : "";

    setLogbuchStatus("Speichere...", "info");

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
                setLogbuchStatus("Gespeichert: " + readableEventType(type), "success");

                if (textField) {
                    textField.value = "";
                    textField.focus();
                }

                loadLogbuchEntries();

                console.log("logbuch saved", data);
                return;
            }

            /*
             * Server liefert ERROR bei ungültigen Zuständen:
             * z. B. Motor an, obwohl Motor bereits läuft.
             */
            setLogbuchStatus(data.message || "Aktion nicht möglich", "warning");
            console.warn("logbook warning", data);
        })
        .catch(function(err) {
            setLogbuchStatus("Fehler beim Speichern", "error");
            console.error("logbook request error", err);
        });
}

function loadLogbuchEntries() {
    var target = document.getElementById("logbuchEntries");
    if (!target) {
        return;
    }

    target.innerHTML = "Lade Einträge...";

    fetch(AVNAV_BASE_URL + "/api/list?limit=12")
        .then(function(response) {
            return response.json();
        })
        .then(function(data) {
            if (data.status !== "OK") {
                target.innerHTML = "Einträge konnten nicht geladen werden.";
                return;
            }

            renderLogbuchEntries(data.entries || []);
        })
        .catch(function(err) {
            target.innerHTML = "Fehler beim Laden der Einträge.";
            console.error("logbook list error", err);
        });
}

function renderLogbuchEntries(entries) {
    var target = document.getElementById("logbuchEntries");
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
        var icon = iconForEvent(entry.event_type || "manual");
        var position = "";

        if (entry.lat !== null && entry.lat !== undefined && entry.lon !== null && entry.lon !== undefined) {
            position = " · " + entry.lat + ", " + entry.lon;
        }

        html +=
            '<div class="logbuchEntry">' +
                '<div class="logbuchEntryIcon">' +
                    '<img src="' + iconPath(icon) + '" alt="">' +
                '</div>' +
                '<div class="logbuchEntryContent">' +
                    '<div class="logbuchEntryTitle">' + escapeHtml(type) + '</div>' +
                    '<div class="logbuchEntryMeta">' + escapeHtml(time) + escapeHtml(position) + '</div>' +
                    '<div class="logbuchEntryText">' + (text || "&nbsp;") + '</div>' +
                '</div>' +
            '</div>';
    });

    target.innerHTML = html;
}

function iconForEvent(type) {
    var icons = {
        motor_on: "motor-on",
        motor_off: "motor-off",
        sail_set: "sail-set",
        sail_down: "sail-down",
        anchor_down: "anchor-down",
        anchor_up: "anchor-up",
        manual: "manual"
    };

    return icons[type] || "manual";
}

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

function escapeHtml(value) {
    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}


function exportTodayKmz() {
    setLogbuchStatus("KMZ Export startet...", "info");

    fetch(AVNAV_BASE_URL + "/api/exportKmz")
        .then(function(response) {
            return response.json();
        })
        .then(function(data) {
            if (data.status !== "OK") {
                setLogbuchStatus("KMZ Exportfehler", "error");
                return;
            }

            monitorExportJob(data.job.id);
        })
        .catch(function(err) {
            console.error(err);
            setLogbuchStatus("KMZ Exportfehler", "error");
        });
}

function exportTripKmz() {
    var choice = window.prompt(
        "Törn Export:\n\n1 = letzte 7 Tage\n2 = seit letztem Törn Start",
        "2"
    );

    if (choice === null) {
        setLogbuchStatus("Törn Export abgebrochen", "info");
        return;
    }

    choice = String(choice).trim();

    if (choice === "1") {
        exportTripKmzLastSevenDays();
        return;
    }

    if (choice === "2") {
        exportTripKmzSinceTripStart();
        return;
    }

    setLogbuchStatus("Ungültige Auswahl", "error");
}

function exportTripKmzLastSevenDays() {
    setLogbuchStatus("Törn Export 7 Tage startet...", "info");

    var now = new Date();
    var toDate = now.toISOString().slice(0, 10);
    var from = new Date(now.getTime() - (6 * 24 * 60 * 60 * 1000));
    var fromDate = from.toISOString().slice(0, 10);

    var url =
        AVNAV_BASE_URL +
        "/api/exportTripKmz?from=" +
        encodeURIComponent(fromDate) +
        "&to=" +
        encodeURIComponent(toDate);

    startExportRequest(url, "Törn Exportfehler");
}

function exportTripKmzSinceTripStart() {
    setLogbuchStatus("Törn Export seit Start startet...", "info");

    startExportRequest(
        AVNAV_BASE_URL + "/api/exportCurrentTripKmz",
        "Törn Exportfehler"
    );
}

function startExportRequest(url, errorMessage) {
    fetch(url)
        .then(function(response) {
            return response.json();
        })
        .then(function(data) {
            if (data.status !== "OK") {
                setLogbuchStatus(data.message || errorMessage, "error");
                return;
            }

            monitorExportJob(data.job.id);
        })
        .catch(function(err) {
            console.error(err);
            setLogbuchStatus(errorMessage, "error");
        });
}

function monitorExportJob(jobId) {
    var pollCount = 0;

    var timer = setInterval(function() {
        pollCount++;

        fetch(
            AVNAV_BASE_URL +
            "/api/exportStatus?job=" +
            encodeURIComponent(jobId)
        )
            .then(function(response) {
                return response.json();
            })
            .then(function(data) {
                if (data.status !== "OK") {
                    clearInterval(timer);
                    setLogbuchStatus("Exportstatus Fehler", "error");
                    return;
                }

                var job = data.job;

                if (!job) {
                    clearInterval(timer);
                    setLogbuchStatus("Job nicht gefunden", "error");
                    return;
                }

                if (job.status === "RUNNING") {
                    setLogbuchStatus("Export läuft...", "info");
                    return;
                }

                clearInterval(timer);

                if (job.status === "OK") {
                    setLogbuchStatus("Export fertig", "success");
                    return;
                }

                setLogbuchStatus(job.message || "Export fehlgeschlagen", "error");
            })
            .catch(function(err) {
                console.error(err);
                clearInterval(timer);
                setLogbuchStatus("Exportstatus Fehler", "error");
            });

        if (pollCount > 60) {
            clearInterval(timer);
            setLogbuchStatus("Export Timeout", "error");
        }
    }, 1000);
}

