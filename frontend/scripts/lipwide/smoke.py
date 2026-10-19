"""One-item smoke test of the lab page: prints clips, morph names, a few recorded rows."""
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).parent
URL = 'http://127.0.0.1:5386/avatar-component-preview.html?framing=meadow&state=idle&bars=0&sim=0'
item = sys.argv[1] if len(sys.argv) > 1 else 'wa28.plain'

with sync_playwright() as pw:
    b = pw.chromium.launch(channel='msedge', headless=True, args=['--autoplay-policy=no-user-gesture-required', '--disable-background-timer-throttling', '--disable-renderer-backgrounding'])
    ctx = b.new_context(viewport={'width': 1440, 'height': 900})
    ctx.add_init_script(path=str(HERE / 'helpers.js'))
    page = ctx.new_page()
    errs = []
    page.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
    page.on('pageerror', lambda e: errs.append(str(e)))
    page.goto(URL)
    page.wait_for_function('() => window.__voice && window.__control && window.__control.current', timeout=60000)
    page.wait_for_timeout(2500)
    clips = page.evaluate('() => window.__voice.clips.map(c => c.name)')
    print(len(clips), [c for c in clips if c.startswith(('wa', 'we'))][:6])
    print(json.dumps(page.evaluate('() => window.__rec.names()'))[:900])
    print(page.evaluate('() => Object.keys(window.__control.current)'))
    print(page.evaluate('() => Object.keys(window.__voice)'))
    clip = next(c for c in page.evaluate('() => window.__voice.clips') if c['name'] == item)
    page.evaluate('() => window.__rec.start()')
    page.evaluate('(c) => window.__voice.speak(c)', clip)
    page.wait_for_timeout(500)
    for _ in range(200):
        if not page.evaluate('() => Boolean(window.__voice.playing)'):
            break
        page.wait_for_timeout(100)
    page.wait_for_timeout(700)
    r = page.evaluate('() => window.__rec.stop()')
    rows = r['rows']
    print('rows', len(rows), 'dur', r['duration'], 'nonFinite', r['nonFinite'])
    for row in rows[40:44]:
        print(json.dumps(row)[:400])
    ts = [x['t'] for x in rows]
    import numpy as np
    d = np.diff(ts)
    print('dt median', np.median(d), 'p95', np.percentile(d, 95), 'max', d.max())
    print('errors', errs)
    page.screenshot(path=str(HERE / 'smoke.png'))
    ctx.close()
    b.close()
