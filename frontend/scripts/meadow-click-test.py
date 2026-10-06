"""Click-test of the meadow child page in Edge (headless, muted): Home, the one camera ease, the call controls, Voice | Chat.

usage: python scripts/meadow-click-test.py URL OUT_DIR W H [lang]

Needs `vite` running at URL (dev, so window.__stage exists). The API is mocked at localhost:8000 and the LiveKit hook is
replaced by scripts/fixtures/useLiveKitRoom.stub.js (no audio, no network). Never clicks mailto: or tel: links.
"""
import base64
import json
import sys
import time
from playwright.sync_api import sync_playwright

URL, OUT, W, H = sys.argv[1].rstrip("/"), sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
LANG = sys.argv[5] if len(sys.argv) > 5 else "ar"
tag = f"{W}x{H}-{LANG}"
# avatar-integ: the bottom nav label is localized (Main / the Arabic label) and the way back to voice is the Voice|Chat pill
NAV = "nav[aria-label=Main]" if LANG == "en" else "nav[aria-label='التنقل الرئيسي']"


def b64(o):
    return base64.urlsafe_b64encode(json.dumps(o).encode()).decode().rstrip("=")


tok = b64({"alg": "none", "typ": "JWT"}) + "." + b64({"user_id": 7, "username": "layla", "is_parent": False, "is_child": True, "exp": int(time.time()) + 86400}) + "."
CORS = {"access-control-allow-origin": "*", "access-control-allow-headers": "*", "access-control-allow-methods": "*"}
errs, checks = [], []


def check(name, ok, info=""):
    checks.append((name, bool(ok), info))
    print(("PASS " if ok else "FAIL ") + name + (" :: " + str(info) if info else ""))


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
    elif "/conversation/sessions/" in u and request.method == "POST" and u.rstrip("/").endswith("/sessions"):
        body = {"session_id": 11, "voice_mode": "eleven", "livekit_token": "x", "livekit_url": "ws://localhost:1", "max_seconds": 600}
    return route.fulfill(status=200, headers={**CORS, "content-type": "application/json"}, body=json.dumps(body))


STATE = "() => { const s = window.__stage; return s ? { m: s.m, t: s.t, pz: s.pz, px: s.px, mode: s.mode, hidden: s.hidden, phase: s.phase, face: s.facing, armed: s.walk.armed } : null }"

with sync_playwright() as pw:
    b = pw.chromium.launch(channel="msedge", headless=True, args=["--mute-audio", "--use-angle=d3d11", "--ignore-gpu-blocklist"])
    ctx = b.new_context(viewport={"width": W, "height": H})
    ctx.add_init_script("localStorage.setItem('access_token', %s); localStorage.setItem('refresh_token', %s); localStorage.setItem('demo_lang', %s);" % (json.dumps(tok), json.dumps(tok), json.dumps(LANG)))
    ctx.route("http://localhost:8000/**", api)
    # vite serves (and transforms) the stub from the project root; hand that to the page in place of the real hook
    stub = ctx.request.get(URL + "/scripts/fixtures/useLiveKitRoom.stub.js").text()
    ctx.route("**/src/hooks/useLiveKitRoom.js*", lambda r: r.fulfill(status=200, headers={"content-type": "text/javascript"}, body=stub))
    p = ctx.new_page()
    p.on("console", lambda m: errs.append(m.text[:300]) if m.type == "error" else None)
    p.on("pageerror", lambda e: errs.append("pageerror " + str(e)[:300]))
    p.goto(URL + "/child", wait_until="domcontentloaded")
    try:
        p.wait_for_selector(".mh-cta", timeout=30000)
    except Exception:
        print("home never showed the CTA; console errors:", errs[:6])
        print(p.inner_text("body")[:400])
        raise
    check("home shows the CTA, the level card and the quest card", p.locator(".mh-level").count() == 1 and p.locator(".mh-quest").count() == 1)
    check("nav floats over the meadow on home", p.locator(NAV).count() == 1)

    p.wait_for_function("() => window.__stage && window.__stage.mode !== 'arrive'", timeout=30000)
    p.wait_for_timeout(500)
    s0 = p.evaluate(STATE)
    check("he arrives at his rest spot (z = 0) and idles", abs(s0["pz"]) < 1e-3, s0)
    p.screenshot(path=f"{OUT}/ct-home-{tag}.png")
    check("a tap on Sadiq is the same as the green key (it has a target)", p.locator(".mh-tap").count() == 1)

    # start the call and sample the camera mix every 80 ms
    p.evaluate("() => { window.__ms = []; window.__iv = setInterval(() => { const s = window.__stage; window.__ms.push([performance.now(), s.m, s.pz, s.px]); }, 80); }")
    p.locator(".mh-cta").first.click()
    p.wait_for_selector(".mc-controls", timeout=30000)
    p.screenshot(path=f"{OUT}/ct-call-{tag}-a.png")
    p.wait_for_timeout(6000)
    ms = p.evaluate("() => { clearInterval(window.__iv); return window.__ms; }")
    mm = [r[1] for r in ms]
    mono = all(mm[i + 1] >= mm[i] - 1e-9 for i in range(len(mm) - 1))
    check("the mix only ever rises while the call starts (one ease, no wobble)", mono)
    check("the mix reaches 1", mm[-1] == 1, mm[-1])
    first1 = next(i for i, v in enumerate(mm) if v >= 1)
    after = ms[first1:]
    steady = max(abs(r[2] - after[0][2]) for r in after) < 0.5 and all(r[1] == 1 for r in after)
    check("the framing is steady for the rest of the call (m stays 1)", steady)
    check("the call has the level bar, the mic, end and speaker keys and the Voice|Chat pill",
          p.locator(".mc-level").count() == 1 and p.locator(".mc-btn").count() == 3 and p.locator(".mc-end").count() == 1 and p.locator(".mc-seg button").count() == 2,
          [p.locator(".mc-btn").count(), p.locator(".mc-seg button").count()])
    check("the bottom nav is hidden during the call", p.locator(NAV).count() == 0)
    p.screenshot(path=f"{OUT}/ct-call-{tag}-b.png")

    mic = p.locator(".mc-btn").nth(0)
    mic.click()
    p.wait_for_timeout(250)
    check("the mic key toggles muted", mic.get_attribute("data-muted") == "true", mic.get_attribute("data-muted"))
    mic.click()
    p.wait_for_timeout(250)
    check("the mic key toggles back", mic.get_attribute("data-muted") == "false")
    spk = p.locator(".mc-btn").nth(2)
    spk.click()
    p.wait_for_timeout(250)
    check("the speaker key toggles muted", spk.get_attribute("data-muted") == "true")
    spk.click()
    p.wait_for_timeout(250)
    p.screenshot(path=f"{OUT}/ct-call-{tag}-speaking.png")

    # Voice | Chat
    chat_btn = p.locator(".mc-seg button").nth(1)
    chat_btn.click()
    p.wait_for_timeout(900)
    st = p.evaluate(STATE)
    check("chat hides the avatar and keeps the meadow", st["hidden"] is True and p.locator("[data-meadow-stage]").count() == 1, st)
    p.screenshot(path=f"{OUT}/ct-chat-{tag}.png")
    p.wait_for_timeout(300)
    # back to voice (the chat screen keeps its own toggle)
    back = p.locator(".mc-seg button").nth(0)
    if back.count():
        back.first.click()
        p.wait_for_timeout(900)
        st = p.evaluate(STATE)
        check("voice brings the avatar back at the same framing", st["hidden"] is False and st["m"] == 1, st)
        p.screenshot(path=f"{OUT}/ct-voice-again-{tag}.png")
    else:
        check("a way back to voice exists in chat", False)

    # end the call
    if p.locator(".mc-end").count():
        p.locator(".mc-end").first.click()
        p.wait_for_timeout(1200)
        p.screenshot(path=f"{OUT}/ct-end-{tag}.png")
    print("errors", json.dumps(errs[:10], indent=1))
    b.close()

fails = [c for c in checks if not c[1]]
print(f"{len(checks) - len(fails)}/{len(checks)} checks passed")
sys.exit(1 if fails else 0)
