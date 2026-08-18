# Astrowatch Kundli Studio -- Desktop (Electron / macOS)

A native desktop build of Kundli Studio (see `../astrowatch_kundli_studio.html`
for the plain-browser version). Same UI, same feature set -- kundli chart
picture (North/South Indian/Sudarshan), Vimshottari Mahadasha/Antardasha,
Yogini Dasha, Varshaphal, Ashtakoot match-making, `.kun` save/load, print --
but every planetary position is computed by the **real Swiss Ephemeris C
library** (via the `sweph` native Node binding), not the approximate
client-side JS formulas the browser version has to use.

## Why this exists

The browser version cannot call a native C library or read local files, so it
uses a compact analytic approximation (accurate to roughly a Nakshatra pada,
disclosed in-app). This desktop build removes that limitation entirely: the
Electron **main process** (a real Node.js process, not a browser sandbox)
loads `sweph` and the same `.se1` ephemeris data files Astrowatch's own
Python backend uses (bundled under `resources/ephemeris/`), and answers
chart-computation requests from the renderer UI over IPC. See `main.js`'s
`computeChartNative()` -- it is a deliberate line-by-line port of
`astrowatch/kundli.py`'s `compute_kundli()`, verified this session to
reproduce that Python function's output to floating-point precision (see
"Verification" below).

The renderer UI shows, visibly, which engine actually computed the chart on
screen ("Engine: Swiss Ephemeris (native)" vs "Engine: Approximate (JS
fallback)") -- it never silently substitutes one for the other.

## Architecture

- `main.js` -- Electron main process. Loads `sweph`, points it at
  `resources/ephemeris/*.se1`, sets Lahiri sidereal mode, and answers two
  synchronous IPC calls (`astrowatch:native-status`,
  `astrowatch:compute-chart`).
- `preload.js` -- contextBridge shim exposing `window.astrowatchNative` to
  the renderer (`computeChartSync`, `available`, `statusDetail`).
- `renderer/` -- the Kundli Studio UI itself. `engine_core.js`'s
  `computeChart()` calls `window.astrowatchNative.computeChartSync()` when
  available and falls back to the original approximate algorithm
  (`computeChartApprox()`) otherwise -- every other file (`render.js`,
  `chart.js`, `panchang.js`, `yogini.js`, `varshaphal.js`,
  `matchmaking.js`) is completely unmodified from the browser version and
  needed no changes to benefit from native precision.
- `resources/ephemeris/` -- the same `sepl_18.se1` / `semo_18.se1` /
  `seas_18.se1` (+ 12/24-block variants) files as `astrowatch/ephemeris/`,
  copied here so `electron-builder` can bundle them as app resources.

## Building

```bash
cd astrowatch/kundli_mass/mac_app
npm install
npm start          # run in dev mode
npm run dist:mac    # build a .dmg + .zip for both Apple Silicon and Intel
```

Output lands in `dist/`.

### This could not be built or run in this development sandbox

Two real limitations, disclosed rather than worked around:

1. **`npm install` cannot complete here.** `electron`'s postinstall script
   downloads a large prebuilt binary directly from `github.com`'s release
   CDN, and that specific request fails in this sandbox (`getaddrinfo
   EAI_AGAIN github.com` even with the sandbox's HTTP proxy configured --
   Electron's installer, via `@electron/get`, does not honor the proxy
   env vars this sandbox otherwise uses for `npm install <package>` against
   the npm registry, which works fine and is how `sweph` itself was
   installed and tested). This is an infrastructure limitation of the
   sandbox, not of the app's code.
2. **A real `.dmg` can only be produced on macOS.** `electron-builder`'s
   `dmg` target shells out to Apple-only tools (`hdiutil`, `bomutils`) that
   do not exist on Linux -- this is documented by electron-builder itself,
   not something this session could route around.

Practically: run `npm install && npm run dist:mac` on an actual Mac (or a
macOS GitHub Actions runner), not in this sandbox. The `sweph` dependency
does ship prebuilt native binaries for `darwin-arm64` (Apple Silicon) -- no
compiler needed there. For `darwin-x64` (Intel Mac) there is currently no
prebuilt binary for `sweph`, so it will compile from source via `node-gyp`
on first `npm install`, which requires Xcode Command Line Tools
(`xcode-select --install`) to be present on that machine.

The resulting `.dmg` will also be **unsigned and not notarized** (no Apple
Developer account/certificate is available here) -- macOS Gatekeeper will
show "Apple could not verify... is free of malware" on first launch; the
user needs to right-click the app -> Open (or System Settings -> Privacy &
Security -> Open Anyway) once to run it.

## Verification performed this session (without a real Electron launch)

Since Electron itself couldn't be installed here, `main.js`'s
`computeChartNative()` calculation logic was extracted and run standalone
(same `sweph` package, installed directly from the npm registry, which does
work in this sandbox) against a real test case (1990-01-15 08:30 +5:30,
New Delhi 28.6139N 77.2090E) and diffed field-by-field against
`astrowatch/kundli.py`'s `compute_kundli()` for the identical
Julian Day / latitude / longitude. Every value (ayanamsha, ascendant
tropical + sidereal, and tropical + sidereal longitude for all 9 grahas)
matched to floating-point noise (< 1e-10 degrees, i.e. effectively exact --
the same C library, the same data files, the same flags). This confirms the
Electron main-process code is algorithmically correct; it does not confirm
the Electron app launches, renders, or packages correctly on a real Mac,
which could not be tested here.

All planet IDs, flags, and constant names (`SEFLG_SWIEPH`, `SEFLG_SIDEREAL`,
`SE_SIDM_LAHIRI`, `SE_MEAN_NODE`, house system `"W"` = whole sign, etc.) were
taken from `sweph`'s own `index.d.ts` type definitions, not guessed.
