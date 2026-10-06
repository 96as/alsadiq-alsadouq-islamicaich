"""Contact sheet of the Home walk in Edge (headless, muted): the arrival, the rest, one stroll away and back.

usage: python scripts/home-walk-sheet.py URL OUT.png W H [lang] [seconds]

Needs `vite` running at URL (dev: window.__stage). Same mocks as scripts/meadow-click-test.py.
"""
import base64
import json
import sys
import time
from PIL import Image
from playwright.sync_api import sync_playwright

URL, OUT, W, H = sys.argv[1].rstrip("/"), sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
LANG = sys.argv[5] if len(sys.argv) > 5 else "en"
SECS = float(sys.argv[6]) if len(sys.argv) > 6 else 24


def b64(o):
    return base64.urlsafe_b64encode(json.dumps(o).encode()).decode().rstrip("=")


tok = b64({"alg": "none", "typ": "JWT"}) + "." + b64({"user_id": 7, "username": "layla", "is_parent": False, "is_child": True, "exp": int(time.time()) + 86400}) + "."
CORS = {"access-control-allow-origin": "*", "access-control-allow-headers": "*", "access-control-allow-methods": "*"}


def api(route, request):
    if request.method == "OPTIONS":
        return route.fulfill(status=204, headers=CORS)
    u = request.url
    body = {}
    if "/api/auth/profile" in u:
        body = {"email": "k@example.test", "first_name": "Layla", "last_name": "", "profile": {"nickname": "Layla", "language": LANG}, "children": []}
    elif "/gamification/level" in u:
        body = {"level_name": "Explorer", "level_number": 2, "total_points": 140, "current_level_min": 100, "next_level_min": 200, "current_streak": 3, "progress_pct": 40}
    elif "/gamification/quests" in u:
        body = []
    return route.fulfill(status=200, headers={**CORS, "content-type": "application/json"}, body=json.dumps(body))


frames = []
with sync_playwright() as pw:
    b = pw.chromium.launch(channel="msedge", headless=True, args=["--mute-audio", "--use-angle=d3d11", "--ignore-gpu-blocklist"])
    ctx = b.new_context(viewport={"width": W, "height": H})
    ctx.add_init_script("localStorage.setItem('access_token', %s); localStorage.setItem('refresh_token', %s); localStorage.setItem('demo_lang', %s);" % (json.dumps(tok), json.dumps(tok), json.dumps(LANG)))
    ctx.route("http://localhost:8000/**", api)
    p = ctx.new_page()
    p.goto(URL + "/child", wait_until="domcontentloaded")
    p.wait_for_selector(".mh-cta", timeout=30000)
    p.wait_for_function("() => window.__stage && window.__stage.walk.armed", timeout=30000)
    t0 = time.time()
    log = []
    forced = False
    while time.time() - t0 < SECS:
        s = p.evaluate("() => { const s = window.__stage; return { mode: s.mode, pz: s.pz, st: s.walk.state, face: s.facing, wait: s.wait } }")
        if s["mode"] == "rest" and not forced:
            p.evaluate("() => { window.__stage.wait = 0.05 }")
            forced = True
        log.append(s)
        path = OUT + f".f{len(frames):02d}.png"
        p.screenshot(path=path)
        frames.append((path, s))
        p.wait_for_timeout(450)
    b.close()

# contact sheet
n = len(frames)
cols = 8 if W < 700 else 4
tw = 200 if W < 700 else 480
th = int(tw * H / W)
rows = (n + cols - 1) // cols
sheet = Image.new("RGB", (cols * tw, rows * th), "white")
for i, (path, s) in enumerate(frames):
    im = Image.open(path).convert("RGB").resize((tw, th))
    sheet.paste(im, ((i % cols) * tw, (i // cols) * th))
sheet.save(OUT)
import os
for path, _ in frames:
    os.remove(path)
print(json.dumps([(round(x["pz"], 2), x["mode"], x["st"], round(x["face"], 2)) for x in log]))
