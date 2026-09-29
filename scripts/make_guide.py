"""Record the 2-minute "How to use WildTrace" guide from the live site.

    python scripts/make_guide.py [--base URL]

A real browser plays a scripted walkthrough: the question-first opening, an answer with its sources, routes, accuracy, with captions
and a visible cursor drawn into the page (motion on the OpenHiggsfield easing: cubic-bezier(0.2, 0,
0, 1) in, cubic-bezier(0.4, 0, 1, 1) out). Nothing is generated: every frame is the real interface.
Outputs web/media/guide.mp4 (H.264, plays everywhere), guide.jpg (poster), guide-thumb.jpg (Pulse card) and guide.vtt (captions for
screen readers). Needs Playwright's Chromium and ffmpeg.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "web" / "media"
BASE = sys.argv[sys.argv.index("--base") + 1] if "--base" in sys.argv else "https://tarunv13.github.io/wildtrace/"
EXE = os.environ.get("WILDTRACE_CHROMIUM") or None
W, H = 1280, 720

# Caption bar, title card, cursor and highlight ring, injected into the page.
OVERLAY = r"""
(() => {
  if (window.__guide) return;
  const css = document.createElement('style');
  css.textContent = `
  .g-cap{position:fixed;left:50%;bottom:22px;transform:translate(-50%,16px);opacity:0;z-index:2147483000;max-width:880px;
    padding:14px 22px 15px;border-radius:18px;background:rgba(15,26,23,.86);color:#fff;font:500 19px/1.4 Geist,system-ui,sans-serif;
    box-shadow:0 18px 40px -16px rgba(0,0,0,.55);pointer-events:none;transition:opacity .45s cubic-bezier(.2,0,0,1),transform .55s cubic-bezier(.2,0,0,1);text-align:center}
  .g-cap.on{opacity:1;transform:translate(-50%,0)}
  .g-cap small{display:block;font:600 12px/1 Geist,system-ui,sans-serif;letter-spacing:.09em;text-transform:uppercase;color:#f0c35a;margin-bottom:7px}
  .g-title{position:fixed;inset:0;z-index:2147483001;display:grid;place-items:center;background:rgba(237,241,239,.94);backdrop-filter:blur(10px);
    opacity:0;pointer-events:none;transition:opacity .5s cubic-bezier(.2,0,0,1)}
  .g-title.on{opacity:1}
  .g-title div{text-align:center;max-width:900px;padding:0 40px;transform:translateY(10px);transition:transform .7s cubic-bezier(.16,1,.3,1)}
  .g-title.on div{transform:none}
  .g-title h1{font:800 54px/1.05 "Bricolage Grotesque",Geist,sans-serif;letter-spacing:-.03em;color:#0f1a17;margin:0 0 14px}
  .g-title p{font:500 22px/1.45 Geist,sans-serif;color:#3c4a45;margin:0}
  .g-title small{display:block;font:600 14px/1 Geist,sans-serif;letter-spacing:.12em;text-transform:uppercase;color:#8a5300;margin-bottom:16px}
  .g-cur{position:fixed;left:0;top:0;width:22px;height:22px;margin:-11px 0 0 -11px;border-radius:50%;z-index:2147483002;pointer-events:none;
    background:rgba(101,80,200,.28);border:2.5px solid #6550c8;box-shadow:0 2px 10px rgba(0,0,0,.25);
    transition:left .7s cubic-bezier(.2,0,0,1),top .7s cubic-bezier(.2,0,0,1),transform .18s}
  .g-cur.tap{transform:scale(.7)}
  .g-ring{position:fixed;z-index:2147482999;border-radius:14px;box-shadow:0 0 0 3px #f0c35a,0 0 0 9999px rgba(15,26,23,.12);pointer-events:none;
    transition:all .45s cubic-bezier(.2,0,0,1);opacity:0}
  .g-ring.on{opacity:1}`;
  document.head.append(css);
  const cap = Object.assign(document.createElement('div'), { className: 'g-cap' });
  const title = Object.assign(document.createElement('div'), { className: 'g-title' });
  const cur = Object.assign(document.createElement('div'), { className: 'g-cur' });
  const ring = Object.assign(document.createElement('div'), { className: 'g-ring' });
  document.body.append(ring, cap, title, cur);
  cur.style.left = innerWidth / 2 + 'px'; cur.style.top = innerHeight / 2 + 'px';
  window.__guide = {
    cap(text, eyebrow) { cap.classList.remove('on'); setTimeout(() => { cap.innerHTML = (eyebrow ? `<small>${eyebrow}</small>` : '') + text; cap.classList.add('on'); }, text ? 180 : 0); if (!text) cap.classList.remove('on'); },
    title(h, p, eyebrow) { if (!h) { title.classList.remove('on'); return; } title.innerHTML = `<div>${eyebrow ? `<small>${eyebrow}</small>` : ''}<h1>${h}</h1><p>${p || ''}</p></div>`; requestAnimationFrame(() => title.classList.add('on')); },
    point(sel) { const el = document.querySelector(sel); if (!el) return false; el.scrollIntoView({ block: 'nearest' }); const r = el.getBoundingClientRect();
      cur.style.left = (r.left + r.width / 2) + 'px'; cur.style.top = (r.top + r.height / 2) + 'px';
      Object.assign(ring.style, { left: r.left - 6 + 'px', top: r.top - 6 + 'px', width: r.width + 12 + 'px', height: r.height + 12 + 'px' }); ring.classList.add('on'); return true; },
    tap() { cur.classList.add('tap'); setTimeout(() => cur.classList.remove('tap'), 180); setTimeout(() => ring.classList.remove('on'), 500); },
  };
})();
"""

cues: list[tuple[float, str]] = []
cuts: list[tuple[float, float]] = []   # loading waits removed in the edit (jump cuts)


def _ffmpeg() -> str:
    """ffmpeg on PATH, else the binary bundled with imageio-ffmpeg."""
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="wt-guide-"))
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=EXE, args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
        ctx = b.new_context(viewport={"width": W, "height": H}, record_video_dir=str(tmp), record_video_size={"width": W, "height": H})
        ctx.add_init_script("localStorage.setItem('wildtrace.tour.v2','done');localStorage.setItem('wildtrace.tips','off');localStorage.setItem('wildtrace.guide','seen');localStorage.removeItem('wildtrace.basemap');")
        pg = ctx.new_page()
        t0 = time.time()
        pg.goto(BASE, wait_until="domcontentloaded")
        pg.wait_for_timeout(9000)                                   # map, tiles and data settle
        pg.evaluate(OVERLAY)
        fold = pg.locator(".tv-toggle")
        if fold.count():
            fold.first.click()                                      # fold the trivia box: it covers the map
        start = time.time() - t0                                    # everything before this is cut

        def at() -> float:
            return time.time() - t0 - start

        def say(text, eyebrow="", hold=3.2):
            pg.evaluate("([t, e]) => window.__guide.cap(t, e)", [text, eyebrow])
            cues.append((at(), (f"{eyebrow}: " if eyebrow else "") + text))
            pg.wait_for_timeout(int(hold * 1000))

        def card(h, sub="", eyebrow="", hold=3.2):
            pg.evaluate("([h, p, e]) => window.__guide.title(h, p, e)", [h, sub, eyebrow])
            cues.append((at(), f"{(eyebrow + ': ') if eyebrow else ''}{h}{'' if h[-1] in '.?!' else '.'} {sub}".strip()))
            pg.wait_for_timeout(int(hold * 1000))
            pg.evaluate("() => window.__guide.title('')")
            pg.wait_for_timeout(500)

        def idle():
            """Return once the page paints again (two animation frames)."""
            for _ in range(3):
                pg.evaluate("() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))")
                pg.wait_for_timeout(300)

        def click(sel, wait=1.4, ready=None):
            """Point, tap, click. With `ready`, the wait until that element is drawn is cut from the video."""
            pg.evaluate("s => window.__guide.point(s)", sel)
            pg.wait_for_timeout(750)
            pg.evaluate("() => window.__guide.tap()")
            if ready:
                pg.evaluate("() => window.__guide.cap('')")                 # no stale caption over a new view
            pg.locator(sel).first.click()
            if ready:
                a = at() + 0.5
                pg.wait_for_selector(ready, state="visible", timeout=180000)
                idle()                                                  # a map re-projection blocks the page: cut it too
                pg.wait_for_timeout(1200)                               # let it settle on screen
                cuts.append((a, at() - 0.6))
            pg.wait_for_timeout(int(wait * 1000))

        def scroll_to(sel):
            pg.evaluate("s => document.querySelector(s)?.scrollIntoView({ block: 'center', behavior: 'smooth' })", sel)
            pg.wait_for_timeout(700)
            pg.evaluate("s => window.__guide.point(s)", sel)

        # ---- Intro: the Atlas opens with a question
        card("WildTrace in 2 minutes", "Ask a question. Get the answer, its sources and its limits.", "How to use", 3.4)
        pg.evaluate("s => window.__guide.point(s)", "#ask-h")
        say("The Atlas opens with a question, not a dashboard.", "Ask", 3.0)
        click('[data-persona="journalists"]', 0.6)
        say("Say who you are, and the questions change to fit.", "Ask", 2.6)

        # ---- Q1: an answer, and its anatomy
        card("Is wildlife sold online ever caught?", "", "Question 1 of 3", 2.4)
        click('.qcard[data-answer="is-wildlife-sold-online-ever-caught"]', 1.0, ready="#insp-body .answer-lede")
        say("Every answer: one line, its number and a chart.", "Question 1", 3.2)
        scroll_to("#insp-body .link-row")
        say("Who answers: each source is named and linked.", "Question 1", 2.8)
        scroll_to("#insp-body .box.limit")
        say("And what the number cannot tell you.", "Question 1", 2.8)
        click("#close", 0.8)

        # ---- Q2: follow the trade on the map
        card("Where does seized red sanders go?", "", "Question 2 of 3", 2.4)
        click('[data-mode="flows"]', 1.0, ready="#fs-body .route")
        say("Flows: seized shipments reported to CITES, from source to market.", "Question 2", 3.0)
        pg.evaluate("s => window.__guide.point(s)", "#f-addg")
        pg.wait_for_timeout(700)
        a = at() + 0.4
        pg.select_option("#f-addg", "red_sanders")
        pg.wait_for_selector('#fs-body .ev[data-route="s|IN|CN"]', timeout=120000)
        pg.wait_for_timeout(1500)
        cuts.append((a, at() - 0.8))
        say("Lines shade green at the source, blue in transit, amber at the market.", "Question 2", 3.2)
        click('#fs-body .ev[data-route="s|IN|CN"]', 1.6)
        say("Evidence: what was seized, when, who reported it, and the news.", "Question 2", 3.2)
        click("#close", 0.8)

        # ---- Q3: can I trust it?
        card("How accurate is WildTrace?", "", "Question 3 of 3", 2.4)
        click('[data-mode="cases"]', 1.0, ready="#ask-h")
        click('.qcard[data-answer="how-accurate-is-wildtrace"]', 1.0, ready="#insp-body .answer-lede")
        say("Measured, not asserted: a blind audit of 200 random cases.", "Question 3", 3.4)
        click("#close", 0.6)
        scroll_to("#pulse .feed .item")
        pg.wait_for_timeout(400)
        click("#pulse .feed .item", 1.4, ready="#insp-body .title")
        say("Each case: a plain account and its evidence grade.", "Question 3", 2.8)
        pg.evaluate("() => { const b = document.querySelector('#insp-body'); b.scrollTo({ top: b.scrollHeight, behavior: 'smooth' }); }")
        say("Every source is listed with its outlet. Nobody accused is ever named.", "Question 3", 3.0)
        click("#close", 0.6)

        # ---- Tools and close
        click('[data-sheet="investigate"]', 1.0, ready="#cy canvas")
        say("Investigate: a link chart, plus your own data, kept in your browser.", "Tools", 3.0)
        click("#sheet-close", 0.6)
        click('[data-sheet="analysis"]', 1.0, ready="#an-month svg")
        say("Analysis: the whole record on one sheet.", "Tools", 2.4)
        click("#sheet-close", 0.6)
        card("Open data, free to reuse", "Every answer has a citable page · download every case as CSV · DOI 10.5281/zenodo.22902819", "WildTrace · Follow the trade", 4.2)
        end = at()
        pg.close(); ctx.close(); b.close()

    webm = next(tmp.glob("*.webm"))
    cuts[:] = [(a, b) for a, b in cuts if b - a > 0.3]
    removed = lambda t: sum(max(0.0, min(t, b) - a) for a, b in cuts)
    keep = "+".join(f"between(t,{a:.2f},{b:.2f})" for a, b in cuts) or "0"
    cues[:] = [(t - removed(t), text) for t, text in cues]
    end_cut = end - removed(end)
    # Land under two minutes: a gentle speed-up (under 1.15x) is barely visible and keeps captions readable.
    speed = min(1.15, max(1.0, end_cut / 115.0))
    cues[:] = [(t / speed, text) for t, text in cues]
    end_cut /= speed
    # Cut the loading seconds, then encode small H.264 and VP9 files and a poster.
    common = ["-ss", f"{start:.2f}", "-i", str(webm), "-t", f"{end:.2f}", "-an",
              "-vf", f"fps=25,select='not({keep})',setpts=N/FRAME_RATE/TB/{speed:.4f},fps=25"]
    subprocess.run([_ffmpeg(), "-y", "-loglevel", "error", *common, "-c:v", "libx264", "-preset", "slow", "-crf", "30",
                    "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(OUT / "guide.mp4")], check=True)
    subprocess.run([_ffmpeg(), "-y", "-loglevel", "error", "-ss", "0.8", "-i", str(OUT / "guide.mp4"), "-frames:v", "1",
                    "-q:v", "4", str(OUT / "guide.jpg")], check=True)
    # Small thumbnail for the Pulse card: the globe from the Atlas scene (the title card reads as blank when small).
    subprocess.run([_ffmpeg(), "-y", "-loglevel", "error", "-ss", "5", "-i", str(OUT / "guide.mp4"), "-frames:v", "1",
                    "-vf", "crop=640:360:500:190,scale=240:-2", "-q:v", "4", str(OUT / "guide-thumb.jpg")], check=True)
    # Captions for screen readers (the same words are burned into the picture).
    def ts(t):
        t = max(0.0, t); return f"{int(t // 3600):02d}:{int(t % 3600 // 60):02d}:{t % 60:06.3f}"
    lines = ["WEBVTT", ""]
    for k, (t, text) in enumerate(cues):
        nxt = cues[k + 1][0] if k + 1 < len(cues) else end_cut
        lines += [ts(t), "-->", ""]
        lines[-3:] = [f"{ts(t)} --> {ts(max(t + 1, nxt - 0.1))}", text, ""]
    (OUT / "guide.vtt").write_text("\n".join(lines), encoding="utf-8")
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"guide: recorded {end:.1f}s, {len(cuts)} loading waits cut, x{speed:.2f} -> {end_cut:.1f}s -> {OUT}")


if __name__ == "__main__":
    main()
