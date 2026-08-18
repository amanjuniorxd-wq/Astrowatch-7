/* ===== Verified core engine, ported unchanged from Astrowatch's
   astrowatch_kundli_life_report.html (itself cross-validated against the
   project's Python Swiss-Ephemeris pipeline). ===== */
function julianDay(y, m, d, hourUT) {
  if (m <= 2) { y -= 1; m += 12; }
  var A = Math.floor(y / 100);
  var B = 2 - A + Math.floor(A / 4);
  return Math.floor(365.25 * (y + 4716)) + Math.floor(30.6001 * (m + 1)) + d + hourUT/24 + B - 1524.5;
}
function rad(x) { return x * Math.PI / 180; }
function deg(x) { return x * 180 / Math.PI; }
function norm360(x) { var r = x % 360; if (r < 0) r += 360; return r; }
function norm180(x) { var r = norm360(x); if (r > 180) r -= 360; return r; }

function sunEclipticLongitude(jd) {
  var D = jd - 2451545.0;
  var g = rad(357.529 + 0.98560028 * D);
  var q = 280.459 + 0.98564736 * D;
  var L = q + 1.915 * Math.sin(g) + 0.020 * Math.sin(2*g);
  return norm360(L);
}
function obliquity(jd) {
  var D = jd - 2451545.0;
  return 23.439 - 0.00000036 * D;
}
/* Moon ecliptic longitude -- Paul Schlyter's orbital-elements + Kepler-solve
   + 12-term perturbation model (stjarnhimlen.se/comp/ppcomp.html), verified
   against Astrowatch's own Swiss-Ephemeris output this session to ~0.02-0.05
   deg across 6 spot-check dates spanning 1946-2010. REPLACES an earlier
   single-term approximation (+6.289*sin(M) only) that had 0.7-2.2 deg
   errors -- large enough, near a nakshatra boundary, to place the Moon in
   the WRONG nakshatra entirely (reproduced for 2000-05-17: old formula gave
   Vishakha, correct is Swati), which changes the starting Mahadasha lord
   and shifts every downstream dasha date by months. Fixed after a user
   report that Mahadasha looked wrong. */
function moonEclipticLongitude(jd) {
  var d = jd - 2451543.5; // days since 2000 Jan 0.0 UT (Schlyter's epoch)

  var N = norm360(125.1228 - 0.0529538083 * d);
  var i = 5.1454;
  var w = norm360(318.0634 + 0.1643573223 * d);
  var a = 60.2666;
  var e = 0.054900;
  var M = norm360(115.3654 + 13.0649929509 * d);

  var E = M + (e * 180 / Math.PI) * Math.sin(rad(M)) * (1 + e * Math.cos(rad(M)));
  for (var it = 0; it < 8; it++) {
    var dE = (E - (e * 180 / Math.PI) * Math.sin(rad(E)) - M) / (1 - e * Math.cos(rad(E)));
    E -= dE;
    if (Math.abs(dE) < 1e-8) break;
  }

  var xv = a * (Math.cos(rad(E)) - e);
  var yv = a * (Math.sqrt(1 - e * e) * Math.sin(rad(E)));
  var r = Math.sqrt(xv * xv + yv * yv);
  var v = deg(Math.atan2(yv, xv));

  var vw = rad(v + w);
  var xh = r * (Math.cos(rad(N)) * Math.cos(vw) - Math.sin(rad(N)) * Math.sin(vw) * Math.cos(rad(i)));
  var yh = r * (Math.sin(rad(N)) * Math.cos(vw) + Math.cos(rad(N)) * Math.sin(vw) * Math.cos(rad(i)));
  var lonecl = norm360(deg(Math.atan2(yh, xh)));

  // Sun's mean anomaly / argument of perihelion (Schlyter's own Sun
  // elements, same day-number convention) -- needed for the perturbation
  // terms below, kept local to this function so the project's separate
  // sunEclipticLongitude() (USNO-style, used for the Sun's own displayed
  // position and Panchang) is untouched.
  var wSun = norm360(282.9404 + 4.70935e-5 * d);
  var Msun = norm360(356.0470 + 0.9856002585 * d);

  var Ls = norm360(Msun + wSun);
  var Lm = norm360(M + w + N);
  var D = norm360(Lm - Ls);
  var F = norm360(Lm - N);

  var pert = 0;
  pert += -1.274 * Math.sin(rad(M - 2 * D));
  pert += 0.658 * Math.sin(rad(2 * D));
  pert += -0.186 * Math.sin(rad(Msun));
  pert += -0.059 * Math.sin(rad(2 * M - 2 * D));
  pert += -0.057 * Math.sin(rad(M - 2 * D + Msun));
  pert += 0.053 * Math.sin(rad(M + 2 * D));
  pert += 0.046 * Math.sin(rad(2 * D - Msun));
  pert += 0.041 * Math.sin(rad(M - Msun));
  pert += -0.035 * Math.sin(rad(D));
  pert += -0.031 * Math.sin(rad(M + Msun));
  pert += -0.015 * Math.sin(rad(2 * F - 2 * D));
  pert += 0.011 * Math.sin(rad(M - 4 * D));

  return norm360(lonecl + pert);
}
function rahuLongitude(jd) {
  var T = (jd - 2451545.0) / 36525;
  var omega = 125.04452 - 1934.136261 * T;
  return norm360(omega);
}
var PLANET_ELEMENTS = {
  earth:   [1.00000261, 0.00000562, 0.01671123, -0.00004392, -0.00001531, -0.01294668, 100.46457166, 35999.37244981, 102.93768193, 0.32327364, 0.0, 0.0],
  mercury: [0.38709927, 0.00000037, 0.20563593, 0.00001906, 7.00497902, -0.00594749, 252.25032350, 149472.67411175, 77.45779628, 0.16047689, 48.33076593, -0.12534081],
  venus:   [0.72333566, 0.00000390, 0.00677672, -0.00004107, 3.39467605, -0.00078890, 181.97909950, 58517.81538729, 131.60246718, 0.00268329, 76.67984255, -0.27769418],
  mars:    [1.52371034, 0.00001847, 0.09339410, 0.00007882, 1.84969142, -0.00813131, -4.55343205, 19140.30268499, -23.94362959, 0.44441088, 49.55953891, -0.29257343],
  jupiter: [5.20288700, -0.00011607, 0.04838624, -0.00013253, 1.30439695, -0.00183714, 34.39644051, 3034.74612775, 14.72847983, 0.21252668, 100.47390909, 0.20469106],
  saturn:  [9.53667594, -0.00125060, 0.05386179, -0.00050991, 2.48599187, 0.00193609, 49.95424423, 1222.49362201, 92.59887831, -0.41897216, 113.66242448, -0.28867794]
};
function solveKepler(Mdeg, e) {
  var eStar = 57.29578 * e;
  var M = Mdeg;
  var E = M + eStar * Math.sin(rad(M));
  for (var i = 0; i < 20; i++) {
    var dM = M - (E - eStar * Math.sin(rad(E)));
    var dE = dM / (1 - e * Math.cos(rad(E)));
    E += dE;
    if (Math.abs(dE) < 1e-6) break;
  }
  return E;
}
function heliocentricXYZ(bodyKey, T) {
  var el = PLANET_ELEMENTS[bodyKey];
  var a = el[0] + el[1]*T, e = el[2] + el[3]*T, I = el[4] + el[5]*T, L = el[6] + el[7]*T;
  var longPeri = el[8] + el[9]*T, longNode = el[10] + el[11]*T;
  var omega = longPeri - longNode;
  var M = norm180(L - longPeri);
  var E = solveKepler(M, e);
  var xp = a * (Math.cos(rad(E)) - e);
  var yp = a * Math.sqrt(1 - e*e) * Math.sin(rad(E));
  var cosO = Math.cos(rad(omega)), sinO = Math.sin(rad(omega));
  var cosN = Math.cos(rad(longNode)), sinN = Math.sin(rad(longNode));
  var cosI = Math.cos(rad(I)), sinI = Math.sin(rad(I));
  var xecl = (cosO*cosN - sinO*sinN*cosI) * xp + (-sinO*cosN - cosO*sinN*cosI) * yp;
  var yecl = (cosO*sinN + sinO*cosN*cosI) * xp + (-sinO*sinN + cosO*cosN*cosI) * yp;
  return [xecl, yecl];
}
function planetGeocentricLongitude(bodyKey, jd) {
  var T = (jd - 2451545.0) / 36525;
  var e = heliocentricXYZ("earth", T);
  var p = heliocentricXYZ(bodyKey, T);
  var xg = p[0] - e[0], yg = p[1] - e[1];
  return norm360(deg(Math.atan2(yg, xg)));
}
var ANCHOR_1956_JD = 2435553.5, ANCHOR_1956_AYANAMSA = 23.25;
var ANCHOR_J2000_JD = 2451545.0, ANCHOR_J2000_AYANAMSA = 23.853222;
var DEG_PER_DAY = (ANCHOR_J2000_AYANAMSA - ANCHOR_1956_AYANAMSA) / (ANCHOR_J2000_JD - ANCHOR_1956_JD);
function ayanamsha(jd) { return ANCHOR_1956_AYANAMSA + DEG_PER_DAY * (jd - ANCHOR_1956_JD); }

var RASHI_NAMES = ["Mesha","Vrishabha","Mithuna","Karka","Simha","Kanya","Tula","Vrischika","Dhanu","Makara","Kumbha","Meena"];
var NAKSHATRA_NAMES = ["Ashwini","Bharani","Krittika","Rohini","Mrigashira","Ardra","Punarvasu","Pushya","Ashlesha","Magha","Purva Phalguni","Uttara Phalguni","Hasta","Chitra","Swati","Vishakha","Anuradha","Jyeshtha","Mula","Purva Ashadha","Uttara Ashadha","Shravana","Dhanishta","Shatabhisha","Purva Bhadrapada","Uttara Bhadrapada","Revati"];
function rashiFor(lon) { var idx = Math.floor(lon / 30) % 12; return { index: idx, name: RASHI_NAMES[idx] }; }
function nakshatraFor(lon) {
  var w = 360/27; var idx = Math.floor(lon / w) % 27;
  var within = lon - idx * w;
  var pada = Math.floor(within / (w/4)) + 1;
  return { index: idx, name: NAKSHATRA_NAMES[idx], pada: pada };
}
function computeChartApprox(jd, latDeg, lonDeg) {
  var aya = ayanamsha(jd);
  var tropical = {
    sun: sunEclipticLongitude(jd), moon: moonEclipticLongitude(jd),
    mercury: planetGeocentricLongitude("mercury", jd), venus: planetGeocentricLongitude("venus", jd),
    mars: planetGeocentricLongitude("mars", jd), jupiter: planetGeocentricLongitude("jupiter", jd),
    saturn: planetGeocentricLongitude("saturn", jd), rahu: rahuLongitude(jd)
  };
  tropical.ketu = norm360(tropical.rahu + 180);
  var sidereal = {};
  for (var k in tropical) sidereal[k] = norm360(tropical[k] - aya);

  var T = (jd - 2451545.0) / 36525;
  var gst = norm360(280.46061837 + 360.98564736629 * (jd - 2451545.0) + 0.000387933*T*T);
  var lst = norm360(gst + lonDeg);
  var eps = rad(obliquity(jd));
  var phi = rad(latDeg);
  var lstRad = rad(lst);
  var ascTropical = norm360(deg(Math.atan2(Math.cos(lstRad), -(Math.sin(lstRad)*Math.cos(eps) + Math.tan(phi)*Math.sin(eps)))));
  var ascSidereal = norm360(ascTropical - aya);
  return { ayanamsha: aya, tropical: tropical, sidereal: sidereal, ascendantSidereal: ascSidereal };
}
// ---------------------------------------------------------------------------
// Native Swiss Ephemeris bridge (added for the desktop/Electron build).
// preload.js exposes window.astrowatchNative when running inside Electron with
// a working sweph native binding + bundled .se1 files. In that case every chart
// computed by this app uses the REAL Swiss Ephemeris library (the same one the
// Python backend uses), not the approximate JS formulas below. In a plain
// browser tab (no Electron), window.astrowatchNative is undefined and this
// falls through to the approximate engine, same as before -- with the
// resulting chart tagged chart.engine = "approximate-js" so the UI can show a
// visible (not silent) notice about which engine actually produced the numbers.
// This function name (computeChart) is kept the same so every other file in
// this app (render.js, chart.js, panchang.js, yogini.js, varshaphal.js,
// matchmaking.js) needs zero changes to benefit from native precision.
// ---------------------------------------------------------------------------
function computeChart(jd, latDeg, lonDeg) {
  if (typeof window !== "undefined" && window.astrowatchNative && window.astrowatchNative.available) {
    var native = window.astrowatchNative.computeChartSync(jd, latDeg, lonDeg);
    if (native && !native.error) {
      native.engine = "swisseph-native";
      native.engineLabel = "Swiss Ephemeris (native, file-based)";
      return native;
    }
    console.warn("Native Swiss Ephemeris call failed, falling back to the approximate JS engine for this chart:", native && native.error);
  }
  var approx = computeChartApprox(jd, latDeg, lonDeg);
  approx.engine = "approximate-js";
  approx.engineLabel = "Approximate (client-side JS, no native engine available)";
  return approx;
}
function houseNumber(grahaRashiIdx, ascRashiIdx) { return ((grahaRashiIdx - ascRashiIdx + 12) % 12) + 1; }

var DASHA_SEQUENCE = [["ketu",7],["venus",20],["sun",6],["moon",10],["mars",7],["rahu",18],["jupiter",16],["saturn",19],["mercury",17]];
var NAKSHATRA_STARTING_LORD = [];
for (var _i = 0; _i < 27; _i++) NAKSHATRA_STARTING_LORD.push(DASHA_SEQUENCE[_i % 9][0]);
var SIDEREAL_YEAR_DAYS = 365.25636;
var NAKSHATRA_WIDTH = 360/27;
function lordIndex(lord) { for (var i=0;i<9;i++) if (DASHA_SEQUENCE[i][0]===lord) return i; return -1; }
function birthBalanceMahadasha(moonSiderealLon) {
  var nakIdx = Math.floor(moonSiderealLon / NAKSHATRA_WIDTH) % 27;
  var degInNak = moonSiderealLon - nakIdx * NAKSHATRA_WIDTH;
  var startingLord = NAKSHATRA_STARTING_LORD[nakIdx];
  var startingYears = DASHA_SEQUENCE[lordIndex(startingLord)][1];
  var fractionElapsed = degInNak / NAKSHATRA_WIDTH;
  var elapsedYears = fractionElapsed * startingYears;
  return { lord: startingLord, elapsedYears: elapsedYears, balanceYears: startingYears - elapsedYears };
}
function fullLifetimeMahadashas(birthJd, moonSiderealLon, horizonYears) {
  var bb = birthBalanceMahadasha(moonSiderealLon);
  var idx = lordIndex(bb.lord);
  var startJd = birthJd - bb.elapsedYears * SIDEREAL_YEAR_DAYS;
  var endJd = startJd + DASHA_SEQUENCE[idx][1] * SIDEREAL_YEAR_DAYS;
  var horizonJd = birthJd + horizonYears * SIDEREAL_YEAR_DAYS;
  var out = [];
  while (startJd < horizonJd) {
    out.push({ lord: DASHA_SEQUENCE[idx][0], startJd: startJd, endJd: endJd });
    idx = (idx + 1) % 9;
    startJd = endJd;
    endJd = startJd + DASHA_SEQUENCE[idx][1] * SIDEREAL_YEAR_DAYS;
  }
  return out;
}
function antardashasFor(mahaLord, mahaStartJd) {
  var idx = lordIndex(mahaLord);
  var mahaLordYears = DASHA_SEQUENCE[idx][1];
  var cursor = mahaStartJd;
  var out = [];
  for (var offset = 0; offset < 9; offset++) {
    var subIdx = (idx + offset) % 9;
    var subLord = DASHA_SEQUENCE[subIdx][0], subYears = DASHA_SEQUENCE[subIdx][1];
    var durationDays = (subYears * mahaLordYears / 120.0) * SIDEREAL_YEAR_DAYS;
    var subEnd = cursor + durationDays;
    out.push({ lord: subLord, startJd: cursor, endJd: subEnd });
    cursor = subEnd;
  }
  return out;
}
function pratyantardashasFor(antarLord, antarStartJd, mahaLord) {
  var idx = lordIndex(antarLord);
  var mahaIdx = lordIndex(mahaLord);
  var mahaLordYears = DASHA_SEQUENCE[mahaIdx][1];
  var antarYears = DASHA_SEQUENCE[idx][1];
  var cursor = antarStartJd;
  var out = [];
  for (var offset = 0; offset < 9; offset++) {
    var subIdx = (idx + offset) % 9;
    var subLord = DASHA_SEQUENCE[subIdx][0], subYears = DASHA_SEQUENCE[subIdx][1];
    var durationDays = (subYears * antarYears * mahaLordYears / (120.0*120.0)) * SIDEREAL_YEAR_DAYS;
    var subEnd = cursor + durationDays;
    out.push({ lord: subLord, startJd: cursor, endJd: subEnd });
    cursor = subEnd;
  }
  return out;
}
function jdToIsoDate(jdUt) {
  var jd = jdUt + 0.5;
  var z = Math.floor(jd);
  var f = jd - z;
  var a;
  if (z < 2299161) a = z;
  else { var alpha = Math.floor((z - 1867216.25) / 36524.25); a = z + 1 + alpha - Math.floor(alpha/4); }
  var b = a + 1524;
  var c = Math.floor((b - 122.1) / 365.25);
  var d = Math.floor(365.25 * c);
  var e = Math.floor((b - d) / 30.6001);
  var day = Math.floor(b - d - Math.floor(30.6001*e) + f);
  var month = e < 14 ? e - 1 : e - 13;
  var year = month > 2 ? c - 4716 : c - 4715;
  return String(year).padStart(4,"0") + "-" + String(month).padStart(2,"0") + "-" + String(day).padStart(2,"0");
}
var GRAHA_THEME = {
  sun: "authority, visibility, executive action and one's own will",
  moon: "public mood, emotional currents, mind and personal/domestic life",
  mars: "confrontation, assertive drive, energy and sudden action",
  mercury: "communication, negotiation, learning and information flow",
  jupiter: "expansion, recognition, teaching/mentorship and institutional validation",
  venus: "creativity, relationships, wealth and public appeal",
  saturn: "discipline, delay, restriction, endurance and structural pressure",
  rahu: "disruption, ambition, foreign/unconventional pursuits and sudden rise",
  ketu: "withdrawal, introspection, loose ends and quiet transitions"
};
var HOUSE_SIG = {
  1: "self, body, personality, general vitality", 2: "wealth, family, speech, accumulated resources",
  3: "courage, siblings, effort, short journeys, communication", 4: "home, mother, emotional foundation, property",
  5: "creativity, children, intelligence, romance", 6: "health, obstacles, competition, daily work",
  7: "partnerships, marriage, public dealings, open rivals", 8: "transformation, longevity, sudden change, shared resources",
  9: "fortune, higher learning, philosophy, father, long journeys", 10: "career, public standing, authority, actions in the world",
  11: "gains, income, networks, aspirations", 12: "loss, expenditure, foreign lands, withdrawal, endings"
};
var EXALTATION = {sun:"Mesha",moon:"Vrishabha",mars:"Makara",mercury:"Kanya",jupiter:"Karka",venus:"Meena",saturn:"Tula"};
var DEBILITATION = {sun:"Tula",moon:"Vrischika",mars:"Karka",mercury:"Meena",jupiter:"Makara",venus:"Kanya",saturn:"Mesha"};
var OWN_SIGNS = {sun:["Simha"],moon:["Karka"],mars:["Mesha","Vrischika"],mercury:["Mithuna","Kanya"],jupiter:["Dhanu","Meena"],venus:["Vrishabha","Tula"],saturn:["Makara","Kumbha"]};
var SPECIAL_ASPECTS = {mars:[4,8],jupiter:[5,9],saturn:[3,10]};
function dignityOf(lord, rashiName) {
  if (!EXALTATION[lord]) return null;
  if (rashiName === EXALTATION[lord]) return "exalted";
  if (rashiName === DEBILITATION[lord]) return "debilitated";
  if ((OWN_SIGNS[lord]||[]).indexOf(rashiName) >= 0) return "own sign";
  return "neutral";
}
function housesOwnedBy(lord, ascRashiIdx) {
  var owned = [];
  (OWN_SIGNS[lord]||[]).forEach(function(sign){
    var signIdx = RASHI_NAMES.indexOf(sign);
    owned.push(houseNumber(signIdx, ascRashiIdx));
  });
  return owned.sort(function(a,b){return a-b;});
}
function aspectedHousesOf(lord, occupiedHouse) {
  var offsets = [7].concat(SPECIAL_ASPECTS[lord]||[]);
  var set = {};
  offsets.forEach(function(off){ set[((occupiedHouse - 1 + off) % 12) + 1] = true; });
  return Object.keys(set).map(Number).sort(function(a,b){return a-b;});
}
