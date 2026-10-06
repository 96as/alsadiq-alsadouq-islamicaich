# -*- coding: utf-8 -*-
"""Synthesise the Arabic lip-sync test set with ElevenLabs (with-timestamps) and cache it.

For every line of testset-ar.json two variants are made:
  diac   the voweled text (its alignment labels every short vowel, shadda and sukun)
  plain  the same text with the marks deleted (the live condition: the LLM writes no marks)

Output goes to frontend/dev-audio/eval-ar/ (gitignored, never commit it):
  <id>.<variant>.f32          raw little-endian float32 mono samples
  <id>.<variant>.wav          16-bit PCM copy for listening and for the lab
  <id>.<variant>.align.json   {characters, starts, ends} in seconds, as sent (alignment, not normalized)
  meta.json                   {"<id>.<variant>": sampleRate}

Usage (from frontend/):
  python scripts/lipsync-eval/synth_testset.py --dry-run
  python scripts/lipsync-eval/synth_testset.py

Standard library and numpy only. The API key comes from ELEVEN_API_KEY, else the worktree .env,
else Alsadiq-wt/eleven-key.txt. It is read here and never printed.
"""
import argparse
import base64
import io
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
import wave
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
FRONTEND = HERE.parent.parent
REPO = FRONTEND.parent
OUT = FRONTEND / 'dev-audio' / 'eval-ar'
CHAR_CAP = 5000
MARKS = re.compile('[ً-ْٰ]')
# The production voice settings (backend/conversation/agent/tts_factory.py defaults).
VOICE_SETTINGS = {
    'stability': 0.65,
    'similarity_boost': 0.75,
    'style': 0.0,
    'use_speaker_boost': True,
    'speed': 0.92,
}
FORMATS = (('pcm_22050', 22050), ('pcm_24000', 24000))
UA = 'Mozilla/5.0 (compatible; alsadiq-lipsync-eval/1.0)'


def find_key():
    key = os.environ.get('ELEVEN_API_KEY', '').strip()
    if key:
        return key
    for p in (REPO / '.env', REPO / 'backend' / '.env', FRONTEND / '.env'):
        if p.exists():
            for line in p.read_text(encoding='utf-8', errors='replace').splitlines():
                if line.startswith('ELEVEN_API_KEY='):
                    v = line.split('=', 1)[1].strip().strip('"').strip("'")
                    if v and not v.lower().startswith(('your-', '<')):
                        return v
    kf = REPO.parent / 'eleven-key.txt'
    if kf.exists():
        return kf.read_text(encoding='utf-8').strip()
    return ''


def plain_of(text):
    return MARKS.sub('', text)


def call(key, voice, model, lang, text, fmt):
    body = json.dumps({
        'text': text,
        'model_id': model,
        'language_code': lang,
        'voice_settings': VOICE_SETTINGS,
    }, ensure_ascii=False).encode('utf-8')
    url = f'https://api.elevenlabs.io/v1/text-to-speech/{voice}/with-timestamps?output_format={fmt}'
    req = urllib.request.Request(url, data=body, headers={
        'xi-api-key': key, 'Content-Type': 'application/json', 'User-Agent': UA, 'Accept': 'application/json'})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true', help='print the character count and stop')
    ap.add_argument('--only', help='comma separated line ids')
    args = ap.parse_args()

    ts = json.loads((HERE / 'testset-ar.json').read_text(encoding='utf-8'))
    lines = ts['lines']
    if args.only:
        want = set(args.only.split(','))
        lines = [l for l in lines if l['id'] in want]
    jobs = []
    for l in lines:
        for variant, text in (('diac', l['text']), ('plain', plain_of(l['text']))):
            jobs.append((l['id'], variant, text))
    todo = [j for j in jobs if not (OUT / f'{j[0]}.{j[1]}.align.json').exists()]
    new_chars = sum(len(j[2]) for j in todo)
    total_chars = sum(len(j[2]) for j in jobs)
    print(f'lines {len(lines)}, jobs {len(jobs)} ({total_chars} characters in total)')
    print(f'cached {len(jobs) - len(todo)}, to synthesise {len(todo)} ({new_chars} new characters, cap {CHAR_CAP})')
    if args.dry_run:
        return 0
    if new_chars > CHAR_CAP:
        print('refusing: this run would send more than the cap', file=sys.stderr)
        return 2
    if not todo:
        return 0
    key = find_key()
    if not key:
        print('no ElevenLabs key found (ELEVEN_API_KEY, .env or eleven-key.txt)', file=sys.stderr)
        return 3
    OUT.mkdir(parents=True, exist_ok=True)
    meta_path = OUT / 'meta.json'
    meta = json.loads(meta_path.read_text(encoding='utf-8')) if meta_path.exists() else {}
    fmt_i = 0
    for n, (lid, variant, text) in enumerate(todo):
        name = f'{lid}.{variant}'
        resp = None
        for attempt in range(2):
            fmt, sr = FORMATS[fmt_i]
            try:
                resp = call(key, ts['voice'], ts['model'], ts['language_code'], text, fmt)
                break
            except urllib.error.HTTPError as e:
                detail = e.read(300).decode('utf-8', 'replace')
                detail = detail.replace(key, '[redacted]')
                if e.code == 429 and attempt == 0:
                    print(f'{name}: 429, waiting 5 s')
                    time.sleep(5)
                    continue
                if e.code in (400, 402, 403) and fmt_i == 0 and 'output_format' in detail.lower():
                    fmt_i = 1
                    print(f'{name}: {fmt} refused, trying {FORMATS[1][0]}')
                    continue
                print(f'{name}: HTTP {e.code} {detail[:200]}', file=sys.stderr)
                return 4
            except Exception as e:  # noqa: BLE001
                print(f'{name}: {type(e).__name__}', file=sys.stderr)
                return 4
        if resp is None:
            print(f'{name}: no response', file=sys.stderr)
            return 4
        raw = base64.b64decode(resp['audio_base64'])
        pcm16 = np.frombuffer(raw, dtype='<i2')
        f32 = (pcm16.astype(np.float32) / 32768.0).astype('<f4')
        f32.tofile(OUT / f'{name}.f32')
        with wave.open(str(OUT / f'{name}.wav'), 'wb') as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(sr)
            w.writeframes(pcm16.tobytes())
        al = resp.get('alignment') or {}
        out = {
            'text': text,
            'sr': sr,
            'duration': len(f32) / sr,
            'characters': al.get('characters', []),
            'starts': al.get('character_start_times_seconds', []),
            'ends': al.get('character_end_times_seconds', []),
        }
        (OUT / f'{name}.align.json').write_text(json.dumps(out, ensure_ascii=False), encoding='utf-8')
        meta[name] = sr
        meta_path.write_text(json.dumps(meta, indent=1), encoding='utf-8')
        print(f'[{n + 1}/{len(todo)}] {name}: {len(text)} chars, {len(f32) / sr:.2f} s, {len(out["characters"])} aligned chars')
        time.sleep(1.0)
    return 0


if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.exit(main())
