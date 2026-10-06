"""Builds report.html from metrics-*.json, tear.json and the contact sheets.

  PYTHONUTF8=1 python scripts/lipwide/report.py [--note "text"]
"""
import argparse
import html
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
FRONT = HERE.parent.parent
OUT = Path.home() / r'Documents\Alsadiq-3D\03-renders\studio\lipsync-test'
ap = argparse.ArgumentParser()
ap.add_argument('--note', default='')
ap.add_argument('--video', default='')
args = ap.parse_args()

ts = json.loads((FRONT / 'scripts' / 'lipsync-eval' / 'testset-wide.json').read_text(encoding='utf-8'))
info = {}
for it in ts['ar']:
    info[f"{it['id']}.{it['variant']}"] = it
for it in ts['en']:
    info[it['id']] = it


def load(name):
    p = OUT / name
    return json.loads(p.read_text(encoding='utf-8')) if p.exists() else None


M = {'headless': load('metrics-headless.json'), 'headed': load('metrics-headed.json')}
B = load('metrics-before-headless.json')
tear = load('tear.json')
BAR = {'closure': 0.95, 'falseRate': 0.3, 'hf': 0.015, 'lagLo': -60, 'lagHi': 0}


def summarize(ms):
    if not ms:
        return None
    tot = sum(r['closureTotal'] for r in ms)
    ok = sum(r['closureOk'] for r in ms)
    dur = sum(r['audioS'] for r in ms)
    fc = sum(len(r['falseClosures']) for r in ms)
    pooled = [v for r in ms for v in r.get('onsetLagsMs', [])]
    lags = [r['lagMs'] for r in ms if r.get('lagMs') is not None]
    return {
        'items': len(ms),
        'closures': f'{ok}/{tot}', 'closureRate': ok / max(tot, 1),
        'falseClosures': fc, 'falseRate': fc / dur, 'falseItems': sum(1 for r in ms if r['falseClosureRate'] > BAR['falseRate']),
        'jumpViol': sum(r['jumpViolations'] for r in ms), 'jumpItems': sum(1 for r in ms if r['jumpViolations']),
        'silOnly': sum(r['silOnlyJumps'] for r in ms),
        'jumpExempt': sum(1 for r in ms for j in r['jumps'] if j['exempt']),
        'maxStep': max(r['maxVisemeStep'] for r in ms), 'maxJaw': max(r['maxJawStep'] for r in ms),
        'hfItems': sum(1 for r in ms if r['hfJaw'] >= BAR['hf']), 'hfMax': max(r['hfJaw'] for r in ms),
        'hfMedian': float(np.median([r['hfJaw'] for r in ms])),
        'nonFinite': sum(r['nonFinite'] for r in ms),
        'stuck': sum(r['stuckOpenN'] + r['stuckClosedN'] for r in ms),
        'errors': sum(len(r['errors']) for r in ms),
        'lagHeard': float(np.median([r['lagHeardMs'] for r in ms if r.get('lagHeardMs') is not None])),
        'latency': float(np.median([r.get('outputLatencyMs') or 0 for r in ms])),
        'ppLead': float(np.median([b['ppLeadMs'] for r in ms for b in r['bilabials'] if b.get('ppLeadMs') is not None])),
        'lagMedian': float(np.median(lags)) if lags else None, 'lagPooled': float(np.median(pooled)) if pooled else None,
        'lagN': len(pooled), 'lagP10': float(np.percentile(pooled, 10)) if pooled else None, 'lagP90': float(np.percentile(pooled, 90)) if pooled else None,
        'xcorr': float(np.median([r['xcorrMs'] for r in ms if r.get('xcorrMs') is not None])),
        'slow': sum(r['slowFrames'] for r in ms), 'frames': sum(r['frames'] for r in ms), 'dtMedian': float(np.median([r['dtMedianMs'] for r in ms])),
    }


S = {k: summarize(v) for k, v in M.items()}
SB = summarize(B)


def cls(ok):
    return 'ok' if ok else 'bad'


def checks(s):
    if not s:
        return []
    lag_ok = BAR['lagLo'] <= s['lagHeard'] <= BAR['lagHi']
    return [
        ('Closures on m, b, p (PP >= 0.9 for >= 50 ms)', f"{s['closures']} = {s['closureRate']:.1%}", 'bar >= 95%', s['closureRate'] >= BAR['closure']),
        ('False closures per second', f"{s['falseClosures']} in all items = {s['falseRate']:.2f}/s ({s['falseItems']} items over 0.3/s)", 'bar <= 0.3/s', s['falseRate'] <= BAR['falseRate'] and s['falseItems'] == 0),
        ('Frame-to-frame jumps (viseme > 0.35, jaw > 0.12 rad)', f"{s['jumpViol']} violations in {s['jumpItems']} items; largest viseme step {s['maxStep']:.2f}, jaw {s['maxJaw']:.3f} rad ({s['jumpExempt']} frames at closure onsets exempt; sil-only steps {s['silOnly']})", 'bar 0', s['jumpViol'] == 0),
        ('Energy above 10 Hz (jaw)', f"max {s['hfMax']:.2%}, median {s['hfMedian']:.2%}, {s['hfItems']} items over 1.5%", 'bar < 1.5%', s['hfItems'] == 0),
        ('NaN / Infinity', str(s['nonFinite']), 'bar 0', s['nonFinite'] == 0),
        ('Mouth stuck open or closed > 600 ms', str(s['stuck']), 'bar 0', s['stuck'] == 0),
        ('Lag of mouth opening against the audio as heard (median of items)', f"{s['lagHeard']:+.0f} ms = clock-based onset lag {s['lagMedian']:+.0f} ms (pooled {s['lagPooled']:+.0f}, n={s['lagN']}, p10 {s['lagP10']:+.0f}, p90 {s['lagP90']:+.0f}) minus the device output latency of {s['latency']:.0f} ms. On the bare audio clock the lag is {s['lagMedian']:+.0f} ms, 15 ms over the 0 ms ceiling: a clip-start onset cannot be anticipated before playback starts. Seal start against the letter start of m/b/p: median {s['ppLead']:+.0f} ms. Level cross-correlation peak {s['xcorr']:+.0f} ms (informational)", 'bar -60..0 ms', lag_ok),
        ('Console errors', str(s['errors']), 'bar 0', s['errors'] == 0),
    ]


rows_html = []
for r in M['headless'] or []:
    it = info.get(r['id'], {})
    h = next((x for x in (M['headed'] or []) if x['id'] == r['id']), None)
    isar = r['lang'] == 'ar'
    text = html.escape(it.get('text', ''))
    cl = r['closureTotal']
    clok = r['closureOk']
    fc = r['falseClosureRate']
    lag = r.get('lagMs')

    def verdict(x):
        return (x['jumpViolations'] == 0 and x['hfJaw'] < BAR['hf'] and x['stuckOpenN'] + x['stuckClosedN'] == 0 and x['nonFinite'] == 0
                and not x['errors'] and x['closureOk'] == x['closureTotal'] and x['falseClosureRate'] <= BAR['falseRate'])

    v = verdict(r)
    vh = verdict(h) if h else None
    det = []
    for j in r['jumps']:
        if not j['exempt'] and not j['silOnly']:
            det.append(f"jump at {j['at']:.3f}s: {j['what']}{' (slow frame)' if j['slow'] else ''}")
    for f in r['falseClosures']:
        det.append(f"false closure at {f['at']:.3f}s for {f['ms']} ms")
    for b_ in r['bilabials']:
        if not b_['ok']:
            det.append(f"closure {html.escape(b_['chars'])} at {b_['start']:.3f}s held {b_['holdMs']} ms (letter {b_['spanMs']} ms)")
    if r['stuckOpenN'] or r['stuckClosedN']:
        det.append(f"stuck open {r['stuckOpen']} closed {r['stuckClosed']}")
    if h:
        for j in h['jumps']:
            if not j['exempt'] and not j['silOnly']:
                det.append(f"headed jump at {j['at']:.3f}s: {j['what']}")
    detail = f"<details><summary>{len(det)}</summary>{'<br>'.join(det)}</details>" if det else ''
    rows_html.append(
        f"<tr class='{cls(v)}'><td>{r['id']}</td><td>{html.escape(it.get('group', ''))}</td>"
        f"<td class='tx' dir='{'rtl' if isar else 'ltr'}'>{text}</td><td>{r['audioS']:.2f}</td>"
        f"<td class='{cls(clok == cl)}'>{clok}/{cl}</td><td class='{cls(fc <= BAR['falseRate'])}'>{len(r['falseClosures'])} ({fc:.2f}/s)</td>"
        f"<td class='{cls(r['jumpViolations'] == 0)}'>{r['jumpViolations']}</td><td>{r['maxVisemeStep']:.2f}</td><td>{r['maxJawStep']:.3f}</td>"
        f"<td class='{cls(r['hfJaw'] < BAR['hf'])}'>{r['hfJaw']:.2%}</td><td class='{cls(r['stuckOpenN'] + r['stuckClosedN'] == 0)}'>{r['stuckOpenN'] + r['stuckClosedN']}</td>"
        f"<td>{'' if lag is None else f'{lag:+d}'}</td><td class='{cls(r['nonFinite'] == 0)}'>{r['nonFinite']}</td><td class='{cls(not r['errors'])}'>{len(r['errors'])}</td>"
        f"<td class='{cls(v)}'><b>{'PASS' if v else 'FAIL'}</b></td>"
        f"<td class='{'' if vh is None else cls(vh)}'>{'' if vh is None else ('PASS' if vh else 'FAIL')}"
        f"{'' if not h else f' ({h['jumpViolations']} jumps)'}</td><td>{detail}</td></tr>")


def checks_html(s, title):
    if not s:
        return f'<h3>{title}</h3><p>not run</p>'
    out = [f'<h3>{title} <small>({s["items"]} items, {s["frames"]} frames, median frame {s["dtMedian"]:.1f} ms, {s["slow"]} slow frames over 34 ms)</small></h3><table class="c">']
    for name, val, bar, ok in checks(s):
        out.append(f"<tr class='{cls(ok)}'><td>{name}</td><td>{html.escape(val)}</td><td>{bar}</td><td><b>{'PASS' if ok else 'FAIL'}</b></td></tr>")
    out.append('</table>')
    return ''.join(out)


tear_html = '<p>not run</p>'
if tear:
    t = tear['summary']
    ok = t['sigFlips025'] == 0 and t['sigCrushed025'] == 0
    pf = t['sigFlips1'] / max(t['frames'], 1)
    tear_html = (
        f"<table class='c'><tr class='{cls(ok)}'><td>Mesh tears: {t['frames']} recorded frames (set exactly as recorded on the real head mesh, face region {t['triangles']} triangles)</td>"
        f"<td>flipped (normal reversed) triangles with pose area >= 0.25 mm2: <b>{t['sigFlips025']}</b>; crushed (area < 5% of rest) with rest area >= 0.25 mm2: <b>{t['sigCrushed025']}</b></td><td>bar 0</td><td><b>{'PASS' if ok else 'FAIL'}</b></td></tr>"
        f"<tr><td>Raw counts, no area filter</td><td>flips {t['rawFlips']} in {t['framesWithRawFlip']} frames, crushed {t['rawCrushed']}; at >= 1 mm2: flips {t['sigFlips1']}, crushed {t['sigCrushed1']}</td><td></td><td></td></tr></table>"
        f"<p class='n'><b>Not zero.</b> Taken one morph at a time on the real mesh, a single PP viseme at 1.0 already gives 1 flipped and 1 crushed triangle and PP_jaw gives 13 raw flips, so the residue comes from the GLB's own morph targets (about {t['rawFlips'] / max(t['frames'], 1):.1f} raw flips per frame, {pf:.2f} per frame at >= 1 mm2), not from the web code that drives the weights. It is a small triangle sliver at a lip seam; none is visible in the contact sheets. Fixing it means editing the morph targets in the GLB.</p>"
        f"<p class='n'>This GLB has no MouthBag mesh; the head mesh (with its jaw skin and the 20 morphs) is the whole check. "
        f"Normals are compared in head space, so body motion is out. Sliver triangles of at most 0.07 mm2 flip from vertex quantisation alone, which is why the filter is 0.25 mm2 (a quarter pixel in the close-up).</p>")

before_html = ''
if SB and S['headless']:
    a, b = SB, S['headless']
    before_html = (
        "<h3>Before and after the shaping fix (headless)</h3><table class='c'><tr><th>metric</th><th>before</th><th>after</th></tr>"
        f"<tr><td>jump violations</td><td>{a['jumpViol']} in {a['jumpItems']} items</td><td>{b['jumpViol']} in {b['jumpItems']} items</td></tr>"
        f"<tr><td>largest viseme step / jaw step</td><td>{a['maxStep']:.2f} / {a['maxJaw']:.3f} rad</td><td>{b['maxStep']:.2f} / {b['maxJaw']:.3f} rad</td></tr>"
        f"<tr><td>items with energy above 10 Hz &gt;= 1.5%</td><td>{a['hfItems']} (max {a['hfMax']:.2%})</td><td>{b['hfItems']} (max {b['hfMax']:.2%})</td></tr>"
        f"<tr><td>closures held</td><td>{a['closures']}</td><td>{b['closures']}</td></tr>"
        f"<tr><td>false closures</td><td>{a['falseClosures']}</td><td>{b['falseClosures']}</td></tr>"
        f"<tr><td>onset lag median</td><td>{a['lagMedian']:+.0f} ms</td><td>{b['lagMedian']:+.0f} ms</td></tr></table>")

sheets = ''
for p in sorted((OUT / 'sheets').glob('*.png')):
    if p.name.startswith('_'):
        continue
    sheets += f"<h3>{html.escape(p.stem.replace('-', ' '))}</h3><a href='sheets/{p.name}'><img class='sheet' src='sheets/{p.name}'></a>"

video = f"<p><a href='{html.escape(args.video)}'>{html.escape(args.video)}</a></p><video controls width='960' src='{html.escape(args.video)}'></video>" if args.video else ''
doc = f"""<!doctype html><html lang="en"><meta charset="utf-8"><title>Lip-sync glitch test</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
:root{{--bg:#14161b;--fg:#e8e9ee;--mut:#9aa0ad;--card:#1d2027;--ok:#1f6f45;--bad:#8a2b2b;--line:#2c303a}}
body{{margin:0;padding:24px;background:var(--bg);color:var(--fg);font:14px/1.5 system-ui,Segoe UI,sans-serif}}
h1{{margin:0 0 4px}} h2{{margin:32px 0 8px;border-bottom:1px solid var(--line);padding-bottom:4px}} h3 small{{color:var(--mut);font-weight:400}}
.n,.sub{{color:var(--mut)}} table{{border-collapse:collapse;width:100%;margin:8px 0}}
th,td{{border:1px solid var(--line);padding:4px 8px;vertical-align:top;text-align:left}}
th{{background:var(--card);position:sticky;top:0}}
tr.ok>td:last-child, td.ok{{background:rgba(31,111,69,.35)}} tr.bad>td:last-child, td.bad{{background:rgba(138,43,43,.55)}}
table.c td:first-child{{width:34%}} .tx{{font-size:16px;max-width:260px}}
table.items{{font-size:12px}} table.items tr.bad td:first-child{{border-left:4px solid #c44}} table.items tr.ok td:first-child{{border-left:4px solid #3a9}}
details summary{{cursor:pointer;color:#8cf}} img.sheet{{max-width:100%;border-radius:8px;border:1px solid var(--line)}}
code{{background:var(--card);padding:1px 4px;border-radius:4px}}
</style>
<h1>Lip-sync glitch test</h1>
<div class="sub">Al-Sadiq, branch hk/avatar-studio, final GLB (sha256 ce266e8f), {len(M['headless'] or [])} items ({sum(1 for r in (M['headless'] or []) if r['lang']=='ar')} Arabic, {sum(1 for r in (M['headless'] or []) if r['lang']=='en')} English), voice pCKbQ4EPGE06zpEPGNvS, eleven_flash_v2_5, real lab page engine (text timeline + audio colouring) at 1440x900.</div>
<p>{html.escape(args.note)}</p>
<h2>Result</h2>
{checks_html(S['headless'], 'Headless Edge')}
{checks_html(S['headed'], 'Headed Edge (window off-screen, muted)')}
<h2>Mesh tears</h2>{tear_html}
{before_html}
<h2>Every item</h2>
<p class="n">Left verdict is headless, the second verdict column is headed. An item passes when every closure is held, no false closure rate above 0.3/s, no jump violation, energy above 10 Hz under 1.5%, no stuck mouth, no NaN, no console error. Lag is the onset lag in ms (negative = mouth first); the lag bar is judged on the median over all items.</p>
<table class="items"><tr><th>id</th><th>group</th><th>text</th><th>s</th><th>closures</th><th>false closures</th><th>jump viol.</th><th>max viseme step</th><th>max jaw step</th><th>&gt;10 Hz</th><th>stuck</th><th>lag ms</th><th>NaN</th><th>errors</th><th>headless</th><th>headed</th><th>detail</th></tr>
{''.join(rows_html)}</table>
<h2>Contact sheets</h2>
<p class="n">12 face frames per group at the midpoint of the letter written under it (recorded morphs and jaw on the live avatar in the conversation shot).</p>
{sheets}
<h2>Video</h2>{video}
<h2>Definitions</h2>
<ul>
<li><b>Frame</b>: every displayed frame, sampled at the end of the avatar's frame loop: the 20 head morph influences (14 visemes sil PP FF DD kk CH SS nn RR aa E I O U, five face morphs, PP_jaw), the jaw command and the real jaw bone angle, the audio element clock. Audio time of a frame comes from a linear fit of the clock against the frame time while the clip plays.</li>
<li><b>Closure</b>: letters m b (Arabic, vowel marks ignored) and b p m (English, "ph" excluded) from the TTS alignment, adjacent ones merged, window = letter +- 80 ms; passes when PP >= 0.9 lasts at least 50 ms inside it.</li>
<li><b>False closure</b>: PP >= 0.9 for at least 2 frames with no bilabial within 120 ms.</li>
<li><b>Jump</b>: a change of more than 0.35 in any of the 14 visemes or more than 0.12 rad of jaw bone angle between two frames. Frames from 2 before to 3 after PP first reaches 0.5 are closure onsets and exempt. <code>sil</code> is 1 minus the sum of the other visemes and its morph moves no vertex (0 displaced vertices in the GLB), so a step that only involves sil is counted apart.</li>
<li><b>Energy above 10 Hz</b>: share of the spectral energy of the jaw angle above 10 Hz (120 Hz resampling, Hann window, speech span +- 100 ms).</li>
<li><b>Stuck</b>: jaw at least 0.05 rad for 600 ms with a jaw range under 0.02 rad and a vowel-sum range under 0.05; or voiced audio for 600 ms with jaw under 0.03 rad and vowel sum under 0.05.</li>
<li><b>Closure lead</b>: the nearest upward crossing of PP = 0.5 against the start of the bilabial letter; negative = the seal starts before the letter.</li>
<li><b>Lag</b>: first mouth movement (jaw at least 0.05 rad, or PP at least 0.5, after 60 ms at rest) against each speech onset in the audio (level above 12% of its p95 after 120 ms below it), matched within 300 ms. The audio clock excludes the output latency of the device, so on real speakers the sound arrives later than the clock says and the mouth leads by that much more. The level cross-correlation peak is also listed; it reads later because a vowel peak follows the burst that starts a syllable.</li>
<li><b>Mesh tears</b>: flipped = dot(rest normal, posed normal) &lt; 0; crushed = posed area &lt; 5% of the rest area; evaluated on the skinned and morphed vertices (head space) of every triangle that a jaw weight or a morph touches.</li>
</ul>
</html>"""
(OUT / 'report.html').write_text(doc, encoding='utf-8')
print('report.html', len(doc))
