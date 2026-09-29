// Pulse: the always-on summary of what is on the map. Every bar is also a filter,
// so reading and exploring are the same gesture.
import { esc, fmt } from "./charts.js";
import { KIND, KIND_COLOR, KIND_LABEL } from "./globe.js";
import { S, ccName, clearFilters, emit, filtered, go, spLabel, toggle, verBucket } from "./store.js";
import * as ic from "./icons.js";
const VERB = { strong: ["Official or validated", "var(--species)"], corroborated: ["Corroborated", "var(--place)"], single: ["Single report", "var(--ink-3)"] };

function bars(entries, facet, color, max = 8, icon = null) {
  const top = Math.max(1, ...entries.map((e) => e[1]));
  return entries.slice(0, max).map(([k, n, label]) => `<button class="bar" data-f="${facet}" data-v="${esc(k)}" aria-pressed="${S.filters[facet].has(k)}"
      style="--c:${color};--w:${Math.max(4, (n / top) * 100)}%"><i class="fill"></i><span>${icon ? icon(k) : ""}${esc(label)}</span><b class="n">${fmt(n)}</b></button>`).join("");
}

export function renderPulse(el) {
  const cs = filtered();
  const countries = new Set(cs.map((c) => c.place?.country).filter(Boolean));
  const sp = {}, cc = {}, kinds = {};
  filtered("species").forEach((c) => c.species.forEach((s) => (sp[s] = (sp[s] || 0) + 1)));
  filtered("countries").forEach((c) => c.place && (cc[c.place.country] = (cc[c.place.country] || 0) + 1));
  filtered("kinds").forEach((c) => (kinds[KIND(c.kind)] = (kinds[KIND(c.kind)] || 0) + 1));
  const f = S.filters, any = f.kinds.size || f.species.size || f.countries.size || f.ver.size || f.range;
  const mapped = cs.filter((c) => c.place && c.place.type !== "country").length;
  const vers = {};
  filtered("ver").forEach((c) => (vers[verBucket(c)] = (vers[verBucket(c)] || 0) + 1));
  const reports = cs.reduce((n, c) => n + c.n_sources, 0);
  const latest = [...cs].sort((a, b) => (b.date || "").localeCompare(a.date || "")).slice(0, 12);
  const m = S.data.meta || {};
  const A = S.data.answers?.answers || [];
  const persona = S.persona || "everyone";
  const qs = A.filter((a) => persona === "all" || a.personas.includes(persona)).slice(0, 6);
  const ask = any || !A.length ? "" : `
    <section class="ask" aria-labelledby="ask-h">
      <h1 class="headline" id="ask-h">What do you want to know?</h1>
      <p class="lede">Questions this atlas answers from ${fmt(reports)} public reports and three government trade records, each with its sources and its limits.</p>
      <div class="seg ask-for" role="group" aria-label="Answers for">${[["everyone", "Everyone"], ["journalists", "Journalists"], ["researchers", "Researchers"], ["policy", "Policy"]].map(([k, l]) =>
        `<button type="button" data-persona="${k}" aria-pressed="${k === persona}">${l}</button>`).join("")}</div>
      <div class="qcards">${qs.map((a) => `<button class="qcard" data-answer="${a.slug}" style="--qc:${a.color}">
        <span class="qq">${esc(a.q)}</span><span class="qn"><b>${esc(a.number.v)}</b> ${esc(a.number.k)}</span></button>`).join("")}</div>
      <button class="linkish ask-all" data-all-q>All ${A.length} questions and their sources →</button>
    </section>`;
  el.innerHTML = `${ask}
    <h1 class="headline${ask ? " sub" : ""}">${fmt(cs.length)} cases across ${countries.size} ${countries.size === 1 ? "country" : "countries"}</h1>
    <p class="lede">${any ? "Filtered view. Click a chip to remove it." : `Seizures, arrests and convictions from ${fmt(reports)} public reports, ${esc(m.window?.[0] || "")} to ${esc(m.window?.[1] || "")}. <b>${fmt(mapped)}</b> are pinned to a city or district; the rest are country-level or name no place. Nobody accused is ever named.`}</p>
    ${any ? "" : `<button class="guide-card-cta" data-guide aria-label="Watch the 2-minute video guide">
      <span class="gc-thumb"><img src="media/guide-thumb.jpg" alt=""><span class="gc-play">▶</span></span>
      <span class="gc-text"><b>New here? Watch the 2-minute guide</b><span>Ask a question, read the answer, check the evidence</span></span></button>`}
    <div class="active-filters">${[
      ...[...f.kinds].map((k) => `<button class="chip k" style="--kc:${KIND_COLOR[k]}" data-f="kinds" data-v="${k}">${KIND_LABEL[k]} <span class="x">✕</span></button>`),
      ...[...f.species].map((s) => `<button class="chip" data-f="species" data-v="${s}">${esc(spLabel(s))} <span class="x">✕</span></button>`),
      ...[...f.countries].map((c) => `<button class="chip" data-f="countries" data-v="${c}">${esc(ccName(c))} <span class="x">✕</span></button>`),
      ...[...f.ver].map((v) => `<button class="chip" data-f="ver" data-v="${v}">${esc(VERB[v]?.[0] || v)} <span class="x">✕</span></button>`),
      f.range ? `<button class="chip" data-clear-range>${esc(f.range[0])} → ${esc(f.range[1])} <span class="x">✕</span></button>` : "",
      any ? `<button class="chip" data-clear-all style="background:transparent">Clear all</button>` : "",
    ].join("")}</div>
    <div class="tiles">
      <div class="tile"><div class="v">${fmt(reports)}</div><div class="k">reports merged into cases</div></div>
      <div class="tile"><div class="v">${Object.keys(sp).length}</div><div class="k">species groups</div></div>
    </div>
    <div class="chips" style="margin-bottom:6px">${Object.entries(KIND_LABEL).map(([k, l]) => `<button class="chip k" style="--kc:${KIND_COLOR[k]}${f.kinds.has(k) ? ";background:#fff;box-shadow:inset 0 0 0 1.5px " + KIND_COLOR[k] : ""}" data-f="kinds" data-v="${k}" aria-pressed="${f.kinds.has(k)}">${l} <span class="muted">${kinds[k] || 0}</span></button>`).join("")}</div>
    <div class="sec"><h3>Evidence</h3><button data-open="about">What do these mean?</button></div>
    <div class="chips" style="margin-bottom:4px">${Object.entries(VERB).map(([k, [l, c]]) => `<button class="chip k" style="--kc:${c}${f.ver.has(k) ? ";background:#fff;box-shadow:inset 0 0 0 1.5px " + c : ""}" data-f="ver" data-v="${k}" aria-pressed="${f.ver.has(k)}">${l} <span class="muted">${vers[k] || 0}</span></button>`).join("")}</div>
    <div class="sec"><h3>Species</h3></div>
    <div class="bars">${bars(Object.entries(sp).sort((a, b) => b[1] - a[1]).map(([k, n]) => [k, n, spLabel(k)]), "species", "var(--species)", 8, (k) => ic.sp(k))}</div>
    <div class="sec"><h3>Countries</h3></div>
    <div class="bars">${bars(Object.entries(cc).sort((a, b) => b[1] - a[1]).map(([k, n]) => [k, n, ccName(k)]), "countries", "var(--place)", 8, (k) => ic.flag(k))}</div>
    <div class="sec"><h3>Latest</h3><button data-open="table">All ${fmt(cs.length)} as a table</button></div>
    <div class="feed">${latest.map((c) => `<button class="item" data-case="${c.id}" style="--kc:${KIND_COLOR[KIND(c.kind)]}"><i class="k ki">${ic.kind(c.kind)}</i><span><div class="t">${esc(c.summary)}</div>
      <div class="s">${esc(c.date || "undated")} · ${c.n_sources} report${c.n_sources > 1 ? "s" : ""}</div></span></button>`).join("") || `<p class="muted">Nothing matches these filters.</p>`}</div>`;
  el.querySelectorAll("[data-f]").forEach((b) => b.addEventListener("click", () => toggle(b.dataset.f, b.dataset.v)));
  el.querySelectorAll("[data-persona]").forEach((b) => b.addEventListener("click", () => { S.persona = b.dataset.persona; renderPulse(el); }));
  el.querySelectorAll("[data-answer]").forEach((b) => b.addEventListener("click", () => go({ kind: "answer", id: b.dataset.answer })));
  el.querySelector("[data-all-q]")?.addEventListener("click", () => (location.href = "answers.html"));
  el.querySelector("[data-clear-all]")?.addEventListener("click", clearFilters);
  el.querySelector("[data-guide]")?.addEventListener("click", () => dispatchEvent(new CustomEvent("wildtrace:video")));
  el.querySelector("[data-clear-range]")?.addEventListener("click", () => { S.filters.range = null; emit("filters"); });
  el.querySelectorAll("[data-case]").forEach((b) => b.addEventListener("click", () => go({ kind: "case", id: b.dataset.case })));
  el.querySelectorAll("[data-open]").forEach((b) => b.addEventListener("click", () => dispatchEvent(new CustomEvent("wildtrace:open", { detail: b.dataset.open }))));
  el.insertAdjacentHTML("beforeend", `<button class="btn violet" style="width:100%;margin-top:16px" id="p-chart">Explore the links in Investigate</button>`);
  el.querySelector("#p-chart").addEventListener("click", () => dispatchEvent(new CustomEvent("wildtrace:open", { detail: "investigate" })));
  el.insertAdjacentHTML("beforeend", `<p class="muted" style="font-size:12px;margin:16px 0 0">Counts show where wildlife crime is <i>reported</i> in the newsrooms and government sites searched, not where it happens. <a href="data/cases.csv" download>Download CSV</a> · CC BY 4.0</p>`);
}
