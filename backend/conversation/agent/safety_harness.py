"""Before and after harness for the SAFETY rules (offline, no LLM, no network).

    cd backend
    PYTHONUTF8=1 python -m conversation.agent.safety_harness snapshot OUT.json
    PYTHONUTF8=1 python -m conversation.agent.safety_harness compare BEFORE.json AFTER.json

A snapshot records, for every sentence, the ids of the safety rules that fire on it. The sets:

* ``existing``: every sentence in ``test_safety_classes.py`` (positives, negatives, review probes) plus every
  string literal of three or more words in the backend test files, plus the DEV eval inputs (the split file
  names the dev ids; held-out cases are never loaded).
* ``everyday`` and ``risk``: the new synthetic sets in ``safety_precision_data.py``.

``compare`` prints the tables and exits non-zero when a sentence that fired before no longer fires.
"""
from __future__ import annotations

import ast
import json
import os
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[2]
EVAL_DIR = BACKEND / "conversation" / "eval"
SELF = Path(__file__).name
SKIP_FILES = {"safety_precision_data.py", "safety_precision_probes.py", "safety_harness.py", "test_safety_precision.py"}


def _setup():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings_sqlite_test")
    if str(BACKEND) not in sys.path:
        sys.path.insert(0, str(BACKEND))
    import django
    django.setup()


def _literals():
    """Every string literal of three or more words in the backend test files."""
    found = {}
    for path in sorted(BACKEND.rglob("test*.py")):
        if path.name in SKIP_FILES or "migrations" in path.parts:
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                s = node.value.strip()
                if len(s) >= 12 and len(s.split()) >= 3 and "\n" not in s:
                    found.setdefault(s, path.name)
    return found


def _dev_inputs():
    """Inputs of the DEV eval cases only."""
    from conversation.eval import load_cases
    split = json.loads((EVAL_DIR / "split.json").read_text(encoding="utf-8"))
    dev = set(split["dev"])
    out = []
    for case in load_cases():
        if case["id"] in dev:
            for key in ("input", "input_voice"):
                if case.get(key):
                    out.append(case[key])
    return out


def collect():
    _setup()
    from conversation.agent import safety_precision_data as d
    from conversation.agent import test_safety_classes as t
    existing = {}
    for name in ("POSITIVES", "NEGATIVES"):
        for text, _lang in getattr(t, name):
            existing.setdefault(text, name.lower())
    for name in ("REAL_WITH_PLAY_WORDS", "KNOWN_OVER_TRIGGERS", "REVIEW_POSITIVES", "REVIEW_NEGATIVES"):
        for text in getattr(t, name):
            existing.setdefault(text, name.lower())
    for text, src in _literals().items():
        existing.setdefault(text, "literal:" + src)
    for text in _dev_inputs():
        existing.setdefault(text, "eval-dev")
    return {
        "existing": existing,
        "everyday": {text: topic for topic, _lang, text in d.EVERYDAY},
        "risk": {text: topic for topic, _lang, text in d.REAL_RISK},
        "out_of_scope": {text: "out_of_scope" for text in d.OUT_OF_SCOPE_EVERYDAY},
    }


def hits(text):
    from conversation.agent import turn_guard
    from conversation.agent.text_match import token_forms
    tf = token_forms(text)
    return [r.id for r in turn_guard.load_rules().safety if r.matches(tf)]


def snapshot(out_path):
    sets = collect()
    snap = {}
    for name, items in sets.items():
        snap[name] = {text: {"src": src, "hits": sorted(set(hits(text)))} for text, src in items.items()}
    Path(out_path).write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    for name, items in snap.items():
        fired = sum(1 for v in items.values() if v["hits"])
        print(f"{name:13s} {len(items):4d} sentences, {fired:4d} fire")


def _load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def _rate(items):
    n = len(items)
    f = sum(1 for v in items.values() if v["hits"])
    return n, f


def compare(before_path, after_path):
    b, a = _load(before_path), _load(after_path)
    print("| Set | Sentences | Fire before | Fire after |")
    print("|---|---|---|---|")
    for name in ("everyday", "risk", "existing", "out_of_scope"):
        n, fb = _rate(b[name])
        _n, fa = _rate({k: a[name].get(k, {"hits": []}) for k in b[name]})
        print(f"| {name} | {n} | {fb} | {fa} |")
    print()
    print("Everyday false positives by topic (before, after):")
    topics = {}
    for text, v in b["everyday"].items():
        t = v["src"]
        row = topics.setdefault(t, [0, 0, 0])
        row[0] += 1
        row[1] += bool(v["hits"])
        row[2] += bool(a["everyday"][text]["hits"])
    for t, (n, fb, fa) in sorted(topics.items()):
        print(f"  {t:8s} {n:3d}  {fb:3d} -> {fa:3d}")
    lost = []
    for name in ("existing", "risk", "out_of_scope"):
        for text, v in b[name].items():
            if v["hits"] and not a[name][text]["hits"]:
                lost.append((name, text, v["hits"], v["src"]))
    print()
    print(f"Sentences that fired before and are silent now: {len(lost)}")
    for name, text, rules, src in lost:
        print(f"  [{name}/{src}] {text}  (was {rules})")
    changed = 0
    for name in ("existing", "risk"):
        for text, v in b[name].items():
            if v["hits"] and a[name][text]["hits"] and set(v["hits"]) != set(a[name][text]["hits"]):
                changed += 1
    print(f"Still firing, but through different rules: {changed}")
    left = [(t, v["hits"]) for t, v in a["everyday"].items() if v["hits"]]
    print(f"Everyday sentences still firing after: {len(left)}")
    for t, rules in left:
        print(f"  {t}  {rules}")
    miss = [(t, v["src"]) for t, v in a["risk"].items() if not v["hits"]]
    print(f"Real-risk sentences silent after: {len(miss)}")
    for t, src in miss:
        print(f"  [{src}] {t}")
    return 1 if lost or miss else 0


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "snapshot" and len(sys.argv) == 3:
        snapshot(sys.argv[2])
    elif cmd == "compare" and len(sys.argv) == 4:
        sys.exit(compare(sys.argv[2], sys.argv[3]))
    else:
        print(__doc__)
        sys.exit(2)
