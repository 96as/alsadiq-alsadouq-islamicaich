"""Step 2 end-to-end check on the showcase dist served at http://localhost:5385/page/meadow.

usage: PYTHONUTF8=1 python e2e-step2.py headless|headed [size ...]   (size = 2000x713)
Headed runs go off-screen (--window-position=-3000,0) and muted (--mute-audio), and close afterwards.
Writes results-<mode>.json and screenshots next to this file's out dir.
"""
import json
import os
import sys
import time
import urllib.request
from playwright.sync_api import sync_playwright

URL = "http://localhost:5385/page/meadow"
OUT = os.path.join(os.path.expanduser("~"), r"Documents\Alsadiq-3D\03-renders\studio\step2\e2e")
os.makedirs(OUT, exist_ok=True)
MODE = sys.argv[1] if len(sys.argv) > 1 else "headless"
SIZES = [tuple(int(x) for x in s.split("x")) for s in sys.argv[2:]] or [(2000, 713), (1440, 900), (390, 844), (360, 740)]

INIT = r"""
(() => {
  window.__plays = [];
  const orig = HTMLMediaElement.prototype.play;
  window.__tapFlag = false;
  HTMLMediaElement.prototype.play = function (...a) {
    window.__audioEl = this;
    window.__plays.push({ t: performance.now(), inTap: window.__tapFlag, active: !!(navigator.userActivation && navigator.userActivation.isActive) });
    return orig.apply(this, a);
  };
  window.addEventListener('click', (e) => { window.__tapFlag = true; window.__clickT = e.timeStamp; }, true);
  window.addEventListener('click', () => { window.__tapFlag = false; }, false);

  window.__walkLog = [];
  (() => {
    let last = '';
    const t0 = performance.now();
    const id = setInterval(() => {
      const c = window.__control && window.__control.current;
      if (!c || !c.info) return;
      const i = c.info;
      const key = [i.base, i.transition || '', i.walkState, i.shot || ''].join('|');
      if (key !== last) { last = key; window.__walkLog.push({ t: Math.round(performance.now() - t0), base: i.base, transition: i.transition || '', walkState: i.walkState, shot: i.shot || '', studio: i.studio }); }
      if (performance.now() - t0 > 20000) clearInterval(id);
    }, 40);
  })();
  window.__body = () => {
    const c = window.__control.current;
    let root = c.bones.head; while (root.parent) root = root.parent;
    let mesh = null;
    root.traverse((o) => { if (!mesh && o.isSkinnedMesh && o.morphTargetDictionary && 'aa' in o.morphTargetDictionary) mesh = o; });
    mesh.updateWorldMatrix(true, false);
    mesh.geometry.computeBoundingBox();
    const bb = mesh.geometry.boundingBox;
    const cam = c.camera;
    let minY = 1e9, maxY = -1e9;
    for (const x of [bb.min.x, bb.max.x]) for (const y of [bb.min.y, bb.max.y]) for (const z of [bb.min.z, bb.max.z]) {
      const v = new bb.min.constructor(x, y, z).applyMatrix4(mesh.matrixWorld).project(cam);
      minY = Math.min(minY, v.y); maxY = Math.max(maxY, v.y);
    }
    const vh = window.innerHeight;
    const topPx = (1 - maxY) / 2 * vh, botPx = (1 - minY) / 2 * vh;
    return { topPx, botPx, bodyPx: botPx - topPx, ofViewport: (botPx - topPx) / vh };
  };
  window.__startSampling = () => {
    const c = window.__control && window.__control.current;
    let root = c.bones.head; while (root.parent) root = root.parent;
    let mesh = null;
    root.traverse((o) => { if (!mesh && o.morphTargetDictionary && Object.keys(o.morphTargetDictionary).some((k) => /pp$/i.test(k))) mesh = o; });
    const d = mesh.morphTargetDictionary;
    const pick = (v) => { const k = Object.keys(d).find((x) => x.toLowerCase().endsWith(('_' + v).toLowerCase())) || Object.keys(d).find((x) => x.toLowerCase() === v.toLowerCase()); return k == null ? -1 : d[k]; };
    const idx = {}; for (const v of ['PP', 'aa', 'O', 'U', 'E', 'I']) idx[v] = pick(v);
    window.__samples = []; window.__sampling = true;
    const tick = () => {
      if (!window.__sampling) return;
      const a = window.__audioEl;
      const r = { t: a ? a.currentTime : -1, paused: a ? a.paused : true, now: performance.now(), jaw: c.info.jaw, shot: c.shot ? c.shot.amount : -1 };
      for (const [k, i] of Object.entries(idx)) r[k] = i >= 0 ? mesh.morphTargetInfluences[i] : null;
      window.__samples.push(r);
      requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
    return idx;
  };
  window.__stopSampling = () => { window.__sampling = false; return window.__samples; };
  window.__face = () => {
    const c = window.__control.current;
    const m = c.shot ? c.shot.metrics() : null;
    const ex = c.faceExact ? c.faceExact() : null;
    const vh = window.innerHeight;
    return { metrics: m, exact: ex, vh, vw: window.innerWidth, exactOfViewport: ex ? ex.px / vh : null };
  };
})();
"""


def fetch_json(path):
    return json.load(urllib.request.urlopen("http://localhost:5385/page/showcase-audio/" + path))


MANIFEST = fetch_json("manifest.json")["clips"]
ALIGN = {c["id"]: fetch_json(c["align"]) for c in MANIFEST}


def closure_check(clip, samples):
    """PP peak around each bilabial (م ب in Arabic; m b p in English), by audio time."""
    al = ALIGN[clip["id"]]
    chars, starts, ends = al["characters"], al["starts"], al["ends"]
    targets = "مب" if clip["lang"] == "ar" else "mbpMBP"
    res = []
    for ch, s, e in zip(chars, starts, ends):
        if ch not in targets:
            continue
        win = [x["PP"] for x in samples if x.get("PP") is not None and x["t"] >= 0 and s - 0.08 <= x["t"] <= e + 0.14]
        res.append({"ch": ch, "t": round(s, 3), "pp": round(max(win), 3) if win else None})
    return res


def vowel_check(samples):
    play = [x for x in samples if x["t"] > 0 and not x["paused"]]
    return {
        "aa_max": round(max([x["aa"] or 0 for x in play] or [0]), 3),
        "jaw_max": round(max([x["jaw"] or 0 for x in play] or [0]), 3),
        "pp_max": round(max([x["PP"] or 0 for x in play] or [0]), 3),
        "frames": len(play),
    }


def wait_ended(p, timeout=9000):
    t0 = time.time()
    while time.time() - t0 < timeout / 1000:
        done = p.evaluate("(() => { const a = window.__audioEl; return !!a && (a.ended || (a.paused && a.currentTime > 0.3)); })()")
        if done:
            return
        p.wait_for_timeout(100)
    raise RuntimeError("clip did not end")


def run():
    results = {"mode": MODE, "sizes": {}}
    with sync_playwright() as pw:
        args = ["--use-angle=d3d11", "--ignore-gpu-blocklist", "--mute-audio"]
        if MODE == "headed":
            args += ["--window-position=-3000,0"]
        browser = pw.chromium.launch(channel="msedge", headless=(MODE != "headed"), args=args)
        try:
            for (w, h) in SIZES:
                key = f"{w}x{h}"
                r = {"errors": [], "clips": []}
                results["sizes"][key] = r
                ctx = browser.new_context(viewport={"width": w, "height": h}, device_scale_factor=1)
                ctx.add_init_script(INIT)
                p = ctx.new_page()
                p.on("console", lambda m, r=r: r["errors"].append(m.text) if m.type == "error" else None)
                p.on("pageerror", lambda e, r=r: r["errors"].append("pageerror: " + str(e)))
                p.goto(URL, wait_until="networkidle", timeout=40000)
                p.wait_for_function("window.__control && window.__control.current && window.__control.current.shot", timeout=40000)
                wide = w >= 1024
                p.wait_for_selector("[data-speak-primary]" if wide else "[data-speak-quick]", timeout=20000)
                p.wait_for_timeout(2500)  # prefetch + settle
                idle = p.evaluate("window.__face()")
                r["idle"] = {"faceOfViewport": idle["exactOfViewport"], "facePx": idle["exact"]["px"] if idle["exact"] else None, "metricsAmount": idle["metrics"]["amount"]}
                r["walkLog"] = p.evaluate("window.__walkLog")
                r["idleBody"] = p.evaluate("window.__body()")
                r["meadow"] = p.evaluate("(() => { const el = document.querySelector('[data-meadow-life]'); return el ? { state: el.getAttribute('data-meadow-life'), canvases: el.querySelectorAll('canvas').length } : null; })()") or {}
                import io
                import numpy as np
                from PIL import Image, ImageChops
                shot_a = Image.open(io.BytesIO(p.screenshot())).convert("RGB")
                p.wait_for_timeout(1200)
                shot_b = Image.open(io.BytesIO(p.screenshot())).convert("RGB")
                diff = np.asarray(ImageChops.difference(shot_a, shot_b)).astype("int16").sum(axis=2)
                r["meadow"]["pixelsChanged"] = int((diff > 12).sum())
                r["meadow"]["share"] = round(float((diff > 12).mean()), 4)
                p.screenshot(path=f"{OUT}\\{MODE}-{key}-idle.png")
                idx = p.evaluate("window.__startSampling()")
                r["morphIdx"] = idx

                # ---- first tap: the primary control (wide) or the quick button (phone) ----
                sel = "[data-speak-primary]" if wide else "[data-speak-quick]"
                p.click(sel)
                p.wait_for_timeout(2600)
                face = p.evaluate("window.__face()")
                p.screenshot(path=f"{OUT}\\{MODE}-{key}-speaking.png")
                r["speaking"] = {
                    "exactPx": face["exact"]["px"], "exactOfViewport": face["exactOfViewport"],
                    "projectedPx": face["metrics"]["facePx"], "projectedOfViewport": face["metrics"]["faceOfViewport"],
                    "amount": face["metrics"]["amount"], "boost": face["metrics"]["boost"],
                    "faceTop": face["exact"]["top"], "faceBottom": face["exact"]["bottom"], "stageH": face["metrics"]["stageH"],
                    "cameraZ": face["metrics"]["camera"]["z"],
                }
                wait_ended(p)
                first = p.evaluate("window.__stopSampling()")
                r["first_tap_vowels"] = vowel_check(first)
                r["plays"] = p.evaluate("window.__plays")
                r["voiceLog"] = p.evaluate("window.__voiceLog")
                p.wait_for_timeout(2200)  # the shot eases back out
                after = p.evaluate("window.__face()")
                r["after_ease_out"] = {"amount": after["metrics"]["amount"]}

                # ---- every clip, from the Speak tab ----
                if not wide:
                    p.click("[data-panel-toggle]")
                    p.wait_for_timeout(500)
                for clip in MANIFEST:
                    cr = {"id": clip["id"], "lang": clip["lang"]}
                    p.evaluate("window.__startSampling()")
                    n0 = len(p.evaluate("window.__voiceLog || []"))
                    p.click(f"[data-speak={clip['id']}]")
                    p.wait_for_timeout(2400)
                    f = p.evaluate("window.__face()")
                    cr["exactPx"] = f["exact"]["px"]
                    cr["exactOfViewport"] = f["exactOfViewport"]
                    wait_ended(p)
                    s = p.evaluate("window.__stopSampling()")
                    log = p.evaluate("window.__voiceLog")
                    entry = log[-1] if log else {}
                    cr["playMs"] = entry.get("playMs")
                    cr["ok"] = entry.get("ok")
                    cr["ctx"] = entry.get("ctx")
                    cr["prefetched"] = entry.get("prefetched")
                    cr["closures"] = closure_check(clip, s)
                    cr["vowels"] = vowel_check(s)
                    r["clips"].append(cr)
                    p.wait_for_timeout(400)

                # ---- mute: the lips keep moving, the gain goes to 0 ----
                p.click("[data-toggle=speaker]")
                p.wait_for_timeout(300)
                st = p.evaluate("window.__voiceState && window.__voiceState()")
                p.evaluate("window.__startSampling()")
                p.click(f"[data-speak={MANIFEST[0]['id']}]")
                p.wait_for_timeout(1500)
                st2 = p.evaluate("window.__voiceState()")
                wait_ended(p)
                s = p.evaluate("window.__stopSampling()")
                r["mute"] = {"before": st, "during": st2, "pressed": p.get_attribute("[data-toggle=speaker]", "aria-pressed"), "vowels": vowel_check(s)}
                p.click("[data-toggle=speaker]")
                p.wait_for_timeout(300)
                r["mute"]["after_unmute"] = p.evaluate("window.__voiceState()")
                r["tapOrder"] = p.evaluate("window.__plays")
                r["blockedBannerShown"] = p.locator("[data-sound-blocked]").count()
                ctx.close()
        finally:
            browser.close()
    with open(os.path.join(OUT, f"results-{MODE}.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, indent=1, ensure_ascii=False)
    return results


if __name__ == "__main__":
    res = run()
    for k, r in res["sizes"].items():
        print("==", k, "errors", len(r["errors"]))
        print(" idle face of viewport", round(r["idle"]["faceOfViewport"], 3))
        sp = r["speaking"]
        print(" speaking face px", round(sp["exactPx"]), "of viewport", round(sp["exactOfViewport"], 3), "projected", round(sp["projectedOfViewport"], 3), "boost", round(sp["boost"], 3))
        print(" plays inTap", [x["inTap"] for x in r["tapOrder"]])
        for c in r["clips"]:
            cl = [x["pp"] for x in c["closures"]]
            print("  ", c["id"], "playMs", None if c["playMs"] is None else round(c["playMs"], 1), "face", round(c["exactOfViewport"], 3), "PP@bilabials", cl, "aa", c["vowels"]["aa_max"], "jaw", c["vowels"]["jaw_max"])
        print(" mute", r["mute"]["during"], "pressed", r["mute"]["pressed"], "lips jaw", r["mute"]["vowels"]["jaw_max"])
        if r["errors"]:
            print(" ERRORS", r["errors"][:5])
