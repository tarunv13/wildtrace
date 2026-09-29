/* Tours: the main walkthrough, plus a short tour inside every section.
 *
 * The main tour runs once for a first-time reader (and from the Tour menu). Each section (Flows,
 * Zoonoses, Investigate and its import tab, Analysis, the heatmap, Network, Table, Methods) has
 * its own short tour that runs the first time the reader opens it, unless they switched section
 * tips off. Every card carries that switch; the Tour button opens a menu to replay any tour.
 *
 * Each step spotlights a real element (a hole cut in a dimming overlay, so the thing explained is
 * the live interface) and places its card where there is room. Steps whose element is not on
 * screen are skipped. Keyboard: → or Enter next, ← back, Esc to leave; focus stays in the card.
 */
const KEY = "wildtrace.tour.v2";      // main tour seen
const TIPS = "wildtrace.tips";         // "off" = no automatic section tours
const SEEN = "wildtrace.tip.";         // + section key

const store = {
  get: (k) => { try { return localStorage.getItem(k); } catch { return null; } },
  set: (k, v) => { try { localStorage.setItem(k, v); } catch { /* private window */ } },
};
export const tipsOn = () => store.get(TIPS) !== "off";
export const setTips = (on) => store.set(TIPS, on ? "on" : "off");

const open = (what) => () => dispatchEvent(new CustomEvent("wildtrace:open", { detail: what }));
const mode = (m) => () => dispatchEvent(new CustomEvent("wildtrace:mode", { detail: m }));

export const TOURS = {
  main: { name: "The Atlas", steps: [
    { el: null, title: "Welcome to WildTrace",
      body: "One open map of the illegal trade in wild animals and plants: seizures, arrests and convictions from public reports, where traded wildlife comes from and goes, and where animal-borne outbreaks are reported. About a minute; leave at any point. Prefer to watch? A 2-minute video shows how to ask a question, read the answer and check its evidence.",
      cta: [["▶ Watch the 2-minute video", () => dispatchEvent(new CustomEvent("wildtrace:video"))]] },
    { el: "#globe", place: "center", title: "The Atlas",
      body: "Every case sits where its report says it happened. The icon inside a point is the kind of event (box: seizure, lock: arrest, hands: rescue); paler points rest on a single report; a ring means the place is approximate; the glow shows where reporting is dense. Switch cases and observatories on and off in the legend, bottom right, and turn on satellite imagery with the map buttons to see the landscape. Trade routes live in Flows." },
    { el: ".modes", title: "Three ways to read the map",
      body: "<b>Cases</b> is the news record. <b>Flows</b> shows where wildlife is taken and where it is seized, from government reports to CITES. <b>Zoonoses</b> places animal-borne outbreaks beside the trade. Each has its own short tour the first time you open it." },
    { el: "#pulse", title: "Pulse: what is in view",
      body: "A live summary of whatever the map shows, and every row is a filter: click a species or a country to narrow the map to it. In Flows and Zoonoses this panel becomes the controls." },
    { el: "#tl", title: "The timeline",
      body: "Cases per week across the whole record. Drag across it to choose a period; the map and Pulse follow. Play glides through the cases in time order." },
    { el: "#omni", title: "One search box",
      body: "Cases, species, countries and observatories in the same box. Press / from anywhere to jump into it." },
    { el: '[data-sheet="analysis"]', title: "Analysis",
      body: "What the evidence shows on one sheet: cases over time, events, species, which countries are sources or markets, how wildlife moves, and CITES seizures by year, each chart saying what it cannot show." },
    { el: '[data-sheet="table"]', title: "Every case as a table",
      body: "Sortable and filterable, with a CSV download. Cases with no mappable place are listed too, marked as not mapped rather than dropped." },
    { el: '[data-sheet="network"]', title: "The observatory network",
      body: "The 33 databases, dashboards and codebooks that watch this trade, each checked, with what WildTrace takes from it." },
    { el: '[data-sheet="investigate"]', title: "Investigate: your own analysis bench",
      body: "A link chart of cases, species, places, agencies and outlets. Isolate a cluster, expand a node, find the shortest path between two entities, and export to PNG, GraphML, CSV or JSON. <b>Your data</b> lets you import a spreadsheet and chart it against the public record, in your browser only: nothing is uploaded. Any case can be sent here with <i>Chart this case</i>.",
      cta: [["Show me Investigate", () => { open("investigate")(); setTimeout(() => startSection("investigate", { force: true }), 900); }]] },
    { el: '[data-sheet="methods"]', title: "Methods and About",
      body: "How a report becomes a case, how far to trust one (validated, official, corroborated or single report), the data sources and licences, and how to cite. Every case has a Report a correction link." },
    { el: "#tour-btn", title: "The guide, any time",
      body: "Open Guide to watch the 2-minute video again, replay this tour, tour the section you are in, or switch the automatic section tips off.",
      cta: [["Show me Flows", () => { mode("flows")(); setTimeout(() => startSection("flows", { force: true }), 1400); }]] },
  ] },
  flows: { name: "Flows", steps: [
    { el: "#pulse", title: "Build your view",
      body: "Flows draws seized shipments that governments report to CITES, from the country a specimen was taken to the country that seized it. Everything you choose here is kept in the link, so a view can be shared." },
    { el: "#f-story", title: "Choose a story",
      body: "Follow a species, follow one country (as source, hub and market), or compare the busiest routes." },
    { el: "#f-addg", title: "Species",
      body: "Add one or more species groups; each chip can be removed. With none chosen, every group is included." },
    { el: ".two", title: "Taken from, seized in",
      body: "Limit the routes to source countries, market countries, or both." },
    { el: "#f-color", title: "Colour",
      body: "Region shades each line from the source region's colour to the market's. Role shows sources, hubs and markets. Species colours by what was seized." },
    { el: "#f-ev-s", title: "Evidence",
      body: "Seized shipments reported to CITES are the default. Add imports seized at US ports (LEMIS), declared (mostly legal) trade, drawn dashed, or the routes named in news cases. “Spread across markets” (on by default) keeps any one country from filling the list; untick the United States to compare the rest, since it reports seizures more completely than most." },
    { el: "#fs-body", title: "Routes, and the proof behind each",
      body: "Every route is a switch. <b>Evidence</b> opens what was seized, when, who reported it and why it moved, the news cases for the same species in those countries, and a link to check the CITES database. Clicking a line on the map opens it too." },
    { el: '[data-open="matrix"]', title: "Who supplies whom",
      body: "The same data as a heatmap of sources against markets, by country or region. Click a cell to draw that route." },
  ] },
  zoo: { name: "Zoonoses", steps: [
    { el: "#pulse", title: "A shared map, not a cause",
      body: "WHO outbreak reports of animal-borne disease, beside the wildlife trade. An outbreak near a seizure does not mean the trade caused it; this view shows where to look closer." },
    { el: "[data-pw]", title: "How it reaches people",
      body: "Diseases are grouped by route to people: wildlife contact, birds, livestock, insects and ticks. Switch pathways on and off; pick a disease to see only it." },
    { el: "#z-cases", title: "WildTrace cases as rings",
      body: "Dark rings mark where trafficking cases are reported, so the two layers can be read together." },
    { el: "#fs-body", title: "Countries with both",
      body: "Wildlife-contact outbreak reports next to seized shipments taken from the same country and WildTrace cases there. Click a country for its record." },
    { el: '[data-open="zoo"]', title: "Species and viruses",
      body: "Which traded species groups carry viruses also found in people, or close relatives of them, confirmed by sequencing or isolation (VIRION), with notes from the research literature." },
  ] },
  investigate: { name: "Investigate", steps: [
    { el: "#cy", place: "top", title: "The link chart",
      body: "Cases (red squares) joined to species, places, agencies and outlets. It opens on the best-connected part of the record. Drag to move, scroll to zoom, click an entity to see its links." },
    { el: ".wb-side", place: "right", title: "Filter and arrange",
      body: "Find an entity, switch entity types on and off, change the layout, size entities by connections or brokerage, and colour by community to see clusters." },
    { el: ".wb-tools", place: "bottom", title: "Tools",
      body: "Fit the view, Expand a node's neighbours, Isolate a selection, Hide what is noise, and Reset. Shift-click two entities and choose Shortest path to see how they connect." },
    { el: "#x-png", place: "bottom", title: "Take it with you",
      body: "Export what is on screen as a PNG, or the network as GraphML (Gephi, i2, yEd), CSV or JSON." },
    { el: "#wb-insp", place: "left", title: "Selection, as text",
      body: "Everything selected is listed here with its links, so the chart is readable without seeing it. Cases open on the map from here." },
    { el: '#sheet-tabs [data-t="import"]', place: "bottom", title: "Bring your own data",
      body: "Import a CSV, Excel or JSON file of your own entities or links and chart it against the public record. It stays in your browser: nothing is uploaded." },
  ] },
  import: { name: "Your data", steps: [
    { el: "#drop", place: "bottom", title: "Drop a file",
      body: "CSV, TSV, Excel or JSON. Each row can be one entity, or a link between two. The first rows are previewed before anything is added." },
    { el: "#sample", place: "bottom", title: "Try it with a sample",
      body: "A small fictional dataset shows how import works without touching real data." },
    { el: "#clear-local", place: "bottom", title: "Private by design",
      body: "Your data is kept in this browser only and never sent anywhere. Clear it here whenever you like." },
  ] },
  analysis: { name: "Analysis", steps: [
    { el: ".an-tiles", place: "bottom", title: "The record in five numbers",
      body: "Cases, the reports behind them, countries, people reported arrested (a count only, never names), and cases involving the most endangered species." },
    { el: "#an-month", place: "top", title: "Read time with care",
      body: "Cases per month reflect news coverage, which widened over time, not the size of the trade." },
    { el: ".bal", place: "top", title: "Source or market?",
      body: "For each country, seized shipments taken from it (left) against those seized arriving there (right)." },
  ] },
  matrix: { name: "Who supplies whom", steps: [
    { el: ".matrix", place: "top", title: "Sources against markets",
      body: "Rows are where wildlife was taken, columns where it was seized. Darker cells hold more shipments. Click a cell to draw that route on the map." },
    { el: "#m-by", place: "bottom", title: "Countries or regions",
      body: "Switch to eight regions for the big picture, or narrow to plants or animals." },
    { el: "#m-us", place: "bottom", title: "Without the United States",
      body: "The US reports its seizures more completely than most. Untick it to compare the rest fairly." },
  ] },
  network: { name: "Network", steps: [
    { el: "#sheet-body .filters", place: "bottom", title: "Filter by kind",
      body: "Intelligence platforms, online-trade monitors, courts, trade statistics, reference data, tools, public reporting, journalism and funding." },
    { el: "#sheet-body .obs", place: "top", title: "Each observatory, checked",
      body: "Its status when last checked, who runs it, what it does, and how WildTrace uses it. Click a card for its record and link." },
  ] },
  table: { name: "Table", steps: [
    { el: "#t-q", place: "bottom", title: "Filter the record",
      body: "Type to filter by any word: species, place, agency. Column headers sort." },
    { el: '#sheet-body a[download]', place: "bottom", title: "Download",
      body: "The full record as CSV, CC BY 4.0." },
  ] },
  methods: { name: "Methods", steps: [
    { el: "#sheet-tabs", place: "bottom", title: "How it is made",
      body: "The pipeline, the classifier, what is never published, and every data source with its licence." },
  ] },
};

const $ = (s) => document.querySelector(s);
let steps = [], idx = 0, root = null, onKey = null, lastFocus = null, current = null, queued = null;

/** On the page and drawn (inside a scrolling panel counts: render() scrolls it into view). */
function present(sel) {
  const el = sel && $(sel);
  const r = el && el.getBoundingClientRect();
  return !!(r && r.width > 0 && r.height > 0 && getComputedStyle(el).visibility !== "hidden");
}
function visible(sel) {
  const el = sel && $(sel);
  const r = el && el.getBoundingClientRect();
  return r && r.width > 0 && r.height > 0 && r.bottom > 0 && r.top < innerHeight && getComputedStyle(el).visibility !== "hidden" ? r : null;
}

/** Put the card beside the hole where there is most room. */
function position(card, hole, place) {
  const pad = 14, w = card.offsetWidth, h = card.offsetHeight;
  let left, top;
  if (!hole || place === "center") { left = (innerWidth - w) / 2; top = (innerHeight - h) / 2; }
  else {
    const room = { right: innerWidth - hole.right, left: hole.left, bottom: innerHeight - hole.bottom, top: hole.top };
    const side = place && room[place] > (place === "left" || place === "right" ? w : h) + pad ? place
      : Object.entries(room).sort((a, b) => b[1] - a[1])[0][0];
    if (side === "right") { left = hole.right + pad; top = hole.top; }
    else if (side === "left") { left = hole.left - w - pad; top = hole.top; }
    else if (side === "top") { left = hole.left; top = hole.top - h - pad; }
    else { left = hole.left; top = hole.bottom + pad; }
  }
  card.style.left = `${Math.max(pad, Math.min(left, innerWidth - w - pad))}px`;
  card.style.top = `${Math.max(pad, Math.min(top, innerHeight - h - pad))}px`;
}

function render() {
  const s = steps[idx];
  if (s.el && !visible(s.el)) $(s.el)?.scrollIntoView({ block: "center", behavior: "instant" });
  const box = s.el ? visible(s.el) : null;
  const cut = root.querySelector(".tour-cut");
  if (box) {
    cut.hidden = false;
    Object.assign(cut.style, { left: `${box.left - 6}px`, top: `${box.top - 6}px`, width: `${box.width + 12}px`, height: `${box.height + 12}px` });
  } else cut.hidden = true;
  const last = idx === steps.length - 1;
  const card = root.querySelector(".tour-card");
  card.innerHTML = `
    <div class="tour-step mono">${current === "main" ? "Guided tour" : `${TOURS[current].name} tour`} · step ${idx + 1} of ${steps.length}</div>
    <h2>${s.title}</h2>
    <p>${s.body}</p>
    ${s.cta ? `<div class="row" style="margin:-4px 0 12px">${s.cta.map(([l], i) => `<button class="btn tour-cta" data-i="${i}">${l}</button>`).join("")}</div>` : ""}
    <div class="tour-nav">
      <button class="btn tour-skip">${last ? "Close" : "Skip"}</button>
      <span style="flex:1"></span>
      ${idx ? '<button class="btn tour-prev">Back</button>' : ""}
      <button class="btn primary tour-next">${last ? (current === "main" ? "Start exploring" : "Done") : "Next"}</button>
    </div>
    <label class="tour-tips"><input type="checkbox" ${tipsOn() ? "" : "checked"}> Don't show section tips automatically</label>`;
  card.classList.remove("bloom"); void card.offsetWidth; card.classList.add("bloom");
  position(card, box, s.place);
  card.querySelector(".tour-next").addEventListener("click", () => step(1));
  card.querySelector(".tour-prev")?.addEventListener("click", () => step(-1));
  card.querySelector(".tour-skip").addEventListener("click", end);
  card.querySelector(".tour-tips input").addEventListener("change", (e) => setTips(!e.target.checked));
  card.querySelectorAll(".tour-cta").forEach((b) => b.addEventListener("click", () => { const fn = s.cta[+b.dataset.i][1]; end(); fn(); }));
  card.querySelector(".tour-next").focus();
}

function step(d) {
  const next = idx + d;
  if (next >= steps.length) return end();
  idx = Math.max(0, next);
  render();
}

export function endTour() { end(); }
function end() {
  if (!root) return;
  store.set(current === "main" ? KEY : SEEN + current, "done");
  removeEventListener("keydown", onKey, true);
  removeEventListener("resize", render);
  root.classList.add("out");
  const r = root; root = null;
  setTimeout(() => r.remove(), 220);
  lastFocus?.focus?.();
  document.body.classList.remove("touring");
  if (queued) { const q = queued; queued = null; setTimeout(() => startSection(q), 500); }
}

function run(key) {
  // Keep only steps whose element is on screen (a welcome card has none and always shows).
  steps = TOURS[key].steps.filter((s) => !s.el || present(s.el));
  if (!steps.length) return;
  current = key; idx = 0;
  lastFocus = document.activeElement;
  root = document.createElement("div");
  root.className = "tour";
  root.innerHTML = `<div class="tour-veil"></div><div class="tour-cut" hidden></div><div class="tour-card glass" role="dialog" aria-modal="true" aria-label="${TOURS[key].name} tour"></div>`;
  document.body.append(root);
  document.body.classList.add("touring");
  root.querySelector(".tour-veil").addEventListener("click", end);
  onKey = (e) => {
    if (e.key === "Escape") { e.preventDefault(); end(); }
    else if (e.key === "ArrowRight" || (e.key === "Enter" && !e.target.closest?.(".tour-tips"))) { e.preventDefault(); step(1); }
    else if (e.key === "ArrowLeft") { e.preventDefault(); step(-1); }
    else if (e.key === "Tab") { e.preventDefault(); }
  };
  addEventListener("keydown", onKey, true);
  addEventListener("resize", render);
  render();
}

/** The main tour. `auto` runs it only for a reader who has not seen it. */
export function startTour({ auto = false } = {}) {
  if (root || (auto && store.get(KEY) === "done") || innerWidth < 860) return;   // tours point at the desktop layout
  run("main");
}

/** A section's tour. Automatic the first time a section opens, unless tips are off; `force` from the menu. */
export function startSection(key, { force = false } = {}) {
  if (!TOURS[key] || innerWidth < 860) return;
  if (!force && (!tipsOn() || store.get(SEEN + key) === "done")) return;
  if (!force && store.get(KEY) !== "done") return;          // the main tour comes first
  if (root) { if (!force) queued = key; return; }
  setTimeout(() => run(key), force ? 0 : 700);             // let the section finish drawing
}

/** The Tour button's menu: replay the main tour, tour this section, switch tips on or off. */
export function tourMenu(anchor, section) {
  document.querySelector(".tour-menu")?.remove();
  const m = document.createElement("div");
  m.className = "tour-menu glass";
  m.setAttribute("role", "menu");
  const r = anchor.getBoundingClientRect();
  m.style.top = `${r.bottom + 8}px`;
  m.style.right = `${Math.max(12, innerWidth - r.right)}px`;
  const sec = section && TOURS[section] && section !== "main" ? section : null;
  m.innerHTML = `
    <button role="menuitem" data-a="video" class="tm-video">▶ Watch the 2-minute video guide</button>
    <button role="menuitem" data-a="main">Full tour of the Atlas</button>
    ${sec ? `<button role="menuitem" data-a="sec">Tour this section: ${TOURS[sec].name}</button>` : ""}
    <label class="tm-switch"><input type="checkbox" ${tipsOn() ? "checked" : ""}> Show section tips the first time I open a section</label>
    <button role="menuitem" data-a="reset" class="muted">Show every section tip again</button>`;
  document.body.append(m);
  const close = (e) => { if (!m.contains(e.target) && e.target !== anchor) { m.remove(); removeEventListener("pointerdown", close, true); } };
  addEventListener("pointerdown", close, true);
  m.querySelector('[data-a="main"]').addEventListener("click", () => { m.remove(); run("main"); });
  m.querySelector('[data-a="video"]').addEventListener("click", () => { m.remove(); dispatchEvent(new CustomEvent("wildtrace:video")); });
  m.querySelector('[data-a="sec"]')?.addEventListener("click", () => { m.remove(); startSection(sec, { force: true }); });
  m.querySelector("input").addEventListener("change", (e) => setTips(e.target.checked));
  m.querySelector('[data-a="reset"]').addEventListener("click", () => {
    Object.keys(TOURS).forEach((k) => store.set(SEEN + k, "")); setTips(true); m.remove();
    dispatchEvent(new CustomEvent("wildtrace:toast", { detail: "Section tips will show again" }));
  });
  m.querySelector("button").focus();
}
