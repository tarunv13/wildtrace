"""Captive-bred claims in declared CITES trade: where to ask whether "bred" means "caught".

A CITES record says where a specimen came from: W (taken from the wild), C or F (bred in captivity),
D (commercially bred, Appendix I), R (ranched). Declaring wild-caught animals as captive-bred is a
documented way to launder them into legal trade: Lyons & Natusch (2011, Biological Conservation
144:3073) showed that green pythons exported from Indonesia as "captive-bred" were overwhelmingly
wild-caught, because breeding them at that scale was not plausible.

This module does not detect laundering. It computes two signals that tell an investigator where to
look, from declared (non-seized) commercial (purpose T) CITES records of animal groups since 2015:

* the captive share: records declared C, F or D, out of records with a wild or captive source;
* the shift: the change in captive share between the early years (2015-2018) and the late years
  (2020-2023). A trade that switches from wild to captive in a few years is the pattern Lyons &
  Natusch describe, though genuine new breeding operations produce it too.

Only exporter-group pairs with enough records to mean anything are kept (MIN_RECORDS). Plants are
left out: artificial propagation (source A) is the normal, legitimate route for most plant trade.

    wildtrace captive path/to/Trade_database_download_vYYYY.1    -> web/data/captive_claims.json + .csv
"""
from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

from ..config import WEB_DATA
from .cites import group_of, taxon_index

MIN_YEAR = 2015
EARLY, LATE = (2015, 2018), (2020, 2023)
MIN_RECORDS = 30
CAPTIVE, WILD = {"C", "F", "D"}, {"W", "R", "U", "X"}
FLORA = {"orchids", "cacti_succulents", "cycads", "carnivorous_plants", "medicinal_plants", "sandalwood", "resins_gums",
         "bulbs_ornamental", "rosewood", "agarwood", "red_sanders"}


def aggregate(folder: Path | str) -> dict:
    species, higher = taxon_index()
    n = defaultdict(Counter)            # (group, exporter) -> {"wild", "captive", "early_w", ...}
    taxa = defaultdict(Counter)         # (group, exporter) -> captive-declared taxa
    files = sorted(Path(folder).glob("*.csv"))
    if not files:
        raise SystemExit(f"no CSV files in {folder}: unzip the CITES download there first")
    for f in files:
        with open(f, encoding="utf-8", errors="replace", newline="") as fh:
            for r in csv.DictReader(fh):
                src = (r.get("Source") or "").strip()
                if src not in CAPTIVE and src not in WILD:
                    continue                                   # seized (I), pre-Convention, unknown, plants' A
                if (r.get("Purpose") or "").strip() != "T":
                    continue                                   # commercial only: zoo, science and breeding loans are not the risk
                try:
                    y = int(r["Year"])
                except (TypeError, ValueError):
                    continue
                if y < MIN_YEAR:
                    continue
                g = group_of(r, species, higher)
                if not g or g in FLORA:
                    continue
                exp = (r.get("Exporter") or "").strip()
                if not exp:
                    continue
                k, cap = (g, exp), src in CAPTIVE
                n[k]["captive" if cap else "wild"] += 1
                for name, (a, b) in (("early", EARLY), ("late", LATE)):
                    if a <= y <= b:
                        n[k][f"{name}_{'c' if cap else 'w'}"] += 1
                if cap:
                    taxa[k][(r.get("Taxon") or "").strip()] += 1
        print(f"  {f.name}: {len(n):,} exporter-group pairs so far")
    rows = []
    for (g, e), c in n.items():
        tot = c["wild"] + c["captive"]
        if tot < MIN_RECORDS:
            continue
        share = c["captive"] / tot
        e_t, l_t = c["early_c"] + c["early_w"], c["late_c"] + c["late_w"]
        shift = (c["late_c"] / l_t - c["early_c"] / e_t) if e_t >= 10 and l_t >= 10 else None
        rows.append({"group": g, "exporter": e, "records": tot, "captive": c["captive"], "captive_share": round(share, 3),
                     "early_share": round(c["early_c"] / e_t, 3) if e_t >= 10 else None,
                     "late_share": round(c["late_c"] / l_t, 3) if l_t >= 10 else None,
                     "shift": round(shift, 3) if shift is not None else None,
                     "top_captive_taxa": [t for t, _ in taxa[(g, e)].most_common(3) if t]})
    rows.sort(key=lambda r: (-(r["shift"] or 0), -r["captive"]))
    return {
        "source": "CITES Trade Database (UNEP-WCMC for the CITES Secretariat)", "year_min": MIN_YEAR,
        "early": list(EARLY), "late": list(LATE), "min_records": MIN_RECORDS,
        "licence": "Derived from the CITES Trade Database; reuse under its terms (non-commercial, with attribution), not CC BY.",
        "note": "Declared (legal) commercial trade (purpose T) only, animal groups. Captive = source C, F or D; wild = W, R, U or X. A high or rising "
                "captive share is a question to ask, not evidence of laundering: genuine breeding produces it too.",
        "cite": "Lyons, J. A. & Natusch, D. J. D. (2011). Wildlife laundering through breeding farms. Biological Conservation "
                "144, 3073-3081. doi:10.1016/j.biocon.2011.10.002",
        "rows": rows,
    }


def publish(data: dict, out: Path = WEB_DATA) -> Path:
    path = out / "captive_claims.json"
    path.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
    with open(out / "captive_claims.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["species_group", "exporter", "declared_records", "captive_records", "captive_share",
                    f"share_{EARLY[0]}_{EARLY[1]}", f"share_{LATE[0]}_{LATE[1]}", "shift", "top_captive_taxa"])
        for r in data["rows"]:
            w.writerow([r["group"], r["exporter"], r["records"], r["captive"], r["captive_share"], r["early_share"],
                        r["late_share"], r["shift"], "; ".join(r["top_captive_taxa"])])
    return path
