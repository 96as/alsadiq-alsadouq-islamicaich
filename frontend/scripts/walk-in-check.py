"""Walk-in check in Edge: studio walk transitions on the dist. usage: python walk_in.py URL OUT_DIR"""
import json
import sys
from playwright.sync_api import sync_playwright

URL = sys.argv[1].rstrip("/")
OUT = sys.argv[2]
errs = []
with sync_playwright() as pw:
    b = pw.chromium.launch(channel="msedge", headless=True, args=["--mute-audio", "--use-angle=d3d11", "--ignore-gpu-blocklist"])
    ctx = b.new_context(viewport={"width": 1440, "height": 900})
    p = ctx.new_page()
    p.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
    p.on("pageerror", lambda e: errs.append("pageerror " + str(e)))
    p.on("response", lambda r: errs.append("HTTP %d %s" % (r.status, r.url)) if r.status >= 400 else None)
    p.add_init_script("window.__t0 = performance.now();")
    p.goto(URL + "/dev/forest")
    p.wait_for_function("() => window.__control && window.__control.current && window.__control.current.info", timeout=60000)
    p.evaluate("""() => {
      window.__log = [];
      let last = '';
      const t0 = performance.now();
      setInterval(() => {
        const i = window.__control.current.info;
        const key = [i.base, i.transition || '', i.walkState, i.studio].join('|');
        if (key !== last) { last = key; window.__log.push({ t: Math.round(performance.now() - t0), base: i.base, transition: i.transition || '', walkState: i.walkState, studio: i.studio }); }
      }, 30);
    }""")
    shots = 0
    for k in range(16):
        p.wait_for_timeout(1000)
        if k in (1, 3, 5, 7, 9, 12):
            p.screenshot(path=f"{OUT}/walk-{k:02d}.png")
    log = p.evaluate("window.__log")
    print(json.dumps(log, indent=1))
    print("errors", errs)
    b.close()
json.dump({"log": log, "errors": errs}, open(OUT + "/walk-log.json", "w"), indent=1)
