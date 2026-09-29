"""Questions WildTrace answers: computed from the published data at every build.

Every answer has the same shape, so the Atlas, the static pages and answer engines read it the same
way (docs/VOICE.md): the question; who it is for; a one-sentence answer with its number; a small
chart; who answers it (the sources, with their standing); what the number cannot tell you; and where
to explore it on the map. Figures are never typed in: a question whose data is missing is skipped.

Output: web/data/answers.json (the Atlas) and web/answers/<slug>.html (crawlable, citable).
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

PERSONAS = {"journalists": "Journalists", "researchers": "Researchers", "policy": "Policy & enforcement", "everyone": "Everyone"}
# Colour follows the domain of the data, as everywhere in the Atlas.
DOMAIN = {"cases": "#d6453d", "species": "#218a5b", "trade": "#c27a06", "network": "#0f8b8d", "place": "#2563eb", "health": "#7c4dff"}


def _load(p: Path):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def _pct(a, b):
    return round(100 * a / b) if b else 0


def build(cases: list[dict], species: dict, countries: dict, meta: dict, data: Path) -> list[dict]:
    sp = lambda g: (species.get(g) or {}).get("label", g)
    cc = lambda c: (countries.get(c) or {}).get("name") or c
    flows, lemis, zoo = _load(data / "flows.json"), _load(data / "lemis.json"), _load(data / "zoonoses.json")
    gap, cap, acc = _load(data / "online_gap.json"), _load(data / "captive_claims.json"), _load(data / "accuracy.json")
    v = meta.get("verification", {})
    news = {"name": "Public reports (WildTrace)", "detail": f"{v.get('official', 0):,} official, {v.get('corroborated', 0):,} corroborated, "
            f"{v.get('single', 0):,} single report", "url": "#methods"}
    cites = {"name": "CITES Trade Database", "detail": "seized shipments (source I), reported by governments to UNEP-WCMC", "url": "https://trade.cites.org/"}
    out: list[dict] = []
    kinds = Counter(c["kind"] for c in cases)
    by_sp = Counter(s for c in cases for s in c["species"] if s != "wildlife_general")
    plants = {g for g, m in species.items() if m.get("kingdom") == "plant"}

    top = by_sp.most_common(6)
    if len(top) >= 3:
        out.append({"slug": "what-wildlife-is-seized-most", "domain": "species", "personas": ["everyone", "journalists"],
                    "q": "Which wildlife is seized most often?",
                    "a": f"{sp(top[0][0])} lead the public record with {top[0][1]:,} cases, then {sp(top[1][0]).lower()} ({top[1][1]:,}) and "
                         f"{sp(top[2][0]).lower()} ({top[2][1]:,}).",
                    "number": {"v": f"{top[0][1]:,}", "k": f"cases involving {sp(top[0][0]).lower()}"},
                    "chart": [[sp(g), n] for g, n in top], "who": [news],
                    "limit": "Cases count reporting, not trafficking volume: well-covered species and countries look bigger.",
                    "go": {"label": "See these species on the map", "href": "./"}})

    if flows:
        s = [r for r in flows["seized"] if r[1] not in ("XX",) and r[1] != r[3]]
        tot = sum(r[4] for r in flows["seized"])
        us = sum(r[4] for r in flows["seized"] if r[3] == "US")
        routes = Counter()
        for g, o, e, i, n in s:
            if i != "US" and o != "US":
                routes[(o, i)] += n
        rt = routes.most_common(6)
        if rt:
            out.append({"slug": "where-seized-wildlife-comes-from-and-goes", "domain": "trade", "personas": ["policy", "researchers"],
                        "q": "Where does seized wildlife come from, and where is it caught?",
                        "a": f"Leaving the United States aside, the busiest seized route is {cc(rt[0][0][0])} to {cc(rt[0][0][1])} "
                             f"({rt[0][1]:,} shipments); US-bound routes are {_pct(us, tot)}% of all {tot:,} seized shipments reported to CITES.",
                        "number": {"v": f"{tot:,}", "k": f"seized shipments reported to CITES since {flows.get('year_min')}"},
                        "chart": [[f"{cc(a)} → {cc(b)}", n] for (a, b), n in rt], "who": [cites],
                        "limit": "Countries report seizures unevenly; the United States reports far more completely than most.",
                        "go": {"label": "Follow the routes in Flows", "href": "./?mode=flows&us=0"}})

    if gap:
        rows = sorted([p for p in gap["pairs"] if p["adverts"] >= 50], key=lambda p: -(p["adverts"] / (p["cases"] + 1)))[:6]
        if rows:
            r0 = rows[0]
            out.append({"slug": "is-wildlife-sold-online-ever-caught", "domain": "network", "personas": ["journalists", "policy"],
                        "q": "Is wildlife sold online ever caught?",
                        "a": f"Rarely, in the public record: {sp(r0['group'])} in {cc(r0['country'])} drew {r0['adverts']:,} adverts and "
                             f"{r0['cases']} WildTrace cases in the same period.",
                        "number": {"v": f"{gap['adverts']:,}", "k": f"adverts recorded by ECO-SOLVE, {gap['window'][0][:7]} to {gap['window'][1][:7]}"},
                        "chart": [[f"{sp(p['group'])}, {cc(p['country'])}", p["adverts"]] for p in rows],
                        "who": [{"name": "ECO-SOLVE (Global Initiative Against Transnational Organized Crime)", "detail": "adverts recorded by regional hubs", "url": gap["url"]}, news],
                        "limit": "Adverts and cases are recorded with different effort; the ratio is not a detection rate.",
                        "go": {"label": "See the comparison in Analysis", "href": "./#analysis"}})

    seiz, conv = kinds.get("seizure", 0), kinds.get("conviction", 0)
    if seiz:
        out.append({"slug": "how-often-a-seizure-ends-in-conviction", "domain": "cases", "personas": ["policy", "journalists"],
                    "q": "How often does a seizure end in a conviction?",
                    "a": f"In the public record, for every conviction there are about {round(seiz / max(conv, 1))} seizures: "
                         f"{seiz:,} seizures, {kinds.get('arrest', 0):,} arrest reports and {conv:,} convictions.",
                    "number": {"v": f"{conv:,}", "k": "convictions in the record"},
                    "chart": [["Seizures", seiz], ["Arrests", kinds.get("arrest", 0)], ["Rescues", kinds.get("rescue", 0)], ["Convictions", conv]],
                    "who": [news],
                    "limit": "Courts are reported far less than seizures, so part of the drop is a reporting gap, not only attrition.",
                    "go": {"label": "Open the convictions", "href": "./"}})

    if flows:
        tot = sum(r[4] for r in flows["seized"])
        pl = sum(r[4] for r in flows["seized"] if r[0] in plants)
        pc = sum(1 for c in cases if any(s in plants for s in c["species"]))
        out.append({"slug": "are-plants-trafficked-too", "domain": "species", "personas": ["everyone", "researchers"],
                    "q": "Are plants trafficked as much as animals?",
                    "a": f"Plants are {_pct(pl, tot)}% of seized shipments reported to CITES but only {_pct(pc, len(cases))}% of news cases: "
                         "timber, orchids and medicinal plants are trafficked far more than they are reported.",
                    "number": {"v": f"{_pct(pl, tot)}%", "k": "of CITES seizures are plants"},
                    "chart": [["Plants in CITES seizures (%)", _pct(pl, tot)], ["Plants in news cases (%)", _pct(pc, len(cases))]],
                    "who": [cites, news],
                    "limit": "CITES lists many more plant species than news ever names; plant blindness cuts both ways.",
                    "go": {"label": "Browse plant groups", "href": "browse.html"}})

    if lemis:
        org = Counter()
        for g, o, e, i, n in lemis["seized"]:
            if o != "XX":
                org[o] += n
        t = sum(r[4] for r in lemis["seized"])
        out.append({"slug": "what-is-seized-at-us-ports", "domain": "trade", "personas": ["researchers", "journalists"],
                    "q": "What is seized at US ports, and where does it come from?",
                    "a": f"US wildlife inspectors seized {t:,} import records of the groups WildTrace follows; most came from "
                         + ", ".join(cc(c) for c, _ in org.most_common(3)) + ".",
                    "number": {"v": f"{t:,}", "k": "import records seized by US inspectors"},
                    "chart": [[cc(c), n] for c, n in org.most_common(6)],
                    "who": [{"name": "US Fish and Wildlife Service LEMIS", "detail": "cleaned by Marshall et al. 2025 and Eskew et al. 2020", "url": "https://doi.org/10.5281/zenodo.14982583"}],
                    "limit": "It measures where US inspection is strong as much as where trade flows.",
                    "go": {"label": "Seizures at US ports in Flows", "href": "./?mode=flows&ev=sl"}})

    if cap:
        rows = [r for r in cap["rows"] if r["shift"] is not None and r["records"] >= 50][:6]
        if rows:
            out.append({"slug": "can-captive-bred-labels-be-trusted", "domain": "trade", "personas": ["policy", "researchers"],
                        "q": "Can \"captive-bred\" labels be trusted?",
                        "a": f"Not always: declaring wild-caught animals as bred is a documented laundering route. {cc(rows[0]['exporter'])}'s "
                             f"commercial {sp(rows[0]['group']).lower()} exports moved from {round(100 * (rows[0]['early_share'] or 0))}% to "
                             f"{round(100 * (rows[0]['late_share'] or 0))}% captive-bred in a few years.",
                        "number": {"v": f"{len(cap['rows']):,}", "k": "exporter-group pairs checked"},
                        "chart": [[f"{cc(r['exporter'])}: {sp(r['group'])}", round(100 * (r['late_share'] or 0))] for r in rows],
                        "who": [cites, {"name": "Lyons & Natusch 2011", "detail": "the green python laundering study", "url": "https://doi.org/10.1016/j.biocon.2011.10.002"}],
                        "limit": "A rise is a question to ask, never a finding: genuine breeding and coral farming produce it too.",
                        "go": {"label": "See the table in Analysis", "href": "./#analysis"}})

    if zoo:
        g = zoo["virion"]["groups"]
        reps = zoo["who"].get("reports", [])
        out.append({"slug": "wildlife-trade-and-disease", "domain": "health", "personas": ["researchers", "policy"],
                    "q": "Does wildlife trade overlap with disease outbreaks?",
                    "a": f"Viruses confirmed by sequencing or isolation are recorded in {sum(1 for x in g.values() if x.get('viruses'))} traded groups, "
                         f"and WHO published {len(reps):,} reports on diseases with an animal reservoir; the two share a map, not a cause.",
                    "number": {"v": f"{len(reps):,}", "k": "WHO outbreak reports on animal-borne disease"},
                    "chart": sorted([[sp(k), x.get("viruses", 0)] for k, x in g.items()], key=lambda r: -r[1])[:6],
                    "who": [{"name": "VIRION (Carlson et al. 2022)", "detail": "virus-host records", "url": "https://doi.org/10.1128/mbio.02985-21"},
                            {"name": "WHO Disease Outbreak News", "detail": "outbreak reports", "url": "https://www.who.int/emergencies/disease-outbreak-news"}],
                    "limit": "Virus records follow where scientists sampled; an outbreak near a seizure does not mean the trade caused it.",
                    "go": {"label": "Open Zoonoses", "href": "./?mode=zoo"}})

    out.append({"slug": "is-wildlife-crime-a-security-risk", "domain": "cases", "personas": ["policy", "everyone"],
                "q": "Is wildlife crime a national security risk?",
                "a": "It reaches security through seven links, from extraction to crime revenue, disease and ecosystem loss; the weakest in open "
                     "data is who profits.",
                "number": {"v": "7", "k": "links from nature to security, each rated"},
                "chart": [], "who": [{"name": "WildTrace Risk pathways", "detail": "after the Oxford Agile Initiative agenda (2026)", "url": "pathways.html"}],
                "limit": "Security framing must not become militarisation: evidence first, rights respected.",
                "go": {"label": "Read Risk pathways", "href": "pathways.html"}})

    if acc:
        out.append({"slug": "how-accurate-is-wildtrace", "domain": "network", "personas": ["everyone", "researchers", "journalists", "policy"],
                    "q": "How accurate is WildTrace?",
                    "a": f"In a blind audit of {acc['n']} randomly sampled cases, {acc['relevant']} were genuine wildlife-trade enforcement "
                         f"events ({acc['precision']:.1%}; 95% interval {acc['ci'][0]:.1%} to {acc['ci'][1]:.1%}), and species were right in "
                         f"{acc['species_ok']:.1%} of them.",
                    "number": {"v": f"{acc['precision']:.1%}", "k": f"of audited cases are real events ({acc['date']})"},
                    "chart": [[k, n] for k, n in acc.get("errors", {}).items()],
                    "who": [{"name": "WildTrace accuracy audit", "detail": acc.get("method", ""), "url": "https://github.com/tarunv13/wildtrace/blob/main/docs/ACCURACY.md"}, news],
                    "limit": "Precision is measured; recall (events WildTrace misses) is not, and coverage follows the sources searched.",
                    "go": {"label": "Read the method", "href": "./#methods"}})

    latest = sorted((c for c in cases if c.get("date")), key=lambda c: c["date"], reverse=True)
    if latest:
        month = latest[0]["date"][:7]
        cur = [c for c in latest if c["date"].startswith(month)]
        tsp = Counter(s for c in cur for s in c["species"] if s != "wildlife_general").most_common(4)
        out.append({"slug": "what-was-seized-this-month", "domain": "cases", "personas": ["journalists", "everyone"],
                    "q": "What was seized this month?",
                    "a": f"{len(cur):,} cases so far in {month}" + (f", most often {', '.join(sp(g).lower() for g, _ in tsp[:3])}." if tsp else "."),
                    "number": {"v": f"{len(cur):,}", "k": f"cases in {month}"},
                    "chart": [[sp(g), n] for g, n in tsp], "who": [news],
                    "limit": "The latest weeks fill in as reports arrive; the daily run adds them.",
                    "go": {"label": "Play the timeline", "href": "./"}})
    for a in out:
        a["color"] = DOMAIN[a["domain"]]
        a["for"] = [PERSONAS[p] for p in a["personas"]]
    return out


def publish(answers: list[dict], out_dir: Path, page, esc, site: str, write) -> None:
    (out_dir / "data").mkdir(parents=True, exist_ok=True)
    (out_dir / "data" / "answers.json").write_text(json.dumps({"personas": PERSONAS, "answers": answers}, ensure_ascii=False,
                                                              separators=(",", ":")), encoding="utf-8")
    for a in answers:
        mx = max([n for _, n in a["chart"]] or [1]) or 1
        bars = "".join(f'<li><span class="l">{esc(l)}</span><span class="b"><i style="width:{max(2, 100 * n / mx):.0f}%;background:{a["color"]}"></i></span>'
                       f'<span class="n">{n:,}</span></li>' for l, n in a["chart"])
        who = "".join(f'<li><a href="{esc(w["url"] if w["url"].startswith("http") else site + "/" + w["url"].lstrip("./"))}">{esc(w["name"])}</a>'
                      f' <span class="muted">{esc(w["detail"])}</span></li>' for w in a["who"])
        go = a["go"]["href"]
        body = f"""
<p class="eyebrow" style="color:{a['color']}">Answer · for {esc(', '.join(a['for']))}</p>
<h1>{esc(a['q'])}</h1>
<div class="answer"><p class="lede">{esc(a['a'])}</p>
  <p class="big" style="color:{a['color']}">{esc(a['number']['v'])} <span>{esc(a['number']['k'])}</span></p></div>
{f'<ul class="bars">{bars}</ul>' if bars else ''}
<h2>Who answers</h2><ul class="who">{who}</ul>
<h2>What the number cannot tell you</h2><p>{esc(a['limit'])}</p>
<p><a class="pill" href="{esc(site + '/' + go.lstrip('./')) if not go.startswith('http') else esc(go)}">{esc(a['go']['label'])} →</a>
   <a class="pill" href="{site}/answers.html">All questions →</a></p>
<p class="small">Rebuilt daily from the WildTrace data. Cite: Verma, T. K. (2026). WildTrace: the open atlas of illegal wildlife trade.
  Zenodo. doi:10.5281/zenodo.22902819</p>"""
        ld = {"@context": "https://schema.org", "@type": "QAPage", "mainEntity": {"@type": "Question", "name": a["q"], "answerCount": 1,
              "acceptedAnswer": {"@type": "Answer", "text": f"{a['a']} {a['limit']}", "url": f"{site}/answers/{a['slug']}.html"}}}
        write(f"answers/{a['slug']}.html", page(f"{a['q']} — WildTrace", a["a"][:155], f"{site}/answers/{a['slug']}.html", body, ld,
                                                [("WildTrace", site + "/"), ("Questions", f"{site}/answers.html")]))
    groups = "".join(f"<h2>For {esc(label)}</h2><ul class=\"cases\">" + "".join(
        f'<li><a href="{site}/answers/{a["slug"]}.html">{esc(a["q"])}</a> <span class="muted">{esc(a["number"]["v"])} {esc(a["number"]["k"])}</span></li>'
        for a in answers if key in a["personas"]) + "</ul>" for key, label in PERSONAS.items())
    ld = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": a["q"], "acceptedAnswer": {"@type": "Answer", "text": a["a"]}} for a in answers]}
    write("answers.html", page("Questions WildTrace answers about illegal wildlife trade — WildTrace",
                               "Live answers about illegal wildlife trade: what is seized, where it goes, whether online sales are caught, how often seizures "
                               "end in convictions, and how accurate the data is. Each with its sources and limits.",
                               f"{site}/answers.html", f"<p class=\"eyebrow\">Questions</p><h1>What WildTrace answers, and for whom</h1>"
                               f"<p class=\"lede\">Every answer names its sources and says what its number cannot tell you. Figures are rebuilt daily.</p>{groups}",
                               ld, [("WildTrace", site + "/"), ("Questions", f"{site}/answers.html")]))
