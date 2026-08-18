/* ===== Yogini Dasha (36-year, 8-Yogini system) =====
   Formula verified via web search this session (multiple concurring
   sources, e.g. shubhdivas.in, vedicrishi.in, paramarsh.app -- classical
   source cited as Devi Bhagavata): remainder of (janma-nakshatra-number + 3)
   / 8 selects the starting Yogini. Nakshatra numbering Ashwini=1..Revati=27.
   Sequence order and year-lengths are fixed and always run in this order
   regardless of starting point: Mangala(1) -> Pingala(2) -> Dhanya(3) ->
   Bhramari(4) -> Bhadrika(5) -> Ulka(6) -> Siddha(7) -> Sankata(8) -> repeat.
   Balance-at-birth uses the same proportional-elapsed-nakshatra technique
   as this project's Vimshottari implementation. */
var YOGINI_SEQUENCE = [["Mangala",1],["Pingala",2],["Dhanya",3],["Bhramari",4],["Bhadrika",5],["Ulka",6],["Siddha",7],["Sankata",8]];
function yoginiIndexFromRemainder(rem) { return (rem === 0) ? 7 : rem - 1; } // Sankata = remainder 0 or 8 -> last index
function birthBalanceYogini(moonSiderealLon) {
  var w = 360/27;
  var nakNum = Math.floor(moonSiderealLon / w) + 1; // 1..27
  var rem = (nakNum + 3) % 8;
  var idx = yoginiIndexFromRemainder(rem);
  var degInNak = moonSiderealLon - (nakNum - 1) * w;
  var fractionElapsed = degInNak / w;
  var years = YOGINI_SEQUENCE[idx][1];
  var elapsedYears = fractionElapsed * years;
  return { index: idx, name: YOGINI_SEQUENCE[idx][0], nakshatraNumber: nakNum, elapsedYears: elapsedYears, balanceYears: years - elapsedYears };
}
function fullLifetimeYoginis(birthJd, moonSiderealLon, horizonYears) {
  var bb = birthBalanceYogini(moonSiderealLon);
  var idx = bb.index;
  var startJd = birthJd - bb.elapsedYears * SIDEREAL_YEAR_DAYS;
  var endJd = startJd + YOGINI_SEQUENCE[idx][1] * SIDEREAL_YEAR_DAYS;
  var horizonJd = birthJd + horizonYears * SIDEREAL_YEAR_DAYS;
  var out = [];
  while (startJd < horizonJd) {
    out.push({ lord: YOGINI_SEQUENCE[idx][0], startJd: startJd, endJd: endJd });
    idx = (idx + 1) % 8;
    startJd = endJd;
    endJd = startJd + YOGINI_SEQUENCE[idx][1] * SIDEREAL_YEAR_DAYS;
  }
  return out;
}
/* "Yogini Pratyantar" (sub-period), mirrored from the old software's field
   label ("Yogini Pratyantar from the year starting"). Sub-periods within a
   Yogini Mahadasha follow the same 8-fold proportional split technique used
   for Vimshottari Antardasha (sub-period length proportional to both the
   main period's own duration and the sub-lord's classical year-count). */
function yoginiPratyantarsFor(mainLord, mainStartJd) {
  var idx = -1;
  for (var i=0;i<8;i++) if (YOGINI_SEQUENCE[i][0]===mainLord) idx = i;
  var mainYears = YOGINI_SEQUENCE[idx][1];
  var cursor = mainStartJd;
  var out = [];
  for (var offset = 0; offset < 8; offset++) {
    var subIdx = (idx + offset) % 8;
    var subLord = YOGINI_SEQUENCE[subIdx][0], subYears = YOGINI_SEQUENCE[subIdx][1];
    var durationDays = (subYears * mainYears / 36.0) * SIDEREAL_YEAR_DAYS;
    var subEnd = cursor + durationDays;
    out.push({ lord: subLord, startJd: cursor, endJd: subEnd });
    cursor = subEnd;
  }
  return out;
}
