"""Image evidence: read the text in a picture, and recognise the species in it.

Listings and seizure photos carry evidence that captions leave out: a price and "WhatsApp" written
on the image, pangolin scales in a bag, a tokay gecko in a jar. Text-only matching also has to treat
many words as ambiguous ("monitor", "horn", Thai "เหี้ย"). This module adds two independent,
local, key-free signals:

* OCR (LiteParse, Apache-2.0, runs on the machine): the text inside the image, scrubbed of phone
  numbers and handles before it is kept, then matched against the lexicon and code words.
* Visual species recognition (BioCLIP, imageomics/bioclip, MIT; a CLIP model trained on the
  Tree of Life): zero-shot scores for the scientific names behind each WildTrace group, against
  look-alike distractors (a computer monitor, a car horn, jewellery, a person).

`analyse()` combines them with the caption. An ambiguous term that lacked text context is
confirmed when the picture shows the same group with enough confidence (CONFIRM); a text match
the picture contradicts is flagged for review, never silently dropped. Results are private
(data/interim/vision.jsonl): images and OCR text are never published.

    pip install liteparse open_clip_torch      # optional; weights (~600 MB) cache under HF_HOME
    wildtrace vision path/to/images [--caption-file captions.csv]
"""
from __future__ import annotations

import json
import os
import re
from functools import lru_cache
from pathlib import Path

from .. import lexicon
from ..config import INTERIM
from ..privacy import scrub

CONFIRM = 0.5          # BioCLIP probability that confirms a group
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
# Things that ambiguous words also name, so the model has somewhere to put them.
DISTRACTORS = ["a computer monitor", "a car horn", "a person", "a pet dog", "a pet cat", "jewellery", "a plastic toy",
               "a python programming book", "a sports team logo", "an empty room"]
# Taxa with a photographable form, per group; the lexicon's `taxa` lists fill the rest.
EXTRA_TAXA = {"elephant": ["Loxodonta africana", "carved elephant ivory"], "rhino": ["Ceratotherium simum", "rhinoceros horn"],
              "pangolin": ["Manis javanica", "pangolin scales"], "shark_ray": ["dried shark fins", "Hippocampus"],
              "tiger": ["Panthera tigris", "tiger skin"], "birds": ["Psittacus erithacus", "Psittacula krameri"],
              "turtles": ["Geochelone elegans", "Testudo"], "sea_fan": ["black coral", "Gorgonacea"], "bear": ["Ursus thibetanus"],
              "amphibians": ["Ambystoma mexicanum", "Dendrobates"], "monitor_lizard": ["Varanus salvator"]}


@lru_cache(maxsize=1)
def _ocr():
    from liteparse import LiteParse
    return LiteParse(ocr_enabled=True, quiet=True)


def ocr(path: str | Path) -> str:
    """Text in the image, with phone numbers, emails and handles removed."""
    try:
        return scrub((_ocr().parse(str(path)).text or "").strip())
    except Exception:
        return ""


def _labels() -> tuple[list[str], list[str | None]]:
    texts, groups = [], []
    for gid, g in lexicon.load()["groups"].items():
        if gid == lexicon.GENERAL:
            continue
        taxa = [re.sub(r"\s*spp\.|\(.*?\)", "", t).strip() for t in g.get("taxa", [])] + EXTRA_TAXA.get(gid, [])
        for t in dict.fromkeys(x for x in taxa if x):
            texts.append(f"a photo of {t}")
            groups.append(gid)
    for d in DISTRACTORS:
        texts.append(f"a photo of {d}")
        groups.append(None)
    return texts, groups


@lru_cache(maxsize=1)
def _bioclip():
    os.environ.setdefault("HF_HOME", str(Path(INTERIM).parent / "hf_cache"))
    import open_clip
    import torch
    model, _, pre = open_clip.create_model_and_transforms("hf-hub:imageomics/bioclip")
    tok = open_clip.get_tokenizer("hf-hub:imageomics/bioclip")
    texts, groups = _labels()
    with torch.no_grad():
        tf = model.encode_text(tok(texts))
        tf /= tf.norm(dim=-1, keepdim=True)
    model.eval()
    return model, pre, tf, texts, groups


def species(path: str | Path, top: int = 3) -> list[dict]:
    """Group probabilities from the picture (label probabilities summed per group)."""
    import torch
    from PIL import Image
    model, pre, tf, texts, groups = _bioclip()
    try:
        im = pre(Image.open(path).convert("RGB")).unsqueeze(0)
    except Exception:
        return []
    with torch.no_grad():
        f = model.encode_image(im)
        f /= f.norm(dim=-1, keepdim=True)
        p = (100 * f @ tf.T).softmax(-1)[0].tolist()
    by: dict[str, float] = {}
    best: dict[str, str] = {}
    for prob, g, t in zip(p, groups, texts):
        key = g or "not wildlife"
        by[key] = by.get(key, 0) + prob
        if prob > by.get(f"_{key}", 0):
            by[f"_{key}"], best[key] = prob, t.removeprefix("a photo of ")
    out = [{"group": k, "p": round(v, 3), "label": best.get(k)} for k, v in by.items() if not k.startswith("_")]
    return sorted(out, key=lambda x: -x["p"])[:top]


def analyse(path: str | Path, caption: str = "") -> dict:
    """Caption, OCR and picture, combined. Nothing is dropped: disagreements are flagged."""
    text_ocr = ocr(path)
    seen = species(path)
    both = f"{caption} {text_ocr}".strip()
    groups_text = set(lexicon.species_groups(both)) - {lexicon.GENERAL}
    amb = lexicon.ambiguous_hits(both)
    pic = {s["group"]: s["p"] for s in seen}
    confirmed = sorted({a["group"] for a in amb if not a["accepted"] and a.get("group") and pic.get(a["group"], 0) >= CONFIRM})
    top = seen[0] if seen else None
    groups = sorted(groups_text | set(confirmed) | ({top["group"]} if top and top["group"] != "not wildlife" and top["p"] >= CONFIRM else set()))
    conflict = bool(groups_text) and top is not None and top["p"] >= CONFIRM and top["group"] not in groups_text
    return {"image": Path(path).name, "ocr_text": text_ocr, "picture": seen, "text_groups": sorted(groups_text),
            "ambiguous": amb, "confirmed_by_picture": confirmed, "groups": groups,
            "codewords": [c["term"] for c in lexicon.codeword_hits(both)],
            "review": conflict or bool([a for a in amb if not a["accepted"] and a.get("group") not in confirmed])}


def run(folder: str | Path, captions: dict[str, str] | None = None) -> Path:
    paths = [Path(folder)] if Path(folder).is_file() else sorted(p for p in Path(folder).rglob("*") if p.suffix.lower() in IMAGE_EXT)
    out = INTERIM / "vision.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "a", encoding="utf-8") as f:
        for p in paths:
            r = analyse(p, (captions or {}).get(p.name, ""))
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
            print(f"  {p.name}: {r['groups'] or '-'}  picture={r['picture'][:1]}  review={r['review']}")
    return out
