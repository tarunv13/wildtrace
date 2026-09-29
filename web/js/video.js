// The 2-minute video guide: a real recording of the question-first Atlas (ask, answer, evidence)
// (scripts/make_guide.py). It opens by itself on a first visit; after that from the Guide button, the
// card at the top of Pulse, About, or #guide. Captions are burned into the picture and also offered as
// a text track for screen readers.
const KEY = "wildtrace.guide";       // "seen" once a reader has been shown the video
const store = {
  get: (k) => { try { return localStorage.getItem(k); } catch { return null; } },
  set: (k, v) => { try { localStorage.setItem(k, v); } catch { /* private window */ } },
};
let root = null, lastFocus = null;

/** True for a reader who has never been shown the video in this browser. */
export const firstVisit = () => store.get(KEY) !== "seen";

/** `first`: the welcome version, muted autoplay with "take the tour / explore" choices underneath. */
export function openGuide({ first = false } = {}) {
  if (root) return;
  store.set(KEY, "seen");
  lastFocus = document.activeElement;
  root = document.createElement("div");
  root.className = "guide";
  root.innerHTML = `
    <div class="guide-veil"></div>
    <div class="guide-card glass" role="dialog" aria-modal="true" aria-label="WildTrace in 2 minutes: video guide">
      ${first ? `<div class="guide-hello">Welcome to WildTrace, the open atlas of illegal wildlife trade</div>` : ""}
      <div class="guide-head"><b>WildTrace in 2 minutes</b><span class="muted">Ask a question, read the answer, check the evidence</span>
        <button class="icon-btn" aria-label="Close the video"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 6l12 12M18 6 6 18"/></svg></button></div>
      <video controls playsinline muted preload="${first ? "auto" : "metadata"}" poster="media/guide.jpg">
        <source src="media/guide.mp4" type="video/mp4">
        <track kind="captions" src="media/guide.vtt" srclang="en" label="English">
        Your browser cannot play this video. <a href="media/guide.mp4" download>Download it (MP4, 3 MB)</a>.
      </video>
      <div class="guide-foot"><span class="muted">1 min 39 s · no sound, captions on screen · <a href="media/guide.mp4" download>download MP4</a> · find it again under <b>▶ Guide</b></span>
        ${first ? `<span class="row"><button class="btn" data-g="explore">${innerWidth < 860 ? "Start exploring" : "Explore on my own"}</button>${innerWidth < 860 ? "" : `<button class="btn primary" data-g="tour">Take the guided tour</button>`}</span>` : ""}</div>
    </div>`;
  document.body.append(root);
  const close = () => { root?.remove(); root = null; removeEventListener("keydown", onKey, true); lastFocus?.focus?.(); };
  const onKey = (e) => { if (e.key === "Escape") { e.preventDefault(); close(); } };
  addEventListener("keydown", onKey, true);
  root.querySelector(".guide-veil").addEventListener("click", close);
  root.querySelector(".guide-head button").addEventListener("click", close);
  root.querySelector('[data-g="explore"]')?.addEventListener("click", close);
  root.querySelector('[data-g="tour"]')?.addEventListener("click", () => { close(); dispatchEvent(new CustomEvent("wildtrace:tour")); });
  const v = root.querySelector("video");
  v.focus();
  v.play?.().catch(() => { /* the reader presses play */ });
}
