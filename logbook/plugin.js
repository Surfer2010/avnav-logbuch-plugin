console.log("logbook plugin loaded");

var logbookWidget = {
  name: "logbook_EntryWidget",

  storeKeys: {
    lat: "nav.gps.lat",
    lon: "nav.gps.lon"
  },

  caption: "Logbuch",

  initFunction: function(context) {
    context.eventHandler.openLogbook = function(ev) {
      var existing = document.getElementById("logbookOverlay");
      if (existing) existing.remove();

      var overlay = document.createElement("div");
      overlay.id = "logbookOverlay";

      overlay.innerHTML =
        '<div class="logbookBox">' +
        '<h2>Logbucheintrag</h2>' +

        '<div class="logbookGroup">' +
        '<button data-type="motor_on">Motor an</button>' +
        '<button data-type="motor_off">Motor aus</button>' +
        '</div>' +

        '<div class="logbookGroup">' +
        '<button data-type="sail_set">Segel setzen</button>' +
        '<button data-type="sail_down">Segel einholen</button>' +
        '</div>' +

        '<div class="logbookGroup">' +
        '<button data-type="anchor_down">Anker ab</button>' +
        '<button data-type="anchor_up">Anker auf</button>' +
        '</div>' +

        '<textarea id="logbookText" placeholder="Anmerkung"></textarea>' +

        '<div class="logbookActions">' +
        '<button id="logbookSaveManual">Speichern</button>' +
        '<button id="logbookClose">Schließen</button>' +
        '</div>' +

        '<div id="logbookStatus"></div>' +
        '</div>';

      document.body.appendChild(overlay);

      function saveEntry(type) {
        var text = document.getElementById("logbookText").value || "";
        var url = AVNAV_BASE_URL + "/api/add?type=" + encodeURIComponent(type) +
          "&text=" + encodeURIComponent(text);

        fetch(url)
          .then(function(r) { return r.json(); })
          .then(function(data) {
            document.getElementById("logbookStatus").innerText = "Gespeichert";
            console.log("logbook saved", data);
          })
          .catch(function(err) {
            document.getElementById("logbookStatus").innerText = "Fehler beim Speichern";
            console.error("logbook error", err);
          });
      }

      overlay.querySelectorAll("button[data-type]").forEach(function(btn) {
        btn.addEventListener("click", function() {
          saveEntry(btn.getAttribute("data-type"));
        });
      });

      document.getElementById("logbookSaveManual").addEventListener("click", function() {
        saveEntry("manual");
      });

      document.getElementById("logbookClose").addEventListener("click", function() {
        overlay.remove();
      });
    };
  },

  renderHtml: function(props) {
    return '<div class="widgetData"><button class="logbookOpenButton">Logbuch</button></div>';
  }
};

avnav.api.registerWidget(logbookWidget);
