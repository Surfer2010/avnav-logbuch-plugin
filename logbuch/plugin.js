console.log("logbuch plugin loaded");

var LOGBUCH_VERSION = "2.0.0";

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
                '<button type="button" class="logbuchOpenButton" data-logbuch-open="1">' +
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
                    '<button type="button" class="logbuchDirectButton" data-logbuch-direct="' + widget.type + '" aria-label="' + escapeHtml(widget.caption) + '">' +
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

    if (target.getAttribute("data-logbuch-open") === "1") {
        ev.preventDefault();
        ev.stopPropagation();
        openLogbuchOverlay();
        return;
    }

    var directType = target.getAttribute("data-logbuch-direct");

    if (!directType && target.closest) {
        var directButton = target.closest("[data-logbuch-direct]");
        if (directButton) {
            directType = directButton.getAttribute("data-logbuch-direct");
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
                '<button type="button" id="logbuchCloseTop" class="logbuchCloseButton">×</button>' +
            '</div>' +

            '<div class="logbuchMainLayout">' +

                '<div class="logbuchInputPane">' +

                    '<div class="logbuchActionGrid">' +

                        '<div class="logbuchActionLabel"><span>Motor</span></div>' +
                        logbuchButton("motor_on", "Motor an", "motor-on", "logbuchMotorOn") +
                        logbuchButton("motor_off", "Motor aus", "motor-off", "logbuchMotorOff") +

                        '<div class="logbuchActionLabel"><span>Segel</span></div>' +
                        logbuchButton("sail_set", "Segel setzen", "sail-set", "logbuchSailOn") +
                        logbuchButton("sail_down", "Segel einholen", "sail-down", "logbuchSailOff") +

                        '<div class="logbuchActionLabel"><span>Anker</span></div>' +
                        logbuchButton("anchor_down", "Anker ab", "anchor-down", "logbuchAnchorOn") +
                        logbuchButton("anchor_up", "Anker auf", "anchor-up", "logbuchAnchorOff") +

                    '</div>' +

                '</div>' +

                '<div class="logbuchHistoryPane">' +

                    '<div id="logbuchStatus" class="logbuchStatus logbuchStatus-info">Bereit</div>' +

                    '<div class="logbuchExportRow">' +

                        '<button type="button" id="logbuchOpenExport" class="logbuchMiniButton">' +
                            'Export' +
                        '</button>' +

                        '<button type="button" id="logbuchTripStart" class="logbuchMiniButton">' +
                            'Törn Start' +
                        '</button>' +

                        '<button type="button" id="logbuchTripEnd" class="logbuchMiniButton">' +
                            'Törn Ende' +
                        '</button>' +

                    '</div>' +

                    '<div class="logbuchSectionTitle logbuchHistoryTitle">Anmerkung / Freitext</div>' +

                    '<div class="logbuchTextRow">' +

                        '<textarea id="logbuchText" readonly placeholder="Freitext / Bemerkung eingeben..." autocomplete="off" autocorrect="off" autocapitalize="sentences" spellcheck="false"></textarea>' +

                        '<button type="button" id="logbuchSaveManual" class="logbuchVerticalSave">' +
                            '<span>Speichern</span>' +
                        '</button>' +

                    '</div>' +

                    '<div class="logbuchSectionTitle">Letzte Einträge</div>' +
                    '<div id="logbuchEntries" class="logbuchEntries">Lade Einträge...</div>' +

                '</div>' +

            '</div>' +

            '<div class="logbuchVersion">v' + escapeHtml(LOGBUCH_VERSION) + '</div>' +

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

    var textField = document.getElementById("logbuchText");
    // Kein automatischer Fokus:
    // Auf Tablets würde sonst sofort die Bildschirmtastatur öffnen.
    if (document.activeElement && document.activeElement.blur) {
        document.activeElement.blur();
    }

    if (textField) {
        textField.addEventListener("pointerdown", function() {
            textField.removeAttribute("readonly");
        }, false);

        textField.addEventListener("click", function() {
            textField.removeAttribute("readonly");
        }, false);
    }

    overlay.querySelectorAll("button[data-type]").forEach(function(btn) {
        btn.addEventListener("click", function(e) {
            e.preventDefault();
            e.stopPropagation();

            var type = btn.getAttribute("data-type");
            if (type === "motor_off") {
                openLogbuchMotorHoursOverlay();
                return;
            }

            saveLogbuchEntry(type);
        }, false);
    });

    document.getElementById("logbuchSaveManual").addEventListener("click", function(e) {
        e.preventDefault();
        e.stopPropagation();
        saveLogbuchEntry("manual");
    }, false);
    document.getElementById("logbuchCloseTop").addEventListener("click", function(e) {
        e.preventDefault();
        e.stopPropagation();
        overlay.remove();
    }, false);

    document.getElementById("logbuchOpenExport").addEventListener("click", function(e) {
        e.preventDefault();
        e.stopPropagation();
        openLogbuchExportOverlay();
    }, false);

    document.getElementById("logbuchTripStart").addEventListener("click", function(e) {
        e.preventDefault();
        e.stopPropagation();
        saveLogbuchEntry("trip_start");
    }, false);

    document.getElementById("logbuchTripEnd").addEventListener("click", function(e) {
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

function isStatusEvent(type) {
    return [
        "motor_on",
        "motor_off",
        "sail_set",
        "sail_down",
        "anchor_down",
        "anchor_up"
    ].indexOf(type) >= 0;
}



function deriveLogbuchState(entries) {
    var state = {
        motor: false,
        sail: false,
        anchor: false
    };

    (entries || []).forEach(function(entry) {
        if (entry && entry.state) {
            state.motor = !!entry.state.motor;
            state.sail = !!entry.state.sail;
            state.anchor = !!entry.state.anchor;
            return;
        }

        var type = entry ? entry.event_type : "";
        if (type === "motor_on") state.motor = true;
        if (type === "motor_off") state.motor = false;
        if (type === "sail_set") state.sail = true;
        if (type === "sail_down") state.sail = false;
        if (type === "anchor_down") state.anchor = true;
        if (type === "anchor_up") state.anchor = false;
    });

    return state;
}

function setLogbuchButtonActive(selector, active) {
    var btn = document.querySelector(selector);
    if (!btn) {
        return;
    }

    btn.classList.toggle("logbuchStatusActive", !!active);
    btn.classList.toggle("logbuchStatusInactive", !active);
}

function updateLogbuchStatusButtons(state) {
    state = state || {
        motor: false,
        sail: false,
        anchor: false
    };

    setLogbuchButtonActive('[data-type="motor_on"]', state.motor === true);
    setLogbuchButtonActive('[data-type="motor_off"]', state.motor !== true);

    setLogbuchButtonActive('[data-type="sail_set"]', state.sail === true);
    setLogbuchButtonActive('[data-type="sail_down"]', state.sail !== true);

    setLogbuchButtonActive('[data-type="anchor_down"]', state.anchor === true);
    setLogbuchButtonActive('[data-type="anchor_up"]', state.anchor !== true);
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

            if (isStatusEvent(type)) {
                openLogbuchForceOverlay(type, "", data.message || "Der aktuelle Status passt nicht zum Ereignis.");
                return;
            }

            console.warn("direct logbuch warning", data);
        })
        .catch(function(err) {
            console.error("direct logbuch error", err);
        });
}

function saveLogbuchEntry(type) {
    var textField = document.getElementById("logbuchText");
    var text = textField ? (textField.value || "") : "";

    saveLogbuchEntryWithText(type, text, false);
}

function saveLogbuchEntryWithText(type, text, force) {
    setLogbuchStatus("Speichere...", "info");

    var url =
        AVNAV_BASE_URL +
        "/api/add?type=" +
        encodeURIComponent(type) +
        "&text=" +
        encodeURIComponent(text || "");

    if (force) {
        url += "&force=1";
    }

    fetch(url)
        .then(function(response) {
            return response.json();
        })
        .then(function(data) {
            if (data.status === "OK") {
                setLogbuchStatus("Gespeichert: " + readableEventType(type), "success");

                var textField = document.getElementById("logbuchText");
                if (textField) {
                    textField.value = "";
                    if (document.activeElement && document.activeElement.blur) {
                        document.activeElement.blur();
                    }
                }

                loadLogbuchEntries();

                console.log("logbuch saved", data);
                return;
            }

            if (!force && isStatusEvent(type)) {
                openLogbuchForceOverlay(type, text, data.message || "Der aktuelle Status passt nicht zum Ereignis.");
                return;
            }

            setLogbuchStatus(data.message || "Aktion nicht möglich", "warning");
            console.warn("logbuch warning", data);
        })
        .catch(function(err) {
            setLogbuchStatus("Fehler beim Speichern", "error");
            console.error("logbuch request error", err);
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

            var entries = data.entries || [];
            updateLogbuchStatusButtons(deriveLogbuchState(entries));
            renderLogbuchEntries(entries);
        })
        .catch(function(err) {
            target.innerHTML = "Fehler beim Laden der Einträge.";
            console.error("logbuch list error", err);
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



function todayDateString() {
    var now = new Date();
    var year = now.getFullYear();
    var month = String(now.getMonth() + 1).padStart(2, "0");
    var day = String(now.getDate()).padStart(2, "0");
    return year + "-" + month + "-" + day;
}

function isValidDateString(value) {
    if (!/^\d{4}-\d{2}-\d{2}$/.test(value || "")) {
        return false;
    }

    var parts = value.split("-");
    var date = new Date(Number(parts[0]), Number(parts[1]) - 1, Number(parts[2]));

    return (
        date.getFullYear() === Number(parts[0]) &&
        date.getMonth() === Number(parts[1]) - 1 &&
        date.getDate() === Number(parts[2])
    );
}

function openLogbuchExportOverlay() {
    var existing = document.getElementById("logbuchExportOverlay");
    if (existing) {
        existing.remove();
    }

    var today = todayDateString();

    var overlay = document.createElement("div");
    overlay.id = "logbuchExportOverlay";

    overlay.innerHTML =
        '<div class="logbuchExportBox">' +
            '<div class="logbuchHeader">' +
                '<h2>Export</h2>' +
                '<button type="button" id="logbuchExportCloseTop" class="logbuchCloseButton">×</button>' +
            '</div>' +

            '<div class="logbuchExportForm">' +
                '<label for="logbuchExportFrom">Von</label>' +
                '<input type="date" id="logbuchExportFrom" value="' + today + '">' +

                '<label for="logbuchExportTo">Bis</label>' +
                '<input type="date" id="logbuchExportTo" value="' + today + '">' +

                '<label for="logbuchExportFormat">Format</label>' +
                '<select id="logbuchExportFormat">' +
                    '<option value="kmz">KMZ</option>' +
                    '<option value="html">HTML-Tagesbericht</option>' +
                '</select>' +

                '<div class="logbuchExportHint">' +
                    'HTML ist nur für einen einzelnen Tag verfügbar.' +
                '</div>' +

                '<div class="logbuchExportButtons">' +
                    '<button type="button" id="logbuchExportRun" class="logbuchMiniButton">Exportieren</button>' +
                    '<button type="button" id="logbuchExportCancel" class="logbuchMiniButton logbuchSecondaryButton">Zurück</button>' +
                '</div>' +
            '</div>' +
        '</div>';

    document.body.appendChild(overlay);

    overlay.addEventListener("click", function(e) {
        if (e.target === overlay) {
            e.preventDefault();
            e.stopPropagation();
            overlay.remove();
        }
    }, false);

    var box = overlay.querySelector(".logbuchExportBox");
    if (box) {
        box.addEventListener("click", function(e) {
            e.stopPropagation();
        }, false);
    }

    document.getElementById("logbuchExportCloseTop").addEventListener("click", function(e) {
        e.preventDefault();
        e.stopPropagation();
        overlay.remove();
    }, false);

    document.getElementById("logbuchExportCancel").addEventListener("click", function(e) {
        e.preventDefault();
        e.stopPropagation();
        overlay.remove();
    }, false);

    document.getElementById("logbuchExportRun").addEventListener("click", function(e) {
        e.preventDefault();
        e.stopPropagation();

        var fromDate = document.getElementById("logbuchExportFrom").value;
        var toDate = document.getElementById("logbuchExportTo").value;
        var format = document.getElementById("logbuchExportFormat").value;

        if (!isValidDateString(fromDate) || !isValidDateString(toDate)) {
            setLogbuchStatus("Ungültiges Exportdatum", "error");
            return;
        }

        if (fromDate > toDate) {
            setLogbuchStatus("Exportdatum: Von liegt nach Bis", "error");
            return;
        }

        if (format === "html" && fromDate !== toDate) {
            setLogbuchStatus("HTML-Export ist nur für einen einzelnen Tag verfügbar", "error");
            return;
        }

        overlay.remove();

        if (format === "html") {
            exportTodayHtml(fromDate);
            return;
        }

        if (fromDate === toDate) {
            exportTodayKmz(fromDate);
            return;
        }

        exportTripKmz(fromDate, toDate);
    }, false);
}


function openLogbuchMotorHoursOverlay() {
    var existing = document.getElementById("logbuchMotorHoursOverlay");
    if (existing) {
        existing.remove();
    }

    var overlay = document.createElement("div");
    overlay.id = "logbuchMotorHoursOverlay";

    overlay.innerHTML =
        '<div class="logbuchExportBox">' +
            '<div class="logbuchHeader">' +
                '<h2>Motorstunden</h2>' +
                '<button type="button" id="logbuchMotorHoursCloseTop" class="logbuchCloseButton">×</button>' +
            '</div>' +

            '<div class="logbuchExportForm">' +
                '<label for="logbuchMotorHoursInput">Stunden</label>' +
                '<input type="number" id="logbuchMotorHoursInput" inputmode="decimal" min="0" step="0.1" placeholder="optional">' +

                '<div class="logbuchExportHint">' +
                    'Leere Eingabe ist erlaubt. Der Eintrag wird als Motor aus gespeichert.' +
                '</div>' +

                '<div class="logbuchExportButtons">' +
                    '<button type="button" id="logbuchMotorHoursSave" class="logbuchMiniButton">Speichern</button>' +
                    '<button type="button" id="logbuchMotorHoursCancel" class="logbuchMiniButton logbuchSecondaryButton">Abbrechen</button>' +
                '</div>' +
            '</div>' +
        '</div>';

    document.body.appendChild(overlay);

    overlay.addEventListener("click", function(e) {
        if (e.target === overlay) {
            e.preventDefault();
            e.stopPropagation();
            overlay.remove();
        }
    }, false);

    var box = overlay.querySelector(".logbuchExportBox");
    if (box) {
        box.addEventListener("click", function(e) {
            e.stopPropagation();
        }, false);
    }

    document.getElementById("logbuchMotorHoursCloseTop").addEventListener("click", function(e) {
        e.preventDefault();
        e.stopPropagation();
        overlay.remove();
    }, false);

    document.getElementById("logbuchMotorHoursCancel").addEventListener("click", function(e) {
        e.preventDefault();
        e.stopPropagation();
        overlay.remove();
    }, false);

    document.getElementById("logbuchMotorHoursSave").addEventListener("click", function(e) {
        e.preventDefault();
        e.stopPropagation();

        var input = document.getElementById("logbuchMotorHoursInput");
        var hours = input ? String(input.value || "").trim() : "";

        var textField = document.getElementById("logbuchText");
        var currentText = textField ? String(textField.value || "").trim() : "";
        var text = currentText;

        if (hours !== "") {
            text = "Motorstunden: " + hours;
            if (currentText !== "") {
                text += " | " + currentText;
            }
        }

        overlay.remove();
        saveLogbuchEntryWithText("motor_off", text);
    }, false);
}

function openLogbuchForceOverlay(type, text, message) {
    var existing = document.getElementById("logbuchForceOverlay");
    if (existing) {
        existing.remove();
    }

    var overlay = document.createElement("div");
    overlay.id = "logbuchForceOverlay";

    overlay.innerHTML =
        '<div class="logbuchExportBox">' +
            '<div class="logbuchHeader">' +
                '<h2>Warnung</h2>' +
                '<button type="button" id="logbuchForceCloseTop" class="logbuchCloseButton">×</button>' +
            '</div>' +

            '<div class="logbuchExportForm">' +
                '<div class="logbuchExportHint">' +
                    escapeHtml(message || "Der aktuelle Status passt nicht zum Ereignis.") +
                    '<br><br>Trotzdem als Nachtrag speichern?' +
                '</div>' +

                '<div class="logbuchExportButtons">' +
                    '<button type="button" id="logbuchForceSave" class="logbuchMiniButton">Trotzdem speichern</button>' +
                    '<button type="button" id="logbuchForceCancel" class="logbuchMiniButton logbuchSecondaryButton">Abbrechen</button>' +
                '</div>' +
            '</div>' +
        '</div>';

    document.body.appendChild(overlay);

    function closeForceOverlay(e) {
        if (e) {
            e.preventDefault();
            e.stopPropagation();
        }
        overlay.remove();
    }

    overlay.addEventListener("click", function(e) {
        if (e.target === overlay) {
            closeForceOverlay(e);
        }
    }, false);

    var box = overlay.querySelector(".logbuchExportBox");
    if (box) {
        box.addEventListener("click", function(e) {
            e.stopPropagation();
        }, false);
    }

    document.getElementById("logbuchForceCloseTop").addEventListener("click", closeForceOverlay, false);
    document.getElementById("logbuchForceCancel").addEventListener("click", closeForceOverlay, false);

    document.getElementById("logbuchForceSave").addEventListener("click", function(e) {
        e.preventDefault();
        e.stopPropagation();
        overlay.remove();
        saveLogbuchEntryWithText(type, text, true);
    }, false);
}

function exportTodayHtml(date) {
    setLogbuchStatus("HTML Export startet...", "info");

    startExportRequest(
        AVNAV_BASE_URL + "/api/exportHtml?date=" + encodeURIComponent(date),
        "HTML Exportfehler",
        true
    );
}

function exportTodayKmz(date) {
    setLogbuchStatus("KMZ Export startet...", "info");

    var url = AVNAV_BASE_URL + "/api/exportKmz";
    if (date) {
        url += "?date=" + encodeURIComponent(date);
    }

    fetch(url)
        .then(function(response) {
            return response.json();
        })
        .then(function(data) {
            if (data.status !== "OK") {
                setLogbuchStatus("KMZ Exportfehler", "error");
                return;
            }

            monitorExportJob(data.job.id, downloadWhenReady === true);
        })
        .catch(function(err) {
            console.error(err);
            setLogbuchStatus("KMZ Exportfehler", "error");
        });
}

function exportTripKmz(fromDate, toDate) {
    setLogbuchStatus("Törn Export startet...", "info");

    var url =
        AVNAV_BASE_URL +
        "/api/exportTripKmz?from=" +
        encodeURIComponent(fromDate) +
        "&to=" +
        encodeURIComponent(toDate);

    startExportRequest(url, "Törn Exportfehler");
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

function startExportRequest(url, errorMessage, downloadWhenReady) {
    fetch(url)
        .then(function(response) {
            return response.json();
        })
        .then(function(data) {
            if (data.status !== "OK") {
                setLogbuchStatus(data.message || errorMessage, "error");
                return;
            }

            monitorExportJob(data.job.id, downloadWhenReady);
        })
        .catch(function(err) {
            console.error(err);
            setLogbuchStatus(errorMessage, "error");
        });
}

function monitorExportJob(jobId, downloadWhenReady) {
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
                    if (downloadWhenReady && job.downloadUrl) {
                        var link = document.createElement("a");
                        link.href = job.downloadUrl;
                        link.download = job.downloadName || "logbuch.html";
                        link.style.display = "none";
                        document.body.appendChild(link);
                        link.click();
                        link.remove();
                    }
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

