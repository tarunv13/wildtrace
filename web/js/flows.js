// Flows: where wildlife is taken, where it passes through, and where it is seized.
// The reader builds the view (species, countries, evidence, colour, how many routes) and
// switches single routes on and off; the map, the route list and the story sentence follow.
// Data: CITES Trade Database shipments (web/data/flows.json), US LEMIS seizures (web/data/lemis.json),
// plus routes named in cases.
import { esc, fmt } from "./charts.js";
import { S, ccName, emit, spLabel } from "./store.js";
import * as icons from "./icons.js";

// Eight trade regions in a fixed order (validated categorical palette), Other in grey.
export const REGION_COLOR = { south_asia: "#2a78d6", southeast_asia: "#eb6834", east_asia: "#1baf7a", mena: "#eda100",
  africa: "#e87ba4", latin_america: "#008300", europe: "#4a3aa7", north_america: "#e34948", other: "#8a948f" };
export const ROLE = { supply: ["Source", "#218a5b", "taken from the wild here"], transit: ["Transit hub", "#2563eb", "re-exported on the way"],
  demand: ["Market", "#c27a06", "seized arriving here"] };
const SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"];
const GREY = "#8a948f";

export const regionOf = (cc) => S.data.countries[cc]?.region || "other";
export const regionName = (k) => S.data.regions?.regions?.[k] || k;
const name = (cc) => (cc === "XX" ? "Origin not recorded" : ccName(cc));
const has = (cc) => cc && S.data.countries[cc];

// ------------------------------------------------------------------ roles (all seized data)
let roleCache = null;
export function roles() {
  if (roleCache || !S.data.flows) return roleCache || {};
  const r = {};
  const add = (cc, k, n) => ((r[cc] ||= { supply: 0, transit: 0, demand: 0 })[k] += n);
  S.data.flows.seized.forEach(([, o, e, i, n]) => { if (o !== "XX") add(o, "supply", n); if (e !== o) add(e, "transit", n); add(i, "demand", n); });
  return (roleCache = r);
}
export const roleOf = (cc) => { const v = roles()[cc]; return v ? Object.keys(v).reduce((a, b) => (v[a] >= v[b] ? a : b)) : "supply"; };

// ------------------------------------------------------------------ routes from the reader's choices
function speciesColors() {
  const f = S.flow, map = {};
  const order = f.groups.size ? [...f.groups] : topGroups(7);
  order.forEach((g, i) => (map[g] = i < SERIES.length ? SERIES[i] : GREY));
  return map;
}
function topGroups(k) {
  const c = {};
  S.data.flows?.seized.forEach(([g, , , , n]) => (c[g] = (c[g] || 0) + n));
  return Object.entries(c).sort((a, b) => b[1] - a[1]).slice(0, k).map(([g]) => g);
}

// "Spread across markets": the busiest routes, but at most this many into any one country, so one
// country's reporting (the United States files seizures far more completely than most) cannot
// fill the whole list.
const PER_MARKET = 2;
function spread(list) {
  if (!S.flow.spread) return list;
  const per = {};
  return list.filter((r) => (per[r.b] = (per[r.b] || 0) + 1) <= PER_MARKET);
}

/** All routes the current choices allow, before the reader's on/off switches. */
export function routes() {
  const f = S.flow, d = S.data.flows, out = [];
  if (!d) return out;
  const okG = (g) => !f.groups.size || f.groups.has(g);
  const okEnds = (a, b) => (!f.noUS || (a !== "US" && b !== "US"))
    && (f.story !== "country" || !f.country || a === f.country || b === f.country)
    && (f.story === "country" || ((!f.from.size || f.from.has(a)) && (!f.to.size || f.to.has(b))));
  if (f.ev.seized) {
    const agg = {};
    d.seized.forEach(([g, o, , i, n]) => {
      if (o === "XX" || o === i || !okG(g) || !okEnds(o, i)) return;
      const r = (agg[`s|${o}|${i}`] ||= { key: `s|${o}|${i}`, k: "s", a: o, b: i, n: 0, gs: {} });
      r.n += n; r.gs[g] = (r.gs[g] || 0) + n;
    });
    out.push(...spread(Object.values(agg).filter((r) => has(r.a) && has(r.b)).sort((x, y) => y.n - x.n)).slice(0, f.top));
  }
  if (f.ev.lemis && S.data.lemis) {
    const agg = {};
    S.data.lemis.seized.forEach(([g, o, , i, n]) => {
      if (o === "XX" || o === i || !okG(g) || !okEnds(o, i)) return;
      const r = (agg[`l|${o}|${i}`] ||= { key: `l|${o}|${i}`, k: "l", a: o, b: i, n: 0, gs: {} });
      r.n += n; r.gs[g] = (r.gs[g] || 0) + n;
    });
    // Every LEMIS route ends in the US, so "spread across markets" would keep only two.
    out.push(...Object.values(agg).filter((r) => has(r.a) && has(r.b)).sort((x, y) => y.n - x.n).slice(0, f.top));
  }
  if (f.ev.declared) {
    const agg = {};
    Object.entries(d.declared).forEach(([g, rows]) => okG(g) && rows.forEach(([e, i, n]) => {
      if (!okEnds(e, i)) return;
      const r = (agg[`d|${e}|${i}`] ||= { key: `d|${e}|${i}`, k: "d", a: e, b: i, n: 0, gs: {} });
      r.n += n; r.gs[g] = (r.gs[g] || 0) + n;
    }));
    out.push(...spread(Object.values(agg).filter((r) => has(r.a) && has(r.b)).sort((x, y) => y.n - x.n)).slice(0, f.top));
  }
  if (f.ev.news) {
    const agg = {};
    S.data.cases.forEach((c) => {
      if (!c.route_coords?.[0] || !c.route_coords?.[1] || (f.groups.size && !c.species.some((s) => f.groups.has(s)))) return;
      const key = `n|${c.route.join(">")}`;
      const r = (agg[key] ||= { key, k: "n", la: c.route[0], lb: c.route[1], ac: c.route_coords[0], bc: c.route_coords[1], n: 0, gs: {} });
      r.n += 1; c.species.forEach((s) => (r.gs[s] = (r.gs[s] || 0) + 1));
    });
    out.push(...Object.values(agg));
  }
  return out;
}
const coords = (cc) => [S.data.countries[cc].lon, S.data.countries[cc].lat];
const label = (r) => (r.k === "n" ? `${r.la} → ${r.lb}` : `${name(r.a)} → ${name(r.b)}`);
const flagLabel = (r) => (r.k === "n" ? esc(label(r)) : `${icons.flag(r.a)}${esc(name(r.a))} <span class="muted">→</span> ${icons.flag(r.b)}${esc(name(r.b))}`);
const KIND = { s: "seized shipments (CITES)", l: "records seized at US ports (LEMIS)", d: "declared shipments (CITES, legal trade)", n: "case(s) naming this route" };

function ends(r, sc) {
  const by = S.flow.colorBy;
  if (by === "role") return [ROLE.supply[1], ROLE.demand[1]];
  if (by === "species") { const g = Object.entries(r.gs).sort((a, b) => b[1] - a[1])[0]?.[0]; const c = sc[g] || GREY; return [c, c]; }
  if (r.k === "n") return [ROLE.supply[1], ROLE.demand[1]];
  return [REGION_COLOR[regionOf(r.a)], REGION_COLOR[regionOf(r.b)]];
}
const hex = (h) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16));
const mix = (a, b, t) => { const x = hex(a), y = hex(b); return `#${x.map((v, i) => Math.round(v + (y[i] - v) * t).toString(16).padStart(2, "0")).join("")}`; };
// Flows are drawn on the flat map, so a route is a gentle curve in map space that stays on
// the map (a great circle from Asia to America would leave the top edge and wrap round).
const mercY = (lat) => (Math.log(Math.tan(Math.PI / 4 + (Math.max(-85, Math.min(85, lat)) * Math.PI) / 360)) * 180) / Math.PI;
const unY = (y) => (Math.atan(Math.exp((y * Math.PI) / 180)) * 360) / Math.PI - 90;
function curve([lo1, la1], [lo2, la2], n = 40) {
  const y1 = mercY(la1), y2 = mercY(la2), dx = lo2 - lo1, dy = y2 - y1, d = Math.hypot(dx, dy) || 1;
  let cx = (lo1 + lo2) / 2 - (dy / d) * 0.22 * d, cy = (y1 + y2) / 2 + (dx / d) * 0.22 * d;
  if (cy < (y1 + y2) / 2) { cx = (lo1 + lo2) / 2 + (dy / d) * 0.22 * d; cy = (y1 + y2) / 2 - (dx / d) * 0.22 * d; } // bow north
  const out = [];
  for (let i = 0; i <= n; i++) {
    const t = i / n, u = 1 - t;
    out.push([u * u * lo1 + 2 * u * t * cx + t * t * lo2, unY(u * u * y1 + 2 * u * t * cy + t * t * y2)]);
  }
  return out;
}
/** Screen angle of the last stretch of a curve, clockwise from north, for the arrowhead. */
const heading = ([lo1, la1], [lo2, la2]) => ((Math.atan2(lo2 - lo1, mercY(la2) - mercY(la1)) * 180) / Math.PI + 360) % 360;

/** GeoJSON for the map: coloured segments, dash overlay, arrowheads, nodes and market glows. */
export function geo() {
  const all = routes(), shown = all.filter((r) => !S.flow.off.has(r.key)), sc = speciesColors();
  const max = {}; shown.forEach((r) => (max[r.k] = Math.max(max[r.k] || 1, r.n)));
  const lines = [], dash = [], arrows = [], vol = {}, inb = {};
  shown.forEach((r) => {
    const a = r.ac || coords(r.a), b = r.bc || coords(r.b), pts = curve(a, b, 48);
    const q = Math.sqrt(r.n / max[r.k]), w = 1.4 + 7 * q, o = r.k === "d" ? 0.35 + 0.35 * q : 0.5 + 0.45 * q;
    const [ca, cb] = ends(r, sc), what = `${fmt(r.n)} ${KIND[r.k]}`, lab = label(r);
    const SEG = 12, step = Math.ceil((pts.length - 1) / SEG);
    for (let i = 0; i < pts.length - 1; i += step) {
      const seg = pts.slice(i, Math.min(pts.length, i + step + 1));
      lines.push({ type: "Feature", properties: { c: mix(ca, cb, (i + step / 2) / (pts.length - 1)), w, o, k: r.k, key: r.key, label: lab, what: `${what} · click for the evidence` }, geometry: { type: "LineString", coordinates: seg } });
    }
    if (r.k !== "d") dash.push({ type: "Feature", properties: { w }, geometry: { type: "LineString", coordinates: pts } });
    const j = pts.length - 3;
    arrows.push({ type: "Feature", properties: { c: cb, b: heading(pts[j - 2], pts[j]), s: 0.32 + 0.035 * w }, geometry: { type: "Point", coordinates: pts[j] } });
    if (r.k !== "n") { vol[r.a] = (vol[r.a] || 0) + r.n; vol[r.b] = (vol[r.b] || 0) + r.n; inb[r.b] = (inb[r.b] || 0) + r.n; }
  });
  const vmax = Math.max(1, ...Object.values(vol)), imax = Math.max(1, ...Object.values(inb)), R = roles();
  const nodeColor = (cc) => (S.flow.colorBy === "role" ? ROLE[roleOf(cc)][1] : S.flow.colorBy === "species" ? "#3c4a45" : REGION_COLOR[regionOf(cc)]);
  const nodes = Object.entries(vol).map(([cc, v]) => ({ type: "Feature",
    properties: { cc, name: name(cc), c: nodeColor(cc), r: 4 + 8 * Math.sqrt(v / vmax),
      what: `${regionName(regionOf(cc))} · all CITES seizures: taken ${fmt(R[cc]?.supply || 0)}, passed through ${fmt(R[cc]?.transit || 0)}, arriving ${fmt(R[cc]?.demand || 0)}` },
    geometry: { type: "Point", coordinates: coords(cc) } }));
  const glow = Object.entries(inb).map(([cc, v]) => ({ type: "Feature", properties: { c: nodeColor(cc), r: 14 + 30 * Math.sqrt(v / imax) }, geometry: { type: "Point", coordinates: coords(cc) } }));
  const fc = (features) => ({ type: "FeatureCollection", features });
  return { all, shown, lines: fc(lines), dash: fc(dash), arrows: fc(arrows), nodes: fc(nodes), glow: fc(glow), sc };
}

// ------------------------------------------------------------------ the story sentence
function story(shown) {
  const f = S.flow, seized = shown.filter((r) => r.k === "s" || r.k === "l");
  if (!shown.length) return "Nothing to draw with these choices. Widen the species or countries, or switch on more evidence.";
  if (f.story === "country" && f.country) {
    const v = roles()[f.country] || {};
    return `<b>${esc(name(f.country))}</b> is mostly a <b>${ROLE[roleOf(f.country)][0].toLowerCase()}</b>: ${fmt(v.supply || 0)} seized shipments taken from here, `
      + `${fmt(v.transit || 0)} passed through, ${fmt(v.demand || 0)} seized arriving, since ${S.data.flows.year_min}.`;
  }
  const top2 = (key) => { const c = {}; seized.forEach((r) => (c[regionOf(r[key])] = (c[regionOf(r[key])] || 0) + r.n));
    return Object.entries(c).sort((a, b) => b[1] - a[1]).slice(0, 2).map(([k]) => regionName(k)); };
  const what = f.groups.size ? [...f.groups].map(spLabel).join(", ") : "Wildlife";
  const lead = seized.length ? `${esc(what)} seized on the way from <b>${esc(top2("a").join(" and "))}</b> to <b>${esc(top2("b").join(" and "))}</b>. ` : "";
  // Each evidence layer is counted in its own unit; CITES and LEMIS overlap on US routes, so they are never summed.
  const UNIT = { s: "CITES seized shipments", l: "records seized at US ports", d: "declared shipments", n: "news cases" };
  const parts = Object.entries(UNIT).map(([k, u]) => { const rs = shown.filter((r) => r.k === k); return rs.length ? `<span class="mono">${fmt(rs.reduce((n, r) => n + r.n, 0))}</span> ${u}` : ""; }).filter(Boolean);
  return `${lead}${parts.join(" and ")} on ${shown.length} route${shown.length > 1 ? "s" : ""}.`;
}

// ------------------------------------------------------------------ controls (left panel in Flows mode)
const chk = (id, on, lab, sub = "") => `<label class="ck"><input type="checkbox" id="${id}" ${on ? "checked" : ""}><span><b>${lab}</b>${sub ? `<small>${sub}</small>` : ""}</span></label>`;
const seg = (id, opts, cur) => `<div class="seg" role="group" id="${id}">${opts.map(([v, l]) => `<button type="button" data-v="${v}" aria-pressed="${v === cur}">${l}</button>`).join("")}</div>`;

export function renderControls(el) {
  const f = S.flow, d = S.data.flows;
  if (!d) { el.innerHTML = `<div class="skeleton" style="height:120px"></div><p class="muted">Loading trade flows…</p>`; return; }
  const gTot = {}; d.seized.forEach(([g, , , , n]) => (gTot[g] = (gTot[g] || 0) + n));
  const groups = Object.keys(S.data.species).filter((g) => gTot[g]).sort((a, b) => gTot[b] - gTot[a]);
  const ccs = Object.keys(S.data.countries).sort((a, b) => ccName(a).localeCompare(ccName(b)));
  const years = {}; d.seized_years.forEach(([g, y, n]) => (!f.groups.size || f.groups.has(g)) && (years[y] = (years[y] || 0) + n));
  const ys = Object.keys(years).map(Number).sort(), ymax = Math.max(1, ...Object.values(years)), last = ys[ys.length - 1];
  const picker = (id, set) => `<div class="chips">${[...set].map((c) => `<button class="chip" data-rm="${id}" data-v="${c}">${icons.flag(c)}${esc(ccName(c))} <span class="x">✕</span></button>`).join("")}
    <select id="${id}" aria-label="Add a country"><option value="">${set.size ? "Add" : "Any country"}</option>${ccs.map((c) => `<option value="${c}">${esc(ccName(c))}</option>`).join("")}</select></div>`;
  el.innerHTML = `
    <h1 class="headline" style="font-size:25px">Where wildlife is taken, and where it is bought</h1>
    <p class="lede">Lines run from the country a specimen came from to the country that seized it. Build the view you need; every choice is in the link.</p>
    <div class="sec"><h3>Story</h3></div>
    ${seg("f-story", [["species", "Follow a species"], ["country", "Follow a country"], ["compare", "Compare routes"]], f.story)}
    ${f.story === "country" ? `<div class="sec"><h3>Country</h3></div><select id="f-country" aria-label="Country to follow" style="width:100%"><option value="">Choose a country</option>${ccs.map((c) => `<option value="${c}" ${c === f.country ? "selected" : ""}>${esc(ccName(c))}</option>`).join("")}</select>` : ""}
    <div class="sec"><h3>Species</h3>${f.groups.size ? `<button id="f-allg">All species</button>` : ""}</div>
    <div class="chips">${[...f.groups].map((g) => `<button class="chip" data-rm="g" data-v="${g}">${esc(spLabel(g))} <span class="x">✕</span></button>`).join("")}
      <select id="f-addg" aria-label="Add a species group"><option value="">${f.groups.size ? "Add species" : "All species · add one"}</option>${groups.filter((g) => !f.groups.has(g)).map((g) => `<option value="${g}">${esc(spLabel(g))} (${fmt(gTot[g])})</option>`).join("")}</select></div>
    ${f.story !== "country" ? `<div class="two"><div><div class="sec"><h3>Taken from</h3></div>${picker("f-from", f.from)}</div><div><div class="sec"><h3>Seized in</h3></div>${picker("f-to", f.to)}</div></div>` : ""}
    <div class="sec"><h3>Colour lines by</h3></div>
    ${seg("f-color", [["region", "Region"], ["role", "Role"], ["species", "Species"]], f.colorBy)}
    <div class="sec"><h3>How many routes</h3><span class="mono">top ${f.top}</span></div>
    <input type="range" id="f-top" min="3" max="40" value="${f.top}" aria-label="How many routes to draw" style="width:100%">
    <div class="sec"><h3>Evidence</h3></div>
    ${chk("f-ev-s", f.ev.seized, "Seized shipments", "CITES, source code I (confiscated or seized)")}
    ${chk("f-ev-l", f.ev.lemis, "Seized at US ports", "US Fish and Wildlife Service LEMIS, 2000–2022. Overlaps US-reported CITES seizures: compare, don't add")}
    ${chk("f-ev-d", f.ev.declared, "Declared trade", "CITES, all other sources: mostly legal, dashed")}
    ${chk("f-ev-n", f.ev.news, "News routes", "origin and destination named in WildTrace cases")}
    ${chk("f-spread", f.spread, "Spread across markets", `at most ${PER_MARKET} routes into any one country, so no single market fills the list`)}
    ${chk("f-us", !f.noUS, "Include the United States", "it reports seizures more completely than most")}
    <div class="sec"><h3>Seizures per year</h3><span class="muted" style="font-size:11.5px">${last} still being reported</span></div>
    <div class="yrs">${ys.map((y) => `<i title="${y}: ${fmt(years[y])}" style="height:${Math.max(2, (years[y] / ymax) * 44)}px" class="${y === last ? "part" : ""}"></i>`).join("")}</div>
    <div class="yrs-l"><span>${ys[0] || ""}</span><span>${last || ""}</span></div>
    <div class="row" style="margin-top:14px"><button class="btn" data-open="matrix">Who supplies whom</button><button class="btn" id="f-copy">Copy link</button><button class="btn" id="f-reset">Reset</button></div>
    <div class="m-only" id="f-routes-m"></div>
    <p class="muted" style="font-size:11.5px;margin-top:14px">${esc(d.cite)} Counts are shipment records, not quantities.</p>`;
  const set = (fn) => { fn(); f.off.clear(); emit("flows"); };
  el.querySelectorAll(".seg").forEach((sg) => sg.querySelectorAll("button").forEach((b) => b.addEventListener("click", () => set(() => {
    if (sg.id === "f-story") f.story = b.dataset.v; else f.colorBy = b.dataset.v;
  }))));
  el.querySelector("#f-country")?.addEventListener("change", (e) => set(() => (f.country = e.target.value)));
  el.querySelector("#f-addg").addEventListener("change", (e) => e.target.value && set(() => f.groups.add(e.target.value)));
  el.querySelector("#f-allg")?.addEventListener("click", () => set(() => f.groups.clear()));
  el.querySelector("#f-from")?.addEventListener("change", (e) => e.target.value && set(() => f.from.add(e.target.value)));
  el.querySelector("#f-to")?.addEventListener("change", (e) => e.target.value && set(() => f.to.add(e.target.value)));
  el.querySelectorAll("[data-rm]").forEach((b) => b.addEventListener("click", () => set(() => ({ g: f.groups, "f-from": f.from, "f-to": f.to }[b.dataset.rm].delete(b.dataset.v)))));
  el.querySelector("#f-top").addEventListener("change", (e) => set(() => (f.top = +e.target.value)));
  el.querySelector("#f-top").addEventListener("input", (e) => (e.target.previousElementSibling.querySelector(".mono").textContent = `top ${e.target.value}`));
  [["f-ev-s", "seized"], ["f-ev-l", "lemis"], ["f-ev-d", "declared"], ["f-ev-n", "news"]].forEach(([id, k]) => el.querySelector(`#${id}`).addEventListener("change", (e) => set(() => (f.ev[k] = e.target.checked))));
  el.querySelector("#f-us").addEventListener("change", (e) => set(() => (f.noUS = !e.target.checked)));
  el.querySelector("#f-spread").addEventListener("change", (e) => set(() => (f.spread = e.target.checked)));
  el.querySelector("#f-reset").addEventListener("click", () => set(() => Object.assign(f, { story: "species", country: "", colorBy: "region", top: 14, noUS: false, spread: true,
    ev: { seized: true, lemis: false, declared: false, news: false } }, f.groups.clear(), f.from.clear(), f.to.clear())));
  el.querySelector("#f-copy").addEventListener("click", () => navigator.clipboard?.writeText(location.href).then(() => dispatchEvent(new CustomEvent("wildtrace:toast", { detail: "Link to this view copied" }))));
  el.querySelectorAll("[data-open]").forEach((b) => b.addEventListener("click", () => dispatchEvent(new CustomEvent("wildtrace:open", { detail: b.dataset.open }))));
}

const spIcons = (r) => Object.entries(r.gs).sort((a, b) => b[1] - a[1]).slice(0, 3).map(([g]) => icons.sp(g, spLabel(g))).join("");

// ------------------------------------------------------------------ right panel: story + route switches + legend
export function renderSide(el, g) {
  const f = S.flow;
  const legend = f.colorBy === "role" ? Object.values(ROLE).map(([l, c, s]) => `<span class="lg"><i style="background:${c}"></i><b>${l}</b> ${s}</span>`).join("")
    : f.colorBy === "species" ? Object.entries(g.sc).map(([k, c]) => `<span class="lg"><i style="background:${c}"></i>${esc(spLabel(k))}</span>`).join("") + `<span class="lg"><i style="background:${GREY}"></i>Other</span>`
    : Object.entries(REGION_COLOR).map(([k, c]) => `<span class="lg"><i style="background:${c}"></i>${esc(regionName(k))}</span>`).join("");
  const top = Math.max(1, ...g.all.map((r) => r.n));
  const list = g.all.map((r) => {
    const on = !f.off.has(r.key), [ca, cb] = ends(r, g.sc);
    const gs = Object.entries(r.gs).sort((a, b) => b[1] - a[1]).slice(0, 2).map(([k]) => spLabel(k)).join(", ");
    return `<label class="route ${on ? "" : "off"}"><input type="checkbox" data-key="${esc(r.key)}" ${on ? "checked" : ""}>
      <span class="rt"><b class="rl" title="${esc(label(r))}">${flagLabel(r)}</b>${r.k === "d" ? ` <span class="status info">declared</span>` : r.k === "l" ? ` <span class="status bad">US ports</span>` : r.k === "n" ? ` <span class="status warn">news</span>` : ""}
        <i class="rb" style="width:${Math.max(6, (r.n / top) * 100)}%;background:linear-gradient(90deg,${ca},${cb})"></i><small>${spIcons(r)}${esc(gs)}</small></span>
      <span class="rt-r"><span class="mono">${fmt(r.n)}</span>${r.k !== "n" ? `<button class="ev" data-route="${esc(r.key)}" title="See the evidence for this route" aria-label="Evidence for ${esc(label(r))}"><b>Evidence</b> ›</button>` : ""}</span></label>`;
  }).join("");
  const html = `
    <div class="eyebrow" style="--c:var(--trade)">Your story</div>
    <p class="story">${story(g.shown)}</p>
    <div class="sec"><h3>Routes · ${g.shown.length} of ${g.all.length} on</h3><span><button data-all="1">All on</button> · <button data-all="0">All off</button></span></div>
    <div class="routes">${list || `<p class="muted">No routes.</p>`}</div>
    <div class="sec"><h3>${f.colorBy === "role" ? "Roles" : f.colorBy === "species" ? "Species" : "Line runs from source region to market region"}</h3></div>
    <div class="legend-f">${legend}</div>
    <p class="muted" style="font-size:11.5px;margin:10px 0 0">Thicker and more solid = more shipments. The glow under a market grows with what arrives. ${f.spread ? `Showing the busiest routes with at most ${PER_MARKET} per market; switch off "Spread across markets" for the raw ranking. ` : ""}${f.noUS ? "" : "The United States reports its seizures more completely than most countries, so it looks bigger than it may be."}</p>`;
  el.innerHTML = html;
  el.querySelectorAll("[data-key]").forEach((b) => b.addEventListener("change", () => { b.checked ? f.off.delete(b.dataset.key) : f.off.add(b.dataset.key); emit("flows"); }));
  el.querySelectorAll("[data-route]").forEach((b) => b.addEventListener("click", (e) => { e.preventDefault(); e.stopPropagation();
    dispatchEvent(new CustomEvent("wildtrace:go", { detail: { kind: "route", id: b.dataset.route } })); }));
  el.querySelectorAll("[data-all]").forEach((b) => b.addEventListener("click", () => { f.off.clear(); if (b.dataset.all === "0") g.all.forEach((r) => f.off.add(r.key)); emit("flows"); }));
}

// ------------------------------------------------------------------ the view in the URL
export function toQuery() {
  const f = S.flow, q = new URLSearchParams();
  q.set("mode", "flows");
  if (f.story !== "species") q.set("story", f.story);
  if (f.country) q.set("c", f.country);
  if (f.groups.size) q.set("g", [...f.groups].join(","));
  if (f.from.size) q.set("from", [...f.from].join(","));
  if (f.to.size) q.set("to", [...f.to].join(","));
  if (f.colorBy !== "region") q.set("colour", f.colorBy);
  if (f.top !== 14) q.set("n", f.top);
  const ev = Object.entries(f.ev).filter(([, v]) => v).map(([k]) => k[0]).join("");
  if (ev !== "s") q.set("ev", ev);
  if (f.noUS) q.set("us", "0");
  if (!f.spread) q.set("spread", "0");
  if (f.off.size) q.set("off", [...f.off].join(","));
  return q;
}
export function fromQuery(q) {
  const f = S.flow, list = (k) => (q.get(k) || "").split(",").filter(Boolean);
  f.story = q.get("story") || "species"; f.country = q.get("c") || "";
  f.groups = new Set(list("g")); f.from = new Set(list("from")); f.to = new Set(list("to"));
  f.colorBy = q.get("colour") || "region"; f.top = +q.get("n") || 14;
  const ev = q.get("ev") || "s"; f.ev = { seized: ev.includes("s"), lemis: ev.includes("l"), declared: ev.includes("d"), news: ev.includes("n") };
  f.noUS = q.get("us") === "0"; f.spread = q.get("spread") !== "0"; f.off = new Set(list("off"));
}

// ------------------------------------------------------------------ inspector blocks
/** Three-column Sankey of seized shipments for one species group: taken from -> shipped from -> seized in. */
export function sankey(gid) {
  const d = S.data.flows;
  if (!d) return "";
  const rows = d.seized.filter((r) => r[0] === gid);
  const tot = rows.reduce((n, r) => n + r[4], 0);
  if (tot < 5) return "";
  const top = (idx, k) => { const c = {}; rows.forEach((r) => (c[r[idx]] = (c[r[idx]] || 0) + r[4])); return new Set(Object.entries(c).sort((a, b) => b[1] - a[1]).slice(0, k).map(([x]) => x)); };
  const keep = [top(1, 3), top(2, 4), top(3, 4)];
  const key = (idx, v) => (keep[idx - 1].has(v) ? v : "OTHER");
  const L1 = {}, L2 = {}, cols = [{}, {}, {}];
  rows.forEach(([, o, e, i, n]) => {
    const a = key(1, o), b = key(2, e), c = key(3, i);
    L1[`${a}|${b}`] = (L1[`${a}|${b}`] || 0) + n; L2[`${b}|${c}`] = (L2[`${b}|${c}`] || 0) + n;
    cols[0][a] = (cols[0][a] || 0) + n; cols[1][b] = (cols[1][b] || 0) + n; cols[2][c] = (cols[2][c] || 0) + n;
  });
  const W = 384, H = 240, NW = 10, GAP = 8, X = [0, 168, W - NW], TOP = 22;
  const order = (c) => Object.keys(c).sort((a, b) => (a === "OTHER") - (b === "OTHER") || c[b] - c[a]);
  const pos = cols.map((c) => { const ks = order(c), sc = (H - TOP - GAP * (ks.length - 1)) / tot; let y = TOP; const p = {};
    ks.forEach((k) => { p[k] = { y, h: c[k] * sc, o: y, i: y }; y += c[k] * sc + GAP; }); p.sc = sc; return p; });
  const col = (ci, k) => (ci === 0 ? ROLE.supply[1] : ci === 2 ? ROLE.demand[1] : "")
    || ([...Object.keys(cols[0])].includes(k) && k !== "OTHER" ? ROLE.supply[1] : ROLE.transit[1]);
  const nm = (k, ci) => (k === "OTHER" ? (ci === 0 ? "Other / unrecorded" : "Other") : name(k));
  let bands = "";
  [[L1, 0], [L2, 1]].forEach(([L, ci]) => Object.entries(L).sort().forEach(([k, n]) => {
    const [a, b] = k.split("|"), s = pos[ci][a], t = pos[ci + 1][b], h0 = n * pos[ci].sc, h1 = n * pos[ci + 1].sc;
    const x0 = X[ci] + NW, x1 = X[ci + 1], m = (x0 + x1) / 2, y0 = s.o, y1 = t.i; s.o += h0; t.i += h1;
    bands += `<path d="M${x0},${y0} C${m},${y0} ${m},${y1} ${x1},${y1} L${x1},${y1 + h1} C${m},${y1 + h1} ${m},${y0 + h0} ${x0},${y0 + h0}Z" fill="${col(ci + 1, b)}" fill-opacity=".22"><title>${esc(nm(a, ci))} → ${esc(nm(b, ci + 1))}: ${fmt(n)}</title></path>`;
  }));
  const nodes = pos.map((p, ci) => order(cols[ci]).map((k) => `<rect x="${X[ci]}" y="${p[k].y}" width="${NW}" height="${Math.max(2, p[k].h)}" rx="3" fill="${col(ci, k)}"/>
    <text x="${ci === 2 ? X[ci] - 4 : X[ci] + NW + 4}" y="${p[k].y + Math.min(p[k].h, 24) / 2 + 4}" class="sk" text-anchor="${ci === 2 ? "end" : "start"}">${esc(nm(k, ci))} <tspan class="skn">${Math.round((cols[ci][k] / tot) * 100)}%</tspan></text>`).join("")).join("");
  const heads = ["TAKEN FROM", "SHIPPED FROM", "SEIZED IN"].map((t, i) => `<text x="${i === 2 ? W : X[i]}" text-anchor="${i === 2 ? "end" : "start"}" y="12" class="skh" fill="${[ROLE.supply[1], ROLE.transit[1], ROLE.demand[1]][i]}">${t}</text>`).join("");
  return `<div class="eyebrow" style="margin:16px 0 6px;--c:var(--trade)">Where it goes · ${fmt(tot)} seized shipments</div>
    <svg viewBox="0 0 ${W} ${H}" class="sankey" role="img" aria-label="Seized shipments of ${esc(spLabel(gid))}: country taken from, shipped from, seized in">${heads}${bands}${nodes}</svg>
    <p class="muted" style="font-size:11.5px;margin:4px 0 0">CITES Trade Database, source code I, since ${d.year_min}.</p>`;
}

/** Source / transit / market bar for one country. */
export function roleBar(cc) {
  const v = roles()[cc];
  if (!v) return "";
  const t = v.supply + v.transit + v.demand;
  return `<div class="eyebrow" style="margin:16px 0 8px;--c:var(--trade)">Source, hub or market?</div>
    <div class="rolebar" role="img" aria-label="Taken ${v.supply}, passed through ${v.transit}, seized arriving ${v.demand}">${Object.entries(ROLE).map(([k, [, c]]) => `<i style="width:${(v[k] / t) * 100}%;background:${c}"></i>`).join("")}</div>
    <dl class="facts" style="margin-top:8px">${Object.entries(ROLE).map(([k, [l, c]]) => `<dt><span class="dotc" style="background:${c}"></span>${k === "supply" ? "Taken from here" : k === "transit" ? "Passed through" : "Seized arriving"}</dt><dd class="num">${fmt(v[k])}</dd>`).join("")}</dl>
    <p class="muted" style="font-size:12px;margin:6px 0 0">Mostly a <b>${ROLE[roleOf(cc)][0].toLowerCase()}</b>, in seized shipments reported to CITES since ${S.data.flows.year_min}. <button class="linkish" data-follow="${cc}">Follow this country's flows</button></p>`;
}

// ------------------------------------------------------------------ sheet: who supplies whom
export function mountMatrix(root) {
  const d = S.data.flows;
  if (!d) { root.innerHTML = `<p class="muted" style="padding:18px">Loading…</p>`; return; }
  const st = { by: "countries", kingdom: "all", us: true };
  const BINS = [1, 10, 30, 100, 300], RAMP = ["#f6ead3", "#ecc98d", "#dca04a", "#b87708", "#7d4c00"];
  const cell = (v) => { if (!v) return ["transparent", "var(--ink-3)"]; const k = BINS.filter((b) => v >= b).length - 1; return [RAMP[k], k >= 3 ? "#fff" : "var(--ink)"]; };
  const draw = () => {
    const kg = (g) => st.kingdom === "all" || (S.data.species[g]?.kingdom || "animal") === st.kingdom;
    const m = {}, O = {}, I = {};
    d.seized.forEach(([g, o, , i, n]) => {
      if (o === "XX" || o === i || !kg(g) || (!st.us && (o === "US" || i === "US"))) return;
      const a = st.by === "regions" ? regionOf(o) : o, b = st.by === "regions" ? regionOf(i) : i;
      m[`${a}|${b}`] = (m[`${a}|${b}`] || 0) + n; O[a] = (O[a] || 0) + n; I[b] = (I[b] || 0) + n;
    });
    const rows = st.by === "regions" ? Object.keys(REGION_COLOR) : Object.entries(O).sort((a, b) => b[1] - a[1]).slice(0, 14).map(([k]) => k);
    const cols = st.by === "regions" ? Object.keys(REGION_COLOR) : Object.entries(I).sort((a, b) => b[1] - a[1]).slice(0, 11).map(([k]) => k);
    const lab = (k) => (st.by === "regions" ? regionName(k) : name(k));
    const dot = (k) => REGION_COLOR[st.by === "regions" ? k : regionOf(k)];
    const best = Object.entries(m).filter(([k]) => !k.includes("US")).sort((a, b) => b[1] - a[1])[0];
    root.innerHTML = `<div class="filters">
        ${seg("m-by", [["countries", "Countries"], ["regions", "Regions"]], st.by)}
        ${seg("m-k", [["all", "All species"], ["plant", "Plants"], ["animal", "Animals"]], st.kingdom)}
        <label class="ck" style="margin:0"><input type="checkbox" id="m-us" ${st.us ? "checked" : ""}><span><b>Include the United States</b></span></label>
        <span style="flex:1"></span><span class="muted" style="font-size:12.5px">Rows: where it was taken · Columns: where it was seized · click a cell to draw it</span></div>
      <div style="padding:12px 16px 16px;overflow:auto"><table class="matrix" aria-label="Seized shipments from each source to each market">
        <thead><tr><th scope="col"></th>${cols.map((c) => `<th scope="col"><span class="dotc" style="background:${dot(c)}"></span>${st.by === "countries" ? icons.flag(c) : ""}${esc(lab(c))}</th>`).join("")}</tr></thead>
        <tbody>${rows.map((r) => `<tr><th scope="row"><span class="dotc" style="background:${dot(r)}"></span>${st.by === "countries" ? icons.flag(r) : ""}${esc(lab(r))}</th>${cols.map((c) => { const v = m[`${r}|${c}`] || 0, [bg, fg] = cell(v);
          return `<td><button class="mc" style="background:${bg};color:${fg}" data-a="${r}" data-b="${c}" ${v ? "" : "disabled"} title="${esc(lab(r))} → ${esc(lab(c))}: ${fmt(v)} seized shipments">${v ? fmt(v) : "·"}</button></td>`; }).join("")}</tr>`).join("")}</tbody></table>
        <div class="row" style="margin-top:12px;gap:14px"><span class="muted" style="font-size:12px">Seized shipments</span>${RAMP.map((c, i) => `<span class="lg"><i style="background:${c};border-radius:4px;width:20px"></i>${["1–9", "10–29", "30–99", "100–299", "300+"][i]}</span>`).join("")}</div>
        ${best ? `<p style="font-size:13.5px;margin:12px 0 0">Leaving the US out, the busiest route here is <b>${esc(lab(best[0].split("|")[0]))} → ${esc(lab(best[0].split("|")[1]))}</b>, ${fmt(best[1])} seized shipments.</p>` : ""}
        <p class="muted" style="font-size:12px;margin:6px 0 0">${esc(d.note)}</p></div>`;
    root.querySelectorAll("#m-by button").forEach((b) => b.addEventListener("click", () => { st.by = b.dataset.v; draw(); }));
    root.querySelectorAll("#m-k button").forEach((b) => b.addEventListener("click", () => { st.kingdom = b.dataset.v; draw(); }));
    root.querySelector("#m-us").addEventListener("change", (e) => { st.us = e.target.checked; draw(); });
    root.querySelectorAll(".mc[data-a]").forEach((b) => b.addEventListener("click", () => {
      const f = S.flow;
      f.story = "species"; f.off.clear(); f.noUS = !st.us;
      if (st.by === "countries") { f.from = new Set([b.dataset.a]); f.to = new Set([b.dataset.b]); }
      else { f.from = new Set(Object.keys(S.data.countries).filter((c) => regionOf(c) === b.dataset.a)); f.to = new Set(Object.keys(S.data.countries).filter((c) => regionOf(c) === b.dataset.b)); }
      if (st.kingdom !== "all") f.groups = new Set(Object.keys(S.data.species).filter((g) => S.data.species[g].kingdom === st.kingdom));
      dispatchEvent(new CustomEvent("wildtrace:flows-focus"));
    }));
  };
  draw();
}

// ------------------------------------------------------------------ one route, with its evidence
const PURPOSE = { P: "personal", T: "commercial", S: "scientific", Z: "zoo", H: "hunting trophy", Q: "circus or travelling show",
  E: "education", B: "captive breeding", M: "medical", L: "law enforcement or court", N: "reintroduction", G: "botanical garden" };

/** Inspector page for a route "s|origin|importer" (seized) or "d|exporter|importer" (declared). */
export function routeView(key, ic) {
  if (key.startsWith("l|")) return lemisRouteView(key, ic);
  const [k, a, b] = key.split("|"), d = S.data.flows;
  if (!d) return `<p class="muted">Loading trade flows…</p>`;
  const rows = k === "s" ? d.seized.filter((r) => r[1] === a && r[3] === b) : [];
  const decl = k === "d" ? Object.entries(d.declared).flatMap(([g, rs]) => rs.filter((r) => r[0] === a && r[1] === b).map((r) => [g, r[2]])) : [];
  const total = k === "s" ? rows.reduce((n, r) => n + r[4], 0) : decl.reduce((n, r) => n + r[1], 0);
  const groups = {};
  (k === "s" ? rows.map((r) => [r[0], r[4]]) : decl).forEach(([g, n]) => (groups[g] = (groups[g] || 0) + n));
  const det = k === "s" ? S.data.flows_detail?.[`${a}|${b}`] : null;
  const via = det?.via?.map(([c]) => c) || [];
  const ccs = new Set([a, b, ...via]);
  const news = S.data.cases.filter((c) => c.place && ccs.has(c.place.country) && c.species.some((s) => groups[s]))
    .sort((x, y) => (y.date || "").localeCompare(x.date || "")).slice(0, 10);
  const plant = (g) => S.data.species[g]?.kingdom === "plant";
  const anyPlant = Object.keys(groups).some(plant);
  const years = det ? Object.entries(det.years) : [];
  const ymax = Math.max(1, ...years.map(([, n]) => n));
  const reporter = det ? Object.entries(det.reporter).map(([r, n]) => `${fmt(n)} reported by the ${r === "I" ? `importing country (${esc(name(b))})` : r === "E" ? `exporting country (${esc(name(a))})` : "a party"}`).join(", ") : "";
  return `
    <div class="eyebrow">${ic.ui("package")} Route · ${k === "s" ? "seized shipments" : "declared trade"}</div>
    <h2 class="title route-t">${ic.flag(a)}<span>${esc(name(a))}</span> <span class="muted">→</span> ${ic.flag(b)}<span>${esc(name(b))}</span></h2>
    <p class="muted" style="font-size:12px;margin:-4px 0 10px"><span class="dotc" style="background:${REGION_COLOR[regionOf(a)]}"></span>${esc(regionName(regionOf(a)))} → <span class="dotc" style="background:${REGION_COLOR[regionOf(b)]}"></span>${esc(regionName(regionOf(b)))}</p>
    <div class="tiles"><div class="tile"><div class="v">${fmt(total)}</div><div class="k">${k === "s" ? "shipments seized or confiscated" : "shipments declared (mostly legal)"}</div></div>
      <div class="tile"><div class="v">${years.length ? `${years[0][0]}–${years[years.length - 1][0]}` : `${d.year_min}+`}</div><div class="k">years on record</div></div></div>
    <div class="eyebrow" style="margin:6px 0 8px">What ${k === "s" ? "was seized" : "was traded"}</div>
    <div class="evid">${Object.entries(groups).sort((x, y) => y[1] - x[1]).map(([g, n]) =>
      `<button class="chip" data-go="species|${g}">${ic.sp(g)}${esc(spLabel(g))} <span class="muted">${fmt(n)}</span></button>`).join("")}</div>
    ${det ? `<div class="evid" style="margin-top:8px">${det.terms.filter(([t]) => t).map(([t, n]) => `<span class="term-chip">${ic.term(t, anyPlant)}${esc(t)} <span class="muted">${n}</span></span>`).join("")}</div>
      <p class="muted" style="font-size:12px;margin:8px 0 0">Recorded taxa: <i>${det.taxa.filter(([t]) => t).map(([t, n]) => `${esc(t)} (${n})`).join(", ")}</i></p>` : ""}
    ${years.length > 1 ? `<div class="eyebrow" style="margin:16px 0 6px">When</div>
      <div class="yrs">${years.map(([y, n]) => `<i title="${y}: ${n}" style="height:${Math.max(3, (n / ymax) * 44)}px"></i>`).join("")}</div>
      <div class="yrs-l"><span>${years[0][0]}</span><span>${years[years.length - 1][0]}</span></div>` : ""}
    ${det ? `<div class="box"><h4>Who reported it, and why it moved</h4>
      <p style="margin:0 0 6px">${reporter}.</p>
      ${Object.keys(det.purpose).length ? `<p style="margin:0 0 6px">Declared purpose: ${Object.entries(det.purpose).map(([p, n]) => `${esc(PURPOSE[p] || p || "not stated")} (${n})`).join(", ")}.</p>` : ""}
      ${via.length ? `<p style="margin:0">Re-exported through ${via.map((c) => esc(name(c))).join(", ")} on the way.</p>` : ""}</div>` : ""}
    <div class="box limit"><h4>Where is the article?</h4>
      <p style="margin:0 0 6px">This route is not built from news. Each record is a shipment a government reported to CITES in its annual report, with source code I: confiscated or seized. CITES anonymises individual shipments, so the counts, products, years and reporters above are the evidence.</p>
      <p style="margin:0"><a href="https://trade.cites.org/" target="_blank" rel="noopener">Check it in the CITES Trade Database ↗</a> (exporter ${esc(a)}, importer ${esc(b)}, source I, ${esc(String(d.year_min))} onward).</p></div>
    <div class="eyebrow" style="margin:16px 0 6px">${ic.ui("news")} In the news</div>
    ${news.length ? `<p class="muted" style="font-size:12px;margin:0 0 6px">WildTrace cases involving the same species in ${[...ccs].map((c) => esc(name(c))).join(", ")}. They support the pattern; they are not the same shipments.</p>
      ${news.map((c) => `<button class="link-row" data-go="case|${c.id}"><span style="display:inline-flex;gap:8px;align-items:center;min-width:0">${ic.kind(c.kind)}<span>${esc(c.summary)}</span></span>
        <span style="display:inline-flex;gap:4px;align-items:center">${(c.sources || []).slice(0, 3).map((s) => ic.outlet(s.outlet)).join("")}<span class="muted" style="font-size:12px;margin-left:4px">${esc(c.date || "")}</span></span></button>`).join("")}`
      : `<p class="muted" style="font-size:13px">No news case in WildTrace matches these species in these countries yet. News covers few of the seizures that governments report.</p>`}
    <div class="row" style="margin-top:14px"><button class="btn" data-act="copy">Copy link</button></div>
    <p class="muted" style="font-size:11.5px;margin-top:10px">${esc(d.cite)}</p>`;
}

/** News cases on the same species in the same countries: they support a route, they are not its shipments. */
function newsFor(ccs, groups, ic) {
  const news = S.data.cases.filter((c) => c.place && ccs.has(c.place.country) && c.species.some((s) => groups[s]))
    .sort((x, y) => (y.date || "").localeCompare(x.date || "")).slice(0, 10);
  return `<div class="eyebrow" style="margin:16px 0 6px">${ic.ui("news")} In the news</div>
    ${news.length ? `<p class="muted" style="font-size:12px;margin:0 0 6px">WildTrace cases involving the same species in ${[...ccs].map((c) => esc(name(c))).join(", ")}. They support the pattern; they are not the same shipments.</p>
      ${news.map((c) => `<button class="link-row" data-go="case|${c.id}"><span style="display:inline-flex;gap:8px;align-items:center;min-width:0">${ic.kind(c.kind)}<span>${esc(c.summary)}</span></span>
        <span style="display:inline-flex;gap:4px;align-items:center">${(c.sources || []).slice(0, 3).map((s) => ic.outlet(s.outlet)).join("")}<span class="muted" style="font-size:12px;margin-left:4px">${esc(c.date || "")}</span></span></button>`).join("")}`
      : `<p class="muted" style="font-size:13px">No news case in WildTrace matches these species in these countries yet.</p>`}`;
}

// LEMIS product names carry their definition in brackets ("Shoe (including boots)"): the chip shows the
// name, the tooltip the full text.
const prodChip = (d, t, n) => { const full = d.product_names[t] || t;
  return `<span class="term-chip" title="${esc(full)}">${esc(full.replace(/\s*\(.*\)\s*$/, ""))} <span class="muted">${fmt(n)}</span></span>`; };

/** Inspector page for a LEMIS route "l|origin|US": imports the US Fish and Wildlife Service seized. */
function lemisRouteView(key, ic) {
  const [, a, b] = key.split("|"), d = S.data.lemis;
  if (!d) return `<p class="muted">Loading US port seizures…</p>`;
  const rows = d.seized.filter((r) => r[1] === a && r[3] === b), total = rows.reduce((n, r) => n + r[4], 0);
  const groups = {}; rows.forEach(([g, , , , n]) => (groups[g] = (groups[g] || 0) + n));
  const det = d.detail?.[`${a}|${b}`];
  const years = det ? Object.entries(det.years) : [], ymax = Math.max(1, ...years.map(([, n]) => n));
  const via = det?.via?.map(([c]) => c) || [];
  const named = (m, names) => Object.entries(m).map(([k, n]) => `${esc(names?.[k] || k || "not stated")} (${fmt(n)})`).join(", ");
  return `
    <div class="eyebrow">${ic.ui("package")} Route · seized at US ports</div>
    <h2 class="title route-t">${ic.flag(a)}<span>${esc(name(a))}</span> <span class="muted">→</span> ${ic.flag(b)}<span>${esc(name(b))}</span></h2>
    <div class="tiles"><div class="tile"><div class="v">${fmt(total)}</div><div class="k">import records seized by US wildlife inspectors</div></div>
      <div class="tile"><div class="v">${years.length ? `${years[0][0]}–${years[years.length - 1][0]}` : "–"}</div><div class="k">years on record</div></div></div>
    <div class="eyebrow" style="margin:6px 0 8px">What was seized</div>
    <div class="evid">${Object.entries(groups).sort((x, y) => y[1] - x[1]).map(([g, n]) =>
      `<button class="chip" data-go="species|${g}">${ic.sp(g)}${esc(spLabel(g))} <span class="muted">${fmt(n)}</span></button>`).join("")}</div>
    ${det ? `<div class="evid" style="margin-top:8px">${det.products.map(([t, n]) => prodChip(d, t, n)).join("")}</div>
      <p class="muted" style="font-size:12px;margin:8px 0 0">Recorded taxa: <i>${det.taxa.filter(([t]) => t).map(([t, n]) => `${esc(t)} (${fmt(n)})`).join(", ")}</i></p>` : ""}
    ${years.length > 1 ? `<div class="eyebrow" style="margin:16px 0 6px">When</div>
      <div class="yrs">${years.map(([y, n]) => `<i title="${y}: ${n}" style="height:${Math.max(3, (n / ymax) * 44)}px"></i>`).join("")}</div>
      <div class="yrs-l"><span>${years[0][0]}</span><span>${years[years.length - 1][0]}</span></div>` : ""}
    ${det ? `<div class="box"><h4>What the importer declared</h4>
      <p style="margin:0 0 6px">Purpose: ${named(det.purpose, d.purpose_names)}.</p>
      <p style="margin:0 0 6px">Source: ${named(det.source, d.source_names)}.</p>
      ${via.length ? `<p style="margin:0">Shipped through ${via.map((c) => esc(name(c))).join(", ")}.</p>` : ""}</div>` : ""}
    <div class="box limit"><h4>Where is the article?</h4>
      <p style="margin:0 0 6px">This route is not built from news. Each record is a wildlife import the US Fish and Wildlife Service seized at a US port of entry (LEMIS disposition S), released under the Freedom of Information Act and cleaned by researchers. Seizures can follow missing permits as well as smuggling, and they measure US inspection effort as much as trade. The US also reports seizures to CITES, so this route can overlap the CITES seized layer: compare the two, never add them.</p>
      <p style="margin:0">${esc(d.note)}</p></div>
    ${newsFor(new Set([a, b, ...via]), groups, ic)}
    <div class="row" style="margin-top:14px"><button class="btn" data-act="copy">Copy link</button></div>
    <p class="muted" style="font-size:11.5px;margin-top:10px">${esc(d.cite)} ${esc(d.licence)}</p>`;
}

/** Species page block: what US inspectors seized of this group, and from where. */
export function lemisBlock(gid) {
  const d = S.data.lemis;
  if (!d) return "";
  const rows = d.seized.filter((r) => r[0] === gid), tot = rows.reduce((n, r) => n + r[4], 0);
  if (tot < 3) return "";
  const org = {}; rows.forEach(([, o, , , n]) => o !== "XX" && (org[o] = (org[o] || 0) + n));
  const top = Object.entries(org).sort((x, y) => y[1] - x[1]).slice(0, 5), omax = Math.max(1, ...top.map(([, n]) => n));
  const prod = (d.products[gid] || []).slice(0, 6);
  return `<div class="eyebrow" style="margin:16px 0 6px;--c:var(--trade)">Seized at US ports · ${fmt(tot)} records</div>
    <dl class="facts">${top.map(([cc, n]) => `<dt>${icons.flag(cc)}${esc(name(cc))}</dt><dd class="num"><i class="rb" style="display:inline-block;height:6px;border-radius:3px;margin-right:6px;vertical-align:middle;width:${Math.max(4, (n / omax) * 70)}px;background:${REGION_COLOR[regionOf(cc)]}"></i>${fmt(n)}</dd>`).join("")}</dl>
    ${prod.length ? `<div class="evid" style="margin-top:8px">${prod.map(([t, n]) => prodChip(d, t, n)).join("")}</div>` : ""}
    <p class="muted" style="font-size:11.5px;margin:6px 0 0">Imports the US Fish and Wildlife Service seized, by country of origin and product (LEMIS; Marshall et al. 2025, Eskew et al. 2020; CC BY 4.0).</p>`;
}
