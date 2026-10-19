#!/usr/bin/env python3
"""Compare every verse item's Arabic with a pinned KFGQPC Hafs data file. CI-friendly.

  python3 verify_arabic.py --kfgqpc hafsData_v2-0.json --sha256 <HEX> [--items DIR] [--strict]
  python3 verify_arabic.py hafsData_v18.json [items_dir]          (positional form)

A verse passes when `arabic_text` equals the file's `aya_text` exactly, after removing
only the trailing NBSP + ayah number. If an item has `arabic_text_search` or
`text_edition` those must match the file too; with --strict they must be present, --sha256 is required
and `arabic_text` must not end in NBSP, a space, a digit or an ayah-number glyph (U+FC00-U+FDFF).
Prints one line per verse, then "N mismatching verse(s)". Exit 1 on any mismatch,
2 on a usage/pin error. No normalisation of any kind is applied before comparing.
"""
import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kfgqpc  # noqa: E402

DEFAULT_ITEMS = Path(__file__).resolve().parent.parent / 'items'
WASLA = 'ٱ'
# A stored arabic_text must never end in whitespace (incl. NBSP), a digit or an ayah-number glyph.
TRAILING_JUNK = re.compile(f'[\\s{kfgqpc._DIGITS}{kfgqpc.GLYPHS}]\\Z')


def first_diff(a, b):
    for i, (x, y) in enumerate(zip(a, b)):
        if x != y:
            return i
    return min(len(a), len(b))


def iter_verses(items_dir):
    for f in sorted(Path(items_dir).glob('*.json')):
        for it in json.loads(f.read_text(encoding='utf-8')):
            if it.get('type') == 'verse':
                yield f.name, it


def check_item(item, kf, strict=False):
    """Return a list of problems (empty = OK) for one verse item."""
    key = (item['surah'], item['ayah'])
    if key not in kf.text:
        return ['not in the KFGQPC file']
    want, have = kf.get(*key), item.get('arabic_text', '')
    problems = []
    if have != want:
        i = first_diff(have, want)
        nfc = unicodedata.normalize('NFC', have) == unicodedata.normalize('NFC', want)
        problems.append(f'arabic_text differs at char {i}{" (NFC-equal)" if nfc else ""}; '
                        f'wasla in file={WASLA in want} in item={WASLA in have}')
    if strict and TRAILING_JUNK.search(have):
        problems.append(f'arabic_text ends with NBSP/space/digit/ayah-number glyph (U+{ord(have[-1]):04X})')
    if 'arabic_text_search' in item:
        if kf.get_search(*key) != item['arabic_text_search']:
            problems.append('arabic_text_search differs from aya_text_emlaey')
    elif strict and kf.get_search(*key):
        problems.append('arabic_text_search missing')
    if 'text_edition' in item:
        if item['text_edition'] != kf.edition():
            problems.append(f'text_edition {item["text_edition"]!r} != {kf.edition()!r}')
    elif strict:
        problems.append('text_edition missing')
    return problems


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    kfgqpc.add_common_args(p)
    p.add_argument('--items', help=f'items directory (default: {DEFAULT_ITEMS})')
    p.add_argument('--strict', action='store_true', help='also require arabic_text_search and text_edition')
    p.add_argument('positional', nargs='*', metavar='FILE [ITEMS_DIR]',
                   help='legacy form: KFGQPC file, then optional items dir')
    args = p.parse_args(argv)
    if args.positional and not args.kfgqpc:
        args.kfgqpc = args.positional[0]
        if len(args.positional) > 1 and not args.items:
            args.items = args.positional[1]
    if not args.kfgqpc:
        p.error('give --kfgqpc PATH')
    if args.strict and not args.sha256:
        print('error: --strict (CI mode) requires --sha256', file=sys.stderr)
        return 2
    try:
        kf = kfgqpc.Kfgqpc(args.kfgqpc, args.sha256, args.release)
    except kfgqpc.KfgqpcError as e:
        print(f'error: {e}', file=sys.stderr)
        return 2
    items_dir = Path(args.items) if args.items else DEFAULT_ITEMS
    if not items_dir.is_dir():
        print(f'error: items directory not found: {items_dir}', file=sys.stderr)
        return 2
    print(f'{kf.edition()} pinned={kf.pinned} code points: {kf.encoding_report()}')
    bad = total = 0
    for fname, it in iter_verses(items_dir):
        total += 1
        problems = check_item(it, kf, args.strict)
        ref = f'{it["surah"]}:{it["ayah"]}'
        if problems:
            bad += 1
            print(f'{ref} MISMATCH ({fname}): ' + '; '.join(problems))
        else:
            print(f'{ref} OK')
    print(f'{total} verse(s) checked')
    print(f'{bad} mismatching verse(s)')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
