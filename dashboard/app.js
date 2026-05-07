/* ============================================================
   HDBSCAN Attraction Weight Dashboard — App Logic
   Only HDBSCAN | Color by Category | Size by Attraction Weight
   Master's Thesis: Atefeh Zaeemi, BHT Berlin, 2026
   ============================================================ */

// ── CATEGORY COLOURS ─────────────────────────────────────────────────────────
const CAT_COL = {
  Tourism:    '#4da6e8',
  Catering:   '#f0813a',
  Health:     '#e05566',
  Services:   '#a87fd4',
  Shops:      '#e8a83a',
  School:     '#4a9ecf',
  Education:  '#4a9ecf',
  Leisure:    '#52c27a',
  Industry:   '#8a95a8',
  Retail:     '#c47a4a',
  Gastronomy: '#d4b23a',
  Others:     '#888fa8',
  Other:      '#888fa8',
};

// ── WEIGHT → RADIUS ──────────────────────────────────────────────────────────
// Maps attraction_weight to circle radius (px)
function wRadius(w) {
  if (!w || w <= 0)   return 3;
  if (w < 100)        return 4;
  if (w < 300)        return 6;
  if (w < 600)        return 8;
  if (w < 1200)       return 11;
  if (w < 2400)       return 14;
  return 18;
}

// ── WEIGHT → OPACITY ─────────────────────────────────────────────────────────
function wOpacity(w) {
  if (!w || w <= 0) return 0.35;
  if (w < 100)      return 0.50;
  if (w < 400)      return 0.65;
  if (w < 1000)     return 0.80;
  return 0.92;
}

// ── GLOBALS ──────────────────────────────────────────────────────────────────
let map, renderer, poiLayer;
let activeCats = new Set(); // empty = all shown

// ── INIT ─────────────────────────────────────────────────────────────────────
window.onload = () => {
  map = L.map('map', { center: [50.095, 12.055], zoom: 12, preferCanvas: true });
  renderer = L.canvas({ padding: 0.5 });

  L.tileLayer(
    'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
    {
      attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors © <a href="https://carto.com">CARTO</a>',
      subdomains: 'abcd', maxZoom: 19, opacity: 0.85,
    }
  ).addTo(map);

  poiLayer = L.layerGroup().addTo(map);

  buildFclassDropdown();
  buildCategoryButtons();
  buildCategoryLegend();
  draw();
  setTimeout(() => fitDistrict(), 300);
};

// ── BUILD FCLASS DROPDOWN ─────────────────────────────────────────────────────
function buildFclassDropdown() {
  const fclasses = [...new Set(POI_DATA.map(p => p.fclass))].sort();
  const el = document.getElementById('sf');
  fclasses.forEach(f => {
    const n = POI_DATA.filter(p => p.fclass === f).length;
    el.innerHTML += `<option value="${f}">${f} (${n})</option>`;
  });
}

// ── CATEGORY TOGGLE BUTTONS ───────────────────────────────────────────────────
function buildCategoryButtons() {
  const cats = [...new Set(POI_DATA.map(p => p.category))].filter(Boolean).sort();
  const el   = document.getElementById('cat-btns');
  cats.forEach(cat => {
    const col = CAT_COL[cat] || '#888';
    const btn = document.createElement('button');
    btn.className = 'catbtn';
    btn.textContent = cat;
    btn.dataset.cat = cat;
    btn.style.setProperty('--ccat', col);
    btn.onclick = () => toggleCat(cat);
    el.appendChild(btn);
  });
}

function toggleCat(cat) {
  if (activeCats.has(cat)) {
    activeCats.delete(cat);
  } else {
    activeCats.add(cat);
  }
  updateCatButtons();
  draw();
}

function updateCatButtons() {
  document.querySelectorAll('.catbtn').forEach(btn => {
    const cat = btn.dataset.cat;
    const col = CAT_COL[cat] || '#888';
    const isActive = activeCats.size === 0 || activeCats.has(cat);
    btn.classList.toggle('active', isActive);
    if (isActive) {
      btn.style.background = col + '33';
      btn.style.borderColor = col;
      btn.style.color = col;
    } else {
      btn.style.background = '';
      btn.style.borderColor = '';
      btn.style.color = '';
    }
  });
}

function resetCats() {
  activeCats.clear();
  updateCatButtons();
  draw();
}

// ── CATEGORY LEGEND ───────────────────────────────────────────────────────────
function buildCategoryLegend() {
  const cats = [...new Set(POI_DATA.map(p => p.category))].filter(Boolean).sort();
  const el   = document.getElementById('cleg');
  cats.forEach(c => {
    const n   = POI_DATA.filter(p => p.category === c).length;
    const col = CAT_COL[c] || '#888';
    el.innerHTML +=
      `<div class="li">
        <div class="ldot" style="background:${col}"></div>
        <span style="flex:1;color:#c0c8dc">${c}</span>
        <span class="ln">${n}</span>
      </div>`;
  });
}

// ── DRAW ──────────────────────────────────────────────────────────────────────
function draw() {
  poiLayer.clearLayers();

  const fc        = document.getElementById('sf').value;
  const showNoise = document.getElementById('cbn').checked;
  let   count     = 0;

  // Sort by weight ascending so heavier points render on top
  const sorted = [...POI_DATA].sort((a, b) => (a.attraction_weight || 0) - (b.attraction_weight || 0));

  sorted.forEach(p => {
    // Category filter
    if (activeCats.size > 0 && !activeCats.has(p.category)) return;
    // fclass filter
    if (fc && p.fclass !== fc) return;

    const cl = (p.cluster_hdb != null) ? p.cluster_hdb : -1;
    if (!showNoise && cl < 0) return;

    const w   = p.attraction_weight || 0;
    const col = cl < 0 ? null : (CAT_COL[p.category] || '#888');
    const r   = cl < 0 ? 3 : wRadius(w);
    const op  = cl < 0 ? 0.25 : wOpacity(w);

    const mk = L.circleMarker([p.lat, p.lon], {
      renderer,
      radius:      r,
      fillColor:   cl < 0 ? 'transparent' : col,
      color:       cl < 0 ? 'rgba(255,82,82,0.5)' : col,
      weight:      cl < 0 ? 1 : 0.8,
      fillOpacity: op,
      dashArray:   cl < 0 ? '2,2' : null,
    });

    const clLabel = cl < 0 ? '<span style="color:#ff5252">Noise (−1)</span>' : `Cluster <b>${cl}</b>`;
    mk.bindTooltip(
      `<b style="color:#eef">${p.name || '(unnamed)'}</b><br>` +
      `<span style="color:#8ab;font-size:10px">${p.fclass} · ${p.category || ''}</span><br>` +
      `W<sub>c</sub> = <b>${w > 0 ? w.toFixed(1) : '—'}</b> &nbsp;·&nbsp; ${clLabel}`,
      { sticky: true, offset: [8, 0], className: 'tt' }
    );
    mk.on('click', () => showInfo(p, cl, col));
    mk.addTo(poiLayer);
    count++;
  });

  document.getElementById('pcnt').textContent = count.toLocaleString() + ' POIs angezeigt';
  updateCatButtons();
}

// ── INFO PANEL ────────────────────────────────────────────────────────────────
function showInfo(p, cl, col) {
  const w     = p.attraction_weight != null ? p.attraction_weight.toFixed(2) : '—';
  const noise = cl < 0;
  const swatch = col ? `<span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:${col};margin-right:4px;vertical-align:middle"></span>` : '';
  document.getElementById('ibox').innerHTML =
    `<b style="color:#dce3f0">${p.name || '(unnamed)'}</b><br>` +
    `<span class="tag">${p.fclass}</span>` +
    `<span class="tag ${noise ? 'tnoise' : ''}">${noise ? 'Noise −1' : 'Cluster ' + cl}</span><br>` +
    `${swatch}<b style="color:${col || '#888'}">${p.category || '?'}</b><br>` +
    `<span style="color:#6b7591;font-size:10px">Attraction W<sub>c</sub>:</span> ` +
    `<b style="color:#dce3f0">${w}</b>`;
}

// ── FIT ───────────────────────────────────────────────────────────────────────
function fitDistrict() {
  map.fitBounds([[49.9774, 11.8456], [50.2217, 12.2523]], { padding: [30, 30] });
}
