"""Load the species/trade lexicon and match it against text in any script."""
from __future__ import annotations

import re
import unicodedata
from functools import lru_cache
from typing import Any

import yaml

from .config import RESOURCES


def norm(text: str) -> str:
    text = unicodedata.normalize("NFKC", text or "").lower()
    text = text.replace("’", "'").replace("‘", "'").replace("ʼ", "'")   # curly apostrophes
    return re.sub(r"\s+", " ", text)


@lru_cache(maxsize=1)
def _mask_re() -> re.Pattern[str] | None:
    masks = sorted((norm(m) for m in load().get("masks") or []), key=len, reverse=True)
    return re.compile("|".join(re.escape(m) for m in masks)) if masks else None


def prep(text: str) -> str:
    """Normalised text with known non-species phrases blanked ("tiger strike force", "ivory coast")."""
    t = norm(text)
    rx = _mask_re()
    return rx.sub(" ", t) if rx else t


@lru_cache(maxsize=1)
def _ambiguous_words() -> frozenset[str]:
    """Curated ambiguous words (lexicon.yaml). They take precedence over strong lists. Codebook-derived
    ambiguous names do not: a core species name ("elephant") stays a strong term."""
    return frozenset(norm(a["term"]) for a in load().get("ambiguous", []) if "codebook" not in (a.get("source") or ""))


def _pattern(term: str) -> re.Pattern[str]:
    t = re.escape(norm(term)).replace(r"\ ", r"[\s\-_]*")
    # A plural species term also matches its singular ("parakeets" finds "parakeet species").
    # Not when the singular is itself an ambiguous word ("pythons" must not match "Python" bare).
    if re.fullmatch(r"[a-z][a-z \-]{3,}[^s]s", norm(term)) and norm(term)[:-1] not in _ambiguous_words():
        t = t[:-1] + "s?"
    elif re.fullmatch(r"[a-z][a-z \-]{2,}[a-rt-z]", norm(term)):
        t = t + "(?:s|es)?"            # and a singular term matches its plural ("parrot" finds "parrots")
    # \b does not work for Devanagari/Thai combining marks; use lookarounds on word chars
    # only when the term starts/ends with an ASCII letter or digit.
    left = r"(?<![a-z0-9])" if re.match(r"[a-z0-9]", norm(term)) else ""
    right = r"(?![a-z0-9])" if re.search(r"[a-z0-9]$", norm(term)) else ""
    return re.compile(left + t + right)


@lru_cache(maxsize=1)
def load() -> dict[str, Any]:
    """Curated lexicon, extended by the PMC8579131 codebook when it has been built
    (`wildtrace codebook`). Codebook names go under `pmc_<lang>` keys so their
    provenance stays visible."""
    with open(RESOURCES / "lexicon.yaml", encoding="utf-8") as f:
        lex = yaml.safe_load(f)
    pmc = RESOURCES / "lexicon_pmc.yaml"
    if pmc.exists():
        extra = yaml.safe_load(pmc.read_text(encoding="utf-8")) or {}
        for gid, g in (extra.get("groups") or {}).items():
            if gid not in lex["groups"]:
                continue
            for lang, terms in (g.get("terms") or {}).items():
                lex["groups"][gid]["terms"].setdefault(f"pmc_{lang}", []).extend(terms)
            if g.get("uses"):
                lex["groups"][gid]["uses"] = g["uses"]
            # Codebook names that are also everyday words (monitor, musk, horn ...) are kept as
            # ambiguous terms that need trade or enforcement context, never thrown away.
            for t in g.get("ambiguous") or []:
                lex.setdefault("ambiguous", []).append({"term": t, "group": gid, "needs": ["enforcement", "trade", "wildlife"],
                                                        "source": "PMC8579131 codebook (common word)"})
    return lex


# ------------------------------------------------------------------ ambiguous terms
# A word can name a traded species and also mean something else ("monitor", "musk", Thai "เหี้ย",
# which is both the water monitor and a swear word). Dropping such words loses real reports; matching
# them bare adds noise. So each ambiguous term lists the context it needs, within WINDOW characters:
#   species     another, unambiguous species term
#   enforcement an enforcement cue (seized, arrested ...)
#   trade       a sale cue (for sale, price ...)
#   wildlife    a general wildlife phrase (protected species, สัตว์ป่า ...)
#   quantity    a number (a count, weight or value)
# A hit with that context counts; every hit, accepted or not, is kept for review (ambiguous_hits),
# so the rule can be checked and tightened from evidence, and later confirmed by image evidence.
WINDOW = 80
_QTY = re.compile(r"\d")


@lru_cache(maxsize=1)
def _ambiguous() -> list[tuple[dict, re.Pattern[str]]]:
    return [(a, _pattern(a["term"])) for a in load().get("ambiguous", [])]


_WORDS = re.compile(r"\w+", re.UNICODE)
_NOSPACE = re.compile(r"[฀-໿က-႟ក-៿぀-ヿ一-鿿]")


@lru_cache(maxsize=1)
def _context_sets() -> dict[str, tuple[frozenset[str], tuple[str, ...]]]:
    """Per context kind: word sequences (hash lookup) and terms in scripts written without spaces
    (substring check). Much faster than one regex alternation over thousands of terms."""
    def split(terms):
        seqs, nospace = set(), []
        for t in terms:
            n = norm(t)
            if n in _ambiguous_words():
                continue
            if _NOSPACE.search(n):
                nospace.append(n)
            else:
                w = " ".join(_WORDS.findall(n))
                if w:
                    seqs.add(w)
                    if w.endswith("s") and len(w) > 4 and not w.endswith("ss"):
                        seqs.add(w[:-1])
        return frozenset(seqs), tuple(nospace)
    lex = load()
    strong = [t for gid, g in lex["groups"].items() if gid != GENERAL for ts in (g.get("terms") or {}).values() for t in ts]
    general = [t for ts in (lex["groups"].get(GENERAL, {}).get("terms") or {}).values() for t in ts]
    return {"species": split(strong), "enforcement": split([t for ts in lex["enforcement_cues"].values() for t in ts]
                                 + [t for ts in (lex.get("topic_cues") or {}).values() for t in ts]),
            "trade": split([t for ts in lex["sale_cues"].values() for t in ts]), "wildlife": split(general)}


def _context(snippet: str) -> set[str]:
    words = _WORDS.findall(snippet)
    grams = {" ".join(words[i:i + n]) for n in range(1, 6) for i in range(len(words) - n + 1)}
    have = {k for k, (seqs, nospace) in _context_sets().items() if grams & seqs or any(t in snippet for t in nospace)}
    if _QTY.search(snippet):
        have.add("quantity")
    return have


@lru_cache(maxsize=1)
def _ambiguous_any() -> re.Pattern[str]:
    return re.compile("|".join(f"(?:{p.pattern})" for _, p in _ambiguous()) or r"(?!x)x")


def ambiguous_hits(text: str) -> list[dict]:
    """Every ambiguous term in the text, with the context found around it and whether it counts."""
    t = prep(text)
    out = []
    if not _ambiguous_any().search(t):      # fast path: most texts have no ambiguous word
        return out
    for a, p in _ambiguous():
        for m in p.finditer(t):
            snip = t[max(0, m.start() - WINDOW):m.end() + WINDOW]
            ctx = _context(snip.replace(m.group(0), " ", 1))
            terms_ok = any(norm(x) in snip for x in a.get("needs_terms") or []) or bool(
                a.get("needs_regex") and re.search(a["needs_regex"], snip))
            if terms_ok:
                ctx.add("terms")
            out.append({"term": a["term"], "group": a.get("group"), "cue": a.get("cue"), "context": sorted(ctx), "span": m.span(),
                        "accepted": terms_ok if a.get("needs_regex") else (bool(ctx & set(a.get("needs") or [])) or terms_ok)})
            break
    return out


@lru_cache(maxsize=1)
def codewords() -> list[dict[str, Any]]:
    path = RESOURCES / "codewords.yaml"
    return (yaml.safe_load(path.read_text(encoding="utf-8")) or {}).get("codewords", []) if path.exists() else []


def codeword_hits(text: str) -> list[dict[str, Any]]:
    """Watchlist hits. Unverified codewords only flag an item for human review;
    they never make it a case on their own."""
    t = prep(text)
    return [c for c in codewords() if _pattern(c["term"]).search(t)]


@lru_cache(maxsize=1)
def _compiled() -> dict[str, list[tuple[str, re.Pattern[str]]]]:
    lex = load()
    out: dict[str, list[tuple[str, re.Pattern[str]]]] = {}
    for gid, g in lex["groups"].items():
        pats = []
        for terms in (g.get("terms") or {}).values():
            for t in terms:
                # A word registered as ambiguous is always context-checked, whichever list also has it.
                if norm(t) not in _ambiguous_words():
                    pats.append((t, _pattern(t)))
        out[gid] = pats
    return out


def _cue_patterns(section: str) -> dict[str, list[re.Pattern[str]]]:
    lex = load()[section]
    return {k: [_pattern(t) for t in v] for k, v in lex.items()}


@lru_cache(maxsize=None)
def cues(section: str) -> dict[str, list[re.Pattern[str]]]:
    return _cue_patterns(section)


GENERAL = "wildlife_general"


def species_groups(text: str) -> list[str]:
    """Groups named in the text. The catch-all 'wildlife (unspecified)' group is kept
    only when nothing more specific matches."""
    t = prep(text)
    found: list[tuple[int, int, str]] = []
    for gid, pats in _compiled().items():
        for _, p in pats:
            found += [(m.start(), m.end(), gid) for m in p.finditer(t)]
    found += [(a["span"][0], a["span"][1], a["group"]) for a in ambiguous_hits(text) if a["accepted"] and a.get("group")]
    # Leftmost-longest: where matches from different groups overlap, the one that starts first (then the
    # longer) wins, as in a tokenizer. "red sandalwood smuggling" is red sanders, not also sandalwood;
    # "लाल चंदन" is red sanders even though "चंदन" alone means sandalwood.
    picked, last_end = [], -1
    for s0, e0, gid in sorted(found, key=lambda x: (x[0], -(x[1] - x[0]))):
        if s0 >= last_end:
            picked.append((s0, e0, gid))
            last_end = e0
    hits = list(dict.fromkeys(g for _, _, g in picked))
    specific = [g for g in hits if g != GENERAL]
    return specific or hits


def matched_terms(text: str) -> list[str]:
    t = prep(text)
    terms = {term for pats in _compiled().values() for term, p in pats if p.search(t)}
    return sorted(terms | {a["term"] for a in ambiguous_hits(text) if a["accepted"]})


def count_cues(text: str, section: str) -> dict[str, int]:
    t = prep(text)
    out = {k: sum(1 for p in pats if p.search(t)) for k, pats in cues(section).items()}
    if section == "enforcement_cues":
        for a in ambiguous_hits(text):
            if a["accepted"] and a.get("cue") in out:
                out[a["cue"]] += 1
    return out


def group_label(gid: str) -> str:
    return load()["groups"].get(gid, {}).get("label", gid)


def search_terms(min_len: int = 4) -> dict[str, list[str]]:
    """Terms worth sending to a search engine, per group (skips very short/ambiguous ones)."""
    lex = load()["groups"]
    return {gid: [t for terms in g["terms"].values() for t in terms if len(t) >= min_len] for gid, g in lex.items()}
