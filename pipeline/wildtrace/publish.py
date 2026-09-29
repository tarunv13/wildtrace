"""Build step: raw records → scored → extracted → cases → public JSON for the website.

Private intermediate output (headlines, full extraction) goes to data/interim.
Public output goes to web/data and passes privacy.assert_public_safe first.
"""
from __future__ import annotations

import json
import os
import time
from collections import Counter, defaultdict
from pathlib import Path

import yaml

from . import lexicon
from .collect.base import read_all_raw
from .config import INTERIM, LABELS, MODELS, RESOURCES, WEB_DATA, ensure_dirs
from .extract.cases import cluster, summarise
from .extract.events import extract, is_enforcement_candidate
from .graph import build as graph
from .privacy import assert_public_safe, scrub


MIN_DATE = "2024-01-01"
NOT_EVENTS = {"cordis.europa.eu", "op.europa.eu", "eur-lex.europa.eu", "data.europa.eu", "researchgate.net", "frontiersin.org", "sciencedirect.com"}



# Species groups that are plants; everything else in the lexicon is an animal.
FLORA = {"red_sanders", "rosewood", "agarwood", "orchids", "cacti_succulents", "cycads", "carnivorous_plants",
         "medicinal_plants", "sandalwood", "resins_gums", "bulbs_ornamental"}


def _cite() -> str:
    """Citation line for the site. Uses the Zenodo DOI once CITATION.cff records one."""
    try:
        cff = yaml.safe_load((Path(__file__).resolve().parents[2] / "CITATION.cff").read_text(encoding="utf-8")) or {}
    except OSError:
        cff = {}
    # Same form as GitHub's "Cite this repository" (APA): authors, version and DOI all from CITATION.cff.
    names = [f"{a['family-names']}, " + " ".join(f"{g[0]}." for g in a.get("given-names", "").split())
             for a in cff.get("authors", []) if a.get("family-names")] or ["Verma, T. K."]
    title = cff.get("title", "WildTrace: the open atlas of illegal wildlife trade")
    version = f" (Version {cff['version']})" if cff.get("version") else ""
    doi = cff.get("doi")
    where = f"Zenodo. https://doi.org/{doi}" if doi else "https://tarunv13.github.io/wildtrace/"
    return (f"{' & '.join(names)} ({str(cff.get('date-released', ''))[:4] or time.strftime('%Y')}). {title}{version} "
            f"[Computer software]. {where} (data built {time.strftime('%Y-%m-%d')}).")

def _dump(name: str, obj) -> Path:
    p = WEB_DATA / name
    p.write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":"), default=str), encoding="utf-8")
    return p


def score_records(recs):
    """Attach the listing model's P(trade signal) when a trained model exists."""
    try:
        from .classify.train import load_model, predict
        bundle = load_model()
    except Exception:
        return {}
    texts = [f"{r.title} \n {r.text}" for r in recs]
    return dict(zip([r.id for r in recs], predict(texts, bundle).round(4))) if texts else {}



def trivia(cases: list[dict], species_meta: dict) -> list[dict]:
    """Cards for the trivia box: sourced report figures, plus a few facts derived
    from this dataset.

    A derived card states something about WildTrace's own collected cases, never
    about the world, and is computed here from the same list the site publishes,
    so a figure cannot drift from what a reader can count in cases.csv. Each one
    carries the caveat that collection, not the trade, decides what is in it.
    """
    cards = yaml.safe_load((RESOURCES / "trivia.yaml").read_text(encoding="utf-8"))["cards"]
    for c in cards:
        c["kind"] = "reported"
    n = len(cases)
    if not n:
        return cards
    ours, caveat = [], ("Counted in WildTrace's own cases, which come from the newsrooms and "
                       "government sites searched, in the languages searched. It shows where "
                       "wildlife crime is reported, not where it happens.")
    counts: dict[str, int] = {}
    for c in cases:
        for sp in c.get("species", []):
            if sp == lexicon.GENERAL:  # the catch-all group says nothing worth a card
                continue
            counts[sp] = counts.get(sp, 0) + 1
    top = max(counts.items(), key=lambda kv: kv[1], default=None)
    if top and top[1] > 1:
        label = species_meta.get(top[0], {}).get("label", top[0])
        ours.append({"id": "wt_top_species", "art": "bars", "kind": "ours",
                     "fact": f"{label} appears in more WildTrace cases than any other group",
                     "detail": f"{top[1]} of {n:,} cases name it, from {len({c['place']['country'] for c in cases if c.get('place') and c.get('place', {}).get('country')})} countries in all.",
                     "caveat": caveat})
    single = sum(1 for c in cases if c.get("verification") == "single")
    if single:
        ours.append({"id": "wt_single", "art": "clock", "kind": "ours",
                     "fact": f"{round(100 * single / n)}% of cases here rest on a single report",
                     "detail": f"{single:,} of {n:,} cases have one outlet behind them. Treat those as leads: "
                               "the map pales them, and the evidence filter separates them out.",
                     "caveat": caveat})
    unmapped = sum(1 for c in cases if not c.get("place"))
    if unmapped:
        ours.append({"id": "wt_unmapped", "art": "web", "kind": "ours",
                     "fact": f"{unmapped:,} cases name no place at all",
                     "detail": f"Of {n:,} cases, {unmapped:,} could not be put on the map because no report "
                               "names a town, district or country. They are counted, not drawn.",
                     "caveat": caveat})
    return cards + ours


def stats(cases: list[dict]) -> dict:
    by = lambda f: Counter(x for c in cases for x in f(c))
    month = Counter((c["date"] or "")[:7] for c in cases if c.get("date"))
    routes = Counter(tuple(c["route"]) for c in cases if len(c.get("route") or []) == 2)
    state = Counter((c["place"] or {}).get("admin1") or (c["place"] or {}).get("name") for c in cases if c.get("place"))
    sp_state = defaultdict(Counter)
    for c in cases:
        if c.get("place"):
            for s in c["species"]:
                sp_state[s][(c["place"].get("admin1") or c["place"]["name"])] += 1
    return {
        "kpi": {
            "cases": len(cases),
            "sources": sum(c["n_sources"] for c in cases),
            "species_groups": len({s for c in cases for s in c["species"]}),
            "countries": len({c["place"]["country"] for c in cases if c.get("place")}),
            "people_arrested": sum(c["people_arrested"] or 0 for c in cases),
            "value_inr": sum(c["value_inr"] or 0 for c in cases),
            "appendix_I_cases": sum(1 for c in cases if any(
                str(lexicon.load()["groups"].get(s, {}).get("cites", "")).startswith("I") and
                not str(lexicon.load()["groups"].get(s, {}).get("cites", "")).startswith("II") for s in c["species"])),
        },
        "by_species": dict(by(lambda c: c["species"]).most_common()),
        "by_kind": dict(Counter(c["kind"] for c in cases).most_common()),
        "by_agency": dict(by(lambda c: c["agencies"]).most_common(25)),
        "by_mode": dict(by(lambda c: c["modes"]).most_common()),
        # Online trade at the enforcement end: platforms named in seizure, arrest and court reports.
        "by_platform": dict(by(lambda c: c.get("platforms") or []).most_common()),
        "online": {"cases": sum(1 for c in cases if "online" in c["modes"]),
                   "by_kind": dict(Counter(c["kind"] for c in cases if "online" in c["modes"]).most_common()),
                   "by_species": dict(by(lambda c: c["species"] if "online" in c["modes"] else []).most_common(12)),
                   "by_country": dict(Counter((c.get("place") or {}).get("country") for c in cases
                                              if "online" in c["modes"] and c.get("place")).most_common(15))},
        "by_region": dict(state.most_common(40)),
        "by_month": dict(sorted(month.items())),
        "routes": [{"from": a, "to": b, "n": n} for (a, b), n in routes.most_common(50)],
        "species_by_region": {s: dict(v.most_common(10)) for s, v in sp_state.items()},
    }


def trade_signals() -> dict:
    """Aggregate view of the WCS-OWT online-trade set (supply side). No URLs, no channels."""
    try:
        from .classify.dataset import load_labelled
        df, _ = load_labelled()
    except FileNotFoundError:
        return {}
    out = {"by_group": {}, "cues": {}}
    for gid, sub in df.groupby("group"):
        out["by_group"][gid] = {"label": lexicon.group_label(gid) if gid != "unknown" else "Unmatched",
                                "R": int(sub["y"].sum()), "IR": int((1 - sub["y"]).sum())}
    cue_counts = Counter()
    for t in df.loc[df["y"] == 1, "text"]:
        for k, v in lexicon.count_cues(t, "sale_cues").items():
            cue_counts[k] += v
    out["cues"] = dict(cue_counts)
    out["phone_in_R"] = round(float(df.loc[df["y"] == 1, "text"].str.contains(r"[6-9]\d{9}").mean()), 3)
    out["phone_in_IR"] = round(float(df.loc[df["y"] == 0, "text"].str.contains(r"[6-9]\d{9}").mean()), 3)
    out["n"] = int(len(df))
    return out


def write_csv(cases: list[dict]) -> None:
    """Flat, citable export of every published case (CC BY 4.0)."""
    import csv
    cols = ["id", "date", "kind", "verification", "summary", "species", "place", "admin1", "country", "place_precision", "lat", "lon",
            "quantities", "people_arrested", "agencies", "modes", "platforms", "n_reports", "n_outlets", "official_sources", "source_urls"]
    with open(WEB_DATA / "cases.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(cols)
        for c in cases:
            p = c.get("place") or {}
            w.writerow([c["id"], c["date"], c["kind"], c["verification"], c["summary"], ";".join(c["species"]), p.get("name", ""),
                        p.get("admin1", ""), p.get("country", ""), ("inferred from publisher" if c.get("place_basis") == "outlet" else p.get("type", "")),
                        p.get("lat", ""), p.get("lon", ""), ";".join(f"{q['value']:g} {q['unit']}" for q in c.get("quantities") or []),
                        c.get("people_arrested") or "", ";".join(c["agencies"]), ";".join(c["modes"]), ";".join(c.get("platforms") or []), c["n_sources"], c.get("n_outlets", ""),
                        sum(1 for s in c["sources"] if s["tier"] == "official"), " ".join(s["url"] for s in c["sources"])])


def live_listings(listings, scores) -> dict:
    """Aggregate freshly collected online listings (YouTube etc.). Public output is
    counts only: per species group and month, split by the classifier's decision.
    Titles, channels and URLs stay private; unverified codeword hits go to a
    private review file."""
    try:
        from .classify.train import load_model
        thr = float(load_model()["threshold"])
    except Exception:
        thr = None
    by_group: dict[str, dict[str, int]] = defaultdict(lambda: {"flagged": 0, "not_flagged": 0, "unscored": 0})
    by_month: Counter = Counter()
    review = []
    for r in listings:
        text = f"{r.title} {r.text}"
        groups = lexicon.species_groups(text) or ["unknown"]
        p = scores.get(r.id)
        key = "unscored" if p is None or thr is None else ("flagged" if p >= thr else "not_flagged")
        for g in groups:
            by_group[g][key] += 1
        when = r.published or (r.extra or {}).get("seen", "")
        if key == "flagged" and when:
            by_month[when[:7]] += 1
        hits = lexicon.codeword_hits(text)
        if hits:
            review.append({"id": r.id, "url": r.url, "title": r.title, "p_relevant": p,
                           "codewords": ";".join(h["term"] for h in hits)})
    if review:
        import csv
        with open(LABELS / "codeword_review.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(review[0])); w.writeheader(); w.writerows(review)
    return {"n": len(listings), "threshold": thr, "by_group": dict(by_group), "flagged_by_month": dict(sorted(by_month.items())),
            "codeword_flags": len(review)}


def ambiguous_review(records, candidate_ids: set[str]) -> None:
    """Every ambiguous-term hit (accepted or held) in every screened record, for human review.
    Private (data/labels, gitignored): it carries headlines. Reviewers mark `verdict` right/wrong;
    the counts per term show which context rules to tighten or loosen."""
    import csv
    rows = []
    for r in records:
        for h in lexicon.ambiguous_hits(f"{r.title} {r.text}"):
            rows.append({"id": r.id, "date": r.published, "title": r.title[:200], "term": h["term"], "group": h.get("group") or "",
                         "cue": h.get("cue") or "", "accepted": h["accepted"], "context": ";".join(h["context"]),
                         "became_candidate": r.id in candidate_ids, "verdict": ""})
    LABELS.mkdir(parents=True, exist_ok=True)
    with open(LABELS / "ambiguous_review.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]) if rows else ["id"]); w.writeheader(); w.writerows(rows)
    by = Counter((x["term"], x["accepted"]) for x in rows)
    print(f"  ambiguous terms: {len(rows)} hits; " + ", ".join(f"{t} {'kept' if a else 'held'} {n}" for (t, a), n in by.most_common(10)))


def enrich(cands, limit: int = 200) -> None:
    """Add article ledes to headline-only candidates (private; cached in data/interim)."""
    from .collect.article import lede
    path = INTERIM / "ledes.json"
    cache = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    todo = [r for r in cands if not r.text and r.id not in cache][:limit]
    for i, r in enumerate(todo, 1):
        cache[r.id] = lede(r.url)
        if i % 10 == 0:
            print(f"  enriched {i}/{len(todo)}")
    path.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    for r in cands:
        if not r.text and cache.get(r.id):
            r.text = cache[r.id]


def build(min_relevance: float | None = None, fetch_text: bool = True) -> dict:
    ensure_dirs()
    recs = read_all_raw()
    news = [r for r in recs if r.kind in ("news", "official", "court")]  # "official": government releases
    listings = [r for r in recs if r.kind in ("listing", "video")]
    scores = score_records(news + listings)

    # Published window: from MIN_DATE on (older records stay in the private raw archive).
    # Research and project-information portals describe projects, not enforcement events.
    from .sources_tier import domain as _dom
    news = [r for r in news if not r.published or r.published >= MIN_DATE]
    news = [r for r in news if _dom((r.extra or {}).get("source_url") or r.url) not in NOT_EVENTS]
    cand = [r for r in news if is_enforcement_candidate(f"{r.title} {r.text}")]
    ambiguous_review(news, {r.id for r in cand})
    if fetch_text:
        enrich(cand)
    events = []
    for r in cand:
        e = extract(r)
        e.trade_signal = float(scores[r.id]) if r.id in scores else None
        events.append(e)
    with open(INTERIM / "events.jsonl", "w", encoding="utf-8") as f:
        for e in events:
            f.write(json.dumps(e.to_dict(), ensure_ascii=False) + "\n")

    cases = [summarise(g) for g in cluster(events)]
    # Human review (resources/validations.yaml) outranks every automatic status.
    vpath = RESOURCES / "validations.yaml"
    reviews = (yaml.safe_load(vpath.read_text(encoding="utf-8")) or {}) if vpath.exists() else {}
    cases = [c for c in cases if (reviews.get(c["id"]) or {}).get("status") != "rejected"]
    for c in cases:
        r = reviews.get(c["id"]) or {}
        if r.get("status") == "validated":
            c["verification"] = "validated"
            c["review"] = {k: str(r.get(k, "")) for k in ("reviewer", "date", "note")}
    cases.sort(key=lambda c: c.get("date") or "", reverse=True)
    for c in cases:
        c["summary"] = scrub(c["summary"])

    # Coordinates for both ends of reported routes (the map draws them as arcs).
    from .extract.events import gazetteer as _gaz
    gz = _gaz()
    def _pt(name):
        hit = gz.get(name.lower())
        return [hit[0].lon, hit[0].lat] if hit else None
    for c in cases:
        if len(c.get("route") or []) == 2:
            a, b = _pt(c["route"][0]), _pt(c["route"][1])
            c["route_coords"] = [a, b] if a and b else None

    G = graph.build(cases)
    assert_public_safe(cases, "cases")

    geo = {"type": "FeatureCollection", "features": [
        {"type": "Feature", "geometry": {"type": "Point", "coordinates": [c["place"]["lon"], c["place"]["lat"]]},
         "properties": {"id": c["id"], "kind": c["kind"], "date": c["date"], "summary": c["summary"],
                        "species": ",".join(c["species"]), "n_sources": c["n_sources"],
                        "country": c["place"]["country"], "level": c["place"]["type"],
                        "basis": c.get("place_basis", "text")}}
        for c in cases if c.get("place")]}

    with open(RESOURCES / "sources.yaml", encoding="utf-8") as f:
        registry = yaml.safe_load(f)["sources"]
    lex = lexicon.load()["groups"]
    species_meta = {gid: {"label": g["label"], "taxa": g.get("taxa", []), "cites": g.get("cites"),
                          "products": g.get("products", []), "uses": g.get("uses", []),
                          "terms": {k: v for k, v in g["terms"].items()},
                          "kingdom": "plant" if gid in FLORA else "animal"} for gid, g in lex.items()}
    report = {}
    if (MODELS / "relevance_report.json").exists():
        report = json.loads((MODELS / "relevance_report.json").read_text(encoding="utf-8"))
        report.pop("review_queue", None)

    s = stats(cases)
    meta = {"built": time.strftime("%Y-%m-%d %H:%M"), "records_seen": len(recs), "news_records": len(news),
            "licence": "CC BY 4.0 (data) · MIT (code)",
            "cite": _cite(),
            "coverage": {"mapped": sum(1 for c in cases if c.get("place") and c["place"]["type"] != "country"),
                         "country_only": sum(1 for c in cases if c.get("place") and c["place"]["type"] == "country"),
                         "unmapped": sum(1 for c in cases if not c.get("place"))},
            "verification": dict(Counter(c["verification"] for c in cases)),
            "source_tiers": dict(Counter(src["tier"] for c in cases for src in c["sources"])),
            "listing_records": len(listings), "by_source": dict(Counter(r.source for r in recs)),
            "candidates": len(cand), "cases": len(cases), "version": "0.1.0",
            "window": [min((c["date"] for c in cases if c.get("date")), default=""),
                       max((c["date"] for c in cases if c.get("date")), default="")]}

    # Guard: a thin archive (a failed restore, a blocked source) must never shrink the live site.
    old = WEB_DATA / "cases.json"
    if old.exists() and not os.environ.get("WILDTRACE_ALLOW_SHRINK"):
        n_old = len(json.loads(old.read_text(encoding="utf-8")))
        if len(cases) < 0.9 * n_old:
            raise SystemExit(f"refusing to publish: {len(cases)} cases against {n_old} live (more than 10% fewer). "
                             "Check the record archive, or set WILDTRACE_ALLOW_SHRINK=1 if the drop is intended.")
    _dump("cases.json", cases); _dump("cases.geojson", geo); _dump("stats.json", s)
    write_csv(cases)
    _dump("species.json", species_meta); _dump("sources.json", registry); _dump("meta.json", meta)
    # Country index: code -> name + capital point + bounding box of its cases.
    countries = {}
    for places in gz.values():
        for pl in places:
            if pl.type == "country" and pl.country not in countries:
                countries[pl.country] = {"name": pl.name, "lon": pl.lon, "lat": pl.lat}
    # Territories the gazetteer lacks but CITES records name (Hong Kong, Israel, Kosovo, Macao).
    for cc, pt in json.loads((RESOURCES / "country_points.json").read_text(encoding="utf-8"))["points"].items():
        countries.setdefault(cc, pt)
    # Trade region (UN M49 sub-regions grouped into eight): the Flows lens colours by it.
    regions = json.loads((RESOURCES / "regions.json").read_text(encoding="utf-8"))
    for cc, c in countries.items():
        c["region"] = regions["countries"].get(cc, "other")
    _dump("countries.json", countries)
    _dump("regions.json", {"source": regions["source"], "regions": regions["regions"]})
    obs = yaml.safe_load((RESOURCES / "observatories.yaml").read_text(encoding="utf-8"))
    _dump("observatories.json", obs)
    # Outlet and organisation icons (self-hosted; fetched once, only for new domains).
    from . import logos
    try:
        logos.update(cases, obs.get("observatories", []))
    except Exception as e:   # a logo outage must never stop a data refresh
        print(f"  logos skipped: {e}")
    _dump("codewords.json", [{k: v for k, v in c.items()} for c in lexicon.codewords()])
    _dump("trivia.json", trivia(cases, species_meta))
    # CI has no private data or model: keep the last published aggregates instead of blanking them.
    ts = trade_signals()
    old_ts = WEB_DATA / "trade_signals.json"
    if not ts and old_ts.exists():  # CI: no private data, keep the published OWT aggregates
        ts = json.loads(old_ts.read_text(encoding="utf-8"))
    ts["live"] = live_listings(listings, scores)
    _dump("trade_signals.json", ts)
    if report or not (WEB_DATA / "model_report.json").exists():
        _dump("model_report.json", report)
    graph.export(G, WEB_DATA)
    # The static, crawlable layer: one page per case, species and country, plus sitemap and robots.
    from .seo import build_pages
    n_pages = build_pages(cases, species_meta, countries, meta, WEB_DATA.parent)
    print(f"  static pages: {n_pages}")
    print(f"built: {len(recs)} records -> {len(cand)} enforcement candidates -> {len(cases)} cases; "
          f"graph {G.number_of_nodes()} nodes / {G.number_of_edges()} links -> {WEB_DATA}")
    return meta
