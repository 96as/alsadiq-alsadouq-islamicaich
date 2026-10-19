"""Multi-turn conversation eval: scripted child conversations through the real agent, judged whole.

Per conversation one ``EvalAgent`` is built (so session state such as ``_alerted_rules`` persists
like in a real session) and the scripted child turns are fed one after the other. A turn is built
exactly like production: ``[system: agent.instructions] + history + this turn``. History holds only
the child's text and the guarded reply the child heard; the per-turn injection from ``_prepare`` and
the tool call/result messages are not kept (LiveKit adds the injection to a temporary copy only).
Text channel: injection before the child message; voice channel: after it.

conversations.yaml format (a list)::

    - id: smalltalk-school-ar-gulf   # unique
      lang: ar                       # ar | en (session language)
      age: 8                         # 6-13 -> age band 6-9 / 10-13
      theme: small-talk              # free label
      memory: ""                     # optional: session memory (what Sadiq remembers from earlier sessions)
      turns: ["...", "..."]          # child messages in order, the same for every prompt variant
      expect: "what a great friend would do (read by the judge)"

Reuses ``llm_driver`` (agent, throttled client, call budget, tool stubs, live ``search_bank``, output
guards) and ``judge`` (model list, refusal classification, JSON parsing). Placeholder text only; no
scripture.

Per turn the runner records what the hybrid agent (hk/12) does: the guard that fired (SAFETY, REFER or
none), whether the model called ``search_bank``, the ``{{card:ID}}`` ids it cited, and whether the child's
message was an Islamic question (``asked_flags``, a keyword heuristic: the conversations carry no
per-turn labels).
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import re
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from conversation.eval import judge as eval_judge
from conversation.eval import llm_driver
from conversation.eval.runner import age_band

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]                       # dev_conversations -> eval -> conversation -> backend -> repo
CONVERSATIONS_PATH = HERE / 'conversations.yaml'
RUBRIC_PATH = HERE / 'judge_rubric.md'
SCORE_KEYS = ('friendliness', 'natural_flow', 'memory', 'advice_timing', 'source_timing',
              'no_lesson_creep', 'grounding', 'overall')
JUDGE_MAX_TOKENS = 1500


# ------------------------------------------------------------------ loading

def load_conversations(path=None, ids=None) -> list:
    import yaml
    data = yaml.safe_load(Path(path or CONVERSATIONS_PATH).read_text(encoding='utf-8')) or []
    seen = set()
    for c in data:
        cid = c.get('id')
        if not cid or cid in seen:
            raise ValueError(f'missing or duplicate conversation id: {cid!r}')
        seen.add(cid)
        if c.get('lang') not in ('ar', 'en'):
            raise ValueError(f'{cid}: lang must be ar or en')
        if not isinstance(c.get('age'), int) or not 6 <= c['age'] <= 13:
            raise ValueError(f'{cid}: age must be an integer 6-13')
        if not c.get('turns') or not all(isinstance(t, str) and t.strip() for t in c['turns']):
            raise ValueError(f'{cid}: turns must be a non-empty list of strings')
        c.setdefault('theme', '')
        c['memory'] = (c.get('memory') or '').strip()
        c['expect'] = (c.get('expect') or '').strip()
    if ids:
        missing = [i for i in ids if i not in seen]
        if missing:
            raise ValueError(f'unknown conversation ids: {missing}')
        data = [c for c in data if c['id'] in ids]
    return data


# ------------------------------------------------------------------ one conversation

def card_infos(ids, index) -> list:
    out = []
    for pk in ids:
        ii = index.items.get(pk) if index else None
        out.append({'id': pk, 'type': ii.type if ii else '?', 'values': list(ii.value_slugs) if ii else []})
    return out


def source_label(info: dict) -> str:
    return f"{info['type']}/{info['values'][0] if info['values'] else '-'}"


def count_questions(text: str) -> int:
    return text.count('?') + text.count('؟')


# Is the child's message an Islamic question? The conversations carry no per-turn labels, so: a question
# (mark, or a leading question word) that names an Islamic or value topic, or a bare short follow-up
# ("why?", "but why five times?") to a turn that was one. ponytail: keyword list, not a classifier; a
# value question in unusual words reads as "unasked". Upgrade: per-turn labels in conversations.yaml.
_TOPIC_RE = re.compile(
    r"\b(?:allah|god|qur'?an|hadith|prophet|muhammad|pray(?:er|ing|s)?|salah|salat|zakat|ramadan|fasting|"
    r"jannah|heaven|hell|du'?a|haram|halal|islam(?:ic)?|muslim|mosque|surah|verse|angels?|sadaqah|charity|"
    r"honest(?:y)?|truth|lie|lying|lies|kindness|patien(?:t|ce)|grateful|gratitude|forgive(?:ness)?|"
    r"alhamdulillah|trustworthy|amanah|sin|sinful)\b"
    r"|الله|قران|القران|حديث|النبي|نبينا|رسول|صلا|نصلي|زكا|رمضان|صوم|صيام|جنه|الجنه|النار|دعاء|ادعي|حرام|حلال|"
    r"اسلام|مسلم|مسجد|سوره|ايه|ملائكه|صدق|كذب|حمدلله|الحمد|سبحان|صبر|امانه|شكر|سماح|يسامح", re.I)
_QWORD_RE = re.compile(r"^\W*(?:why|what|how|who|when|where|is|are|do|does|can|could|should|will|was|did|"
                       r"ليش|ليه|لماذا|شو|شنو|شلون|كيف|ايش|وش|هل|متى|وين|مين|ماذا)\b", re.I)


def _is_question(text: str) -> bool:
    return count_questions(text) > 0 or bool(_QWORD_RE.match(_plain(text)))


def asked_flags(texts: list) -> list:
    """Per child message: is it an Islamic (or value) question? See ``_TOPIC_RE``."""
    out = []
    for text in texts:
        plain = _plain(text).replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا').replace('ى', 'ي').replace('ة', 'ه')
        q = _is_question(text)
        followup = q and len(text.split()) <= 5 and bool(out) and out[-1]
        out.append(bool(q and (_TOPIC_RE.search(plain) or followup)))
    return out


async def run_conversation(client, model, conv, index, channel, effort, budget) -> dict:
    lang, age = conv['lang'], age_band(conv['age'])
    agent = llm_driver.EvalAgent(
        db_session_id=0, child_id=0, language=lang, age_band=age, value_index=index,
        session_memory=conv.get('memory') or None)
    schemas = llm_driver.tool_schemas(agent)
    effort = llm_driver._effort(effort)
    out = {'id': conv['id'], 'lang': lang, 'age': conv['age'], 'age_band': age, 'theme': conv.get('theme', ''),
           'memory': conv.get('memory', ''), 'expect': conv.get('expect', ''), 'turns': [], 'error': '',
           'instructions_sha1': hashlib.sha1(agent.instructions.encode('utf-8')).hexdigest()[:12]}
    asked = asked_flags(conv['turns'])
    history = []
    for n, text in enumerate(conv['turns'], 1):
        turn = {'n': n, 'child': text, 'asked': asked[n - 1]}
        out['turns'].append(turn)
        try:
            rec = llm_driver.TurnRecord(agent=agent)
            injection = agent._prepare(text.strip())
            built = llm_driver.build_messages(agent, text, injection, channel)
            messages = built[:1] + history + built[1:]
            api = [0.0, 0]
            token = llm_driver.API_SECONDS.set(api)
            started = time.perf_counter()
            try:
                raw = await llm_driver._agent_rounds(client, model, messages, schemas, effort, budget, rec, agent)
            finally:
                llm_driver.API_SECONDS.reset(token)
            wall = time.perf_counter() - started
            await llm_driver.finish_turn(agent, rec, raw, injection)
        except Exception as exc:  # noqa: BLE001 - recorded; the conversation stops here
            turn['error'] = f'{type(exc).__name__}: {str(exc)[:200]}'
            out['error'] = f'turn {n}: {turn["error"]}'
            break
        reply = rec.reply
        calls = [c['name'] for c in rec.tool_calls]
        turn.update(
            guard=rec.guard, injection=injection, reply_raw=raw, reply=reply, guard_changed=rec.guard_changed,
            tool_calls=rec.tool_calls, search_bank_called='search_bank' in calls,
            flagged=rec.guard == 'SAFETY' or 'flag_safety_concern' in calls,
            retrieved_ids=rec.retrieved_ids, retrieved=card_infos(rec.retrieved_ids, index),
            cards_cited=rec.cards_raw, cards_shown=rec.cards_shown, items=card_infos(rec.cards_shown, index),
            cards_invalid=rec.cards_invalid,
            licence=sorted(rec.licence),
            prompt_tokens=rec.prompt_tokens, completion_tokens=rec.completion_tokens,
            latency_s=round(api[0] if api[1] else wall, 3), model=rec.model,
            words=len(reply.split()), questions=count_questions(reply))
        history.append({'role': 'user', 'content': text})
        if reply:
            history.append({'role': 'assistant', 'content': reply})
    return out


# ------------------------------------------------------------------ deterministic metrics

_SOURCE_RE = re.compile(r'\b(?:card|verse|hadith|surah|quran|prophet)s?\b|آية|حديث|سورة|القرآن|النبي|الرسول|البطاقة|بطاقة', re.I)
_RELIGIOUS_RE = re.compile(
    r'\ballah\b|\bma sha allah\b|\bjannah\b|\breward\b|remember to|\balways\b|الله|ما شاء الله|الجنة|أجر|تذكر|دائما|لازم', re.I)
_TASHKEEL = re.compile('[ً-ْٰـ]')


def _plain(text: str) -> str:
    return _TASHKEEL.sub('', text or '')


def metrics(turns: list) -> dict:
    done = [t for t in turns if not t.get('error') and 'reply' in t]
    if not done:
        return {}
    words = [t['words'] for t in done]
    qs = [t['questions'] for t in done]
    searched = [t['n'] for t in done if t['search_bank_called']]
    # "unasked": a source word in the reply on a turn where nothing was looked up and no card was cited
    unasked = [t['n'] for t in done if not t['search_bank_called'] and not t['items']
               and _SOURCE_RE.search(_plain(t['reply']))]
    # "plain" turns: no guard note and no search_bank call, so nothing religious was asked for or served
    plain = [t for t in done if t['guard'] == 'none' and not t['search_bank_called']]
    religious = [t['n'] for t in plain if _RELIGIOUS_RE.search(_plain(t['reply']))]
    repeated, prev = 0, None
    for t in done:
        first = re.findall(r'\w+', t['reply'].lower())[:3]
        if prev is not None and first and first == prev:
            repeated += 1
        prev = first
    return {
        'avg_reply_words': round(sum(words) / len(words), 1), 'max_reply_words': max(words),
        'avg_questions': round(sum(qs) / len(qs), 2), 'multi_question_turns': sum(1 for q in qs if q > 1),
        'source_turns': sum(1 for t in done if t['items']),
        'search_bank_turns': len(searched), 'searched_turns': searched,
        'cards_shown': sum(len(t['items']) for t in done),
        'cards_on_unasked_turns': sum(len(t['items']) for t in done if not t['asked']),
        'cards_invalid': sum(len(t['cards_invalid']) for t in done),
        'unasked_source_mentions': len(unasked), 'unasked_source_turns': unasked,
        'religious_phrase_in_plain_turns': len(religious), 'religious_phrase_turns': religious,
        'repeated_openers': repeated,
    }


# ------------------------------------------------------------------ judge

def transcript_for_judge(conv: dict, turns: list) -> str:
    lines = ['## CONVERSATION', f"language: {conv['lang']}", f"child age: {conv['age']}",
             'EXPECT (what a great friend would do):', '<<<EXPECT>>>', conv.get('expect') or '(none)', '<<<END EXPECT>>>',
             'MEMORY (what Sadiq remembers from earlier sessions):', '<<<MEMORY>>>',
             conv.get('memory') or '(none)', '<<<END MEMORY>>>', '', '## TRANSCRIPT']
    for t in turns:
        if t.get('error') or 'reply' not in t:
            break
        srcs = ', '.join(source_label(i) for i in t['retrieved']) or 'none'
        cards = ', '.join(source_label(i) for i in t['items']) or 'none'
        tools = ''.join(f"; tool: {c['name']}" for c in t['tool_calls'])
        lines += ['', f"### TURN {t['n']}", '<<<CHILD>>>', t['child'], '<<<END CHILD>>>',
                  f"SADIQ (guard: {t['guard']}; sources: {srcs}; cards shown: {cards}{tools})",
                  '<<<REPLY>>>', t['reply'], '<<<END REPLY>>>']
    return '\n'.join(lines)


class JudgeState:
    """Judge models in preference order, shared by all conversations; remembers what the API refused."""

    def __init__(self, models: list) -> None:
        self.models = list(models)
        self.dropped = {}            # model -> optional params the API rejected (temperature, reasoning_effort)


async def call_judge(client, state: JudgeState, messages: list, budget) -> tuple:
    """(content, usage dict, model). Drops an optional parameter the model rejects, else tries the next model."""
    last = None
    for model in list(state.models):
        dropped = state.dropped.setdefault(model, set())
        while True:
            kw = {'response_format': {'type': 'json_object'}, 'max_completion_tokens': JUDGE_MAX_TOKENS}
            if 'temperature' not in dropped:
                kw['temperature'] = 0
            if 'reasoning_effort' not in dropped:
                kw['reasoning_effort'] = 'none'
            budget.take('judge')
            try:
                resp = await client.chat.completions.create(model=model, messages=messages, **kw)
            except Exception as exc:  # noqa: BLE001 - classified below
                if not eval_judge.model_refused(exc):
                    raise
                param = str(getattr(exc, 'param', '') or '')
                if param in ('temperature', 'reasoning_effort') and param not in dropped:
                    dropped.add(param)
                    continue
                last = exc
                if model in state.models:
                    state.models.remove(model)
                break
            usage = getattr(resp, 'usage', None)
            u = {'prompt': getattr(usage, 'prompt_tokens', 0) or 0, 'completion': getattr(usage, 'completion_tokens', 0) or 0}
            return resp.choices[0].message.content or '', u, str(getattr(resp, 'model', '') or model)
    raise eval_judge.JudgeUnavailable(f'no judge model accepted the call: {str(last)[:160]}')


def _norm(s: str) -> str:
    return ' '.join(_plain(s).split())


def parse_judge(text: str, turns: list) -> dict:
    data = eval_judge._loads(text)
    if not isinstance(data, dict) or not isinstance(data.get('scores'), dict):
        return {'parsed': False}
    scores = {}
    for k in SCORE_KEYS:
        v = data['scores'].get(k)
        scores[k] = int(v) if isinstance(v, (int, float)) and not isinstance(v, bool) and 1 <= v <= 5 else None
    reasons = {k: str((data.get('reasons') or {}).get(k, ''))[:300] for k in SCORE_KEYS}
    by_n = {t['n']: t.get('reply', '') for t in turns}
    problems, bad = [], 0
    for p in data.get('problems') or []:
        if not isinstance(p, dict):
            continue
        quote, reply = str(p.get('quote', '')).strip(), by_n.get(p.get('turn'), '')
        if quote and (quote in reply or _norm(quote) in _norm(reply)):
            problems.append({'turn': p['turn'], 'quote': quote, 'issue': str(p.get('issue', ''))[:300]})
        else:
            bad += 1
    best = data.get('best_moment') if isinstance(data.get('best_moment'), dict) else {}
    return {'parsed': True, 'scores': scores, 'reasons': reasons, 'problems': problems, 'bad_quotes': bad,
            'best_moment': {'turn': best.get('turn'), 'why': str(best.get('why', ''))[:300]}}


async def judge_conversation(client, state: JudgeState, conv: dict, result: dict, budget) -> dict:
    messages = [{'role': 'system', 'content': RUBRIC_PATH.read_text(encoding='utf-8')},
                {'role': 'user', 'content': transcript_for_judge(conv, result['turns'])}]
    content, usage, model = await call_judge(client, state, messages, budget)
    verdict = parse_judge(content, result['turns'])
    verdict['model'], verdict['usage'] = model, usage
    return verdict


# ------------------------------------------------------------------ whole run

def _mean(xs):
    xs = [x for x in xs if x is not None]
    return round(sum(xs) / len(xs), 2) if xs else None


def aggregate(results: list) -> dict:
    turns = [t for r in results for t in r['turns'] if not t.get('error') and 'reply' in t]
    ms = [r['metrics'] for r in results if r.get('metrics')]
    scored = [r['judge']['scores'] for r in results if r.get('judge', {}).get('parsed')]
    out = {
        'conversations': len(results), 'errors': sum(1 for r in results if r['error']),
        'scores': {k: _mean([s[k] for s in scored]) for k in SCORE_KEYS} if scored else {},
        'metrics': {
            'avg_reply_words': _mean([m['avg_reply_words'] for m in ms]),
            'max_reply_words': max([m['max_reply_words'] for m in ms], default=None),
            'avg_questions': _mean([m['avg_questions'] for m in ms]),
            **{k: sum(m[k] for m in ms) for k in ('multi_question_turns', 'source_turns', 'search_bank_turns',
                                                  'cards_shown', 'cards_on_unasked_turns', 'cards_invalid',
                                                  'unasked_source_mentions', 'religious_phrase_in_plain_turns',
                                                  'repeated_openers')}},
        'turns': len(turns),
        'agent_prompt_tokens': sum(t['prompt_tokens'] for t in turns),
        'agent_completion_tokens': sum(t['completion_tokens'] for t in turns),
        'judge_prompt_tokens': sum(r['judge']['usage']['prompt'] for r in results if r.get('judge', {}).get('usage')),
        'judge_completion_tokens': sum(r['judge']['usage']['completion'] for r in results if r.get('judge', {}).get('usage')),
        'mean_latency_s': _mean([t['latency_s'] for t in turns]),
        'bad_quotes': sum(r['judge'].get('bad_quotes', 0) for r in results if r.get('judge')),
    }
    return out


def _git(*args) -> str:
    try:
        return subprocess.run(['git', *args], cwd=REPO, capture_output=True, text=True, timeout=10).stdout.strip()
    except Exception:  # noqa: BLE001 - provenance is best effort
        return ''


def run_dev_convs(conversations: list, index, *, client, agent_model: str, judge_models: list, label: str = 'run',
                  channel: str = 'voice', effort: str | None = None, max_calls: int = 600, concurrency: int = 6,
                  judge_on: bool = True, file_path=None, progress=None) -> dict:
    budget = llm_driver.CallBudget(max_calls)
    state = JudgeState(judge_models)

    async def one(sem, conv):
        async with sem:
            res = await run_conversation(client, agent_model, conv, index, channel, effort, budget)
            res['metrics'] = metrics(res['turns'])
            if judge_on and not res['error'] and res['turns']:
                try:
                    res['judge'] = await judge_conversation(client, state, conv, res, budget)
                except Exception as exc:  # noqa: BLE001 - recorded; the transcript is still useful
                    res['judge'] = {'parsed': False, 'error': f'{type(exc).__name__}: {str(exc)[:200]}'}
            if progress:
                progress(res, budget)
            return res

    async def main():
        sem = asyncio.Semaphore(concurrency)
        return await asyncio.gather(*(one(sem, c) for c in conversations))

    started = datetime.now(timezone.utc)
    results = list(asyncio.run(main()))
    path = Path(file_path or CONVERSATIONS_PATH)
    judge_used = sorted({r['judge']['model'] for r in results if r.get('judge', {}).get('model')})
    snapshots = sorted({t['model'] for r in results for t in r['turns'] if t.get('model')})
    return {
        'config': {
            'label': label, 'date': started.isoformat(timespec='seconds'), 'git_commit': _git('rev-parse', '--short', 'HEAD'),
            'git_dirty': bool(_git('status', '--porcelain')), 'agent_model': agent_model, 'agent_model_resolved': snapshots,
            'judge_models_tried': list(judge_models), 'judge_model_used': judge_used, 'judge_on': judge_on,
            'reasoning_effort': llm_driver._effort(effort) or '', 'channel': channel, 'concurrency': concurrency,
            'max_calls': max_calls, 'calls_used': budget.used, 'agent_calls': budget.agent_calls,
            'judge_calls': budget.judge_calls,
            'seed': 'none: child turns are scripted and fixed; model sampling is not seeded',
            'conversations_file': str(path), 'conversations_sha256': hashlib.sha256(path.read_bytes()).hexdigest()[:16],
            'judge_params_dropped': {m: sorted(d) for m, d in state.dropped.items() if d},
        },
        'aggregate': aggregate(results),
        'conversations': results,
    }


# ------------------------------------------------------------------ reports

def render_transcript(run: dict) -> str:
    cfg = run['config']
    out = [f"# Dev conversations: {cfg['label']}", '',
           f"commit {cfg['git_commit']}{' (dirty)' if cfg['git_dirty'] else ''}, agent {cfg['agent_model']}, "
           f"judge {', '.join(cfg['judge_model_used']) or 'none'}, effort {cfg['reasoning_effort'] or 'default'}, "
           f"channel {cfg['channel']}", '']
    for r in run['conversations']:
        out += [f"## {r['id']}  (lang {r['lang']}, age {r['age']}, theme {r['theme']})", '']
        if r['expect']:
            out += [f"Expect: {r['expect']}", '']
        if r['memory']:
            out += [f"Memory: {r['memory']}", '']
        for t in r['turns']:
            out.append(f"**Child:** {t['child']}")
            if t.get('error'):
                out += ['', f"ERROR: {t['error']}"]
                break
            srcs = ', '.join(source_label(i) for i in t['retrieved']) or 'none'
            cards = ', '.join(source_label(i) for i in t['items']) or 'none'
            tools = f", tools: {', '.join(c['name'] for c in t['tool_calls'])}" if t['tool_calls'] else ''
            out += ['', f"**Sadiq** [guard: {t['guard']}; sources: {srcs}; cards: {cards}{tools}; {t['words']} words]: "
                        f"{t['reply']}", '']
        j = r.get('judge')
        if j and j.get('parsed'):
            out.append('Scores: ' + ', '.join(f"{k} {v}" for k, v in j['scores'].items()))
            out += [f"- {k}: {v}" for k, v in j['reasons'].items() if v]
            out += [f"- PROBLEM turn {p['turn']}: \"{p['quote']}\" ({p['issue']})" for p in j['problems']]
            b = j['best_moment']
            out.append(f"- Best moment: turn {b['turn']}: {b['why']}")
        elif j:
            out.append(f"Judge failed: {j.get('error') or 'unparsable output'}")
        m = r.get('metrics') or {}
        if m:
            out.append('Metrics: ' + ', '.join(f"{k} {v}" for k, v in m.items() if not k.endswith('_turns')))
        out.append('')
    return '\n'.join(out)


def write_reports(run: dict, out_dir) -> list:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    a, b = out_dir / 'run.json', out_dir / 'transcript.md'
    a.write_text(json.dumps(run, ensure_ascii=False, indent=1), encoding='utf-8')
    b.write_text(render_transcript(run), encoding='utf-8')
    return [a, b]


def console_summary(run: dict) -> str:
    cfg, agg = run['config'], run['aggregate']
    lines = [f"== dev conversations [{cfg['label']}] commit {cfg['git_commit']}{'+dirty' if cfg['git_dirty'] else ''}: "
             f"{agg['conversations']} conversations, {agg['turns']} turns, {agg['errors']} errors",
             f"agent {cfg['agent_model']} (effort {cfg['reasoning_effort'] or 'default'}, {cfg['channel']}), "
             f"judge {', '.join(cfg['judge_model_used']) or 'none'}, calls {cfg['calls_used']}/{cfg['max_calls']}"]
    if agg['scores']:
        lines.append('scores (mean 1-5): ' + '  '.join(f"{k} {v}" for k, v in agg['scores'].items()))
    lines.append('metrics: ' + '  '.join(f"{k} {v}" for k, v in agg['metrics'].items()))
    lines.append(f"tokens: agent {agg['agent_prompt_tokens']} in / {agg['agent_completion_tokens']} out, "
                 f"judge {agg['judge_prompt_tokens']} in / {agg['judge_completion_tokens']} out; "
                 f"mean latency {agg['mean_latency_s']} s per turn; judge quotes dropped {agg['bad_quotes']}")
    lines.append('')
    lines.append(f"{'conversation':36} {'overall':>7} {'ground':>6} {'words':>6} {'search':>6} {'cards':>5} {'c-unask':>7} "
                 f"{'unasked':>7} {'relig':>5}")
    for r in run['conversations']:
        m, s = r.get('metrics') or {}, (r.get('judge') or {}).get('scores') or {}
        lines.append(f"{r['id'][:36]:36} {str(s.get('overall', '-')):>7} {str(s.get('grounding', '-')):>6} "
                     f"{str(m.get('avg_reply_words', '-')):>6} {str(m.get('search_bank_turns', '-')):>6} "
                     f"{str(m.get('cards_shown', '-')):>5} {str(m.get('cards_on_unasked_turns', '-')):>7} "
                     f"{str(m.get('unasked_source_mentions', '-')):>7} {str(m.get('religious_phrase_in_plain_turns', '-')):>5}"
                     + (f"  ERROR {r['error']}" if r['error'] else ''))
    return '\n'.join(lines)
