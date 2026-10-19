"""Headless Edge check: the demo landing shows the painted meadow by default and the forest only
with ?forest=1 (isForestEnabled). Usage: python scripts/landing-scene-check.py http://localhost:5414
Starts nothing: point it at a dev server built with VITE_DEMO_MODE=1."""
import sys
from playwright.sync_api import sync_playwright

base = sys.argv[1] if len(sys.argv) > 1 else 'http://localhost:5414'


def scene(page, url):
    page.goto(url, wait_until='domcontentloaded')
    page.wait_for_selector('[data-demo-scene]', timeout=20000)
    page.wait_for_timeout(2500)
    return page.get_attribute('[data-demo-scene]', 'data-demo-scene')


ok = True
with sync_playwright() as p:
    browser = p.chromium.launch(channel='msedge', headless=True, args=['--use-gl=swiftshader', '--enable-unsafe-swiftshader'])
    for url, want in ((base + '/', 'meadow'), (base + '/?forest=1', 'forest'), (base + '/?forest=0', 'meadow')):
        ctx = browser.new_context(viewport={'width': 1280, 'height': 800})
        page = ctx.new_page()
        got = scene(page, url)
        print(url, '->', got, 'PASS' if got == want else 'FAIL (wanted %s)' % want)
        ok = ok and got == want
        ctx.close()
    browser.close()
sys.exit(0 if ok else 1)
