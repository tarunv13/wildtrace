"""CITES Trade Database: where traded wildlife comes from and where it goes.

Download the full database from https://trade.cites.org/ (``Download`` → full
database, a zip of CSVs, updated yearly), unzip it anywhere, and run

    wildtrace cites path/to/Trade_database_download_vYYYY.1

The loader streams every shipment worldwide, maps taxa onto the lexicon's species
groups, and aggregates two layers for web/data/flows.json:

* seized: shipments with Source code ``I`` (confiscated or seized specimens), kept
  as origin → exporter → importer, the closest open record of illegal flows;
* declared: all other reported trade, exporter → importer, the legal baseline.

Individual shipments and permit identifiers are never published, only counts.
Recommended citation (UNEP-WCMC): Full CITES Trade Database Download. Version YYYY.1.
Compiled by UNEP-WCMC, Cambridge, UK for the CITES Secretariat, Geneva, Switzerland.
"""
from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from .. import lexicon
from ..config import WEB_DATA

MIN_YEAR = 2015
DECLARED_TOP = 60   # declared-trade corridors kept per species group (the file stays small)
# Ranks that are not CITES ranks, or families a group implies but does not list.
# The groups' labels are broader than the Indian species their `taxa` lists name (news matching
# relies on those lists staying narrow), so trade records use these wider ranks too.
EXTRA_HIGHER = {"elasmobranchii": "shark_ray", "manidae": "pangolin", "testudines": "turtles", "varanus": "monitor_lizard",
                "elephantidae": "elephant", "rhinocerotidae": "rhino", "ursidae": "bear", "moschidae": "musk_deer",
                "psittaciformes": "birds", "crocodylia": "pythons_reptiles", "crocodilia": "pythons_reptiles", "alligatoridae": "pythons_reptiles", "pythonidae": "pythons_reptiles",
                "primates": "primates", "anguillidae": "eels", "antipatharia": "sea_fan", "corallium": "sea_fan"}


def taxon_index() -> tuple[dict[str, str], dict[str, str]]:
    """species name -> group, and higher taxon (genus/family/order/class) -> group.
    The first group to list a taxon keeps it, so a specific group beats a catch-all."""
    species, higher = {}, {}
    for gid, g in lexicon.load()["groups"].items():
        for t in g.get("taxa", []):
            m = re.search(r"\(([^)]+)\)", t)       # "Tree ferns (Cyatheaceae)" -> Cyatheaceae
            t = (m.group(1) if m else t).replace(" spp.", "").strip().lower()
            (species if " " in t else higher).setdefault(t, gid)
    for k, v in EXTRA_HIGHER.items():
        higher.setdefault(k, v)
    return species, higher


def group_of(row: dict, species: dict, higher: dict) -> str | None:
    g = species.get((row.get("Taxon") or "").strip().lower())
    if g:
        return g
    for col in ("Genus", "Family", "Order", "Class"):
        g = higher.get((row.get(col) or "").strip().lower())
        if g:
            return g
    return None


def aggregate(folder: Path | str, min_year: int = MIN_YEAR) -> dict:
    species, higher = taxon_index()
    seized, seized_years, declared = Counter(), Counter(), Counter()
    # The evidence behind each seized route (origin -> importer): what, when, reported by whom.
    detail = defaultdict(lambda: {"years": Counter(), "taxa": Counter(), "terms": Counter(), "reporter": Counter(),
                                  "purpose": Counter(), "via": Counter(), "groups": Counter()})
    files = sorted(Path(folder).glob("*.csv"))
    if not files:
        raise SystemExit(f"no CSV files in {folder}: unzip the CITES download there first")
    version = next((m.group(1) for f in Path(folder).glob("*.zip") if (m := re.search(r"v(\d{4}\.\d)", f.name))), "")
    for f in files:
        with open(f, encoding="utf-8", errors="replace", newline="") as fh:
            for r in csv.DictReader(fh):
                try:
                    y = int(r["Year"])
                except (TypeError, ValueError):
                    continue
                if y < min_year:
                    continue
                exp, imp = (r.get("Exporter") or "").strip(), (r.get("Importer") or "").strip()
                if not exp or not imp or exp == imp:
                    continue
                g = group_of(r, species, higher)
                if not g:
                    continue
                if (r.get("Source") or "").strip() == "I":
                    org = (r.get("Origin") or "").strip() or exp
                    seized[(g, org, exp, imp)] += 1
                    seized_years[(g, y)] += 1
                    d = detail[f"{org}|{imp}"]
                    d["years"][y] += 1; d["groups"][g] += 1
                    d["taxa"][(r.get("Taxon") or "").strip()] += 1
                    d["terms"][(r.get("Term") or "").strip()] += 1
                    d["reporter"][(r.get("Reporter.type") or "").strip()] += 1
                    d["purpose"][(r.get("Purpose") or "").strip()] += 1
                    if exp != org:
                        d["via"][exp] += 1
                else:
                    declared[(g, exp, imp)] += 1
        print(f"  {f.name}: {sum(seized.values()):,} seized, {sum(declared.values()):,} declared so far")
    per_group = defaultdict(list)
    for (g, e, i), n in declared.most_common():
        if len(per_group[g]) < DECLARED_TOP:
            per_group[g].append([e, i, n])
    declared_tot = Counter()
    for (g, _, _), n in declared.items():
        declared_tot[g] += n
    return {
        "source": "CITES Trade Database (UNEP-WCMC for the CITES Secretariat)",
        "version": version, "year_min": min_year,
        "cite": f"Full CITES Trade Database Download. Version {version or 'YYYY.1'}. Compiled by UNEP-WCMC, Cambridge, UK "
                "for the CITES Secretariat, Geneva, Switzerland. Available at: trade.cites.org.",
        "licence": "Derived from the CITES Trade Database; reuse under its terms (non-commercial, with attribution), not CC BY.",
        "note": "Counts are shipment records, not quantities. Seized = source code I (confiscated or seized specimens). "
                "Reporting is uneven: some Parties report seizures far more completely than others.",
        # [group, origin, exporter, importer, shipments]; origin XX = not recorded
        "seized": [[g, o, e, i, n] for (g, o, e, i), n in seized.most_common()],
        "seized_years": [[g, y, n] for (g, y), n in sorted(seized_years.items())],
        # [group, exporter, importer, shipments], top corridors per group; totals below
        "declared": {g: rows for g, rows in per_group.items()},
        "declared_total": dict(declared_tot),
        # Per seized route "origin|importer": the records behind the line on the map.
        "detail": {k: {"years": dict(sorted(v["years"].items())), "taxa": v["taxa"].most_common(6),
                       "terms": v["terms"].most_common(6), "reporter": dict(v["reporter"]),
                       "purpose": dict(v["purpose"].most_common(4)), "via": v["via"].most_common(4),
                       "groups": v["groups"].most_common(4)} for k, v in detail.items()},
    }


def publish_flows(data: dict, out: Path = WEB_DATA) -> Path:
    path = out / "flows.json"
    # The per-route evidence is only needed when a reader opens a route: it ships separately.
    detail = data.pop("detail", None)
    path.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
    if detail is not None:
        (out / "flows_detail.json").write_text(json.dumps(detail, separators=(",", ":")), encoding="utf-8")
    # The same counts as flat tables, for spreadsheets and R/Python users.
    with open(out / "cites_seized_flows.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["species_group", "origin", "exporter", "importer", "seized_shipments"])
        w.writerows(data["seized"])
    with open(out / "cites_declared_flows.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["species_group", "exporter", "importer", "declared_shipments"])
        w.writerows([g, *row] for g, rows in data["declared"].items() for row in rows)
    return path


def load(folder):  # kept for the CLI's older call shape
    return aggregate(folder)
