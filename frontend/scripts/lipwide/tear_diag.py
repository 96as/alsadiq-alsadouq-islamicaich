"""Diagnostic: take one recorded frame, then drop or isolate each non-zero morph and the jaw rotation, to see
which part of the pose produces the flipped triangles.

  PYTHONUTF8=1 python scripts/lipwide/tear_diag.py <item> <frame>
"""
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).parent
OUT = Path.home() / r'Documents\Alsadiq-3D\03-renders\studio\lipsync-test'
URL = 'http://127.0.0.1:5386/avatar-component-preview.html?framing=meadow&state=idle&bars=0&sim=0'

item = sys.argv[1] if len(sys.argv) > 1 else 'we19'
frame = int(sys.argv[2]) if len(sys.argv) > 2 else 25
raw = json.loads((OUT / 'raw' / 'headless' / f'{item}.json').read_text(encoding='utf-8'))
r = raw['rows'][frame]

JS = """async (r) => {
  const c = window.__control.current;
  const jr = c.bones.jawRest;
  const base = r.m[0];
  const frames = [];
  const labels = [];
  const add = (l, m, q) => { frames.push({ m: [m], q }); labels.push(l); };
  add('recorded', base, r.q);
  add('recorded, jaw at rest', base, [jr.x, jr.y, jr.z, jr.w]);
  for (let i = 0; i < base.length; i++) if (base[i] > 0.0005) { const m = base.slice(); m[i] = 0; add('without ' + i, m, r.q); }
  for (let i = 0; i < base.length; i++) if (base[i] > 0.0005) { const m = new Array(base.length).fill(0); m[i] = base[i]; add('only ' + i + ' = ' + base[i], m, r.q); }
  const out = await window.__tearCheck(frames, [0.25]);
  return { q: [jr.x, jr.y, jr.z, jr.w], out: out.map((o, i) => ({ l: labels[i], flips: o.flips, crushed: o.crushed, sig: o.sig[0] })) };
}"""

with sync_playwright() as pw:
    b = pw.chromium.launch(channel='msedge', headless=True, args=['--autoplay-policy=no-user-gesture-required'])
    ctx = b.new_context(viewport={'width': 1440, 'height': 900})
    ctx.add_init_script(path=str(HERE / 'helpers.js'))
    page = ctx.new_page()
    page.goto(URL)
    page.wait_for_function('() => window.__voice && window.__control && window.__control.current', timeout=60000)
    page.wait_for_timeout(2500)
    for k in range(12):
        one = page.evaluate("async (r) => { const o = await window.__tearCheck([{ m: r.m, q: r.q }], [0.25]); return [o[0].flips, o[0].sig[0].flips, o[0].crushed, window.__control.current.bones.jaw.quaternion.toArray().map((v) => +v.toFixed(3)), window.__control.current.state || null]; }", r)
        print('t', k, one)
        page.wait_for_timeout(450)
    res = page.evaluate(JS, r)
    print('jawRest', res['q'], 'recorded q', r['q'])
    print('m', [round(x, 3) for x in r['m'][0]])
    for o in res['out']:
        print(o['l'], o['flips'], o['crushed'], o['sig'])
    ctx.close()
    b.close()
