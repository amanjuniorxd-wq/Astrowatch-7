// Small UI glue for the desktop build: shows, honestly and visibly (never
// silently), which calculation engine actually produced the numbers on
// screen -- the real native Swiss Ephemeris library, or (only if the native
// binding could not be loaded on this machine) the disclosed client-side
// approximate JS engine that the browser version of this app always used.
function updateEngineBadge(chart) {
  var badge = document.getElementById("engine-badge");
  var note = document.getElementById("precision-note-engine");
  if (!badge || !note) return;

  var native = (typeof window !== "undefined" && window.astrowatchNative) || null;
  var usedNative = chart ? chart.engine === "swisseph-native" : (native && native.available);

  if (usedNative) {
    badge.textContent = "Engine: Swiss Ephemeris (native)";
    badge.className = "engine-badge native";
    note.innerHTML =
      "This desktop app computes every position with the real Swiss Ephemeris C library " +
      "(via the bundled sweph native binding and the same .se1 data files Astrowatch's own " +
      "server-side backend uses) -- not an approximation. Positions match the Python backend " +
      "to the same sub-arcsecond precision class for the same date/time/place.";
  } else {
    var detail = native && native.available === false && native.error ? " (" + native.error + ")" : "";
    badge.textContent = "Engine: Approximate (JS fallback)";
    badge.className = "engine-badge approx";
    note.innerHTML =
      "The native Swiss Ephemeris engine is not available on this machine right now" +
      detail +
      ", so this chart used the same compact analytic model (JPL/Standish 1992 elements, " +
      "Schlyter Moon with 12 perturbation terms, linear Lahiri ayanamsha) as the browser " +
      "version of this app -- typically accurate to about 0.02&ndash;0.05&deg; for the Moon " +
      "and roughly half a degree for other planets, comfortably inside a Nakshatra pada, but " +
      "not exact. Restart the app, or check that it was installed correctly, to restore native precision.";
  }
}

document.addEventListener("DOMContentLoaded", function () {
  updateEngineBadge(null);
});
