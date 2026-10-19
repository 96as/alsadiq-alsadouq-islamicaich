#!/usr/bin/env python3
"""Record human review of knowledge-bank items.

Usage:
    python3 mark_reviewed.py --by "Name" [--at YYYY-MM-DD] REF ...
    python3 mark_reviewed.py --check          (alias: --list-stale)

REF is a value slug (every item whose `values` has it), a file name (prayer.json)
or a natural key (verse:2:153). Marking writes the CURRENT hash of the item to
content/reviewed.json AND sets verification_status/reviewed_by/reviewed_at in the
item file. Any later content edit makes the hash stale: --check then exits 1 and
seed_content downgrades the item to `seeded`.
"""
import argparse
import datetime
import importlib.util
import json
from pathlib import Path

CONTENT = Path(__file__).resolve().parents[1]
# Load the shared helpers by path so Django is not needed.
_spec = importlib.util.spec_from_file_location(
    'review', CONTENT.parent / 'utils' / 'review.py')
review = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(review)
LEDGER = CONTENT / 'reviewed.json'


def load_files():
    """{file path: list of item dicts}, in filename order."""
    return {f: json.loads(f.read_text(encoding='utf-8'))
            for f in sorted((CONTENT / 'items').glob('*.json'))}


def with_review(item, by, at):
    """Copy of item with the review fields set, other key order kept."""
    out = {}
    for k, v in item.items():
        if k in review.STATUS_KEYS:
            continue
        out[k] = v
        if k == 'verification_status':
            out.update(verification_status='reviewed', reviewed_by=by, reviewed_at=at)
    if 'verification_status' not in out:
        out.update(verification_status='reviewed', reviewed_by=by, reviewed_at=at)
    return out


def check(ledger, files):
    """Print problems; return True if every review is valid."""
    current = {review.natural_key(i)[1]: i for items in files.values() for i in items}
    bad = []
    for k, i in sorted(current.items()):
        e = ledger.get(k)
        if i.get('verification_status') == 'reviewed' and (
                not e or e['sha256'] != review.item_hash(i)):
            bad.append(f"{k} - file says reviewed but "
                       f"{'content changed since review' if e else 'no ledger entry'}")
    for k, e in sorted(ledger.items()):
        if k not in current:
            bad.append(f'{k} - stale ledger entry, no such item')
        elif e['sha256'] != review.item_hash(current[k]):
            bad.append(f'{k} - stale ledger entry, content changed')
    print('\n'.join(bad) if bad else 'all reviews valid')
    return not bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--by')
    ap.add_argument('--at', default=datetime.date.today().isoformat())
    ap.add_argument('--check', '--list-stale', dest='check', action='store_true')
    ap.add_argument('refs', nargs='*')
    a = ap.parse_args()
    ledger = {e['key']: e for e in json.loads(LEDGER.read_text(encoding='utf-8'))}
    files = load_files()

    if a.check:
        raise SystemExit(0 if check(ledger, files) else 1)
    if not a.by or not a.refs:
        ap.error('--by and at least one REF are required')
    datetime.date.fromisoformat(a.at)

    hit = set()
    for ref in a.refs:
        n = 0
        for f, items in files.items():
            for idx, i in enumerate(items):
                k = review.natural_key(i)[1]
                if ref in (f.name, k) or ref in i.get('values', []):
                    items[idx] = with_review(i, a.by, a.at)
                    ledger[k] = {'key': k, 'sha256': review.item_hash(i), 'by': a.by, 'at': a.at}
                    hit.add(f)
                    n += 1
                    print(f'marked {k} ({ref})')
        if not n:
            ap.error(f'no items match {ref!r}')
    for f in hit:
        f.write_text(json.dumps(files[f], ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    LEDGER.write_text(
        json.dumps([ledger[k] for k in sorted(ledger)], ensure_ascii=False, indent=2) + '\n',
        encoding='utf-8')


if __name__ == '__main__':
    main()
