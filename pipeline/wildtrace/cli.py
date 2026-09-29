"""Command line.

  wildtrace train   [--target-recall 0.98] [--embed]    train + evaluate relevance model
  wildtrace collect [--countries IN,TH,VN] [--gnews] [--youtube] [--timespan 3m]
  wildtrace build                                        extract cases, publish web/data
  wildtrace run                                          collect + build
  wildtrace cites   <folder>                             CITES supply -> demand flows (web/data/flows.json)
  wildtrace captive <folder>                             captive-bred claims in CITES trade (web/data/captive_claims.json)
  wildtrace ecosolve <csv>                               ECO-SOLVE adverts vs WildTrace cases (web/data/online_gap.json)
  wildtrace vision  <image|folder> [--captions csv]       OCR + BioCLIP species evidence for images (private)
  wildtrace lemis   <folder> [--taxonomy <codebook>]     US LEMIS seizures by origin + product (web/data/lemis.json)
  wildtrace zoonoses [--offline]                         VIRION + WHO outbreaks (web/data/zoonoses.json)
  wildtrace relabel                                      merge reviewed labels into corrections.csv
  wildtrace codebook <zip>                               merge PMC8579131 multilingual names (CC BY)
  wildtrace gazetteer                                    build GeoNames place index (CC-BY)
  wildtrace doctor                                       show which sources/tools are available
"""
from __future__ import annotations

import argparse
import shutil
import sys


def _collect(a) -> None:
    from .collect import feeds, gdelt
    from .collect.base import write_jsonl
    countries = [c.strip().upper() for c in a.countries.split(",") if c.strip()]
    # Fast, reliable sources first; GDELT (heavily throttled) last.
    print("RSS feeds")
    print("  ->", write_jsonl(feeds.collect_feeds(), "feeds"))
    if a.gnews:
        eds = list(feeds.GNEWS_EDITIONS) if "ALL" in countries else [c for c in feeds.GNEWS_EDITIONS if c.split("-")[0] in countries]
        print(f"Google News RSS: {eds}")
        groups = {g.strip() for g in (getattr(a, "groups", "") or "").split(",") if g.strip()} or None
        print("  ->", write_jsonl(feeds.collect_gnews(eds, when=a.gnews_window, groups=groups), "gnews"))
        if getattr(a, "online", False):
            print("Google News: online wildlife crime (platforms, social media)")
            print("  ->", write_jsonl(feeds.collect_gnews_online(eds, when=a.gnews_window), "gnews"))
    if a.youtube:
        from .collect import social
        print("YouTube (yt-dlp, metadata only)")
        print("  ->", write_jsonl(social.collect_youtube(), "youtube"))
    if getattr(a, "official", False):
        print("Official sources (government, enforcement, judicial domains)")
        print("  ->", write_jsonl(feeds.collect_official(), "official"))
    if getattr(a, "history", 0):
        print(f"History backfill: {a.history} months")
        print("  ->", write_jsonl(feeds.collect_history(a.history), "history"))
    if getattr(a, "no_gdelt", False):
        return
    print(f"GDELT: {countries}")
    print("  ->", write_jsonl(gdelt.collect(countries, a.timespan), "gdelt"))


def _relabel() -> None:
    import pandas as pd
    from .config import LABELS
    q = LABELS / "review_queue.csv"
    if not q.exists():
        sys.exit("no review queue yet: run `wildtrace train` first")
    df = pd.read_csv(q, dtype=str).fillna("")
    done = df[df["new_label"].str.upper().isin(["R", "IR"])][["id", "new_label"]].rename(columns={"new_label": "label"})
    done["label"] = done["label"].str.upper()
    path = LABELS / "corrections.csv"
    if path.exists():
        old = pd.read_csv(path, dtype=str)
        done = pd.concat([old, done]).drop_duplicates("id", keep="last")
    done.to_csv(path, index=False)
    print(f"{len(done)} corrections in {path}. Run `wildtrace train` again.")


def _doctor() -> None:
    from .collect.social import agent_reach_channels
    from .config import MODELS, WCS_OWT_DIR
    print("yt-dlp       :", shutil.which("yt-dlp") or "missing (pip install yt-dlp)")
    print("agent-reach  :", shutil.which("agent-reach") or "missing (optional)")
    ch = agent_reach_channels()
    if ch:
        print("  channels   :", ", ".join(k for k, ok in ch.items() if ok))
    print("WCS-OWT dir  :", WCS_OWT_DIR, "(found)" if WCS_OWT_DIR.exists() else "(missing: set WILDTRACE_WCS_OWT_DIR)")
    print("model        :", "trained" if (MODELS / "relevance.joblib").exists() else "not trained")
    try:
        import sentence_transformers  # noqa: F401
        print("embeddings   : available (--embed)")
    except ImportError:
        print("embeddings   : pip install sentence-transformers")


def main(argv=None) -> None:
    p = argparse.ArgumentParser("wildtrace", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("train"); t.add_argument("--target-recall", type=float, default=0.98)
    t.add_argument("--embed", action="store_true"); t.add_argument("--repeats", type=int, default=2)
    for name in ("collect", "run"):
        c = sub.add_parser(name)
        c.add_argument("--countries", default="IN,NP,BD,MM,TH,VN,MY,ID,PH")
        c.add_argument("--timespan", default="3m")
        c.add_argument("--gnews", action="store_true", help="opt-in: Google News RSS (personal-use terms)")
        c.add_argument("--youtube", action="store_true", help="opt-in: YouTube listing search via yt-dlp")
        c.add_argument("--official", action="store_true", help="search government / enforcement / judicial domains")
        c.add_argument("--history", type=int, default=0, help="backfill this many past months (Google News date ranges)")
        c.add_argument("--no-gdelt", action="store_true", help="skip GDELT (heavily throttled)")
        c.add_argument("--online", action="store_true", help="also search for online wildlife crime reaching enforcement")
        c.add_argument("--groups", default="", help="limit the news search to these species groups (comma-separated)")
        c.add_argument("--gnews-window", default="30d", help="how far back Google News searches reach (daily runs use 3d)")
    mi = sub.add_parser("mine", help="mine the research literature for taxa, trade names and datasets")
    mi.add_argument("--topics", default="all", help="all | flora | fauna | codewords | datasets (comma-separated)")
    mi.add_argument("--pages", type=int, default=2, help="pages per query, 50-100 papers each")
    b = sub.add_parser("build"); b.add_argument("--no-fetch", action="store_true", help="skip fetching article ledes")
    sub.add_parser("relabel"); sub.add_parser("doctor"); sub.add_parser("gazetteer")
    ci = sub.add_parser("cites"); ci.add_argument("folder")
    cp = sub.add_parser("captive"); cp.add_argument("folder")
    ec = sub.add_parser("ecosolve"); ec.add_argument("csv")
    vi = sub.add_parser("vision"); vi.add_argument("path"); vi.add_argument("--captions", default="", help="CSV with image,caption")
    le = sub.add_parser("lemis"); le.add_argument("folder")
    le.add_argument("--taxonomy", default="", help="PMC8579131 zip or folder (genus -> family/order), improves matching")
    le.add_argument("--min-year", type=int, default=2000)
    zo = sub.add_parser("zoonoses"); zo.add_argument("--offline", action="store_true", help="use the files already in data/raw/zoonoses")
    cb = sub.add_parser("codebook"); cb.add_argument("source", help="PMC8579131 zip or unzipped folder")
    a = p.parse_args(argv)

    if a.cmd == "train":
        from .classify.train import train
        train(a.target_recall, a.embed, repeats=a.repeats)
    elif a.cmd == "collect":
        _collect(a)
    elif a.cmd == "mine":
        from .collect.literature import mine
        mine(a.topics, a.pages)
    elif a.cmd == "build":
        from .publish import build
        build(fetch_text=not a.no_fetch)
    elif a.cmd == "run":
        _collect(a)
        from .publish import build
        build()
    elif a.cmd == "cites":
        from .collect.cites import aggregate, publish_flows
        print(publish_flows(aggregate(a.folder)))
    elif a.cmd == "captive":
        from .collect.captive import aggregate as captive_aggregate, publish as captive_publish
        print(captive_publish(captive_aggregate(a.folder)))
    elif a.cmd == "ecosolve":
        import json as _json
        from .config import WEB_DATA
        from .collect.ecosolve import aggregate as eco_aggregate, publish as eco_publish
        cases = _json.loads((WEB_DATA / "cases.json").read_text(encoding="utf-8"))
        print(eco_publish(eco_aggregate(a.csv, cases)))
    elif a.cmd == "vision":
        import csv as _csv
        from .classify.vision import run as vision_run
        caps = {r["image"]: r["caption"] for r in _csv.DictReader(open(a.captions, encoding="utf-8"))} if a.captions else None
        print(vision_run(a.path, caps))
    elif a.cmd == "lemis":
        from .collect.lemis import aggregate as lemis_aggregate, publish as lemis_publish
        print(lemis_publish(lemis_aggregate(a.folder, a.taxonomy or None, a.min_year)))
    elif a.cmd == "zoonoses":
        from .collect.zoonoses import build as build_zoonoses
        build_zoonoses(a.offline)
    elif a.cmd == "codebook":
        from .extract.codebook import build as build_codebook
        build_codebook(a.source)
    elif a.cmd == "relabel":
        _relabel()
    elif a.cmd == "gazetteer":
        from .extract.gazetteer_build import build as build_gazetteer
        build_gazetteer()
    elif a.cmd == "doctor":
        _doctor()


if __name__ == "__main__":
    main()
