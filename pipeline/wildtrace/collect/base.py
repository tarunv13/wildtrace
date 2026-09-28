"""Polite HTTP: one shared session, robots.txt respected, fixed delay per host, disk cache."""
from __future__ import annotations

import hashlib
import json
import time
import urllib.robotparser
from pathlib import Path
from urllib.parse import urlparse

import requests

from ..config import RAW, REQUEST_DELAY_S, USER_AGENT
from ..schema import Record

_session = requests.Session()
_session.headers["User-Agent"] = USER_AGENT
_last_hit: dict[str, float] = {}
_robots: dict[str, urllib.robotparser.RobotFileParser | None] = {}
CACHE = RAW / "_http_cache"


def allowed(url: str) -> bool:
    host = urlparse(url).scheme + "://" + urlparse(url).netloc
    if host not in _robots:
        rp = urllib.robotparser.RobotFileParser(host + "/robots.txt")
        try:
            rp.read()
        except Exception:
            rp = None  # unreachable robots.txt: treat as allowed, like most crawlers
        _robots[host] = rp
    rp = _robots[host]
    return True if rp is None else rp.can_fetch(USER_AGENT, url)


def get(url: str, params: dict | None = None, delay: float | None = None, cache_hours: float = 12,
        check_robots: bool = True, timeout: int = 40, valid=None, retries: int = 4) -> requests.Response | None:
    key = hashlib.sha1((url + json.dumps(params or {}, sort_keys=True)).encode()).hexdigest()
    cpath = CACHE / f"{key}.bin"
    if cpath.exists() and time.time() - cpath.stat().st_mtime < cache_hours * 3600:
        r = requests.Response(); r._content = cpath.read_bytes(); r.status_code = 200; r.url = url
        r.encoding = "utf-8"
        return r
    if check_robots and not allowed(url):
        print(f"  robots.txt disallows {url}; skipped")
        return None
    host = urlparse(url).netloc
    wait = (delay if delay is not None else REQUEST_DELAY_S) - (time.time() - _last_hit.get(host, 0))
    if wait > 0:
        time.sleep(wait)
    for attempt in range(retries):
        try:
            r = _session.get(url, params=params, timeout=timeout)
            _last_hit[host] = time.time()
            if r.status_code == 429:
                # GDELT-style throttles escalate if you keep knocking: wait 1, 2, 4, 5 minutes.
                pause = min(300, 60 * 2 ** attempt)
                print(f"  {host}: 429 rate-limited; backing off {pause}s")
                time.sleep(pause); continue
            if r.ok and (valid is None or valid(r)):
                CACHE.mkdir(parents=True, exist_ok=True)
                cpath.write_bytes(r.content)
            return r
        except requests.RequestException as e:
            print(f"  {host}: {e.__class__.__name__}; retry {attempt + 1}/{retries}")
            time.sleep(5 * (attempt + 1))
    return None


def write_jsonl(records: list[Record], name: str) -> Path:
    RAW.mkdir(parents=True, exist_ok=True)
    path = RAW / f"{time.strftime('%Y%m%d')}_{name}.jsonl"
    seen = set()
    if path.exists():
        seen = {json.loads(l)["id"] for l in path.read_text(encoding="utf-8").split("\n") if l.strip()}
    with path.open("a", encoding="utf-8") as f:
        for r in records:
            if r.id not in seen:
                # U+2028/U+2029 are legal inside JSON strings but end a line for splitlines(): escape them.
                line = json.dumps(r.to_dict(), ensure_ascii=False).replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
                f.write(line + "\n"); seen.add(r.id)
    return path


def read_all_raw() -> list[Record]:
    out: dict[str, Record] = {}
    for p in sorted(RAW.glob("*.jsonl")):
        # split("\n"), not splitlines(): older files may carry raw U+2028/U+2029 inside a record.
        for line in p.read_text(encoding="utf-8").split("\n"):
            if line.strip():
                d = json.loads(line)
                out.setdefault(d["id"], Record.from_dict(d))
    return list(out.values())
