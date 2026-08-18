/* ===== Varshaphal (annual solar-return chart) + Muntha =====
   Old software had a "Varshphal for the year starting from" / "Number of
   years for prediction" field (frameVarshPhal). This reimplements the
   solar-return event itself (a precise, well-defined astronomical moment:
   the instant the tropical Sun returns to its exact natal longitude) plus
   Muntha (a single well-defined classical rule: natal Ascendant sign
   advanced by the completed age in years).

   NOT implemented: the classical "Varsheshwar" (year-lord) determination,
   which traditionally compares the relative strength of five candidate
   lords (Dinesh/day-lord, Muntheshwar/Muntha-lord, Varsheshwar-proper,
   Trirashesh, Dwadashesh) via a multi-factor strength (Panchadhikari)
   comparison. That comparison has enough traditional variation and
   intricacy that this project is not confident it could implement it
   correctly without an authoritative reference to verify against --
   consistent with this project's rule to stop and disclose rather than
   silently approximate. Muntha, Varshapati candidates and full Mudda Dasha
   are therefore NOT computed here. */
function solarReturnJd(natalJd, natalSunTropicalLon, targetAge) {
  var guess = natalJd + targetAge * 365.2425;
  for (var i = 0; i < 8; i++) {
    var curLon = sunEclipticLongitude(guess);
    var diff = norm180(natalSunTropicalLon - curLon);
    if (Math.abs(diff) < 1e-6) break;
    guess += diff / 0.9856002585;
  }
  return guess;
}
function munthaRashi(ascRashiIdx, completedAge) {
  var idx = (ascRashiIdx + (completedAge % 12)) % 12;
  return { index: idx, name: RASHI_NAMES[idx] };
}
