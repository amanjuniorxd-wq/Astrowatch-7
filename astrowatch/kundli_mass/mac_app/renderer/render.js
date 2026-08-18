/* ===== UI wiring, report rendering, chart pictures, Yogini/Varshaphal,
   match-making, letterhead/print, and .kun save/load ===== */
var PLACES = window.ASTROWATCH_PLACES || [];
var LAST_RESULT = null;   // full computed horoscope result, used for .kun save / print

/* ---- reusable place autocomplete: attaches to any input+list pair,
   calls onSelect({label,lat,lon,utc}) and onClear() when typed text no
   longer matches the confirmed selection ---- */
function attachPlaceAutocomplete(inputEl, listEl, onSelect, onClear) {
  var selected = null;
  inputEl.addEventListener("input", function(){
    selected = null;
    if (onClear) onClear();
    var q = inputEl.value.trim().toLowerCase();
    listEl.innerHTML = "";
    if (q.length < 2) { listEl.style.display = "none"; return; }
    var matches = [];
    for (var i = 0; i < PLACES.length && matches.length < 25; i++) {
      if (PLACES[i][0].toLowerCase().indexOf(q) !== -1) matches.push(PLACES[i]);
    }
    if (!matches.length) { listEl.style.display = "none"; return; }
    matches.forEach(function(p){
      var d = document.createElement("div");
      d.textContent = p[0] + "  (" + p[1].toFixed(2) + ", " + p[2].toFixed(2) + (p[3] != null ? ", UTC" + (p[3]>=0?"+":"") + p[3] : "") + ")";
      d.addEventListener("click", function(){
        selected = { label: p[0], lat: p[1], lon: p[2], utc: p[3] };
        inputEl.value = p[0];
        listEl.style.display = "none";
        onSelect(selected);
      });
      listEl.appendChild(d);
    });
    listEl.style.display = "block";
  });
  document.addEventListener("click", function(ev){
    if (ev.target !== inputEl) listEl.style.display = "none";
  });
  return { get: function(){ return selected; }, set: function(v){ selected = v; } };
}

/* ================= HOROSCOPE MODE ================= */
var selectedPlaceHandle = attachPlaceAutocomplete(
  document.getElementById("in-place"), document.getElementById("place-list"),
  function(){ document.getElementById("btn-save").disabled = true; },
  function(){ document.getElementById("btn-save").disabled = true; }
);

var manualFields = document.getElementById("manual-fields");
document.getElementById("manual-toggle").addEventListener("click", function(){
  manualFields.classList.toggle("show");
});
var letterheadFields = document.getElementById("letterhead-fields");
document.getElementById("letterhead-toggle").addEventListener("click", function(){
  letterheadFields.classList.toggle("show");
});

function showErr(id, msg) {
  var e = document.getElementById(id);
  e.textContent = msg; e.style.display = msg ? "block" : "none";
}

function gatherBirthInputs() {
  var dateStr = document.getElementById("in-date").value;
  var timeStr = document.getElementById("in-time").value;
  if (!dateStr || !timeStr) { showErr("form-err", "Enter a date and time of birth."); return null; }
  var lat, lon, utc, placeLabel;
  var manualOpen = manualFields.classList.contains("show");
  var selectedPlace = selectedPlaceHandle.get();
  if (manualOpen) {
    lat = parseFloat(document.getElementById("in-lat").value);
    lon = parseFloat(document.getElementById("in-lon").value);
    utc = parseFloat(document.getElementById("in-utc").value);
    if (isNaN(lat) || isNaN(lon) || isNaN(utc)) { showErr("form-err", "Enter latitude, longitude and UTC offset, or pick a place above."); return null; }
    placeLabel = "lat " + lat + ", lon " + lon + " (manual)";
  } else if (selectedPlace) {
    lat = selectedPlace.lat; lon = selectedPlace.lon; utc = selectedPlace.utc;
    placeLabel = selectedPlace.label;
    if (utc == null) { showErr("form-err", "This place has no timezone data in the bundled database -- enter coordinates manually instead."); return null; }
  } else {
    showErr("form-err", "Select a place from the list, or enter coordinates manually.");
    return null;
  }
  showErr("form-err", null);
  return {
    dateStr: dateStr, timeStr: timeStr, lat: lat, lon: lon, utc: utc, placeLabel: placeLabel,
    name: document.getElementById("in-name").value || null,
    chartStyle: document.getElementById("in-chart-style").value,
    showHouseNumbers: document.getElementById("in-house-numbers").checked,
    letterhead: {
      name: document.getElementById("lh-name").value || null,
      addr: document.getElementById("lh-addr").value || null,
      phone: document.getElementById("lh-phone").value || null
    }
  };
}

function jdFromLocal(y, mo, d, hh, mm, utc) {
  var localHour = hh + mm/60;
  var utcHour = localHour - utc;
  var jd = julianDay(y, mo, d, ((utcHour % 24) + 24) % 24);
  if (utcHour < 0) jd -= 1;
  if (utcHour >= 24) jd += 1;
  return jd;
}

function computeFull(inputs) {
  var parts = inputs.dateStr.split("-").map(Number);
  var tparts = inputs.timeStr.split(":").map(Number);
  var y = parts[0], mo = parts[1], d = parts[2];
  var jd = jdFromLocal(y, mo, d, tparts[0], tparts[1], inputs.utc);

  var chart = computeChart(jd, inputs.lat, inputs.lon);
  var ascRashi = rashiFor(chart.ascendantSidereal);
  var ascNak = nakshatraFor(chart.ascendantSidereal);
  var grahaOrder = ["sun","moon","mars","mercury","jupiter","venus","saturn","rahu","ketu"];
  var grahaInfo = {};
  grahaOrder.forEach(function(g){
    var lonG = chart.sidereal[g];
    var r = rashiFor(lonG), n = nakshatraFor(lonG);
    var house = houseNumber(r.index, ascRashi.index);
    grahaInfo[g] = {
      lon: lonG, rashi: r.name, nakshatra: n.name, pada: n.pada, house: house,
      dignity: dignityOf(g, r.name), owns: housesOwnedBy(g, ascRashi.index), aspects: aspectedHousesOf(g, house)
    };
  });
  var mahas = fullLifetimeMahadashas(jd, chart.sidereal.moon, 100);
  var yogis = fullLifetimeYoginis(jd, chart.sidereal.moon, 100);
  var tithi = computeTithi(chart.tropical.sun, chart.tropical.moon);
  var yoga = computeYoga(chart.tropical.sun, chart.tropical.moon);
  var karana = computeKarana(chart.tropical.sun, chart.tropical.moon);
  var vaar = computeVaar(y, mo, d);

  return {
    inputs: inputs, jd: jd, chart: chart, ascRashi: ascRashi, ascNak: ascNak,
    grahaOrder: grahaOrder, grahaInfo: grahaInfo, mahas: mahas, yogis: yogis,
    panchang: { tithi: tithi, yoga: yoga, karana: karana, vaar: vaar }
  };
}

function fmtDate(jd) { return jdToIsoDate(jd); }

function svgForResult(result) {
  var north = buildNorthIndianCells(result.ascRashi.index, result.grahaInfo, result.grahaOrder);
  var style = result.inputs.chartStyle;
  var opts = { size: 420, showHouseNumbers: result.inputs.showHouseNumbers };
  if (style === "south") {
    var bySign = buildSouthIndianOccupants(result.grahaInfo, result.grahaOrder);
    return renderSouthIndianSVG(bySign, result.ascRashi.index, opts);
  }
  if (style === "sudarshan") {
    var moonRashi = rashiFor(result.chart.sidereal.moon);
    var sunRashi = rashiFor(result.chart.sidereal.sun);
    var chandraCells = buildNorthIndianCells(moonRashi.index, result.grahaInfo, result.grahaOrder);
    var suryaCells = buildNorthIndianCells(sunRashi.index, result.grahaInfo, result.grahaOrder);
    return renderSudarshanSVG(north, chandraCells, suryaCells, { size: 220 });
  }
  return renderNorthIndianSVG(north, opts);
}

function svgToPngDownload(svgString, filename) {
  var svgBlob = new Blob([svgString], { type: "image/svg+xml;charset=utf-8" });
  var url = URL.createObjectURL(svgBlob);
  var img = new Image();
  img.onload = function(){
    var m = svgString.match(/width="(\d+(\.\d+)?)"/);
    var w = m ? parseFloat(m[1]) : img.width || 440;
    var m2 = svgString.match(/height="(\d+(\.\d+)?)"/);
    var h = m2 ? parseFloat(m2[1]) : img.height || 440;
    var scale = 2; // export at 2x for print-quality
    var canvas = document.createElement("canvas");
    canvas.width = w * scale; canvas.height = h * scale;
    var ctx = canvas.getContext("2d");
    ctx.fillStyle = "#ffffff"; ctx.fillRect(0,0,canvas.width,canvas.height);
    ctx.scale(scale, scale);
    ctx.drawImage(img, 0, 0, w, h);
    URL.revokeObjectURL(url);
    canvas.toBlob(function(blob){
      var a = document.createElement("a");
      var pngUrl = URL.createObjectURL(blob);
      a.href = pngUrl; a.download = filename;
      document.body.appendChild(a); a.click(); document.body.removeChild(a);
      URL.revokeObjectURL(pngUrl);
    }, "image/png");
  };
  img.src = url;
}

function renderReport(result) {
  LAST_RESULT = result;
  document.getElementById("btn-save").disabled = false;
  document.getElementById("btn-print").disabled = false;
  var r = result;
  var todayJd = julianDay(new Date().getFullYear(), new Date().getMonth()+1, new Date().getDate(), 12);
  var currentMaha = null;
  r.mahas.forEach(function(m){ if (m.startJd <= todayJd && todayJd < m.endJd) currentMaha = m; });
  var currentYogi = null;
  r.yogis.forEach(function(m){ if (m.startJd <= todayJd && todayJd < m.endJd) currentYogi = m; });

  var lh = r.inputs.letterhead || {};
  var printHeaderHtml = "";
  if (lh.name || lh.addr || lh.phone) {
    printHeaderHtml = "<strong>" + (lh.name||"") + "</strong>" + (lh.addr?" &middot; "+lh.addr:"") + (lh.phone?" &middot; "+lh.phone:"");
  }
  document.getElementById("print-header").innerHTML = printHeaderHtml;

  var html = "";

  html += "<section class='card'><h2>Chart Summary</h2>";
  html += "<div class='kv'>";
  html += "<div class='item'><div class='k'>Name</div><div class='v'>" + (r.inputs.name || "—") + "</div></div>";
  html += "<div class='item'><div class='k'>Birth</div><div class='v'>" + r.inputs.dateStr + " " + r.inputs.timeStr + "</div></div>";
  html += "<div class='item'><div class='k'>Place</div><div class='v'>" + r.inputs.placeLabel + "</div></div>";
  html += "<div class='item'><div class='k'>Ascendant</div><div class='v'>" + r.ascRashi.name + "</div></div>";
  html += "<div class='item'><div class='k'>Moon Nakshatra</div><div class='v'>" + r.grahaInfo.moon.nakshatra + " · pada " + r.grahaInfo.moon.pada + "</div></div>";
  html += "<div class='item'><div class='k'>Ayanamsha</div><div class='v'>" + r.chart.ayanamsha.toFixed(4) + "°</div></div>";
  html += "</div>";
  html += "<div class='chip-row'>";
  html += "<span class='pill'>" + r.panchang.vaar.name + "</span>";
  html += "<span class='pill'>" + r.panchang.tithi.paksha + " · " + r.panchang.tithi.name + "</span>";
  html += "<span class='pill'>Yoga: " + r.panchang.yoga.name + "</span>";
  html += "<span class='pill'>Karana: " + r.panchang.karana.name + "</span>";
  html += "</div></section>";

  html += "<section class='card'><h2>Kundli Chart</h2>";
  html += "<div class='chart-block'>";
  html += "<div class='chart-picture' id='chart-picture'>" + svgForResult(r) + "</div>";
  html += "<div class='chart-controls'><button type='button' id='btn-png'>Download chart (PNG)</button>";
  html += "<div class='note'>Style: " + (r.inputs.chartStyle==='south'?'South Indian (fixed sign grid)':r.inputs.chartStyle==='sudarshan'?'Sudarshan Chakra (Lagna / Chandra / Surya)':'North Indian (fixed house diamond)') + ". Change style above and regenerate to switch.</div></div>";
  html += "</div></section>";

  html += "<section class='card'><h2>Graha Positions</h2>";
  html += "<table><tr><th>Graha</th><th>Sign</th><th>Nakshatra</th><th>Pada</th><th>House</th><th>Dignity</th><th>Rules</th><th>Aspects</th></tr>";
  r.grahaOrder.forEach(function(g){
    var v = r.grahaInfo[g];
    html += "<tr><td style='text-transform:capitalize'>" + g + "</td><td>" + v.rashi + "</td><td>" + v.nakshatra + "</td><td>" + v.pada + "</td><td>" + v.house + "</td><td>" + (v.dignity || "—") + "</td><td>" + (v.owns.join(", ") || "—") + "</td><td>" + v.aspects.join(", ") + "</td></tr>";
  });
  html += "</table></section>";

  html += "<section class='card'><h2>Vimshottari Mahadasha &amp; Antardasha (birth to age ~100)</h2>";
  html += "<div class='note'>Click a period to expand its nine Antardashas; click an Antardasha to compute its nine Pratyantardashas on demand.</div>";
  r.mahas.forEach(function(m, mi){
    var v = r.grahaInfo[m.lord];
    var isCurrent = (m === currentMaha);
    html += "<details" + (isCurrent ? " open" : "") + " data-mi='" + mi + "'>";
    html += "<summary><span style='text-transform:capitalize'>" + m.lord + (isCurrent ? " — current" : "") + "</span><span>" + fmtDate(m.startJd) + " → " + fmtDate(m.endJd) + "</span><span class='marker'>+</span></summary>";
    html += "<div class='body'>";
    html += "<div class='note'>Natal " + m.lord + ": house " + v.house + " (" + HOUSE_SIG[v.house] + ") in " + v.rashi + (v.dignity ? ", " + v.dignity : "") + ". Classical theme: " + GRAHA_THEME[m.lord] + ".</div>";
    html += "<table class='antar-table'><tr><th>Antardasha</th><th>From</th><th>To</th></tr>";
    var subs = antardashasFor(m.lord, m.startJd);
    subs.forEach(function(s, si){
      var isCurAntar = isCurrent && s.startJd <= todayJd && todayJd < s.endJd;
      html += "<tr class='antar-row" + (isCurAntar?" cur":"") + "' data-lord='" + s.lord + "' data-start='" + s.startJd + "' data-maha='" + m.lord + "' style='cursor:pointer'><td style='text-transform:capitalize'>" + s.lord + (isCurAntar?" (current)":"") + "</td><td>" + fmtDate(s.startJd) + "</td><td>" + fmtDate(s.endJd) + "</td></tr>";
      html += "<tr class='pratyantar-slot' style='display:none'><td colspan='3'></td></tr>";
    });
    html += "</table></div></details>";
  });
  html += "</section>";

  html += "<section class='card'><h2>Yogini Dasha (birth to age ~100)</h2>";
  html += "<div class='note'>36-year, 8-Yogini system (Mangala&rarr;Pingala&rarr;Dhanya&rarr;Bhramari&rarr;Bhadrika&rarr;Ulka&rarr;Siddha&rarr;Sankata). Click a period to expand its nine Pratyantar sub-periods.</div>";
  r.yogis.forEach(function(m, mi){
    var isCurrent = (m === currentYogi);
    html += "<details" + (isCurrent ? " open" : "") + ">";
    html += "<summary><span>" + m.lord + (isCurrent ? " — current" : "") + "</span><span>" + fmtDate(m.startJd) + " → " + fmtDate(m.endJd) + "</span><span class='marker'>+</span></summary>";
    html += "<div class='body'><table class='yogini-antar-table'><tr><th>Pratyantar</th><th>From</th><th>To</th></tr>";
    var subs = yoginiPratyantarsFor(m.lord, m.startJd);
    subs.forEach(function(s){
      var isCur = isCurrent && s.startJd <= todayJd && todayJd < s.endJd;
      html += "<tr" + (isCur?" class='cur'":"") + "><td>" + s.lord + (isCur?" (current)":"") + "</td><td>" + fmtDate(s.startJd) + "</td><td>" + fmtDate(s.endJd) + "</td></tr>";
    });
    html += "</table></div></details>";
  });
  html += "</section>";

  html += "<section class='card'><h2>Varshaphal (Annual Chart)</h2>";
  html += "<div class='note'>Computes the exact moment the tropical Sun returns to its natal longitude for a chosen age, and the Muntha (natal Ascendant advanced by that many signs). Uses the birth place's coordinates by default. Does not compute the classical Varsheshwar (year-lord) -- see the note at the bottom of the page.</div>";
  html += "<div class='subrow'><div class='field'><label>Age turning</label><input type='number' id='varsha-age' min='0' max='120' value='25' style='width:100px'></div><button type='button' id='btn-varsha' class='small'>Generate annual chart</button></div>";
  html += "<div id='varsha-out'></div>";
  html += "</section>";

  var el = document.getElementById("report");
  el.innerHTML = html;
  el.style.display = "block";

  el.querySelectorAll(".antar-row").forEach(function(row){
    row.addEventListener("click", function(){
      var mahaLord = row.getAttribute("data-maha");
      var antarLord = row.getAttribute("data-lord");
      var antarStart = parseFloat(row.getAttribute("data-start"));
      var slot = row.nextElementSibling;
      if (slot.style.display === "table-row") { slot.style.display = "none"; return; }
      if (!slot.dataset.filled) {
        var pratyas = pratyantardashasFor(antarLord, antarStart, mahaLord);
        var inner = "<div class='note' style='margin:8px 0 4px'>Pratyantardasha within " + mahaLord + " / " + antarLord + ":</div><table><tr><th>Pratyantardasha</th><th>From</th><th>To</th></tr>";
        pratyas.forEach(function(p){
          inner += "<tr><td style='text-transform:capitalize'>" + p.lord + "</td><td>" + fmtDate(p.startJd) + "</td><td>" + fmtDate(p.endJd) + "</td></tr>";
        });
        inner += "</table>";
        slot.querySelector("td").innerHTML = inner;
        slot.dataset.filled = "1";
      }
      slot.style.display = "table-row";
    });
  });

  document.getElementById("btn-png").addEventListener("click", function(){
    var svg = document.getElementById("chart-picture").innerHTML;
    var safeName = (r.inputs.name || "chart").replace(/[^a-z0-9\-_]+/gi, "_");
    svgToPngDownload(svg, safeName + "_kundli.png");
  });

  document.getElementById("btn-varsha").addEventListener("click", function(){
    var age = parseInt(document.getElementById("varsha-age").value, 10);
    if (isNaN(age) || age < 0) return;
    var natalSunTropical = r.chart.tropical.sun;
    var srJd = solarReturnJd(r.jd, natalSunTropical, age);
    var srChart = computeChart(srJd, r.inputs.lat, r.inputs.lon);
    var srAscRashi = rashiFor(srChart.ascendantSidereal);
    var srGrahaInfo = {};
    r.grahaOrder.forEach(function(g){
      var lonG = srChart.sidereal[g];
      var rr = rashiFor(lonG), nn = nakshatraFor(lonG);
      var house = houseNumber(rr.index, srAscRashi.index);
      srGrahaInfo[g] = { rashi: rr.name, nakshatra: nn.name, pada: nn.pada, house: house };
    });
    var muntha = munthaRashi(r.ascRashi.index, age);
    var cells = buildNorthIndianCells(srAscRashi.index, srGrahaInfo, r.grahaOrder);
    var svg = renderNorthIndianSVG(cells, { size: 320, showHouseNumbers: true });
    var out = "<div class='chart-block'>";
    out += "<div class='chart-picture'>" + svg + "</div>";
    out += "<div class='chart-controls'>";
    out += "<div class='kv'><div class='item'><div class='k'>Solar return</div><div class='v'>" + fmtDate(srJd) + "</div></div>";
    out += "<div class='item'><div class='k'>Annual Ascendant</div><div class='v'>" + srAscRashi.name + "</div></div>";
    out += "<div class='item'><div class='k'>Muntha</div><div class='v'>" + muntha.name + "</div></div></div>";
    out += "</div></div>";
    document.getElementById("varsha-out").innerHTML = out;
  });

  var reportEl = document.getElementById("report");
  if (reportEl.scrollIntoView) reportEl.scrollIntoView({behavior:"smooth"});
}

document.getElementById("btn-generate").addEventListener("click", function(){
  var inputs = gatherBirthInputs();
  if (!inputs) return;
  var result = computeFull(inputs);
  renderReport(result);
  if (typeof updateEngineBadge === "function") updateEngineBadge(result.chart);
});

document.getElementById("btn-reset").addEventListener("click", function(){
  ["in-name","in-date","in-time","in-place","in-lat","in-lon","in-utc","lh-name","lh-addr","lh-phone"].forEach(function(id){
    document.getElementById(id).value = "";
  });
  selectedPlaceHandle.set(null);
  LAST_RESULT = null;
  manualFields.classList.remove("show");
  letterheadFields.classList.remove("show");
  document.getElementById("report").style.display = "none";
  document.getElementById("btn-save").disabled = true;
  document.getElementById("btn-print").disabled = true;
  showErr("form-err", null);
});

document.getElementById("btn-print").addEventListener("click", function(){
  window.print();
});

/* ================= .kun FILE FORMAT ================= */
var KUN_FORMAT = "ASTROWATCH_KUN_V2";

document.getElementById("btn-save").addEventListener("click", function(){
  if (!LAST_RESULT) return;
  var r = LAST_RESULT;
  var payload = {
    format: KUN_FORMAT,
    generatedAt: new Date().toISOString(),
    inputs: r.inputs,
    julianDayUT: r.jd,
    ayanamshaDeg: r.chart.ayanamsha,
    ascendant: { rashi: r.ascRashi.name, nakshatra: r.ascNak.name, pada: r.ascNak.pada, siderealLon: r.chart.ascendantSidereal },
    grahas: r.grahaInfo,
    mahadashas: r.mahas.map(function(m){ return { lord: m.lord, startJd: m.startJd, endJd: m.endJd, startDate: fmtDate(m.startJd), endDate: fmtDate(m.endJd) }; }),
    yoginiDashas: r.yogis.map(function(m){ return { lord: m.lord, startJd: m.startJd, endJd: m.endJd, startDate: fmtDate(m.startJd), endDate: fmtDate(m.endJd) }; }),
    panchang: {
      tithi: r.panchang.tithi.name, paksha: r.panchang.tithi.paksha,
      yoga: r.panchang.yoga.name, karana: r.panchang.karana.name, vaar: r.panchang.vaar.name
    },
    disclaimer: "Astrological calculation only, computed client-side by Astrowatch Kundli Studio. Not a forecast; Astrowatch's own blind backtest found no statistically significant predictive edge for this style of astrology."
  };
  var blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
  var url = URL.createObjectURL(blob);
  var a = document.createElement("a");
  var safeName = (r.inputs.name || "chart").replace(/[^a-z0-9\-_]+/gi, "_");
  a.href = url;
  a.download = safeName + "_" + r.inputs.dateStr + ".kun";
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
});

document.getElementById("btn-load").addEventListener("click", function(){
  document.getElementById("file-load").click();
});
document.getElementById("file-load").addEventListener("change", function(ev){
  var file = ev.target.files[0];
  if (!file) return;
  var reader = new FileReader();
  reader.onload = function(e){
    var data;
    try { data = JSON.parse(e.target.result); }
    catch (err) { showErr("form-err", "Could not read this .kun file -- not valid JSON."); return; }
    if (data.format !== KUN_FORMAT && data.format !== "ASTROWATCH_KUN_V1") { showErr("form-err", "This file was not recognised as an Astrowatch .kun chart file."); return; }
    document.getElementById("in-name").value = data.inputs.name || "";
    document.getElementById("in-date").value = data.inputs.dateStr;
    document.getElementById("in-time").value = data.inputs.timeStr;
    document.getElementById("in-place").value = data.inputs.placeLabel;
    selectedPlaceHandle.set({ label: data.inputs.placeLabel, lat: data.inputs.lat, lon: data.inputs.lon, utc: data.inputs.utc });
    if (data.inputs.chartStyle) document.getElementById("in-chart-style").value = data.inputs.chartStyle;
    if (data.inputs.showHouseNumbers != null) document.getElementById("in-house-numbers").checked = data.inputs.showHouseNumbers;
    if (data.inputs.letterhead) {
      document.getElementById("lh-name").value = data.inputs.letterhead.name || "";
      document.getElementById("lh-addr").value = data.inputs.letterhead.addr || "";
      document.getElementById("lh-phone").value = data.inputs.letterhead.phone || "";
    }
    var inputsForCompute = data.inputs;
    if (!inputsForCompute.chartStyle) inputsForCompute.chartStyle = "north";
    if (inputsForCompute.showHouseNumbers == null) inputsForCompute.showHouseNumbers = true;
    var result = computeFull(inputsForCompute);
    renderReport(result);
    if (typeof updateEngineBadge === "function") updateEngineBadge(result.chart);
    showErr("form-err", null);
  };
  reader.readAsText(file);
  ev.target.value = "";
});

/* ================= MODE TABS ================= */
document.getElementById("tab-horoscope").addEventListener("click", function(){
  document.getElementById("tab-horoscope").classList.add("active");
  document.getElementById("tab-match").classList.remove("active");
  document.getElementById("panel-horoscope").classList.add("active");
  document.getElementById("panel-match").classList.remove("active");
});
document.getElementById("tab-match").addEventListener("click", function(){
  document.getElementById("tab-match").classList.add("active");
  document.getElementById("tab-horoscope").classList.remove("active");
  document.getElementById("panel-match").classList.add("active");
  document.getElementById("panel-horoscope").classList.remove("active");
});

/* ================= MATCH-MAKING MODE ================= */
var boyPlaceHandle = attachPlaceAutocomplete(document.getElementById("m-boy-place"), document.getElementById("m-boy-list"), function(){}, function(){});
var girlPlaceHandle = attachPlaceAutocomplete(document.getElementById("m-girl-place"), document.getElementById("m-girl-list"), function(){}, function(){});

function personChartData(prefix, handle) {
  var dateStr = document.getElementById(prefix+"-date").value;
  var timeStr = document.getElementById(prefix+"-time").value || "12:00";
  var place = handle.get();
  if (!dateStr || !place) return null;
  var parts = dateStr.split("-").map(Number);
  var tparts = timeStr.split(":").map(Number);
  var jd = jdFromLocal(parts[0], parts[1], parts[2], tparts[0], tparts[1], place.utc);
  var chart = computeChart(jd, place.lat, place.lon);
  var moonLon = chart.sidereal.moon;
  var r = rashiFor(moonLon), n = nakshatraFor(moonLon);
  var w = 360/27;
  var nakNum = Math.floor(moonLon / w) + 1;
  return {
    name: document.getElementById(prefix+"-name").value || "—",
    moonSiderealLon: moonLon, rashiIdx: r.index, nakshatraNum: nakNum, nakshatraName: n.name,
    degInSign: moonLon % 30
  };
}

document.getElementById("btn-match").addEventListener("click", function(){
  var boy = personChartData("m-boy", boyPlaceHandle);
  var girl = personChartData("m-girl", girlPlaceHandle);
  if (!boy || !girl) { showErr("match-err", "Enter date of birth and a selected place for both partners."); return; }
  showErr("match-err", null);
  var result = computeAshtakoot(boy, girl);
  var html = "";
  html += "<div class='score-banner'><div class='big'>" + result.total + " / " + result.maxTotal + "</div><div class='lbl'>Ashtakoot Guna Milan Score</div>";
  html += "<div class='dosha-flags'>";
  if (result.doshas.length) {
    result.doshas.forEach(function(d){ html += "<span class='dosha-pill'>" + d + "</span>"; });
  } else {
    html += "<span class='no-dosha'>No Nadi / Bhakoot / Gana Dosha flagged</span>";
  }
  html += "</div></div>";
  html += "<section class='card'><h2>" + boy.name + " &amp; " + girl.name + " — 8 Koota Breakdown</h2>";
  html += "<table class='koota-table'><tr><th>Koota</th><th>Score</th><th>Max</th><th>Detail</th></tr>";
  result.items.forEach(function(i){
    var cls = i.score === 0 ? "score-0" : (i.score === i.max ? "score-full" : "");
    html += "<tr><td>" + i.name + "</td><td class='"+cls+"'>" + i.score + "</td><td>" + i.max + "</td><td>" + i.detail + "</td></tr>";
  });
  html += "</table>";
  html += "<div class='note'>Score guide (traditional, not applied automatically): 18+ generally considered the minimum acceptable threshold, 24+ good, 32+ excellent. Nadi and Bhakoot doshas are traditionally weighed more heavily than the numeric total regardless of score, and experienced astrologers apply case-by-case exceptions that this calculator does not auto-apply -- see the methodology note in the footer.</div>";
  html += "</section>";
  var el = document.getElementById("match-report");
  el.innerHTML = html;
  if (el.scrollIntoView) el.scrollIntoView({behavior:"smooth"});
});
