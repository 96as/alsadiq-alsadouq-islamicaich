"""JSON and HTML reports for the LLM eval run (task 09).

The HTML is one self-contained file (inline CSS, no scripts, no network), light and dark,
every case text escaped and set ``dir="auto"`` so Arabic renders right to left.
"""
from __future__ import annotations

import json
from dataclasses import fields as _fields
from datetime import datetime
from html import escape
from pathlib import Path

from .runner import EVAL_DIR
from .llm_driver import CallBudget
from .llm_runner import LlmResult, LlmRun, console_summary, rate, summarize, to_json  # noqa: F401  (re-export)

_CSS = """
:root{--bg:#fbfaf7;--fg:#1d2433;--mut:#5d6679;--card:#fff;--line:#e3e0d8;--ok:#1f8a4c;--bad:#c0392b;--gap:#b7791f;--err:#6b46c1;--bar:#e8e5dc}
@media (prefers-color-scheme:dark){:root{--bg:#10141c;--fg:#e8ebf2;--mut:#98a1b5;--card:#181e2a;--line:#2a3243;--ok:#46c37b;--bad:#ff7a6b;--gap:#e0b25a;--err:#a98bff;--bar:#273045}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,Segoe UI,sans-serif}
main{max-width:1080px;margin:0 auto;padding:24px 16px 64px}h1{font-size:1.5rem;margin:0 0 4px}h2{font-size:1.15rem;margin:32px 0 10px}
.sub{color:var(--mut);margin:0 0 16px}.banner{background:var(--gap);color:#fff;padding:8px 12px;border-radius:8px;font-weight:600;margin:12px 0}
.grid{display:grid;gap:12px;grid-template-columns:repeat(auto-fit,minmax(150px,1fr))}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 14px}.card b{display:block;font-size:1.6rem}
.card span{color:var(--mut);font-size:.85rem}
table{width:100%;border-collapse:collapse;background:var(--card);border:1px solid var(--line);border-radius:10px;overflow:hidden}
th,td{text-align:left;padding:7px 10px;border-bottom:1px solid var(--line);vertical-align:middle}th{font-size:.8rem;color:var(--mut);text-transform:uppercase;letter-spacing:.04em}
td.n{text-align:right;font-variant-numeric:tabular-nums}
.bar{height:10px;background:var(--bar);border-radius:5px;min-width:90px;overflow:hidden;display:flex}
.bar i{display:block;height:100%}.bar .p{background:var(--ok)}.bar .f{background:var(--bad)}.bar .g{background:var(--gap)}.bar .e{background:var(--err)}
.tag{display:inline-block;padding:1px 8px;border-radius:99px;font-size:.78rem;font-weight:600;color:#fff}
.t-pass{background:var(--ok)}.t-fail{background:var(--bad)}.t-gap{background:var(--gap)}.t-error{background:var(--err)}
details{background:var(--card);border:1px solid var(--line);border-radius:10px;margin:8px 0;padding:8px 12px}
summary{cursor:pointer;font-weight:600}.mut{color:var(--mut)}
pre{white-space:pre-wrap;word-break:break-word;background:var(--bg);border:1px solid var(--line);border-radius:8px;padding:8px 10px;margin:6px 0;font:13px/1.5 ui-monospace,Consolas,monospace}
ul.why{margin:6px 0 6px 18px;padding:0}.kv{display:grid;grid-template-columns:max-content 1fr;gap:3px 14px;margin:0}.kv dt{color:var(--mut)}.kv dd{margin:0;word-break:break-word}
.tw{max-width:100%;overflow-x:auto;-webkit-overflow-scrolling:touch}
@media (max-width:640px){th,td{padding:6px}.kv{grid-template-columns:1fr}.bar{min-width:48px}th{font-size:.7rem;letter-spacing:0}}
"""


def _pct(v):
    return '-' if v is None else f'{v:.0%}'


def _bar(c: dict) -> str:
    tot = sum(c.get(k, 0) for k in ('pass', 'fail', 'gap', 'error')) or 1
    parts = ''.join(f'<i class="{cls}" style="width:{c.get(k, 0) * 100 / tot:.1f}%"></i>'
                    for cls, k in (('p', 'pass'), ('f', 'fail'), ('g', 'gap'), ('e', 'error')))
    return f'<div class="bar" role="img" aria-label="pass {c.get("pass", 0)} fail {c.get("fail", 0)}">{parts}</div>'


def _table(title: str, rows: dict) -> str:
    out = [f'<h2>{escape(title)}</h2><div class="tw"><table><tr><th>{escape(title.split(" ")[-1])}</th><th>runs</th><th>pass</th>'
           '<th>fail</th><th>gap</th><th>error</th><th>pass rate</th><th></th></tr>']
    for k, c in rows.items():
        out.append(f'<tr><td>{escape(str(k))}</td><td class="n">{sum(c.values())}</td><td class="n">{c.get("pass", 0)}</td>'
                   f'<td class="n">{c.get("fail", 0)}</td><td class="n">{c.get("gap", 0)}</td><td class="n">{c.get("error", 0)}</td>'
                   f'<td class="n">{_pct(rate(c))}</td><td>{_bar(c)}</td></tr>')
    return ''.join(out) + '</table></div>'


def _pre(text: str) -> str:
    return f'<pre dir="auto">{escape(text or "")}</pre>'


def _case(r) -> str:
    why = ''.join(f'<li dir="auto">{escape(x)}</li>' for x in r.reasons) or '<li>no reason recorded</li>'
    if r.error:
        why += f'<li>run error: {escape(r.error)}</li>'
    j = r.judge or {}
    judge_line = (f'rubric {escape(str(j.get("rubric")))}; referral_ok {j.get("referral_ok")}; states_ai {j.get("states_ai")}; '
                  f'{escape(j.get("reason", ""))}' if j else escape(r.judge_skipped or 'not run'))
    kv = [('input', escape(r.input)), ('age / lang / channel', f'{r.age} / {r.lang} / {r.channel}'),
          ('policy', escape(f'level {r.level}, mode {r.mode}, rule {r.rule or "-"}')),
          ('served', escape(', '.join(r.served) or 'nothing')),
          ('tool calls', escape(', '.join(c['name'] for c in r.tool_calls) or 'none')),
          ('judge', judge_line), ('calls', f'agent {r.agent_calls}, judge {r.judge_calls}')]
    dl = ''.join(f'<dt>{k}</dt><dd dir="auto">{v}</dd>' for k, v in kv)
    guard = ('<p class="mut">The output guard changed the model text. Raw reply:</p>' + _pre(r.reply_raw)) if r.guard_changed else ''
    return (f'<details><summary><span class="tag t-{r.status}">{r.status}</span> {escape(r.case_id)} '
            f'<span class="mut">[{escape(r.channel)}] {escape(r.category)}</span></summary>'
            f'<ul class="why">{why}</ul><p class="mut">Reply the child would hear:</p>{_pre(r.reply)}{guard}'
            f'<dl class="kv">{dl}</dl></details>')


def render_html(run: LlmRun) -> str:
    s = summarize(run.results)
    t, cfg = s['total'], run.config
    dry = bool(cfg.get('dry_run'))
    judge_used = ', '.join(cfg.get('judge_model_used') or []) or ('none' if not cfg.get('judge') else 'not called')
    available = cfg.get('available_runs') or run.planned
    not_sampled = cfg.get('not_sampled', 0)
    cards = [(_pct(s['pass_rate']), f"scored pass rate ({s['scored']} scored, gaps and errors excluded)"),
             (_pct(s['gate_pass_rate']), f"triage only: policy, checks and judge tags, rubric verdict excluded ({s['rubric_only_fails']} runs differ)"),
             (t.get('pass', 0), 'pass'), (t.get('fail', 0), 'fail'),
             (t.get('gap', 0), 'content gap (task 02)'), (t.get('error', 0), 'run errors'),
             (f"{len(run.results)} / {available}" if 'available_runs' in cfg else len(run.results),
              'runs in this report / runs the filters allow' if 'available_runs' in cfg else 'runs in this report'),
             (f"{s['agent_calls']} + {s['judge_calls']}", f"LLM calls, agent + judge (cap {run.budget.limit})")]
    fp = cfg.get('fingerprints') or {}
    cfg_rows = [('date', cfg.get('date', '')), ('commit', cfg.get('commit') or 'not recorded (set EVAL_COMMIT in a container)'),
                ('agent model', cfg.get('agent_model', '') + (f" (API: {', '.join(cfg['agent_model_resolved'])})"
                                                              if cfg.get('agent_model_resolved') else '')),
                ('judge model', judge_used + (f" (API: {', '.join(cfg['judge_model_resolved'])})"
                                              if cfg.get('judge_model_resolved') else '')),
                ('judge settings', 'temperature 0, reasoning none, JSON object output'),
                ('agent reasoning effort', cfg.get('reasoning_effort') or 'provider default'),
                ('agent temperature', cfg.get('agent_temperature', '')), ('channels', ', '.join(cfg.get('channels', []))),
                ('sample', (f"{len(run.results)} of {available} runs (seed {cfg.get('seed')}); {not_sampled} not sampled; "
                            if 'available_runs' in cfg else
                            f"{len(run.results)} runs (seed {cfg.get('seed')}); this older report does not record how many "
                            "runs the sample left out; ") + f"{len(run.not_run)} left out by the call cap"),
                ('filters', str(cfg.get('filters') or 'none')),
                ('fingerprints', ', '.join(f'{k} {v}' for k, v in fp.items()) or 'not recorded'),
                ('agent API time per case', f"median {s.get('median_latency_s', 0):.1f} s, mean {s['mean_latency_s']:.1f} s"
                                            + ('' if fp else ' (this older report includes token-pacing waits)')),
                ('concurrency', cfg.get('concurrency'))]
    if dry:
        cfg_rows.append(('live run would use', f"about {cfg.get('estimated_live_calls')} calls for "
                                              f"{cfg.get('sample')} runs"))
    fails = [r for r in run.results if r.status in ('fail', 'error')]
    warn = [r for r in run.results if r.status == 'pass' and (r.warnings or r.raw_violations)]
    out = ['<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
           f'<title>Eval report {escape(cfg.get("date", "")[:10])}</title><style>{_CSS}</style></head><body><main>',
           '<h1>Al-Sadiq eval report</h1>',
           f'<p class="sub">{"Dry run: policy checks only, no model was called." if dry else "Agent text path plus deterministic checks plus strict judge."} '
           f'{escape(cfg.get("date", ""))}</p>']
    if dry:
        out.append('<div class="banner">DRY RUN. The numbers below are policy-only. Replies and the judge did not run.</div>')
    out.append('<div class="grid">' + ''.join(f'<div class="card"><b>{escape(str(a))}</b><span>{escape(b)}</span></div>'
                                              for a, b in cards) + '</div>')
    out.append('<h2>Configuration</h2><div class="card"><dl class="kv">' +
               ''.join(f'<dt>{escape(a)}</dt><dd>{escape(str(b))}</dd>' for a, b in cfg_rows) + '</dl></div>')
    out.append(_table('Pass rate by category', s['by_category']))
    out.append(_table('Pass rate by language', s['by_lang']))
    out.append(_table('Pass rate by channel', s['by_channel']))
    if s['failed_checks']:
        out.append('<h2>What failed</h2><div class="tw"><table><tr><th>check</th><th>runs</th></tr>' +
                   ''.join(f'<tr><td>{escape(k)}</td><td class="n">{v}</td></tr>' for k, v in s['failed_checks'].items()) +
                   '</table></div>')
    out.append(f'<h2>Failing cases ({len(fails)})</h2>' + (''.join(_case(r) for r in fails) or '<p class="mut">None.</p>'))
    if warn:
        out.append(f'<h2>Passed with a warning ({len(warn)})</h2><p class="mut">Not failures: the raw model text broke a '
                   'rule that the output guard then fixed, or a soft signal fired.</p>')
        for r in warn:
            items = ''.join(f'<li dir="auto">{escape(str(w))}</li>' for w in r.warnings)
            items += ''.join(f'<li dir="auto">raw: {escape(f["tag"])} {escape(f["detail"])}</li>' for f in r.raw_violations)
            out.append(f'<details><summary>{escape(r.case_id)} [{escape(r.channel)}]</summary><ul class="why">{items}</ul>'
                       f'{_pre(r.reply)}</details>')
    gaps = sorted({(r.case_id, tuple(r.expected.get('items') or [])) for r in run.results if r.gap})
    if gaps:
        out.append(f'<h2>Content gaps ({len(gaps)} cases)</h2><p class="mut">The bank lacks the item the case expects. '
                   'Scored on the safety and grounding checks only.</p><ul>' +
                   ''.join(f'<li>{escape(c)}: {escape(", ".join(p))}</li>' for c, p in gaps) + '</ul>')
    out.append('</main></body></html>')
    return ''.join(out)


def write_reports(run: LlmRun, directory=EVAL_DIR, json_=True, html_=True) -> list:
    stamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    kind = 'dry' if run.config.get('dry_run') else 'llm'
    d = Path(directory)
    d.mkdir(parents=True, exist_ok=True)
    paths = []
    if json_:
        p = d / f'report-{kind}-{stamp}.json'
        p.write_text(to_json(run), encoding='utf-8')
        paths.append(p)
    if html_:
        p = d / f'report-{kind}-{stamp}.html'
        p.write_text(render_html(run), encoding='utf-8')
        paths.append(p)
    return paths


def load_run(path) -> LlmRun:
    """Rebuild a finished run from its JSON report, to re-render it without any model call."""
    d = json.loads(Path(path).read_text(encoding='utf-8'))
    names = {f.name for f in _fields(LlmResult)}
    results = []
    for raw in d['results']:
        kw = {k: v for k, v in raw.items() if k in names}
        kw['policy_failures'] = [(p['check'], p['expected'], p['got']) for p in kw.get('policy_failures', [])]
        results.append(LlmResult(**kw))
    s = d.get('summary', {})
    budget = CallBudget(d['config'].get('max_llm_calls', 0))
    budget.agent_calls, budget.judge_calls = s.get('agent_calls', 0), s.get('judge_calls', 0)
    return LlmRun(results, d['config'], budget, started=d.get('started', ''), finished=d.get('finished', ''),
                  planned=d.get('planned', len(results)), not_run=[tuple(x) for x in d.get('left_out_by_cap', [])])
