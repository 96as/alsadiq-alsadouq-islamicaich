"""Contact sheets: 12 face frames per item group with the letter under each frame.

  PYTHONUTF8=1 python scripts/lipwide/sheets.py [--mode headless]

The poses are the recorded morphs and jaw of the real run, rendered on the live avatar in the conversation shot
(page state listening). Sheets are built as HTML (the browser shapes Arabic) and screenshotted to <OUT>/sheets/.
"""
import argparse
import html
import json
import re
from pathlib import Path

import numpy as np
from playwright.sync_api import sync_playwright

HERE = Path(__file__).parent
FRONT = HERE.parent.parent
OUT = Path.home() / r'Documents\Alsadiq-3D\03-renders\studio\lipsync-test'
URL = 'http://127.0.0.1:5386/avatar-component-preview.html?framing=meadow&state=listening&bars=0&sim=0'
MARKS = re.compile('[\u064b-\u065f\u0670\u0640]')

ap = argparse.ArgumentParser()
ap.add_argument('--mode', default='headless')
ap.add_argument('--only', default='')
args = ap.parse_args()

ts = json.loads((FRONT / 'scripts' / 'lipsync-eval' / 'testset-wide.json').read_text(encoding='utf-8'))
groups = {}
for it in ts['ar']:
    groups.setdefault(it['group'], []).append((f"{it['id']}.{it['variant']}", 'ar'))
for it in ts['en']:
    groups.setdefault(it['group'], []).append((it['id'], 'en'))

PRIO_AR = {'م': 5, 'ب': 5, 'ف': 4, 'و': 3, 'ث': 3, 'ذ': 3, 'ظ': 3, 'ص': 3, 'ض': 3, 'ط': 3, 'ع': 3, 'ح': 3, 'ق': 3, 'غ': 3, 'خ': 3, 'ه': 2, 'ء': 2, 'ر': 2, 'ش': 2, 'س': 2, 'ا': 2, 'ي': 2, 'ن': 2, 'ل': 1, 'ز': 2}
PRIO_EN = {'m': 5, 'b': 5, 'p': 5, 'f': 4, 'v': 4, 'w': 3, 'o': 3, 'u': 3, 'a': 2, 'e': 2, 'i': 2, 'r': 2, 's': 2, 'l': 1}


def units(lang, al):
    ch, st, en = al['characters'], al['starts'], al['ends']
    out = []
    for i, c in enumerate(ch):
        if c.isspace() or MARKS.match(c) or not c.strip():
            continue
        if not c.isalpha():
            continue
        label = c
        j = i + 1
        while lang == 'ar' and j < len(ch) and MARKS.match(ch[j]):
            label += ch[j]
            j += 1
        out.append({'label': label, 'mid': (st[i] + en[i]) / 2, 'c': c, 'prio': (PRIO_AR if lang == 'ar' else PRIO_EN).get(c.lower(), 1), 'marked': len(label) > 1})
    return out


def pick(group, members):
    cand = []
    for name, lang in members:
        al = json.loads((FRONT / 'dev-audio' / ('eval-ar' if lang == 'ar' else 'eval-en') / f'{name}.align.json').read_text(encoding='utf-8'))
        for u in units(lang, al):
            cand.append(dict(u, item=name, lang=lang))
    chosen = []
    seen_letters = set()
    per_item = {}
    # greedy: highest priority first, letters not yet shown, at most 3 per item, then fill
    order = sorted(range(len(cand)), key=lambda i: (-(cand[i]['prio'] + (1 if cand[i]['marked'] else 0)), i))
    for rnd in range(3):
        for i in order:
            c = cand[i]
            if len(chosen) >= 12:
                break
            if i in chosen or per_item.get(c['item'], 0) >= 3:
                continue
            key = c['label']
            if rnd == 0 and key in seen_letters:
                continue
            if rnd <= 1 and any(cand[k]['item'] == c['item'] and abs(cand[k]['mid'] - c['mid']) < 0.12 for k in chosen):
                continue
            chosen.append(i)
            seen_letters.add(key)
            per_item[c['item']] = per_item.get(c['item'], 0) + 1
    return [cand[i] for i in chosen][:12]


def frame_at(raw, t_audio):
    rows = raw['rows']
    t = np.array([r['t'] for r in rows]) / 1000.0
    at = np.array([r['at'] for r in rows])
    pa = np.array([r['pa'] for r in rows])
    en = np.array([r['en'] for r in rows])
    dur = raw['duration']
    ok = (pa == 0) & (en == 0) & (at > 0.05) & (at < dur - 0.05)
    b, a = np.polyfit(t[ok], at[ok], 1)
    A = a + b * t
    return int(np.abs(A - t_audio).argmin()), A


(OUT / 'sheets').mkdir(parents=True, exist_ok=True)
plans = {}
for g, members in groups.items():
    if args.only and not g.startswith(args.only):
        continue
    chosen = pick(g, members)
    chosen.sort(key=lambda c: (c['item'], c['mid']))
    poses = []
    for c in chosen:
        raw = json.loads((OUT / 'raw' / args.mode / f"{c['item']}.json").read_text(encoding='utf-8'))
        i, A = frame_at(raw, c['mid'])
        r = raw['rows'][i]
        poses.append({'m': r['m'], 'q': r['q']})
        c['frame'] = i
        c['viseme'] = ', '.join(f'{n} {v:.2f}' for n, v in sorted(zip(['sil', 'PP', 'FF', 'DD', 'kk', 'CH', 'SS', 'nn', 'RR', 'aa', 'E', 'I', 'O', 'U'], r['m'][0][:14]), key=lambda x: -x[1])[:2] if v > 0.05)
        c['jaw'] = round(r['ja'], 3)
    plans[g] = (chosen, poses)

with sync_playwright() as pw:
    b = pw.chromium.launch(channel='msedge', headless=True, args=['--autoplay-policy=no-user-gesture-required'])
    ctx = b.new_context(viewport={'width': 1440, 'height': 900})
    ctx.add_init_script(path=str(HERE / 'helpers.js'))
    page = ctx.new_page()
    page.goto(URL)
    page.wait_for_function('() => window.__voice && window.__control && window.__control.current', timeout=60000)
    page.wait_for_timeout(4500)  # the conversation shot eases in
    print('shot', page.evaluate('() => JSON.stringify(window.__control.current.shot && window.__control.current.shot.current ? 1 : 0)'))
    page.screenshot(path=str(OUT / 'sheets' / '_shot.png'))
    first = True
    for g, (chosen, poses) in plans.items():
        caps = page.evaluate('(p) => window.__capturePoses(p, 360)', poses)
        bad = [c for c in caps if 'error' in c]
        if bad:
            print('capture errors', bad[:2])
        cells = []
        for c, cap in zip(chosen, caps):
            lab = html.escape(c['label'])
            cells.append(
                f'<figure><img src="{cap.get("url", "")}"><figcaption><span class="L" lang="{c["lang"]}" dir="{"rtl" if c["lang"] == "ar" else "ltr"}">{lab}</span>'
                f'<span class="m">{html.escape(c["item"])} @ {c["mid"]:.2f}s<br>{html.escape(c["viseme"] or "rest")} &middot; jaw {c["jaw"]}</span></figcaption></figure>')
        doc = f'''<!doctype html><meta charset="utf-8"><style>
body{{margin:0;background:#15171c;color:#eee;font:14px system-ui,sans-serif;padding:16px;width:1288px}}
h1{{font-size:20px;margin:0 0 12px}}
.g{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}}
figure{{margin:0;background:#20232b;border-radius:8px;overflow:hidden}}
img{{width:100%;display:block}}
figcaption{{display:flex;align-items:center;gap:12px;padding:8px 10px}}
.L{{font-size:40px;line-height:1.1;min-width:64px;text-align:center;font-family:"Segoe UI","Noto Naskh Arabic",serif}}
.m{{font-size:12px;opacity:.8}}
</style><h1>{html.escape(g)} &mdash; {args.mode}, face frames at the letter's midpoint</h1><div class="g">{"".join(cells)}</div>'''
        sp = ctx.new_page()
        sp.set_viewport_size({'width': 1320, 'height': 900})
        sp.set_content(doc)
        sp.wait_for_timeout(300)
        slug = re.sub(r'[^A-Za-z0-9]+', '-', g).strip('-').lower()
        sp.screenshot(path=str(OUT / 'sheets' / f'{slug}.png'), full_page=True)
        (OUT / 'sheets' / f'{slug}.json').write_text(json.dumps([{k: v for k, v in c.items()} for c in chosen], ensure_ascii=False, indent=1), encoding='utf-8')
        sp.close()
        print('sheet', slug)
    ctx.close()
    b.close()
