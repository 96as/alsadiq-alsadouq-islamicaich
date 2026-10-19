# -*- coding: utf-8 -*-
"""Synthesise the wide lip-sync glitch test set (testset-wide.json) with ElevenLabs with-timestamps.

Reuses synth_testset.py (key lookup, voice settings, output formats). The key is read there and is
never printed. Output goes to the gitignored frontend/dev-audio/:
  eval-ar/<id>.<variant>.{f32,wav,align.json}   Arabic items (variant plain or diac, as the item says)
  eval-en/<id>.{f32,wav,align.json}             English items
  eval-ar/meta.json, eval-en/meta.json          sample rates

Usage (from frontend/):
  python scripts/lipsync-eval/synth_wide.py --dry-run
  python scripts/lipsync-eval/synth_wide.py
"""
import argparse
import base64
import io
import json
import sys
import time
import urllib.error
import urllib.request
import wave

import numpy as np

import synth_testset as S

HERE = S.HERE
OUT_AR = S.FRONTEND / 'dev-audio' / 'eval-ar'
OUT_EN = S.FRONTEND / 'dev-audio' / 'eval-en'
CAP = 5000


def call(key, voice, model, lang, text, fmt, speed):
    settings = dict(S.VOICE_SETTINGS)
    if speed:
        settings['speed'] = speed
    body = json.dumps({'text': text, 'model_id': model, 'language_code': lang, 'voice_settings': settings}, ensure_ascii=False).encode('utf-8')
    url = f'https://api.elevenlabs.io/v1/text-to-speech/{voice}/with-timestamps?output_format={fmt}'
    req = urllib.request.Request(url, data=body, headers={
        'xi-api-key': key, 'Content-Type': 'application/json', 'User-Agent': S.UA, 'Accept': 'application/json'})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--only', help='comma separated ids')
    args = ap.parse_args()
    ts = json.loads((HERE / 'testset-wide.json').read_text(encoding='utf-8'))
    jobs = []
    for it in ts['ar']:
        text = it['text'] if it['variant'] == 'diac' else S.plain_of(it['text'])
        jobs.append((it['id'], f"{it['id']}.{it['variant']}", 'ar', text, it.get('speed'), OUT_AR))
    for it in ts['en']:
        jobs.append((it['id'], it['id'], 'en', it['text'], it.get('speed'), OUT_EN))
    if args.only:
        want = set(args.only.split(','))
        jobs = [j for j in jobs if j[0] in want]
    todo = [j for j in jobs if not (j[5] / f'{j[1]}.align.json').exists()]
    total = sum(len(j[3]) for j in jobs)
    new = sum(len(j[3]) for j in todo)
    print(f'items {len(jobs)} ({total} characters), cached {len(jobs) - len(todo)}, to synthesise {len(todo)} ({new} characters, cap {CAP})')
    if args.dry_run:
        return 0
    if new > CAP:
        print('refusing: over the cap', file=sys.stderr)
        return 2
    key = S.find_key()
    if not key:
        print('no ElevenLabs key found', file=sys.stderr)
        return 3
    for d in (OUT_AR, OUT_EN):
        d.mkdir(parents=True, exist_ok=True)
    metas = {}
    for d in (OUT_AR, OUT_EN):
        p = d / 'meta.json'
        metas[d] = json.loads(p.read_text(encoding='utf-8')) if p.exists() else {}
    fmt_i = 0
    for n, (iid, name, lang, text, speed, out) in enumerate(todo):
        resp = None
        for attempt in range(3):
            fmt, sr = S.FORMATS[fmt_i]
            try:
                resp = call(key, ts['voice'], ts['model'], lang, text, fmt, speed)
                break
            except urllib.error.HTTPError as e:
                detail = e.read(300).decode('utf-8', 'replace').replace(key, '[redacted]')
                if e.code == 429 and attempt < 2:
                    print(f'{name}: 429, waiting 6 s')
                    time.sleep(6)
                    continue
                if e.code in (400, 402, 403) and fmt_i == 0 and 'output_format' in detail.lower():
                    fmt_i = 1
                    continue
                print(f'{name}: HTTP {e.code} {detail[:200]}', file=sys.stderr)
                return 4
            except Exception as e:  # noqa: BLE001
                print(f'{name}: {type(e).__name__}', file=sys.stderr)
                return 4
        if resp is None:
            return 4
        raw = base64.b64decode(resp['audio_base64'])
        pcm16 = np.frombuffer(raw, dtype='<i2')
        f32 = (pcm16.astype(np.float32) / 32768.0).astype('<f4')
        f32.tofile(out / f'{name}.f32')
        with wave.open(str(out / f'{name}.wav'), 'wb') as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(sr)
            w.writeframes(pcm16.tobytes())
        al = resp.get('alignment') or {}
        rec = {
            'text': text, 'sr': sr, 'duration': len(f32) / sr, 'speed': speed or S.VOICE_SETTINGS['speed'],
            'characters': al.get('characters', []),
            'starts': al.get('character_start_times_seconds', []),
            'ends': al.get('character_end_times_seconds', []),
        }
        (out / f'{name}.align.json').write_text(json.dumps(rec, ensure_ascii=False), encoding='utf-8')
        metas[out][name] = sr
        (out / 'meta.json').write_text(json.dumps(metas[out], indent=1), encoding='utf-8')
        print(f'[{n + 1}/{len(todo)}] {name}: {len(text)} chars, {len(f32) / sr:.2f} s, {len(rec["characters"])} aligned')
        time.sleep(0.6)
    return 0


if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.exit(main())
