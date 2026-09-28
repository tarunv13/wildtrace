"""Risk pathways: wildlife crime as an environment-to-security risk, with the evidence for each link.

The Oxford Agile Initiative's "Environment and National Security: Exploring the Risk Pathways"
(September 2026) maps how environmental damage reaches national security through causal
pathways, and notes that its diagrams "could be linked to a database showing relevant evidence
for each link". Its research agenda names environmental crime once, as a revenue source for
hostile actors and organised crime (R1.37), and asks whether "animal life" and
"revenue-generating uses" belong in the weaponisation of nature (R5.2, R5.3).

This page does that linking for the wildlife-crime pathway. Every link carries a number taken
from WildTrace's published data at build time, a strength rating for the open evidence, the
limit that stops the number meaning more, and the research question it speaks to. Where the
open evidence runs out, the page says so: that is where research is needed, and a claim that
outruns its evidence is how conservation gets securitised and militarised (Duffy 2015;
Lunstrum 2014; Massé et al. 2020).

Written as `web/pathways.html` by every build, so its figures never go stale.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

REPORT = ("Agile Initiative (2026). Environment and National Security: Exploring the Risk Pathways. "
          "Forward-looking research agenda. Oxford Martin School, University of Oxford.")

REFS = [
    ("Carlson, C. J. et al. (2022). The Global Virome in One Network (VIRION). mBio 13, e02985-21.", "https://doi.org/10.1128/mbio.02985-21"),
    ("Di Minin, E., Fink, C., Tenkanen, H. et al. (2018). Machine learning for tracking illegal wildlife trade on social media. Nature Ecology & Evolution 2, 406-407.", "https://doi.org/10.1038/s41559-018-0466-x"),
    ("Douglas, L. R. & Alie, K. (2014). High-value natural resources: linking wildlife conservation to international conflict, insecurity, and development concerns. Biological Conservation 171, 270-277.", "https://doi.org/10.1016/j.biocon.2014.01.031"),
    ("Duffy, R. (2015). War, by conservation. Geoforum 69, 238-248.", "https://doi.org/10.1016/j.geoforum.2015.09.014"),
    ("Eskew, E. A. et al. (2020). United States wildlife and wildlife product imports from 2000-2014. Scientific Data 7, 22.", "https://doi.org/10.1038/s41597-020-0354-5"),
    ("Kurland, J., Pires, S. F., McFann, S. C. & Moreto, W. D. (2017). Wildlife crime: a conceptual integration, literature review, and methodological critique. Crime Science 6, 4.", "https://doi.org/10.1186/s40163-017-0066-0"),
    ("Lunstrum, E. (2014). Green militarization: anti-poaching efforts and the spatial contours of Kruger National Park. Annals of the Association of American Geographers 104, 816-832.", "https://doi.org/10.1080/00045608.2014.912545"),
    ("Margulies, J. D. et al. (2019). Illegal wildlife trade and the persistence of \"plant blindness\". Plants, People, Planet 1, 173-182.", "https://doi.org/10.1002/ppp3.10053"),
    ("Marshall, B. M. et al. (2025). Tracing trade: mapping the global dimensions of US wildlife imports. Current Biology 35, 3959-3972.", "https://doi.org/10.1016/j.cub.2025.07.012"),
    ("Massé, F., Dickinson, H., Margulies, J. et al. (2020). Conservation and crime convergence? Situating the 2018 London Illegal Wildlife Trade Conference. Journal of Political Ecology 27, 23-42.", "https://doi.org/10.2458/v27i1.23543"),
    ("Scheffers, B. R., Oliveira, B. F., Lamb, I. & Edwards, D. P. (2019). Global wildlife trade across the tree of life. Science 366, 71-76.", "https://doi.org/10.1126/science.aav5327"),
    ("Stringham, O. C. et al. (2021). Dataset of seized wildlife and their intended uses. Data in Brief 39, 107531.", "https://doi.org/10.1016/j.dib.2021.107531"),
    ("'t Sas-Rolfes, M., Challender, D. W. S., Hinsley, A., Veríssimo, D. & Milner-Gulland, E. J. (2019). Illegal wildlife trade: scale, processes, and governance. Annual Review of Environment and Resources 44, 201-228.", "https://doi.org/10.1146/annurev-environ-101718-033253"),
    ("Wittemyer, G. et al. (2014). Illegal killing for ivory drives global decline in African elephants. PNAS 111, 13117-13121.", "https://doi.org/10.1073/pnas.1403984111"),
]

STRENGTH = {"strong": ("Open evidence: strong", "#218a5b"), "partial": ("Open evidence: partial", "#c27a06"),
            "gap": ("Open evidence: a gap", "#b3261e")}


def _load(p: Path):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def evidence(cases: list[dict], species: dict, data: Path) -> dict:
    """The figures behind each link, computed from the published files."""
    flows, lemis, zoo = _load(data / "flows.json"), _load(data / "lemis.json"), _load(data / "zoonoses.json")
    plants = {g for g, m in species.items() if m.get("kingdom") == "plant"}
    kinds = Counter(c.get("kind") for c in cases)
    ver = Counter(c.get("verification") for c in cases)
    modes = Counter(m for c in cases for m in c.get("modes") or [])
    e = {"cases": len(cases), "kinds": kinds, "ver": ver, "modes": modes,
         "arrested": sum(c.get("people_arrested") or 0 for c in cases),
         "multi": sum(1 for c in cases if len(c.get("countries") or []) > 1),
         "plant_cases": sum(1 for c in cases if any(s in plants for s in c.get("species", []))),
         "groups": len(species)}
    if flows:
        s = flows["seized"]
        e["cites"] = sum(r[4] for r in s)
        e["cites_plants"] = sum(r[4] for r in s if r[0] in plants)
        e["cites_transit"] = sum(r[4] for r in s if r[1] not in ("XX", r[2]))
        e["cites_us"] = sum(r[4] for r in s if r[3] == "US")
        e["cites_since"] = flows.get("year_min")
        e["cites_countries"] = len({r[1] for r in s if r[1] != "XX"} | {r[3] for r in s})
    if lemis:
        e["lemis"] = sum(r[4] for r in lemis["seized"])
        org = Counter()
        for r in lemis["seized"]:
            if r[1] != "XX":
                org[r[1]] += r[4]
        e["lemis_top"] = org.most_common(3)
        e["lemis_origins"] = len(org)
    if zoo:
        g = zoo["virion"]["groups"]
        e["zoo_groups"] = sum(1 for v in g.values() if v.get("viruses"))
        e["zoo_reports"] = len(zoo["who"].get("reports", []))
        e["zoo_wildlife"] = sum(1 for r in zoo["who"].get("reports", []) if r.get("pathway") == "wildlife")
    return e


def _pct(a, b):
    return f"{round(100 * a / b)}%" if b else "–"


def links(e: dict, cc_name) -> list[dict]:
    site = "https://tarunv13.github.io/wildtrace"
    top = ", ".join(f"{cc_name(c)} ({n:,})" for c, n in e.get("lemis_top", []))
    k = e["kinds"]
    return [
        {"id": "extraction", "n": 1, "title": "Nature is taken: poaching, illegal logging and collection",
         "strength": "strong",
         "shows": f"{e['cases']:,} seizures, arrests, convictions and rescues from public reports across {e['groups']} species groups, "
                  f"and {e.get('cites', 0):,} seized shipments reported to CITES since {e.get('cites_since', 2015)}. "
                  f"Plants make up {_pct(e.get('cites_plants', 0), e.get('cites', 0))} of the CITES seizures but only "
                  f"{_pct(e['plant_cases'], e['cases'])} of news cases: timber, orchids and medicinal plants are traded far more than they are reported.",
         "limit": "A seizure is an enforcement event. It shows that something was intercepted, not how much was taken.",
         "question": "R1.11 Interacting drivers of nature loss; R1.37 illegal extraction",
         "go": [("Species in the Atlas", f"{site}/browse.html")]},
        {"id": "routes", "n": 2, "title": "It moves: routes, transit hubs and online markets",
         "strength": "partial",
         "shows": f"{e.get('cites_transit', 0):,} CITES seizures passed through a third country between origin and seizure. "
                  f"{e['multi']} news cases span more than one country. Where reports name a transport mode, air "
                  f"({e['modes'].get('air', 0)}) and online sale ({e['modes'].get('online', 0)}) lead, then road ({e['modes'].get('road', 0)}) and sea ({e['modes'].get('sea', 0)}).",
         "limit": "Only 2 news cases name both ends of a route, so routes come from trade records, not from reporting.",
         "question": "Theme III, shipping and trade chokepoints",
         "go": [("Follow routes on the Flows map", f"{site}/?mode=flows")]},
        {"id": "ports", "n": 3, "title": "It reaches the border: what inspectors intercept",
         "strength": "strong",
         "shows": f"US wildlife inspectors seized {e.get('lemis', 0):,} import records of the groups WildTrace follows, from "
                  f"{e.get('lemis_origins', 0)} countries of origin; most often from {top}. "
                  f"Routes into the United States make up {_pct(e.get('cites_us', 0), e.get('cites', 0))} of CITES seizure records.",
         "limit": "This measures where inspection is strong and reported, above all in the United States, as much as where trade flows. "
                  "The US and CITES records overlap: compare them, never add them.",
         "question": "Theme III, resilience of ports and trade",
         "go": [("Seizures at US ports", f"{site}/?mode=flows&ev=sl"), ("Who supplies whom", f"{site}/?mode=flows")]},
        {"id": "crime", "n": 4, "title": "It funds crime and corrupts institutions",
         "strength": "gap",
         "shows": f"The record thins sharply after the seizure: {k.get('seizure', 0):,} seizures, {k.get('arrest', 0)} arrest reports "
                  f"({e['arrested']:,} people, counted and never named) and {k.get('conviction', 0)} convictions. "
                  "Documented links between wildlife products and armed groups exist for specific places and periods (Douglas & Alie 2014), "
                  "but the open evidence on who profits, and how much, is thin and contested (Duffy 2015; Massé et al. 2020).",
         "limit": "News reports convictions far less often than seizures, so the drop is partly a reporting gap. Financial flows are "
                  "not in open data; they need financial intelligence that WildTrace does not have.",
         "question": "R1.37 environmental crime as revenue for hostile actors; R5.2-R5.3 animal life and revenue-generating uses in the weaponisation of nature",
         "go": [("Arrests and convictions in the Atlas", f"{site}/")]},
        {"id": "health", "n": 5, "title": "It carries disease risk",
         "strength": "partial",
         "shows": f"Viruses confirmed by sequencing or isolation are recorded in {e.get('zoo_groups', 0)} of the traded species groups (VIRION). "
                  f"WHO published {e.get('zoo_reports', 0):,} outbreak reports on diseases with an animal reservoir, "
                  f"{e.get('zoo_wildlife', 0):,} of them spread by contact with wildlife.",
         "limit": "The two layers share a map, not a cause: an outbreak near a seizure does not mean the trade caused it, and "
                  "virus records follow where scientists have sampled.",
         "question": "Societal resilience and health security (a pathway the report's six themes do not name)",
         "go": [("Zoonoses mode", f"{site}/?mode=zoo")]},
        {"id": "systems", "n": 6, "title": "It erodes critical natural infrastructure",
         "strength": "partial",
         "shows": "The groups seized most often include seed dispersers (hornbills, primates), predators (big cats, sharks, owls), reef "
                  "builders (corals) and forest trees (rosewood, agarwood, sandalwood). About one in five land vertebrate species is traded "
                  "(Scheffers et al. 2019), and ivory poaching alone drove the decline of African elephants (Wittemyer et al. 2014).",
         "limit": "WildTrace records removals, not their ecological effect. The consequence for ecosystems comes from the literature, "
                  "species by species.",
         "question": "Theme I, critical natural infrastructure (R1.3 cascading risks, R1.12 actionable indicators)",
         "go": [("Species pages", f"{site}/browse.html")]},
        {"id": "trust", "n": 7, "title": "It is fought with evidence, or with rumour",
         "strength": "strong",
         "shows": f"Every case is graded: {e['ver'].get('official', 0)} rest on a government, customs, police or court source, "
                  f"{e['ver'].get('corroborated', 0)} on two or more independent outlets, and {e['ver'].get('single', 0):,} on a single "
                  "report, which WildTrace treats as a lead, not a finding.",
         "limit": "Grades describe the sources, not the truth of every detail in them.",
         "question": "Section 11, communicating uncertainty and countering misinformation",
         "go": [("Method and limits", f"{site}/#methods")]},
    ]


def diagram(ls: list[dict]) -> str:
    """The pathway as an inline SVG: five stages, seven numbered links, each a link to its evidence card."""
    stages = [("Nature", "species and habitats", "#218a5b"), ("Extraction", "poaching, logging", "#218a5b"),
              ("Trafficking", "routes, hubs, online", "#2563eb"), ("Markets", "borders and demand", "#c27a06"),
              ("Security", "consequences", "#b3261e")]
    w, h, bw, pad = 720, 270, 116, 18
    gap = (w - 2 * pad - 5 * bw) / 4
    X = [pad + i * (bw + gap) for i in range(5)]
    out = []
    for i, (t, s_, c) in enumerate(stages):
        x = X[i]
        out.append(f'<g><rect x="{x:.0f}" y="70" width="{bw}" height="70" rx="14" fill="{c}" fill-opacity=".1" stroke="{c}" stroke-width="1.5"/>'
                   f'<text x="{x + bw / 2:.0f}" y="100" text-anchor="middle" class="pw-t" fill="{c}">{t}</text>'
                   f'<text x="{x + bw / 2:.0f}" y="121" text-anchor="middle" class="pw-s">{s_}</text></g>')
        if i < 4:
            out.append(f'<path d="M{x + bw + 4:.0f},105 L{X[i + 1] - 6:.0f},105" stroke="#8a948f" stroke-width="1.6" marker-end="url(#pw-a)"/>')
    sx = X[4] + bw / 2
    # Security fans out into three consequences (links 4-6); trust (7) sits under the whole chain.
    for dx, lab in ((-50, "crime"), (0, "health"), (50, "nature")):
        out.append(f'<path d="M{sx:.0f},140 L{sx + dx:.0f},176" stroke="#b3261e" stroke-opacity=".45" stroke-width="1.4"/>'
                   f'<text x="{sx + dx:.0f}" y="222" text-anchor="middle" class="pw-s">{lab}</text>')
    out.append(f'<text x="{(X[0] + X[3] + bw) / 2:.0f}" y="245" text-anchor="middle" class="pw-s">evidence and trust, along the whole chain</text>')
    spots = {1: ((X[0] + bw + X[1]) / 2, 105), 2: (X[2] + bw / 2, 44), 3: (X[3] + bw / 2, 44),
             4: (sx - 50, 192), 5: (sx, 192), 6: (sx + 50, 192), 7: ((X[0] + X[3] + bw) / 2, 212)}
    for l in ls:
        x, y = spots[l["n"]]
        c = STRENGTH[l["strength"]][1]
        out.append(f'<a href="#{l["id"]}" aria-label="Link {l["n"]}: {l["title"]}"><circle cx="{x:.0f}" cy="{y:.0f}" r="15" fill="#fff" stroke="{c}" stroke-width="2.4"/>'
                   f'<text x="{x:.0f}" y="{y + 5:.0f}" text-anchor="middle" class="pw-n" fill="{c}">{l["n"]}</text><title>{l["title"]}</title></a>')
    gov = f'<rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="18" fill="none" stroke="#8a948f" stroke-dasharray="4 5"/>'           f'<text x="{pad}" y="26" class="pw-g">Governance: who enforces, who is accountable, who is heard</text>'
    return (f'<svg class="pathway" viewBox="0 0 {w} {h}" role="img" aria-labelledby="pw-title pw-desc">'
            f'<title id="pw-title">The wildlife-crime pathway from nature to national security</title>'
            f'<desc id="pw-desc">Five stages: nature, extraction, trafficking, markets and security consequences (crime, disease, '
            f'ecosystems), with seven numbered links, each rated by the strength of the open evidence behind it.</desc>'
            f'<defs><marker id="pw-a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
            f'<path d="M0,0 L10,5 L0,10z" fill="#8a948f"/></marker></defs>{gov}{"".join(out)}</svg>')


def build(cases: list[dict], species: dict, countries: dict, meta: dict, out_dir: Path, page, esc, site: str) -> tuple[str, str]:
    """Return (path, html) for the pathways page."""
    e = evidence(cases, species, Path(out_dir) / "data")
    cc_name = lambda cc: (countries.get(cc) or {}).get("name") or cc
    ls = links(e, cc_name)
    cards = "".join(
        f'<section class="link" id="{l["id"]}"><div class="link-h"><span class="num" style="--c:{STRENGTH[l["strength"]][1]}">{l["n"]}</span>'
        f'<h2>{esc(l["title"])}</h2></div>'
        f'<p class="badge" style="--c:{STRENGTH[l["strength"]][1]}">{STRENGTH[l["strength"]][0]}</p>'
        f'<p><b>What WildTrace shows.</b> {esc(l["shows"])}</p>'
        f'<p><b>What the number cannot tell you.</b> {esc(l["limit"])}</p>'
        f'<p class="small"><b>Research agenda.</b> {esc(l["question"])}</p>'
        f'<p>{"".join(f"<a class=pill href={chr(34)}{esc(u)}{chr(34)}>{esc(t)} →</a>" for t, u in l["go"])}</p></section>'
        for l in ls)
    n_strong = sum(1 for l in ls if l["strength"] == "strong")
    n_gap = [l for l in ls if l["strength"] == "gap"]
    faq = [
        ("Is illegal wildlife trade a national security issue?",
         f"It reaches national security through several pathways: organised crime and corruption, disease risk, and the loss of species "
         f"that ecosystems depend on. WildTrace maps seven links from nature to security and rates the open evidence for each: "
         f"{n_strong} are well evidenced in open data, and the link to crime revenue is the weakest. The 2026 Oxford research agenda on "
         f"environment and national security names environmental crime as a revenue source for hostile actors (R1.37)."),
        ("Does wildlife trafficking fund armed groups or terrorism?",
         "Documented links exist for particular places and periods, such as ivory and armed groups in Central Africa (Douglas & Alie 2014). "
         "But open evidence on who profits and how much is thin, and researchers warn that overstating a poaching-terrorism nexus has been "
         "used to justify militarised conservation that harms local people (Duffy 2015; Massé et al. 2020)."),
        ("How much wildlife is seized at borders?",
         f"CITES Parties reported {e.get('cites', 0):,} seized shipments of the species groups WildTrace follows since {e.get('cites_since', 2015)}, "
         f"and US inspectors seized {e.get('lemis', 0):,} wildlife import records between 2000 and 2022. The United States reports far more "
         "completely than most countries, so these numbers show inspection effort as much as trade."),
        ("Can wildlife trade cause pandemics?",
         f"Traded wildlife can carry viruses: {e.get('zoo_groups', 0)} of the traded species groups have viruses confirmed in VIRION. "
         "A shared location between a seizure and an outbreak does not show that the trade caused it; WildTrace shows the two together as a "
         "shared map, not a cause."),
        ("Where can I get open data on wildlife seizures?",
         f"WildTrace publishes cases, CITES seizure flows and US port seizures as CSV at {site}/data/, with a DOI on Zenodo "
         "(10.5281/zenodo.22902819). Case data are CC BY 4.0; CITES-derived files follow the CITES terms."),
    ]
    faq_html = "".join(f"<h3>{esc(q)}</h3><p>{esc(a)}</p>" for q, a in faq)
    refs = "".join(f'<li>{esc(t)} <a href="{esc(u)}">{esc(u.replace("https://doi.org/", "doi:"))}</a></li>' for t, u in REFS)
    lede_hook = (f"{e['kinds'].get('seizure', 0):,} seizures in the news, {e.get('cites', 0):,} seized shipments reported to CITES, "
                 f"{e.get('lemis', 0):,} imports seized at US ports, and {e['kinds'].get('conviction', 0)} convictions.")
    body = f"""
<p class="eyebrow">Risk pathways</p>
<h1>Wildlife crime as an environment-to-security risk: seven links, and the evidence for each</h1>
<p class="lede">{esc(lede_hook)} That last number is the story: nature is taken and moved at scale, and the record goes quiet
  where money and accountability begin.</p>
<div class="answer"><h2>The short answer</h2><ul>
  <li>Wildlife crime reaches security through <b>seven links</b>, from extraction to crime revenue, disease risk and the erosion of ecosystems.</li>
  <li><b>{n_strong} links are well evidenced</b> in open data; <b>{len(n_gap)} is a gap</b>: who profits, and how much ({esc(n_gap[0]['title'].lower()) if n_gap else ''}).</li>
  <li>Plants are {_pct(e.get('cites_plants', 0), e.get('cites', 0))} of CITES seizures but {_pct(e['plant_cases'], e['cases'])} of news cases: the pathway is greener than the headlines.</li>
  <li>Security framing must not become militarisation: evidence first, rights respected, no person named.</li></ul></div>
<figure class="pw">{diagram(ls)}
  <ol class="pw-list">{"".join(f'<li><a href="#{l["id"]}" style="--c:{STRENGTH[l["strength"]][1]}"><span class="num">{l["n"]}</span>{esc(l["title"])}</a></li>' for l in ls)}</ol>
  <figcaption>Each numbered link opens its evidence below. Ring colour: <span style="color:#218a5b">strong</span>,
  <span style="color:#c27a06">partial</span>, <span style="color:#b3261e">a gap</span> in open evidence.
  Framework after the Oxford Agile Initiative's environment and national security pathways (2026).</figcaption></figure>
{cards}
<h2>Where the evidence runs out</h2>
<p>The gaps are the research agenda. Open data cannot yet show who profits from wildlife crime, how much wildlife is taken
  rather than seized, or how removals cascade through ecosystems. Language technology can narrow some gaps: extracting several
  events from one report, telling a sale from a condemnation or a news story, and checking claims against evidence.
  <a href="https://github.com/tarunv13/wildtrace/blob/main/docs/RESEARCH_AGENDA.md">Read the open research agenda</a> and pick a question.</p>
<h2>Security without militarisation</h2>
<p>Calling wildlife crime a security threat can bring money and attention. It has also justified shoot-on-sight policies, the
  exclusion of local people from land they depend on, and "war by conservation" (Duffy 2015; Lunstrum 2014). WildTrace takes the
  security frame with three commitments: every claim carries its evidence and its limits; enforcement is counted, never glorified, and
  no accused person is named; and the harms to people who live alongside wildlife are part of the pathway, not a side effect.</p>
<h2>What can be done</h2>
<p>The research agenda sorts interventions into six kinds. For this pathway they look like this:</p>
<ul>
  <li><b>Information and foresight:</b> open observatories that grade evidence, like this one, and early warning for new species and routes.</li>
  <li><b>Regulation and standards:</b> due diligence for timber and wildlife supply chains, and consistent seizure reporting by every CITES Party.</li>
  <li><b>Capacity-building:</b> customs, port and postal inspection where routes converge, and forensic identification of seized products.</li>
  <li><b>Governance and coordination:</b> environment, health and security departments reading the same evidence, not three silos.</li>
  <li><b>Incentives:</b> livelihoods for the communities who live with wildlife, so that protection pays more than extraction.</li>
  <li><b>Communication:</b> local cases linked to the system they belong to, uncertainty stated as a range, and public concern made visible.</li>
</ul>
<h2>Questions people ask</h2>
{faq_html}
<h2>Sources</h2>
<p class="small">{esc(REPORT)} The research question numbers (R1.37, R5.2 and others) refer to this report.</p>
<ol class="refs small">{refs}</ol>
<h2>Cite this page</h2>
<p class="small">Verma, T. K. ({meta.get('built', '')[:4] or '2026'}). Wildlife crime as an environment-to-security risk: seven links, and the evidence for each.
  WildTrace. {site}/pathways.html. Figures rebuilt daily from the WildTrace data (doi:10.5281/zenodo.22902819).</p>
"""
    title = "Is wildlife crime a security risk? Seven pathways and the evidence for each — WildTrace"
    desc = (f"How illegal wildlife trade reaches national security: extraction, routes, borders, crime revenue, disease and "
            f"ecosystem loss, each link rated by its open evidence. {e.get('cites', 0):,} CITES seizures, "
            f"{e.get('lemis', 0):,} US port seizures, {e['cases']:,} cases.")
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "Article", "headline": "Wildlife crime as an environment-to-security risk: seven links, and the evidence for each",
         "url": f"{site}/pathways.html", "description": desc, "inLanguage": "en",
         "author": {"@type": "Person", "name": "Tarun Kumar Verma", "identifier": "https://orcid.org/0009-0009-4130-2455"},
         "isBasedOn": [{"@type": "Dataset", "name": "WildTrace", "identifier": "https://doi.org/10.5281/zenodo.22902819"},
                       {"@type": "Report", "name": "Environment and National Security: Exploring the Risk Pathways (2026)"}],
         "citation": [u for _, u in REFS], "license": "https://creativecommons.org/licenses/by/4.0/",
         "about": ["illegal wildlife trade", "environmental security", "national security", "wildlife crime", "zoonoses"]},
        {"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]}]}
    return "pathways.html", page(title, desc, f"{site}/pathways.html", body, ld, [("WildTrace", site + "/"), ("Risk pathways", f"{site}/pathways.html")])
