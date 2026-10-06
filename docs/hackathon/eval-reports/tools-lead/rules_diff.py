"""Structural diff of turn_rules.json between two git refs, run from the agent-quality worktree. Prints rule ids and counts only."""
import json, subprocess, sys

P = 'backend/session_moral_context/content/turn_rules.json'


def load(ref):
    return json.loads(subprocess.check_output(['git', 'show', f'{ref}:{P}']).decode('utf8'))


a, b = load(sys.argv[1]), load(sys.argv[2])
print(type(a).__name__, list(a.keys()) if isinstance(a, dict) else len(a))


def ids(x):
    if isinstance(x, dict):
        return x
    return {(i.get('id') or i.get('name') or str(n)): i for n, i in enumerate(x)}


for k in a:
    va, vb = a[k], b.get(k)
    if isinstance(va, (dict, list)):
        da, db = ids(va), ids(vb)
        print(f'{k}: before {len(da)} after {len(db)}')
        print('  added  :', sorted(set(db) - set(da))[:200])
        print('  removed:', sorted(set(da) - set(db)))
        print('  changed:', [x for x in da if x in db and da[x] != db[x]])
    else:
        print(k, 'same' if va == vb else f'{va!r} -> {vb!r}')
for k in b:
    if k not in a:
        print('new top-level key', k)
