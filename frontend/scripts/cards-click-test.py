"""Click-test of the cards-spec (05) work in Edge (headless, muted): source cards, the AI chip and sheet, registration,
the Terms modal, the login/landing/settings links and the public /privacy page.

usage: python scripts/cards-click-test.py URL OUT_DIR W H [lang]

Needs `vite` running at URL (dev, so window.__mockReference exists) with VITE_QURAN_AUDIO_BASE=https://audio.test/quran.
The API is mocked at localhost:8000. The LiveKit hook is replaced by a generated copy of scripts/fixtures/useLiveKitRoom.stub.js
that also registers `reference` handlers and exposes window.__lkDeliver(bytes): the bytes go through the REAL parseData()
copied out of src/hooks/useLiveKitRoom.js, then through normalizeReference, exactly like a LiveKit data packet.
Placeholders only (no Quran or hadith text). Never clicks mailto: or tel: links.
"""
import base64
import json
import os
import re
import sys
import time

from playwright.sync_api import sync_playwright

URL, OUT, W, H = sys.argv[1].rstrip("/"), sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
LANG = sys.argv[5] if len(sys.argv) > 5 else "en"
tag = f"{W}x{H}-{LANG}"
HERE = os.path.dirname(os.path.abspath(__file__))
os.makedirs(OUT, exist_ok=True)

# ---- the generated stub: the repo's stub + reference handlers + the real parseData ----
hook_src = open(os.path.join(HERE, "..", "src", "hooks", "useLiveKitRoom.js"), encoding="utf-8").read()
m = re.search(r"function parseData\(payload\) \{.*?\n\}\n", hook_src, re.S)
assert m, "parseData not found in the real hook"
stub_src = open(os.path.join(HERE, "fixtures", "useLiveKitRoom.stub.js"), encoding="utf-8").read()
old = "const onReference = useCallback(() => {}, []);"
assert old in stub_src
new = """const refHandlers = useRef(new Set());
  useEffect(() => {
    window.__lkDeliver = (arr) => { const data = parseData(new Uint8Array(arr)); refHandlers.current.forEach((h) => h(data)); };
    return () => { delete window.__lkDeliver; };
  }, []);
  const onReference = useCallback((h) => { refHandlers.current.add(h); return () => refHandlers.current.delete(h); }, []);"""
gen_name = "_cards-stub.generated.js"
gen_path = os.path.join(HERE, "fixtures", gen_name)
open(gen_path, "w", encoding="utf-8").write(m.group(0) + "\n" + stub_src.replace(old, new))


def b64(o):
    return base64.urlsafe_b64encode(json.dumps(o).encode()).decode().rstrip("=")


def token(child):
    return b64({"alg": "none", "typ": "JWT"}) + "." + b64({"user_id": 7, "username": "layla", "is_parent": not child, "is_child": child, "exp": int(time.time()) + 86400}) + "."


CORS = {"access-control-allow-origin": "*", "access-control-allow-headers": "*", "access-control-allow-methods": "*"}
errs, checks = [], []


def check(name, ok, info=""):
    checks.append((name, bool(ok), info))
    print(("PASS " if ok else "FAIL ") + name + (" :: " + str(info)[:200] if info else ""))


def make_api(child):
    def api(route, request):
        if request.method == "OPTIONS":
            return route.fulfill(status=204, headers=CORS)
        u = request.url
        body = {}
        if "/api/auth/profile" in u:
            body = {
                "email": "k@example.test", "first_name": "Layla", "last_name": "", "username": "layla", "is_child": child,
                "profile": {"nickname": "Layla", "language": LANG, "language_preference": LANG},
                "children": [] if child else [{"id": 1, "nickname": "Sam", "username": "sam1"}],
            }
        elif "/gamification/level" in u:
            body = {"level_name": "Explorer", "level_number": 2, "total_points": 140, "current_level_min": 100, "next_level_min": 200, "current_streak": 3, "progress_pct": 40}
        elif "/gamification/quests" in u:
            body = []
        elif "/conversation/sessions/" in u and request.method == "POST" and u.rstrip("/").endswith("/sessions"):
            body = {"session_id": 11, "voice_mode": "eleven", "livekit_token": "x", "livekit_url": "ws://localhost:1", "max_seconds": 600}
        return route.fulfill(status=200, headers={**CORS, "content-type": "application/json"}, body=json.dumps(body))
    return api


# a few bytes of valid WAV so the audio element has something to fetch; the clip is never played for real
WAV = bytes.fromhex("52494646240000005741564566666d7410000000010001004400000088580100020010006461746100000000")

OVERLAP = """() => {
  const chip = document.querySelector('[data-testid=ai-chip]');
  if (!chip) return ['no chip'];
  const c = chip.getBoundingClientRect();
  const hits = [];
  for (const el of document.querySelectorAll('button, a, input, [role=button], select')) {
    if (el === chip || chip.contains(el) || el.closest('[data-testid=ai-info-sheet]')) continue;
    const s = getComputedStyle(el);
    if (s.visibility === 'hidden' || s.display === 'none' || Number(s.opacity) === 0) continue;
    const r = el.getBoundingClientRect();
    if (!r.width || !r.height) continue;
    const w = Math.min(c.right, r.right) - Math.max(c.left, r.left);
    const h = Math.min(c.bottom, r.bottom) - Math.max(c.top, r.top);
    if (w > 2 && h > 2) hits.push((el.className || el.tagName).toString().slice(0, 60) + ' ' + Math.round(w) + 'x' + Math.round(h));
  }
  return hits;
}"""


def deliver(p, obj):
    p.evaluate("(arr) => window.__lkDeliver(arr)", list(json.dumps(obj).encode("utf-8")))
    p.wait_for_timeout(150)


def card_count(p):
    return p.locator("[data-testid=source-header]").count()


def run():
    with sync_playwright() as pw:
        b = pw.chromium.launch(channel="msedge", headless=True, args=["--mute-audio", "--use-angle=d3d11", "--ignore-gpu-blocklist"])

        # ================= context 1: the child, signed in =================
        ctx = b.new_context(viewport={"width": W, "height": H})
        ctx.add_init_script("localStorage.setItem('access_token', %s); localStorage.setItem('refresh_token', %s); localStorage.setItem('demo_lang', %s);" % (json.dumps(token(True)), json.dumps(token(True)), json.dumps(LANG)))
        ctx.route("http://localhost:8000/**", make_api(True))
        ctx.route("https://audio.test/**", lambda r: r.fulfill(status=200, headers={"content-type": "audio/wav", **CORS}, body=WAV))
        stub = ctx.request.get(URL + "/scripts/fixtures/" + gen_name).text()
        ctx.route("**/src/hooks/useLiveKitRoom.js*", lambda r: r.fulfill(status=200, headers={"content-type": "text/javascript"}, body=stub))
        p = ctx.new_page()
        p.on("console", lambda msg: errs.append(msg.text[:300]) if msg.type == "error" else None)
        p.on("pageerror", lambda e: errs.append("pageerror " + str(e)[:300]))
        p.goto(URL + "/child", wait_until="domcontentloaded")
        p.wait_for_selector(".mh-cta", timeout=30000)
        p.wait_for_timeout(600)

        # ---- the chip in every state
        chip = p.locator("[data-testid=ai-chip]")
        check("chip: visible on the idle home screen", chip.count() == 1 and chip.is_visible())
        check("chip: its text is AI and it names itself for screen readers", chip.inner_text().strip() == "AI" and "AI" in (chip.get_attribute("aria-label") or "") or LANG == "ar", chip.get_attribute("aria-label"))
        box = chip.bounding_box()
        check("chip: a touch target of at least 44px", box and box["width"] >= 44 and box["height"] >= 44, box)
        hits = p.evaluate(OVERLAP)
        check("chip: overlaps no other control on the home screen", hits == [], hits)
        p.screenshot(path=f"{OUT}/cards-home-{tag}.png")

        p.locator(".mh-cta").first.click()
        p.wait_for_timeout(250)
        check("chip: visible while connecting", p.locator("[data-testid=ai-chip]").count() == 1 and p.locator("[data-testid=ai-chip]").is_visible())
        p.wait_for_selector(".mc-controls", timeout=30000)
        p.wait_for_timeout(500)
        check("chip: visible when connected (voice mode)", p.locator("[data-testid=ai-chip]").is_visible())
        hits = p.evaluate(OVERLAP)
        check("chip: overlaps no control on the call screen", hits == [], hits)
        p.screenshot(path=f"{OUT}/cards-call-{tag}.png")

        # ---- the info sheet: open, read, toggle, privacy link, focus trap, Escape, focus back
        p.locator("[data-testid=ai-chip]").click()
        sheet = p.locator("[data-testid=ai-info-sheet]")
        sheet.wait_for(timeout=5000)
        txt = sheet.inner_text()
        if LANG == "en":
            check("sheet: the exact English title and four lines", all(s in txt for s in ["Sadiq is an AI", "I am Sadiq, an AI friend. I am not a real person.", "I can make mistakes. I am not a scholar and I do not give fatwas.", "The part called \"In simple words\" is my own explanation."]), txt[:120])
        else:
            check("sheet: the exact Arabic title and lines, right to left", "الصديق ذكاء اصطناعي" in txt and "أنا الصديق، ذكاء اصطناعي ولست إنسانًا" in txt and sheet.get_attribute("dir") == "rtl", txt[:80])
        # cards-spec (05) judge r2: the parent API's preview is empty since caa2d65, so line 5 is shown (check:cards guards it)
        check("sheet: line 5 (parent summaries) is shown", ("Your parents can see short summaries of our chats." in txt) if LANG == "en" else ("يرى والداك ملخصات قصيرة عن حديثنا." in txt), txt[-120:])
        link = sheet.locator("a").first
        href = link.get_attribute("href") or ""
        check("sheet: a privacy link in a new tab, no opener", "/privacy" in href and link.get_attribute("target") == "_blank" and "noopener" in (link.get_attribute("rel") or ""), href)
        check("sheet: focus moved inside the dialog", p.evaluate("() => !!document.activeElement.closest('[data-testid=ai-info-sheet]')"))
        inside = True
        for _ in range(10):
            p.keyboard.press("Tab")
            inside = inside and p.evaluate("() => !!document.activeElement.closest('[data-testid=ai-info-sheet]')")
        check("sheet: Tab never leaves the dialog (focus trap)", inside)
        p.screenshot(path=f"{OUT}/cards-sheet-{tag}.png")
        p.locator("[data-testid=ai-sheet-lang-toggle]").click()
        p.wait_for_timeout(150)
        other = "ar" if LANG == "en" else "en"
        check("sheet: the EN/AR toggle switches the language and direction", sheet.get_attribute("lang") == other and sheet.get_attribute("dir") == ("rtl" if other == "ar" else "ltr"), sheet.get_attribute("lang"))
        check("sheet: the privacy link follows the shown language", f"lang={other}" in (sheet.locator("a").first.get_attribute("href") or ""))
        p.screenshot(path=f"{OUT}/cards-sheet-toggled-{tag}.png")
        p.keyboard.press("Escape")
        p.wait_for_timeout(250)
        check("sheet: Escape closes it", p.locator("[data-testid=ai-info-sheet]").count() == 0)
        check("sheet: focus returns to the chip", p.evaluate("() => document.activeElement && document.activeElement.getAttribute('data-testid')") == "ai-chip")
        p.locator("[data-testid=ai-chip]").press("Enter")
        p.wait_for_timeout(200)
        check("sheet: Enter on the chip opens it again, language reset to the page language", p.locator("[data-testid=ai-info-sheet]").get_attribute("lang") == LANG)
        p.keyboard.press("Escape")
        p.wait_for_timeout(200)

        # ---- source cards through the real decoder (bytes -> parseData -> normalizeReference)
        def mock(kind):
            return p.evaluate("(k) => { window.__lkMock = true; return typeof window.__mockReference }", kind)
        check("dev mock hook present", mock("verse") == "function")

        def fire(kind):
            p.evaluate("(k) => window.__mockReference(k)", kind)
            p.wait_for_timeout(250)

        # verse with an explanation, delivered as bytes
        verse_payload = p.evaluate("""() => new Promise((resolve) => import('/src/features/child/sources/mockReference.js').then((m) => resolve(m.buildMockReference('verse-explained'))))""")
        deliver(p, verse_payload)
        check("verse: the card renders from raw bytes through the real decoder", p.locator("[data-testid=source-header]").count() >= 1)
        body = p.inner_text("body")
        header_expect = "From the Quran:" if LANG == "en" else "من القرآن الكريم:"
        check("verse: header text", header_expect in body, header_expect)
        qt = p.locator(".quran-text").first
        fs = p.evaluate("(el) => parseFloat(getComputedStyle(el).fontSize)", qt.element_handle())
        check("verse: Quran text is 28px or larger", fs >= 28, fs)
        cred = p.locator("[data-testid=recitation-credit]").first.inner_text()
        check("verse: the recitation credit is always shown", "Husary" in cred or "الحصري" in cred, cred)
        check("verse: surah line and the KFGQPC caption", p.locator("[data-testid=surah-line]").count() >= 1 and "KFGQPC" in p.locator("[data-testid=verse-caption]").first.inner_text())
        eh = p.locator("[data-testid=explanation-header]").first.inner_text()
        check("verse: the tier-2 header is the exact organiser-ruled line", eh.strip() in ("In simple words, for children (our explanation, not the source's words):", "بكلمات بسيطة للأطفال (شرحنا، وليس نص المصدر):"), eh)
        order = p.evaluate("() => { const a = document.querySelector('[data-testid=source-block]'); const b = document.querySelector('[data-testid=explanation-block]'); return !!(a && b && (a.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING)); }")
        check("verse: the explanation comes after the source block", order)
        fb = p.evaluate("() => document.querySelector('.quran-text').classList.contains('quran-fallback')")
        check("font: no KFGQPC file on the dev server, so the Amiri Quran fallback is on", fb is True)
        p.screenshot(path=f"{OUT}/cards-verse-{tag}.png")

        # the other kinds, one at a time
        n0 = card_count(p)
        fire("hadith-hadeeth")
        cite = p.locator("[data-testid=citation-line]").first.inner_text()
        check("hadith: citation line names book, number, sahih, grader and source", ("graded sahih" in cite and "source:" in cite) or ("الحكم: صحيح" in cite and "المصدر" in cite), cite)
        check("hadith: only sahih is ever shown", "hasan" not in p.inner_text("body").lower())
        tl = p.locator("a[data-testid=translation-line]")
        check("hadith: a HadeethEnc link only to the approved host", tl.count() >= 1 and (tl.first.get_attribute("href") or "").startswith("https://hadeethenc.com/"), tl.first.get_attribute("href") if tl.count() else None)
        check("hadith: the link opens in a new tab with noopener", tl.count() >= 1 and tl.first.get_attribute("target") == "_blank" and "noopener" in (tl.first.get_attribute("rel") or ""))
        p.screenshot(path=f"{OUT}/cards-hadith-{tag}.png")
        fire("hadith")
        check("hadith: a placeholder example.com translation link is not a link", p.locator("a[data-testid=translation-line][href*='example.com']").count() == 0)
        for kind, tid in [("tafsir", None), ("tafsir-book", None), ("faq", None), ("term", None), ("aqidah", None), ("fiqh", "fiqh-note"), ("sirah", None), ("level-c", "disagreement-note")]:
            fire(kind)
            check(f"{kind}: renders with a header" + (f" and its {tid}" if tid else ""), p.locator("[data-testid=source-header]").count() >= 1 and (tid is None or p.locator(f"[data-testid={tid}]").count() >= 1))
            if kind in ("tafsir", "level-c"):
                p.screenshot(path=f"{OUT}/cards-{kind}-{tag}.png")
        check("at most 3 cards at a time", card_count(p) <= 3, card_count(p))
        fire("faq-marker")
        bt = p.inner_text("body")
        check("marker: the raw {{verse:..}} marker never appears", "{{" not in bt and "}}" not in bt)
        check("marker: a reference chip is shown instead", p.locator("[data-testid=verse-marker]").count() >= 1, p.locator("[data-testid=verse-marker]").first.inner_text() if p.locator("[data-testid=verse-marker]").count() else "")
        p.screenshot(path=f"{OUT}/cards-marker-{tag}.png")
        # hk/01 form: the server already resolved the marker into `segments`; the same chip and no raw marker
        fire("faq-segments")
        bt2 = p.inner_text("body")
        check("segments: no raw marker and a reference chip with its recitation button", "{{" not in bt2 and p.locator("[data-testid=verse-marker]").count() >= 1 and p.locator("[data-testid=verse-marker] button").count() >= 1, p.locator("[data-testid=verse-marker]").count())
        check("segments: the Arabic text around the chip is kept", "[بداية الجواب]" in bt2 and "[تتمة الجواب]" in bt2)
        p.screenshot(path=f"{OUT}/cards-segments-{tag}.png")
        before = card_count(p)
        for kind in ("bad-grade", "bad-host", "bad-marker", "bad-segment"):
            fire(kind)
        check("bad payloads (non-sahih grade, wrong host, broken marker) are dropped", card_count(p) == before, (before, card_count(p)))
        # garbage straight onto the wire
        p.evaluate("() => window.__lkDeliver(Array.from(new TextEncoder().encode('not json')))")
        p.evaluate("() => window.__lkDeliver(Array.from(new TextEncoder().encode('[1,2]')))")
        p.wait_for_timeout(150)
        check("garbage bytes are dropped without an error", card_count(p) == before)
        check("chip still visible with cards on screen", p.locator("[data-testid=ai-chip]").is_visible() and p.evaluate(OVERLAP) == [], p.evaluate(OVERLAP))

        # chat mode
        p.locator(".mc-seg button").nth(1).click()
        p.wait_for_timeout(900)
        check("chip: visible in chat mode", p.locator("[data-testid=ai-chip]").is_visible())
        hits = p.evaluate(OVERLAP)
        check("chip: overlaps no control in chat mode", hits == [], hits)
        p.screenshot(path=f"{OUT}/cards-chat-{tag}.png")
        back = p.get_by_role("button", name="Switch to voice" if LANG == "en" else "الانتقال إلى الصوت")
        if back.count():
            back.first.click()
            p.wait_for_timeout(700)
        if p.locator(".mc-end").count():
            p.locator(".mc-end").first.click()
            p.wait_for_timeout(1500)
        check("chip: still there after the call ends", p.locator("[data-testid=ai-chip]").count() == 1)
        p.screenshot(path=f"{OUT}/cards-ended-{tag}.png")

        # settings (child) privacy link
        p.goto(URL + "/child/settings", wait_until="domcontentloaded")
        p.wait_for_selector("[data-testid=settings-privacy-link]", timeout=20000)
        check("child settings: a privacy link", "/privacy" in (p.locator("[data-testid=settings-privacy-link]").get_attribute("href") or ""))
        p.locator("[data-testid=settings-privacy-link]").click()
        p.wait_for_selector("[data-testid=privacy-page]", timeout=10000)
        check("child settings: the link opens the privacy page", p.locator("h1").count() == 1)
        ctx.close()

        # ================= recitation marker audio + the font that loads =================
        ctx2 = b.new_context(viewport={"width": W, "height": H})
        ctx2.add_init_script("localStorage.setItem('access_token', %s); localStorage.setItem('refresh_token', %s); localStorage.setItem('demo_lang', %s);" % (json.dumps(token(True)), json.dumps(token(True)), json.dumps(LANG)))
        ctx2.route("http://localhost:8000/**", make_api(True))
        ctx2.route("https://audio.test/**", lambda r: r.fulfill(status=200, headers={"content-type": "audio/wav", **CORS}, body=WAV))
        # a stand-in file only to prove the loaded-font path (it is NOT the KFGQPC font, which the lead supplies)
        stand_in = "C:/Windows/Fonts/arial.ttf"
        if os.path.exists(stand_in):
            ctx2.route("**/fonts/KFGQPCHafs.ttf", lambda r: r.fulfill(status=200, headers={"content-type": "font/ttf"}, body=open(stand_in, "rb").read()))
        stub2 = ctx2.request.get(URL + "/scripts/fixtures/" + gen_name).text()
        ctx2.route("**/src/hooks/useLiveKitRoom.js*", lambda r: r.fulfill(status=200, headers={"content-type": "text/javascript"}, body=stub2))
        p2 = ctx2.new_page()
        p2.on("pageerror", lambda e: errs.append("pageerror " + str(e)[:300]))
        p2.goto(URL + "/child", wait_until="domcontentloaded")
        p2.wait_for_selector(".mh-cta", timeout=30000)
        p2.locator(".mh-cta").first.click()
        p2.wait_for_selector(".mc-controls", timeout=30000)
        p2.wait_for_timeout(400)
        p2.evaluate("() => window.__mockReference('verse')")
        p2.wait_for_timeout(1200)
        if os.path.exists(stand_in):
            fb2 = p2.evaluate("() => document.querySelector('.quran-text').classList.contains('quran-fallback')")
            check("font: when the TTF loads, the fallback class is off (loaded-path, stand-in file)", fb2 is False)
        p2.evaluate("() => window.__mockReference('faq-marker')")
        p2.wait_for_timeout(300)
        mk = p2.locator("[data-testid=verse-marker] button")
        if mk.count():
            src = p2.evaluate("() => document.querySelector('[data-testid=verse-marker] audio')?.getAttribute('src')")
            check("marker: the play button's audio is <base>/002255.mp3", (src or "").endswith("/002255.mp3"), src)
            # cards-spec (05) section 1.6, organiser ruling 2026-10-05: the credit is shown once per card, not once
            # per segment, so it is a sibling of the marker (inside source-block), not nested inside it.
            check("marker: its credit line is shown with it", p2.locator("[data-testid=source-block] [data-testid=recitation-credit]").count() >= 1)
        else:
            check("marker: a play button for the marker (needs VITE_QURAN_AUDIO_BASE=https://audio.test/quran)", False)
        ctx2.close()

        # ================= context 3: parent settings =================
        ctx3 = b.new_context(viewport={"width": W, "height": H})
        ctx3.add_init_script("localStorage.setItem('access_token', %s); localStorage.setItem('refresh_token', %s);" % (json.dumps(token(False)), json.dumps(token(False))))
        ctx3.route("http://localhost:8000/**", make_api(False))
        p3 = ctx3.new_page()
        p3.goto(URL + "/parent/settings", wait_until="domcontentloaded")
        try:
            p3.wait_for_selector("[data-testid=settings-privacy-link]", timeout=20000)
            check("parent settings: a privacy link", "/privacy" in (p3.locator("[data-testid=settings-privacy-link]").get_attribute("href") or ""))
            p3.screenshot(path=f"{OUT}/cards-parent-settings-{tag}.png")
        except Exception as e:  # noqa: BLE001
            check("parent settings: a privacy link", False, str(e)[:150])
        ctx3.close()

        # ================= context 4: logged out =================
        ctx4 = b.new_context(viewport={"width": W, "height": H})
        ctx4.route("http://localhost:8000/**", make_api(True))
        p4 = ctx4.new_page()
        p4.on("pageerror", lambda e: errs.append("pageerror " + str(e)[:300]))
        for plang in ("en", "ar"):
            p4.goto(f"{URL}/privacy?lang={plang}", wait_until="domcontentloaded")
            p4.wait_for_selector("[data-testid=privacy-page]", timeout=20000)
            check(f"privacy ({plang}): reachable logged out, stays on /privacy", "/privacy" in p4.url, p4.url)
            pb = p4.inner_text("[data-testid=privacy-page]")
            check(f"privacy ({plang}): no [bracket] placeholder left", "[" not in pb and "]" not in pb)
            check(f"privacy ({plang}): real tables with captions", p4.locator("table").count() >= 2 and p4.locator("table caption").count() == p4.locator("table").count(), p4.locator("table").count())
            check(f"privacy ({plang}): the draft banner is shown", p4.locator("[data-testid=privacy-draft-banner]").count() == 1)
            check(f"privacy ({plang}): direction", p4.locator("[data-testid=privacy-page]").get_attribute("dir") == ("rtl" if plang == "ar" else "ltr"))
            noscroll = p4.evaluate("() => document.documentElement.scrollWidth <= window.innerWidth + 1 && document.querySelector('[data-testid=privacy-page]').scrollWidth <= window.innerWidth + 1")
            check(f"privacy ({plang}): no sideways scroll at {W}px", noscroll)
            p4.screenshot(path=f"{OUT}/cards-privacy-{plang}-{tag}.png", full_page=True)
        p4.locator("[data-testid=privacy-lang-toggle]").click()
        p4.wait_for_timeout(150)
        check("privacy: the toggle switches the language", p4.locator("[data-testid=privacy-page]").get_attribute("lang") == "en")

        # login footer
        p4.goto(URL + "/login", wait_until="domcontentloaded")
        p4.wait_for_selector("[data-testid=login-privacy-link]", timeout=20000)
        p4.locator("[data-testid=login-privacy-link]").click()
        p4.wait_for_selector("[data-testid=privacy-page]", timeout=10000)
        check("login: the privacy link opens /privacy", "/privacy" in p4.url, p4.url)

        # registration steps 1 and 3 and the Terms modal
        p4.goto(URL + "/register", wait_until="domcontentloaded")
        p4.wait_for_selector("[data-testid=reg-ai-notice]", timeout=20000)
        n = p4.inner_text("[data-testid=reg-ai-notice]")
        check("register step 1: the AI notice (not a person, not a scholar, no fatwas)", "AI companion" in n and "not a scholar" in n and "fatwas" in n, n[:80])
        l1 = p4.locator("[data-testid=reg-privacy-link-1]")
        check("register step 1: the data link goes to /privacy in a new tab", "/privacy" in (l1.get_attribute("href") or "") and l1.get_attribute("target") == "_blank" and "noopener" in (l1.get_attribute("rel") or ""))
        p4.screenshot(path=f"{OUT}/cards-register1-{tag}.png")
        p4.fill("#reg-first-name", "Test")
        p4.fill("#reg-last-name", "Parent")
        p4.fill("#reg-username", "testparent1")
        p4.get_by_role("button", name=re.compile("next|continue", re.I)).first.click()
        p4.wait_for_timeout(300)
        # step 2: the contact fields
        email = p4.locator("input[type=email], input[name=email]").first
        if email.count():
            email.fill("parent@example.test")
        p4.get_by_role("button", name=re.compile("next|continue", re.I)).first.click()
        p4.wait_for_timeout(300)
        if p4.locator("[data-testid=reg-privacy-link-3]").count() == 0:
            p4.screenshot(path=f"{OUT}/cards-register-step2-stuck-{tag}.png")
        check("register step 3: a privacy policy link next to the Terms checkbox", p4.locator("[data-testid=reg-privacy-link-3]").count() == 1)
        if p4.locator("[data-testid=reg-privacy-link-3]").count():
            l3 = p4.locator("[data-testid=reg-privacy-link-3]")
            check("register step 3: it opens in a new tab with noopener", l3.get_attribute("target") == "_blank" and "noopener" in (l3.get_attribute("rel") or ""))
            p4.get_by_role("button", name="terms & conditions").click()
            p4.wait_for_selector("[data-testid=terms-clause-11]", timeout=5000)
            c11 = p4.inner_text("[data-testid=terms-clause-11]")
            check("terms: clause 11 (AI companion) is there", "AI Companion" in c11 and "not a source of fatwas" in c11, c11[:90])
            tl_ = p4.locator("[data-testid=terms-privacy-link]")
            check("terms: clause 3 links to the Privacy Policy", tl_.count() == 1 and "/privacy" in (tl_.get_attribute("href") or ""))
            p4.screenshot(path=f"{OUT}/cards-terms-{tag}.png")
            p4.keyboard.press("Escape")

        # landing footer
        # The landing page (DemoLanding) is only mounted in the showcase build (VITE_SHOWCASE=1): point LANDING_URL at a
        # showcase dev server, e.g. LANDING_URL=http://127.0.0.1:5422. Without it this check is skipped, not faked.
        landing = os.environ.get("LANDING_URL", "").rstrip("/")
        if not landing:
            print("SKIP landing: set LANDING_URL to a VITE_SHOWCASE=1 server to check the landing footer link")
        else:
            p4.goto(landing + "/landing", wait_until="domcontentloaded")
            try:
                p4.wait_for_selector("[data-testid=landing-privacy-link]", timeout=20000)
                check("landing: a privacy link in the footer", "/privacy" in (p4.locator("[data-testid=landing-privacy-link]").get_attribute("href") or ""))
                p4.locator("[data-testid=landing-privacy-link]").scroll_into_view_if_needed()
                p4.screenshot(path=f"{OUT}/cards-landing-footer-{tag}.png")
            except Exception as e:  # noqa: BLE001
                check("landing: a privacy link in the footer", False, str(e)[:150])
        ctx4.close()
        b.close()


try:
    run()
finally:
    try:
        os.remove(gen_path)
    except OSError:
        pass

print("console/page errors:", json.dumps([e for e in errs if "favicon" not in e][:10], indent=1))
fails = [c for c in checks if not c[1]]
print(f"{len(checks) - len(fails)}/{len(checks)} checks passed")
sys.exit(1 if fails else 0)
