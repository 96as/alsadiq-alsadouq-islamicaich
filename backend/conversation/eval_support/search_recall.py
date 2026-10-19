"""Search recall report (task 13): does ``search_bank`` find a value when a child asks about it?

About 380 child phrasings (``conversation/eval/search_recall_phrasings.yaml``: 5 English and 5 Arabic per
value) are run two ways through ``bank_search.search`` over the seeded bank:

* (a) raw: the child's words as the question, a topic guessed from the shape, no value names;
* (b) real: gpt-5.4-mini gets the agent's real instructions and tool schema and is forced to call
  ``search_bank``; its own ``question`` / ``topic`` / ``values`` arguments go to the search.

A phrasing is a miss when no returned item is linked to the value it was written for. Each miss gets a
class (``MISS_CLASSES``). The model's arguments are cached (``--refresh-args`` asks again), so a re-run
after a fix measures the search and not the model's mood. Run: ``manage.py search_recall``.
"""
from __future__ import annotations

import asyncio
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import yaml

from conversation.agent import bank_search
from conversation.agent.retrieval import items_for_values, match_values

HERE = Path(__file__).resolve()
PHRASINGS_PATH = HERE.parents[1] / "eval" / "search_recall_phrasings.yaml"
OUT_DIR = HERE.parents[3] / "docs" / "hackathon" / "eval-reports" / "source-timing"
TOPIC_FOR_SHAPE = {"verse": "quran", "hadith": "hadith", "say": "values", "sit": "values"}
# what a phrasing of each shape needs the value to have in the bank
NEEDS = {"verse": ("verse",), "hadith": ("hadith",), "say": ("verse", "hadith"), "sit": ("verse", "hadith")}
MISS_CLASSES = {
    "bank_gap": "true bank gap: the value has no item of the kind asked for",
    "value_name_unmatched": "the model passed only value names the search does not match, and the question matched nothing of this value",
    "other_value": "the model named a different value (and the question matched nothing of this one)",
    "no_keyword": "no keyword matched: nothing of this value was a candidate",
    "topic_filter": "the topic filter emptied the value's items",
    "ranked_out": "the value's items were candidates but other items filled the top 3",
}


def load_phrasings(path: Path = PHRASINGS_PATH) -> list[dict]:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    out = []
    for slug, langs in raw.items():
        for lang, entries in langs.items():
            for shape, text in entries:
                out.append({"value": slug, "lang": lang, "shape": shape, "text": text.strip(),
                            "topic": TOPIC_FOR_SHAPE[shape]})
    return out


def case_key(case: dict) -> str:
    return f"{case['lang']}|{case['text']}"


# --------------------------------------------------------------------------- one search

def _expected_items(index, slug: str) -> list:
    return [index.items[pk].obj for _o, pk in index.links.get(slug, [])]


def classify_miss(index, case: dict, question: str, topic: str, values) -> str:
    """Why the search did not return an item of the value the phrasing was written for."""
    slug, lang = case["value"], case["lang"]
    mine = _expected_items(index, slug)
    if not any(it.type in NEEDS[case["shape"]] for it in mine):
        return "bank_gap"
    names = [str(v) for v in (values or []) if str(v).strip()]
    resolved = bank_search._value_slugs(index, names)
    cands = list(match_values(question, lang, None, index)) + items_for_values(
        index, resolved, lang, None, limit=len(index.items))
    in_cands = [it for it in mine if it in cands]
    if not in_cands:
        if names and not resolved:
            return "value_name_unmatched"
        return "other_value" if resolved else "no_keyword"
    allowed = bank_search.TOPIC_TYPES[bank_search._topic(topic)]
    if not any(it.type in allowed for it in in_cands):
        return "topic_filter"
    return "ranked_out"


def run_one(index, case: dict, question: str, topic: str, values) -> dict:
    items = bank_search.search(index, question, topic, list(values or []), case["lang"], None)
    ids = [it.pk for it in items]
    right = any(case["value"] in index.items[pk].value_slugs for pk in ids)
    rec = {"found": bool(ids), "related": bool(ids) and bool(getattr(items, "related", False)),
           "right": right, "ids": ids}
    if not right:
        rec["miss"] = classify_miss(index, case, question, topic, values)
    return rec


# --------------------------------------------------------------------------- the model's arguments

async def ask_models(client, model: str, index, cases: list[dict], cache: dict, *, effort: str | None = "none",
                     concurrency: int = 8, progress=None) -> dict:
    """Fill ``cache`` (key -> {question, topic, values, guard} or {error}) for every case it lacks."""
    from conversation.eval import llm_driver

    agents = {lang: llm_driver.make_agent({"lang": lang}, index, "10-13") for lang in {c["lang"] for c in cases}}
    schemas = {lang: llm_driver.tool_schemas(a) for lang, a in agents.items()}
    sem = asyncio.Semaphore(concurrency)
    todo = [c for c in cases if case_key(c) not in cache]

    async def one(case):
        agent = agents[case["lang"]]
        injection = agent._prepare(case["text"])        # the turn guard, as run_turn does; sync, so no interleaving
        messages = llm_driver.build_messages(agent, case["text"], injection, "voice")
        guard = llm_driver.guard_hit(agent, injection)
        kw = {"model": model, "messages": messages, "tools": schemas[case["lang"]],
              "tool_choice": {"type": "function", "function": {"name": "search_bank"}}}
        if effort:
            kw["reasoning_effort"] = effort
        async with sem:
            try:
                resp = await client.chat.completions.create(**kw)
                args = json.loads(resp.choices[0].message.tool_calls[0].function.arguments or "{}")
                cache[case_key(case)] = {"question": str(args.get("question") or ""), "topic": str(args.get("topic") or ""),
                                         "values": [str(v) for v in (args.get("values") or [])], "guard": guard}
            except Exception as exc:  # noqa: BLE001 - one failed call must not sink the run
                cache[case_key(case)] = {"error": f"{type(exc).__name__}: {str(exc)[:160]}"}
        if progress:
            progress(len(cache), len(cases))

    await asyncio.gather(*(one(c) for c in todo))
    return cache


# --------------------------------------------------------------------------- the report

def evaluate(index, cases: list[dict], args_by_key: dict | None) -> list[dict]:
    rows = []
    for c in cases:
        row = {**c, "a": run_one(index, c, c["text"], c["topic"], [])}
        got = (args_by_key or {}).get(case_key(c))
        if got and "error" not in got:
            row["args"] = {k: got[k] for k in ("question", "topic", "values", "guard") if k in got}
            row["b"] = run_one(index, c, got["question"], got["topic"], got["values"])
        rows.append(row)
    return rows


def _rate(n: int, total: int) -> float:
    return round(n / total, 4) if total else 0.0


def _stats(runs: list[dict]) -> dict:
    n = len(runs)
    return {"n": n,
            "not_found": _rate(sum(not r["found"] for r in runs), n),
            "no_primary": _rate(sum(not r["found"] or r["related"] for r in runs), n),
            "right_value": _rate(sum(r["right"] for r in runs), n)}


def summarise(rows: list[dict], value_order: list[str]) -> dict:
    out = {"cases": len(rows)}
    for mode in ("a", "b"):
        runs = [(r, r[mode]) for r in rows if mode in r]
        if not runs:
            continue
        per_value = {}
        for slug in value_order:
            sub = [x for r, x in runs if r["value"] == slug]
            if sub:
                per_value[slug] = _stats(sub)
        misses = [(r, x) for r, x in runs if not x["right"]]
        out[mode] = {
            **_stats([x for _r, x in runs]),
            "by_lang": {lang: _stats([x for r, x in runs if r["lang"] == lang]) for lang in ("en", "ar")},
            "by_shape": {s: _stats([x for r, x in runs if r["shape"] == s]) for s in TOPIC_FOR_SHAPE},
            "miss_classes": dict(Counter(x["miss"] for _r, x in misses)),
            "per_value": per_value,
        }
    return out


def top_misses(rows: list[dict], mode: str = "b", limit: int = 20) -> list[dict]:
    misses = [r for r in rows if mode in r and not r[mode]["right"]]
    misses.sort(key=lambda r: (r[mode]["found"], r["value"], r["lang"]))     # nothing returned first
    return [{"value": r["value"], "lang": r["lang"], "shape": r["shape"], "text": r["text"],
             "args": r.get("args"), "returned": len(r[mode]["ids"]), "class": r[mode]["miss"]}
            for r in misses[:limit]]


def _pct(x: float) -> str:
    return f"{x * 100:.1f}%"


def render_md(summary: dict, misses: list[dict], meta: dict, baseline: dict | None = None) -> str:
    L = [f"# Search recall report (task 13)", "",
         f"Run {meta['date']} on `{meta.get('commit', '')}`, {summary['cases']} child phrasings "
         f"({meta.get('values', 0)} values x 10), agent model `{meta.get('model', '')}`, "
         f"reasoning effort `{meta.get('effort', '')}`. Children's questions only: no scripture anywhere.", "",
         "(a) raw: the child's words, topic guessed from the shape, no value names. (b) real: gpt-5.4-mini with the "
         "agent's real instructions and tool schema, forced to call `search_bank`; its arguments go to the search. "
         "A miss means no returned item is linked to the value the phrasing was written for.", ""]
    L += ["## Overall", "", "| mode | not found | no verse/hadith as asked | right value |" + (" before: not found | before: right value |" if baseline else ""),
          "|---|---|---|---|" + ("---|---|" if baseline else "")]
    for mode, label in (("a", "(a) raw"), ("b", "(b) real")):
        s = summary.get(mode)
        if not s:
            continue
        row = f"| {label} | {_pct(s['not_found'])} | {_pct(s['no_primary'])} | {_pct(s['right_value'])} |"
        if baseline and baseline.get(mode):
            row += f" {_pct(baseline[mode]['not_found'])} | {_pct(baseline[mode]['right_value'])} |"
        L.append(row)
    L += ["", "\"No verse/hadith as asked\" counts a result that holds only RELATED items from the same value "
          "(the related-item fallback) as a miss of what was asked; \"not found\" counts only an empty result.", ""]
    for mode, label in (("a", "(a) raw"), ("b", "(b) real")):
        s = summary.get(mode)
        if not s:
            continue
        L += [f"### {label}: by language and shape", "", "| group | n | not found | right value |", "|---|---|---|---|"]
        for k, v in {**s["by_lang"], **s["by_shape"]}.items():
            L.append(f"| {k} | {v['n']} | {_pct(v['not_found'])} | {_pct(v['right_value'])} |")
        L += ["", f"### {label}: miss classes", ""]
        classes = s["miss_classes"]
        if classes:
            L += ["| class | count | meaning |", "|---|---|---|"]
            L += [f"| {k} | {n} | {MISS_CLASSES.get(k, '')} |" for k, n in sorted(classes.items(), key=lambda x: -x[1])]
        else:
            L.append("No misses.")
        L.append("")
    b = summary.get("b")
    if b:
        L += ["## Per value, (b) real", "", "| value | n | not found | right value |" + (" before: not found | before: right value |" if baseline and baseline.get("b") else ""),
              "|---|---|---|---|" + ("---|---|" if baseline and baseline.get("b") else "")]
        for slug, v in b["per_value"].items():
            row = f"| {slug} | {v['n']} | {_pct(v['not_found'])} | {_pct(v['right_value'])} |"
            if baseline and baseline.get("b"):
                old = baseline["b"]["per_value"].get(slug)
                row += f" {_pct(old['not_found'])} | {_pct(old['right_value'])} |" if old else " | |"
            L.append(row)
        L.append("")
    L += ["## Top 20 misses, (b) real", "", "| # | value | lang | shape | child said | model's args | returned | class |",
          "|---|---|---|---|---|---|---|---|"]
    for i, m in enumerate(misses, 1):
        a = m["args"] or {}
        shown = f"topic={a.get('topic')}; values={a.get('values')}; question={a.get('question')}".replace("|", "/")
        L.append(f"| {i} | {m['value']} | {m['lang']} | {m['shape']} | {m['text']} | {shown} | {m['returned']} | {m['class']} |")
    L.append("")
    return "\n".join(L)


def git_commit() -> str:
    import subprocess
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                              cwd=HERE.parent, timeout=10).stdout.strip()
    except Exception:  # noqa: BLE001
        return ""


def build_report(index, cases: list[dict], args_by_key: dict | None, meta: dict, baseline: dict | None = None):
    """(rows, summary, misses, markdown) for a run."""
    rows = evaluate(index, cases, args_by_key)
    order = [v.slug for v in index.values]
    summary = summarise(rows, order)
    misses = top_misses(rows)
    meta = {**meta, "date": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"), "values": len(order),
            "commit": meta.get("commit") or git_commit()}
    return rows, summary, misses, render_md(summary, misses, meta, baseline), meta
