// The inspector: one panel, many subjects (case, species, country, observatory,
// your own entity). Everything links onward, so a reader can wander
// case → species → country → another case and step back again.
import { esc, fmt } from "./charts.js";
import { KIND, KIND_COLOR, KIND_LABEL } from "./globe.js";
import { S, ccName, go, spLabel } from "./store.js";
import { lemisBlock, roleBar, routeView, sankey } from "./flows.js";
import * as ic from "./icons.js";
import { countryBlock, speciesBlock } from "./zoo.js";

const HUE = { case: "var(--cases)", species: "var(--species)", country: "var(--place)", obs: "var(--network)", entity: "var(--invest)", route: "var(--trade)" };
const LANG = { en: "English", hi: "Hindi", hi_latn: "Hindi (Latin)", te: "Telugu", te_latn: "Telugu (Latin)", vi: "Vietnamese", id_ms: "Indonesian / Malay",
  th: "Thai", pt: "Portuguese", es: "Spanish", fr: "French" };
const inr = (v) => (v == null ? null : v >= 1e7 ? `₹${(v / 1e7).toFixed(1)} crore` : v >= 1e5 ? `₹${(v / 1e5).toFixed(1)} lakh` : `₹${fmt(v)}`);
const VER = {
  validated: ["good", "✓ Validated", "Checked by a person against its sources."],
  official: ["good", "● Official source", "At least one report is a government, customs, police or judicial release."],
  corroborated: ["info", "◑ Corroborated", "Two or more independent outlets report it."],
  single: ["warn", "○ Single report", "One outlet only. Treat it as a lead until it is corroborated."],
};
const TIER = { official: "Official", ngo: "NGO", media: "Media" };
const correction = (c) => `https://github.com/tarunv13/wildtrace/issues/new?labels=correction&title=${encodeURIComponent(`Correction: case ${c.id}`)}&body=${encodeURIComponent(
  `Case: ${c.summary}\nID: ${c.id}\nLink: ${location.origin}${location.pathname}#case/${c.id}\n\nWhat is wrong, and the source that shows it:\n`)}`;

const MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
const longDate = (d) => {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(d || "");
  return m ? `${+m[3]} ${MONTHS[+m[2] - 1]} ${m[1]}` : "an unrecorded date";
};
const WORDS = ["no", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten"];
const count = (n) => (n <= 10 ? WORDS[n] : String(n));
const listOf = (xs) => (xs.length < 2 ? xs.join("") : `${xs.slice(0, -1).join(", ")} and ${xs[xs.length - 1]}`);
const KIND_VERB = { seizure: "A seizure", arrest: "An arrest or conviction", other: "A rescue or report" };

/** A plain-language account of the case, assembled from what the reports actually stated.
 *  It repeats nothing the reader cannot check in the sources listed below, and every
 *  attribution ("as the reports state") is kept, because none of it is independently verified. */
function narrative(c, place, qs) {
  const sp = c.species.map(spLabel).filter(Boolean);
  const where = place
    ? `${place.name}${place.admin1 && place.admin1 !== place.name ? `, ${place.admin1}` : ""}${place.country ? `, ${ccName(place.country)}` : ""}`
    : "";
  const out = [];
  out.push(`${KIND_VERB[KIND(c.kind)] || "A case"} involving ${sp.length ? listOf(sp).toLowerCase() : "wildlife"} was first reported on `
    + `${longDate(c.date)}${where ? `, in ${esc(where)}` : ", with no place named in any report"}.`);
  if (qs.length) out.push(`The reports give the quantity as ${listOf(qs)}.`);
  if (c.people_arrested) {
    out.push(`${count(c.people_arrested)} ${c.people_arrested === 1 ? "person was" : "people were"} reported arrested. `
      + `WildTrace records the number only, never who they are, and an arrest is not a conviction.`);
  }
  if (c.agencies.length) out.push(`${listOf(c.agencies.map(esc))} ${c.agencies.length > 1 ? "are" : "is"} named as acting in the reports.`);
  if (c.modes.length) out.push(`Transport named: ${listOf(c.modes.map(esc))}.`);
  if (c.platforms?.length) out.push(`Platform named in the reports: ${listOf(c.platforms.map(esc))}. WildTrace records the platform, never the seller.`);
  if (c.route?.length === 2) {
    out.push(`The consignment is described as moving from <b>${esc(c.route[0])}</b> to <b>${esc(c.route[1])}</b>, as stated in the reports. `
      + `An origin and destination given by a source are not the same as an established route.`);
  }
  const how = c.verification === "validated" ? "and a reviewer has checked the case against them"
    : c.verification === "official" ? "at least one of them an official government, customs, police or judicial release"
    : c.verification === "corroborated" ? `from ${c.n_outlets || 2} independent outlets`
    : "from a single outlet, so it stands as a lead rather than an established fact";
  out.push(`It is drawn from ${count(c.n_sources).toLowerCase()} report${c.n_sources > 1 ? "s" : ""}, ${how}.`);
  return out;
}

const days = (a, b) => Math.abs((new Date(a) - new Date(b)) / 864e5);
const link = (kind, id, label, sub = "") => `<button class="link-row" data-go="${kind}|${esc(id)}"><span>${label}</span><span class="muted" style="font-size:12px">${sub}</span></button>`;
const caseLink = (c) => link("case", c.id, `<span style="display:inline-flex;gap:8px;align-items:center"><span style="color:${KIND_COLOR[KIND(c.kind)]};display:inline-flex">${ic.kind(c.kind)}</span>${esc(c.summary)}</span>`, esc(c.date || ""));

export function title(item) {
  if (item.kind === "case") return S.data.byId[item.id]?.summary.split(" · ").slice(0, 2).join(" · ") || "Case";
  if (item.kind === "species") return spLabel(item.id);
  if (item.kind === "country") return ccName(item.id);
  if (item.kind === "route") { const [, a, b] = item.id.split("|"); return `${ccName(a)} → ${ccName(b)}`; }
  if (item.kind === "obs") return S.data.obsById[item.id]?.name.split(" (")[0] || "Observatory";
  return item.label || item.id;
}

export function render(item, el, ctx) {
  el.style.setProperty("--c", HUE[item.kind]);
  const fn = { case: caseView, species: speciesView, country: countryView, obs: obsView, entity: entityView, route: (id) => routeView(id, ic) }[item.kind];
  el.innerHTML = fn ? fn(item.id, ctx) : "";
  el.querySelectorAll("[data-go]").forEach((b) => b.addEventListener("click", () => {
    const [kind, id] = b.dataset.go.split("|");
    go({ kind, id });
  }));
  el.querySelectorAll("[data-act]").forEach((b) => b.addEventListener("click", () => ctx.act(b.dataset.act, item)));
  el.querySelectorAll("[data-follow]").forEach((b) => b.addEventListener("click", () => dispatchEvent(new CustomEvent("wildtrace:follow", { detail: b.dataset.follow }))));
  el.querySelectorAll("[data-open-zoo]").forEach((b) => b.addEventListener("click", () => dispatchEvent(new CustomEvent("wildtrace:open", { detail: "zoo" }))));
  el.querySelectorAll("[data-flows-g]").forEach((b) => b.addEventListener("click", () => {
    Object.assign(S.flow, { story: "species" }); S.flow.groups = new Set([b.dataset.flowsG]); S.flow.from.clear(); S.flow.to.clear(); S.flow.off.clear();
    // A group with no CITES seizures (e.g. only US port records) needs the LEMIS layer to show anything.
    if (!S.data.flows?.seized.some((r) => r[0] === b.dataset.flowsG)) S.flow.ev.lemis = true;
    dispatchEvent(new CustomEvent("wildtrace:flows-focus"));
  }));
  el.scrollTop = 0;
}

// ------------------------------------------------------------------ case
function caseView(id) {
  const c = S.data.byId[id];
  if (!c) return `<p class="muted">This case is not in the current build.</p>`;
  const place = c.place;
  const precision = !place ? "No place is named in any report."
    : c.place_basis === "outlet" ? `No report names a place. The point marks the publisher's home region (${esc(place.name)}), a hint only.`
    : place.type === "country" ? `Reports name only the country, so the point sits at the capital as a stand-in.`
    : place.type === "state" ? `Reports name the state or province; the point marks its centre, not the scene.`
    : `Named in the reports: ${esc(place.name)}. The point marks the ${esc(place.type)} centre, not the exact scene.`;
  const related = S.data.cases.filter((o) => o.id !== c.id && o.species.some((s) => c.species.includes(s)) && o.date && c.date && days(o.date, c.date) <= 45)
    .sort((a, b) => days(a.date, c.date) - days(b.date, c.date)).slice(0, 6);
  const sameCountry = place ? S.data.cases.filter((o) => o.place?.country === place.country && o.species.some((s) => c.species.includes(s))).length : 0;
  const qs = [...new Set((c.quantities || (c.quantity ? [c.quantity] : [])).map((q) => `${fmt(q.value)} ${esc(q.unit)}`))];
  // The same figures as the account above, laid out to be scanned or copied rather than read.
  const facts = [
    ["Reported", esc(c.date || "date unknown")],
    ["Event", esc(KIND_LABEL[KIND(c.kind)])],
    ["Species", c.species.map(spLabel).map(esc).join(", ") || "Wildlife, unspecified"],
    ["Place", place ? `${esc(place.name)}${place.admin1 && place.admin1 !== place.name ? `, ${esc(place.admin1)}` : ""}${place.country ? `, ${esc(ccName(place.country))}` : ""}` : "Not named in any report"],
    qs.length ? ["Quantity", qs.join(" · ")] : null,
    c.people_arrested ? ["Arrested", `${c.people_arrested} (count only)`] : null,
    c.agencies.length ? ["Agencies", c.agencies.map(esc).join(", ")] : null,
    c.value_inr ? ["Value as reported", inr(c.value_inr)] : null,
    ["Reports", `${c.n_sources} from ${c.n_outlets || 1} outlet${(c.n_outlets || 1) > 1 ? "s" : ""}`],
  ].filter(Boolean);
  const context = [
    c.route?.length === 2 ? `The reports describe movement from <b>${esc(c.route[0])}</b> to <b>${esc(c.route[1])}</b>. This route is as stated in the reports, not independently established.` : "",
    sameCountry > 1 ? `This is one of ${sameCountry} cases involving the same species group in ${esc(ccName(place.country))} in this dataset.` : "",
    related.length ? `${related.length} other case(s) with the same species group fall within 45 days (listed below).` : "",
    c.modes.length ? `Transport named: ${c.modes.map(esc).join(", ")}.` : "",
  ].filter(Boolean);
  return `
    <div class="eyebrow">${ic.kind(c.kind)} ${esc(KIND_LABEL[KIND(c.kind)])} · ${esc(c.date || "undated")}</div>
    <h2 class="title">${esc(c.summary)}</h2>
    <div class="row" style="margin-bottom:8px"><span class="status ${VER[c.verification]?.[0] || "info"}" title="${esc(VER[c.verification]?.[2] || "")}">${VER[c.verification]?.[1] || ""}</span>
      <span class="muted" style="font-size:12.5px">${esc(VER[c.verification]?.[2] || "")}</span></div>
    ${c.review ? `<div class="box" style="border-left:3px solid var(--species)"><h4>Review</h4>${esc(c.review.note || "")} <span class="muted">(${esc(c.review.reviewer || "")}, ${esc(c.review.date || "")})</span></div>` : ""}
    ${!place ? `<div class="box" style="border-left:3px solid var(--ink-3)"><h4>Not on the map</h4>No report names a place for this case, so it is counted but not drawn. The reports below may say more.</div>` : ""}
    <div class="row">
      ${c.species.map((s) => `<button class="chip" data-go="species|${s}" style="border-color:rgba(33,138,91,.3)">${ic.sp(s)}${esc(spLabel(s))} <span class="muted">CITES ${esc(S.data.species[s]?.cites || "–")}</span></button>`).join("")}
      ${place ? `<button class="chip" data-go="country|${esc(place.country)}">${ic.flag(place.country)}${esc(ccName(place.country))}</button>` : ""}
    </div>
    <div class="account">${narrative(c, place, qs).map((t) => `<p>${t}</p>`).join("")}</div>
    <div class="box"><h4>Documented facts</h4>
      <dl class="facts">${facts.map(([k, v]) => `<dt>${k}</dt><dd>${v}</dd>`).join("")}</dl></div>
    ${context.length ? `<div class="box"><h4>Analytical context</h4>${context.map((f) => `<p style="margin:0 0 6px">${f}</p>`).join("")}</div>` : ""}
    <div class="box limit"><h4>Limits of the evidence</h4>
      <p style="margin:0 0 6px">${precision}</p>
      <p style="margin:0 0 6px">Extracted automatically from ${c.n_sources} public report${c.n_sources > 1 ? "s" : ""}; not reviewed by a person. Confidence ${Math.round(c.confidence * 100)}%.</p>
      <p style="margin:0">CITES appendices shown are group-level; check the taxon on Species+.</p></div>
    <div class="eyebrow" style="margin:18px 0 6px">Reports (${c.n_sources})</div>
    ${c.sources.map((s) => `<a class="link-row" href="${esc(s.url)}" target="_blank" rel="noopener noreferrer nofollow"><span style="display:inline-flex;gap:8px;align-items:center">${ic.outlet(s.outlet)}${esc(s.outlet || new URL(s.url).hostname)} ↗ <span class="status ${s.tier === "official" ? "good" : "info"}" style="margin-left:4px">${TIER[s.tier] || "Media"}</span></span><span class="muted" style="font-size:12px">${esc(s.date || "")}</span></a>`).join("")}
    ${related.length ? `<div class="eyebrow" style="margin:18px 0 6px">Related in time</div>${related.map(caseLink).join("")}` : ""}
    <div class="row" style="margin-top:16px">
      <button class="btn violet" data-act="chart">Chart this case</button>
      <button class="btn" data-act="copy">Copy link</button>
      <a class="btn" href="${correction(c)}" target="_blank" rel="noopener">Report a correction</a>
    </div>
    <p class="muted mono" style="margin-top:10px">Case ID ${esc(c.id)}</p>`;
}

// ------------------------------------------------------------------ species
function speciesView(gid) {
  const g = S.data.species[gid];
  if (!g) return `<p class="muted">Unknown species group.</p>`;
  const cases = S.data.cases.filter((c) => c.species.includes(gid)).sort((a, b) => (b.date || "").localeCompare(a.date || ""));
  const byCountry = {};
  cases.forEach((c) => c.place && (byCountry[c.place.country] = (byCountry[c.place.country] || 0) + 1));
  const online = S.data.trade?.live?.by_group?.[gid], owt = S.data.trade?.by_group?.[gid];
  const terms = Object.entries(g.terms).filter(([k]) => !k.startsWith("pmc_"));
  const pmcN = Object.entries(g.terms).filter(([k]) => k.startsWith("pmc_")).reduce((n, [, v]) => n + v.length, 0);
  return `
    <div class="eyebrow">Species group</div>
    <div class="sp-hero">${ic.sp(gid, g.label)}<h2 class="title">${esc(g.label)}</h2></div>
    ${S.data.speciesIcons?.[gid] ? `<p class="muted" style="font-size:11px;margin:-4px 0 8px">Silhouette: <i>${esc(S.data.speciesIcons[gid].taxon)}</i>${S.data.speciesIcons[gid].attribution ? `, ${esc(S.data.speciesIcons[gid].attribution)}` : ""}, <a href="${esc(S.data.speciesIcons[gid].page)}" target="_blank" rel="noopener">PhyloPic</a></p>` : ""}
    <div class="row"><span class="status ${String(g.cites).startsWith("I") && !String(g.cites).startsWith("II") ? "bad" : "info"}">CITES ${esc(g.cites || "not listed")}</span>
      <span class="muted" style="font-size:12.5px"><i>${esc(g.taxa.join(", "))}</i></span></div>
    <dl class="facts">
      <dt>Traded as</dt><dd>${esc(g.products.join(", "))}</dd>
      ${g.uses?.length ? `<dt>Intended uses</dt><dd>${esc(g.uses.slice(0, 10).join(", "))} <span class="muted">(seizure records, PMC8579131)</span></dd>` : ""}
      <dt>Cases</dt><dd>${cases.length}</dd>
      ${online ? `<dt>Online listings</dt><dd>${online.flagged} flagged as trade this build <span class="muted">(${online.not_flagged} not)</span></dd>` : ""}
      ${owt ? `<dt>OWT labelled set</dt><dd>${owt.R} trade · ${owt.IR} irrelevant</dd>` : ""}
    </dl>
    ${sankey(gid)}${lemisBlock(gid)}${S.data.flows?.seized.some((r) => r[0] === gid) || S.data.lemis?.seized.some((r) => r[0] === gid) ? `<div class="row" style="margin-top:8px"><button class="btn" data-flows-g="${gid}">Follow on the Flows map</button></div>` : ""}
    ${speciesBlock(gid)}
    ${Object.keys(byCountry).length ? `<div class="eyebrow" style="margin:14px 0 6px">Where</div>${Object.entries(byCountry).sort((a, b) => b[1] - a[1]).slice(0, 8)
      .map(([cc, n]) => link("country", cc, `<span style="display:inline-flex;gap:8px;align-items:center">${ic.flag(cc)}${esc(ccName(cc))}</span>`, `${n} case${n > 1 ? "s" : ""}`)).join("")}` : ""}
    <div class="eyebrow" style="margin:14px 0 8px">Names sellers and reporters use</div>
    <div class="terms">${terms.flatMap(([lang, ts]) => ts.slice(0, 5).map((t) => `<span class="term" title="${esc(LANG[lang] || lang)}"><i>${esc(lang.replace("_latn", "·lat").replace("id_ms", "id/ms"))}</i>${esc(t)}</span>`)).join("")}</div>
    ${pmcN ? `<p class="muted" style="font-size:12px;margin-top:8px">Plus ${pmcN} names in other languages from the open seized-wildlife codebook (PMC8579131).</p>` : ""}
    ${cases.length ? `<div class="eyebrow" style="margin:16px 0 6px">Cases</div>${cases.slice(0, 12).map(caseLink).join("")}` : ""}
    <div class="row" style="margin-top:14px"><button class="btn" data-act="filter-species">Show only this group on the map</button></div>`;
}

// ------------------------------------------------------------------ country
function countryView(cc) {
  const cases = S.data.cases.filter((c) => c.place?.country === cc).sort((a, b) => (b.date || "").localeCompare(a.date || ""));
  const sp = {};
  cases.forEach((c) => c.species.forEach((s) => (sp[s] = (sp[s] || 0) + 1)));
  const obs = (S.data.obs.observatories || []).filter((o) => o.hq && nearCountry(o, cc));
  const outRoutes = S.data.cases.filter((c) => c.route?.length === 2 && c.route_coords && (c.place?.country === cc));
  return `
    <div class="eyebrow">Country</div>
    <div class="sp-hero">${ic.flag(cc).replace('class="flag"', 'class="flag xl"')}<h2 class="title">${esc(ccName(cc))}</h2></div>
    <div class="tiles"><div class="tile"><div class="v">${cases.length}</div><div class="k">cases</div></div>
      <div class="tile"><div class="v">${Object.keys(sp).length}</div><div class="k">species groups</div></div></div>
    ${roleBar(cc)}${countryBlock(cc)}
    ${Object.keys(sp).length ? `<div class="eyebrow" style="margin:14px 0 6px">Species involved</div>${Object.entries(sp).sort((a, b) => b[1] - a[1])
      .map(([s, n]) => link("species", s, `<span style="display:inline-flex;gap:8px;align-items:center">${ic.sp(s)}${esc(spLabel(s))}</span>`, `${n}`)).join("")}` : ""}
    ${outRoutes.length ? `<div class="eyebrow" style="margin:14px 0 6px">Reported routes</div>${outRoutes.map((c) => link("case", c.id, `${esc(c.route[0])} → ${esc(c.route[1])}`, esc(c.date || ""))).join("")}` : ""}
    ${obs.length ? `<div class="eyebrow" style="margin:14px 0 6px">Observatories based here</div>${obs.map((o) => link("obs", o.id, esc(o.name.split(" (")[0]), esc(o.hq.city))).join("")}` : ""}
    ${cases.length ? `<div class="eyebrow" style="margin:14px 0 6px">Cases</div>${cases.slice(0, 15).map(caseLink).join("")}` : `<p class="muted">No cases located here in this build.</p>`}
    <div class="row" style="margin-top:14px"><button class="btn" data-act="filter-country">Show only this country on the map</button></div>`;
}
const HQ_CC = { "Rio de Janeiro": "BR", "Cambridge, UK": "GB", "London": "GB", "Washington, DC": "US", "New York": "US", "Los Angeles": "US", "Falls Church, VA": "US",
  "Vienna": "AT", "Geneva": "CH", "Zurich": "CH", "Helsinki": "FI", "Bengaluru": "IN", "New Delhi": "IN", "Adelaide": "AU", "Sydney": "AU", "Copenhagen": "DK",
  "Johannesburg": "ZA", "The Hague": "NL", "Bangkok": "TH", "Hanoi": "VN" };
const nearCountry = (o, cc) => HQ_CC[o.hq.city] === cc;

// ------------------------------------------------------------------ observatory
const STATE = { active: ["good", "● Active"], prototype: ["warn", "◐ Prototype"], restricted: ["info", "◌ Restricted"], "bot-blocked": ["info", "◌ Browser only"],
  offline: ["bad", "✕ Offline"], unverified: ["warn", "? Unverified"] };
function obsView(id) {
  const o = S.data.obsById[id];
  if (!o) return `<p class="muted">Unknown observatory.</p>`;
  const [cls, lab] = STATE[o.status.state] || ["info", o.status.state];
  return `
    <div class="eyebrow">Observatory · ${esc(S.data.obs.categories?.[o.category] || o.category)}</div>
    <div class="sp-hero">${ic.org(o.id, o.name)}<h2 class="title">${esc(o.name)}</h2></div>
    <div class="row"><span class="status ${cls}">${lab}</span><span class="muted" style="font-size:12.5px">checked ${esc(String(o.status.checked))}</span></div>
    <dl class="facts">
      <dt>Run by</dt><dd>${esc(o.entity)}</dd>
      <dt>Focus</dt><dd>${esc(o.focus)}</dd>
      ${o.hq ? `<dt>Based in</dt><dd>${esc(o.hq.city)}</dd>` : ""}
      <dt>What it does</dt><dd>${esc(o.features)}</dd>
      <dt>Access</dt><dd>${esc(o.access)}</dd>
      ${o.languages?.length ? `<dt>Languages</dt><dd>${esc(o.languages.join(", "))}</dd>` : ""}
    </dl>
    ${o.global_south ? `<div class="box"><h4>Global South relevance</h4>${esc(o.global_south)}</div>` : ""}
    <div class="box" style="border-left:3px solid var(--network)"><h4>How WildTrace uses it</h4>${esc(o.wildtrace.how)}</div>
    ${o.status.note ? `<div class="box limit"><h4>Check note</h4>${esc(o.status.note)}</div>` : ""}
    <div class="row" style="margin-top:12px">${o.url ? `<a class="btn primary" href="${esc(o.url)}" target="_blank" rel="noopener noreferrer">Open ${esc(o.name.split(" (")[0].split(" ·")[0])} ↗</a>` : ""}
      <button class="btn" data-act="network">All observatories</button></div>
    <p class="muted" style="font-size:12px;margin-top:10px">Listed via ${esc((o.provenance || []).join(", "))}.</p>`;
}

// ------------------------------------------------------------------ your entity (local data)
function entityView(id, ctx) {
  const n = ctx.entity?.(id);
  if (!n) return `<p class="muted">This entity is in your local data. Open Investigate to see it.</p>`;
  return `
    <div class="eyebrow">Your data · ${esc(n.type)}</div>
    <h2 class="title">${esc(n.label)}</h2>
    <div class="note">Stored only in this browser. WildTrace never uploads it.</div>
    <dl class="facts">${Object.entries(n).filter(([k, v]) => !["id", "label", "type", "local"].includes(k) && v !== "" && v != null)
      .map(([k, v]) => `<dt>${esc(k)}</dt><dd>${esc(v)}</dd>`).join("")}</dl>
    <div class="row"><button class="btn violet" data-act="chart-entity">Show in chart</button></div>`;
}
