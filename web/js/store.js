// Shared state: data, filters, layer visibility and the navigation trail.
// Every surface reads from here and calls `emit()` after a change; subscribers redraw.
import { KIND } from "./globe.js";

export const S = {
  data: { cases: [], species: {}, countries: {}, obs: { observatories: [], categories: {} }, meta: {}, report: {}, trade: {}, sources: [], codewords: [], graph: { elements: [] } },
  filters: { kinds: new Set(), species: new Set(), countries: new Set(), ver: new Set(), range: null },
  layers: { cases: true, routes: false, observatories: false, mine: true },   // news routes: shown in Flows only
  trail: [], pos: -1, // navigation stack for the inspector (back / forward)
  // Atlas mode: "cases" (the default map), "flows" (supply -> demand) or "zoo" (zoonoses).
  mode: "cases",
  // Flows: what the reader chose to see. Every field round-trips through the URL (see flows.js).
  flow: { story: "species", groups: new Set(), from: new Set(), to: new Set(), country: "", colorBy: "region", top: 14,
    ev: { seized: true, declared: false, news: false }, off: new Set(), noUS: false, spread: true },
  // Zoonoses: which transmission pathways and overlays are on.
  zoo: { pathways: new Set(["wildlife", "birds", "livestock", "vector"]), cases: true, disease: "" },
};
const subs = new Set();
export const on = (fn) => (subs.add(fn), () => subs.delete(fn));
export const emit = (what = "filters") => subs.forEach((fn) => fn(what));

// graph.json (the link chart) is fetched only when Investigate opens: see loadGraph().
const FILES = { cases: "cases", stats: "stats", species: "species", countries: "countries", regions: "regions", obs: "observatories", meta: "meta", speciesIcons: "species_icons", outlets: "outlets",
  report: "model_report", trade: "trade_signals", sources: "sources", codewords: "codewords", answers: "answers" };
export async function loadGraph() {
  if (!S.data.graph.elements?.length) {
    try { S.data.graph = await (await fetch("data/graph.json", { cache: "no-cache" })).json(); } catch { /* keep empty */ }
  }
  return S.data.graph;
}
/** Verification bucket used by the filter: official and validated count as "strong". */
export const verBucket = (c) => (c.verification === "validated" || c.verification === "official" ? "strong" : c.verification || "single");
export async function load() {
  await Promise.all(Object.entries(FILES).map(async ([k, f]) => {
    try { S.data[k] = await (await fetch(`data/${f}.json`, { cache: "no-cache" })).json(); } catch { /* keep default */ }
  }));
  S.data.byId = Object.fromEntries(S.data.cases.map((c) => [c.id, c]));
  S.data.obsById = Object.fromEntries((S.data.obs.observatories || []).map((o) => [o.id, o]));
}

// Flows and zoonoses data are larger and only needed in their modes: fetched once, on demand.
const lazy = {};
export function loadExtra(name) {
  return (lazy[name] ||= fetch(`data/${name}.json`, { cache: "no-cache" }).then((r) => (r.ok ? r.json() : null)).catch(() => null)
    .then((d) => { S.data[name] = d; return d; }));
}

export const spLabel = (g) => S.data.species[g]?.label || g;
// Country names: the gazetteer first, then the browser's own list (covers codes such as HK or MO
// that appear in CITES data but have no case).
let regionNames = null;
try { regionNames = new Intl.DisplayNames(["en"], { type: "region" }); } catch { /* old browser */ }
export const ccName = (cc) => S.data.countries[cc]?.name || (cc && /^[A-Z]{2}$/.test(cc) && cc !== "XX" ? regionNames?.of(cc) : null) || cc;

/** Cases that pass the current filters (optionally ignoring one facet, for facet counts). */
export function filtered(ignore = "") {
  const f = S.filters;
  return S.data.cases.filter((c) =>
    (ignore === "kinds" || !f.kinds.size || f.kinds.has(KIND(c.kind))) &&
    (ignore === "species" || !f.species.size || c.species.some((s) => f.species.has(s))) &&
    (ignore === "countries" || !f.countries.size || f.countries.has(c.place?.country)) &&
    (ignore === "ver" || !f.ver.size || f.ver.has(verBucket(c))) &&
    (ignore === "range" || !f.range || (c.date && c.date >= f.range[0] && c.date <= f.range[1])));
}

export function toggle(facet, value) {
  const set = S.filters[facet];
  set.has(value) ? set.delete(value) : set.add(value);
  emit("filters");
}

export function clearFilters() {
  S.filters.kinds.clear(); S.filters.species.clear(); S.filters.countries.clear(); S.filters.ver.clear(); S.filters.range = null;
  emit("filters");
}

// ---- navigation trail: a stack of {kind, id}; the URL hash mirrors the current item
export function go(item, { replace = false } = {}) {
  if (!item) return;
  const cur = S.trail[S.pos];
  if (cur && cur.kind === item.kind && cur.id === item.id) { emit("nav"); return; }
  if (replace && S.pos >= 0) S.trail[S.pos] = item;
  else { S.trail = S.trail.slice(0, S.pos + 1); S.trail.push(item); S.pos = S.trail.length - 1; }
  const h = `#${item.kind}/${encodeURIComponent(item.id)}`;
  if (location.hash !== h) history.pushState(null, "", h);
  emit("nav");
}
export const back = () => { if (S.pos > 0) { S.pos--; sync(); } };
export const fwd = () => { if (S.pos < S.trail.length - 1) { S.pos++; sync(); } };
export const closeTrail = () => { S.pos = -1; S.trail = []; history.pushState(null, "", location.pathname + location.search); emit("nav"); };
function sync() { const c = S.trail[S.pos]; history.replaceState(null, "", `#${c.kind}/${encodeURIComponent(c.id)}`); emit("nav"); }
export function fromHash() {
  const m = location.hash.match(/^#(answer|case|species|country|obs|entity|route)\/(.+)$/);
  return m ? { kind: m[1], id: decodeURIComponent(m[2]) } : null;
}
