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
    manual: {
        icon: "✎",
        title: "Logbucheintrag"
    }
};

const dayList = document.getElementById("day-list");
const dayNavigation = document.getElementById("day-navigation");
const dialog = document.getElementById("event-dialog");
const sidebar = document.getElementById("sidebar");
const menuToggle = document.getElementById("menu-toggle");
const statusText = document.getElementById("status-text");

let navigationDays = [];
let selectedDate = null;

function getEventPresentation(eventType) {
    return EVENT_TYPES[eventType] || {
        icon: "•",
        title: eventType || "Unbekanntes Ereignis"
    };
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
    if (entry.lat === null || entry.lat === undefined ||
        entry.lon === null || entry.lon === undefined) {
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

function renderNavigation() {
    dayNavigation.replaceChildren();

    navigationDays.forEach((day, index) => {
        const link = document.createElement("a");
        const isActive = day.date === selectedDate;

        link.className = "nav-link";

        if (isActive) {
            link.classList.add("active");
            link.setAttribute("aria-current", "page");
        }

        link.href = `#day-${day.date}`;
        link.innerHTML = `
            <span>${day.weekday} ${day.title}</span>
            <span class="nav-count">${day.count}</span>
        `;

        link.addEventListener("click", async event => {
            event.preventDefault();
            await loadDay(day.date);
            sidebar.classList.remove("open");
        });

        dayNavigation.appendChild(link);
    });
}

function createEventElement(entry) {
    const element = document.createElement("article");
    element.className = "log-entry";
    element.tabIndex = 0;

    element.innerHTML = `
        <div class="entry-time">${entry.time}</div>
        <div class="entry-icon" aria-hidden="true">${entry.icon}</div>
        <div>
            <h3 class="entry-title">${entry.title}</h3>
            <p class="entry-comment">${entry.comment}</p>
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

function createDaySection(day, entries) {
    const section = document.createElement("section");
    section.id = `day-${day.date}`;
    section.className = "day-section open";

    const toggle = document.createElement("button");
    toggle.className = "day-toggle";
    toggle.type = "button";
    toggle.setAttribute("aria-expanded", "true");
    toggle.innerHTML = `
        <span class="day-chevron" aria-hidden="true">▶</span>
        <strong>${day.weekday} ${day.title}</strong>
        <span class="day-count">${entries.length} Einträge</span>
    `;

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

    section.append(toggle, body);
    return section;
}

async function loadSummary() {
    setStatus("Logbuchtage werden geladen …");

    const response = await fetch(`${AVNAV_BASE_URL}/api/summary`);

    if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();

    if (data.status !== "OK") {
        throw new Error(data.message || "Zusammenfassung konnte nicht geladen werden");
    }

    navigationDays = data.days || [];

    if (navigationDays.length === 0) {
        renderNavigation();
        dayList.replaceChildren();
        setStatus("Keine Logbucheinträge vorhanden");
        return;
    }

    const initialDate = selectedDate || navigationDays[0].date;
    await loadDay(initialDate);
}

async function loadDay(dateValue) {
    selectedDate = dateValue;
    renderNavigation();

    setStatus(`Logbuch vom ${dateValue} wird geladen …`);
    dayList.replaceChildren();

    const response = await fetch(
        `${AVNAV_BASE_URL}/api/day?date=${encodeURIComponent(dateValue)}`
    );

    if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();

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

    setStatus(`${day.weekday} ${day.title} · ${entries.length} Einträge`);
}

function showEventDialog(entry) {
    document.getElementById("dialog-time").textContent = entry.time;
    document.getElementById("dialog-title").textContent =
        `${entry.icon} ${entry.title}`;

    const positionText = entry.position
        ? `<p><strong>Position:</strong> ${entry.position}</p>`
        : "<p><strong>Position:</strong> nicht vorhanden</p>";

    const navigationDetails = [];

    if (entry.sog !== null && entry.sog !== undefined) {
        navigationDetails.push(
            `<p><strong>SOG:</strong> ${entry.sog}</p>`
        );
    }

    if (entry.cog !== null && entry.cog !== undefined) {
        navigationDetails.push(
            `<p><strong>COG:</strong> ${entry.cog}</p>`
        );
    }

    if (entry.heading !== null && entry.heading !== undefined) {
        navigationDetails.push(
            `<p><strong>Heading:</strong> ${entry.heading}</p>`
        );
    }

    document.getElementById("dialog-content").innerHTML = `
        <p>${entry.comment}</p>
        ${positionText}
        ${navigationDetails.join("")}
        <p><strong>Event-Typ:</strong> ${entry.type}</p>
        <p><strong>Zeitstempel:</strong> ${entry.timestamp || "-"}</p>
        <p><strong>Positionsquelle:</strong> ${entry.position_source || "-"}</p>
        <p><strong>ID:</strong> ${entry.id || "-"}</p>
    `;

    if (typeof dialog.showModal === "function") {
        dialog.showModal();
    } else {
        dialog.setAttribute("open", "");
    }
}

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
