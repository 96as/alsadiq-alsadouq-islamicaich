#!/usr/bin/env python3
"""Fetch verses as knowledge-bank items.

Usage: python3 fetch_verse.py [options] 2:153 [2:45 ...]

Arabic text, one of two sources:
  * --kfgqpc PATH --sha256 HEX (preferred): the King Fahd Complex (KFGQPC) Hafs data
    file, pinned by sha256. `arabic_text` is `aya_text` byte-for-byte except that the
    trailing NBSP + ayah-number glyphs are removed; `arabic_text_search` is the file's
    `aya_text_emlaey`; `text_edition` records release and hash.
  * default: Quranpedia mushaf id 2 (KFGQPC Uthmani, api.quranpedia.net/v1/mushafs/2/{s}/{a}).
    Mushaf id 1 is NOT the King Fahd text (it serves an imlaei-style script, see
    docs/hackathon/research/r4-quran-text-audio.md section 2.8); do not use it. Only the BOM,
    outer whitespace and the trailing ayah number are removed. No search text is produced.
No punctuation is ever added to any field.

English is the Saheeh International translation (Quranpedia id 1947); only markup is
removed: the leading "(N) " prefix, the `[123]` footnote markers and the trailing
footnotes block; the words are untouched.
`--audio-source everyayah|none` chooses whether `audio_url` (everyayah Husary normal-pace murattal,
provenance only; the decision on the audio source is pending) is emitted.
Any API failure aborts with a non-zero exit; there is no fallback text.
"""
import argparse
import datetime
import hashlib
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kfgqpc  # noqa: E402

API = 'https://api.quranpedia.net/v1'
MUSHAF_ID = 2  # KFGQPC Uthmani (Quranpedia "Hafs text edition"); id 1 is the wrong script
PAGE = 'https://quranpedia.net/ayahs/{s}/{a}'  # 301 -> canonical /tafsir/<surah-slug>/<ayah>
AUDIO = 'https://everyayah.com/data/Husary_128kbps/{s:03d}{a:03d}.mp3'
UA = 'AlSadiq-curation/0.1'
DELAY = 2.0  # limit is 120/min; leaves room for 3 parallel curators
CACHE = Path(__file__).resolve().parent / '.cache'
_last = [0.0]


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def fail(msg):
    sys.exit(f'fetch_verse: {msg}')


def cached(url, method='GET'):
    """Return body text (GET) or Location header (HEAD, redirects not followed)."""
    CACHE.mkdir(exist_ok=True)
    f = CACHE / (method + '_' + hashlib.sha1(url.encode()).hexdigest() + '.txt')
    if f.exists():
        return f.read_text(encoding='utf-8')
    wait = DELAY - (time.monotonic() - _last[0])
    if wait > 0:
        time.sleep(wait)
    req = urllib.request.Request(url, method=method, headers={'User-Agent': UA})
    opener = urllib.request.build_opener(NoRedirect)
    try:
        resp = opener.open(req, timeout=30)
        code, headers, body = resp.status, resp.headers, resp.read()
    except urllib.error.HTTPError as e:
        code, headers, body = e.code, e.headers, b''
    except (urllib.error.URLError, OSError) as e:
        fail(f'{url}: {e}')
    finally:
        _last[0] = time.monotonic()
    if method == 'HEAD':
        out = headers.get('Location') or (url if code == 200 else None)
        if code not in (200, 301, 302) or not out:
            fail(f'{url}: HTTP {code}')
    else:
        if code != 200:
            fail(f'{url}: HTTP {code}')
        out = body.decode('utf-8')
    f.write_text(out, encoding='utf-8')
    return out


def checked(url, ok):
    """Fetch JSON from url; if ok(data) is false, drop the cached copy and abort."""
    data = json.loads(cached(url))
    if not (isinstance(data, dict) and ok(data)):
        (CACHE / ('GET_' + hashlib.sha1(url.encode()).hexdigest() + '.txt')).unlink(missing_ok=True)
        fail(f'{url}: unexpected response (does the ayah exist?)')
    return data


def english(t):
    """Saheeh text minus markup only: the "(N) " prefix, footnote markers [123],
    and the trailing <br /><div class="foot-notes">...</div>. Words are untouched;
    no punctuation is added or removed."""
    t = re.split(r'<br\s*/?>|<div class="foot-notes">', t)[0]
    t = re.sub(r'\[\d+\]', '', t)
    return re.sub(r'^\(\d+\)\s*', '', t.strip())


def arabic_fields(s, a, kf, edition_date):
    """arabic_text (+ arabic_text_search) and text_edition, from the pinned file or Quranpedia."""
    if kf:
        out = {'arabic_text': kf.get(s, a)}
        search = kf.get_search(s, a)
        if search:
            out['arabic_text_search'] = search
        out['text_edition'] = kf.edition()
        return out
    ar = checked(f'{API}/mushafs/{MUSHAF_ID}/{s}/{a}', lambda d: (
        str(d.get('surah')) == str(s) and d.get('number') == a and d.get('text', '').strip()))
    text = kfgqpc.strip_ayah_number(ar['text'].lstrip('﻿').strip())
    return {'arabic_text': text, 'text_edition': f'Quranpedia mushaf {MUSHAF_ID} {edition_date}'}


def verse(s, a, kf=None, audio_source='everyayah', edition_date=None):
    edition_date = edition_date or datetime.date.today().isoformat()
    fields = arabic_fields(s, a, kf, edition_date)
    tr = checked(f'{API}/translation/1947/{s}/{a}', lambda d: (
        d.get('ayah_number') == a and d.get('translation_text', '').strip()))
    item = {'type': 'verse', 'surah': s, 'ayah': a, 'arabic_text': fields['arabic_text']}
    if 'arabic_text_search' in fields:
        item['arabic_text_search'] = fields['arabic_text_search']
    item['text_edition'] = fields['text_edition']
    item.update({
        'english_text': english(tr['translation_text']),
        'translation_name': 'Saheeh International',
        'source_site': 'quranpedia.net',
        'source_url': cached(PAGE.format(s=s, a=a), 'HEAD'),
    })
    if audio_source == 'everyayah':
        item['audio_url'] = AUDIO.format(s=s, a=a)
    item['verification_status'] = 'seeded'
    return item


def main(argv):
    p = argparse.ArgumentParser(description='Fetch verses as knowledge-bank items.')
    kfgqpc.add_common_args(p)
    p.add_argument('--audio-source', choices=('everyayah', 'none'), default='everyayah',
                   help='everyayah (default): emit the everyayah audio_url; none: omit audio_url')
    p.add_argument('--edition-date', help='date for text_edition in Quranpedia mode (default: today)')
    p.add_argument('refs', nargs='+', metavar='SURAH:AYAH')
    args = p.parse_args(argv)
    if not args.kfgqpc and (args.sha256 or args.release):
        fail('--sha256/--release only make sense with --kfgqpc')
    kf = kfgqpc.load_from_args(args, require_pin=True) if args.kfgqpc else None
    out = []
    for ref in args.refs:
        m = re.fullmatch(r'(\d{1,3}):(\d{1,3})', ref)
        if not m or not 1 <= int(m[1]) <= 114 or int(m[2]) < 1:
            fail(f'bad reference {ref!r}, expected SURAH:AYAH')
        try:
            out.append(verse(int(m[1]), int(m[2]), kf, args.audio_source, args.edition_date))
        except kfgqpc.KfgqpcError as e:
            fail(str(e))
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main(sys.argv[1:])
