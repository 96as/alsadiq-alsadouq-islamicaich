"""Product screenshots (Home and the call, 3 sizes, ar and en) and a 30 s recording of Home -> Talk -> steady call.

usage: python scripts/product-media.py URL OUT_DIR [shots|video|all]

Needs `vite` running at URL (dev). Same mocks as scripts/meadow-click-test.py: API at localhost:8000 and the
LiveKit hook stubbed (no audio, no network). Screenshots are headless and muted; the video is a headed Edge
window parked off-screen, muted. Never clicks mailto: or tel: links.
"""
import base64
import json
import os
import sys
import time
from playwright.sync_api import sync_playwright

URL, OUT = sys.argv[1].rstrip("/"), sys.argv[2]
WHAT = sys.argv[3] if len(sys.argv) > 3 else "all"
SIZES = [(390, 844), (1440, 900), (2000, 713)]
CORS = {"access-control-allow-origin": "*", "access-control-allow-headers": "*", "access-control-allow-methods": "*"}


def b64(o):
    return base64.urlsafe_b64encode(json.dumps(o).encode()).decode().rstrip("=")


TOK = b64({"alg": "none", "typ": "JWT"}) + "." + b64({"user_id": 7, "username": "layla", "is_parent": False, "is_child": True, "exp": int(time.time()) + 86400}) + "."


def make_api(lang):
    def api(route, request):
        if request.method == "OPTIONS":
            return route.fulfill(status=204, headers=CORS)
        u = request.url
        body = {}
        if "/api/auth/profile" in u:
            body = {"email": "k@example.test", "first_name": "Layla", "last_name": "", "profile": {"nickname": "Layla", "language": lang}, "children": []}
        elif "/gamification/level" in u:
            body = {"level_name": "Explorer", "level_number": 2, "total_points": 140, "current_level_min": 100, "next_level_min": 200, "current_streak": 3, "progress_pct": 40}
        elif "/gamification/quests" in u:
            body = []
        elif "/conversation/sessions/" in u and request.method == "POST" and u.rstrip("/").endswith("/sessions"):
            body = {"session_id": 11, "voice_mode": "eleven", "livekit_token": "x", "livekit_url": "ws://localhost:1", "max_seconds": 600}
        return route.fulfill(status=200, headers={**CORS, "content-type": "application/json"}, body=json.dumps(body))

    return api


def context(b, W, H, lang, **kw):
    ctx = b.new_context(viewport={"width": W, "height": H}, **kw)
    ctx.add_init_script("localStorage.setItem('access_token', %s); localStorage.setItem('refresh_token', %s); localStorage.setItem('demo_lang', %s);" % (json.dumps(TOK), json.dumps(TOK), json.dumps(lang)))
    ctx.route("http://localhost:8000/**", make_api(lang))
    stub = ctx.request.get(URL + "/scripts/fixtures/useLiveKitRoom.stub.js").text()
    ctx.route("**/src/hooks/useLiveKitRoom.js*", lambda r: r.fulfill(status=200, headers={"content-type": "text/javascript"}, body=stub))
    return ctx


def open_home(p):
    p.goto(URL + "/child", wait_until="domcontentloaded")
    p.wait_for_selector(".mh-cta", timeout=30000)
    p.wait_for_function("() => window.__stage && window.__stage.walk.armed", timeout=30000)


def shots(pw):
    os.makedirs(OUT, exist_ok=True)
    b = pw.chromium.launch(channel="msedge", headless=True, args=["--mute-audio", "--use-angle=d3d11", "--ignore-gpu-blocklist"])
    for W, H in SIZES:
        for lang in ("ar", "en"):
            ctx = context(b, W, H, lang)
            p = ctx.new_page()
            open_home(p)
            p.wait_for_function("() => window.__stage.mode === 'rest'", timeout=40000)
            p.wait_for_timeout(700)
            p.screenshot(path=f"{OUT}/home-{W}x{H}-{lang}.png")
            p.locator(".mh-cta").first.click()
            p.wait_for_selector(".mc-controls", timeout=30000)
            p.wait_for_function("() => window.__stage.m === 1", timeout=15000)
            p.wait_for_timeout(1500)
            p.screenshot(path=f"{OUT}/call-{W}x{H}-{lang}.png")
            print("shot", W, H, lang)
            ctx.close()
    b.close()


def video(pw):
    W, H = 1440, 900
    b = pw.chromium.launch(channel="msedge", headless=False, args=["--mute-audio", "--use-angle=d3d11", "--ignore-gpu-blocklist", "--window-position=-2600,0", f"--window-size={W + 40},{H + 140}"])
    vdir = os.path.join(OUT, "wip", "video")
    os.makedirs(vdir, exist_ok=True)
    ctx = context(b, W, H, "ar", record_video_dir=vdir, record_video_size={"width": W, "height": H})
    p = ctx.new_page()
    t0 = time.time()
    open_home(p)
    p.wait_for_function("() => window.__stage.mode === 'rest'", timeout=40000)
    # let him rest, then force one stroll up the path and back so the clip shows the walk, the turn and the return
    p.wait_for_timeout(1500)
    p.evaluate("() => { window.__stage.wait = 0.05; window.__stage.beats = 0 }")
    p.wait_for_function("() => window.__stage.mode === 'return'", timeout=30000)
    p.wait_for_function("() => window.__stage.mode === 'rest'", timeout=30000)
    p.wait_for_timeout(1200)
    p.locator(".mh-cta").first.click()
    p.wait_for_selector(".mc-controls", timeout=30000)
    p.wait_for_timeout(9000)  # the steady call; the last 30 s of the recording are kept (ffmpeg -sseof -30)
    path = p.video.path()
    ctx.close()
    b.close()
    os.replace(path, os.path.join(vdir, "product-home-to-call.webm"))
    print("video", os.path.join(vdir, "product-home-to-call.webm"), round(time.time() - t0, 1), "s")


with sync_playwright() as pw:
    if WHAT in ("shots", "all"):
        shots(pw)
    if WHAT in ("video", "all"):
        video(pw)
