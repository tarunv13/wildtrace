// Network and Methods sheets. They slide up over the map; the map stays live above them.
import { esc, fmt } from "./charts.js";
import { S, go } from "./store.js";
import * as ic from "./icons.js";

const STATE = { active: ["good", "● Active"], prototype: ["warn", "◐ Prototype"], restricted: ["info", "◌ Restricted"], "bot-blocked": ["info", "◌ Browser only"],
  offline: ["bad", "✕ Offline"], unverified: ["warn", "? Unverified"] };
const CAT = { intelligence: "Intelligence", digital: "Online trade", legal: "Courts & law", trade: "Trade statistics", reference: "Reference data",
  tools: "Tools", crowd: "Public reporting", journalism: "Journalism", funding: "Funding" };

export function mountNetwork(root) {
  const obs = S.data.obs.observatories || [];
  let cat = "";
  const draw = () => {
    const list = obs.filter((o) => !cat || o.category === cat);
    root.innerHTML = `
      <div class="filters">
        <button class="chip" aria-pressed="${!cat}" data-cat="">All ${obs.length}</button>
        ${Object.keys(S.data.obs.categories || {}).map((k) => `<button class="chip" aria-pressed="${cat === k}" data-cat="${k}">${esc(CAT[k] || k)} <span class="muted">${obs.filter((o) => o.category === k).length}</span></button>`).join("")}
        <span style="flex:1"></span><span class="muted" style="font-size:12.5px">Every entry re-checked 22 Sep 2026 · corrections shown on each card</span>
      </div>
      <div class="dir">${list.map((o) => { const [c, l] = STATE[o.status.state] || ["info", o.status.state];
        return `<article class="obs" data-obs="${esc(o.id)}" tabindex="0" role="button" aria-label="${esc(o.name)}">
          <div class="row" style="justify-content:space-between;align-items:start;flex-wrap:nowrap"><h4 style="display:flex;gap:8px;align-items:center">${ic.org(o.id, o.name)}${esc(o.name.split(" (")[0])}</h4><span class="status ${c}">${l}</span></div>
          <div class="muted" style="font-size:12.5px">${esc(o.entity)}${o.hq ? ` · ${esc(o.hq.city)}` : ""}</div>
          <div>${esc(o.features)}</div>
          <div class="use"><b>In WildTrace:</b> ${esc(o.wildtrace.how)}</div>
        </article>`; }).join("")}</div>
      <div class="prose" style="max-width:none">
        <h3>What the network taught this project</h3>
        <div class="dir" style="padding:0">${[
          ["Open code, closed operations", "Software, methods and aggregates are public. Names, informants and patrol data are not.", "SMART, NGO data sharing"],
          ["A machine ranks, a person decides", "Classifiers sort the flood; people confirm. Hence the review queue and relabel loop.", "ECO-SOLVE, WILDTRADE"],
          ["Follow the logistics", "Transport mode, airport and route say more than a species list.", "C4ADS, ROUTES"],
          ["Follow the case to court", "A seizure is where a case starts. Arrest, charge and conviction are the outcome.", "#WildEye, SHERLOC"],
          ["Bridge source and demand", "Local names map to species and species to end uses, so source and demand markets meet in one chart.", "PMC8579131, EIA, Operation Jaguar"],
          ["Verify before you trust", "Several AI-supplied links and claims were wrong; unverified codewords only flag items for review.", "building this registry"],
        ].map(([t, b, f]) => `<div class="obs" style="cursor:default"><h4>${t}</h4><div>${b}</div><div class="muted" style="font-size:12px">From ${f}</div></div>`).join("")}</div>
      </div>`;
    root.querySelectorAll("[data-cat]").forEach((b) => b.addEventListener("click", () => { cat = b.dataset.cat; draw(); }));
    root.querySelectorAll("[data-obs]").forEach((b) => {
      const open = () => go({ kind: "obs", id: b.dataset.obs });
      b.addEventListener("click", open);
      b.addEventListener("keydown", (e) => (e.key === "Enter" || e.key === " ") && (e.preventDefault(), open()));
    });
  };
  draw();
}

export function mountMethods(root, tab = "pipeline") {
  const m = S.data.report || {}, t = m.test || {}, meta = S.data.meta || {};
  const pct = (v) => (v == null ? "–" : `${(v * 100).toFixed(1)}%`);
  const sections = {
    pipeline: `<div class="prose">
      <h3 style="margin-top:0">How a news report becomes a case</h3>
      <p><b>Collect.</b> Open news from GDELT and Google News (23 editions, 8 languages), plus YouTube listings collected locally. This build screened ${fmt(meta.records_seen)} records.</p>
      <p><b>Screen.</b> A multilingual lexicon of 30 species groups (English, Hindi, Telugu, Portuguese, Spanish, French, Vietnamese, Thai, Indonesian, plus 2,376 codebook names in 66 languages) meets enforcement words in the same languages. Films, liquor brands and look-alike places are filtered out.</p>
      <p><b>Extract.</b> Species, place (46,000 places, Hindi and native-script names included), route, quantities, arrests (a count, never a name), agencies and transport, each traceable to a phrase.</p>
      <p><b>Merge.</b> Reports of one incident become one case, across languages and across the days a story runs.</p>
      <p><b>Link and publish.</b> Cases become a graph of species, places, agencies and outlets. A privacy gate blocks names, phones and handles before anything is published.</p>
      <h3>Flows: supply, transit and demand</h3>
      <p>News reports rarely name both ends of a route, so the Flows view draws on the <b>CITES Trade Database</b> (UNEP-WCMC for the CITES Secretariat, full download ${esc(S.data.flows?.version || "2026.1")}).
        Every shipment since ${esc(String(S.data.flows?.year_min || 2015))} is matched to a WildTrace species group by species, genus, family, order or class. Shipments with source code I (confiscated or seized) become the seized layer, drawn from the country of origin to the country that seized them; all other shipments form the declared, mostly legal, layer. Only counts are published, never shipments or permit identifiers.</p>
      <p>A country's role (source, transit hub or market) is whichever of the three counts is largest: taken from there, re-exported through there, or seized arriving there. Reporting to CITES is uneven, and the United States reports its seizures more completely than most, so it can look like a bigger market than it is. Regions follow the UN M49 sub-regions, grouped into eight.</p>
      <p>Species groups are matched on the taxa they list and, for trade records only, on the wider ranks their names imply (turtles = Testudines, bears = Ursidae, monitor lizards = <i>Varanus</i>, crocodilian skins with pythons). News matching keeps the narrower lists, which protect precision.</p>
      <h3>Seized at US ports</h3>
      <p>A second, independent seizure layer comes from the US Fish and Wildlife Service's <b>LEMIS</b> import records, released under the Freedom of Information Act and cleaned by Marshall et al. (2025, <i>Current Biology</i>; 2000–2022, land vertebrates and arachnids) and Eskew et al. (2020, <i>Scientific Data</i>; 2000–2014, used only for fish, invertebrates and plants). Only records with disposition S (seized) are kept; genera are placed in families with the GBIF key of the seized-wildlife codebook (Stringham et al. 2021). Both sources are CC BY 4.0.</p>
      <p>Read it with three limits. A LEMIS seizure can follow missing or wrong paperwork as well as smuggling. It shows what US inspectors intercepted, so it measures US enforcement effort as much as trade. And the United States also reports seizures to CITES, so on routes into the US the two layers overlap: compare them, never add them. US-bound routes already make up about four in five CITES seizure records here, which is why "Spread across markets" is on by default.</p>
      <p>How these layers add up to an environment-to-security pathway, and where the open evidence stops, is set out in <a href="pathways.html">Risk pathways</a>.</p>
      <h3>Zoonoses</h3>
      <p><b>VIRION</b> (Carlson et al. 2022) gives the viruses recorded in each species group; only detections by sequencing or isolation count. A close relative is a virus in a genus that also infects people. <b>WHO Disease Outbreak News</b> gives the outbreak reports: diseases with an animal reservoir are grouped by how they reach people, and each report is placed in every country its title names.
        The two layers share a map, not a cause, and both follow research and reporting effort.</p></div>`,
    model: `<div class="prose">
      <h3 style="margin-top:0">The online-listing classifier</h3>
      <p>${esc(m.task || "")}. Trained on ${fmt(m.n)} items from the OWT labelled set (${fmt(m.n_R)} trade / ${fmt(m.n_IR)} irrelevant). ${esc(m.protocol || "")}.</p>
      <table style="max-width:560px"><tbody>
        <tr><td>Trade listings kept (target ${pct(m.target_recall)})</td><td class="num"><b>${pct(t.recall_R)}</b></td></tr>
        <tr><td>Irrelevant listings rejected</td><td class="num"><b>${pct(t.recall_IR)}</b></td></tr>
        <tr><td>Precision on trade</td><td class="num">${pct(t.precision_R)}</td></tr>
        <tr><td>ROC-AUC</td><td class="num">${t.roc_auc ?? "–"}</td></tr></tbody></table>
      <p>Scored once on a test set split by seller channel, so a seller's videos never appear on both sides. The learning curve has flattened (${esc(m.saturation || "")}); contradictory labels, not the model, set the ceiling.</p></div>`,
    privacy: `<div class="prose">
      <h3 style="margin-top:0">What WildTrace will not publish</h3>
      <p><b>People.</b> Accused persons are presumed innocent. Case summaries are built from extracted facts, never copied headlines, and arrests are counts.</p>
      <p><b>Contacts.</b> Phone numbers, e-mails, messenger links and handles are removed; the build fails if any remain.</p>
      <p><b>Sellers.</b> Channel names are only used to keep one seller's listings on one side of the test split.</p>
      <p><b>You.</b> No accounts. Data you import into Investigate stays in your browser and is never uploaded.
      Usage is measured with <a href="https://clarity.microsoft.com" target="_blank" rel="noopener">Microsoft Clarity</a>,
      which records clicks, scrolling and session replays and sets cookies. Your search text and anything you import
      are masked and never reach a replay, advertising storage is denied, and nothing loads at all if your browser
      sends a Global Privacy Control signal.</p>
      <p><b>Map tiles.</b> The map comes from OpenFreeMap. Satellite imagery (EOxCloudless, from Copernicus Sentinel-2) loads from EOX's servers only if you switch satellite view on.</p>
      <p><b>Sources.</b> robots.txt is respected, which is why Google News links are not decoded; locations come from the reports themselves.</p></div>`,
    sources: `<div style="padding:16px"><table><thead><tr><th>Source</th><th>Access</th><th>Status</th><th>Notes</th></tr></thead><tbody>
      ${(S.data.sources || []).map((s) => `<tr><td>${s.url ? `<a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.name)}</a>` : esc(s.name)}</td><td>${esc(s.access)}</td>
        <td><span class="status ${s.enabled ? "good" : "info"}">${s.enabled ? "on" : "off"}</span></td><td class="muted" style="white-space:normal">${esc(s.notes || s.terms || "")}</td></tr>`).join("")}</tbody></table></div>`,
  };
  root.innerHTML = sections[tab] || sections.pipeline;
}

// ------------------------------------------------------------------ all cases (text alternative to the map)
const VER_LABEL = { validated: "Validated", official: "Official source", corroborated: "Corroborated", single: "Single report" };
export function mountTable(root) {
  const cases = S.data.cases;
  let key = "date", dir = -1, q = "";
  const cols = [["date", "Date"], ["summary", "Case"], ["verification", "Evidence"], ["country", "Country"], ["n_sources", "Reports"]];
  const val = (c, k) => (k === "country" ? (c.place ? S.data.countries[c.place.country]?.name || c.place.country : "") : c[k] ?? "");
  const draw = () => {
    const rows = cases.filter((c) => !q || JSON.stringify([c.summary, c.places, c.agencies, c.species]).toLowerCase().includes(q))
      .sort((a, b) => { const x = val(a, key), y = val(b, key); return (x > y ? 1 : x < y ? -1 : 0) * dir; });
    root.innerHTML = `<div class="filters">
        <input type="search" id="t-q" placeholder="Filter cases…" aria-label="Filter cases" value="${esc(q)}" style="min-width:240px">
        <span class="muted" style="font-size:12.5px">${rows.length} of ${cases.length} cases · ${cases.filter((c) => !c.place).length} have no mappable place</span>
        <span style="flex:1"></span>
        <a class="btn" href="data/cases.csv" download>Download CSV</a>
      </div>
      <div style="padding:10px 16px 18px;overflow:auto">
      <table aria-label="All cases"><thead><tr>${cols.map(([k, l]) => `<th scope="col" aria-sort="${key === k ? (dir > 0 ? "ascending" : "descending") : "none"}">
        <button class="sort" data-k="${k}">${l}${key === k ? (dir > 0 ? " ↑" : " ↓") : ""}</button></th>`).join("")}</tr></thead>
      <tbody>${rows.map((c) => `<tr><td class="num">${esc(c.date || "")}</td>
        <td><button class="linkish" data-case="${c.id}">${esc(c.summary)}</button></td>
        <td><span class="status ${c.verification === "single" ? "info" : "good"}">${esc(VER_LABEL[c.verification] || "")}</span></td>
        <td>${esc(val(c, "country")) || '<span class="muted">not mapped</span>'}</td><td class="num">${c.n_sources}</td></tr>`).join("")}</tbody></table></div>`;
    root.querySelector("#t-q").addEventListener("input", (e) => { q = e.target.value.toLowerCase(); const pos = e.target.selectionStart; draw(); const i = root.querySelector("#t-q"); i.focus(); i.setSelectionRange(pos, pos); });
    root.querySelectorAll(".sort").forEach((b) => b.addEventListener("click", () => { dir = key === b.dataset.k ? -dir : 1; key = b.dataset.k; draw(); root.querySelector(`.sort[data-k="${key}"]`)?.focus(); }));
    root.querySelectorAll("[data-case]").forEach((b) => b.addEventListener("click", () => go({ kind: "case", id: b.dataset.case })));
  };
  draw();
}

// ------------------------------------------------------------------ about
export function mountAbout(root) {
  const m = S.data.meta || {};
  const v = m.verification || {}, cov = m.coverage || {};
  setTimeout(() => root.querySelector("#about-video")?.addEventListener("click", () => dispatchEvent(new CustomEvent("wildtrace:video"))), 0);
  root.innerHTML = `<div class="prose" style="max-width:80ch">
    <h3 style="margin-top:0">The open atlas of illegal wildlife trade</h3>
    <p>WildTrace maps seizures, arrests and convictions involving wild fauna and flora, from ivory and pangolins to rosewood and agarwood. Every case links back to its public sources and states how strong its evidence is. The link-analysis workbench runs on your own data in your browser.</p>
    <h3>How reliable is a case?</h3>
    <p><b>Validated</b> (${v.validated || 0}): checked by a person against its sources. <b>Official source</b> (${v.official || 0}): at least one government, customs, police or judicial release. <b>Corroborated</b> (${v.corroborated || 0}): two or more independent outlets. <b>Single report</b> (${v.single || 0}): one outlet; treat as a lead.</p>
    <p>${cov.mapped || 0} cases have a city- or district-level place, ${cov.country_only || 0} only a country, and ${cov.unmapped || 0} none. Coverage follows the newsrooms and government sites searched, so counts show where wildlife crime is <i>reported</i>, not where it happens.</p>
    <p><button class="btn" id="about-video">▶ Watch the 2-minute video guide</button></p>
    <h3>Why it matters beyond conservation</h3>
    <p>Wildlife crime reaches national security through crime revenue, disease risk and the loss of ecosystems people depend on. <a href="pathways.html">Risk pathways</a> maps seven links from nature to security, rates the open evidence for each, and says where it runs out, with a commitment to security without militarisation.</p>
    <h3>Who runs it</h3>
    <p>An open-source research project, maintained on GitHub by <a href="https://github.com/tarunv13" target="_blank" rel="noopener">@tarunv13</a>. It builds on the OWT labelled set of online listings and on the observatories listed under Network. Code and method: <a href="https://github.com/tarunv13/wildtrace" target="_blank" rel="noopener">github.com/tarunv13/wildtrace</a>.</p>
    <h3>Use and cite</h3>
    <p>Case data: <b>CC BY 4.0</b>. Code: MIT. The Flows data (<code>flows.json</code>) is derived from the CITES Trade Database and shared under its terms (non-commercial, with attribution); the virus counts in <code>zoonoses.json</code> come from VIRION under <b>ODbL 1.0</b>. Suggested citation:</p>
    <p class="box mono" style="font-size:12.5px">${esc(m.cite || "WildTrace. The open atlas of illegal wildlife trade.")}</p>
    <div class="row"><a class="btn primary" href="data/cases.csv" download>Download all cases (CSV)</a>
      <a class="btn" href="browse.html">Browse by species &amp; country</a></div>
    <h3>More open data</h3>
    <div class="row"><a class="btn" href="data/cites_seized_flows.csv" download>Seized-shipment flows (CSV)</a>
      <a class="btn" href="data/lemis_seized_flows.csv" download>US port seizures (CSV)</a>
      <a class="btn" href="data/cites_declared_flows.csv" download>Declared-trade flows (CSV)</a>
      <a class="btn" href="data/zoonotic_outbreak_reports.csv" download>Zoonotic outbreak reports (CSV)</a>
      <a class="btn" href="data/species_viruses.csv" download>Viruses by species group (CSV, ODbL)</a>
      <a class="btn" href="https://github.com/tarunv13/wildtrace/issues/new?title=Correction%3A%20&labels=correction" target="_blank" rel="noopener">Report a correction</a></div>
    <p class="muted" style="font-size:12.5px">Every species group, country and case also has a plain page of its own,
      readable without JavaScript and linked from <a href="browse.html">the index</a>.</p>
    <h3>Icons and logos</h3>
    <p class="muted" style="font-size:12.5px">Species silhouettes from <a href="https://www.phylopic.org" target="_blank" rel="noopener">PhyloPic</a> (public domain, CC0 or CC BY; each credited on its species page). Interface icons: <a href="https://tabler.io/icons" target="_blank" rel="noopener">Tabler Icons</a> (MIT). Flags: <a href="https://flagicons.lipis.dev" target="_blank" rel="noopener">flag-icons</a> (MIT). Satellite view: <a href="https://cloudless.eox.at" target="_blank" rel="noopener">EOxCloudless 2024</a> by EOX IT Services GmbH, contains modified Copernicus Sentinel data 2024 (CC BY-NC-SA 4.0). Outlet and organisation logos are their own site icons, shown only to identify a source; they imply no endorsement and are served from this site, so your browser never contacts a third party for them.</p>
    <p class="muted" style="font-size:12.5px;margin-top:12px">Last updated ${esc(m.built || "")}. Refreshed weekly. Usage measured with Microsoft Clarity; no accounts.</p>
  </div>`;
}
