#!/usr/bin/env python3
"""Download Husary (normal-pace murattal) ayah audio. Usage: python3 fetch_audio.py --out DIR 2:153 [...]

Saves SSSAAA.mp3 into DIR; existing files are skipped. Exits non-zero on any failure.
"""
import argparse
import re
import sys
import time
import urllib.request
from pathlib import Path

URL = 'https://everyayah.com/data/Husary_128kbps/{}.mp3'
UA = 'AlSadiq-curation/0.1'
DELAY = 0.7


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--out', required=True)
    p.add_argument('refs', nargs='+', metavar='SURAH:AYAH')
    args = p.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    failed = 0
    for ref in args.refs:
        m = re.fullmatch(r'(\d{1,3}):(\d{1,3})', ref)
        if not m or not 1 <= int(m[1]) <= 114 or int(m[2]) < 1:
            sys.exit(f'bad reference {ref!r}, expected SURAH:AYAH')
        name = f'{int(m[1]):03d}{int(m[2]):03d}'
        dest = out / f'{name}.mp3'
        if dest.exists():
            print(f'skip {dest.name}')
            continue
        try:
            req = urllib.request.Request(URL.format(name), headers={'User-Agent': UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                if r.status != 200 or 'audio' not in r.headers.get('Content-Type', ''):
                    raise OSError(f'HTTP {r.status} {r.headers.get("Content-Type")}')
                data = r.read()
            if not data:
                raise OSError('empty body')
            tmp = dest.with_suffix('.part')
            tmp.write_bytes(data)
            tmp.rename(dest)
            print(f'ok   {dest.name} ({len(data)} bytes)')
        except OSError as e:
            print(f'FAIL {ref}: {e}', file=sys.stderr)
            failed += 1
        time.sleep(DELAY)
    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()
