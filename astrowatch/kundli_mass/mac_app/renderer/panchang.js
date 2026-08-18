/* ===== Basic Panchang (Tithi/Yoga/Karana/Vaar) -- standard classical
   definitions, computed from Sun-Moon tropical longitudes (the ayanamsha
   cancels out in the difference/sum, so tropical vs sidereal doesn't matter
   here). New to this webapp -- not present in the earlier life-report app. */
var TITHI_NAMES = ["Pratipada","Dwitiya","Tritiya","Chaturthi","Panchami","Shashthi","Saptami","Ashtami","Navami","Dashami","Ekadashi","Dwadashi","Trayodashi","Chaturdashi"];
var YOGA_NAMES = ["Vishkambha","Priti","Ayushman","Saubhagya","Shobhana","Atiganda","Sukarma","Dhriti","Shoola","Ganda","Vriddhi","Dhruva","Vyaghata","Harshana","Vajra","Siddhi","Vyatipata","Variyana","Parigha","Shiva","Siddha","Sadhya","Shubha","Shukla","Brahma","Indra","Vaidhriti"];
var KARANA_MOVABLE = ["Bava","Balava","Kaulava","Taitila","Gara","Vanija","Vishti"];
var WEEKDAY_NAMES = ["Ravivar (Sunday)","Somvar (Monday)","Mangalvar (Tuesday)","Budhvar (Wednesday)","Guruvar (Thursday)","Shukravar (Friday)","Shanivar (Saturday)"];

function computeTithi(sunTropical, moonTropical) {
  var diff = norm360(moonTropical - sunTropical);
  var idx = Math.floor(diff / 12); // 0..29
  var paksha = idx < 15 ? "Shukla Paksha" : "Krishna Paksha";
  var within = idx % 15;
  var name;
  if (idx === 14) name = "Purnima";
  else if (idx === 29) name = "Amavasya";
  else name = TITHI_NAMES[within];
  return { index: idx, paksha: paksha, name: name, percentComplete: Math.round(((diff % 12) / 12) * 1000)/10 };
}
function computeYoga(sunTropical, moonTropical) {
  var sum = norm360(moonTropical + sunTropical);
  var w = 360/27;
  var idx = Math.floor(sum / w) % 27;
  return { index: idx, name: YOGA_NAMES[idx] };
}
function computeKarana(sunTropical, moonTropical) {
  var diff = norm360(moonTropical - sunTropical);
  var half = Math.floor(diff / 6) % 60; // 0..59
  var name;
  if (half === 0) name = "Kimstughna";
  else if (half >= 57) name = ["Shakuni","Chatushpada","Naga"][half - 57];
  else name = KARANA_MOVABLE[(half - 1) % 7];
  return { index: half, name: name };
}
function computeVaar(y, mo, d) {
  var idx = new Date(Date.UTC(y, mo - 1, d)).getUTCDay();
  return { index: idx, name: WEEKDAY_NAMES[idx] };
}
