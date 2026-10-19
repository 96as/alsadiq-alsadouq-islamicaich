#!/usr/bin/env python3
"""Cut per-ayah mp3 clips out of an mp3quran.net surah file using its ayat_timing data.

  python3 cut_ayah_clips.py --read 1 --server https://cdn.mp3quran.net/audio/ibrahim-akhdar/r1/ \\
      --out ../../static/quran 2:153 49:12 ...
Offline mode (no network): --timing-json t.json --surah-mp3 file.mp3, with refs from ONE surah.
Timing JSON (mp3quran v3): list of {"ayah": int, "start_time": ms, "end_time": ms, ...};
entries with ayah < 1 (intro) are ignored. Needs ffmpeg and ffprobe on PATH.
Writes SSSAAA.mp3 (same names as the everyayah clips). Each clip is re-encoded
(128 kbps, 44.1 kHz) with 50 ms of lead and 150 ms of tail; stream copy drifts by an mp3 frame.
The mp3quran timing is a start/end marker, so a clip can contain a breath of the neighbour:
listen to a few before shipping. Audio source and licence are pending a human decision.
Downloads are cached (one request per surah file); requests are paced. Not for bulk crawling.
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

UA = 'AlSadiq-curation/0.1'
TIMING = 'https://www.mp3quran.net/api/v3/ayat_timing?surah={s}&read={r}'
PAD_BEFORE, PAD_AFTER = 0.05, 0.15  # seconds of air around an ayah
DELAY = 2.0
_last = [0.0]


def get(url):
    wait = DELAY - (time.monotonic() - _last[0])
    if wait > 0:
        time.sleep(wait)
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.read()
    finally:
        _last[0] = time.monotonic()


def parse_refs(refs):
    by_surah = {}
    for ref in refs:
        m = re.fullmatch(r'(\d{1,3}):(\d{1,3})', ref)
        if not m or not 1 <= int(m[1]) <= 114 or int(m[2]) < 1:
            raise ValueError(f'bad reference {ref!r}, expected SURAH:AYAH')
        by_surah.setdefault(int(m[1]), []).append(int(m[2]))
    return by_surah


def timing_map(timing):
    """{ayah: (start_s, end_s)} from the mp3quran list; ayah < 1 entries are dropped."""
    return {int(x['ayah']): (x['start_time'] / 1000, x['end_time'] / 1000)
            for x in timing if int(x['ayah']) >= 1}


def clip_window(start, end):
    return max(0.0, start - PAD_BEFORE), end + PAD_AFTER


def cut(src, dest, start, end):
    """Re-encode src[start:end] to dest. Returns the measured duration in seconds."""
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{start:.3f}', '-to', f'{end:.3f}', '-i', str(src),
                    '-vn', '-c:a', 'libmp3lame', '-b:a', '128k', '-ar', '44100', '-map_metadata', '-1',
                    str(dest)], check=True)
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(dest)],
                       capture_output=True, text=True, check=True)
    return float(r.stdout)


def cut_surah(surah, ayat, timing, src, out):
    """Cut the listed ayat of one surah file. Returns [(filename, duration, expected)]."""
    t = timing_map(timing)
    res = []
    for n in ayat:
        if n not in t:
            raise ValueError(f'no timing for {surah}:{n}')
        start, end = clip_window(*t[n])
        dest = Path(out) / f'{surah:03d}{n:03d}.mp3'
        res.append((dest.name, cut(src, dest, start, end), end - start))
    return res


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--read', type=int, help='mp3quran moshaf id (the "read" parameter of ayat_timing)')
    p.add_argument('--server', help='moshaf server folder URL (the "server" field of the reciters API), e.g. https://cdn.mp3quran.net/audio/<reciter>/rN/ -> <server>/NNN.mp3')
    p.add_argument('--out', required=True)
    p.add_argument('--cache', default=str(Path(__file__).resolve().parent / '.cache' / 'mp3quran'))
    p.add_argument('--timing-json', help='offline: local timing JSON for the (single) surah')
    p.add_argument('--surah-mp3', help='offline: local surah mp3 for the (single) surah')
    p.add_argument('refs', nargs='+', metavar='SURAH:AYAH')
    a = p.parse_args(argv)
    if not (shutil.which('ffmpeg') and shutil.which('ffprobe')):
        sys.exit('error: ffmpeg and ffprobe must be on PATH')
    try:
        by_surah = parse_refs(a.refs)
    except ValueError as e:
        sys.exit(f'error: {e}')
    offline = bool(a.timing_json or a.surah_mp3)
    if offline and not (a.timing_json and a.surah_mp3 and len(by_surah) == 1):
        sys.exit('error: offline mode needs both --timing-json and --surah-mp3 and refs from one surah')
    if not offline and not (a.read and a.server):
        sys.exit('error: online mode needs --read and --server')
    out, cache = Path(a.out), Path(a.cache)
    out.mkdir(parents=True, exist_ok=True)
    for s, ayat in sorted(by_surah.items()):
        if offline:
            timing = json.loads(Path(a.timing_json).read_text(encoding='utf-8'))
            src = Path(a.surah_mp3)
        else:
            cache.mkdir(parents=True, exist_ok=True)
            tf = cache / f'timing_{a.read}_{s:03d}.json'
            if not tf.exists():
                tf.write_bytes(get(TIMING.format(s=s, r=a.read)))
            timing = json.loads(tf.read_text(encoding='utf-8'))
            src = cache / f'{a.read}_{s:03d}.mp3'
            if not src.exists():
                src.write_bytes(get(f'{a.server.rstrip("/")}/{s:03d}.mp3'))
        try:
            for name, dur, expected in cut_surah(s, ayat, timing, src, out):
                print(f'ok {name} {dur:.2f}s (expected {expected:.2f}s)')
        except ValueError as e:
            sys.exit(f'error: {e}')


if __name__ == '__main__':
    main()
