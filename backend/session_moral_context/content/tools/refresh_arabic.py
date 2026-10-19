#!/usr/bin/env python3
"""One-shot refresh of the verse text in items/*.json from a pinned KFGQPC Hafs file.

  python3 refresh_arabic.py --kfgqpc hafsData_v2-0.json --sha256 <HEX> --dry-run
  python3 refresh_arabic.py --kfgqpc hafsData_v2-0.json --sha256 <HEX>
  python3 refresh_arabic.py ... --fix-english quranenc_english_saheeh.json

For every item of type "verse" (nothing else is touched):
  * `arabic_text`        <- the file's `aya_text` minus the trailing NBSP + ayah number, byte for byte;
  * `arabic_text_search` <- the file's `aya_text_emlaey`;
  * `text_edition`       <- "KFGQPC Hafs <release> sha256:<first12>".
The new keys sit directly after `arabic_text`. All other keys keep their order and value;
`verification_status`, `reviewed_by` and `reviewed_at` are NOT changed on purpose: the review
ledger hash goes stale, so `mark_reviewed.py --check` lists the verses until a human re-reviews.
Files are rewritten in the repo style (indent 2, ensure_ascii=False, trailing newline) and
only when something changed. Nothing is written if any verse is missing from the data file.

--fix-english SOURCE_JSON (optional): also re-derive `english_text` from a QuranEnc / Quranpedia
dump so it equals the source wording (markup removed, nothing added). Accepted shapes:
  {"49": [{"chapter": 49, "verse": 12, "text": "..."}]}      (risan/quran-json quranenc dump)
  {"result": [{"sura": "49", "aya": "12", "translation": "..."}]}   (QuranEnc API; a list of those also works)
  {"49:12": "..."}                                            (plain map)
Only items whose translation_name is "Saheeh International" are touched.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kfgqpc  # noqa: E402
from fetch_verse import english  # noqa: E402

DEFAULT_ITEMS = Path(__file__).resolve().parent.parent / 'items'
NEW_KEYS = ('arabic_text_search', 'text_edition')


def load_translations(path):
    """Return {(surah, ayah): cleaned english} from one of the accepted JSON shapes."""
    raw = json.loads(Path(path).read_text(encoding='utf-8-sig'))
    out = {}

    def add(s, a, t):
        out[(int(s), int(a))] = english(t)

    chunks = raw if isinstance(raw, list) else [raw]
    for ch in chunks:
        if 'result' in ch and isinstance(ch['result'], list):
            for r in ch['result']:
                add(r['sura'], r['aya'], r['translation'])
            continue
        for k, v in ch.items():
            if isinstance(v, list):  # {"49": [ {chapter, verse, text} ]}
                for r in v:
                    add(r.get('chapter', k), r['verse'], r['text'])
            elif isinstance(v, str) and ':' in k:  # {"49:12": "..."}
                s, a = k.split(':')
                add(s, a, v)
    if not out:
        raise ValueError(f'{path}: no translations recognised')
    return out


def refresh_item(item, kf, translations=None):
    """Return (new_item, changes) for a verse item; changes is a list of field names."""
    key = (item['surah'], item['ayah'])
    new = {
        'arabic_text': kf.get(*key),
        'arabic_text_search': kf.get_search(*key),
        'text_edition': kf.edition(),
    }
    if new['arabic_text_search'] is None:
        del new['arabic_text_search']
    out, changes = {}, []
    for k, v in item.items():
        if k in NEW_KEYS:
            continue  # re-inserted after arabic_text
        if k == 'arabic_text':
            for nk, nv in new.items():
                out[nk] = nv
                if item.get(nk) != nv:
                    changes.append(nk)
            continue
        out[k] = v
    if 'arabic_text_search' in item and 'arabic_text_search' not in new:
        # The pinned file has no emlaey text for this ayah: drop the stale field so the
        # item matches the file, and say so.
        changes.append('arabic_text_search')
        print(f'warning: {key[0]}:{key[1]}: no aya_text_emlaey in the data file; '
              'dropping the item\'s arabic_text_search', file=sys.stderr)
    if 'arabic_text' not in item:
        raise ValueError(f'{key}: verse item has no arabic_text key to anchor the new fields')
    if translations is not None and item.get('translation_name') == 'Saheeh International':
        want = translations.get(key)
        if want is not None and want != item.get('english_text'):
            out['english_text'] = want
            changes.append('english_text')
    return out, changes


def run(items_dir, kf, dry_run=False, translations=None, out=None):
    """Process every items file. Returns (files_changed, verses_changed, per-field counts)."""
    out = out or sys.stdout
    plan = []  # (path, new_list)
    verses = changed_verses = 0
    counts = {}
    for f in sorted(Path(items_dir).glob('*.json')):
        items = json.loads(f.read_text(encoding='utf-8'))
        new_items, dirty = [], False
        for it in items:
            if it.get('type') != 'verse':
                new_items.append(it)
                continue
            verses += 1
            new, changes = refresh_item(it, kf, translations)
            new_items.append(new)
            if changes:
                dirty = True
                changed_verses += 1
                for c in changes:
                    counts[c] = counts.get(c, 0) + 1
                print(f'{f.name} {it["surah"]}:{it["ayah"]}: ' + ', '.join(changes), file=out)
                if 'english_text' in changes:
                    print(f'    english_text: {it["english_text"]!r} -> {new["english_text"]!r}', file=out)
            elif list(new) != list(it):  # key order only
                dirty = True
        if dirty:
            plan.append((f, new_items))
    if not dry_run:
        for f, new_items in plan:
            f.write_text(json.dumps(new_items, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'{"would change" if dry_run else "changed"} {changed_verses} of {verses} verse(s) '
          f'in {len(plan)} file(s); field counts: {counts or "none"}', file=out)
    return len(plan), changed_verses, counts


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    kfgqpc.add_common_args(p)
    p.add_argument('--items', help=f'items directory (default: {DEFAULT_ITEMS})')
    p.add_argument('--dry-run', action='store_true', help='print what would change, write nothing')
    p.add_argument('--fix-english', metavar='SOURCE_JSON',
                   help='also set english_text from a QuranEnc/Quranpedia dump (see docstring)')
    args = p.parse_args(argv)
    if not args.kfgqpc:
        p.error('--kfgqpc is required')
    kf = kfgqpc.load_from_args(args, require_pin=True)
    items_dir = Path(args.items) if args.items else DEFAULT_ITEMS
    if not items_dir.is_dir():
        sys.exit(f'error: items directory not found: {items_dir}')
    translations = None
    if args.fix_english:
        try:
            translations = load_translations(args.fix_english)
        except (OSError, ValueError, KeyError) as e:
            sys.exit(f'error: --fix-english: {e}')
    try:
        run(items_dir, kf, args.dry_run, translations)
    except (kfgqpc.KfgqpcError, ValueError) as e:
        sys.exit(f'error: {e} (nothing written)')


if __name__ == '__main__':
    main()
