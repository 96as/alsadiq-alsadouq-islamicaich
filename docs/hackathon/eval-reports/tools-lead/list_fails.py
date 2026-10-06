"""List every non-pass run (id, category, status, counted tags, policy checks) per side and split. Ids and tags only. Local triage."""
import glob, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
cats = set(sys.argv[1:])
rows = {}
for side in ('before', 'after'):
    for f in sorted(glob.glob(os.path.join(HERE, 'out2', side, 'report-llm-*.json'))):
        d = json.load(open(f, encoding='utf8'))
        for r in d['results']:
            tags = sorted({x['tag'] for x in (r.get('findings') or []) if x.get('counts', True)} | {'policy:' + str(p['check']) for p in (r.get('policy_failures') or [])})
            rows.setdefault(r['case_id'], {})[side] = (r['status'], r['category'], tags, r.get('mode'))
for cid, v in sorted(rows.items(), key=lambda kv: (kv[1]['after'][1], kv[0])):
    b, a = v['before'], v['after']
    if cats and a[1] not in cats:
        continue
    if b[0] == 'pass' and a[0] == 'pass':
        continue
    print(f"{a[1]:16s} {cid:34s} B {b[0]:5s} {b[3]!s:12s} {','.join(b[2])[:60]:60s} | A {a[0]:5s} {a[3]!s:12s} {','.join(a[2])[:70]}")
