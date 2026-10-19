"""Mesh tear check on 300 recorded frames: sets the recorded morphs and jaw on the real mesh in the lab page and
counts flipped (normal dot < 0) and crushed (area ratio < 0.05) triangles of the face region (head-local).

  PYTHONUTF8=1 python scripts/lipwide/tear.py [--mode headless] [--n 300]

Writes <OUT>/tear.json. Frames per item: peak closure, peak jaw, biggest step, plus evenly spaced fills.
"""
import argparse
import json
from pathlib import Path

import numpy as np
from playwright.sync_api import sync_playwright

HERE = Path(__file__).parent
OUT = Path.home() / r'Documents\Alsadiq-3D\03-renders\studio\lipsync-test'
URL = 'http://127.0.0.1:5386/avatar-component-preview.html?framing=meadow&state=idle&bars=0&sim=0'

ap = argparse.ArgumentParser()
ap.add_argument('--mode', default='headless')
ap.add_argument('--n', type=int, default=300)
args = ap.parse_args()

files = sorted((OUT / 'raw' / args.mode).glob('*.json'))
per = max(4, args.n // len(files))
picked = []
meta = []
for p in files:
    raw = json.loads(p.read_text(encoding='utf-8'))
    rows = raw['rows']
    M = np.array([[v or 0 for v in r['m'][0]] for r in rows])
    ja = np.array([r['ja'] for r in rows])
    step = np.r_[0, np.abs(np.diff(M[:, :14], axis=0)).max(axis=1)]
    idx = [int(M[:, 1].argmax()), int(ja.argmax()), int(step.argmax())]
    speaking = [i for i, r in enumerate(rows) if r['pa'] == 0 and r['at'] > 0.02]
    k = per - 3
    if speaking and k > 0:
        for q in np.linspace(0, len(speaking) - 1, k + 2)[1:-1]:
            idx.append(speaking[int(q)])
    seen = set()
    for i in idx:
        if i in seen:
            continue
        seen.add(i)
        r = rows[i]
        picked.append({'m': r['m'], 'q': r['q']})
        meta.append({'id': p.stem, 'frame': i, 'at': r['at'], 'maxViseme': float(M[i, :14].max()), 'jaw': float(ja[i]), 'PP': float(M[i, 1])})
picked = picked[:args.n + 20]
meta = meta[:len(picked)]
print('frames', len(picked))

with sync_playwright() as pw:
    b = pw.chromium.launch(channel='msedge', headless=True, args=['--autoplay-policy=no-user-gesture-required'])
    ctx = b.new_context(viewport={'width': 1440, 'height': 900})
    ctx.add_init_script(path=str(HERE / 'helpers.js'))
    page = ctx.new_page()
    errs = []
    page.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
    page.on('pageerror', lambda e: errs.append(str(e)))
    page.goto(URL)
    page.wait_for_function('() => window.__voice && window.__control && window.__control.current', timeout=60000)
    page.wait_for_timeout(2500)
    res = []
    for i in range(0, len(picked), 15):
        res += page.evaluate('(f) => window.__tearCheck(f, [0.25, 1.0])', picked[i:i + 15])
    ctx.close()
    b.close()

summary = {
    'frames': len(res),
    'triangles': res[0]['nTri'],
    'rawFlips': int(sum(r['flips'] for r in res)),
    'rawCrushed': int(sum(r['crushed'] for r in res)),
    'framesWithRawFlip': int(sum(1 for r in res if r['flips'])),
    'sigFlips025': int(sum(r['sig'][0]['flips'] for r in res)),
    'sigCrushed025': int(sum(r['sig'][0]['crushed'] for r in res)),
    'sigFlips1': int(sum(r['sig'][1]['flips'] for r in res)),
    'sigCrushed1': int(sum(r['sig'][1]['crushed'] for r in res)),
    'consoleErrors': errs,
}
worst = sorted([(r['worst'], m) for r, m in zip(res, meta) if r['worst']], key=lambda x: x[0]['dot'])[:8]
(OUT / 'tear.json').write_text(json.dumps({'summary': summary, 'worst': [{'w': w, 'm': m} for w, m in worst], 'frames': [dict(m, **{k: r[k] for k in ('flips', 'crushed', 'nTri')}, sig=r['sig']) for r, m in zip(res, meta)]}, indent=1), encoding='utf-8')
print(json.dumps(summary, indent=1))
for w, m in worst[:5]:
    print(w, m['id'], m['frame'])
