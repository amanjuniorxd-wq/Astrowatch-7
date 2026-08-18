// Astrowatch Kundli Studio -- Electron main process.
//
// This is what makes the desktop build different from the plain-browser
// Kundli Studio webapp: it loads `sweph` (an N-API binding to the real
// Swiss Ephemeris C library, the same engine version -- 2.10.3 -- used by
// this project's own Python backend, astrowatch/kundli.py) and answers
// chart-computation requests from the renderer over a synchronous IPC
// channel. See renderer/engine_core.js's computeChart() for the client side
// of this bridge, and preload.js for the contextBridge wiring.
//
// The algorithm below is a deliberate line-by-line port of
// astrowatch/kundli.py's compute_kundli()/_placement_from_calc(), so that a
// chart built by this desktop app and a chart built by the Python backend
// for the same date/time/place agree to the same sub-arcsecond precision
// class -- not just "closer than the JS approximation," but the literal
// same calculation path (FLG_SWIEPH for tropical, FLG_SWIEPH|FLG_SIDEREAL
// for sidereal, SIDM_LAHIRI, mean-node Rahu/Ketu, whole-sign houses via the
// Ascendant only).
"use strict";

const path = require("path");
const fs = require("fs");
const { app, BrowserWindow, ipcMain, Menu } = require("electron");

let sweph = null;
let swephLoadError = null;
let ephePath = null;

const REQUIRED_FILES = ["sepl_18.se1", "semo_18.se1", "seas_18.se1"];

function resolveEphemerisPath() {
  // Packaged app: files are copied into resources/ephemeris via
  // electron-builder's extraResources config (see package.json).
  // Dev run (npm start / electron .): read straight from this folder.
  const candidates = [
    path.join(process.resourcesPath || "", "ephemeris"),
    path.join(__dirname, "resources", "ephemeris")
  ];
  for (const c of candidates) {
    try {
      if (REQUIRED_FILES.every((f) => fs.existsSync(path.join(c, f)))) return c;
    } catch (e) {
      /* keep trying */
    }
  }
  return null;
}

function initSweph() {
  ephePath = resolveEphemerisPath();
  if (!ephePath) {
    swephLoadError =
      "Bundled Swiss Ephemeris data files (sepl_18.se1 / semo_18.se1 / seas_18.se1) " +
      "were not found next to the app. The desktop app will not silently fall back to " +
      "an approximation for this -- it will report native precision as unavailable " +
      "and the renderer will use the disclosed client-side approximate engine instead.";
    return;
  }
  try {
    sweph = require("sweph");
    sweph.set_ephe_path(ephePath);
    sweph.set_sid_mode(sweph.constants.SE_SIDM_LAHIRI, 0, 0);
  } catch (e) {
    // Most likely cause on a real Mac: no prebuilt native binary for this
    // architecture/Node ABI and no local compiler toolchain (Xcode Command
    // Line Tools) to build one from source. Documented, not hidden.
    sweph = null;
    swephLoadError = "Failed to load the native Swiss Ephemeris binding (sweph): " + String((e && e.message) || e);
  }
}

const GRAHA_BODY_IDS = {}; // filled once sweph is loaded, below
const NODE_NAME = "rahu";

function bodyIds() {
  return {
    sun: sweph.constants.SE_SUN,
    moon: sweph.constants.SE_MOON,
    mercury: sweph.constants.SE_MERCURY,
    venus: sweph.constants.SE_VENUS,
    mars: sweph.constants.SE_MARS,
    jupiter: sweph.constants.SE_JUPITER,
    saturn: sweph.constants.SE_SATURN
  };
}

function norm360(x) {
  var v = x % 360;
  if (v < 0) v += 360;
  return v;
}

// Direct port of astrowatch/kundli.py's compute_kundli(), returning the same
// { ayanamsha, tropical, sidereal, ascendantSidereal } shape that the JS
// approximate engine's computeChart() produces, so renderer code needs no
// changes to consume either.
function computeChartNative(jd, latDeg, lonDeg) {
  if (!sweph) return { error: swephLoadError || "Native Swiss Ephemeris engine not initialized." };

  var FLG_SWIEPH = sweph.constants.SEFLG_SWIEPH;
  var FLG_SIDEREAL = sweph.constants.SEFLG_SIDEREAL;
  var FLG_SPEED = sweph.constants.SEFLG_SPEED;
  var FLG_MOSEPH = sweph.constants.SEFLG_MOSEPH;

  var ids = bodyIds();
  var tropical = {};
  var sidereal = {};

  try {
    for (var name in ids) {
      var trop = sweph.calc_ut(jd, ids[name], FLG_SWIEPH | FLG_SPEED);
      var sid = sweph.calc_ut(jd, ids[name], FLG_SWIEPH | FLG_SIDEREAL | FLG_SPEED);
      if ((trop.flag & FLG_MOSEPH) || (sid.flag & FLG_MOSEPH)) {
        return {
          error:
            "swe calc_ut() for " +
            name +
            " fell back to Moshier approximation mode instead of the bundled file-based " +
            "ephemeris. Refusing to report this as native-precision data."
        };
      }
      if (trop.error || sid.error) {
        return { error: "swe calc_ut() error for " + name + ": " + (trop.error || sid.error) };
      }
      tropical[name] = norm360(trop.data[0]);
      sidereal[name] = norm360(sid.data[0]);
    }

    // Rahu: mean lunar node (matches astrowatch/kundli.py's NODE_BODY_ID = swe.MEAN_NODE).
    var rahuTrop = sweph.calc_ut(jd, sweph.constants.SE_MEAN_NODE, FLG_SWIEPH | FLG_SPEED);
    var rahuSid = sweph.calc_ut(jd, sweph.constants.SE_MEAN_NODE, FLG_SWIEPH | FLG_SIDEREAL | FLG_SPEED);
    if ((rahuTrop.flag & FLG_MOSEPH) || (rahuSid.flag & FLG_MOSEPH)) {
      return { error: "swe calc_ut() for rahu fell back to Moshier approximation mode." };
    }
    tropical.rahu = norm360(rahuTrop.data[0]);
    sidereal.rahu = norm360(rahuSid.data[0]);
    // Ketu: exactly opposite Rahu by definition, not independently computed
    // (same convention as astrowatch/kundli.py).
    tropical.ketu = norm360(tropical.rahu + 180);
    sidereal.ketu = norm360(sidereal.rahu + 180);

    // Ascendant: whole-sign house system ("W"), computed sidereal directly via
    // SEFLG_SIDEREAL and tropically with no flag, matching kundli.py exactly.
    var housesSid = sweph.houses_ex(jd, FLG_SIDEREAL, latDeg, lonDeg, "W");
    var housesTrop = sweph.houses_ex(jd, 0, latDeg, lonDeg, "W");
    var ascSidereal = norm360(housesSid.data.points[0]);
    var ascTropical = norm360(housesTrop.data.points[0]);
    var ayanamsha = norm360(ascTropical - ascSidereal);

    return {
      ayanamsha: ayanamsha,
      tropical: tropical,
      sidereal: sidereal,
      ascendantSidereal: ascSidereal,
      ephemerisPath: ephePath
    };
  } catch (e) {
    return { error: "Native Swiss Ephemeris call threw: " + String((e && e.message) || e) };
  }
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1180,
    height: 860,
    minWidth: 900,
    minHeight: 640,
    backgroundColor: "#ffffff",
    title: "Astrowatch Kundli Studio",
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false
    }
  });
  win.setMenuBarVisibility(false);
  win.loadFile(path.join(__dirname, "renderer", "index.html"));
}

ipcMain.on("astrowatch:native-status", (event) => {
  event.returnValue = {
    available: !!sweph,
    ephemerisPath: ephePath,
    error: swephLoadError
  };
});

ipcMain.on("astrowatch:compute-chart", (event, args) => {
  event.returnValue = computeChartNative(args.jd, args.lat, args.lon);
});

app.whenReady().then(() => {
  initSweph();
  Menu.setApplicationMenu(null);
  createWindow();
  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});
