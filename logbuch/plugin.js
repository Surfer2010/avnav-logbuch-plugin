/*
 * Kompatibilitätsloader für ältere AVNav-Versionen.
 *
 * Neue AVNav-Versionen laden plugin.mjs direkt.
 * Ältere AVNav-Versionen laden diese Datei und anschließend plugin.mjs.
 */
import("./plugin.mjs?v=2.0.3")
    .then(function(module) {
        if (!module || typeof module.default !== "function") {
            throw new Error("Logbuch: plugin.mjs besitzt keinen Default-Export");
        }

        if (
            typeof avnav === "undefined" ||
            !avnav.api
        ) {
            throw new Error("Logbuch: altes AVNav API ist nicht verfügbar");
        }

        return module.default(avnav.api);
    })
    .catch(function(error) {
        console.error("Logbuch konnte nicht geladen werden", error);
    });
