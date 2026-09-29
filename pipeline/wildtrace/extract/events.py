"""Turn relevant records into structured enforcement events.

Rule-based on purpose: every field it fills can be traced to a phrase in the
source text, which is what a case report needs. Each event keeps the matched
phrases (``evidence``) so reviewers can check the extraction.

What is NOT extracted: names of people. Only the count of people arrested is
kept (see privacy.py).
"""
from __future__ import annotations

import csv
import re
from dataclasses import asdict, dataclass, field
from functools import lru_cache

from .. import lexicon
from ..config import RESOURCES
from ..schema import Record

WORDNUM = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8,
           "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "fifteen": 15, "twenty": 20, "a": 1, "an": 1}
_UNIT = (r"kg|kgs|kilograms?|kilos?|g|grams?|tonnes?|tons?|quintals?|pieces|pcs|nos|numbers|skins?|scales|tusks?|"
         r"horns?|claws|nails|teeth|bones|pelts?|live|birds|parakeets|parrots|turtles|tortoises|snakes|lizards|logs|"
         r"pangolins|geckos|owls|pods|hides|carcass(?:es)?|heads|bags|boxes|sacks")
QTY = re.compile(rf"(?<![\w.])(\d{{1,3}}(?:,\d{{2,3}})+|\d+(?:\.\d+)?|{'|'.join(WORDNUM)})\s*(?:-\s*)?({_UNIT})\b", re.I)
MONEY = re.compile(r"(?:rs\.?|₹|inr|usd|us\$|\$)\s*([\d,]+(?:\.\d+)?)\s*(lakh|lakhs|crore|crores|million|billion|mn|cr)?", re.I)
PEOPLE = re.compile(rf"\b(\d+|{'|'.join(WORDNUM)})\s+(?:\w+\s+){{0,2}}(?:persons?|people|men|women|accused|suspects?|"
                    rf"poachers?|smugglers?|traffickers?|youths?|nationals?|individuals?)\s+(?:were\s+|are\s+)?"
                    r"(?:arrested|held|nabbed|detained|apprehended|caught|booked)", re.I)
_PN = r"[A-Z][\w]+(?:\s[A-Z][\w]+){0,3}"  # a capitalised place name, up to 4 words
# "352 pangolin scales", "4 monitor lizards": up to two words between number and unit.
QTY_GAP = re.compile(rf"(?<![\w.])(\d{{1,3}}(?:,\d{{2,3}})+|\d+(?:\.\d+)?|{'|'.join(k for k in WORDNUM if len(k) > 2)})\s+"
                     rf"(?:[A-Za-z-]+\s+){{1,2}}?({_UNIT})\b", re.I)
# Hindi: "छह लोग गिरफ्तार", "दो आरोपी गिरफ्तार", "4 गिरफ्तार", "13 तस्कर गिरफ्तार"
HINDI_NUM = {"एक": 1, "दो": 2, "तीन": 3, "चार": 4, "पांच": 5, "पाँच": 5, "छह": 6, "छः": 6, "छे": 6, "सात": 7,
             "आठ": 8, "नौ": 9, "दस": 10, "ग्यारह": 11, "बारह": 12}
PEOPLE_HI = re.compile(r"(?<![ऀ-ॿ\d])(\d+|" + "|".join(HINDI_NUM) + r")\s+(?:\S+\s+){0,2}?"
                       r"(?:लोग|लोगों|आरोपी|आरोपियों|तस्कर|तस्करों|युवक|युवकों|व्यक्ति|शिकारी|शिकारियों)?\s*(?:को\s+)?गिरफ्तार")
# "Six Arrested", "2 held", "three nabbed"
PEOPLE_SHORT = re.compile(rf"\b(\d+|{'|'.join(k for k in WORDNUM if len(k) > 2)})\s+(?:arrested|held|nabbed|detained|booked)\b", re.I)
ROUTE = re.compile(rf"\b(?:from|originating in|sourced from)\s+({_PN})\s+(?:to|towards|for|bound for|destined for)\s+({_PN})")
DEST = re.compile(rf"\b(?:bound for|destined for|destined to|en route to|headed (?:for|to)|heading (?:for|to)|meant for|to be sent to|"
                  rf"to be smuggled (?:in)?to|smuggled (?:in)?to|being taken to|com destino (?:a|ao|à)|con destino (?:a|al)|"
                  rf"à destination de)\s+({_PN})")


AGENCY_CANON = {
    "directorate of revenue intelligence": "DRI", "wildlife crime control bureau": "WCCB",
    "forest officials": "Forest Department", "forest officers": "Forest Department", "forest department": "Forest Department",
    "special task force": "STF", "border security force": "BSF", "sashastra seema bal": "SSB",
    "railway protection force": "RPF", "police": "Police", "customs": "Customs", "crime branch": "Crime Branch",
    "coast guard": "Coast Guard", "department of national parks": "DNP (Thailand)",
}


@dataclass
class Place:
    name: str
    type: str
    country: str
    admin1: str
    lat: float
    lon: float
    pop: int = 0


# South and Southeast Asia (dense coverage, towns >= 1,000 people). Elsewhere the
# gazetteer holds towns >= 15,000, and small one-word towns need their country named.
ASIA = {"IN", "NP", "BD", "LK", "BT", "PK", "MM", "TH", "VN", "LA", "KH", "MY", "SG", "ID", "PH", "CN", "HK", "AE"}


_WORD = re.compile(r"[A-Za-zÀ-ɏ][\w'À-ɏ-]*")


@lru_cache(maxsize=1)
def _gazetteer_all() -> tuple[dict[str, list[Place]], list[tuple[str, Place]]]:
    """(latin index, native-script names).

    Latin index: lower-cased name/alias -> places. The hand-curated gazetteer.csv
    wins over the GeoNames extract (gazetteer_geonames.csv, `wildtrace gazetteer`).
    Native names (Devanagari, Odia, Bengali, Tamil, Telugu, Thai, Burmese, Khmer …)
    come from GeoNames alternate names and are matched as whole words."""
    index: dict[str, list[Place]] = {}
    native: dict[str, Place] = {}
    for fname in ("gazetteer.csv", "gazetteer_geonames.csv"):
        path = RESOURCES / fname
        if not path.exists():
            continue
        with open(path, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                p = Place(r["name"], r["type"], r["country"], r["admin1"], float(r["lat"]), float(r["lon"]),
                          int(r.get("population") or 0) if fname != "gazetteer.csv" else 10**7)
                if r["type"] == "state" and fname != "gazetteer.csv":
                    # GeoNames state rows exist only to carry native names; point them at
                    # the curated state entry so both spellings resolve to one place.
                    p = next((c for c in index.get(r["name"].lower(), []) if c.type == "state"), p)
                else:
                    for n in [r["name"]] + [a for a in (r["aliases"] or "").split(";") if a]:
                        bucket = index.setdefault(n.lower(), [])
                        if fname == "gazetteer.csv" or not bucket:
                            bucket.append(p)
                        elif all(b.country != p.country for b in bucket):
                            bucket.append(p)  # same name in another country: keep for country_hint
                for n in (r.get("native") or "").split(";"):
                    if n and n not in native:
                        native[n] = p
    cur = RESOURCES / "gazetteer_native.csv"
    if cur.exists():
        with open(cur, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                hit = index.get(r["name"].lower())
                if hit:
                    native[r["native"]] = hit[0]  # curated spelling wins over GeoNames
    return index, sorted(native.items(), key=lambda kv: -len(kv[0]))


def gazetteer() -> dict[str, list[Place]]:
    return _gazetteer_all()[0]


def _is_script_char(c: str) -> bool:
    o = ord(c)
    return 0x0900 <= o <= 0x0DFF or 0x0E00 <= o <= 0x0EFF or 0x1000 <= o <= 0x109F or 0x1780 <= o <= 0x17FF


def find_native_places(text: str) -> list[tuple[int, Place]]:
    """Native-script place names as whole words (a Devanagari vowel sign or letter
    right next to the match means it is part of a longer word)."""
    if not any(_is_script_char(c) for c in text):
        return []
    found: dict[str, tuple[int, Place]] = {}
    taken: list[tuple[int, int]] = []
    for name, p in _gazetteer_all()[1]:
        start = text.find(name)
        while start != -1:
            end = start + len(name)
            before = text[start - 1] if start else " "
            after = text[end] if end < len(text) else " "
            # Thai is written without spaces between words, so a word boundary almost never exists:
            # accept longer Thai names anywhere, and short ones after a province/district prefix.
            thai = 0x0E00 <= ord(name[0]) <= 0x0E7F
            thai_ok = thai and (len(name) >= 5 or text[max(0, start - 7):start].endswith(("จ.", "อ.", "จังหวัด", "อำเภอ")))
            if (thai_ok or (not _is_script_char(before) and not _is_script_char(after))) and                     not any(a < end and start < b for a, b in taken):
                taken.append((start, end))
                if p.name not in found or start < found[p.name][0]:
                    found[p.name] = (start, p)
                break
            start = text.find(name, start + 1)
    return list(found.values())


RANK = {"airport": 0, "park": 1, "city": 2, "district": 3, "region": 4, "state": 5, "country": 6}
MAX_WORDS = 4
LOWER_OK = {"pan-india"}  # the only lower-case place token worth trusting


def find_places(text: str, country_hint: str = "") -> list[tuple[int, Place]]:
    """Gazetteer places mentioned in text, longest match first, with the offset of
    the first mention. Only capitalised spans are considered, so "star" never
    matches a town called Star."""
    idx = gazetteer()
    words = [(m.start(), m.end(), m.group(0)) for m in _WORD.finditer(text)]
    # Countries named anywhere in the text disambiguate homonyms elsewhere in it
    # ("Santa Cruz … Bolivia" is the Bolivian one, not the Philippine town).
    named_cc = {p.country for w in words for p in idx.get(w[2].lower(), []) if p.type == "country"}
    for a in range(len(words) - 1):
        for p in idx.get(f"{words[a][2]} {words[a + 1][2]}".lower(), []):
            if p.type == "country":
                named_cc.add(p.country)
    found: dict[str, tuple[int, Place]] = {}
    i = 0
    while i < len(words):
        hit = None
        first = words[i][2]
        if not first[0].isupper() and first.lower() not in LOWER_OK:
            i += 1
            continue
        for n in range(min(MAX_WORDS, len(words) - i), 0, -1):
            span = text[words[i][0]:words[i + n - 1][1]]
            cands = idx.get(span.lower())
            if cands:
                pick = next((c for c in cands if c.country in named_cc), None) or                     next((c for c in cands if c.country == country_hint), cands[0])
                # A small one-word town outside Asia is too often an ordinary word ("Time",
                # "Normal", "Lens"): accept it only when the report also names its country.
                if n == 1 and pick.type == "city" and pick.country not in ASIA and pick.pop < 100_000                         and pick.country not in named_cc and pick.country != country_hint:
                    continue
                hit = (n, pick)
                break
        if hit:
            n, p = hit
            if p.name not in found:
                found[p.name] = (words[i][0], p)
            i += n
        else:
            i += 1
    from .translit import find_hindi_places
    for pos, p in find_native_places(text) + find_hindi_places(text):
        if p.name not in found:
            found[p.name] = (pos, p)
    return sorted(found.values(), key=lambda x: x[0])


def primary_place(places: list[tuple[int, Place]], country_hint: str = "") -> Place | None:
    """Most specific place, preferring ones early in the text and inside the hinted country."""
    if not places:
        return None
    def score(item):
        pos, p = item
        return (RANK.get(p.type, 9), 0 if (not country_hint or p.country == country_hint) else 1, pos)
    # Early mentions (headline/lede) carry the event location; later ones are often context.
    early = [x for x in places if x[0] < 400] or places
    return min(early, key=score)[1]


def _num(s: str) -> float:
    s = s.lower()
    return float(WORDNUM[s]) if s in WORDNUM else float(s.replace(",", ""))


def _money_inr(amount: str, scale: str | None) -> float | None:
    try:
        v = float(amount.replace(",", ""))
    except ValueError:
        return None
    mult = {"lakh": 1e5, "lakhs": 1e5, "crore": 1e7, "crores": 1e7, "cr": 1e7, "million": 1e6, "mn": 1e6,
            "billion": 1e9}.get((scale or "").lower(), 1)
    return v * mult


@dataclass
class Event:
    record_id: str
    url: str
    title: str
    outlet: str
    published: str
    source: str
    event_types: list[str] = field(default_factory=list)
    species: list[str] = field(default_factory=list)
    terms: list[str] = field(default_factory=list)
    place: dict | None = None
    places: list[str] = field(default_factory=list)
    countries: list[str] = field(default_factory=list)
    route: list[str] = field(default_factory=list)
    agencies: list[str] = field(default_factory=list)
    modes: list[str] = field(default_factory=list)
    platforms: list[str] = field(default_factory=list)
    ambiguous: list[dict] = field(default_factory=list)   # every ambiguous term hit, accepted or held (review)
    quantities: list[dict] = field(default_factory=list)
    value_inr: float | None = None
    people_arrested: int | None = None
    evidence: list[str] = field(default_factory=list)
    relevance: float | None = None
    trade_signal: float | None = None
    place_basis: str = ""  # "text" (named in the report) or "outlet" (publisher's home region)
    domain: str = ""       # publisher domain (Google News: from <source url>)
    tier: str = "media"    # official | ngo | media  (see sources_tier.py)

    def to_dict(self):
        return asdict(self)


_OUTLET_TAIL = re.compile(r"\s+[-–—|]\s+[^-–—|]{2,80}$")
_NUMBER = re.compile(r"\d")
_MANY = re.compile(r"(?<![\d.,])(?:[1-9]\d{1,}|[1-9]\d{0,2}(?:[.,]\d{3})+)(?![\d.,]*\s*(?:%|years?|anos|años|ans|साल|kg))")


def record_text(rec) -> str:
    """Headline and text without the " - Outlet" tail Google News appends (outlet names are not
    places or species: "La Patria", "Latina"), and without a snippet that only repeats the headline."""
    title = _OUTLET_TAIL.sub("", rec.title or "")
    text = rec.text or ""
    if "&nbsp;" in text or (len(text) < 300 and text[:40] == (rec.title or "")[:40]):
        text = ""
    return f"{title}. {text}".strip(" .")


def _any(text: str, words) -> bool:
    t = lexicon.prep(text)
    return any(lexicon.norm(w) in t for w in words)


def gate(text: str) -> tuple[bool, str]:
    """Is this report a wildlife-trade enforcement event? Returns (decision, reason) so every
    rejection can be counted and reviewed. Rules, each from the 2026-09-29 accuracy audit:
    a species; an event verb (topic words like "trafficking" alone are not events); no statistics;
    genre stories (features, programmes, reports) only with hard evidence (event verb and a number);
    rescue-only stories only with a trade or captivity word."""
    lex = lexicon.load()
    if sum(lexicon.count_cues(text, "negative_cues").values()):
        return False, "negative"
    if not lexicon.species_groups(text):
        return False, "no species"
    ev = {k: v for k, v in lexicon.count_cues(text, "enforcement_cues").items() if v}
    if not ev:
        return False, "topic only" if _any(text, [w for ws in (lex.get("topic_cues") or {}).values() for w in ws]) else "no event"
    if _any(text, [w for ws in (lex.get("aggregate_cues") or {}).values() for w in ws]):
        return False, "statistics"
    if _any(text, (lex.get("genre_cues") or {}).get("hard") or []):
        return False, "genre"              # unambiguous features and period summaries, whatever their numbers
    if _any(text, [w for k, ws in (lex.get("genre_cues") or {}).items() if k != "hard" for w in ws]) and not _NUMBER.search(text):
        return False, "genre"
    if set(ev) == {"rescue"} and not _any(text, lex.get("rescue_trade_context") or []) and not _MANY.search(text):
        return False, "rescue, no trade"      # a rescue of 10+ animals is almost always an interception
    return True, "event"


def is_enforcement_candidate(text: str) -> bool:
    return gate(text)[0]


@lru_cache(maxsize=1)
def _outlets() -> list[tuple[str, str]]:
    path = RESOURCES / "outlets.csv"
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return [(r["match"].lower(), r["place"]) for r in csv.DictReader(f)]


def outlet_place(outlet: str, url: str = "") -> Place | None:
    """Home region of a regional publisher: a fallback when the report names no place.
    Only publishers whose coverage is regional are listed (resources/outlets.csv)."""
    key = f"{outlet} {url}".lower()
    for m, name in _outlets():
        if m in key:
            hit = gazetteer().get(name.lower())
            if hit:
                return hit[0]
    return None


def extract(rec: Record) -> Event:
    text = record_text(rec)
    ev = Event(rec.id, rec.url, rec.title, rec.outlet, rec.published, rec.source)
    from ..sources_tier import domain as _domain, tier as _tier
    ev.domain = _domain((rec.extra or {}).get("source_url") or (rec.url if "news.google." not in rec.url else "") or rec.outlet)
    ev.tier = _tier(ev.domain)
    ev.species = lexicon.species_groups(text)
    ev.ambiguous = lexicon.ambiguous_hits(text)
    ev.terms = lexicon.matched_terms(text)
    ev.event_types = [k for k, v in lexicon.count_cues(text, "enforcement_cues").items() if v]
    ev.modes = [k for k, v in lexicon.count_cues(text, "modes").items() if v]
    ev.platforms = [k for k, v in lexicon.count_cues(text, "platforms").items() if v]
    if ev.platforms and "online" not in ev.modes:
        ev.modes.append("online")

    ags = []
    for region, names in lexicon.load()["agencies"].items():
        for n in names:
            if re.search(r"(?<![A-Za-z])" + re.escape(n) + r"(?![A-Za-z])", text, re.I if len(n) > 5 else 0):
                ags.append(AGENCY_CANON.get(n.lower(), n if n.isupper() else n.title()))
    ev.agencies = sorted(set(ags))

    hint = rec.country_hint if len(rec.country_hint) == 2 else ""
    places = find_places(text, hint)
    # A place whose name is also a species word ("Badak" = rhino in Indonesian) is not trusted as a place.
    places = [(i, p) for i, p in places if not lexicon.species_groups(p.name) or p.type in ("country", "state")]
    pp = primary_place(places, hint)
    if pp:
        ev.place = asdict(pp); ev.place_basis = "text"
    elif (op := outlet_place(rec.outlet, rec.url)) is not None:
        ev.place = asdict(op); ev.place_basis = "outlet"
    ev.places = [p.name for _, p in places]
    ev.countries = sorted({p.country for _, p in places})

    for m in ROUTE.finditer(text):
        a, b = find_places(m.group(1)), find_places(m.group(2))
        if a and b:
            ev.route = [a[0][1].name, b[0][1].name]; ev.evidence.append(m.group(0)); break
    if not ev.route:
        m = DEST.search(text)
        if m and (b := find_places(m.group(1))) and pp and b[0][1].name != pp.name:
            ev.route = [pp.name, b[0][1].name]; ev.evidence.append(m.group(0))

    hits: list[tuple[int, int, re.Match]] = []
    for rx in (QTY, QTY_GAP):
        for m in rx.finditer(text):
            if not any(a < m.end() and m.start() < b for a, b, _ in hits):
                hits.append((m.start(), m.end(), m))
    for _, _, m in sorted(hits, key=lambda h: h[0]):  # text order: headline quantities lead
        if _num(m.group(1)) <= 0:
            continue
        ev.quantities.append({"value": _num(m.group(1)), "unit": m.group(2).lower()})
        ev.evidence.append(m.group(0))
    m = MONEY.search(text)
    if m:
        v = _money_inr(m.group(1), m.group(2))
        if v and ("$" in m.group(0) or "usd" in m.group(0).lower()):
            v = None  # keep currencies separate; only INR totals are summed
        ev.value_inr = v
        ev.evidence.append(m.group(0))
    m = PEOPLE.search(text) or PEOPLE_SHORT.search(text)
    if m:
        ev.people_arrested = int(_num(m.group(1))); ev.evidence.append(m.group(0))
    elif (m := PEOPLE_HI.search(text)):
        g = m.group(1)
        ev.people_arrested = HINDI_NUM.get(g) or int(g); ev.evidence.append(m.group(0))
    return ev
