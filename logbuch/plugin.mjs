export default function initializeLogbuch(avnavApi) {
    if (!avnavApi) {
        throw new Error("Logbuch: AVNav API fehlt");
    }

    const avnav = { api: avnavApi };

    const AVNAV_BASE_URL = new URL(".", import.meta.url)
        .pathname
        .replace(/\/$/, "");

    console.log("logbuch plugin loaded", {
        baseUrl: AVNAV_BASE_URL
    });

    var LOGBUCH_VERSION = "2.0.2";


    function openNativeQuickDialog(event) {
        if (typeof avnavApi.showDialog !== "function") {
            openNativeEntryDialog(event);
            return;
        }

        var id = "logbuchQuick-" + Date.now();

        var html =
            '<div id="' + id + '" class="logbuchNativeQuickDialog">' +
                '<button type="button" data-quick="entry">' +
                    'Neuer Logbucheintrag' +
                '</button>' +
                '<button type="button" data-quick="logbook">' +
                    'Digitales Logbuch öffnen' +
                '</button>' +
            '</div>';

        avnavApi.showDialog({
            title: "Logbuch",
            html: html,
            buttons: [{
                name: "close",
                shortText: "Schließen",
                close: true
            }]
        }, event || {}).then(function(closeDialog) {
            window.setTimeout(function() {
                var box = document.getElementById(id);
                if (!box) return;

                box.addEventListener("click", function(e) {
                    var button = e.target.closest("[data-quick]");
                    if (!button) return;

                    var action = button.getAttribute("data-quick");

                    if (typeof closeDialog === "function") {
                        closeDialog();
                    }

                    window.setTimeout(function() {
                        if (action === "entry") {
                            openNativeEntryDialog();
                        } else {
                            openNativeLogbookDialog();
                        }
                    }, 0);
                });
            }, 0);
        });
    }

    function logbuchStateSwitch(kind, title, offLabel, onLabel) {
        return (
            '<button type="button" ' +
                'class="logbuchStateSwitch" ' +
                'data-logbuch-switch="' + escapeHtml(kind) + '" ' +
                'data-active="0" ' +
                'aria-pressed="false">' +
                '<span class="logbuchStateSwitchTitle">' +
                    escapeHtml(title) +
                '</span>' +
                '<span class="logbuchStateSwitchTrack">' +
                    '<span class="logbuchStateSwitchOff">' +
                        escapeHtml(offLabel) +
                    '</span>' +
                    '<span class="logbuchStateSwitchKnob"></span>' +
                    '<span class="logbuchStateSwitchOn">' +
                        escapeHtml(onLabel) +
                    '</span>' +
                '</span>' +
            '</button>'
        );
    }

    function logbuchAnchorToggle() {
        return (
            '<button type="button" ' +
                'class="logbuchToggleButton ' +
                    'logbuchAnchorToggle ' +
                    'logbuchLocationButton" ' +
                'data-logbuch-location="anchor">' +
                '<span class="logbuchLocationAnchorIcon" ' +
                    'aria-hidden="true">&#9875;</span>' +
                '<span class="logbuchButtonLabel">' +
                    'Festmachen' +
                '</span>' +
            '</button>'
        );
    }

    function updateLogbuchAnchorToggleButtons(root) {
        root = root || document;

        Array.prototype.forEach.call(
            root.querySelectorAll(
                '[data-logbuch-location="anchor"]'
            ),
            function(button) {
                var label = button.querySelector(
                    ".logbuchButtonLabel"
                );

                button.classList.remove(
                    "logbuchStatusActive",
                    "logbuchStatusInactive"
                );
                button.removeAttribute("data-active");
                button.removeAttribute("aria-pressed");

                if (label) {
                    label.textContent = "Festmachen";
                }

            }
        );
    }

    function updateLogbuchStateSwitches(root, state) {
        root = root || document;
        state = state || {
            motor: false,
            sail: false,
            anchor: false
        };

        Array.prototype.forEach.call(
            root.querySelectorAll("[data-logbuch-switch]"),
            function(button) {
                var kind = button.getAttribute("data-logbuch-switch");
                var active = kind === "motor"
                    ? state.motor === true
                    : state.sail === true;

                button.setAttribute("data-active", active ? "1" : "0");
                button.setAttribute("aria-pressed", active ? "true" : "false");
                button.classList.toggle("logbuchStateSwitchActive", active);
            }
        );

        updateLogbuchAnchorToggleButtons(root, state);
    }

    function getLogbuchSwitchState(button) {
        return button &&
            button.getAttribute("data-active") === "1";
    }

    function loadCurrentLogbuchState(callback) {
        fetch(AVNAV_BASE_URL + "/api/list?limit=12")
            .then(function(response) {
                return response.json();
            })
            .then(function(data) {
                var state = deriveLogbuchState(
                    data && data.status === "OK"
                        ? (data.entries || [])
                        : []
                );

                if (typeof callback === "function") {
                    callback(state);
                }
            })
            .catch(function(error) {
                console.error(
                    "Logbuch-Zustand konnte nicht geladen werden",
                    error
                );

                if (typeof callback === "function") {
                    callback({
                        motor: false,
                        sail: false,
                        anchor: false
                    });
                }
            });
    }

    function openSailMotorQuestion(onMotorOffSuccess) {
        var existing = document.getElementById(
            "logbuchSailMotorOverlay"
        );

        if (existing) {
            existing.remove();
        }

        var overlay = document.createElement("div");
        overlay.id = "logbuchSailMotorOverlay";

        overlay.innerHTML =
            '<div class="logbuchExportBox logbuchSailMotorBox">' +
                '<div class="logbuchHeader">' +
                    '<h2>Segel gesetzt</h2>' +
                '</div>' +

                '<div class="logbuchSailMotorText">' +
                    'Soll der Motor ebenfalls ausgeschaltet werden?' +
                '</div>' +

                '<div class="logbuchSailMotorActions">' +
                    '<button type="button" ' +
                        'id="logbuchSailMotorOff" ' +
                        'class="logbuchSailMotorPrimary">' +
                        'Motor ausschalten' +
                    '</button>' +

                    '<button type="button" ' +
                        'id="logbuchSailMotorKeep" ' +
                        'class="logbuchSailMotorSecondary">' +
                        'Bleibt an' +
                    '</button>' +
                '</div>' +
            '</div>';

        document.body.appendChild(overlay);

        function closeQuestion(event) {
            if (event) {
                event.preventDefault();
                event.stopPropagation();
            }

            overlay.remove();
        }

        overlay.addEventListener("click", function(event) {
            if (event.target === overlay) {
                closeQuestion(event);
            }
        }, false);

        document.getElementById(
            "logbuchSailMotorKeep"
        ).addEventListener("click", closeQuestion, false);

        document.getElementById(
            "logbuchSailMotorOff"
        ).addEventListener("click", function(event) {
            closeQuestion(event);
            openLogbuchMotorHoursOverlay(
                onMotorOffSuccess
            );
        }, false);
    }

    function openNativeEntryDialog(event) {
        if (typeof avnavApi.showDialog !== "function") {
            openLogbuchOverlay(event);
            return;
        }

        var dialogId =
            "logbuchNativeEntryDialog-" +
            Date.now() +
            "-" +
            Math.random().toString(36).slice(2);

        var dialogHtml =
            '<div id="' + dialogId + '" class="logbuchNativeEntryDialog">' +

                '<section class="logbuchNativeGroup">' +
                    logbuchStateSwitch(
                        "motor",
                        "Motor",
                        "AUS",
                        "AN"
                    ) +
                '</section>' +

                '<section class="logbuchNativeGroup">' +
                    logbuchStateSwitch(
                        "sail",
                        "Segel",
                        "UNTEN",
                        "GESETZT"
                    ) +
                '</section>' +

                '<section class="logbuchNativeGroup">' +
                    '<h3>Anker</h3>' +
                    '<div class="logbuchNativeAnchorAction">' +
                        logbuchAnchorToggle() +
                    '</div>' +
                '</section>' +

                '<div class="logbuchNativeWideAction">' +
                    '<button type="button" data-logbuch-action="show-note">' +
                        'Freie Notiz' +
                    '</button>' +
                '</div>' +

                '<div data-logbuch-note-area="1" ' +
                    'class="logbuchNativeNoteArea" hidden>' +
                    '<textarea ' +
                        'data-logbuch-note-text="1" ' +
                        'rows="4" ' +
                        'placeholder="Notiz eingeben">' +
                    '</textarea>' +
                    '<div class="logbuchNativeNoteActions">' +
                        '<button type="button" data-logbuch-action="save-note">' +
                            'Notiz speichern' +
                        '</button>' +
                        '<button type="button" data-logbuch-action="cancel-note">' +
                            'Abbrechen' +
                        '</button>' +
                    '</div>' +
                '</div>' +

                '<div class="logbuchNativeWideAction">' +
                    '<button type="button" data-logbuch-action="open-logbook">' +
                        'Digitales Logbuch öffnen' +
                    '</button>' +
                '</div>' +

                '<div data-logbuch-status="1" ' +
                    'class="logbuchNativeStatus" role="status"></div>' +
            '</div>';

        avnavApi.showDialog(
            {
                title: "Logbucheintrag",
                html: dialogHtml,
                buttons: [
                    {
                        name: "close",
                        shortText: "Schließen",
                        longText: "Dialog schließen",
                        close: true
                    }
                ]
            },
            event || {}
        ).then(function(closeDialog) {
            window.setTimeout(function() {
                var container = document.getElementById(dialogId);

                if (!container) {
                    return;
                }

                var statusElement = container.querySelector(
                    '[data-logbuch-status="1"]'
                );
                var noteArea = container.querySelector(
                    '[data-logbuch-note-area="1"]'
                );
                var noteText = container.querySelector(
                    '[data-logbuch-note-text="1"]'
                );
                var statusTimer = null;
                var actionLocked = false;

                loadCurrentLogbuchState(function(state) {
                    updateLogbuchStateSwitches(container, state);
                });

                var actionLabels = {
                    motor_on: "Motor an gespeichert",
                    motor_off: "Motor aus gespeichert",
                    sail_set: "Segel setzen gespeichert",
                    sail_down: "Segel bergen gespeichert",
                    anchor_down: "Anker fallen gespeichert",
                    anchor_up: "Anker auf gespeichert"
                };

                function showStatus(message, isError) {
                    if (!statusElement) {
                        return;
                    }

                    window.clearTimeout(statusTimer);
                    statusElement.textContent = message || "";
                    statusElement.classList.toggle(
                        "logbuchNativeStatusError",
                        Boolean(isError)
                    );

                    if (message) {
                        statusTimer = window.setTimeout(function() {
                            statusElement.textContent = "";
                            statusElement.classList.remove(
                                "logbuchNativeStatusError"
                            );
                        }, 3000);
                    }
                }

                function lockActions() {
                    actionLocked = true;

                    window.setTimeout(function() {
                        actionLocked = false;
                    }, 700);
                }

                container.addEventListener("click", function(clickEvent) {
                    var button = clickEvent.target.closest(
                        "[data-logbuch-action], " +
                        "[data-logbuch-switch], " +
                        "[data-logbuch-location]"
                    );

                    if (!button || !container.contains(button)) {
                        return;
                    }

                    var locationType = button.getAttribute(
                        "data-logbuch-location"
                    );

                    if (locationType === "anchor") {
                        clickEvent.preventDefault();
                        clickEvent.stopPropagation();

                        if (actionLocked) {
                            return;
                        }

                        lockActions();

                        saveLogbuchEntry(
                            "location",
                            function() {
                                showStatus(
                                    "Festmachen gespeichert"
                                );
                            }
                        );
                        return;
                    }

                    var switchKind = button.getAttribute(
                        "data-logbuch-switch"
                    );

                    if (switchKind) {
                        clickEvent.preventDefault();
                        clickEvent.stopPropagation();

                        if (actionLocked) {
                            return;
                        }

                        var active = getLogbuchSwitchState(button);

                        if (switchKind === "motor") {
                            if (active) {
                                openLogbuchMotorHoursOverlay(function() {
                                    loadCurrentLogbuchState(function(state) {
                                        updateLogbuchStateSwitches(
                                            container,
                                            state
                                        );
                                    });
                                });
                                return;
                            }

                            lockActions();
                            saveLogbuchEntry("motor_on", function() {
                                loadCurrentLogbuchState(function(state) {
                                    updateLogbuchStateSwitches(
                                        container,
                                        state
                                    );
                                });
                            });
                            return;
                        }

                        if (switchKind === "sail") {
                            lockActions();

                            if (active) {
                                saveLogbuchEntry("sail_down", function() {
                                    loadCurrentLogbuchState(function(state) {
                                        updateLogbuchStateSwitches(
                                            container,
                                            state
                                        );
                                    });
                                });
                                return;
                            }

                            var motorWasRunning =
                                container.querySelector(
                                    '[data-logbuch-switch="motor"]'
                                );
                            motorWasRunning = getLogbuchSwitchState(
                                motorWasRunning
                            );

                            saveLogbuchEntry("sail_set", function() {
                                loadCurrentLogbuchState(function(state) {
                                    updateLogbuchStateSwitches(
                                        container,
                                        state
                                    );
                                });

                                if (motorWasRunning) {
                                    openSailMotorQuestion(function() {
                                        loadCurrentLogbuchState(function(state) {
                                            updateLogbuchStateSwitches(
                                                container,
                                                state
                                            );
                                        });
                                    });
                                }
                            });
                            return;
                        }

                        return;
                    }

                    var action = button.getAttribute(
                        "data-logbuch-action"
                    );

                    if (action === "show-note") {
                        noteArea.hidden = false;
                        noteText.focus();
                        return;
                    }

                    if (action === "cancel-note") {
                        noteText.value = "";
                        noteArea.hidden = true;
                        showStatus("");
                        return;
                    }

                    if (action === "save-note") {
                        var text = noteText.value.trim();

                        if (!text) {
                            showStatus(
                                "Bitte zuerst eine Notiz eingeben.",
                                true
                            );
                            noteText.focus();
                            return;
                        }

                        if (actionLocked) {
                            return;
                        }

                        lockActions();
                        saveLogbuchEntryWithText("manual", text);
                        noteText.value = "";
                        noteArea.hidden = true;
                        showStatus("Notiz gespeichert");
                        return;
                    }

                    if (action === "open-logbook") {
                        if (typeof closeDialog === "function") {
                            closeDialog();
                        }

                        window.setTimeout(function() {
                            openNativeLogbookDialog();
                        }, 0);
                        return;
                    }

                    if (!Object.prototype.hasOwnProperty.call(
                        actionLabels,
                        action
                    )) {
                        return;
                    }

                    if (actionLocked) {
                        return;
                    }

                    lockActions();
                    saveLogbuchEntry(action);
                    showStatus(actionLabels[action]);
                });
            }, 0);
        }).catch(function(error) {
            console.error(
                "Logbuch-Eintragsdialog konnte nicht geöffnet werden",
                error
            );
        });
    }

    function openNativeLogbookDialog(event) {
        if (typeof avnavApi.showDialog !== "function") {
            window.location.href = AVNAV_BASE_URL + "/index.html";
            return;
        }

        var logbookUrl = AVNAV_BASE_URL + "/index.html";

        avnavApi.showDialog(
            {
                title: "Digitales Logbuch",
                fullscreen: true,
                html:
                    '<iframe ' +
                        'src="' + logbookUrl + '" ' +
                        'title="Digitales Logbuch" ' +
                        'style="' +
                            'display:block;' +
                            'width:100%;' +
                            'height:calc(100vh - 120px);' +
                            'border:0;' +
                            'background:#fff;' +
                        '">' +
                    '</iframe>',
                buttons: [
                    {
                        name: "close",
                        shortText: "Schließen",
                        longText: "Logbuch schließen",
                        close: true
                    }
                ]
            },
            event || {}
        ).catch(function(error) {
            console.error(
                "Logbuch-Seite konnte nicht geöffnet werden",
                error
            );
        });
    }

    function registerModernLogbuchButtons() {
        if (typeof avnavApi.registerUserButton !== "function") {
            return;
        }

        avnavApi.registerUserButton(
            {
                name: "logbuch-entry-nav",
                shortText: "Logbucheintrag",
                longText: "Logbucheintrag",
                icon: "icons/logbucheintrag.png",
                onClick: function(event) {
                    openNativeQuickDialog(event);
                }
            },
            "navpage"
        );
    }

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
        { name: "logbuch_b_festmachen", caption: "Festmachen", type: "location", icon: "anchor-down" }
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
                            '<div class="logbuchStateSwitchCell">' +
                                logbuchStateSwitch(
                                    "motor",
                                    "Motor",
                                    "AUS",
                                    "AN"
                                ) +
                            '</div>' +

                            '<div class="logbuchActionLabel"><span>Segel</span></div>' +
                            '<div class="logbuchStateSwitchCell">' +
                                logbuchStateSwitch(
                                    "sail",
                                    "Segel",
                                    "UNTEN",
                                    "GESETZT"
                                ) +
                            '</div>' +

                            '<div class="logbuchActionLabel"><span>Anker</span></div>' +
                            '<div class="logbuchAnchorToggleCell">' +
                                logbuchAnchorToggle() +
                            '</div>' +

                        '</div>' +

                    '</div>' +

                    '<div class="logbuchHistoryPane">' +

                        '<div id="logbuchStatus" class="logbuchStatus logbuchStatus-info">Bereit</div>' +

                        '<div class="logbuchExportRow">' +

                            '<button type="button" id="logbuchTripStart" class="logbuchMiniButton">' +
                                'Törn Start' +
                            '</button>' +

                            '<button type="button" id="logbuchTripEnd" class="logbuchMiniButton">' +
                                'Törn Ende' +
                            '</button>' +

                            '<button type="button" id="logbuchOpenFullPage" class="logbuchMiniButton logbuchOpenFullPage">' +
                                'Digitales Logbuch' +
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

        overlay.querySelectorAll(
            "button[data-logbuch-location]"
        ).forEach(function(button) {
            button.addEventListener("click", function(event) {
                event.preventDefault();
                event.stopPropagation();

                saveLogbuchEntry("location");
            }, false);
        });

        overlay.querySelectorAll(
            "button[data-logbuch-switch]"
        ).forEach(function(button) {
            button.addEventListener("click", function(event) {
                event.preventDefault();
                event.stopPropagation();

                var kind = button.getAttribute(
                    "data-logbuch-switch"
                );
                var active = getLogbuchSwitchState(button);

                if (kind === "motor") {
                    if (active) {
                        openLogbuchMotorHoursOverlay();
                    } else {
                        saveLogbuchEntry("motor_on");
                    }
                    return;
                }

                if (kind === "sail") {
                    if (active) {
                        saveLogbuchEntry("sail_down");
                        return;
                    }

                    var motorButton = overlay.querySelector(
                        '[data-logbuch-switch="motor"]'
                    );
                    var motorWasRunning =
                        getLogbuchSwitchState(motorButton);

                    saveLogbuchEntry("sail_set", function() {
                        if (motorWasRunning) {
                            openSailMotorQuestion();
                        }
                    });
                }
            }, false);
        });

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

        document.getElementById("logbuchOpenFullPage").addEventListener(
            "click",
            function(e) {
                e.preventDefault();
                e.stopPropagation();
                window.location.href = AVNAV_BASE_URL + "/index.html";
            },
            false
        );

        loadLogbuchEntries();
    }


    registerModernLogbuchButtons();
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

        updateLogbuchStateSwitches(document, state);
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

    function saveLogbuchEntry(type, onSuccess) {
        var textField = document.getElementById("logbuchText");
        var text = textField ? (textField.value || "") : "";

        saveLogbuchEntryWithText(
            type,
            text,
            false,
            onSuccess
        );
    }

    function saveLogbuchEntryWithText(
        type,
        text,
        force,
        onSuccess
    ) {
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

                    if (typeof onSuccess === "function") {
                        onSuccess(data);
                    }

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

        /*
         * Eine bereits sichtbare Liste während des Nachladens nicht
         * entfernen. Das bisherige Ersetzen durch "Lade Einträge..."
         * ließ den Inhaltsbereich kurz zusammenfallen und verursachte
         * ein sichtbares Springen des gesamten Overlays.
         */
        var hasRenderedEntries =
            target.querySelector(".logbuchEntry") !== null;

        if (!hasRenderedEntries) {
            target.innerHTML = "Lade Einträge...";
        }

        target.setAttribute("aria-busy", "true");

        fetch(AVNAV_BASE_URL + "/api/list?limit=12")
            .then(function(response) {
                return response.json();
            })
            .then(function(data) {
                target.removeAttribute("aria-busy");

                if (data.status !== "OK") {
                    if (!hasRenderedEntries) {
                        target.innerHTML =
                            "Einträge konnten nicht geladen werden.";
                    }

                    setLogbuchStatus(
                        "Einträge konnten nicht aktualisiert werden",
                        "warning"
                    );
                    return;
                }

                var entries = data.entries || [];
                updateLogbuchStatusButtons(deriveLogbuchState(entries));
                renderLogbuchEntries(entries);
            })
            .catch(function(err) {
                target.removeAttribute("aria-busy");

                if (!hasRenderedEntries) {
                    target.innerHTML =
                        "Fehler beim Laden der Einträge.";
                }

                setLogbuchStatus(
                    "Fehler beim Aktualisieren der Einträge",
                    "error"
                );
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
            location: "anchor-down",
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
            location: "Festmachen",
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


    function openLogbuchMotorHoursOverlay(onSuccess) {
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
            saveLogbuchEntryWithText(
                "motor_off",
                text,
                false,
                onSuccess
            );
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

}
