"""Deterministic DEV / HELD-OUT split of the eval cases (hk/agent-quality).

    python conversation/eval/make_split.py            # writes split.json next to cases.yaml
    python conversation/eval/make_split.py --check    # fails if split.json is not what this script produces

Rules
  * The unit is the case FAMILY: a case id with its trailing ``-en`` / ``-ar`` removed, so the English and
    the Arabic version of one question always land on the same side. A held-out family is never tuned on.
  * Cases the lead already tagged ``heldout`` (phrasings written after the reviewer probes) are HELD-OUT here
    too. They are single cases (``heldout-NN-ar|en``), so each is its own family.
  * Cases tagged ``dev`` (written later, for the classifier work) are always DEV and are left out of the draw,
    so they never change which existing family is held out.
  * On top of those, whole families are drawn with a fixed seed until each category holds about 30 percent
    of its cases, preferring the language that is behind its own 30 percent. Every category with two or more
    cases has at least one case on each side.
  * No case text is read or copied into split.json: it holds ids, categories and languages only.

Nobody changes cases.yaml to move a case between sides. If cases.yaml changes (a case added or removed),
re-run this script and say so in the commit; new families are drawn the same way.
"""
from __future__ import annotations

import argparse
import json
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
SEED = 20261005
HELD_FRACTION = 0.30


def family(case_id: str) -> str:
    return re.sub(r'-(en|ar)$', '', case_id)


def build(cases: list[dict], seed: int = SEED, fraction: float = HELD_FRACTION) -> dict:
    fams: dict[str, list[dict]] = defaultdict(list)
    for c in cases:
        fams[family(c['id'])].append(c)
    # families the lead tagged ``dev`` (written after the split, for the classifier work) are always dev and
    # stay out of the draw, so adding them never moves an existing family to the other side
    forced_dev = {fid for fid, members in fams.items() if any('dev' in (m.get('tags') or []) for m in members)}
    by_cat: dict[str, list[str]] = defaultdict(list)
    for fid, members in fams.items():
        if fid not in forced_dev:
            by_cat[members[0]['category']].append(fid)

    held: set[str] = set()
    for fid, members in fams.items():
        if fid in forced_dev:
            assert not any('heldout' in (m.get('tags') or []) for m in members), f'{fid} is tagged dev and heldout'
        elif any('heldout' in (m.get('tags') or []) for m in members):
            held.add(fid)

    rng = random.Random(seed)
    for cat in sorted(by_cat):
        fids = sorted(by_cat[cat])
        n_cat = sum(len(fams[f]) for f in fids)
        lang_total = Counter(m['lang'] for f in fids for m in fams[f])
        target = round(fraction * n_cat)
        if n_cat >= 2:
            target = max(1, min(target, n_cat - 1))
        # draw order is seeded and independent of the other categories
        order = fids[:]
        rng.shuffle(order)
        tie = {f: i for i, f in enumerate(order)}

        def held_count():
            return sum(len(fams[f]) for f in fids if f in held)

        def lang_held():
            return Counter(m['lang'] for f in fids if f in held for m in fams[f])

        while held_count() < target:
            cur = held_count()
            lh = lang_held()
            deficit = {lg: fraction * lang_total[lg] - lh[lg] for lg in lang_total}
            best = None
            for f in order:
                if f in held:
                    continue
                size = len(fams[f])
                gain = sum(min(max(deficit[lg], 0), cnt) for lg, cnt in Counter(m['lang'] for m in fams[f]).items())
                score = (abs(cur + size - target), -gain, tie[f])
                if best is None or score < best[0]:
                    best = (score, f)
            if best is None or best[0][0] >= abs(cur - target):
                break
            held.add(best[1])
        # a category with 2+ cases keeps at least one case on each side
        if n_cat >= 2 and held_count() == n_cat:
            raise SystemExit(f'category {cat}: every case is held out; the lead heldout tags leave no dev case')

    out = {'seed': seed, 'fraction_heldout': fraction,
           'unit': 'family = case id without the trailing -en/-ar; the lead heldout-tagged cases are all held out',
           'dev': [], 'heldout': []}
    for c in cases:
        out['heldout' if family(c['id']) in held else 'dev'].append(c['id'])
    for side in ('dev', 'heldout'):
        ids = set(out[side])
        cs = [c for c in cases if c['id'] in ids]
        out[f'{side}_count'] = len(cs)
        out[f'{side}_by_category'] = dict(sorted(Counter(c['category'] for c in cs).items()))
        out[f'{side}_by_lang'] = dict(sorted(Counter(c['lang'] for c in cs).items()))
    return out


def load_split(path: Path | None = None) -> dict:
    return json.loads((path or HERE / 'split.json').read_text(encoding='utf-8'))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args(argv)
    cases = yaml.safe_load((HERE / 'cases.yaml').read_text(encoding='utf-8'))
    text = json.dumps(build(cases), ensure_ascii=False, indent=1) + '\n'
    path = HERE / 'split.json'
    if args.check:
        if not path.exists() or path.read_text(encoding='utf-8') != text:
            print('split.json is out of date; run make_split.py', file=sys.stderr)
            return 1
        return 0
    path.write_text(text, encoding='utf-8', newline='\n')
    s = json.loads(text)
    print(f"dev {s['dev_count']}  heldout {s['heldout_count']}")
    for cat in sorted(set(s['dev_by_category']) | set(s['heldout_by_category'])):
        print(f"  {cat:16} dev {s['dev_by_category'].get(cat, 0):3}  held {s['heldout_by_category'].get(cat, 0):3}")
    print('lang dev', s['dev_by_lang'], 'held', s['heldout_by_lang'])
    return 0


if __name__ == '__main__':
    sys.exit(main())
