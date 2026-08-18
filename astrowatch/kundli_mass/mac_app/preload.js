// Preload script -- runs in an isolated context with access to Node + the
// renderer's window, before any renderer script executes. This is the ONLY
// bridge between the sandboxed renderer (the Kundli Studio UI, unchanged
// from the browser version) and the main process (which alone can load the
// native Swiss Ephemeris binding, since sweph is a Node/N-API addon and, per
// its own README, "will not work in browsers or in any other environment
// that does not support native C/C++ add-ons").
//
// Uses ipcRenderer.sendSync deliberately (not the async invoke/handle
// pattern) so that engine_core.js's computeChart() can remain a plain
// synchronous function -- every caller in render.js / varshaphal.js /
// matchmaking.js calls it synchronously today, and rewriting that whole
// call chain to be async (and every consumer of it) was judged riskier than
// one blocking IPC round-trip (sub-millisecond in practice; this is a local
// libswe C call, not network I/O).
const { contextBridge, ipcRenderer } = require("electron");

let nativeAvailable = null; // lazily determined, cached

function checkAvailable() {
  if (nativeAvailable !== null) return nativeAvailable;
  try {
    const res = ipcRenderer.sendSync("astrowatch:native-status");
    nativeAvailable = !!(res && res.available);
  } catch (e) {
    nativeAvailable = false;
  }
  return nativeAvailable;
}

contextBridge.exposeInMainWorld("astrowatchNative", {
  get available() {
    return checkAvailable();
  },
  computeChartSync: function (jd, latDeg, lonDeg) {
    try {
      return ipcRenderer.sendSync("astrowatch:compute-chart", { jd: jd, lat: latDeg, lon: lonDeg });
    } catch (e) {
      return { error: String((e && e.message) || e) };
    }
  },
  statusDetail: function () {
    try {
      return ipcRenderer.sendSync("astrowatch:native-status");
    } catch (e) {
      return { available: false, error: String((e && e.message) || e) };
    }
  }
});
