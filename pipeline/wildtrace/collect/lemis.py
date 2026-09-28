"""US LEMIS: wildlife seized at United States ports, by species group, origin and product.

The US Fish and Wildlife Service records every wildlife import in LEMIS (Law Enforcement
Management Information System) with its fate. Disposition ``S`` means the shipment was
seized. Two open, cleaned releases of these FOIA data are used (both CC BY 4.0):

* Marshall et al. 2025, Current Biology 35:3959, "Tracing Trade" (Zenodo 14982583):
  2000-2022, terrestrial mammals, birds, reptiles, amphibians and arachnids, with
  names checked against GBIF. Download the ``LEMIS_distributionsAdded_*.csv`` files.
* Eskew et al. 2020, Scientific Data 7:22 (Zenodo 3565869): 2000-2014, every taxon.
  Only the classes Marshall et al. do not cover (fish, corals, molluscs ...) are taken
  from it, so no shipment is counted twice.

Put the files in one folder and run

    wildtrace lemis path/to/folder [--taxonomy path/to/stringham_dataset]

Genera are placed in families and orders with the GBIF taxonomic key of the seized-wildlife
codebook (Stringham et al. 2021, the same dataset ``wildtrace codebook`` reads), so that
groups defined by a family (pangolins = Manidae) or an order (owls) match.

Only counts are published: no shipment number, company or port-level record.
"""
from __future__ import annotations

import csv
import io
import json
import re
import sys
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

from ..config import WEB_DATA
from .cites import taxon_index

MARSHALL_GLOB = "LEMIS_distributionsAdded_*.csv"
ESKEW_FILE = "lemis_2000_2014_cleaned.csv"
# Classes the Marshall et al. files cover; Eskew rows in these classes are skipped.
MARSHALL_CLASSES = {"mammalia", "aves", "reptilia", "amphibia", "arachnida"}
CODES_FILE = "lemis_codes.csv"

csv.field_size_limit(min(sys.maxsize, 2**31 - 1))


def _taxonomy(src: Path | None) -> dict[str, tuple[str, str, str]]:
    """genus (lower) -> (family, order, class), from the codebook's 02_gbif_taxonomic_key.csv."""
    if not src or not Path(src).exists():
        return {}
    src = Path(src)
    raw = None
    if src.is_dir():
        hit = next(iter(src.rglob("02_gbif_taxonomic_key.csv")), None)
        raw = hit.read_bytes() if hit else None
    elif zipfile.is_zipfile(src):
        z = zipfile.ZipFile(src)
        name = next((n for n in z.namelist() if n.endswith("02_gbif_taxonomic_key.csv")), None)
        raw = z.read(name) if name else None
    if raw is None:
        return {}
    out = {}
    for r in csv.DictReader(io.StringIO(raw.decode("utf-8", errors="replace"))):
        g = (r.get("genus") or "").strip()
        if g and g != "NA":
            out.setdefault(g.lower(), tuple((r.get(k) or "").strip() for k in ("family", "order", "class")))
    return out


def _codes(folder: Path) -> dict[str, dict[str, str]]:
    path = folder / CODES_FILE
    out: dict[str, dict[str, str]] = defaultdict(dict)
    if path.exists():
        with open(path, encoding="utf-8", errors="replace", newline="") as f:
            for r in csv.DictReader(f):
                out[r["field"]][r["code"]] = r["value"]
    return out


def _iso2(v: str) -> str:
    v = (v or "").strip().upper().removeprefix("CTRY_")
    return v if re.fullmatch(r"[A-Z]{2}", v) and v not in {"XX", "ZZ", "NA"} else "XX"


def _year(*vals: str) -> int | None:
    for v in vals:
        m = re.match(r"(\d{4})", (v or "").strip())
        if m:
            return int(m.group(1))
    return None


def aggregate(folder: Path | str, taxonomy: Path | str | None = None, min_year: int = 2000) -> dict:
    folder = Path(folder)
    species, higher = taxon_index()
    tax = _taxonomy(Path(taxonomy) if taxonomy else None)
    codes = _codes(folder)
    no_group = Counter()

    def group(genus: str, sp: str, order: str = "", klass: str = "") -> str | None:
        genus, sp = (genus or "").strip().lower(), (sp or "").strip().lower()
        if genus and sp and f"{genus} {sp}" in species:
            return species[f"{genus} {sp}"]
        fam, ordr, cls = tax.get(genus, ("", "", ""))
        for k in (genus, fam, order or ordr, klass or cls):
            if k and k.lower() in higher:
                return higher[k.lower()]
        return None

    seized, years = Counter(), Counter()
    products: dict[str, Counter] = defaultdict(Counter)
    detail = defaultdict(lambda: {"years": Counter(), "taxa": Counter(), "products": Counter(), "purpose": Counter(),
                                  "source": Counter(), "via": Counter(), "groups": Counter()})
    span: dict[str, list[int]] = {}

    def add(src: str, g: str, org: str, exp: str, y: int, taxon: str, desc: str, purpose: str, source: str):
        seized[(g, org, exp)] += 1
        years[(g, y)] += 1
        products[g][desc or "UNS"] += 1
        d = detail[f"{org}|US"]
        d["years"][y] += 1; d["groups"][g] += 1; d["taxa"][taxon] += 1
        d["products"][desc or "UNS"] += 1; d["purpose"][purpose] += 1; d["source"][source] += 1
        if exp != org and exp != "XX":
            d["via"][exp] += 1
        s = span.setdefault(src, [y, y]); s[0] = min(s[0], y); s[1] = max(s[1], y)

    def rows(path: Path):
        with open(path, encoding="utf-8", errors="replace", newline="") as fh:
            yield from csv.DictReader(fh)

    marshall = sorted(folder.glob(MARSHALL_GLOB))
    for f in marshall:
        n0 = sum(seized.values())
        for r in rows(f):
            if (r.get("disposition") or "").strip() != "S" or (r.get("import_export") or "I").strip() != "I":
                continue
            y = _year(r.get("sYear"), r.get("shipment_date"), r.get("disposition_date"))
            if not y or y < min_year:
                continue
            corr = (r.get("corrected") or "").strip()
            genus = (r.get("correctedGenus") or corr.split(" ")[0] if corr else r.get("genus") or "")
            sp = corr.split(" ")[1] if corr.count(" ") >= 1 else (r.get("species") or "")
            g = group(genus, sp, r.get("orderCorrected") or "")
            if not g:
                no_group[genus.strip().capitalize()] += 1
                continue
            org = _iso2(r.get("code_origin") or r.get("country_origin"))
            exp = _iso2(r.get("code_imp") or r.get("country_imp_exp"))
            add("marshall", g, org if org != "XX" else exp, exp, y, corr or f"{genus} {sp}".strip(),
                (r.get("description") or "").strip(), (r.get("purpose") or "").strip(), (r.get("source") or "").strip())
        print(f"  {f.name}: +{sum(seized.values()) - n0:,} seized records in WildTrace groups")

    eskew = folder / ESKEW_FILE
    if eskew.exists():
        n0 = sum(seized.values())
        for r in rows(eskew):
            if (r.get("disposition") or "").strip() != "S" or (r.get("import_export") or "I").strip() != "I":
                continue
            cls = (r.get("class") or "").strip()
            if marshall and cls.lower() in MARSHALL_CLASSES:
                continue
            y = _year(r.get("shipment_year"), r.get("shipment_date"), r.get("disposition_year"))
            if not y or y < min_year:
                continue
            genus, sp = (r.get("genus") or "").strip(), (r.get("species") or "").strip()
            g = group(genus, sp, "", cls)
            if not g:
                no_group[genus.capitalize()] += 1
                continue
            org, exp = _iso2(r.get("country_origin")), _iso2(r.get("country_imp_exp"))
            add("eskew", g, org if org != "XX" else exp, exp, y, f"{genus.capitalize()} {sp.lower()}".strip(),
                (r.get("description") or "").strip(), (r.get("purpose") or "").strip(), (r.get("source") or "").strip())
        print(f"  {eskew.name}: +{sum(seized.values()) - n0:,} seized records (classes outside Marshall et al.)")

    if not seized:
        raise SystemExit(f"no seized LEMIS records found in {folder}: see the module docstring for the files")
    print(f"  genera seized but in no WildTrace group (top): {no_group.most_common(12)}")
    desc_names = codes.get("description", {})
    return {
        "source": "US Fish and Wildlife Service LEMIS (FOIA), cleaned by Marshall et al. 2025 and Eskew et al. 2020",
        "cite": "Marshall, B. M. et al. (2025) Tracing trade: mapping the global dimensions of US wildlife imports. "
                "Current Biology 35, 3959-3972. doi:10.5281/zenodo.14982583; Eskew, E. A. et al. (2020) United States "
                "wildlife and wildlife product imports from 2000-2014. Scientific Data 7, 22. doi:10.5281/zenodo.3565869.",
        "licence": "CC BY 4.0 (both source datasets).",
        "note": "Counts are LEMIS records of imports the US Fish and Wildlife Service seized (disposition S), not quantities. "
                "Mammals, birds, reptiles, amphibians and arachnids " + _span(span.get("marshall")) +
                "; fish, invertebrates and plants " + _span(span.get("eskew")) + ". "
                "They show what reached US ports, not all illegal trade.",
        "span": span,
        # [group, origin, exporter, importer, records]; the importer is always US
        "seized": [[g, o, e, "US", n] for (g, o, e), n in seized.most_common()],
        "seized_years": [[g, y, n] for (g, y), n in sorted(years.items())],
        "products": {g: c.most_common(8) for g, c in products.items()},
        "product_names": {k: desc_names.get(k, k) for c in products.values() for k in c},
        "purpose_names": codes.get("purpose", {}),
        "source_names": codes.get("source", {}),
        "detail": {k: {"years": dict(sorted(v["years"].items())), "taxa": v["taxa"].most_common(6),
                       "products": v["products"].most_common(6), "purpose": dict(v["purpose"].most_common(4)),
                       "source": dict(v["source"].most_common(4)), "via": v["via"].most_common(4),
                       "groups": v["groups"].most_common(4)} for k, v in detail.items()},
    }


def _span(s: list[int] | None) -> str:
    return f"{s[0]}-{s[1]}" if s else "not loaded"


def publish(data: dict, out: Path = WEB_DATA) -> Path:
    path = out / "lemis.json"
    path.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
    with open(out / "lemis_seized_flows.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["species_group", "origin", "exporter", "importer", "seized_records"])
        w.writerows(data["seized"])
    return path
