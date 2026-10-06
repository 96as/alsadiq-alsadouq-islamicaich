"""Runs every item of testset-wide.json through the lab page (the real engine, timeline and GLB) and records
every displayed frame. Usage (from frontend/):

  PYTHONUTF8=1 python scripts/lipwide/run.py --mode headless
  PYTHONUTF8=1 python scripts/lipwide/run.py --mode headed      # off-screen window, muted

Output: <OUT>/raw/<mode>/<id>.json  ({rows, nonFinite, duration, errors, clip}).
"""
import argparse
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).parent
FRONT = HERE.parent.parent
OUT = Path.home() / r'Documents\Alsadiq-3D\03-renders\studio\lipsync-test'
URL = 'http://127.0.0.1:5386/avatar-component-preview.html?framing=meadow&state=idle&bars=0&sim=0'

ap = argparse.ArgumentParser()
ap.add_argument('--mode', choices=['headless', 'headed'], required=True)
ap.add_argument('--only', default='')
ap.add_argument('--out-sub', default='')
args = ap.parse_args()

ts = json.loads((FRONT / 'scripts' / 'lipsync-eval' / 'testset-wide.json').read_text(encoding='utf-8'))
names = [f"{i['id']}.{i['variant']}" for i in ts['ar']] + [i['id'] for i in ts['en']]
if args.only:
    want = set(args.only.split(','))
    names = [n for n in names if n in want or n.split('.')[0] in want]

raw = OUT / 'raw' / (args.out_sub or args.mode)
raw.mkdir(parents=True, exist_ok=True)

chrome_args = ['--autoplay-policy=no-user-gesture-required', '--disable-background-timer-throttling', '--disable-renderer-backgrounding']
if args.mode == 'headed':
    chrome_args += ['--window-position=-3000,0', '--mute-audio', '--disable-features=CalculateNativeWinOcclusion', '--disable-backgrounding-occluded-windows']


def main():
    with sync_playwright() as pw:
        b = pw.chromium.launch(channel='msedge', headless=(args.mode == 'headless'), args=chrome_args)
        ctx = b.new_context(viewport={'width': 1440, 'height': 900})
        ctx.add_init_script(path=str(HERE / 'helpers.js'))
        page = ctx.new_page()
        errs = []
        page.on('console', lambda m: errs.append(f'{m.type}: {m.text}') if m.type in ('error',) else None)
        page.on('pageerror', lambda e: errs.append(f'pageerror: {e}'))
        page.on('requestfailed', lambda r: errs.append(f'requestfailed: {r.url}'))
        page.goto(URL)
        page.wait_for_function('() => window.__voice && window.__control && window.__control.current', timeout=60000)
        page.wait_for_timeout(2500)
        lat = page.evaluate("""async () => { const c = new AudioContext(); await c.resume(); await new Promise((r) => setTimeout(r, 500)); const v = c.outputLatency || 0; c.close(); return v; }""")
        print('output latency', lat)
        clips = {c['name']: c for c in page.evaluate('() => window.__voice.clips')}
        t_all = time.time()
        for n, name in enumerate(names):
            clip = clips.get(name)
            if clip is None:
                print('missing clip', name)
                continue
            e0 = len(errs)
            page.evaluate('() => window.__rec.start()')
            page.evaluate('(c) => window.__voice.speak(c)', clip)
            t0 = time.time()
            while time.time() - t0 < 6 and not page.evaluate('() => Boolean(window.__voice.playing)'):
                page.wait_for_timeout(30)
            while time.time() - t0 < 60 and page.evaluate('() => Boolean(window.__voice.playing)'):
                page.wait_for_timeout(100)
            page.wait_for_timeout(900)
            r = page.evaluate('() => window.__rec.stop()')
            r['errors'] = errs[e0:]
            r['clip'] = name
            r['mode'] = args.mode
            r['outputLatencyMs'] = lat * 1000
            (raw / f'{name}.json').write_text(json.dumps(r), encoding='utf-8')
            print(f'[{n + 1}/{len(names)}] {name}: {len(r["rows"])} frames, audio {r["duration"]:.2f}s, nonFinite {r["nonFinite"]}, errors {len(r["errors"])}', flush=True)
            page.wait_for_timeout(400)
        print('total', round(time.time() - t_all), 's; all errors:', errs)
        ctx.close()
        b.close()


main()
