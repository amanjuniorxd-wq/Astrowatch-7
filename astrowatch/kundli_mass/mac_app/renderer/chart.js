/* ===== Kundli chart drawing (SVG) =====
   North Indian style: fixed diamond layout, house 1 always the top kite,
   houses numbered clockwise 1..12; each cell displays the RASHI number
   occupying that house and the grahas placed there.
   South Indian style: fixed 4x4 grid where each cell is a FIXED sign
   (Pisces top-left, going clockwise in zodiacal order); the Ascendant
   marker and each graha are placed in the cell matching their own sign.
   Geometry derived from first principles (kendra houses 1/4/7/10 = the
   four kite shapes touching the middle of each edge of the outer square;
   corner regions split by the square's corner-to-corner diagonals). */

var GRAHA_ABBR = { sun:"Su", moon:"Mo", mars:"Ma", mercury:"Me", jupiter:"Ju", venus:"Ve", saturn:"Sa", rahu:"Ra", ketu:"Ke" };

function northIndianHouseCells(S) {
  var h = S/2, q = S/4, t = 3*S/4;
  return {
    1:  [[h,0],[t,q],[h,h],[q,q]],
    2:  [[h,0],[S,0],[t,q]],
    3:  [[S,0],[S,h],[t,q]],
    4:  [[S,h],[t,t],[h,h],[t,q]],
    5:  [[S,h],[S,S],[t,t]],
    6:  [[S,S],[h,S],[t,t]],
    7:  [[h,S],[q,t],[h,h],[t,t]],
    8:  [[h,S],[0,S],[q,t]],
    9:  [[0,S],[0,h],[q,t]],
    10: [[0,h],[q,q],[h,h],[q,t]],
    11: [[0,h],[0,0],[q,q]],
    12: [[0,0],[h,0],[q,q]]
  };
}
function polyCentroid(pts) {
  var x=0,y=0; pts.forEach(function(p){x+=p[0];y+=p[1];});
  return [x/pts.length, y/pts.length];
}
function polyToPoints(pts) { return pts.map(function(p){return p[0]+","+p[1];}).join(" "); }

/* cellsData: array indexed by house-position 1..12 (North) with
   {signNum, occupants:[graha keys...], ascHere:bool} */
function renderNorthIndianSVG(cellsData, opts) {
  opts = opts || {};
  var S = opts.size || 440;
  var showHouseNo = opts.showHouseNumbers !== false;
  var cells = northIndianHouseCells(S);
  var svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 '+S+' '+S+'" width="'+S+'" height="'+S+'" class="kundli-svg">';
  svg += '<rect x="0" y="0" width="'+S+'" height="'+S+'" fill="#ffffff" stroke="#0a0a0a" stroke-width="2"/>';
  // outer diamond + diagonals
  var h=S/2;
  svg += '<polygon points="'+h+',0 '+S+','+h+' '+h+','+S+' 0,'+h+'" fill="none" stroke="#0a0a0a" stroke-width="1.5"/>';
  svg += '<line x1="0" y1="0" x2="'+S+'" y2="'+S+'" stroke="#0a0a0a" stroke-width="1.5"/>';
  svg += '<line x1="'+S+'" y1="0" x2="0" y2="'+S+'" stroke="#0a0a0a" stroke-width="1.5"/>';
  for (var hn = 1; hn <= 12; hn++) {
    var pts = cells[hn];
    var c = cellsData[hn] || {};
    var centroid = polyCentroid(pts);
    var cx = centroid[0], cy = centroid[1];
    // pull sign-number label toward the outer edge of the cell (away from center) for legibility
    var S_half = S/2;
    var dx = cx - S_half, dy = cy - S_half;
    var norm = Math.sqrt(dx*dx+dy*dy) || 1;
    var pull = (hn % 3 === 1) ? 0.62 : 0.42; // kites vs corner triangles pull differently
    var numX = cx + (dx/norm) * (S*0.14) * pull * 2;
    var numY = cy + (dy/norm) * (S*0.14) * pull * 2;
    if (showHouseNo) {
      svg += '<text x="'+numX.toFixed(1)+'" y="'+numY.toFixed(1)+'" font-size="'+(S*0.032).toFixed(1)+'" fill="#999999" text-anchor="middle" font-family="Helvetica,Arial,sans-serif">'+ (c.signNum!=null? c.signNum : "") +'</text>';
    }
    var occ = (c.occupants || []).slice();
    var label = occ.map(function(k){ return (k==="asc") ? "As" : GRAHA_ABBR[k]; }).join(" ");
    if (label) {
      svg += '<text x="'+cx.toFixed(1)+'" y="'+(cy+ (S*0.012)).toFixed(1)+'" font-size="'+(S*0.042).toFixed(1)+'" fill="#0a0a0a" text-anchor="middle" font-family="Helvetica,Arial,sans-serif" font-weight="600">'+label+'</text>';
    }
  }
  svg += '</svg>';
  return svg;
}

var SOUTH_GRID = [
  // [row, col, signIdx(0=Mesha..11=Meena)]
  [0,0,11],[0,1,0],[0,2,1],[0,3,2],
  [1,3,3],[2,3,4],
  [3,3,5],[3,2,6],[3,1,7],[3,0,8],
  [2,0,9],[1,0,10]
];
function renderSouthIndianSVG(signOccupants, ascSignIdx, opts) {
  opts = opts || {};
  var S = opts.size || 440;
  var cell = S/4;
  var svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 '+S+' '+S+'" width="'+S+'" height="'+S+'" class="kundli-svg">';
  svg += '<rect x="0" y="0" width="'+S+'" height="'+S+'" fill="#ffffff" stroke="#0a0a0a" stroke-width="2"/>';
  for (var r=0;r<4;r++) for (var c=0;c<4;c++) {
    svg += '<rect x="'+(c*cell)+'" y="'+(r*cell)+'" width="'+cell+'" height="'+cell+'" fill="none" stroke="#0a0a0a" stroke-width="1"/>';
  }
  svg += '<line x1="'+cell+'" y1="'+cell+'" x2="'+(3*cell)+'" y2="'+cell+'" stroke="#cccccc" stroke-width="0.5"/>';
  SOUTH_GRID.forEach(function(cellDef){
    var r = cellDef[0], c = cellDef[1], signIdx = cellDef[2];
    var cx = c*cell + cell/2, cy = r*cell + cell/2;
    var signName = RASHI_NAMES[signIdx];
    svg += '<text x="'+(c*cell+6)+'" y="'+(r*cell+14)+'" font-size="'+(S*0.024).toFixed(1)+'" fill="#999999" font-family="Helvetica,Arial,sans-serif">'+signName.slice(0,3)+'</text>';
    var occ = (signOccupants[signIdx] || []).slice();
    if (signIdx === ascSignIdx) occ = ["asc"].concat(occ);
    var label = occ.map(function(k){ return (k==="asc") ? "As" : GRAHA_ABBR[k]; }).join(" ");
    if (label) {
      svg += '<text x="'+cx.toFixed(1)+'" y="'+(cy+6).toFixed(1)+'" font-size="'+(S*0.038).toFixed(1)+'" fill="#0a0a0a" text-anchor="middle" font-family="Helvetica,Arial,sans-serif" font-weight="600">'+label+'</text>';
    }
  });
  svg += '<text x="'+(S/2)+'" y="'+(S/2-6)+'" font-size="'+(S*0.03).toFixed(1)+'" fill="#0a0a0a" text-anchor="middle" font-family="Helvetica,Arial,sans-serif" font-weight="700">Rashi</text>';
  svg += '<text x="'+(S/2)+'" y="'+(S/2+16)+'" font-size="'+(S*0.022).toFixed(1)+'" fill="#999999" text-anchor="middle" font-family="Helvetica,Arial,sans-serif">South Indian</text>';
  svg += '</svg>';
  return svg;
}

/* Builds the cellsData input for renderNorthIndianSVG from a computed chart:
   ascRashiIdx (0..11) and grahaInfo {key: {rashi:name,...}} */
function buildNorthIndianCells(ascRashiIdx, grahaInfo, grahaOrder) {
  var cellsData = {};
  for (var hn = 1; hn <= 12; hn++) {
    var signIdx = (ascRashiIdx + hn - 1) % 12;
    cellsData[hn] = { signNum: signIdx + 1, occupants: (hn === 1) ? ["asc"] : [] };
  }
  grahaOrder.forEach(function(g){
    var house = grahaInfo[g].house;
    cellsData[house].occupants.push(g);
  });
  return cellsData;
}
function buildSouthIndianOccupants(grahaInfo, grahaOrder) {
  var bySign = {};
  grahaOrder.forEach(function(g){
    var idx = RASHI_NAMES.indexOf(grahaInfo[g].rashi);
    if (!bySign[idx]) bySign[idx] = [];
    bySign[idx].push(g);
  });
  return bySign;
}

/* Sudarshan Chakra: presented as three side-by-side North Indian diamonds
   (Lagna / Chandra / Surya kundli), a common simplified rendering of the
   classical "three kundli" Sudarshan concept -- not attempted as a single
   concentric-ring diagram, which would need geometry this project has not
   independently verified. */
function renderSudarshanSVG(lagnaCells, chandraCells, suryaCells, opts) {
  opts = opts || {};
  var S = opts.size || 260;
  var gap = 24;
  var totalW = S*3 + gap*2;
  var svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 '+totalW+' '+(S+30)+'" width="'+totalW+'" height="'+(S+30)+'" class="kundli-svg kundli-svg-triple">';
  var labels = ["Lagna Kundli", "Chandra Kundli", "Surya Kundli"];
  [lagnaCells, chandraCells, suryaCells].forEach(function(cd, i){
    var x = i*(S+gap);
    var inner = renderNorthIndianSVG(cd, {size:S}).replace('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 '+S+' '+S+'" width="'+S+'" height="'+S+'" class="kundli-svg">','').replace('</svg>','');
    svg += '<g transform="translate('+x+',0)">' + inner + '</g>';
    svg += '<text x="'+(x+S/2)+'" y="'+(S+20)+'" font-size="13" fill="#0a0a0a" text-anchor="middle" font-family="Helvetica,Arial,sans-serif" font-weight="700">'+labels[i]+'</text>';
  });
  svg += '</svg>';
  return svg;
}
