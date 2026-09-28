"""RSS/Atom feeds listed in resources/sources.yaml, plus opt-in Google News RSS search.

Only the standard library parses XML, so no extra dependency is needed.
"""
from __future__ import annotations

import email.utils
import re
import xml.etree.ElementTree as ET
from urllib.parse import quote_plus, urlparse

import yaml

from .. import lexicon
from ..config import RESOURCES
from ..schema import Record
from .base import get

_TAG = re.compile(r"<[^>]+>")


def _date(s: str) -> str:
    if not s:
        return ""
    try:
        return email.utils.parsedate_to_datetime(s).strftime("%Y-%m-%d")
    except (TypeError, ValueError):
        return s[:10] if re.match(r"\d{4}-\d{2}-\d{2}", s) else ""


def parse(xml: bytes, source: str, country: str = "", kind: str = "news", query: str = "") -> list[Record]:
    try:
        root = ET.fromstring(xml)
    except ET.ParseError:
        return []
    ns = {"a": "http://www.w3.org/2005/Atom"}
    items = root.findall(".//item") or root.findall(".//a:entry", ns)
    out = []
    for it in items:
        def t(tag):
            el = it.find(tag) if not tag.startswith("a:") else it.find(tag, ns)
            return (el.text or "").strip() if el is not None and el.text else ""
        link = t("link")
        if not link:
            el = it.find("a:link", ns)
            link = el.get("href", "") if el is not None else ""
        src_el = it.find("source")
        outlet = (src_el.text or "").strip() if src_el is not None and src_el.text else urlparse(link).netloc
        # Google News wraps links; the publisher's own address is on <source url="...">.
        src_url = src_el.get("url", "") if src_el is not None else ""
        desc = _TAG.sub(" ", t("description") or t("a:summary"))
        out.append(Record(url=link, title=t("title") or t("a:title"), text=desc.strip(), source=source,
                          outlet=outlet, published=_date(t("pubDate") or t("a:updated")),
                          country_hint=country, kind=kind, query=query,
                          extra={"source_url": src_url} if src_url else {}))
    return out


def registry() -> dict:
    with open(RESOURCES / "sources.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def collect_feeds() -> list[Record]:
    recs = []
    for s in registry().get("sources", []):
        if s.get("access") != "rss" or not s.get("enabled", True) or not s.get("feed"):
            continue
        r = get(s["feed"])
        got = parse(r.content, s["id"], s.get("country", ""), s.get("kind", "news")) if r is not None and r.ok else []
        # Official feeds carry everything a ministry publishes; keep wildlife items only.
        got = [x for x in got if lexicon.species_groups(x.title + " " + x.text)
               or re.search(r"wildlife|forest|poach|smuggl|cites", x.title + x.text, re.I)]
        print(f"  feed {s['id']}: {len(got)} wildlife items")
        recs += got
    return recs


GNEWS_EDITIONS = {  # edition: (hl, gl, ceid, lexicon language key)
    # South & Southeast Asia
    "IN": ("en-IN", "IN", "IN:en", "en"), "IN-hi": ("hi", "IN", "IN:hi", "hi"),
    "TH": ("en", "TH", "TH:en", "en"), "VN": ("vi", "VN", "VN:vi", "vi"), "ID": ("id", "ID", "ID:id", "id_ms"),
    "MY": ("en-MY", "MY", "MY:en", "en"), "PH": ("en-PH", "PH", "PH:en", "en"), "SG": ("en-SG", "SG", "SG:en", "en"),
    # Africa (source and transit)
    "ZA": ("en-ZA", "ZA", "ZA:en", "en"), "NG": ("en-NG", "NG", "NG:en", "en"), "KE": ("en-KE", "KE", "KE:en", "en"),
    "UG": ("en-UG", "UG", "UG:en", "en"), "SN": ("fr", "SN", "SN:fr", "fr"),
    # Latin America (source)
    "BR": ("pt-BR", "BR", "BR:pt-419", "pt"), "MX": ("es-419", "MX", "MX:es-419", "es"), "CO": ("es-419", "CO", "CO:es-419", "es"),
    "PE": ("es-419", "PE", "PE:es-419", "es"), "AR": ("es-419", "AR", "AR:es-419", "es"),
    # Demand and transit markets
    "US": ("en-US", "US", "US:en", "en"), "GB": ("en-GB", "GB", "GB:en", "en"), "FR": ("fr", "FR", "FR:fr", "fr"),
    "AU": ("en-AU", "AU", "AU:en", "en"), "HK": ("en-HK", "HK", "HK:en", "en"),
}
LOCAL_CUES = {
    "en": "(seized OR arrested OR smuggling OR trafficking)", "hi": "(जब्त OR गिरफ्तार OR तस्करी)",
    "vi": "(bắt giữ OR buôn lậu)", "id_ms": "(disita OR ditangkap OR penyelundupan)",
    "pt": "(apreensão OR apreendidos OR resgata OR tráfico)", "es": "(decomiso OR incautan OR detenidos OR tráfico)",
    "fr": "(saisie OR arrêtés OR trafic)",
}


def _when(w: str) -> str:
    """Google News `when:` takes hours, days or years; "12m" is read as minutes and returns nothing.
    Months are converted: 12m -> 1y, 3m -> 90d."""
    w = (w or "30d").strip().lower()
    if w.endswith("m") and w[:-1].isdigit():
        n = int(w[:-1])
        return f"{n // 12}y" if n % 12 == 0 else f"{n * 30}d"
    return w


def collect_gnews(editions: list[str] | None = None, when: str = "30d", groups: set[str] | None = None) -> list[Record]:
    """Google News RSS search. OPT-IN: Google's feed terms allow personal,
    non-commercial use only. Enable deliberately (``--gnews``) for research runs,
    and publish only derived facts (event, species, place), never the feed itself.
    Each edition is searched in its own language where the lexicon has terms."""
    recs = []
    lex = lexicon.load()["groups"]
    for ed in editions or ["IN"]:
        hl, gl, ceid, lang = GNEWS_EDITIONS[ed]
        cue = LOCAL_CUES.get(lang, LOCAL_CUES["en"])
        for gid, g in lex.items():
            if groups and gid not in groups:   # --groups: aim a run at newly added species groups
                continue
            local = [t for t in (g["terms"].get(lang) or []) if len(t) > 3][:3]
            if not local and lang != "en":
                continue  # nothing to say in this language: the English editions cover it
            terms = local or [t for t in g["terms"].get("en", []) if len(t) > 4][:3]
            if not terms:
                continue
            q = "(" + " OR ".join(f'"{t}"' for t in terms) + f") {cue} when:{_when(when)}"
            url = f"https://news.google.com/rss/search?q={quote_plus(q)}&hl={hl}&gl={gl}&ceid={ceid}"
            r = get(url, delay=3, check_robots=False)
            got = parse(r.content, "gnews", gl, "news", q) if r is not None and r.ok else []
            if got:
                print(f"  gnews {ed} {gid}: {len(got)}")
            recs += got
    return recs


# ------------------------------------------------------------------ online trade, enforcement end
# ECO-SOLVE and WILDTRADE watch the adverts. These searches find what happens after: reports of
# seizures, arrests and convictions that name a platform or online sale. Each language gets one
# query: [wildlife words] AND [online words], plus enforcement words where the edition accepts them.
ONLINE_QUERIES = {
    "en": '(wildlife OR "protected species" OR "exotic animals" OR pangolin OR parrots OR orchids) '
          '(Facebook OR WhatsApp OR Telegram OR Instagram OR TikTok OR online OR "social media") (seized OR arrested OR convicted)',
    # Google News returns nothing for three OR-groups in these editions; the enforcement screen runs later anyway.
    "pt": '("animais silvestres" OR "fauna silvestre" OR "aves silvestres") (internet OR "redes sociais" OR Facebook OR WhatsApp)',
    "es": '("fauna silvestre" OR "especies protegidas" OR "tráfico de fauna") (Facebook OR "redes sociales" OR internet)',
    "fr": '("espèces protégées" OR "faune sauvage" OR pangolin) (Facebook OR "réseaux sociaux" OR internet)',
    "hi": '(वन्यजीव OR तोता OR कछुआ OR तस्करी) (ऑनलाइन OR "सोशल मीडिया" OR फेसबुक)',
    "vi": '("động vật hoang dã" OR "động vật quý hiếm") ("mạng xã hội" OR Facebook OR Zalo)',
    "id_ms": '("satwa dilindungi" OR "satwa liar") (online OR "media sosial" OR Facebook)',
}


def collect_gnews_online(editions: list[str] | None = None, when: str = "30d") -> list[Record]:
    """Google News searches for online wildlife crime reaching enforcement (same terms as collect_gnews)."""
    recs, seen = [], set()
    for ed in editions or list(GNEWS_EDITIONS):
        hl, gl, ceid, lang = GNEWS_EDITIONS[ed]
        q = ONLINE_QUERIES.get(lang)
        if not q:
            continue
        q = f"{q} when:{_when(when)}"
        url = f"https://news.google.com/rss/search?q={quote_plus(q)}&hl={hl}&gl={gl}&ceid={ceid}"
        r = get(url, delay=3, check_robots=False)
        got = [x for x in (parse(r.content, "gnews", gl, "news", q) if r is not None and r.ok else []) if x.id not in seen]
        seen.update(x.id for x in got)
        if got:
            print(f"  gnews-online {ed}: {len(got)}")
        recs += got
    return recs


# ------------------------------------------------------------------ official sources
# Government, enforcement and judicial publishers, searched through their own domains.
# (site, edition, language). Official releases are the backbone of a validated record.
OFFICIAL_SITES = [
    ("gov.br", "BR", "pt"), ("gob.mx", "MX", "es"), ("gob.pe", "PE", "es"), ("gov.co", "CO", "es"), ("gob.ar", "AR", "es"),
    ("go.id", "ID", "id_ms"), ("gov.ph", "PH", "en"), ("gov.in", "IN", "en"), ("nic.in", "IN", "en"), ("gov.za", "ZA", "en"),
    ("go.ke", "KE", "en"), ("justice.gov", "US", "en"), ("fws.gov", "US", "en"), ("info.gov.hk", "HK", "en"), ("gov.sg", "SG", "en"),
    ("gov.my", "MY", "en"), ("gov.lk", "US", "en"), ("gov.la", "US", "en"), ("gov.vn", "VN", "vi"), ("go.th", "TH", "en"),
    ("gov.au", "AU", "en"), ("gov.uk", "GB", "en"), ("gouv.fr", "FR", "fr"), ("interpol.int", "US", "en"), ("europa.eu", "GB", "en"),
]
OFFICIAL_TERMS = {
    "en": '(wildlife OR pangolin OR ivory OR "rhino horn" OR turtles OR tortoises OR parrots OR "endangered species" OR "red sanders" OR rosewood)',
    "pt": '("animais silvestres" OR "tráfico de animais" OR "fauna silvestre" OR "aves silvestres" OR "madeira ilegal")',
    "es": '("fauna silvestre" OR "tráfico de especies" OR "vida silvestre" OR "especies protegidas" OR totoaba)',
    "fr": "(\"espèces protégées\" OR \"trafic d'espèces\" OR ivoire OR pangolin)",
    "id_ms": '("satwa dilindungi" OR "perdagangan satwa" OR trenggiling OR "satwa liar")',
    "vi": '("động vật hoang dã" OR "tê tê" OR "ngà voi")',
}


def collect_official(since: str = "2024-01-01") -> list[Record]:
    """Official releases about wildlife seizures, arrests and convictions, from
    government domains worldwide (one Google News query per domain)."""
    recs = []
    for site, ed, lang in OFFICIAL_SITES:
        hl, gl, ceid, _ = GNEWS_EDITIONS[ed]
        q = f"{OFFICIAL_TERMS[lang]} {LOCAL_CUES.get(lang, LOCAL_CUES['en'])} site:{site} after:{since}"
        url = f"https://news.google.com/rss/search?q={quote_plus(q)}&hl={hl}&gl={gl}&ceid={ceid}"
        r = get(url, delay=3, check_robots=False)
        got = parse(r.content, "official", gl, "official", q) if r is not None and r.ok else []
        print(f"  official {site}: {len(got)}")
        recs += got
    return recs


def collect_history(months: int = 12, editions: tuple[str, ...] = ("IN", "US", "GB", "ZA", "NG", "BR", "MX", "ID", "PH", "TH")) -> list[Record]:
    """Backfill: one query per month, edition and batch of species terms, using
    Google News' after:/before: operators. Gives the timeline real history instead of
    a 30-day spike."""
    from datetime import date
    lex = lexicon.load()["groups"]
    recs = []
    today = date.today().replace(day=1)
    windows = []
    for k in range(1, months + 1):
        y, m = divmod(today.year * 12 + today.month - 1 - k, 12)
        start = date(y, m + 1, 1)
        y2, m2 = divmod(y * 12 + m + 1, 12)
        windows.append((start, date(y2, m2 + 1, 1)))
    for ed in editions:
        hl, gl, ceid, lang = GNEWS_EDITIONS[ed]
        terms = [t for g in lex.values() for t in (g["terms"].get(lang) or g["terms"].get("en") or [])[:2] if len(t) > 4]
        batches = [terms[i:i + 10] for i in range(0, len(terms), 10)]
        for start, end in windows:
            for b in batches:
                q = "(" + " OR ".join(f'"{t}"' for t in b) + f") {LOCAL_CUES.get(lang, LOCAL_CUES['en'])} after:{start} before:{end}"
                url = f"https://news.google.com/rss/search?q={quote_plus(q)}&hl={hl}&gl={gl}&ceid={ceid}"
                r = get(url, delay=3, check_robots=False, cache_hours=24 * 30)
                got = parse(r.content, "gnews", gl, "news", q) if r is not None and r.ok else []
                recs += got
            print(f"  history {ed} {start:%Y-%m}: {len(recs)} so far")
    return recs
