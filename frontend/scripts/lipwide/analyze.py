"""Metrics for the wide lip-sync glitch test. Reads <OUT>/raw/<mode>/<id>.json (from run.py), the cached alignment
and f32 audio, and writes <OUT>/metrics-<mode>.json.

  PYTHONUTF8=1 python scripts/lipwide/analyze.py --mode headless

Definitions (also printed in report.html):
  audio time of a frame   linear fit of audio.currentTime against the frame clock while the clip plays
  bilabial truth          alignment characters m b (Arabic, marks ignored) and b p m (English, 'ph' excluded),
                          adjacent bilabials merged, window = character span +- 80 ms
  closure pass            longest run of PP >= 0.9 inside the window lasts >= 50 ms (frame count x frame time)
  false closure           a PP >= 0.9 run of >= 2 frames that overlaps no bilabial window +- 120 ms; per second of audio
  jump                    frame-to-frame change > 0.35 in any of the 14 visemes, or > 0.12 rad of jaw bone angle;
                          pairs within 3 frames after PP crosses 0.5 upward (a closure onset) are exempt
  hf energy               share of the spectral energy above 10 Hz of the jaw angle (and of the vowel sum), 120 Hz resampling
  stuck open              jaw >= 0.05 rad for > 600 ms with a jaw range < 0.02 rad and a vowel-sum range < 0.05
  stuck closed            voiced audio for > 600 ms while jaw < 0.03 rad and the vowel sum < 0.05
  lag                     onset lag: first mouth movement (jaw >= 0.05 rad or PP >= 0.5 after 60 ms at rest) against each
                          audio speech onset (level > 12% of p95 after 120 ms below it), matched within 300 ms. lagMs is on the
                          audio-element clock; lagHeardMs subtracts the device output latency (what a listener perceives)
  closure lead            ppLeadMs: the nearest upward crossing of PP = 0.5 against the start of the bilabial letter
                          (negative = the seal starts before the letter); informational
  xcorr                   cross-correlation of the audio level against the jaw angle (informational, reads late)
"""
import argparse
import json
import re
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
FRONT = HERE.parent.parent
OUT = Path.home() / r'Documents\Alsadiq-3D\03-renders\studio\lipsync-test'
VIS = ['sil', 'PP', 'FF', 'DD', 'kk', 'CH', 'SS', 'nn', 'RR', 'aa', 'E', 'I', 'O', 'U']
MARKS = re.compile('[\u064b-\u065f\u0670\u0640\u06d6-\u06ed]')


def load_item(name):
    lang = 'ar' if name.startswith('wa') else 'en'
    d = FRONT / 'dev-audio' / ('eval-ar' if lang == 'ar' else 'eval-en')
    al = json.loads((d / f'{name}.align.json').read_text(encoding='utf-8'))
    f32 = np.fromfile(d / f'{name}.f32', dtype='<f4')
    return lang, al, f32


def bilabials(lang, al):
    ch, st, en = al['characters'], al['starts'], al['ends']
    spans = []
    for i, c in enumerate(ch):
        if lang == 'ar':
            hit = c in 'مب'
        else:
            lc = c.lower()
            hit = lc in 'bm' or (lc == 'p' and not (i + 1 < len(ch) and ch[i + 1].lower() == 'h'))
        if hit:
            spans.append([st[i], en[i], c])
        elif lang == 'ar' and MARKS.match(c):
            continue
    merged = []
    for s in spans:
        if merged and s[0] - merged[-1][1] < 0.03:
            merged[-1][1] = s[1]
            merged[-1][2] += s[2]
        else:
            merged.append(list(s))
    return merged


def runs(mask):
    out = []
    i = 0
    n = len(mask)
    while i < n:
        if mask[i]:
            j = i
            while j + 1 < n and mask[j + 1]:
                j += 1
            out.append((i, j))
            i = j + 1
        else:
            i += 1
    return out


def level_env(f32, sr, hop=0.01, win=0.03):
    h = int(sr * hop)
    w = int(sr * win)
    n = max(1, (len(f32) - w) // h)
    env = np.array([np.sqrt(np.mean(f32[i * h:i * h + w] ** 2)) for i in range(n)])
    return env, hop, win / 2


def analyze(name, raw):
    lang, al, f32 = load_item(name)
    sr = al['sr']
    rows = raw['rows']
    n = len(rows)
    t = np.array([r['t'] for r in rows]) / 1000.0
    at = np.array([r['at'] for r in rows])
    pa = np.array([r['pa'] for r in rows])
    en = np.array([r['en'] for r in rows])
    dur = len(f32) / sr
    M = np.array([[v if v is not None else 0 for v in r['m'][0]] for r in rows], dtype=float)
    V = M[:, :14]
    ja = np.array([r['ja'] for r in rows])
    jw = np.array([r['jw'] for r in rows])
    res = {'id': name, 'lang': lang, 'frames': n, 'audioS': round(dur, 3), 'nonFinite': raw['nonFinite'], 'errors': raw['errors']}
    dt = np.diff(t)
    res['dtMedianMs'] = round(float(np.median(dt)) * 1000, 1)
    res['dtMaxMs'] = round(float(dt.max()) * 1000, 1)
    res['slowFrames'] = int((dt > 0.034).sum())

    ok = (pa == 0) & (en == 0) & (at > 0.05) & (at < dur - 0.05)
    if ok.sum() < 5:
        res['fatal'] = 'audio clock never advanced'
        return res
    b, a = np.polyfit(t[ok], at[ok], 1)
    res['clockSlope'] = round(float(b), 4)
    A = a + b * t  # audio time of every frame

    # --- closures ------------------------------------------------------------------------------------------
    PP = V[:, 1]
    ppmask = PP >= 0.9
    fdt = np.append(dt, np.median(dt))
    bil = bilabials(lang, al)
    items = []
    for s, e, c in bil:
        sel = np.where((A >= s - 0.08) & (A <= e + 0.08))[0]
        best = 0.0
        if len(sel):
            for i0, j0 in runs(ppmask[sel]):
                best = max(best, float(fdt[sel[i0:j0 + 1]].sum()))
        lead = None
        if s > 0.12:
            up = [i for i in range(1, n) if PP[i] >= 0.5 > PP[i - 1] and s - 0.3 <= A[i] <= e]
            if up:
                # the crossing nearest to the letter start (a closure just before it is another letter's)
                lead = round(float(min((A[i] - s for i in up), key=abs)) * 1000)
        items.append({'chars': c, 'start': round(s, 3), 'end': round(e, 3), 'holdMs': round(best * 1000), 'ok': best >= 0.05, 'spanMs': round((e - s) * 1000), 'ppLeadMs': lead})
    res['bilabials'] = items
    res['closureTotal'] = len(items)
    res['closureOk'] = sum(1 for x in items if x['ok'])
    res['closureRate'] = (res['closureOk'] / len(items)) if items else None

    fc = []
    for i0, j0 in runs(ppmask):
        if j0 - i0 + 1 < 2:
            continue
        s0, e0 = A[i0], A[j0]
        near = any(s0 <= e + 0.12 and e0 >= s - 0.12 for s, e, _ in bil)
        if not near:
            fc.append({'at': round(float(s0), 3), 'frames': j0 - i0 + 1, 'ms': round(float(fdt[i0:j0 + 1].sum()) * 1000)})
    res['falseClosures'] = fc
    res['falseClosureRate'] = round(len(fc) / dur, 3)

    # --- jumps ---------------------------------------------------------------------------------------------
    onsets = [k for k in range(1, n) if PP[k] >= 0.5 and (PP[k - 1] < 0.5 or PP[k] - PP[k - 1] > 0.1) and PP[k - 1] < 0.9]
    exempt = set()
    for k in onsets:
        for q in range(max(1, k - 2), min(n, k + 4)):
            exempt.add(q)
    jumps = []
    dV = np.abs(np.diff(V, axis=0))
    dJ = np.abs(np.diff(ja))
    for p in range(1, n):
        mx = dV[p - 1].max()
        jv = dJ[p - 1]
        mxg = dV[p - 1][1:].max()  # geometric visemes: sil is 1 - sum of the others and moves no vertex
        if mx > 0.35 or jv > 0.12:
            which = []
            if mx > 0.35:
                which.append(VIS[int(dV[p - 1].argmax())] + f' {dV[p - 1].max():.2f}')
            if jv > 0.12:
                which.append(f'jaw {jv:.3f} rad')
            jumps.append({'frame': p, 'at': round(float(A[p]), 3), 'what': ', '.join(which), 'exempt': p in exempt, 'silOnly': bool(mxg <= 0.35 and jv <= 0.12), 'dtMs': round(float(dt[p - 1]) * 1000, 1), 'slow': bool(dt[p - 1] > 0.034)})
    res['jumps'] = jumps
    res['jumpViolations'] = sum(1 for j in jumps if not j['exempt'] and not j['silOnly'])
    res['silOnlyJumps'] = sum(1 for j in jumps if not j['exempt'] and j['silOnly'])
    res['maxVisemeStep'] = round(float(dV[:, 1:].max()), 3)
    res['maxJawStep'] = round(float(dJ.max()), 4)
    res['closureOnsets'] = len(onsets)

    # --- high-frequency energy -----------------------------------------------------------------------------
    voice_env, hop, _ = level_env(f32, sr)
    thr = max(0.012, 0.06 * np.percentile(voice_env, 99))
    voiced = voice_env > thr
    vi = np.where(voiced)[0]
    sp0 = vi[0] * hop if len(vi) else 0.0
    sp1 = vi[-1] * hop + 0.03 if len(vi) else dur
    res['speechS'] = [round(float(sp0), 3), round(float(sp1), 3)]
    grid = np.arange(sp0 - 0.1, sp1 + 0.1, 1 / 120)
    vow = V[:, 9:14].sum(axis=1)

    def hf(sig):
        y = np.interp(grid, A, sig)
        y = y - y.mean()
        w = np.hanning(len(y))
        X = np.abs(np.fft.rfft(y * w)) ** 2
        f = np.fft.rfftfreq(len(y), 1 / 120)
        tot = X[1:].sum()
        return float(X[f > 10].sum() / tot) if tot > 1e-12 else 0.0

    res['hfJaw'] = round(hf(ja), 5)
    res['hfVowel'] = round(hf(vow), 5)

    # --- stuck ---------------------------------------------------------------------------------------------
    stuck_open = []
    stuck_closed = []
    wlen = int(round(0.6 / np.median(dt)))
    inspeech = (A >= sp0 - 0.05) & (A <= sp1 + 0.05)
    for i in range(0, n - wlen):
        seg = slice(i, i + wlen)
        if A[i + wlen - 1] - A[i] < 0.59:
            continue
        if ja[seg].min() >= 0.05 and np.ptp(ja[seg]) < 0.02 and np.ptp(vow[seg]) < 0.05:
            stuck_open.append(round(float(A[i]), 3))
        # closed: voiced audio throughout the window
        a0, a1 = A[i], A[i + wlen - 1]
        i0 = max(0, int(a0 / hop))
        i1 = min(len(voiced), int(a1 / hop))
        if i1 - i0 > 40 and voiced[i0:i1].mean() > 0.9 and ja[seg].max() < 0.03 and vow[seg].max() < 0.05:
            stuck_closed.append(round(float(A[i]), 3))
    res['stuckOpen'] = stuck_open[:3]
    res['stuckOpenN'] = len(stuck_open)
    res['stuckClosed'] = stuck_closed[:3]
    res['stuckClosedN'] = len(stuck_closed)
    res['inspeechFrames'] = int(inspeech.sum())
    tail = (A > dur + 0.45)
    res['tailJawMax'] = round(float(ja[tail].max()), 4) if tail.any() else None

    # --- lag -----------------------------------------------------------------------------------------------
    # onset lag: the first mouth movement (jaw >= 0.05 rad or PP >= 0.5, after >= 60 ms at rest) against each
    # speech onset of the audio (level > 12% of its p95 after >= 120 ms below it); negative = the mouth leads
    he = 0.005
    env5, hop5, _ = level_env(f32, sr, hop=he, win=0.02)
    g5 = np.arange(0, dur, he)
    e5 = np.interp(g5, np.arange(len(env5)) * hop5 + 0.01, env5)
    e5 = e5 / max(np.percentile(e5, 95), 1e-9)

    def edges(active, minlow):
        out_, low, prev = [], minlow + 1, False
        for i, a_ in enumerate(active):
            if a_ and not prev and low >= minlow:
                out_.append(g5[i])
            low = 0 if a_ else low + he
            prev = a_
        return out_

    ea = edges(e5 > 0.12, 0.12)
    act = (np.interp(g5, A, ja) >= 0.05) | (np.interp(g5, A, PP) >= 0.5)
    em = edges(act, 0.06)
    lags_on = []
    for x in ea:
        if not em:
            break
        d = np.array(em) - x
        k_ = int(np.argmin(np.abs(d)))
        if abs(d[k_]) < 0.3:
            lags_on.append(float(d[k_] * 1000))
    res['onsetLagsMs'] = [round(v) for v in lags_on]
    res['lagMs'] = round(float(np.median(lags_on))) if lags_on else None
    lat_ms = float(raw.get('outputLatencyMs') or 0.0)
    res['outputLatencyMs'] = round(lat_ms, 1)
    res['lagHeardMs'] = round(float(np.median(lags_on)) - lat_ms) if lags_on else None
    res['onsetLagsHeardMs'] = [round(v - lat_ms) for v in lags_on]
    # level cross-correlation (informational: a vowel peak follows the burst that starts a syllable, so it reads late)
    g = np.arange(max(0.0, sp0 - 0.05), min(dur, sp1 + 0.05), 0.01)
    res['xcorrMs'] = None
    if len(g) > 40:
        envs = np.interp(g, np.arange(len(voice_env)) * hop + 0.015, voice_env)
        envs = np.convolve(envs, np.ones(5) / 5, mode='same')
        e0 = (envs - envs.mean()) / (envs.std() + 1e-9)
        gj = np.arange(-0.5, dur + 0.5, 0.01)
        jj = np.interp(gj, A, ja)
        best, bl = -2, 0
        for L in range(-15, 16):
            idx = np.clip(np.round((g + L * 0.01 - gj[0]) / 0.01).astype(int), 0, len(jj) - 1)
            y = jj[idx]
            c = float((e0 * ((y - y.mean()) / (y.std() + 1e-9))).mean())
            if c > best:
                best, bl = c, L
        res['xcorrMs'] = bl * 10
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--mode', required=True)
    args = ap.parse_args()
    rawd = OUT / 'raw' / args.mode
    out = []
    for p in sorted(rawd.glob('*.json')):
        raw = json.loads(p.read_text(encoding='utf-8'))
        out.append(analyze(p.stem, raw))
    (OUT / f'metrics-{args.mode}.json').write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')
    lags = [r['lagMs'] for r in out if r.get('lagMs') is not None]
    pooled = [v for r in out for v in r.get('onsetLagsMs', [])]
    print(f'{len(out)} items; onset lag: median of items {np.median(lags):.0f} ms, pooled {np.median(pooled):.0f} ms (n={len(pooled)}), p10/p90 {np.percentile(pooled, 10):.0f}/{np.percentile(pooled, 90):.0f}')

    hl=[r['lagHeardMs'] for r in out if r.get('lagHeardMs') is not None]
    pl = [b['ppLeadMs'] for r in out for b in r.get('bilabials', []) if b.get('ppLeadMs') is not None]
    print(f'heard-based lag median {np.median(hl):.0f} ms; closure lead (PP>=0.5 vs letter start) median {np.median(pl):.0f} ms n={len(pl)} p10/p90 {np.percentile(pl,10):.0f}/{np.percentile(pl,90):.0f}')
    xs = [r['xcorrMs'] for r in out if r.get('xcorrMs') is not None]
    print('xcorr median', np.median(xs))
    tot = sum(r['closureTotal'] for r in out)
    okc = sum(r['closureOk'] for r in out)
    print(f'closures {okc}/{tot} = {okc / max(tot, 1):.1%}')
    print('false closure items', [(r['id'], len(r['falseClosures'])) for r in out if r['falseClosures']])
    print('jump violations', sum(r['jumpViolations'] for r in out), 'sil-only', sum(r['silOnlyJumps'] for r in out), [(r['id'], r['jumpViolations']) for r in out if r['jumpViolations']])
    print('max viseme step', max(r['maxVisemeStep'] for r in out), 'max jaw step', max(r['maxJawStep'] for r in out))
    print('hf jaw > 1.5%', [(r['id'], r['hfJaw']) for r in out if r['hfJaw'] > 0.015])
    print('stuck', [(r['id'], r['stuckOpenN'], r['stuckClosedN']) for r in out if r['stuckOpenN'] or r['stuckClosedN']])
    print('nonFinite', sum(r['nonFinite'] for r in out), 'errors', sum(len(r['errors']) for r in out))
    print('fatal', [r['id'] for r in out if r.get('fatal')])


main()
