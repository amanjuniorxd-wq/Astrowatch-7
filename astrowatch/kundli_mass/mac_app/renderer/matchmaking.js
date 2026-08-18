/* ===== Ashtakoot Guna Milan (36-point match-making) =====
   Reengineers the old software's second major mode ("&Match-Making" /
   "Click here to prepare Match", duplicate boy/girl birth-data fields in
   the original exe). All 8 koota tables below were checked against live
   web sources this session (astrolozyy.com's Kundali Matching Points
   guide for Varna/Vashya/Tara/Graha-Maitri/Gana/Bhakoot/Nadi point rules
   and category tables; findyourfate.com's dedicated Yoni Kuta page for the
   27-nakshatra-to-14-animal table and the full friend/neutral/unfriendly/
   hostile animal matrix), not reproduced from memory alone.

   Two DISCLOSED simplifications (documented here, not silently applied):
   1. Vashya Koota's traditional middle "one sign is vashya-of / controls
      the other" 1-point tier is NOT implemented -- sources did not agree
      closely enough on the exact control-pairs for this project to be
      confident reproducing it correctly. Only "same group = 2" / "else = 0"
      is scored.
   2. Graha Maitri's compound (both-direction) relationship table explicitly
      covers 5 of 6 possible combinations (friend+friend=5, friend+neutral=4,
      neutral+neutral=3, friend+enemy=1, enemy+enemy=0); the 6th case
      (neutral+enemy mixed) was not stated by the source consulted and is
      filled in here at 2 points as a reasonable, disclosed interpolation.

   This calculator does NOT auto-apply traditional dosha-cancellation
   exceptions (e.g. Nadi Dosha cancellation when nakshatras differ within
   the same Nadi group, or Bhakoot Dosha cancellation when sign lords are
   friends) -- these are reported as flags for a human to weigh, consistent
   with how actual astrologers apply them case-by-case rather than
   mechanically. */

var VARNA_OF_RASHI = { 3:"Brahmin",7:"Brahmin",11:"Brahmin", 0:"Kshatriya",4:"Kshatriya",8:"Kshatriya", 1:"Vaishya",5:"Vaishya",9:"Vaishya", 2:"Shudra",6:"Shudra",10:"Shudra" };
var VARNA_RANK = { "Brahmin":4, "Kshatriya":3, "Vaishya":2, "Shudra":1 };

var GANA_OF_NAK = {};
["Ashwini","Mrigashira","Punarvasu","Pushya","Hasta","Swati","Anuradha","Shravana","Revati"].forEach(function(n){GANA_OF_NAK[n]="Deva";});
["Bharani","Rohini","Ardra","Purva Phalguni","Uttara Phalguni","Purva Ashadha","Uttara Ashadha","Purva Bhadrapada","Uttara Bhadrapada"].forEach(function(n){GANA_OF_NAK[n]="Manushya";});
["Krittika","Ashlesha","Magha","Chitra","Vishakha","Jyeshtha","Mula","Dhanishta","Shatabhisha"].forEach(function(n){GANA_OF_NAK[n]="Rakshasa";});

var NADI_OF_NAK = {};
["Ashwini","Ardra","Punarvasu","Uttara Phalguni","Hasta","Jyeshtha","Mula","Shatabhisha","Purva Bhadrapada"].forEach(function(n){NADI_OF_NAK[n]="Aadi";});
["Bharani","Mrigashira","Pushya","Purva Phalguni","Chitra","Anuradha","Purva Ashadha","Dhanishta","Uttara Bhadrapada"].forEach(function(n){NADI_OF_NAK[n]="Madhya";});
["Krittika","Rohini","Ashlesha","Magha","Swati","Vishakha","Uttara Ashadha","Shravana","Revati"].forEach(function(n){NADI_OF_NAK[n]="Antya";});

var YONI_OF_NAK = {
  Ashwini:"Horse", Shatabhisha:"Horse",
  Bharani:"Elephant", Revati:"Elephant",
  Krittika:"Sheep", Pushya:"Sheep",
  Rohini:"Serpent", Mrigashira:"Serpent",
  Ardra:"Dog", Mula:"Dog",
  Punarvasu:"Cat", Ashlesha:"Cat",
  Magha:"Rat", "Purva Phalguni":"Rat",
  "Uttara Phalguni":"Cow", "Uttara Bhadrapada":"Cow",
  Hasta:"Buffalo", Swati:"Buffalo",
  Chitra:"Tiger", Vishakha:"Tiger",
  Anuradha:"Deer", Jyeshtha:"Deer",
  "Purva Ashadha":"Monkey", Shravana:"Monkey",
  "Uttara Ashadha":"Mongoose",
  Dhanishta:"Lion", "Purva Bhadrapada":"Lion"
};
var YONI_HOSTILE_PAIRS = [["Horse","Buffalo"],["Elephant","Lion"],["Sheep","Monkey"],["Serpent","Mongoose"],["Cat","Rat"],["Cow","Tiger"]];
var YONI_FRIENDLY = { Horse:["Serpent","Monkey"], Elephant:["Sheep","Serpent","Buffalo","Monkey"], Sheep:["Elephant","Cow","Buffalo","Mongoose"], Serpent:["Horse","Elephant"], Dog:[], Cat:["Monkey"], Rat:[], Cow:["Sheep","Buffalo"], Buffalo:["Elephant","Sheep","Cow"], Tiger:[], Monkey:["Horse","Elephant","Cat","Mongoose"], Mongoose:["Sheep","Monkey"], Lion:[] };
var YONI_NEUTRAL = { Horse:["Elephant","Sheep","Dog","Cat","Mongoose"], Elephant:["Sheep","Serpent","Buffalo","Monkey"], Sheep:["Elephant","Cow","Buffalo","Mongoose"], Serpent:["Horse","Elephant"], Dog:["Horse","Elephant","Serpent","Cat","Cow","Buffalo","Monkey"], Cat:["Horse","Elephant","Sheep","Dog","Cow","Buffalo","Mongoose"], Rat:["Horse","Elephant","Cow","Buffalo","Tiger","Monkey","Lion"], Cow:["Elephant","Dog","Cat","Rat","Monkey","Mongoose"], Buffalo:["Dog","Cat","Rat","Monkey","Mongoose"], Tiger:["Serpent","Rat","Mongoose"], Monkey:["Serpent","Dog","Rat","Cow","Buffalo","Lion"], Mongoose:["Horse","Elephant","Cat","Cow","Buffalo","Tiger","Lion"], Lion:["Serpent","Rat","Buffalo","Monkey","Mongoose"] };

function yoniScore(boyAnimal, girlAnimal) {
  if (boyAnimal === girlAnimal) return 4;
  var hostile = YONI_HOSTILE_PAIRS.some(function(p){ return (p[0]===boyAnimal&&p[1]===girlAnimal)||(p[1]===boyAnimal&&p[0]===girlAnimal); });
  if (hostile) return 0;
  if ((YONI_FRIENDLY[boyAnimal]||[]).indexOf(girlAnimal) !== -1) return 3;
  if ((YONI_NEUTRAL[boyAnimal]||[]).indexOf(girlAnimal) !== -1) return 2;
  return 1; // treated as unfriendly (default when not explicitly friendly/neutral/hostile/same)
}

var GRAHA_LORD_OF_RASHI = ["mars","venus","mercury","moon","sun","mercury","venus","mars","jupiter","saturn","saturn","jupiter"];
var GRAHA_MAITRI_TABLE = {
  sun:     { friends:["moon","mars","jupiter"], enemies:["venus","saturn"] },
  moon:    { friends:["sun","mercury"], enemies:[] },
  mars:    { friends:["sun","moon","jupiter"], enemies:["mercury"] },
  mercury: { friends:["sun","venus"], enemies:["moon"] },
  jupiter: { friends:["sun","moon","mars"], enemies:["mercury","venus"] },
  venus:   { friends:["mercury","saturn"], enemies:["sun","moon"] },
  saturn:  { friends:["mercury","venus"], enemies:["sun","moon","mars"] }
};
function grahaRelation(fromLord, toLord) {
  if (fromLord === toLord) return "friend";
  var t = GRAHA_MAITRI_TABLE[fromLord];
  if (t.friends.indexOf(toLord) !== -1) return "friend";
  if (t.enemies.indexOf(toLord) !== -1) return "enemy";
  return "neutral";
}
function grahaMaitriScore(boyLord, girlLord) {
  var r1 = grahaRelation(boyLord, girlLord), r2 = grahaRelation(girlLord, boyLord);
  var has = function(a,b){ return (r1===a&&r2===b)||(r1===b&&r2===a); };
  if (has("friend","friend")) return 5;
  if (has("friend","neutral")) return 4;
  if (has("neutral","neutral")) return 3;
  if (has("friend","enemy")) return 1;
  if (has("enemy","enemy")) return 0;
  return 2; // neutral-enemy mixed: not explicitly stated by source, disclosed interpolation
}

function taraScore(nakA1based, nakB1based) {
  function countAndRemainder(from, to) {
    var count = ((to - from + 27) % 27) + 1;
    var rem = count % 9;
    if (rem === 0) rem = 9;
    return rem;
  }
  var FAVORABLE = {1:1,2:1,4:1,6:1,8:1,9:1};
  var r1 = countAndRemainder(nakA1based, nakB1based);
  var r2 = countAndRemainder(nakB1based, nakA1based);
  var fav1 = !!FAVORABLE[r1], fav2 = !!FAVORABLE[r2];
  if (fav1 && fav2) return 3;
  if (fav1 || fav2) return 1.5;
  return 0;
}

function vashyaGroupOf(rashiIdx, degInSign) {
  // rashiIdx: 0=Mesha..11=Meena. degInSign: 0-30 within the sign.
  if ([2,5,6,10].indexOf(rashiIdx) !== -1) return "Manav"; // Mithuna,Kanya,Tula,Kumbha
  if (rashiIdx === 4) return "Vanchar"; // Simha
  if (rashiIdx === 7) return "Keeta"; // Vrischika
  if (rashiIdx === 8) return degInSign < 15 ? "Manav" : "Chatushpad"; // Dhanu split
  if (rashiIdx === 9) return degInSign < 15 ? "Chatushpad" : "Jalchar"; // Makara split
  if (rashiIdx === 0 || rashiIdx === 1) return "Chatushpad"; // Mesha, Vrishabha
  if (rashiIdx === 3 || rashiIdx === 11) return "Jalchar"; // Karka, Meena
  return "Manav";
}

function bhakootScore(boyRashiIdx, girlRashiIdx) {
  var d = ((girlRashiIdx - boyRashiIdx + 12) % 12) + 1;
  var DOSHA_SET = {2:1,5:1,6:1,8:1,9:1,12:1};
  return DOSHA_SET[d] ? 0 : 7;
}

/* person: { moonSiderealLon, rashiIdx, nakshatraNum (1-27), nakshatraName } */
function computeAshtakoot(boy, girl) {
  var out = { items: [] };
  var add = function(name, max, score, detail) { out.items.push({name:name, max:max, score:score, detail:detail}); };

  var boyVarna = VARNA_OF_RASHI[boy.rashiIdx], girlVarna = VARNA_OF_RASHI[girl.rashiIdx];
  add("Varna", 1, (VARNA_RANK[boyVarna] >= VARNA_RANK[girlVarna]) ? 1 : 0, boyVarna+" / "+girlVarna);

  var boyVashya = vashyaGroupOf(boy.rashiIdx, boy.degInSign), girlVashya = vashyaGroupOf(girl.rashiIdx, girl.degInSign);
  add("Vashya", 2, (boyVashya === girlVashya) ? 2 : 0, boyVashya+" / "+girlVashya);

  add("Tara", 3, taraScore(boy.nakshatraNum, girl.nakshatraNum), "nak#"+boy.nakshatraNum+" / nak#"+girl.nakshatraNum);

  var boyYoni = YONI_OF_NAK[boy.nakshatraName], girlYoni = YONI_OF_NAK[girl.nakshatraName];
  add("Yoni", 4, yoniScore(boyYoni, girlYoni), boyYoni+" / "+girlYoni);

  var boyLord = GRAHA_LORD_OF_RASHI[boy.rashiIdx], girlLord = GRAHA_LORD_OF_RASHI[girl.rashiIdx];
  add("Graha Maitri", 5, grahaMaitriScore(boyLord, girlLord), boyLord+" / "+girlLord);

  var boyGana = GANA_OF_NAK[boy.nakshatraName], girlGana = GANA_OF_NAK[girl.nakshatraName];
  var ganaScore = (boyGana === girlGana) ? 6 : ( (boyGana==="Deva"&&girlGana==="Manushya")||(boyGana==="Manushya"&&girlGana==="Deva") ? 5 : ( (boyGana==="Manushya"&&girlGana==="Rakshasa")||(boyGana==="Rakshasa"&&girlGana==="Manushya") ? 1 : 0 ) );
  add("Gana", 6, ganaScore, boyGana+" / "+girlGana);

  add("Bhakoot", 7, bhakootScore(boy.rashiIdx, girl.rashiIdx), RASHI_NAMES[boy.rashiIdx]+" / "+RASHI_NAMES[girl.rashiIdx]);

  var boyNadi = NADI_OF_NAK[boy.nakshatraName], girlNadi = NADI_OF_NAK[girl.nakshatraName];
  add("Nadi", 8, (boyNadi === girlNadi) ? 0 : 8, boyNadi+" / "+girlNadi);

  var total = out.items.reduce(function(s,i){return s+i.score;}, 0);
  out.total = total;
  out.maxTotal = 36;
  out.doshas = [];
  if (out.items[6].score === 0) out.doshas.push("Bhakoot Dosha");
  if (out.items[7].score === 0) out.doshas.push("Nadi Dosha");
  if (ganaScore === 0) out.doshas.push("Gana Dosha");
  return out;
}
