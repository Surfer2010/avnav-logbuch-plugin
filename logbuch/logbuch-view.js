"use strict";

const AVNAV_BASE_URL = window.location.pathname
    .replace(/\/index\.html$/, "")
    .replace(/\/$/, "");

const EVENT_TYPES = {
    motor_on: {
        icon: "⚙",
        title: "Motor an"
    },
    motor_off: {
        icon: "⚙",
        title: "Motor aus"
    },
    sail_set: {
        icon: "⛵",
        title: "Segel gesetzt"
    },
    sail_down: {
        icon: "⛵",
        title: "Segel eingeholt"
    },
    anchor_down: {
        icon: "⚓",
        title: "Anker gefallen"
    },
    anchor_up: {
        icon: "⚓",
        title: "Anker auf"
    },
    trip_start: {
        icon: "▶",
        title: "Törn gestartet"
    },
    trip_end: {
        icon: "■",
        title: "Törn beendet"
    },
    manual: {
        icon: "✎",
        title: "Logbucheintrag"
    }
};

const dayList = document.getElementById("day-list");
const dayNavigation = document.getElementById("day-navigation");
const dialog = document.getElementById("event-dialog");
const dialogContent = document.getElementById("dialog-content");
const dialogEditButton = document.getElementById("dialog-edit-button");
const dialogSaveButton = document.getElementById("dialog-save-button");
const dialogForceSaveButton = document.getElementById(
    "dialog-force-save-button"
);
const dialogDeleteButton = document.getElementById(
    "dialog-delete-button"
);
const dialogConfirmDeleteButton = document.getElementById(
    "dialog-confirm-delete-button"
);
const dialogForceDeleteButton = document.getElementById(
    "dialog-force-delete-button"
);
const dialogCancelEditButton = document.getElementById(
    "dialog-cancel-edit-button"
);
const dialogCloseButton = document.getElementById("dialog-close-button");
const dialogDuplicateButton = document.getElementById(
    "dialog-duplicate-button"
);
const dialogBeforeButton = document.getElementById(
    "dialog-before-button"
);
const dialogAfterButton = document.getElementById(
    "dialog-after-button"
);
const sidebar = document.getElementById("sidebar");
const menuToggle = document.getElementById("menu-toggle");
const statusText = document.getElementById("status-text");

let navigationDays = [];
let selectedDate = null;
let activeEntry = null;
let dialogMode = "view";
let dialogBusy = false;
let pendingForcedUpdate = null;
let pendingForcedDelete = null;

function getEventPresentation(eventType) {
    return EVENT_TYPES[eventType] || {
        icon: "•",
        title: eventType || "Unbekanntes Ereignis"
    };
}

function escapeHtml(value) {
    return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function formatTimestamp(timestamp) {
    if (!timestamp) {
        return "--:--";
    }

    const date = new Date(timestamp);

    if (Number.isNaN(date.getTime())) {
        return timestamp;
    }

    return new Intl.DateTimeFormat("de-DE", {
        hour: "2-digit",
        minute: "2-digit"
    }).format(date);
}

function formatPosition(entry) {
    if (
        entry.lat === null ||
        entry.lat === undefined ||
        entry.lon === null ||
        entry.lon === undefined
    ) {
        return null;
    }

    const lat = Number(entry.lat);
    const lon = Number(entry.lon);

    if (!Number.isFinite(lat) || !Number.isFinite(lon)) {
        return null;
    }

    return `${lat.toFixed(5)}, ${lon.toFixed(5)}`;
}

function normalizeEntry(entry) {
    const presentation = getEventPresentation(entry.event_type);

    return {
        ...entry,
        type: entry.event_type || "unknown",
        icon: presentation.icon,
        title: presentation.title,
        time: formatTimestamp(entry.timestamp),
        comment: entry.text || "Kein Kommentar vorhanden.",
        position: formatPosition(entry)
    };
}

function setStatus(text) {
    statusText.textContent = text;
}

function setDialogBusy(isBusy) {
    dialogBusy = isBusy;

    dialogSaveButton.disabled = isBusy;
    dialogForceSaveButton.disabled = isBusy;
    dialogDeleteButton.disabled = isBusy;
    dialogConfirmDeleteButton.disabled = isBusy;
    dialogForceDeleteButton.disabled = isBusy;
    dialogCancelEditButton.disabled = isBusy;
    dialogEditButton.disabled = isBusy;
    dialogDuplicateButton.disabled = isBusy;
    dialogBeforeButton.disabled = isBusy;
    dialogAfterButton.disabled = isBusy;
    dialogCloseButton.disabled = isBusy;

    const fields = dialogContent.querySelectorAll(
        "input, select, textarea, button"
    );

    fields.forEach(field => {
        field.disabled = isBusy;
    });
}

function resetDialogActions() {
    dialogEditButton.hidden = false;
    dialogDeleteButton.hidden = false;
    dialogSaveButton.hidden = true;
    dialogForceSaveButton.hidden = true;
    dialogConfirmDeleteButton.hidden = true;
    dialogForceDeleteButton.hidden = true;
    dialogCancelEditButton.hidden = true;
    dialogDuplicateButton.hidden = false;
    dialogBeforeButton.hidden = false;
    dialogAfterButton.hidden = false;
    dialogCloseButton.hidden = false;

    pendingForcedUpdate = null;
    pendingForcedDelete = null;
    setDialogBusy(false);
}

function setEditDialogActions() {
    dialogEditButton.hidden = true;
    dialogDeleteButton.hidden = true;
    dialogSaveButton.hidden = false;
    dialogForceSaveButton.hidden = true;
    dialogConfirmDeleteButton.hidden = true;
    dialogForceDeleteButton.hidden = true;
    dialogCancelEditButton.hidden = false;
    dialogDuplicateButton.hidden = true;
    dialogBeforeButton.hidden = true;
    dialogAfterButton.hidden = true;
    dialogCloseButton.hidden = true;

    pendingForcedUpdate = null;
    pendingForcedDelete = null;
    setDialogBusy(false);
}

function setDeleteDialogActions(showForce = false) {
    dialogEditButton.hidden = true;
    dialogDeleteButton.hidden = true;
    dialogSaveButton.hidden = true;
    dialogForceSaveButton.hidden = true;
    dialogConfirmDeleteButton.hidden = showForce;
    dialogForceDeleteButton.hidden = !showForce;
    dialogCancelEditButton.hidden = false;
    dialogDuplicateButton.hidden = true;
    dialogBeforeButton.hidden = true;
    dialogAfterButton.hidden = true;
    dialogCloseButton.hidden = true;

    setDialogBusy(false);
}

function renderNavigation() {
    dayNavigation.replaceChildren();

    navigationDays.forEach(day => {
        const link = document.createElement("a");
        const isActive = day.date === selectedDate;

        link.className = "nav-link";

        if (isActive) {
            link.classList.add("active");
            link.setAttribute("aria-current", "page");
        }

        link.href = `#day-${day.date}`;
        link.innerHTML = `
            <span>${escapeHtml(day.weekday)} ${escapeHtml(day.title)}</span>
            <span class="nav-count">${escapeHtml(day.count)}</span>
        `;

        link.addEventListener("click", async event => {
            event.preventDefault();

            try {
                await loadDay(day.date);
                sidebar.classList.remove("open");
            } catch (error) {
                console.error("Tag konnte nicht geladen werden", error);
                setStatus("Fehler beim Laden des Logbuchtages");
            }
        });

        dayNavigation.appendChild(link);
    });
}

function createEventElement(entry) {
    const element = document.createElement("article");
    element.className = "log-entry";
    element.tabIndex = 0;

    element.innerHTML = `
        <div class="entry-time">${escapeHtml(entry.time)}</div>
        <div class="entry-icon" aria-hidden="true">
            ${escapeHtml(entry.icon)}
        </div>
        <div>
            <h3 class="entry-title">${escapeHtml(entry.title)}</h3>
            <p class="entry-comment">${escapeHtml(entry.comment)}</p>
        </div>
    `;

    const open = () => showEventDialog(entry);

    element.addEventListener("click", open);
    element.addEventListener("keydown", event => {
        if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            open();
        }
    });

    return element;
}


async function downloadDailyHtml(dateValue, button) {
    const originalText = button.textContent;
    button.disabled = true;
    button.textContent = "Export läuft …";
    statusText.textContent = `HTML-Tagesbericht für ${dateValue} wird erzeugt …`;

    try {
        const start = await fetchJson(
            `${AVNAV_BASE_URL}/api/exportHtml?date=${encodeURIComponent(dateValue)}`
        );
        const jobId = start.job && start.job.id;
        if (!jobId) {
            throw new Error(start.message || "Export konnte nicht gestartet werden.");
        }

        for (let attempt = 0; attempt < 120; attempt += 1) {
            await new Promise(resolve => window.setTimeout(resolve, 500));
            const result = await fetchJson(
                `${AVNAV_BASE_URL}/api/exportStatus?job=${encodeURIComponent(jobId)}`
            );
            const job = result.job;
            if (!job || job.status === "RUNNING") {
                continue;
            }
            if (job.status !== "OK") {
                throw new Error(job.message || "HTML-Export fehlgeschlagen.");
            }
            if (!job.downloadUrl) {
                throw new Error("Download-Adresse fehlt.");
            }

            const link = document.createElement("a");
            link.href = job.downloadUrl;
            link.download = job.downloadName || `logbuch-${dateValue}.html`;
            link.style.display = "none";
            document.body.appendChild(link);
            link.click();
            link.remove();
            statusText.textContent = `HTML-Tagesbericht für ${dateValue} wurde heruntergeladen.`;
            return;
        }
        throw new Error("Zeitüberschreitung beim HTML-Export.");
    } catch (error) {
        console.error(error);
        statusText.textContent = error.message || "HTML-Export fehlgeschlagen.";
    } finally {
        button.disabled = false;
        button.textContent = originalText;
    }
}


async function downloadDailyKmz(dateValue, button) {
    const originalText = button.textContent;

    button.disabled = true;
    button.textContent = "Export läuft …";
    setStatus(`KMZ für ${dateValue} wird erzeugt …`);

    try {
        const start = await fetchJson(
            `${AVNAV_BASE_URL}/api/exportKmz?date=${
                encodeURIComponent(dateValue)
            }`
        );

        const jobId = start.job && start.job.id;

        if (!jobId) {
            throw new Error(
                start.message ||
                "KMZ-Export konnte nicht gestartet werden."
            );
        }

        for (let attempt = 0; attempt < 120; attempt += 1) {
            await new Promise(resolve =>
                window.setTimeout(resolve, 500)
            );

            const result = await fetchJson(
                `${AVNAV_BASE_URL}/api/exportStatus?job=${
                    encodeURIComponent(jobId)
                }`
            );

            const job = result.job;

            if (!job || job.status === "RUNNING") {
                continue;
            }

            if (job.status !== "OK") {
                throw new Error(
                    job.message || "KMZ-Export fehlgeschlagen."
                );
            }

            if (!job.downloadUrl) {
                throw new Error("Download-Adresse fehlt.");
            }

            const link = document.createElement("a");
            link.href = job.downloadUrl;
            link.download =
                job.downloadName || `logbuch-${dateValue}.kmz`;
            link.hidden = true;

            document.body.appendChild(link);
            link.click();
            link.remove();

            setStatus(`KMZ für ${dateValue} wurde heruntergeladen.`);
            return;
        }

        throw new Error("Zeitüberschreitung beim KMZ-Export.");
    } catch (error) {
        console.error(error);
        setStatus(error.message || "KMZ-Export fehlgeschlagen.");
    } finally {
        button.disabled = false;
        button.textContent = originalText;
    }
}

function createDaySection(day, entries) {
    const section = document.createElement("section");
    section.id = `day-${day.date}`;
    section.className = "day-section open";

    const header = document.createElement("div");
    header.className = "day-header";

    const toggle = document.createElement("button");
    toggle.className = "day-toggle";
    toggle.type = "button";
    toggle.setAttribute("aria-expanded", "true");
    toggle.innerHTML = `
        <span class="day-chevron" aria-hidden="true">▶</span>
        <strong>
            ${escapeHtml(day.weekday)} ${escapeHtml(day.title)}
        </strong>
        <span class="day-count">
            ${entries.length} Einträge
        </span>
    `;

    const exportActions = document.createElement("div");
    exportActions.className = "day-export-actions";

    const htmlExportButton = document.createElement("button");
    htmlExportButton.className = "day-export-button";
    htmlExportButton.type = "button";
    htmlExportButton.textContent = "HTML";
    htmlExportButton.title = "HTML-Tagesbericht herunterladen";
    htmlExportButton.addEventListener("click", event => {
        event.preventDefault();
        event.stopPropagation();
        downloadDailyHtml(day.date, htmlExportButton);
    });

    const kmzExportButton = document.createElement("button");
    kmzExportButton.className = "day-export-button";
    kmzExportButton.type = "button";
    kmzExportButton.textContent = "KMZ";
    kmzExportButton.title = "KMZ für diesen Tag herunterladen";
    kmzExportButton.addEventListener("click", event => {
        event.preventDefault();
        event.stopPropagation();
        downloadDailyKmz(day.date, kmzExportButton);
    });

    exportActions.append(htmlExportButton, kmzExportButton);
    header.append(toggle, exportActions);

    const body = document.createElement("div");
    body.className = "day-body";

    if (entries.length === 0) {
        const empty = document.createElement("p");
        empty.className = "entry-comment";
        empty.textContent = "Für diesen Tag sind keine Einträge vorhanden.";
        body.appendChild(empty);
    } else {
        entries.forEach(entry => {
            body.appendChild(createEventElement(entry));
        });
    }

    toggle.addEventListener("click", () => {
        const isOpen = section.classList.toggle("open");
        toggle.setAttribute("aria-expanded", String(isOpen));
    });

    section.append(header, body);
    return section;
}

async function fetchJson(url, options = {}) {
    const response = await fetch(url, options);

    let data;

    try {
        data = await response.json();
    } catch (error) {
        throw new Error(
            `Ungültige Serverantwort (HTTP ${response.status})`
        );
    }

    if (!response.ok) {
        throw new Error(
            data.message || `HTTP ${response.status}`
        );
    }

    return data;
}

async function loadSummary() {
    setStatus("Logbuchtage werden geladen …");

    const data = await fetchJson(`${AVNAV_BASE_URL}/api/summary`);

    if (data.status !== "OK") {
        throw new Error(
            data.message ||
            "Zusammenfassung konnte nicht geladen werden"
        );
    }

    navigationDays = data.days || [];

    if (navigationDays.length === 0) {
        renderNavigation();
        dayList.replaceChildren();
        setStatus("Keine Logbucheinträge vorhanden");
        return;
    }

    const selectedStillExists = navigationDays.some(
        day => day.date === selectedDate
    );

    const initialDate = selectedStillExists
        ? selectedDate
        : navigationDays[0].date;

    await loadDay(initialDate);
}

async function loadDay(dateValue) {
    selectedDate = dateValue;
    renderNavigation();

    setStatus(`Logbuch vom ${dateValue} wird geladen …`);
    dayList.replaceChildren();

    const data = await fetchJson(
        `${AVNAV_BASE_URL}/api/day?date=${encodeURIComponent(dateValue)}`
    );

    if (data.status !== "OK") {
        throw new Error(data.message || "Tag konnte nicht geladen werden");
    }

    const day = navigationDays.find(item => item.date === dateValue) || {
        date: dateValue,
        title: dateValue,
        weekday: "",
        count: data.count || 0
    };

    const entries = (data.entries || []).map(normalizeEntry);

    dayList.appendChild(createDaySection(day, entries));
    renderNavigation();

    setStatus(
        `${day.weekday} ${day.title} · ${entries.length} Einträge`
    );
}

function createDetailParagraph(label, value) {
    const paragraph = document.createElement("p");
    const strong = document.createElement("strong");

    strong.textContent = `${label}: `;
    paragraph.appendChild(strong);
    paragraph.appendChild(
        document.createTextNode(
            value === null || value === undefined || value === ""
                ? "-"
                : String(value)
        )
    );

    return paragraph;
}

function renderEventDetails(entry) {
    dialogContent.replaceChildren();

    const comment = document.createElement("p");
    comment.className = "dialog-entry-comment";
    comment.textContent = entry.text || "Kein Kommentar vorhanden.";
    dialogContent.appendChild(comment);

    dialogContent.appendChild(
        createDetailParagraph(
            "Position",
            entry.position || "nicht vorhanden"
        )
    );

    if (entry.sog !== null && entry.sog !== undefined) {
        dialogContent.appendChild(
            createDetailParagraph("SOG", entry.sog)
        );
    }

    if (entry.cog !== null && entry.cog !== undefined) {
        dialogContent.appendChild(
            createDetailParagraph("COG", entry.cog)
        );
    }

    if (entry.heading !== null && entry.heading !== undefined) {
        dialogContent.appendChild(
            createDetailParagraph("Heading", entry.heading)
        );
    }

    dialogContent.appendChild(
        createDetailParagraph("Event-Typ", entry.type)
    );
    dialogContent.appendChild(
        createDetailParagraph("Zeitstempel", entry.timestamp)
    );
    dialogContent.appendChild(
        createDetailParagraph(
            "Positionsquelle",
            entry.position_source
        )
    );
    dialogContent.appendChild(
        createDetailParagraph("ID", entry.id)
    );
}

function showEventDialog(entry) {
    activeEntry = normalizeEntry(entry);
    dialogMode = "view";

    document.getElementById("dialog-time").textContent = activeEntry.time;
    document.getElementById("dialog-title").textContent =
        `${activeEntry.icon} ${activeEntry.title}`;

    renderEventDetails(activeEntry);
    resetDialogActions();

    if (typeof dialog.showModal === "function") {
        if (!dialog.open) {
            dialog.showModal();
        }
    } else {
        dialog.setAttribute("open", "");
    }
}

function renderDeleteConfirmation(entry, warningMessage = "") {
    dialogContent.innerHTML = `
        <div id="edit-message"
             class="edit-message warning"
             role="alert"
             ${warningMessage ? "" : "hidden"}>
            ${escapeHtml(warningMessage)}
        </div>

        <div class="delete-confirmation">
            <p class="delete-confirmation-note">
                Dieser Eintrag wird dauerhaft aus dem Logbuch entfernt.
            </p>

            <div class="delete-confirmation-summary">
                <h3>
                    ${escapeHtml(entry.icon)}
                    ${escapeHtml(entry.title)}
                </h3>

                <p>
                    <strong>Zeit:</strong>
                    ${escapeHtml(entry.time)}
                </p>

                <p>
                    <strong>Datum:</strong>
                    ${escapeHtml(
                        String(entry.timestamp || "").slice(0, 10) || "-"
                    )}
                </p>

                <p class="delete-confirmation-comment">
                    ${escapeHtml(entry.text || "Kein Kommentar vorhanden.")}
                </p>
            </div>
        </div>
    `;
}

function startDeleteConfirmation() {
    if (!activeEntry || dialogBusy) {
        return;
    }

    dialogMode = "delete-confirm";
    pendingForcedDelete = null;

    document.getElementById("dialog-time").textContent =
        "Löschbestätigung";
    document.getElementById("dialog-title").textContent =
        "Eintrag wirklich löschen?";

    renderDeleteConfirmation(activeEntry);
    setDeleteDialogActions(false);
}

function cancelDeleteConfirmation() {
    if (!activeEntry || dialogBusy) {
        return;
    }

    dialogMode = "view";
    pendingForcedDelete = null;

    document.getElementById("dialog-time").textContent =
        activeEntry.time;
    document.getElementById("dialog-title").textContent =
        `${activeEntry.icon} ${activeEntry.title}`;

    renderEventDetails(activeEntry);
    resetDialogActions();
}

async function sendEntryDelete(entryId, force = false) {
    const parameters = new URLSearchParams();

    parameters.set("id", entryId);
    parameters.set("force", force ? "true" : "false");

    return fetchJson(
        `${AVNAV_BASE_URL}/api/entry/delete?${parameters.toString()}`
    );
}

async function deleteActiveEntry(force = false) {
    if (!activeEntry || dialogBusy) {
        return;
    }

    const entryId = pendingForcedDelete || activeEntry.id;

    setDialogBusy(true);
    showEditMessage("Eintrag wird gelöscht …", "information");

    try {
        const data = await sendEntryDelete(entryId, force);

        if (data.status === "WARNING") {
            pendingForcedDelete = entryId;
            dialogMode = "delete-warning";

            renderDeleteConfirmation(
                activeEntry,
                warningMessageFromResponse(data)
            );

            setDeleteDialogActions(true);
            return;
        }

        if (data.status !== "OK") {
            throw new Error(
                data.message || "Eintrag konnte nicht gelöscht werden."
            );
        }

        const deletedDate = String(
            (data.deleted && data.deleted.timestamp) ||
            activeEntry.timestamp ||
            ""
        ).slice(0, 10);

        pendingForcedDelete = null;
        setStatus("Logbucheintrag wurde gelöscht");

        if (deletedDate) {
            selectedDate = deletedDate;
        }

        if (dialog.open && typeof dialog.close === "function") {
            dialog.close();
        } else {
            dialog.removeAttribute("open");
        }

        dialogMode = "view";
        activeEntry = null;
        resetDialogActions();

        await loadSummary();
    } catch (error) {
        console.error("Eintrag konnte nicht gelöscht werden", error);

        showEditMessage(
            error.message || "Eintrag konnte nicht gelöscht werden.",
            "error"
        );

        setDialogBusy(false);
    }
}

function timestampToLocalParts(timestamp) {
    const date = new Date(timestamp);

    if (Number.isNaN(date.getTime())) {
        return {
            date: "",
            time: ""
        };
    }

    const pad = value => String(value).padStart(2, "0");

    return {
        date: [
            date.getFullYear(),
            pad(date.getMonth() + 1),
            pad(date.getDate())
        ].join("-"),
        time: [
            pad(date.getHours()),
            pad(date.getMinutes())
        ].join(":")
    };
}

function buildEventTypeOptions(selectedType) {
    return Object.entries(EVENT_TYPES)
        .map(([value, presentation]) => {
            const selected = value === selectedType ? " selected" : "";

            return `
                <option value="${escapeHtml(value)}"${selected}>
                    ${escapeHtml(presentation.icon)}
                    ${escapeHtml(presentation.title)}
                </option>
            `;
        })
        .join("");
}

function renderEditForm(entry) {
    const localParts = timestampToLocalParts(entry.timestamp);

    dialogContent.innerHTML = `
        <div id="edit-message"
             class="edit-message"
             role="alert"
             hidden>
        </div>

        <div class="edit-form">
            <label class="edit-field">
                <span>Eventtyp</span>
                <select id="edit-event-type">
                    ${buildEventTypeOptions(entry.event_type)}
                </select>
            </label>

            <div class="edit-date-time">
                <label class="edit-field">
                    <span>Datum</span>
                    <input id="edit-date"
                           type="date"
                           value="${escapeHtml(localParts.date)}"
                           required>
                </label>

                <label class="edit-field">
                    <span>Uhrzeit</span>
                    <input id="edit-time"
                           type="time"
                           value="${escapeHtml(localParts.time)}"
                           required>
                </label>
            </div>

            <label class="edit-field">
                <span>Logbuchtext</span>
                <textarea id="edit-text"
                          rows="6">${escapeHtml(entry.text || "")}</textarea>
            </label>

            <div class="edit-static-details">
                <p>
                    <strong>Position:</strong>
                    ${escapeHtml(entry.position || "nicht vorhanden")}
                </p>
                <p>
                    <strong>ID:</strong>
                    <span class="entry-id">${
                        dialogMode === "edit"
                            ? escapeHtml(entry.id || "-")
                            : "wird beim Speichern neu erzeugt"
                    }</span>
                </p>
            </div>
        </div>
    `;
}

function startEditing() {
    if (!activeEntry || dialogBusy) {
        return;
    }

    dialogMode = "edit";
    pendingForcedUpdate = null;

    document.getElementById("dialog-time").textContent =
        "Eintrag bearbeiten";
    document.getElementById("dialog-title").textContent =
        `${activeEntry.icon} ${activeEntry.title}`;

    renderEditForm(activeEntry);
    setEditDialogActions();

    const textField = document.getElementById("edit-text");

    if (textField) {
        textField.focus();
        textField.setSelectionRange(
            textField.value.length,
            textField.value.length
        );
    }
}

function openCreateEditor(mode, entry, heading) {
    if (!activeEntry || dialogBusy) {
        return;
    }

    dialogMode = mode;
    pendingForcedUpdate = null;

    document.getElementById("dialog-time").textContent = heading;

    const presentation = getEventPresentation(entry.event_type);
    document.getElementById("dialog-title").textContent =
        `${presentation.icon} ${presentation.title}`;

    renderEditForm(entry);
    setEditDialogActions();

    const textField = document.getElementById("edit-text");

    if (textField) {
        textField.focus();

        if (mode === "duplicate") {
            textField.setSelectionRange(
                textField.value.length,
                textField.value.length
            );
        }
    }
}

function startDuplicating() {
    const duplicate = normalizeEntry({
        ...activeEntry,
        id: null
    });

    openCreateEditor(
        "duplicate",
        duplicate,
        "Eintrag duplizieren"
    );
}

function shiftedEntry(seconds) {
    const sourceTime = new Date(activeEntry.timestamp);

    if (Number.isNaN(sourceTime.getTime())) {
        throw new Error("Zeitstempel des Eintrags ist ungültig.");
    }

    sourceTime.setSeconds(sourceTime.getSeconds() + seconds);

    return normalizeEntry({
        ...activeEntry,
        id: null,
        timestamp: sourceTime.toISOString().replace(/\.\d{3}Z$/, "Z"),
        event_type: "manual",
        text: "",
        lat: null,
        lon: null,
        sog: null,
        cog: null,
        heading: null,
        position_source: "unknown"
    });
}

function startInsertBefore() {
    try {
        openCreateEditor(
            "insert-before",
            shiftedEntry(-60),
            "Eintrag davor hinzufügen"
        );
    } catch (error) {
        console.error(error);
    }
}

function startInsertAfter() {
    try {
        openCreateEditor(
            "insert-after",
            shiftedEntry(60),
            "Eintrag danach hinzufügen"
        );
    } catch (error) {
        console.error(error);
    }
}

function cancelEditing() {
    if (!activeEntry || dialogBusy) {
        return;
    }

    if (
        dialogMode === "delete-confirm" ||
        dialogMode === "delete-warning"
    ) {
        cancelDeleteConfirmation();
        return;
    }

    dialogMode = "view";
    pendingForcedUpdate = null;

    document.getElementById("dialog-time").textContent =
        activeEntry.time;
    document.getElementById("dialog-title").textContent =
        `${activeEntry.icon} ${activeEntry.title}`;

    renderEventDetails(activeEntry);
    resetDialogActions();
}

function showEditMessage(message, type = "error") {
    const messageElement = document.getElementById("edit-message");

    if (!messageElement) {
        return;
    }

    messageElement.textContent = message;
    messageElement.className = `edit-message ${type}`;
    messageElement.hidden = false;
}

function clearEditMessage() {
    const messageElement = document.getElementById("edit-message");

    if (!messageElement) {
        return;
    }

    messageElement.textContent = "";
    messageElement.className = "edit-message";
    messageElement.hidden = true;
}

function collectEditPayload() {
    const eventTypeElement = document.getElementById("edit-event-type");
    const dateElement = document.getElementById("edit-date");
    const timeElement = document.getElementById("edit-time");
    const textElement = document.getElementById("edit-text");

    if (
        !eventTypeElement ||
        !dateElement ||
        !timeElement ||
        !textElement
    ) {
        throw new Error("Bearbeitungsformular ist nicht vollständig.");
    }

    const dateValue = dateElement.value;
    const timeValue = timeElement.value;

    if (!dateValue) {
        throw new Error("Bitte ein Datum angeben.");
    }

    if (!timeValue) {
        throw new Error("Bitte eine Uhrzeit angeben.");
    }

    const localTimestamp = new Date(`${dateValue}T${timeValue}:00`);

    if (Number.isNaN(localTimestamp.getTime())) {
        throw new Error("Datum oder Uhrzeit ist ungültig.");
    }

    const timestamp = localTimestamp
        .toISOString()
        .replace(/\.\d{3}Z$/, "Z");

    const payload = {
        event_type: eventTypeElement.value,
        text: textElement.value,
        timestamp: timestamp
    };

    if (dialogMode === "edit") {
        payload.id = activeEntry.id;
    }

    return payload;
}

function warningMessageFromResponse(data) {
    if (Array.isArray(data.warnings) && data.warnings.length > 0) {
        return data.warnings
            .map(warning => warning.message)
            .filter(Boolean)
            .join("\n");
    }

    return data.message || "Die Änderung erzeugt eine Warnung.";
}

async function sendEntryUpdate(payload, force = false) {
    const parameters = new URLSearchParams();

    parameters.set("id", payload.id);
    parameters.set("event_type", payload.event_type);
    parameters.set("text", payload.text);
    parameters.set("timestamp", payload.timestamp);
    parameters.set("force", force ? "true" : "false");

    return fetchJson(
        `${AVNAV_BASE_URL}/api/entry/update?${parameters.toString()}`
    );
}

async function sendEntryCreate(payload, force = false) {
    const parameters = new URLSearchParams();

    parameters.set("event_type", payload.event_type);
    parameters.set("text", payload.text);
    parameters.set("timestamp", payload.timestamp);
    parameters.set("force", force ? "true" : "false");
    parameters.set("resolve_position", "true");

    return fetchJson(
        `${AVNAV_BASE_URL}/api/add?${parameters.toString()}`
    );
}

async function saveEditedEntry(force = false) {
    if (!activeEntry || dialogBusy) {
        return;
    }

    clearEditMessage();

    let payload;

    try {
        payload = force && pendingForcedUpdate
            ? pendingForcedUpdate
            : collectEditPayload();
    } catch (error) {
        showEditMessage(error.message || String(error), "error");
        return;
    }

    setDialogBusy(true);
    showEditMessage("Eintrag wird gespeichert …", "information");

    try {
        const createsEntry = dialogMode !== "edit";
        const data = createsEntry
            ? await sendEntryCreate(payload, force)
            : await sendEntryUpdate(payload, force);

        if (data.status === "WARNING") {
            pendingForcedUpdate = payload;

            showEditMessage(
                warningMessageFromResponse(data),
                "warning"
            );

            dialogForceSaveButton.hidden = false;
            dialogSaveButton.hidden = true;
            setDialogBusy(false);
            return;
        }

        if (data.status !== "OK") {
            throw new Error(
                data.message || "Eintrag konnte nicht gespeichert werden."
            );
        }

        pendingForcedUpdate = null;

        const savedEntry = normalizeEntry(data.entry || {
            ...activeEntry,
            ...payload
        });

        activeEntry = savedEntry;

        const newDate = String(savedEntry.timestamp || "").slice(0, 10);

        if (newDate) {
            selectedDate = newDate;
        }

        showEditMessage("Eintrag wurde gespeichert.", "success");
        setStatus(
            dialogMode === "edit"
                ? "Logbucheintrag wurde aktualisiert"
                : "Neuer Logbucheintrag wurde gespeichert"
        );

        if (dialog.open && typeof dialog.close === "function") {
            dialog.close();
        } else {
            dialog.removeAttribute("open");
        }

        dialogMode = "view";
        resetDialogActions();

        await loadSummary();
    } catch (error) {
        console.error("Eintrag konnte nicht gespeichert werden", error);

        showEditMessage(
            error.message || "Eintrag konnte nicht gespeichert werden.",
            "error"
        );

        setDialogBusy(false);
    }
}

dialogEditButton.addEventListener("click", startEditing);
dialogDuplicateButton.addEventListener("click", startDuplicating);
dialogBeforeButton.addEventListener("click", startInsertBefore);
dialogAfterButton.addEventListener("click", startInsertAfter);

dialogDeleteButton.addEventListener(
    "click",
    startDeleteConfirmation
);

dialogConfirmDeleteButton.addEventListener("click", () => {
    deleteActiveEntry(false);
});

dialogForceDeleteButton.addEventListener("click", () => {
    deleteActiveEntry(true);
});

dialogCancelEditButton.addEventListener("click", cancelEditing);

dialogSaveButton.addEventListener("click", () => {
    saveEditedEntry(false);
});

dialogForceSaveButton.addEventListener("click", () => {
    saveEditedEntry(true);
});

dialog.addEventListener("cancel", event => {
    if (dialogBusy) {
        event.preventDefault();
        return;
    }

    dialogMode = "view";
    activeEntry = null;
    pendingForcedUpdate = null;
    pendingForcedDelete = null;
    resetDialogActions();
});

dialog.addEventListener("close", () => {
    dialogMode = "view";
    activeEntry = null;
    pendingForcedUpdate = null;
    pendingForcedDelete = null;
    resetDialogActions();
});

menuToggle.addEventListener("click", () => {
    sidebar.classList.toggle("open");
});

loadSummary().catch(error => {
    console.error("Logbuch konnte nicht geladen werden", error);
    setStatus("Fehler beim Laden der Logbuchdaten");

    dayList.innerHTML = `
        <section class="day-section open">
            <div class="day-body">
                <p class="entry-comment">
                    Die Logbuchdaten konnten nicht geladen werden.
                </p>
            </div>
        </section>
    `;
});
