"""Offered online vs caught: ECO-SOLVE adverts set against WildTrace enforcement cases.

ECO-SOLVE (Global Initiative Against Transnational Organized Crime, EU-funded) records adverts for
protected wildlife on online platforms through regional data hubs, and publishes its advert table on
its public dashboard (https://www.ecosolve.eco/dashboard, "download"). WildTrace records where trade
met enforcement. This module maps each advert to a WildTrace species group and counts, per group and
country, adverts against enforcement cases in the same period.

The ratio is not a detection rate: the two sources watch different things with different effort, and
ECO-SOLVE's hubs choose their species and platforms. It shows where wildlife is openly offered while
little reaches the news record of seizures and arrests, which is where to look next.

Only aggregated counts are published (web/data/online_gap.json, .csv), attributed to ECO-SOLVE. The
advert rows stay in data/raw/ecosolve, which is not published. The advert table carries no seller
names, handles or links.

    wildtrace ecosolve data/raw/ecosolve/adverts-data.csv
"""
from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

from .. import lexicon
from ..config import WEB_DATA

# Names in ECO-SOLVE's "sold_in" that are not plain country names.
NAME_TO_CC = {"Czechia": "CZ", "Viet Nam": "VN", "Vietnam": "VN", "Türkiye": "TR", "Turkey": "TR", "Russia": "RU",
              "South Korea": "KR", "Ivory Coast": "CI", "Côte d'Ivoire": "CI", "United States": "US", "United Kingdom": "GB",
              "Laos": "LA", "DR Congo": "CD", "Democratic Republic of the Congo": "CD", "Bolivia": "BO", "Iran": "IR"}
# Advert names the lexicon cannot place, mapped by hand (checked against the most frequent names).
NAME_TO_GROUP = {"elephant": "elephant", "ivory (unspecified)": "elephant", "tiger": "tiger", "lion": "lion", "jaguar": "jaguar",
                 "leopard": "leopard", "bear": "bear", "pangolin": "pangolin", "pangolin spp.": "pangolin", "shark": "shark_ray",
                 "seahorse (hippocampus)": "shark_ray", "himalayan musk deer": "musk_deer", "rhinoceros": "rhino",
                 "bengal monitor": "monitor_lizard", "tokay gecko": "tokay_gecko", "cheetah": "cheetah"}
WEBSITE_TO_GROUP = {"Pangolins": "pangolin", "Parrots": "birds", "Parakeets": "birds", "Songbirds": "birds", "Owls": "owl",
                    "Hornbills": "hornbill", "Primates": "primates", "Monkeys": "primates", "Tortoises": "turtles",
                    "Turtles": "turtles", "Sea turtles": "turtles", "Sharks, rays": "shark_ray", "Seahorses": "shark_ray",
                    "Sea cucumbers": "shark_ray", "Bears": "bear", "Snakes": "pythons_reptiles", "Crocodiles": "pythons_reptiles",
                    "Crocodilians": "pythons_reptiles", "Eels": "eels", "Corals": "sea_fan", "Sea fans": "sea_fan",
                    "Musk deer": "musk_deer", "Elephants": "elephant", "Ivory (unspecified)": "elephant", "Rhinos": "rhino"}


def _cc_index() -> dict[str, str]:
    idx = {}
    path = WEB_DATA / "countries.json"
    if path.exists():
        for cc, c in json.loads(path.read_text(encoding="utf-8")).items():
            if c.get("name"):
                idx[c["name"].lower()] = cc
    idx.update({k.lower(): v for k, v in NAME_TO_CC.items()})
    return idx


def group_for(name: str, website: str) -> str | None:
    n = (name or "").strip().lower()
    if n in NAME_TO_GROUP:
        return NAME_TO_GROUP[n]
    if "monitor" in n:
        return "monitor_lizard"
    if "lion" in n and "mountain" not in n:
        return "lion"
    hits = [g for g in lexicon.species_groups(name or "") if g != lexicon.GENERAL]
    if hits:
        return hits[0]
    return WEBSITE_TO_GROUP.get((website or "").strip())


def aggregate(csv_path: Path | str, cases: list[dict]) -> dict:
    cc_of = _cc_index()
    rows = list(csv.DictReader(open(csv_path, encoding="utf-8", errors="replace", newline="")))
    dates = sorted(r["record_date"] for r in rows if (r.get("record_date") or "")[:2] == "20")
    start, end = dates[0], dates[-1]
    ads = Counter()
    ads_group, ads_country, platforms, types = Counter(), Counter(), Counter(), Counter()
    unmatched = Counter()
    for r in rows:
        g = group_for(r.get("item_common_name", ""), r.get("item_common_name_website", ""))
        cc = cc_of.get((r.get("sold_in") or "").strip().lower(), "")
        if not g:
            unmatched[r.get("item_common_name", "")] += 1
            g = "unmatched"
        ads[(g, cc)] += 1
        ads_group[g] += 1
        if cc:
            ads_country[cc] += 1
        platforms[(r.get("platform") or "").strip()] += 1
        types[(r.get("item_type") or "").strip()] += 1
    # WildTrace cases in the same window, by group and country.
    win = [c for c in cases if c.get("date") and start <= c["date"] <= end]
    caught = Counter()
    for c in win:
        cc = (c.get("place") or {}).get("country", "")
        for s in c.get("species", []):
            caught[(s, cc)] += 1
    hub_cc = {cc for (_, cc) in ads if cc}
    pairs = []
    for (g, cc), n in ads.items():
        if not cc or g == "unmatched" or n < 20:
            continue
        pairs.append({"group": g, "country": cc, "adverts": n, "cases": caught.get((g, cc), 0),
                      "adverts_per_case": round(n / caught[(g, cc)], 1) if caught.get((g, cc)) else None})
    pairs.sort(key=lambda p: (p["cases"] > 0, -(p["adverts"] / (p["cases"] + 1))))
    by_group = [{"group": g, "adverts": n,
                 "cases_in_hub_countries": sum(v for (s, cc), v in caught.items() if s == g and cc in hub_cc)}
                for g, n in ads_group.most_common() if g != "unmatched"]
    print(f"  {len(rows):,} adverts, {start} to {end}; unmatched names (top): {unmatched.most_common(8)}")
    return {
        "source": "ECO-SOLVE Global Monitoring System (Global Initiative Against Transnational Organized Crime; EU Global Illicit Flows Programme)",
        "url": "https://www.ecosolve.eco/dashboard",
        "cite": "ECO-SOLVE Global Monitoring System, advert data, downloaded from https://www.ecosolve.eco/dashboard; "
                "Global Initiative Against Transnational Organized Crime.",
        "licence": "Aggregated counts derived from ECO-SOLVE's public dashboard data, with attribution; the advert rows are not redistributed.",
        "note": "Adverts and cases measure different things with different effort: ECO-SOLVE hubs choose their species and "
                "platforms, and WildTrace counts what reached public reporting. A high ratio shows where wildlife is offered "
                "openly while little reaches the record of seizures and arrests. It is not a detection rate.",
        "window": [start, end], "adverts": len(rows), "species_names": len({r.get("item_common_name") for r in rows}),
        "hubs": sorted({(r.get("datahub") or "").strip() for r in rows if (r.get("datahub") or "").strip() not in ("", "Management")}),
        "platforms": platforms.most_common(15), "item_types": types.most_common(10),
        "matched_share": round(1 - ads_group.get("unmatched", 0) / len(rows), 3),
        "cases_in_window": len(win),
        "by_group": by_group, "pairs": pairs,
        "ads_by_country": ads_country.most_common(20),
        # Offered online but outside every WildTrace group: candidates for new groups.
        "not_tracked": [[k, v] for k, v in unmatched.most_common(15)],
    }


def publish(data: dict, out: Path = WEB_DATA) -> Path:
    path = out / "online_gap.json"
    path.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
    with open(out / "online_gap.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["species_group", "country", "ecosolve_adverts", "wildtrace_cases", "adverts_per_case"])
        for p in data["pairs"]:
            w.writerow([p["group"], p["country"], p["adverts"], p["cases"], p["adverts_per_case"] if p["adverts_per_case"] is not None else ""])
    return path
