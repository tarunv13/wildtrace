"""Static pages for search engines, AI answer engines and people without JavaScript.

The Atlas is one JavaScript application: wonderful to use, invisible to a crawler. Everything a
search engine could rank lives in `cases.json`, which it will never read. So the build also emits
a plain HTML layer from the same data:

    /species/<slug>.html   one page per species group: how often it is reported, where, recent cases
    /country/<cc>.html     one page per country
    /case/<id>.html        one page per case, with its account, its evidence and its sources
    /browse.html           the index that ties them together
    /sitemap.xml           every page above
    /robots.txt            crawling allowed, including the AI crawlers, with the sitemap named
    /pathways.html         wildlife crime as an environment-to-security risk, evidence per link
    /llms.txt              a plain-text brief for answer engines: what this is, how to cite it

These pages are not a trick to catch traffic. They carry the same facts as the panels they
mirror, they say the same things about evidence and coverage, and each one links into the live
Atlas at the matching view. A reader arriving from a search lands on something readable, and an
answer engine quoting the figures gets them with their caveats attached.

Why this matters for citation: an answer engine needs a stable URL, a heading that states the
claim, numbers in text (not in a canvas) and a licence. Every page here has all four.
"""
from __future__ import annotations

import html
import json
import re
from datetime import date
from pathlib import Path

SITE = "https://tarunv13.github.io/wildtrace"
LICENCE = "https://creativecommons.org/licenses/by/4.0/"

MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August",
          "September", "October", "November", "December"]
VERB = {
    "validated": "checked by a reviewer against its sources",
    "official": "reported by at least one government, customs, police or judicial source",
    "corroborated": "reported by two or more independent outlets",
    "single": "reported by a single outlet, so it is a lead rather than an established fact",
}


def esc(s) -> str:
    return html.escape(str(s or ""), quote=True)


def slug(s: str) -> str:
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", str(s).lower())).strip("-") or "x"


def long_date(d: str) -> str:
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", d or "")
    return f"{int(m.group(3))} {MONTHS[int(m.group(2)) - 1]} {m.group(1)}" if m else "an unrecorded date"


def page(title: str, desc: str, canonical: str, body: str, jsonld: dict | None = None,
         crumbs: list[tuple[str, str]] | None = None) -> str:
    """One small, fast, mobile-first document. No JavaScript: nothing here needs it."""
    ld = f'<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>' if jsonld else ""
    crumb = ""
    if crumbs:
        crumb = '<nav class="crumbs" aria-label="Breadcrumb">' + " › ".join(
            f'<a href="{esc(u)}">{esc(t)}</a>' for t, u in crumbs) + "</nav>"
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{esc(canonical)}">
<meta property="og:type" content="article">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{esc(canonical)}">
<meta property="og:image" content="{SITE}/og.png">
<meta name="twitter:card" content="summary_large_image">
<link rel="stylesheet" href="{SITE}/css/page.css">
<link rel="icon" href="{SITE}/brand/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="{SITE}/brand/apple-touch-icon.png">
{ld}
</head>
<body>
<header class="top"><a class="brand" href="{SITE}/"><img src="{SITE}/brand/mark.svg" alt="" width="26" height="26">Wild<b>Trace</b></a>
  <span class="tag">Follow the trade. Open evidence on illegal wildlife trade.</span></header>
<main>
{crumb}
{body}
</main>
<footer>
  <p><a href="{SITE}/">Open the interactive Atlas</a> · <a href="{SITE}/browse.html">Browse every species and country</a>
     · <a href="{SITE}/data/cases.csv">Download the data (CSV)</a> · <a href="https://github.com/tarunv13/wildtrace">Source code</a></p>
  <p class="small">Data CC BY 4.0. Cite as: Verma, T. K. (2026). <i>WildTrace: the open atlas of illegal wildlife trade.</i>
     Zenodo. <a href="https://doi.org/10.5281/zenodo.22902819">https://doi.org/10.5281/zenodo.22902819</a></p>
  <p class="small">Counts show where wildlife crime is <b>reported</b>, in the newsrooms and government sites searched,
     not where it happens. No person accused is ever named.</p>
</footer>
</body>
</html>
"""


def _case_account(c: dict, sp_label) -> str:
    """The same account the case panel shows, in prose, for a crawler and a reader."""
    place = c.get("place") or {}
    where = ", ".join(x for x in [place.get("name"), place.get("admin1") if place.get("admin1") != place.get("name") else None,
                                  place.get("country_name") or place.get("country")] if x)
    sp = [sp_label(s) for s in c.get("species", [])]
    kind = {"seizure": "A seizure", "arrest": "An arrest or conviction"}.get(c.get("kind"), "A rescue or report")
    out = [f"{kind} involving {', '.join(sp).lower() or 'wildlife'} was first reported on {long_date(c.get('date'))}"
           + (f", in {where}." if where else ", with no place named in any report.")]
    qs = {f"{q['value']:g} {q['unit']}" for q in (c.get("quantities") or ([c["quantity"]] if c.get("quantity") else []))}
    if qs:
        out.append(f"The reports give the quantity as {', '.join(sorted(qs))}.")
    if c.get("people_arrested"):
        n = c["people_arrested"]
        out.append(f"{n} {'person was' if n == 1 else 'people were'} reported arrested. WildTrace records the number "
                   "only, never who they are, and an arrest is not a conviction.")
    if c.get("agencies"):
        out.append(f"{', '.join(c['agencies'])} {'is' if len(c['agencies']) == 1 else 'are'} named as acting in the reports.")
    if len(c.get("route") or []) == 2:
        out.append(f"The consignment is described as moving from {c['route'][0]} to {c['route'][1]}, as stated in the "
                   "reports; an origin and destination given by a source are not an established route.")
    out.append(f"The case is drawn from {c.get('n_sources', 1)} report(s), "
               f"{VERB.get(c.get('verification'), 'of unknown standing')}.")
    return "".join(f"<p>{esc(t)}</p>" for t in out)


def build_pages(cases: list[dict], species: dict, countries: dict, meta: dict, out_dir) -> int:
    """Write the whole static layer. Returns the number of pages written."""
    from pathlib import Path
    out = Path(out_dir)
    (out / "species").mkdir(parents=True, exist_ok=True)
    (out / "country").mkdir(parents=True, exist_ok=True)
    (out / "case").mkdir(parents=True, exist_ok=True)
    sp_label = lambda gid: (species.get(gid) or {}).get("label", gid)
    cc_name = lambda cc: (countries.get(cc) or {}).get("name", cc)
    urls: list[tuple[str, str]] = []           # (path, lastmod)
    today = f"{date.today():%Y-%m-%d}"
    window = meta.get("window", ["", ""])

    def write(path: str, content: str):
        p = out / path
        p.parent.mkdir(parents=True, exist_ok=True)
        # Links between these pages are written absolute for clarity, then rewritten relative so the
        # set works when served from a fork, a local folder or a different domain. Canonical, Open
        # Graph and JSON-LD URLs stay absolute, which is what they are for.
        prefix = "../" * path.count("/")
        for attr in ("href", "src"):
            content = content.replace(f'{attr}="{SITE}/', f'{attr}="{prefix}').replace(f'{attr}="{SITE}"', f'{attr}="{prefix}"')
        p.write_text(content, encoding="utf-8")
        urls.append((path, today))

    # ---------------------------------------------------------------- case pages
    for c in cases:
        cid = c["id"]
        place = c.get("place") or {}
        where = place.get("name") or "location not reported"
        sp = [sp_label(s) for s in c.get("species", [])]
        title = f"{c.get('summary', 'Wildlife trade case')} — WildTrace"
        desc = (f"{', '.join(sp) or 'Wildlife'} case reported {long_date(c.get('date'))}"
                + (f" in {where}" if place else "") + f". {c.get('n_sources', 1)} source(s), evidence: "
                f"{c.get('verification', 'single')}. Open data from WildTrace.")
        rows = "".join(
            f'<li><a href="{esc(s.get("url"))}" rel="nofollow noopener" target="_blank">{esc(s.get("outlet") or "report")}</a>'
            f' <span class="muted">{esc(s.get("date") or "")}{" · official source" if s.get("tier") == "official" else ""}</span></li>'
            for s in c.get("sources", []))
        links = " ".join(f'<a class="pill" href="{SITE}/species/{slug(s)}.html">{esc(sp_label(s))}</a>' for s in c.get("species", []))
        if place.get("country"):
            links += f' <a class="pill" href="{SITE}/country/{esc(place["country"]).lower()}.html">{esc(cc_name(place["country"]))}</a>'
        body = f"""
<h1>{esc(c.get('summary', 'Wildlife trade case'))}</h1>
<p class="lede">{esc(long_date(c.get('date')))}{f" · {esc(where)}" if place else ""} ·
  <b>{esc(c.get('verification', 'single').replace('single', 'single report'))}</b>: {esc(VERB.get(c.get('verification'), ''))}.</p>
<div class="account">{_case_account(c, sp_label)}</div>
<h2>Documented facts</h2>
<dl class="facts">
  <dt>Reported</dt><dd>{esc(c.get('date') or 'date unknown')}</dd>
  <dt>Event</dt><dd>{esc(c.get('kind', ''))}</dd>
  <dt>Species group</dt><dd>{esc(', '.join(sp) or 'Wildlife, unspecified')}</dd>
  <dt>Place</dt><dd>{esc(where if place else 'Not named in any report')}</dd>
  <dt>Reports</dt><dd>{esc(c.get('n_sources', 1))} from {esc(c.get('n_outlets', 1))} outlet(s)</dd>
</dl>
<h2>Sources</h2><ul class="sources">{rows}</ul>
<h2>Explore</h2><p>{links} <a class="pill" href="{SITE}/#case/{esc(cid)}">See this case on the map →</a></p>
<p class="small">Case ID {esc(cid)}. Found a mistake?
  <a href="https://github.com/tarunv13/wildtrace/issues/new?labels=correction&amp;title=Correction:%20case%20{esc(cid)}">Report a correction</a>.</p>
"""
        ld = {"@context": "https://schema.org", "@type": "Report", "name": c.get("summary", ""),
              "datePublished": c.get("date", ""), "url": f"{SITE}/case/{cid}.html",
              "about": [{"@type": "Thing", "name": s} for s in sp] or [{"@type": "Thing", "name": "Illegal wildlife trade"}],
              "isPartOf": {"@type": "Dataset", "name": "WildTrace", "url": SITE + "/",
                           "identifier": "https://doi.org/10.5281/zenodo.22902819"},
              "license": LICENCE, "creator": {"@type": "Person", "name": "Tarun Kumar Verma",
                                              "identifier": "https://orcid.org/0009-0009-4130-2455"}}
        if place.get("lat"):
            ld["contentLocation"] = {"@type": "Place", "name": where,
                                     "geo": {"@type": "GeoCoordinates", "latitude": place["lat"], "longitude": place["lon"]}}
        write(f"case/{cid}.html", page(title, desc, f"{SITE}/case/{cid}.html", body, ld,
                                       [("WildTrace", SITE + "/"), ("Cases", SITE + "/browse.html")]))

    # ---------------------------------------------------------------- species pages
    # CITES seizure records (flows.json, from `wildtrace cites`): a group the news rarely covers,
    # such as orchids or cacti, still gets a page when seizures of it are reported to CITES.
    flows_path = Path(out_dir) / "data" / "flows.json"
    cites = {}
    if flows_path.exists():
        fl = json.loads(flows_path.read_text(encoding="utf-8"))
        for g_, o_, _e, i_, n_ in fl["seized"]:
            d_ = cites.setdefault(g_, {"n": 0, "from": {}, "to": {}})
            d_["n"] += n_
            if o_ != "XX":
                d_["from"][o_] = d_["from"].get(o_, 0) + n_
            d_["to"][i_] = d_["to"].get(i_, 0) + n_
        cites_since = fl.get("year_min")
    # Imports seized at US ports (lemis.json, from `wildtrace lemis`), by origin and product.
    lemis_path = Path(out_dir) / "data" / "lemis.json"
    lemis, lemis_products, lemis_names = {}, {}, {}
    if lemis_path.exists():
        lm = json.loads(lemis_path.read_text(encoding="utf-8"))
        for g_, o_, _e, _i, n_ in lm["seized"]:
            d_ = lemis.setdefault(g_, {"n": 0, "from": {}})
            d_["n"] += n_
            if o_ != "XX":
                d_["from"][o_] = d_["from"].get(o_, 0) + n_
        lemis_products, lemis_names = lm.get("products", {}), lm.get("product_names", {})
    for gid, g in species.items():
        mine = [c for c in cases if gid in c.get("species", [])]
        cz = cites.get(gid)
        if not mine and not (cz and cz["n"] >= 5):
            continue
        label = g.get("label", gid)
        cites_html = ""
        if cz and cz["n"] >= 5:
            tf = sorted(cz["from"].items(), key=lambda kv: -kv[1])[:8]
            tt = sorted(cz["to"].items(), key=lambda kv: -kv[1])[:8]
            cites_html = f"""
<h2>Where seized {esc(label.lower())} came from, and where it was seized</h2>
<p><b>{cz["n"]:,}</b> shipments of {esc(label.lower())} seized or confiscated were reported to CITES since {cites_since}
  (CITES Trade Database, source code I). Counts are shipment records, not quantities, and some countries report far more completely than others.</p>
<div class="cols2"><div><h3>Taken from</h3><ul>{"".join(f'<li>{esc(cc_name(cc))} <span class="muted">{n:,}</span></li>' for cc, n in tf)}</ul></div>
<div><h3>Seized in</h3><ul>{"".join(f'<li>{esc(cc_name(cc))} <span class="muted">{n:,}</span></li>' for cc, n in tt)}</ul></div></div>
<p><a class="pill" href="{SITE}/?mode=flows&amp;g={esc(gid)}">Follow {esc(label.lower())} on the Flows map →</a></p>"""
        lz = lemis.get(gid)
        if lz and lz["n"] >= 5:
            lf = sorted(lz["from"].items(), key=lambda kv: -kv[1])[:8]
            prods = ", ".join(f"{lemis_names.get(k, k).lower()} ({n:,})" for k, n in lemis_products.get(gid, [])[:5])
            cites_html += f"""
<h2>Seized at US ports</h2>
<p><b>{lz["n"]:,}</b> import records of {esc(label.lower())} were seized by the US Fish and Wildlife Service
  (LEMIS; Marshall et al. 2025, Eskew et al. 2020; CC BY 4.0). Most often seized as: {esc(prods)}.
  These records reflect US inspection effort and overlap the US seizures reported to CITES above: compare them, do not add them.</p>
<h3>Country of origin</h3><ul>{"".join(f'<li>{esc(cc_name(cc))} <span class="muted">{n:,}</span></li>' for cc, n in lf)}</ul>"""
        by_country: dict[str, int] = {}
        for c in mine:
            cc = (c.get("place") or {}).get("country")
            if cc:
                by_country[cc] = by_country.get(cc, 0) + 1
        top = sorted(by_country.items(), key=lambda kv: -kv[1])[:12]
        recent = sorted(mine, key=lambda c: c.get("date") or "", reverse=True)[:25]
        official = sum(1 for c in mine if c.get("verification") in ("official", "validated"))
        if not mine:   # CITES-only page
            title = f"{label} in the illegal wildlife trade: {cz['n']:,} seized shipments reported to CITES — WildTrace"
            desc = (f"{cz['n']:,} seized or confiscated shipments of {label.lower()} reported to CITES since {cites_since}: "
                    f"where they were taken from and where they were seized. Open data.")
            body = f"""
<h1>{esc(label)} in the illegal wildlife trade</h1>
<p class="lede">No news report of a {esc(label.lower())} seizure has reached WildTrace yet. The trade is still recorded:
  countries report seized and confiscated shipments to CITES.</p>
<p>{f"CITES appendix {esc(g.get('cites'))}. " if g.get("cites") else ""}{f"Taxa covered: {esc(', '.join(g.get('taxa', [])))}. " if g.get("taxa") else ""}</p>
{cites_html}"""
            ld = {"@context": "https://schema.org", "@type": "Dataset", "name": f"Seized shipments of {label} reported to CITES",
                  "description": desc, "url": f"{SITE}/species/{slug(gid)}.html", "license": LICENCE,
                  "isPartOf": {"@type": "Dataset", "name": "WildTrace", "url": SITE + "/"}}
            write(f"species/{slug(gid)}.html", page(title, desc, f"{SITE}/species/{slug(gid)}.html", body, ld,
                                                    [("WildTrace", SITE + "/"), ("Species", SITE + "/browse.html")]))
            continue
        title = f"{label} in the illegal wildlife trade: {len(mine)} recorded cases — WildTrace"
        desc = (f"{len(mine)} seizures, arrests and convictions involving {label.lower()} recorded from public reports "
                f"in {len(by_country)} countries, {window[0]} to {window[1]}. Open data, each case graded by evidence.")
        body = f"""
<h1>{esc(label)} in the illegal wildlife trade</h1>
<p class="lede">WildTrace has recorded <b>{len(mine)}</b> cases involving {esc(label.lower())} from public reports
  between {esc(window[0])} and {esc(window[1])}, in <b>{len(by_country)}</b> countries.
  {official} of them rest on an official or validated source.</p>
<p>{f"CITES appendix {esc(g.get('cites'))}. " if g.get("cites") else ""}
   {f"Taxa covered: {esc(', '.join(g.get('taxa', [])))}. " if g.get("taxa") else ""}
   Counts show where this trade is <b>reported</b>, not where it happens: reporting is uneven between countries and
   languages, and cases whose reports name no place are counted but cannot be mapped.</p>
<h2>Where {esc(label.lower())} cases are reported</h2>
<ul class="cols">{"".join(f'<li><a href="{SITE}/country/{cc.lower()}.html">{esc(cc_name(cc))}</a> <span class="muted">{n}</span></li>' for cc, n in top)}</ul>
<h2>Recent cases</h2>
<ul class="cases">{"".join(f'<li><a href="{SITE}/case/{c["id"]}.html">{esc(c.get("summary", ""))}</a> <span class="muted">{esc(c.get("date", ""))} · {esc(c.get("verification", ""))}</span></li>' for c in recent)}</ul>
{cites_html}
<p><a class="pill" href="{SITE}/#species/{esc(gid)}">See {esc(label.lower())} on the map →</a>
   <a class="pill" href="{SITE}/data/cases.csv">Download all cases (CSV)</a></p>
"""
        ld = {"@context": "https://schema.org", "@type": "Dataset",
              "name": f"Illegal wildlife trade cases involving {label}",
              "description": desc, "url": f"{SITE}/species/{slug(gid)}.html", "license": LICENCE,
              "isPartOf": {"@type": "Dataset", "name": "WildTrace", "url": SITE + "/"},
              "temporalCoverage": f"{window[0]}/{window[1]}", "keywords": [label, "illegal wildlife trade",
              "wildlife trafficking", "seizures", "CITES"],
              "creator": {"@type": "Person", "name": "Tarun Kumar Verma",
                          "identifier": "https://orcid.org/0009-0009-4130-2455"},
              "distribution": [{"@type": "DataDownload", "encodingFormat": "text/csv",
                                "contentUrl": f"{SITE}/data/cases.csv"}]}
        write(f"species/{slug(gid)}.html", page(title, desc, f"{SITE}/species/{slug(gid)}.html", body, ld,
                                                [("WildTrace", SITE + "/"), ("Species", SITE + "/browse.html")]))

    # ---------------------------------------------------------------- country pages
    seen_cc = {(c.get("place") or {}).get("country") for c in cases if (c.get("place") or {}).get("country")}
    for cc in sorted(x for x in seen_cc if x):
        mine = [c for c in cases if (c.get("place") or {}).get("country") == cc]
        name = cc_name(cc)
        by_sp: dict[str, int] = {}
        for c in mine:
            for s in c.get("species", []):
                by_sp[s] = by_sp.get(s, 0) + 1
        top = sorted(by_sp.items(), key=lambda kv: -kv[1])[:12]
        recent = sorted(mine, key=lambda c: c.get("date") or "", reverse=True)[:25]
        title = f"Wildlife trafficking in {name}: {len(mine)} recorded cases — WildTrace"
        desc = (f"{len(mine)} wildlife seizures, arrests and convictions recorded in {name} from public reports, "
                f"{window[0]} to {window[1]}, by species and by strength of evidence. Open data.")
        body = f"""
<h1>Wildlife trafficking cases reported in {esc(name)}</h1>
<p class="lede">WildTrace has recorded <b>{len(mine)}</b> cases in {esc(name)} from public reports between
  {esc(window[0])} and {esc(window[1])}.</p>
<p>These are cases <b>reported</b> in the newsrooms and government sites searched. A country with active reporters and
  a government that publishes its seizures will show more cases than one without, whatever the trade is doing.</p>
<h2>Most reported species groups in {esc(name)}</h2>
<ul class="cols">{"".join(f'<li><a href="{SITE}/species/{slug(g)}.html">{esc(sp_label(g))}</a> <span class="muted">{n}</span></li>' for g, n in top)}</ul>
<h2>Recent cases</h2>
<ul class="cases">{"".join(f'<li><a href="{SITE}/case/{c["id"]}.html">{esc(c.get("summary", ""))}</a> <span class="muted">{esc(c.get("date", ""))} · {esc(c.get("verification", ""))}</span></li>' for c in recent)}</ul>
<p><a class="pill" href="{SITE}/#country/{esc(cc)}">See {esc(name)} on the map →</a></p>
"""
        ld = {"@context": "https://schema.org", "@type": "Dataset",
              "name": f"Illegal wildlife trade cases reported in {name}", "description": desc,
              "url": f"{SITE}/country/{cc.lower()}.html", "license": LICENCE,
              "spatialCoverage": {"@type": "Place", "name": name},
              "temporalCoverage": f"{window[0]}/{window[1]}",
              "isPartOf": {"@type": "Dataset", "name": "WildTrace", "url": SITE + "/"},
              "creator": {"@type": "Person", "name": "Tarun Kumar Verma"}}
        write(f"country/{cc.lower()}.html", page(title, desc, f"{SITE}/country/{cc.lower()}.html", body, ld,
                                                 [("WildTrace", SITE + "/"), ("Countries", SITE + "/browse.html")]))

    # ---------------------------------------------------------------- browse index
    sp_rows = "".join(
        f'<li><a href="{SITE}/species/{slug(gid)}.html">{esc(g.get("label", gid))}</a> '
        f'<span class="muted">{sum(1 for c in cases if gid in c.get("species", []))}</span></li>'
        for gid, g in sorted(species.items(), key=lambda kv: -sum(1 for c in cases if kv[0] in c.get("species", [])))
        if any(gid in c.get("species", []) for c in cases) or (cites.get(gid) or {}).get("n", 0) >= 5)
    cc_rows = "".join(
        f'<li><a href="{SITE}/country/{cc.lower()}.html">{esc(cc_name(cc))}</a> '
        f'<span class="muted">{sum(1 for c in cases if (c.get("place") or {}).get("country") == cc)}</span></li>'
        for cc in sorted(seen_cc, key=lambda cc: -sum(1 for c in cases if (c.get("place") or {}).get("country") == cc)))
    body = f"""
<h1>Browse illegal wildlife trade cases</h1>
<p class="lede">{len(cases):,} cases from {meta.get('n_reports', '')} public reports, {esc(window[0])} to {esc(window[1])},
  covering both animals and plants. Every case links to its sources and says how strongly it is evidenced.</p>
<p><a class="pill" href="{SITE}/answers.html">Questions WildTrace answers →</a> <a class="pill" href="{SITE}/pathways.html">Is wildlife crime a security risk? →</a></p>
<h2>By species group</h2><ul class="cols">{sp_rows}</ul>
<h2>By country</h2><ul class="cols">{cc_rows}</ul>
<h2>The data</h2>
<p><a href="{SITE}/data/cases.csv">cases.csv</a> — one row per case, CC BY 4.0.
   <a href="{SITE}/">The interactive Atlas</a> maps the same data, with a timeline, filters by evidence, and a
   link-analysis workbench that runs in your browser.</p>
"""
    write("browse.html", page("Browse illegal wildlife trade cases by species and country — WildTrace",
                              f"Index of {len(cases):,} recorded wildlife trafficking cases by species group and country, "
                              "from public reports worldwide. Open data, CC BY 4.0.",
                              f"{SITE}/browse.html", body,
                              {"@context": "https://schema.org", "@type": "CollectionPage",
                               "name": "Browse illegal wildlife trade cases", "url": f"{SITE}/browse.html"},
                              [("WildTrace", SITE + "/")]))

    # ---------------------------------------------------------------- risk pathways
    from . import pathways
    pw_path, pw_html = pathways.build(cases, species, countries, meta, out, page, esc, SITE)
    write(pw_path, pw_html)

    # ---------------------------------------------------------------- questions WildTrace answers
    from . import answers as _answers
    _answers.publish(_answers.build(cases, species, countries, meta, out / "data"), out, page, esc, SITE, write)

    # ---------------------------------------------------------------- sitemap, robots, llms.txt
    entries = "".join(f"<url><loc>{SITE}/{u}</loc><lastmod>{m}</lastmod></url>" for u, m in urls)
    (out / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f'<url><loc>{SITE}/</loc><lastmod>{today}</lastmod><priority>1.0</priority></url>{entries}</urlset>\n',
        encoding="utf-8")
    (out / "robots.txt").write_text(
        "# WildTrace: open data, open to crawlers, including the ones that answer questions.\n"
        "User-agent: *\nAllow: /\n\n"
        "# Named explicitly so there is no doubt: the data is CC BY 4.0, and attribution is the only ask.\n"
        + "".join(f"User-agent: {a}\nAllow: /\n\n" for a in
                  ["GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-User", "anthropic-ai",
                   "PerplexityBot", "Google-Extended", "Applebot-Extended", "CCBot", "Bingbot", "DuckDuckBot"])
        + f"Sitemap: {SITE}/sitemap.xml\n", encoding="utf-8")
    (out / "llms.txt").write_text(f"""# WildTrace

> The open atlas of illegal wildlife trade: seizures, arrests and convictions of wild animals and
> plants worldwide, each case graded by the strength of its evidence, with the underlying data
> published as CSV under CC BY 4.0.

WildTrace collects public reports (government, customs, police and judicial releases first, then
news in {len(set(c.get('place', {}).get('country') for c in cases if c.get('place')))} countries and several languages), screens them,
extracts the species, place, quantity, agency and route, merges reports about the same incident
into one case, and publishes the result.

## Facts a citation should carry

- Cases recorded: {len(cases):,}, from {meta.get('n_reports', 'public')} reports, {window[0]} to {window[1]}.
- Evidence: {meta.get('verification', {}).get('official', 0)} official, {meta.get('verification', {}).get('corroborated', 0)} corroborated by two or more outlets, {meta.get('verification', {}).get('single', 0)} single-report.
- Coverage: {meta.get('coverage', {}).get('mapped', 0)} cases are pinned to a city or district, {meta.get('coverage', {}).get('country_only', 0)} to a country only, and {meta.get('coverage', {}).get('unmapped', 0)} name no place.
- Both animals and plants: orchids, succulents, cycads, rosewood, agarwood and medicinal plants are
  covered alongside pangolin, ivory, rhino horn and big cats.
- The essential caveat, which any summary should repeat: these counts show where wildlife crime is
  **reported**, in the sources searched, not where it happens.
- No person accused is ever named. Arrests are counts only.

## Wildlife crime and security

WildTrace maps seven links from nature to national security (extraction, routes, borders, crime
revenue, disease risk, ecosystem loss, evidence and trust) and rates the open evidence for each.
The weakest link is who profits: seizures are common in the record, convictions rare, financial
flows absent. Security framing should not become militarisation (Duffy 2015; Massé et al. 2020).
Page: {SITE}/pathways.html. Framework after the Oxford Agile Initiative's "Environment and National
Security: Exploring the Risk Pathways" (2026), research questions R1.37 and R5.2-R5.3.

## Links

- Atlas (interactive map): {SITE}/
- Browse by species and country: {SITE}/browse.html
- Questions WildTrace answers (live, with sources and limits): {SITE}/answers.html
- Risk pathways (wildlife crime and national security): {SITE}/pathways.html
- US port seizures (CSV, CC BY 4.0): {SITE}/data/lemis_seized_flows.csv
- Open research agenda: https://github.com/tarunv13/wildtrace/blob/main/docs/RESEARCH_AGENDA.md
- Data (CSV, CC BY 4.0): {SITE}/data/cases.csv
- Method and limits: {SITE}/#methods
- Source code: https://github.com/tarunv13/wildtrace
- Citation: Verma, T. K. (2026). WildTrace: the open atlas of illegal wildlife trade. Zenodo.
  https://doi.org/10.5281/zenodo.22902819
""", encoding="utf-8")
    return len(urls) + 3
