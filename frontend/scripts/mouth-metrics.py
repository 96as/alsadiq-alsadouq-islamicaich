"""Browser measurement of the WP4 mouth acting (M1, M2, M4, M8, B4, F2) in Edge.

Plays clips through the dev preview (frontend/dev-audio, gitignored), samples the chin vertex of the
real mesh per frame (window.__mouthMetrics) and writes the numbers as JSON.

  PYTHONUTF8=1 python scripts/mouth-metrics.py --url http://127.0.0.1:5341 --out metrics.json \
      [--clips ar22,ar24,ar26] [--audition abdullah_eleven_multilingual_v2_line01,...] [--throttle 6]

Clips named arNN come from dev-audio/eval-ar/arNN.diac.wav; audition names are the mp3 stems.
Never clicks mailto: or tel: links (there are none on this page).
"""
import argparse
import json
import sys
import time

from playwright.sync_api import sync_playwright

ap = argparse.ArgumentParser()
ap.add_argument('--url', default='http://127.0.0.1:5341')
ap.add_argument('--out', default='metrics.json')
ap.add_argument('--clips', default='ar22,ar24,ar26')
ap.add_argument('--audition', default='')
ap.add_argument('--throttle', type=float, default=1)
ap.add_argument('--width', type=int, default=1000)
ap.add_argument('--height', type=int, default=640)
ap.add_argument('--keep-rows', action='store_true')
args = ap.parse_args()

PAGE = args.url.rstrip('/') + '/avatar-component-preview.html?state=idle'


def run_clip(page, clip):
    page.evaluate('async (c) => { await window.__mouthMetrics.start(); }', clip)
    page.evaluate('(c) => window.__voice.speak(c)', clip)
    t0 = time.time()
    # wait until it has started, then until it ends
    while time.time() - t0 < 4 and not page.evaluate('() => Boolean(window.__voice.playing)'):
        page.wait_for_timeout(50)
    while time.time() - t0 < 60 and page.evaluate('() => Boolean(window.__voice.playing)'):
        page.wait_for_timeout(100)
    page.wait_for_timeout(400)
    rep = page.evaluate('async () => await window.__mouthMetrics.stop()')
    rep['clip'] = clip['name']
    return rep


def main():
    out = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel='msedge', headless=True, args=['--autoplay-policy=no-user-gesture-required', '--disable-background-timer-throttling', '--disable-renderer-backgrounding'])
        ctx = browser.new_context(viewport={'width': args.width, 'height': args.height})
        page = ctx.new_page()
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.goto(PAGE)
        page.wait_for_function('() => window.__control && window.__control.current && window.__control.current.acting', timeout=60000)
        page.wait_for_timeout(1500)
        if args.throttle > 1:
            cdp = ctx.new_cdp_session(page)
            cdp.send('Emulation.setCPUThrottlingRate', {'rate': args.throttle})
        clips = []
        for c in [x for x in args.clips.split(',') if x]:
            clips.append({'name': c, 'url': f'/dev-audio/eval-ar/{c}.diac.wav', 'kind': 'ar/eval', 'text': ''})
        if args.audition:
            avail = {c['name']: c for c in page.evaluate('() => window.__voice.clips')}
            for n in [x for x in args.audition.split(',') if x]:
                if n in avail:
                    clips.append(avail[n])
                else:
                    print('missing audition clip', n, file=sys.stderr)
        for clip in clips:
            rep = run_clip(page, clip)
            if not args.keep_rows:
                rep.pop('rows', None)
            out.append(rep)
            print(json.dumps({k: rep[k] for k in rep if k not in ('events', 'rows')}), flush=True)
        if errors:
            print('PAGE ERRORS', errors[:3], file=sys.stderr)
        browser.close()
    with open(args.out, 'w', encoding='utf8') as f:
        json.dump(out, f)


main()
