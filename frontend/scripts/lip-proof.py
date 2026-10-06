"""Step 2 lip-sync proof in Edge on the dev preview (text-timed clips, like a live session).

usage: PYTHONUTF8=1 python lip_proof.py http://127.0.0.1:5385 out.json [variant,...] [clips,...]
variant = plain | diac. Clips default to ar01 ar05 ar21 ar22 ar24 ar26.
Runs headless msedge, muted. Records, every animation frame, the real mesh morphs (head and MouthBag),
the chin travel (mouthMetrics) and the shaper numbers, and flags glitches:
  nan        any NaN or infinite weight or chin
  oversum    a viseme weight sum above 1.05 while PP >= 0.5 (the lip-tear condition)
  ppjaw      PP >= 0.9 while the jaw is above the PP gate + 0.02 rad for more than 2 frames
  pop        a single-frame chin jump above POP_CM that is not part of a monotone ramp
  flutter    chin direction reversals above 0.15 cm more than FLUTTER_HZ per second
  stuck      the mouth open (chin > 1 cm) for more than 2 s with the audio silent
"""
import json
import sys
import time
from playwright.sync_api import sync_playwright

URL = sys.argv[1]
OUT = sys.argv[2]
VARIANTS = (sys.argv[3] if len(sys.argv) > 3 else "plain,diac").split(",")
CLIPS = (sys.argv[4] if len(sys.argv) > 4 else "ar01,ar05,ar21,ar22,ar24,ar26").split(",")
POP_CM = 1.2
FLUTTER_HZ = 9.0

SAMPLER = r"""
(() => {
  window.__rows = null;
  window.__startRows = () => {
    const c = window.__control.current;
    let root = c.bones.head; while (root.parent) root = root.parent;
    const meshes = [];
    root.traverse((o) => { if (o.morphTargetDictionary && o.morphTargetInfluences) meshes.push(o); });
    const VIS = ['PP','FF','DD','kk','CH','SS','nn','RR','aa','E','I','O','U'];
    const find = (m, v) => { const k = Object.keys(m.morphTargetDictionary).find((x) => x.toLowerCase() === v.toLowerCase() || x.toLowerCase().endsWith('_' + v.toLowerCase())); return k == null ? -1 : m.morphTargetDictionary[k]; };
    const bound = meshes.map((m) => ({ name: m.name, idx: VIS.map((v) => find(m, v)), m, ppJaw: find(m, 'PP_jaw') }));
    window.__rows = [];
    window.__meshNames = bound.map((b) => b.name + ':' + b.idx.filter((i) => i >= 0).length + (b.ppJaw >= 0 ? '+PP_jaw' : ''));
    const tick = () => {
      if (!window.__rows) return;
      const sh = c.acting.shaper;
      const row = { now: performance.now(), jaw: sh.jaw, ppJawMorph: sh.ppJawMorph, meshes: [] };
      for (const b of bound) row.meshes.push(b.idx.map((i) => (i >= 0 ? b.m.morphTargetInfluences[i] : null)));
      const a = window.__voice && window.__voice.audio;
      window.__rows.push(row);
      requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  };
  window.__stopRows = () => { const r = window.__rows; window.__rows = null; return r; };
})();
"""


def analyse(mm, rows):
    """mm = mouthMetrics report with rows (per frame), rows = the raw morph rows (same frame count approx)."""
    res = {"glitches": {}, "frames": len(mm["rows"])}
    g = res["glitches"]
    chin = [x["chin"] for x in mm["rows"] if x["speaking"] or x["active"]]
    allr = mm["rows"]
    sp = [x for x in allr if x["speaking"]]
    # NaN
    bad = 0
    for x in allr:
        for k in ("chin", "jaw", "pp", "ppOut", "aaWritten"):
            v = x[k]
            if v is None or v != v or abs(v) == float("inf"):
                bad += 1
    for r in rows:
        for mesh in r["meshes"]:
            for v in mesh:
                if v is not None and (v != v or abs(v) == float("inf")):
                    bad += 1
    g["nan"] = bad
    # oversum and PP tear condition on the written morphs of every mesh
    over = []
    for r in rows:
        for mi, mesh in enumerate(r["meshes"]):
            vals = [v for v in mesh if v is not None]
            if len(vals) < 5:
                continue
            ppv = mesh[0] or 0
            if ppv >= 0.5 and sum(vals) > 1.05:
                over.append((round(sum(vals), 2), mi))
    g["oversum"] = len(over)
    # PP vs jaw
    gate = 0.08 + 0.02
    ppj = 0
    run = 0
    for x in allr:
        if x["ppOut"] >= 0.9 and x["jaw"] > gate:
            run += 1
            if run == 3:
                ppj += 1
        else:
            run = 0
    g["ppjaw"] = ppj
    # pop: chin step per frame above POP_CM, with the previous and next steps not the same direction
    pops = 0
    steps = [allr[i + 1]["chin"] - allr[i]["chin"] for i in range(len(allr) - 1)]
    for i in range(1, len(steps) - 1):
        if abs(steps[i]) > POP_CM and steps[i] * steps[i - 1] <= 0 and steps[i] * steps[i + 1] <= 0:
            pops += 1
    g["pop"] = pops
    g["maxStepCm"] = round(max([abs(s) for s in steps] or [0]), 2)
    # flutter: reversals above 0.15 cm per second of speech
    rev = 0
    last_ext = allr[0]["chin"] if allr else 0
    direction = 0
    for x in allr:
        d = x["chin"] - last_ext
        if direction >= 0 and d < -0.15:
            rev += 1
            direction = -1
            last_ext = x["chin"]
        elif direction <= 0 and d > 0.15:
            rev += 1
            direction = 1
            last_ext = x["chin"]
        elif (direction >= 0 and x["chin"] > last_ext) or (direction <= 0 and x["chin"] < last_ext):
            last_ext = x["chin"]
    secs = max(0.1, allr[-1]["t"] - allr[0]["t"]) if allr else 1
    res["reversalsPerS"] = round(rev / secs, 2)
    g["flutter"] = 1 if rev / secs > FLUTTER_HZ else 0
    # stuck open: the mouth above 1 cm while not active (silent) for >2 s
    stuck = 0
    t_open = None
    for x in allr:
        if x["chin"] > 1.0 and not x["active"] and not x["speaking"]:
            t_open = x["t"] if t_open is None else t_open
            if x["t"] - t_open > 2:
                stuck = 1
        else:
            t_open = None
    g["stuck"] = stuck
    # peak weights written on head mesh
    res["maxAA"] = round(max([r["meshes"][0][8] or 0 for r in rows] or [0]), 3)
    res["maxPPhead"] = round(max([r["meshes"][0][0] or 0 for r in rows] or [0]), 3)
    res["maxSum"] = round(max([sum(v for v in r["meshes"][0] if v is not None) for r in rows] or [0]), 3)
    res["M1"] = mm["M1"]
    res["M2"] = mm["M2"]
    res["M4"] = mm["M4"]
    res["fps"] = mm["fps"]
    res["B4"] = mm["B4"]
    return res


def main():
    out = {"url": URL, "clips": [], "errors": []}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="msedge", headless=True, args=["--autoplay-policy=no-user-gesture-required", "--mute-audio", "--use-angle=d3d11", "--ignore-gpu-blocklist"])
        ctx = browser.new_context(viewport={"width": 1000, "height": 640})
        ctx.add_init_script(SAMPLER)
        page = ctx.new_page()
        page.on("console", lambda m: out["errors"].append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: out["errors"].append("pageerror: " + str(e)))
        page.goto(URL.rstrip("/") + "/avatar-component-preview.html?state=idle")
        page.wait_for_function("() => window.__control && window.__control.current && window.__control.current.acting", timeout=60000)
        page.wait_for_timeout(1500)
        avail = {c["name"]: c for c in page.evaluate("() => window.__voice.clips")}
        out["timelineOn"] = page.evaluate("() => window.__voice.timelineOn")
        for variant in VARIANTS:
            for cid in CLIPS:
                name = f"{cid}.{variant}"
                if name not in avail:
                    print("missing", name)
                    continue
                clip = avail[name]
                page.evaluate("async () => { await window.__mouthMetrics.start(); }")
                page.evaluate("() => window.__startRows()")
                page.evaluate("(c) => window.__voice.speak(c)", clip)
                t0 = time.time()
                while time.time() - t0 < 5 and not page.evaluate("() => Boolean(window.__voice.playing)"):
                    page.wait_for_timeout(50)
                while time.time() - t0 < 60 and page.evaluate("() => Boolean(window.__voice.playing)"):
                    page.wait_for_timeout(100)
                page.wait_for_timeout(1500)  # the mouth closes after the last word
                rows = page.evaluate("() => window.__stopRows()")
                mm = page.evaluate("async () => await window.__mouthMetrics.stop()")
                meshes = page.evaluate("() => window.__meshNames")
                a = analyse(mm, rows)
                a["clip"] = name
                a["meshes"] = meshes
                a["timeline"] = [x.get("syncPhase") for x in mm["rows"] if x["speaking"]][:1]
                out["clips"].append(a)
                print(json.dumps({k: a[k] for k in a if k != "meshes"}, ensure_ascii=False), flush=True)
        browser.close()
    json.dump(out, open(OUT, "w", encoding="utf-8"), indent=1)
    print("errors", len(out["errors"]), out["errors"][:3])


main()
