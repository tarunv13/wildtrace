"""Merge the open "Dataset of seized wildlife and their intended uses" into the lexicon.

Stringham et al. 2021, Data in Brief 39:107531 (PMC8579131), CC BY 4.0,
figshare 10.6084/m9.figshare.14914773. About 4,900 seized taxa, 45,000+ common
names in 100+ languages, and the intended use of each taxon (medicine, pets,
jewellery ...). It is the closest thing to an open "codebook" that maps local
names to species.

figshare blocks scripted downloads, so fetch the zip in a browser and run:

    wildtrace codebook path/to/dataset_of_seized_wildlife_and_their_intended_uses.zip

Output: resources/lexicon_pmc.yaml, extra common names per lexicon group
(matched on genus/species from `taxa`) plus the recorded use-types. The
lexicon loader merges it automatically. Short or generic names are dropped
(see MIN_LEN) so precision holds. Names that are also everyday words (GENERIC) are not
dropped: they go to each group's `ambiguous` list and count only with trade or enforcement
context nearby (lexicon.ambiguous_hits).
"""
from __future__ import annotations

import io
import re
import zipfile
from collections import defaultdict
from pathlib import Path

import pandas as pd
import yaml

from .. import lexicon
from ..config import RESOURCES

MIN_LEN = 5
GENERIC = {"turtle", "tortoise", "snake", "lizard", "bird", "parrot", "deer", "bear", "shark", "coral", "monkey",
           "owl", "gecko", "cat", "tiger", "leopard", "elephant", "rhino", "pangolin", "animal", "fish",
           # common English words that are also vernacular names: they would tag unrelated news
           "monitor", "sandalwood", "boar", "swine", "musk", "horn", "civet", "hawk", "eagle", "ape", "apes",
           "sea fan", "fan", "whip", "gorgonian", "raven", "robin", "martin", "swift", "crane", "kite", "jack"}


def _csv(raw: bytes) -> pd.DataFrame:
    # Most tables are UTF-8; at least one carries Latin-1 bytes (e.g. 0xF3 "ó").
    for enc in ("utf-8", "cp1252", "latin-1"):
        try:
            return pd.read_csv(io.BytesIO(raw), dtype=str, keep_default_na=False, low_memory=False, encoding=enc)
        except UnicodeDecodeError:
            continue
    raise ValueError("unreadable CSV")


def _read_tables(src: Path) -> dict[str, pd.DataFrame]:
    tables = {}
    if src.is_dir():
        for p in src.rglob("*.csv"):
            tables[p.name] = _csv(p.read_bytes())
    else:
        z = zipfile.ZipFile(src)
        for n in z.namelist():
            if n.endswith(".csv") and not n.startswith("__MACOSX"):
                tables[Path(n).name] = _csv(z.read(n))
    need = {"01_taxa_use_combos.csv", "02_gbif_taxonomic_key.csv", "03_gbif_common_names.csv", "04_db_generic_common_names.csv"}
    missing = need - set(tables)
    if missing:
        raise FileNotFoundError(f"not the PMC8579131 dataset; missing {sorted(missing)}")
    return tables


def _taxon_keys() -> dict[str, str]:
    """species / genus / family / order name (lower) -> lexicon group id."""
    keys = {}
    for gid, g in lexicon.load()["groups"].items():
        for t in g.get("taxa", []):
            keys[t.replace(" spp.", "").strip().lower()] = gid
    return keys


def build(src: str | Path) -> Path:
    t = _read_tables(Path(src))
    keys = _taxon_keys()

    # 1. GBIF id -> lexicon group, most specific rank first.
    tax = t["02_gbif_taxonomic_key.csv"]
    id2group: dict[str, str] = {}
    name2group: dict[str, str] = {}
    for _, r in tax.iterrows():
        gid = next((keys[v.lower()] for v in (r["species"], r["genus"], r["family"], r["order"]) if v and v.lower() in keys), None)
        if gid:
            id2group[r["gbif_id"]] = gid
            name2group[r["db_taxa_name_clean"].lower()] = gid

    names: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    ambiguous: dict[str, set[str]] = defaultdict(set)
    uses: dict[str, set[str]] = defaultdict(set)

    def keep(nm: str, gid: str = "") -> bool:
        nm = nm.strip()
        if nm.lower() in GENERIC:
            if gid and len(nm) >= 3:
                ambiguous[gid].add(nm.lower())
            return False
        return len(nm) >= MIN_LEN and not nm.isupper()

    # 2. Multilingual common names (GBIF vernaculars), keyed by ISO 639-1 where available.
    for _, r in t["03_gbif_common_names.csv"].iterrows():
        gid = id2group.get(r["gbif_id"])
        if gid and keep(r["gbif_common_name"], gid):
            lang = r.get("ISO 639-1 Code") or r.get("ISO 639-2 Code") or "und"
            names[gid][lang].add(r["gbif_common_name"].strip())
    # 3. Trade-database names (LEMIS / TRAFFIC), English.
    for _, r in t["04_db_generic_common_names.csv"].iterrows():
        gid = name2group.get(r["db_taxa_name"].lower())
        if gid and keep(r["db_name"], gid):
            names[gid]["en_db"].add(r["db_name"].strip().lower())
    # 4. Intended uses recorded in seizures.
    for _, r in t["01_taxa_use_combos.csv"].iterrows():
        gid = id2group.get(r["gbif_id"]) or name2group.get(r["db_taxa_name_clean"].lower())
        if gid and r["standardized_use_type"]:
            uses[gid].add(r["standardized_use_type"])

    out = {"source": "Stringham et al. 2021, Data in Brief 39:107531, CC BY 4.0 (figshare 14914773)", "groups": {}}
    for gid in sorted(set(names) | set(uses) | set(ambiguous)):
        out["groups"][gid] = {"terms": {k: sorted(v)[:60] for k, v in sorted(names[gid].items())},
                              "uses": sorted(uses[gid]), "ambiguous": sorted(ambiguous[gid])}
    path = RESOURCES / "lexicon_pmc.yaml"
    path.write_text(yaml.safe_dump(out, allow_unicode=True, sort_keys=False), encoding="utf-8")
    n = sum(len(v) for g in out["groups"].values() for v in g["terms"].values())
    langs = {k for g in out["groups"].values() for k in g["terms"]}
    print(f"codebook: {n} names in {len(langs)} languages for {len(out['groups'])} groups -> {path}")
    return path
