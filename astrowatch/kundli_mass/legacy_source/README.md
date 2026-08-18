# Legacy source: Kundli-Lite reengineering

`astrowatch_kundli_studio.html` reengineers "Kundli-Lite" (a c.2017 offline
Windows desktop astrology tool, VB6 + MS Access, provided by the user as
`Kundli-Lite.exe` + `Kundli-Dat.mdb` + `Kundli-Def.mdb` + supporting
OCX/DLL/help files). The original binaries are not redistributed here.

## What was reused

`Kundli-Dat.mdb` contained three tables -- `Countries` (232 rows), `States`
(96 rows), `Places` (11,053 rows, columns: Place, District, Latitude,
Longitude, PlaceName, Country ID, State ID). This is a genuine, real-world
place/geo lookup database (predominantly India-focused, with worldwide
coverage), extracted with the `access_parser` Python library (mdbtools was
not installable in this sandbox without root).

`places_from_kundli_lite.json` (this directory) is the extracted, converted
result: `[label, latitude_decimal, longitude_decimal, utc_offset_hours]` for
10,975 places (12 rows were dropped for missing coordinates; 78 exact-label
duplicates were deduplicated keeping the first occurrence).

- Latitude/Longitude were stored as degree+hemisphere+minute strings (e.g.
  `"82E30"`) and converted to signed decimal degrees.
- The old software's per-country/per-state `zone` field is a *standard-time
  meridian* (e.g. India `82E30` -> 82.5 / 15 = UTC+5.5, matching India's real
  offset), not an IANA timezone. It was converted the same way: `meridian /
  15 = UTC offset hours`. This has **no daylight-saving/historical-change
  awareness** -- it is a fixed offset per place, exactly as the original 2017
  desktop software used it. The new webapp discloses this limitation in its
  UI and offers manual lat/lon/UTC entry as an escape hatch, consistent with
  this project's no-silent-fallback principle.

## What was NOT reused

The original `.exe`/`.dll`/`.ocx` binaries (VB6 native code) were not
decompiled or executed -- only the bundled Access data was extracted. All
astronomical/astrological computation in the new webapp is Astrowatch's own
existing, previously cross-validated client-side engine (ported from
`astrowatch_kundli_life_report.html`, itself checked against the project's
Python Swiss-Ephemeris backend), extended with Nakshatra Pada, basic Panchang
(Tithi/Yoga/Karana/Vaar), and Pratyantardasha -- none of which existed in the
prior client-side app.

## Round 2: feature parity pass (kundli picture, dashas, match-making)

The user's follow-up request asked to add "kundli chart generation and all
other function from the old software" and specifically to render the chart
"into a picture like the old software did." Since the old software's real
feature set was never directly observable (no GUI access, no execution --
per this project's rule against downloading/executing untrusted binaries),
it was inventoried honestly by running `strings` over `Kundli-Lite.exe`,
`kkundli.dll` and `kkundli1.dll` and reading `Kundli.cnt` (the WinHelp table
of contents), rather than guessed. That inventory found: two main modes
(`&Horoscope` / `&Match-Making`), a chart-style selector (`cmbCharting`), an
ayanamsha selector (`cmbAyanamsa`), a Rahu/Ketu method selector
(`cmbRahuKetu`), a "Housenos" toggle, a `frmSudarshan` form, a
`frameVarshPhal` section ("Varshphal for the year starting from", "Yogini
Pratyantar from the year starting"), and a Settings form with report
letterhead fields (`txtName`/`txtAddr`/`txtPhones`/`txtFooterTop`) plus
Print/Print Preview menu items. No evidence of Navamsa/varga charts,
Ashtakavarga, or a working Hindi-language mode was found, so none of those
were added.

Reimplemented from that inventory, in `astrowatch_kundli_studio.html`:

- **Kundli chart picture**: an SVG chart (North Indian fixed-diamond,
  South Indian fixed-grid, or a Sudarshan Chakra of three side-by-side
  Lagna/Chandra/Surya diamonds), with houses/signs and graha placements,
  downloadable as a PNG via canvas rasterization. Chart geometry was derived
  from first principles (the four "kendra" houses 1/4/7/10 are the four kite
  shapes touching each edge midpoint of the diamond; the eight corner
  triangles are houses 2/3/5/6/8/9/11/12) and unit-tested: for every graha,
  the cell it lands in always shows that graha's own sign number, and the
  South Indian grid places all 9 grahas exactly once.
- **Yogini Dasha** (36-year, 8-Yogini system) with Pratyantar sub-periods.
  Starting-Yogini formula -- remainder of (nakshatra number + 3) / 8 --
  verified via live web search this session against multiple concurring
  sources (not reproduced from memory alone).
- **Varshaphal**: the annual solar-return chart (tropical Sun returns to its
  exact natal longitude -- solved numerically, verified to sub-microdegree
  accuracy) and Muntha. Deliberately does NOT compute the classical
  Varsheshwar (year-lord), which requires comparing five candidate lords'
  relative strength (Panchadhikari) -- traditional sources were not
  consistent enough for this project to be confident implementing it
  correctly, so it was left out rather than guessed.
- **Match-Making (Ashtakoot Guna Milan)**: all 8 kootas (Varna, Vashya,
  Tara, Yoni, Graha Maitri, Gana, Bhakoot, Nadi; 36 points total), as a
  second mode alongside Horoscope, mirroring the old software's two-mode
  toolbar. Every table (Yoni's 27-nakshatra-to-14-animal map and its
  friend/neutral/unfriendly/hostile matrix; Gana and Nadi's per-nakshatra
  groupings; the Graha Maitri planetary-friendship table; Varna/Bhakoot
  sign rules) was checked against live sources this session
  (astrolozyy.com, findyourfate.com) rather than recalled from memory, and
  spot-checked in code against the worked examples those sources gave (e.g.
  Aries-Virgo triggers Bhakoot Dosha at the stated 6-8 relationship;
  Horse-Buffalo scores 0 as a stated hostile Yoni pair). Two simplifications
  are explicitly disclosed in the code and in-app: Vashya's traditional
  middle "controls the other" 1-point tier is collapsed to 0 (sources
  disagreed on the exact control pairs), and Graha Maitri's one
  unspecified compound case (neutral+enemy) is filled with a documented
  2-point interpolation.
- **Report letterhead** (prepared-by name/address/phone) shown on the
  printed report and exported PNG, plus a Print button using the browser's
  native print dialog with a print stylesheet.

All new math was unit-tested via Node before integration (Vimshottari and
Yogini sequences sum to their correct total years; Antardasha/Pratyantardasha/
Yogini-Pratyantar durations sum exactly to their parent period; the
solar-return solver converges to sub-microdegree Sun-longitude error; the
Ashtakoot scorer reproduces every worked example given by the sources
consulted). The full UI flow (all three chart styles, PNG export, Yogini/
Varshaphal sections, .kun save/load round-trip, Match-Making tab, letterhead
+ print) was also tested headlessly via jsdom.
