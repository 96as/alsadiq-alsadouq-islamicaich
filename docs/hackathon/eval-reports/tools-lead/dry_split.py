"""Policy-only (dry-run) pass counts per split, before vs after. Ids and counts only."""
import glob, json, os
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
SPLIT = json.load(open(os.path.join(HERE, '..', 'agent-quality', 'backend', 'conversation', 'eval', 'split.json'), encoding='utf8'))
HELD = set(SPLIT['heldout'])
out = {}
for side in ('before', 'after'):
    f = glob.glob(os.path.join(HERE, 'out2', side, 'dry', 'report-dry-*.json'))[0]
    d = json.load(open(f, encoding='utf8'))
    c = {'heldout': Counter(), 'dev': Counter()}
    safety = {'heldout': Counter(), 'dev': Counter()}
    for r in d['results']:
        sp = 'heldout' if r['case_id'] in HELD else 'dev'
        c[sp][r['status']] += 1
        if r['category'] == 'safety':
            safety[sp][r['status']] += 1
    out[side] = {sp: dict(v) for sp, v in c.items()}
    out[side]['safety'] = {sp: dict(v) for sp, v in safety.items()}
    print(side, out[side])
json.dump(out, open(os.path.join(HERE, 'out2', 'dry_split.json'), 'w'), indent=1)
