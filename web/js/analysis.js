// Analysis: what the evidence shows, in one sheet. Every chart names what it counts and what it
// cannot show (news coverage is not trafficking volume; CITES reporting is uneven).
import { columns, esc, fmt, hbars } from "./charts.js";
import { S, spLabel } from "./store.js";
import { ROLE, roles } from "./flows.js";
import { flag } from "./icons.js";

export function mountAnalysis(root) {
  const cs = S.data.cases, st = S.data.stats || {}, k = st.kpi || {};
  const tile = (v, l, c) => `<div class="tile a"><div class="v">${v}</div><div class="k"><span class="dotc" style="background:${c}"></span>${l}</div></div>`;
  const bm = st.by_month || {};
  const f = S.data.flows, R = roles();
  const bal = ["US", "HK", "CN", "AU", "TH", "MX", "ZA", "IN", "ID", "VN"].filter((c) => R[c]).map((c) => {
    const s = R[c].supply, d = R[c].demand, t = s + d || 1;
    return `<div class="bal"><span>${flag(c)}${esc(S.data.countries[c]?.name || c)}</span>
      <div class="l"><i style="width:${(s / t) * 100}%;background:${ROLE.supply[1]}" title="Taken from here: ${fmt(s)}"></i></div>
      <div class="r"><i style="width:${(d / t) * 100}%;background:${ROLE.demand[1]}" title="Seized arriving: ${fmt(d)}"></i></div>
      <span class="mono muted">${fmt(s + d)}</span></div>`;
  }).join("");
  root.innerHTML = `<div class="an">
    <a class="an-path" href="pathways.html"><b>From evidence to security.</b> Seven links from nature to national security, each rated by its open evidence →</a>
    <div class="an-tiles">
      ${tile(fmt(k.cases), "cases, merged from news reports", "var(--cases)")}
      ${tile(fmt(k.sources), "source reports read", "var(--network)")}
      ${tile(fmt(k.countries), "countries with a case", "var(--place)")}
      ${tile(fmt(k.people_arrested), "people reported arrested (a count, no names)", "#eb6834")}
      ${tile(fmt(k.appendix_I_cases), "cases involve CITES Appendix I species", "var(--species)")}
    </div>
    <div class="an-grid">
      <section class="card wide"><h3>Cases per month</h3><p class="muted">News coverage, not trafficking volume: collection widened over time (see Methods), so read a rise with care.</p><div id="an-month"></div></section>
      <section class="card"><h3>What happened</h3><p class="muted">Main event in each case</p><div id="an-kind"></div></section>
      <section class="card"><h3>Species in the news</h3><p class="muted">Cases per species group</p><div id="an-sp"></div></section>
      <section class="card"><h3>Source or market?</h3><p class="muted">Seized shipments taken from each country versus seized arriving there (CITES since ${f?.year_min || ""})</p>
        <div class="bal hd"><span></span><b style="color:var(--species-ink)">← Taken from here</b><b style="color:var(--trade-ink);text-align:left">Seized arriving →</b><span></span></div>${bal || `<p class="muted">Loading CITES data…</p>`}</section>
      <section class="card"><h3>How it moved</h3><p class="muted">Transport stated in ${fmt(Object.values(st.by_mode || {}).reduce((a, b) => a + b, 0))} of ${fmt(k.cases)} cases; most reports never say</p><div id="an-mode"></div></section>
      <section class="card"><h3>Caught online</h3><p class="muted">${fmt(st.online?.cases || 0)} cases where the trade was online; the platforms named in their headlines are below. Adverts are watched by others (ECO-SOLVE, WILDTRADE); this is where online trade met enforcement.</p><div id="an-plat"></div></section>
      <section class="card"><h3>What was sold online</h3><p class="muted">Species groups in online-trade cases</p><div id="an-onsp"></div></section>
      <section class="card wide"><h3>Offered online, rarely caught</h3><p class="muted">Adverts recorded by ECO-SOLVE's regional hubs against WildTrace enforcement cases for the same species and country, in the same period. Different sources with different effort: not a detection rate, but a map of where open selling meets little public enforcement.</p><div id="an-gap">${S.data.online_gap ? "" : `<p class="muted">Loading…</p>`}</div></section>
      <section class="card wide"><h3>Captive-bred claims: where to ask questions</h3><p class="muted">Commercial CITES exports declared bred in captivity, early years against recent ones. Declaring wild-caught animals as captive-bred is a documented laundering route (Lyons &amp; Natusch 2011), but genuine breeding, ranching and coral farming produce the same rise. A question to ask, never a finding.</p><div id="an-cap">${S.data.captive_claims ? "" : `<p class="muted">Loading…</p>`}</div></section>
      <section class="card wide"><h3>Seized shipments reported to CITES, per year</h3><p class="muted">All WildTrace species groups. The latest year is still being reported by countries.</p><div id="an-cites"></div></section>
    </div>
    <p class="muted" style="font-size:12px;margin:4px 0 0">Cases: CC BY 4.0, <a href="data/cases.csv" download>download CSV</a>. ${f ? esc(f.cite) : ""}</p></div>`;
  columns(root.querySelector("#an-month"), Object.entries(bm).map(([m, v]) => ({ label: m, value: v })), { color: "var(--cases)", height: 180 });
  hbars(root.querySelector("#an-kind"), Object.entries(st.by_kind || {}).map(([l, v]) => ({ label: l[0].toUpperCase() + l.slice(1), value: v, note: "cases" })), { color: "var(--cases)" });
  hbars(root.querySelector("#an-sp"), Object.entries(st.by_species || {}).map(([g, v]) => ({ label: g === "wildlife_general" ? "Species not named" : spLabel(g), value: v, note: "cases" })), { color: "var(--species)", max: 10 });
  hbars(root.querySelector("#an-plat"), Object.entries(st.by_platform || {}).map(([l, v]) => ({ label: l, value: v, note: "cases" })), { color: "var(--network)", max: 10 });
  hbars(root.querySelector("#an-onsp"), Object.entries(st.online?.by_species || {}).map(([g, v]) => ({ label: g === "wildlife_general" ? "Species not named" : spLabel(g), value: v, note: "cases" })), { color: "var(--species)", max: 8 });
  hbars(root.querySelector("#an-mode"), Object.entries(st.by_mode || {}).map(([l, v]) => ({ label: l[0].toUpperCase() + l.slice(1), value: v, note: "cases" })), { color: "var(--place)" });
  const gap = S.data.online_gap;
  if (gap) {
    const rows = gap.pairs.filter((p) => p.adverts >= 50).sort((a, b) => b.adverts / (b.cases + 1) - a.adverts / (a.cases + 1)).slice(0, 10);
    root.querySelector("#an-gap").innerHTML = `<table class="tbl"><thead><tr><th>Country</th><th>Group</th><th class="num">Adverts (ECO-SOLVE)</th><th class="num">Cases (WildTrace)</th></tr></thead><tbody>${rows.map((p) =>
      `<tr><td>${flag(p.country)}${esc(S.data.countries[p.country]?.name || p.country)}</td><td>${esc(spLabel(p.group))}</td><td class="num">${fmt(p.adverts)}</td><td class="num"><b>${fmt(p.cases)}</b></td></tr>`).join("")}</tbody></table>
      <p class="muted" style="font-size:12px;margin:6px 0 0">${fmt(gap.adverts)} adverts, ${esc(gap.window.join(" to "))}, ${gap.hubs.length} hubs. Offered online but in no WildTrace group yet: ${esc(gap.not_tracked.slice(0, 6).map(([n, v]) => `${n} (${fmt(v)})`).join(", "))}. Source: ${esc(gap.source)}. <a href="data/online_gap.csv" download>Download (CSV)</a>.</p>`;
  }
  const cap = S.data.captive_claims;
  if (cap) {
    const top = cap.rows.filter((r) => r.shift !== null && r.records >= 50).slice(0, 8);
    const pct = (v) => (v == null ? "–" : `${Math.round(v * 100)}%`);
    root.querySelector("#an-cap").innerHTML = `<table class="tbl"><thead><tr><th>Exporter</th><th>Group</th><th class="num">${cap.early.join("–")}</th><th class="num">${cap.late.join("–")}</th><th class="num">Records</th><th>Declared captive-bred most often</th></tr></thead><tbody>${top.map((r) =>
      `<tr><td>${flag(r.exporter)}${esc(S.data.countries[r.exporter]?.name || r.exporter)}</td><td>${esc(spLabel(r.group))}</td><td class="num">${pct(r.early_share)}</td><td class="num"><b>${pct(r.late_share)}</b></td><td class="num">${fmt(r.records)}</td><td><i>${esc(r.top_captive_taxa.join(", "))}</i></td></tr>`).join("")}</tbody></table>
      <p class="muted" style="font-size:12px;margin:6px 0 0">Share of commercial records declared captive-bred (source C, F or D). ${esc(cap.licence)} <a href="data/captive_claims.csv" download>Download all ${fmt(cap.rows.length)} exporter-group pairs (CSV)</a>.</p>`;
  }
  if (f) {
    const y = {}; f.seized_years.forEach(([, yr, n]) => (y[yr] = (y[yr] || 0) + n));
    columns(root.querySelector("#an-cites"), Object.entries(y).map(([yr, v]) => ({ label: yr, value: v })), { color: "var(--trade)", height: 150, unit: "seized shipments" });
  }
}
