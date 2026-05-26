console.log("logbook plugin loaded");

/*
 * AVNav Logbook Frontend
 *
 * Funktionen:
 * - AVNav Widget mit Logbuch-Button
 * - Overlay mit Quick-Buttons
 * - Freitextfeld
 * - letzte Einträge
 * - sichtbare Warnungen bei ungültigen Aktionen
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

function stopKeyboardEvent(ev) {
    if (!ev) {
        return;
    }

    ev.stopPropagation();
}

function iconPath(name) {
    return AVNAV_BASE_URL + "/icons/" + name + ".png";
}

function setLogbookStatus(message, level) {
    var status = document.getElementById("logbookStatus");

    if (!status) {
        return;
    }

    status.className = "logbookStatus logbookStatus-" + (level || "info");
    status.innerText = message || "";
}

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

            '<div class="logbookMainLayout">' +

                '<div class="logbookInputPane">' +

                    '<div class="logbookSectionTitle">Motor</div>' +
                    '<div class="logbookGroup">' +
                        logbookButton("motor_on", "Motor an", "motor-on", "logbookMotorOn") +
                        logbookButton("motor_off", "Motor aus", "motor-off", "logbookMotorOff") +
                    '</div>' +

                    '<div class="logbookSectionTitle">Segel</div>' +
                    '<div class="logbookGroup">' +
                        logbookButton("sail_set", "Segel setzen", "sail-set", "logbookSailOn") +
                        logbookButton("sail_down", "Segel einholen", "sail-down", "logbookSailOff") +
                    '</div>' +

                    '<div class="logbookSectionTitle">Anker</div>' +
                    '<div class="logbookGroup">' +
                        logbookButton("anchor_down", "Anker ab", "anchor-down", "logbookAnchorOn") +
                        logbookButton("anchor_up", "Anker auf", "anchor-up", "logbookAnchorOff") +
                    '</div>' +

                '</div>' +

                '<div class="logbookHistoryPane">' +

                    '<div id="logbookStatus" class="logbookStatus logbookStatus-info">Bereit</div>' +

                    '<div class="logbookExportRow">' +

                        '<button type="button" id="logbookExportToday" class="logbookMiniButton">' +
                            'KMZ Heute' +
                        '</button>' +

                        '<button type="button" id="logbookExportTrip" class="logbookMiniButton">' +
                            'Törn Export' +
                        '</button>' +

                        '<button type="button" id="logbookTripStart" class="logbookMiniButton">' +
                            'Törn Start' +
                        '</button>' +

                        '<button type="button" id="logbookTripEnd" class="logbookMiniButton">' +
                            'Törn Ende' +
                        '</button>' +

                    '</div>' +

                    '<div class="logbookSectionTitle logbookHistoryTitle">Anmerkung / Freitext</div>' +

                    '<div class="logbookTextRow">' +

                        '<textarea id="logbookText" placeholder="Freitext / Bemerkung eingeben..." autocomplete="off" autocorrect="off" autocapitalize="sentences" spellcheck="false"></textarea>' +

                        '<button type="button" id="logbookSaveManual" class="logbookVerticalSave">' +
                            '<span>Speichern</span>' +
                        '</button>' +

                    '</div>' +

                    '<div class="logbookSectionTitle">Letzte Einträge</div>' +
                    '<div id="logbookEntries" class="logbookEntries">Lade Einträge...</div>' +

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

    var box = overlay.querySelector(".logbookBox");
    if (box) {
        box.addEventListener("click", function(e) {
            e.stopPropagation();
        }, false);
    }

    var textField = document.getElementById("logbookText");
    if (textField) {
        setTimeout(function() {
            textField.focus();
        }, 100);
    }

    overlay.querySelectorAll("button[data-type]").forEach(function(btn) {
        btn.addEventListener("click", function(e) {
            e.preventDefault();
            e.stopPropagation();
            saveLogbookEntry(btn.getAttribute("data-type"));
        }, false);
    });

    document.getElementById("logbookSaveManual").addEventListener("click", function(e) {
        e.preventDefault();
        e.stopPropagation();
        saveLogbookEntry("manual");
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
        saveLogbookEntry("trip_start");
    }, false);

    document.getElementById("logbookTripEnd").addEventListener("click", function(e) {
        e.preventDefault();
        e.stopPropagation();
        saveLogbookEntry("trip_end");
    }, false);

    loadLogbookEntries();
}

function logbookButton(type, label, iconName, extraClass) {
    return (
        '<button type="button" class="logbookToggleButton ' + extraClass + '" data-type="' + type + '">' +
            '<img class="logbookButtonIcon" src="' + iconPath(iconName) + '" alt="">' +
            '<span class="logbookButtonLabel">' + escapeHtml(label) + '</span>' +
        '</button>'
    );
}

function saveLogbookEntry(type) {
    var textField = document.getElementById("logbookText");
    var text = textField ? (textField.value || "") : "";

    setLogbookStatus("Speichere...", "info");

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
                setLogbookStatus("Gespeichert: " + readableEventType(type), "success");

                if (textField) {
                    textField.value = "";
                    textField.focus();
                }

                loadLogbookEntries();

                console.log("logbook saved", data);
                return;
            }

            /*
             * Server liefert ERROR bei ungültigen Zuständen:
             * z. B. Motor an, obwohl Motor bereits läuft.
             */
            setLogbookStatus(data.message || "Aktion nicht möglich", "warning");
            console.warn("logbook warning", data);
        })
        .catch(function(err) {
            setLogbookStatus("Fehler beim Speichern", "error");
            console.error("logbook request error", err);
        });
}

function loadLogbookEntries() {
    var target = document.getElementById("logbookEntries");
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

            renderLogbookEntries(data.entries || []);
        })
        .catch(function(err) {
            target.innerHTML = "Fehler beim Laden der Einträge.";
            console.error("logbook list error", err);
        });
}

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
        var icon = iconForEvent(entry.event_type || "manual");
        var position = "";

        if (entry.lat !== null && entry.lat !== undefined && entry.lon !== null && entry.lon !== undefined) {
            position = " · " + entry.lat + ", " + entry.lon;
        }

        html +=
            '<div class="logbookEntry">' +
                '<div class="logbookEntryIcon">' +
                    '<img src="' + iconPath(icon) + '" alt="">' +
                '</div>' +
                '<div class="logbookEntryContent">' +
                    '<div class="logbookEntryTitle">' + escapeHtml(type) + '</div>' +
                    '<div class="logbookEntryMeta">' + escapeHtml(time) + escapeHtml(position) + '</div>' +
                    '<div class="logbookEntryText">' + (text || "&nbsp;") + '</div>' +
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
    setLogbookStatus("KMZ Export startet...", "info");

    fetch(AVNAV_BASE_URL + "/api/exportKmz")
        .then(function(response) {
            return response.json();
        })
        .then(function(data) {
            if (data.status !== "OK") {
                setLogbookStatus("KMZ Exportfehler", "error");
                return;
            }

            monitorExportJob(data.job.id);
        })
        .catch(function(err) {
            console.error(err);
            setLogbookStatus("KMZ Exportfehler", "error");
        });
}

function exportTripKmz() {
    var choice = window.prompt(
        "Törn Export:\n\n1 = letzte 7 Tage\n2 = seit letztem Törn Start",
        "2"
    );

    if (choice === null) {
        setLogbookStatus("Törn Export abgebrochen", "info");
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

    setLogbookStatus("Ungültige Auswahl", "error");
}

function exportTripKmzLastSevenDays() {
    setLogbookStatus("Törn Export 7 Tage startet...", "info");

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
    setLogbookStatus("Törn Export seit Start startet...", "info");

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
                setLogbookStatus(data.message || errorMessage, "error");
                return;
            }

            monitorExportJob(data.job.id);
        })
        .catch(function(err) {
            console.error(err);
            setLogbookStatus(errorMessage, "error");
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
                    setLogbookStatus("Exportstatus Fehler", "error");
                    return;
                }

                var job = data.job;

                if (!job) {
                    clearInterval(timer);
                    setLogbookStatus("Job nicht gefunden", "error");
                    return;
                }

                if (job.status === "RUNNING") {
                    setLogbookStatus("Export läuft...", "info");
                    return;
                }

                clearInterval(timer);

                if (job.status === "OK") {
                    setLogbookStatus("Export fertig", "success");
                    return;
                }

                setLogbookStatus(job.message || "Export fehlgeschlagen", "error");
            })
            .catch(function(err) {
                console.error(err);
                clearInterval(timer);
                setLogbookStatus("Exportstatus Fehler", "error");
            });

        if (pollCount > 60) {
            clearInterval(timer);
            setLogbookStatus("Export Timeout", "error");
        }
    }, 1000);
}

