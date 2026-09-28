"""Merge articles that report the same incident into one case.

Two events are the same case when they share a species group, the same
state/country, fall within 4 days of each other, and their titles overlap
(token Jaccard >= 0.25) or they share a quantity. Union-find keeps it linear-ish.
"""
from __future__ import annotations

import hashlib
import re
from collections import Counter
from datetime import date

from .. import lexicon
from .events import Event

_TOK = re.compile(r"[a-z0-9ऀ-ॿ]{3,}")
STOP = {"the", "and", "with", "from", "for", "worth", "seized", "arrested", "held", "news", "police", "forest",
        "times", "india", "post", "today", "express", "tribune", "hindu", "live", "video", "com"}


def _toks(s: str) -> set[str]:
    return {t for t in _TOK.findall(s.lower()) if t not in STOP}


def _d(s: str) -> date | None:
    try:
        return date.fromisoformat(s[:10])
    except (ValueError, TypeError):
        return None


def _country(e: Event) -> str | None:
    return e.place.get("country") if e.place else None


def _admin1(e: Event) -> str | None:
    # A publisher's home region is a hint, not evidence: it never splits or joins cases.
    if not e.place or e.place.get("type") == "country" or e.place_basis == "outlet":
        return None
    return e.place.get("admin1") or e.place["name"]


def compatible(a: Event, b: Event) -> bool:
    """Places agree or one is less precise ("India" vs "Golaghat, Assam")."""
    ca, cb = _country(a), _country(b)
    if ca and cb and ca != cb:
        return False
    ra, rb = _admin1(a), _admin1(b)
    return not (ra and rb and ra != rb)


def same_case(a: Event, b: Event) -> bool:
    """Same incident, or the same developing story.

    * within 4 days: title overlap >= 0.25, or a shared quantity;
    * within 12 days, same state: title overlap >= 0.12 (stories such as a rescue
      followed by a week of probe coverage are worded differently by each outlet);
    * one report without a place: needs overlap >= 0.30 within 4 days.
    """
    if not set(a.species) & set(b.species) or not compatible(a, b):
        return False
    da, db = _d(a.published), _d(b.published)
    days = abs((da - db).days) if da and db else 0
    ta, tb = _toks(a.title), _toks(b.title)
    jac = len(ta & tb) / max(len(ta | tb), 1)
    qa = {(q["value"], q["unit"]) for q in a.quantities}; qb = {(q["value"], q["unit"]) for q in b.quantities}
    if not a.place or not b.place:
        return days <= 4 and jac >= 0.30
    if days <= 4 and (jac >= 0.25 or bool(qa & qb)):
        return True
    # Same state, within two days, same arrest count and kind of event: the same
    # seizure reported in two languages (titles then share no words at all).
    if days <= 2 and _admin1(a) and _admin1(a) == _admin1(b) and a.people_arrested and             a.people_arrested == b.people_arrested and set(a.event_types) & set(b.event_types):
        return True
    return days <= 12 and _admin1(a) is not None and _admin1(a) == _admin1(b) and jac >= 0.12


def cluster(events: list[Event]) -> list[list[Event]]:
    parent = list(range(len(events)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]; i = parent[i]
        return i

    by_species: dict[str, list[int]] = {}
    for i, e in enumerate(events):
        for s in e.species:
            by_species.setdefault(s, []).append(i)
    for idx in by_species.values():
        for x in range(len(idx)):
            for y in range(x + 1, len(idx)):
                i, j = idx[x], idx[y]
                if find(i) != find(j) and same_case(events[i], events[j]):
                    parent[find(i)] = find(j)
    groups: dict[int, list[Event]] = {}
    for i, e in enumerate(events):
        groups.setdefault(find(i), []).append(e)
    return list(groups.values())


def _consensus_place(pool: list[dict], rank: dict) -> dict | None:
    """Where the case happened: the specific place (city, district, park) that the
    most reports name, if at least two do; otherwise the most precise place named.
    Stops a zoo the animals were later moved to from outranking the rescue site."""
    if not pool:
        return None
    specific = [p for p in pool if p["type"] not in ("state", "country", "region")]
    tally = Counter(p["name"] for p in specific)
    if tally and max(tally.values()) >= 2:
        top = max(tally, key=lambda n: (tally[n], -rank.get(next(p for p in specific if p["name"] == n)["type"], 9)))
        return next(p for p in specific if p["name"] == top)
    return min(pool, key=lambda p: rank.get(p["type"], 9))


def summarise(evs: list[Event]) -> dict:
    """One public case record. Built from extracted facts, not from headlines,
    so it carries no names of accused persons and no copied text."""
    evs = sorted(evs, key=lambda e: e.published or "9999")
    first = evs[0]
    species = sorted({s for e in evs for s in e.species})
    types = sorted({t for e in evs for t in e.event_types})
    rank = {"airport": 0, "park": 1, "city": 2, "district": 3, "region": 4, "state": 5, "country": 6}
    # A place named in any report beats a publisher's home region.
    named = [e.place for e in evs if e.place and e.place_basis != "outlet"]
    inferred = [e.place for e in evs if e.place and e.place_basis == "outlet"]
    pool = named or inferred
    place = _consensus_place(pool, rank)
    place_basis = "text" if named else ("outlet" if inferred else "")
    # Headline order: the first quantity reported is the lead item; the rest are listed.
    quantities = []
    for e in evs:
        for q in e.quantities:
            if q not in quantities:
                quantities.append(q)
    qty = quantities[0] if quantities else None
    value = max((e.value_inr for e in evs if e.value_inr), default=None)
    # The count most reports agree on; one outlier lede should not win (ties: the larger).
    counts = Counter(e.people_arrested for e in evs if e.people_arrested)
    people = max(counts, key=lambda k: (counts[k], k)) if counts else None
    route = next((e.route for e in evs if e.route), [])
    kind = ("conviction" if "conviction" in types else "seizure" if "seizure" in types else
            "arrest" if "arrest" in types else "rescue" if "rescue" in types else types[0] if types else "report")
    labels = [lexicon.group_label(s) for s in species]
    where = place["name"] if place else "location unknown"
    bits = [kind.capitalize(), ", ".join(labels) or "wildlife"]
    if qty:
        v = qty["value"]; bits.append(f"{int(v) if v == int(v) else v} {qty['unit']}")
    bits.append(where)
    cid = hashlib.sha1("|".join(sorted(e.record_id for e in evs)).encode()).hexdigest()[:12]
    return {
        "id": cid,
        "date": first.published,
        "kind": kind,
        "event_types": types,
        "summary": " · ".join(bits),
        "species": species,
        "place": place,
        "place_basis": place_basis,
        "places": sorted({p for e in evs for p in e.places}),
        "countries": sorted({c for e in evs for c in e.countries}),
        "route": route,
        "agencies": sorted({a for e in evs for a in e.agencies}),
        "modes": sorted({m for e in evs for m in e.modes}),
        "platforms": sorted({p for e in evs for p in getattr(e, "platforms", [])}),
        "quantity": qty,
        "quantities": quantities[:8],
        "value_inr": value,
        "people_arrested": people,
        "sources": [{"outlet": e.outlet, "url": e.url, "date": e.published, "domain": e.domain, "tier": e.tier} for e in evs],
        "n_sources": len(evs),
        "n_outlets": len({e.domain or e.outlet for e in evs}),
        "verification": ("official" if any(e.tier == "official" for e in evs)
                         else "corroborated" if len({e.domain or e.outlet for e in evs}) >= 2 else "single"),
        "confidence": round(min(1.0, 0.45 + 0.15 * len(evs) + (0.1 if place_basis == "text" else 0.03 if place else 0) + (0.1 if qty else 0)), 2),
    }
