"""Measured accuracy: a random sample of published cases, judged against their sources.

    wildtrace accuracy sample --n 200 --seed 29      # writes data/labels/audit_<date>.csv to fill in
    wildtrace accuracy score data/labels/audit_<date>.csv

A reviewer reads each sampled case's headlines and fills four columns: `relevant` (y/n: a real
wildlife-trade seizure, arrest, conviction or trade-linked rescue), `species_ok`, `kind_ok`,
`country_ok` (y/n, or blank when not applicable), plus an `error` class for any "n". `score`
computes precision with a 95% Wilson interval and writes web/data/accuracy.json (shown on the site)
and docs/ACCURACY.md. The label file stays private (it holds headlines); only the counts are public.

Precision is measured. Recall (events WildTrace misses) is not, and the site says so.
"""
from __future__ import annotations

import csv
import json
import math
import random
from collections import Counter
from datetime import date
from pathlib import Path

from .config import INTERIM, LABELS, WEB_DATA

COLS = ["case_id", "kind", "species", "country", "headline", "relevant", "species_ok", "kind_ok", "country_ok", "error"]


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if not n:
        return 0.0, 0.0
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def sample(n: int = 200, seed: int = 29) -> Path:
    cases = json.loads((WEB_DATA / "cases.json").read_text(encoding="utf-8"))
    titles = {}
    ev = INTERIM / "events.jsonl"
    if ev.exists():
        for line in ev.read_text(encoding="utf-8").split("\n"):
            if line.strip():
                d = json.loads(line)
                titles[d["url"]] = d["title"]
    rng = random.Random(seed)
    pick = rng.sample(cases, min(n, len(cases)))
    path = LABELS / f"audit_{date.today():%Y-%m-%d}_seed{seed}.csv"
    LABELS.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        for c in pick:
            w.writerow({"case_id": c["id"], "kind": c["kind"], "species": ";".join(c["species"]),
                        "country": (c.get("place") or {}).get("country", ""),
                        "headline": " || ".join(titles.get(s["url"], "") for s in c["sources"][:2])})
    return path


def score(path: str | Path, method: str = "") -> dict:
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    yes = lambda v: (v or "").strip().lower() in ("y", "yes", "1", "true")
    judged = [r for r in rows if (r.get("relevant") or "").strip()]
    rel = [r for r in judged if yes(r["relevant"])]
    def share(col):
        pool = [r for r in rel if (r.get(col) or "").strip()]
        return (sum(1 for r in pool if yes(r[col])) / len(pool)) if pool else None   # not measured
    lo, hi = wilson(len(rel), len(judged))
    errors = Counter((r.get("error") or "other").strip() for r in judged if not yes(r["relevant"]))
    out = {"date": f"{date.today():%Y-%m-%d}", "n": len(judged), "relevant": len(rel),
           "precision": len(rel) / len(judged) if judged else 0.0, "ci": [lo, hi],
           "species_ok": share("species_ok"), "kind_ok": share("kind_ok"), "country_ok": share("country_ok"),
           "errors": dict(errors.most_common()),
           "method": method or "blind random sample of published cases, each judged against its source headlines by a reviewer"}
    (WEB_DATA / "accuracy.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    return out
