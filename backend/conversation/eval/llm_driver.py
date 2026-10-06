"""Text-path driver for the LLM eval run (task 09).

Drives the real ``AlSadiqAgent`` on text, with no audio and no LiveKit room:

* instructions: ``agent.instructions`` (persona, grounding rules, speech style ...), unchanged;
* turn guard: ``agent._prepare(text)`` (the same call both entry points use) returns the per-turn note
  ("" unless the guard fired on safety or a referral); ``text`` channel puts it before the child
  message (``reply_to_typed``), ``voice`` puts it after it (``on_user_turn_completed``);
* tools: the agent's own function-tool schemas. ``search_bank`` (pure and in memory over the bank
  index) runs for real through the agent's own method; every other tool is a stub (no database).
  Up to ``MAX_TOOL_ROUNDS`` rounds, so the model can search, read the result and answer;
* output: ``agent.guard_speech`` (card markers, attribution guard, then scripture filter) and the
  markdown and emoji filters, exactly as ``tts_node`` chains them, so the reply scored is what the
  child would hear. The raw model text is kept next to it, with the ``{{card:ID}}`` ids found in it.

``EvalAgent`` neutralises the side effects of ``_prepare`` and of the tools (audit rows, cards,
safety flags are database and room work), nothing else.
"""
from __future__ import annotations

import asyncio
import contextvars
import inspect
import json
import os
import re
import time
from collections import deque
from dataclasses import dataclass, field

from conversation.agent.agent_class import AlSadiqAgent
from conversation.agent.scripture_guard import DECLINE_TEXT

MAX_TOOL_ROUNDS = 2          # search_bank, read the result, (one more call), then the model must answer in text
LIVE_TOOLS = frozenset({'search_bank'})    # run for real: pure in-memory over the bank index
CARD_MARKER = re.compile(r'\{\{card:(\d+)\}\}')   # how the model cites an item in its reply
CARD_IN_RESULT = re.compile(r'\{\{card:(\d+)\}\}')     # how search_bank lists each item it returns (its marker)
REASONING_EFFORTS = ('none', 'minimal', 'low', 'medium', 'high', 'xhigh')
_CHUNK = 14                  # characters per streamed chunk fed to the guards (exercises the holds)


class BudgetExhausted(RuntimeError):
    pass


class CallBudget:
    """Counts LLM calls; ``reserve`` lets a case claim its worst case before it starts."""

    def __init__(self, limit: int) -> None:
        self.limit = limit
        self.agent_calls = 0
        self.judge_calls = 0
        self._reserved = 0

    @property
    def used(self) -> int:
        return self.agent_calls + self.judge_calls

    @property
    def remaining(self) -> int:
        return self.limit - self.used - self._reserved

    def reserve(self, n: int) -> bool:
        if self.remaining < n:
            return False
        self._reserved += n
        return True

    def release(self, n: int) -> None:
        self._reserved = max(0, self._reserved - n)

    def take(self, kind: str = 'agent') -> None:
        # hard cap: a call that would go over the limit is never made (judge model fallbacks
        # are the only calls a case can make beyond its reservation)
        if self.used >= self.limit:
            raise BudgetExhausted(f'LLM call cap of {self.limit} reached')
        if kind == 'judge':
            self.judge_calls += 1
        else:
            self.agent_calls += 1


class Tee:
    """Per-case call counter that also charges the shared budget (cases run concurrently).

    ``reserved`` is what the case reserved up front; each call it makes uses up one unit of that
    reservation, so a running case is not counted twice (once as used, once as still reserved)
    and later cases are not left out while the cap still has room. The runner releases the rest."""

    def __init__(self, parent: CallBudget, reserved: int = 0) -> None:
        self.parent = parent
        self.reserved = reserved
        self.agent_calls = 0
        self.judge_calls = 0

    def take(self, kind: str = 'agent') -> None:
        self.parent.take(kind)
        if self.reserved > 0:
            self.reserved -= 1
            self.parent.release(1)
        if kind == 'judge':
            self.judge_calls += 1
        else:
            self.agent_calls += 1


class Throttle:
    """Sliding 60 s window over estimated prompt tokens, so a shared TPM limit is not hit.

    The OpenAI organisation limit is shared with every other job on the key, so the default
    leaves headroom (``--tpm``). A 429 that still happens is retried by ``ThrottledClient``.
    """

    def __init__(self, tokens_per_minute: int) -> None:
        self.limit = max(1000, tokens_per_minute)
        self._window: deque = deque()          # (monotonic time, tokens)
        self._lock = asyncio.Lock()

    async def acquire(self, tokens: int) -> None:
        tokens = min(tokens, self.limit)
        async with self._lock:
            while True:
                now = time.monotonic()
                while self._window and now - self._window[0][0] >= 60:
                    self._window.popleft()
                used = sum(n for _t, n in self._window)
                if used + tokens <= self.limit:
                    self._window.append((now, tokens))
                    return
                await asyncio.sleep(max(0.2, 60 - (now - self._window[0][0])) if self._window else 0.2)


_RETRY_IN = re.compile(r'try again in ([0-9.]+)\s*(ms|s)', re.I)

# Seconds spent inside the API call itself (not in token pacing or 429 back-off), per case.
# Each case runs in its own asyncio task, so a context variable keeps the cases apart.
API_SECONDS: contextvars.ContextVar = contextvars.ContextVar('eval_api_seconds', default=None)


def _estimate_tokens(messages, kw) -> int:
    chars = sum(len(str(m.get('content') or '')) for m in messages) + len(json.dumps(kw.get('tools') or []))
    return chars // 3 + 400      # Arabic tokenises worse than 4 characters per token; plus the reply


class _Completions:
    def __init__(self, parent) -> None:
        self._p = parent

    async def create(self, **kw):
        p = self._p
        est = _estimate_tokens(kw.get('messages') or [], kw)
        for attempt in range(p.max_429 + 1):
            if p.throttle:
                await p.throttle.acquire(est)
            acc = API_SECONDS.get()
            t0 = time.perf_counter()
            try:
                resp = await p.client.chat.completions.create(**kw)
                if acc is not None:
                    acc[0] += time.perf_counter() - t0
                    acc[1] += 1
                return resp
            except Exception as exc:  # noqa: BLE001 - only rate limits are retried here
                if getattr(exc, 'status_code', None) != 429 or attempt >= p.max_429:
                    raise
                m = _RETRY_IN.search(str(exc))
                wait = (float(m.group(1)) / (1000 if m.group(2).lower() == 'ms' else 1)) if m else 2.0
                p.rate_limited += 1
                await asyncio.sleep(min(30.0, wait + 0.5 + attempt))


class _Chat:
    def __init__(self, parent) -> None:
        self.completions = _Completions(parent)


class ThrottledClient:
    """Wraps an AsyncOpenAI client: paces by tokens per minute and retries 429s (not billed, not counted)."""

    def __init__(self, client, tokens_per_minute: int | None = 120000, max_429: int = 8) -> None:
        self.client = client
        self.throttle = Throttle(tokens_per_minute) if tokens_per_minute else None
        self.max_429 = max_429
        self.rate_limited = 0
        self.chat = _Chat(self)


class EvalAgent(AlSadiqAgent):
    """The real agent with its database and room side effects switched off."""

    def _spawn(self, coro) -> None:        # audit rows, reference cards, safety flag: not in eval
        coro.close()

    async def _publish_event(self, topic: str, payload: dict) -> None:   # no room in eval
        return None


def make_agent(case: dict, index, age_band: str) -> EvalAgent:
    lang = case['lang']
    return EvalAgent(
        db_session_id=0, child_id=0, language=lang, age_band=age_band, value_index=index)


def tool_schemas(agent) -> list:
    """OpenAI function-tool schemas of the agent's own tools (strict mode, as the plugin sends)."""
    from livekit.agents import llm
    from livekit.agents.llm.utils import build_strict_openai_schema

    ctx = llm.ToolContext(agent.tools)
    return [build_strict_openai_schema(t) for t in ctx.function_tools.values()]


def stub_tool(agent, name: str, args: dict) -> str:
    """What the tool would answer, without touching a database."""
    if name == 'flag_safety_concern':
        if agent._safety_turn:
            return 'Already recorded for this message; no need to call again.'
        return 'Recorded for review.'
    if name == 'record_engagement':
        return 'Recorded +5 points (total 5).'
    if name == 'list_my_quests':
        return 'The child has no quests yet.'
    if name == 'complete_conversation_quest':
        return 'Quest not found for this child; check list_my_quests.'
    return 'Unknown tool.'


async def run_tool(agent, name: str, args: dict) -> str:
    """What the tool answers. ``LIVE_TOOLS`` run through the agent's own method (the real ranking over the
    bank index); a live tool the agent does not have yet (before hk/12 lands) falls back to the stub."""
    if name in LIVE_TOOLS and hasattr(agent, name):
        out = getattr(agent, name)(**args)
        if inspect.isawaitable(out):
            out = await out
        return str(out)
    return stub_tool(agent, name, args)


def card_ids(text: str) -> list:
    """Distinct ``{{card:ID}}`` ids in ``text``, in order of first use."""
    return list(dict.fromkeys(int(i) for i in CARD_MARKER.findall(text or '')))


def strip_card_markers(text: str) -> str:
    return CARD_MARKER.sub('', text or '')


def guard_hit(agent, injection: str = '') -> str:
    """Which turn guard fired: ``SAFETY``, ``REFER`` or ``none``. Reads ``agent.last_hit`` (a ``GuardHit``
    with ``kind``, None when the guard stayed silent) and the turn flags; a turn note with no readable hit
    is ``other``."""
    kind = str(getattr(getattr(agent, 'last_hit', None), 'kind', '') or '').upper()
    if kind in ('SAFETY', 'REFER'):
        return kind
    if getattr(agent, '_safety_turn', False):
        return 'SAFETY'
    if getattr(agent, '_refer_turn', False):
        return 'REFER'
    return 'other' if injection else 'none'


def turn_items(agent) -> list:
    """Items search_bank returned this turn and last (what the licence and the card check go by)."""
    return list(getattr(agent, '_turn_items', []) or []) + list(getattr(agent, '_prev_items', []) or [])


def licence_kinds(agent) -> frozenset:
    try:
        return frozenset(agent._licence())
    except Exception:  # noqa: BLE001 - an agent without a licence concept licenses nothing
        return frozenset()


def bank_index():
    """The value index as the agent entrypoint builds it. Raises RuntimeError if the bank is empty."""
    from conversation.agent.retrieval import build_value_index
    index = build_value_index()
    if not index:
        raise RuntimeError('the bank is empty after seed_content')
    return index


@dataclass
class TurnRecord:
    reply_raw: str = ''
    reply: str = ''
    tool_calls: list = field(default_factory=list)
    injection: str = ''
    items: list = field(default_factory=list)
    licence: frozenset = frozenset()
    safety_turn: bool = False
    guard_changed: bool = False
    agent_calls: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_s: float = 0.0       # time inside the API calls (token pacing and 429 waits excluded)
    wall_s: float = 0.0          # wall time of the turn, pacing included
    model: str = ''              # the model snapshot the API reports (resp.model)
    finish_reason: str = ''
    guard: str = ''              # SAFETY | REFER | other | none: which turn guard fired (guard_hit)
    hit: object = None           # the agent's GuardHit (None: the guard stayed silent)
    cards_raw: list = field(default_factory=list)       # {{card:ID}} ids in the raw model text
    cards_shown: list = field(default_factory=list)     # ids the agent actually showed as cards (agent._cards)
    cards_invalid: list = field(default_factory=list)   # cited ids that are not items search_bank returned
    retrieved_ids: list = field(default_factory=list)   # {{card:ID}} ids search_bank returned this turn
    agent: object = None


def build_messages(agent, text: str, injection: str, channel: str) -> list:
    msgs = [{'role': 'system', 'content': agent.instructions}]
    user = {'role': 'user', 'content': text}
    if not injection:
        return msgs + [user]
    inj = {'role': 'system', 'content': injection}
    # text: reply_to_typed puts the injection before the child message;
    # voice: on_user_turn_completed adds it after the message that just completed.
    return msgs + ([inj, user] if channel == 'text' else [user, inj])


async def _aiter(chunks):
    for c in chunks:
        yield c


def _chunks(text: str) -> list:
    return [text[i:i + _CHUNK] for i in range(0, len(text), _CHUNK)] or ['']


async def apply_output_guards(agent, raw: str) -> tuple:
    """(guarded reply, guard changed it). Same chain as ``AlSadiqAgent.tts_node``."""
    from livekit.agents.voice.transcription.filters import filter_emoji, filter_markdown

    guarded = ''.join([c async for c in agent.guard_speech(_aiter(_chunks(raw)), count=False)])
    cleaned = ''.join([c async for c in filter_markdown(filter_emoji(_aiter(_chunks(guarded))))])
    # FALLBACK: the agent's guard_speech strips {{card:ID}} markers (hk/12 marker filter, or the brace
    # filter before it). If an agent without that step ever lets one through, the scored reply must
    # still be marker-free, so strip here. Remove once guard_speech is the only path.
    cleaned = strip_card_markers(cleaned)
    return cleaned.strip(), strip_card_markers(guarded) != strip_card_markers(raw)


async def finish_turn(agent, rec: TurnRecord, raw: str, injection: str = '') -> None:
    """The facts every consumer wants once the model has answered: raw text, card ids, licence after
    the tool rounds, the guarded reply, which turn guard fired."""
    rec.reply_raw = raw
    rec.licence = licence_kinds(agent)
    rec.cards_raw = card_ids(raw)
    rec.reply, rec.guard_changed = await apply_output_guards(agent, raw)    # the marker filter calls the agent's _cite
    rec.guard = guard_hit(agent, injection)
    rec.hit = getattr(agent, 'last_hit', None)
    rec.items = turn_items(agent)
    known = {i.pk for i in rec.items} or set(rec.retrieved_ids)
    rec.cards_shown = list(getattr(agent, '_cards_published', getattr(agent, '_cards', rec.cards_raw)))
    rec.cards_invalid = [i for i in rec.cards_raw if i not in known]


def _effort(value):
    v = (value or os.getenv('REASONING_EFFORT', '')).strip().lower()
    return v if v in REASONING_EFFORTS else None


async def run_turn(client, model: str, case: dict, channel: str, index, age_band: str, *,
                   budget: CallBudget | None = None, reasoning_effort: str | None = None,
                   schemas: list | None = None) -> TurnRecord:
    """One child turn through the agent. Raises on API errors (the runner records them)."""
    agent = make_agent(case, index, age_band)
    text = (case.get('input_voice') or case['input']) if channel == 'voice' else case['input']
    rec = TurnRecord(agent=agent)
    injection = agent._prepare(text.strip())
    rec.injection = injection
    rec.hit = agent.last_hit
    rec.safety_turn = agent._safety_turn
    messages = build_messages(agent, text, injection, channel)
    schemas = schemas if schemas is not None else tool_schemas(agent)
    effort = _effort(reasoning_effort)
    started = time.perf_counter()
    api = [0.0, 0]                       # seconds inside API calls, calls timed (ThrottledClient fills it)
    api_token = API_SECONDS.set(api)
    reply = ''
    try:
        reply = await _agent_rounds(client, model, messages, schemas, effort, budget, rec, agent)
    finally:
        API_SECONDS.reset(api_token)
    rec.wall_s = time.perf_counter() - started
    rec.latency_s = api[0] if api[1] else rec.wall_s   # a bare client (tests) has no pacing to exclude
    await finish_turn(agent, rec, reply, injection)
    return rec


async def _agent_rounds(client, model, messages, schemas, effort, budget, rec, agent) -> str:
    """The model call, up to ``MAX_TOOL_ROUNDS`` rounds of tool calls (``search_bank`` live, the rest stubs),
    the final answer. Returns the raw reply text."""
    reply = ''
    for round_no in range(MAX_TOOL_ROUNDS + 1):
        kw = {}
        if effort:
            kw['reasoning_effort'] = effort
        if schemas:
            kw['tools'] = schemas
            if round_no >= MAX_TOOL_ROUNDS:
                kw['tool_choice'] = 'none'
        if budget is not None:
            budget.take('agent')
        resp = await client.chat.completions.create(model=model, messages=messages, **kw)
        rec.agent_calls += 1
        rec.model = getattr(resp, 'model', '') or rec.model
        usage = getattr(resp, 'usage', None)
        rec.prompt_tokens += getattr(usage, 'prompt_tokens', 0) or 0
        rec.completion_tokens += getattr(usage, 'completion_tokens', 0) or 0
        choice = resp.choices[0]
        rec.finish_reason = choice.finish_reason or ''
        msg = choice.message
        calls = getattr(msg, 'tool_calls', None) or []
        if not calls:
            reply = msg.content or ''
            break
        messages.append({
            'role': 'assistant', 'content': msg.content or None,
            'tool_calls': [{'id': c.id, 'type': 'function',
                            'function': {'name': c.function.name, 'arguments': c.function.arguments}}
                           for c in calls]})
        for c in calls:
            try:
                args = json.loads(c.function.arguments or '{}')
            except ValueError:
                args = {}
            entry = {'name': c.function.name, 'args': args}
            try:
                result = await run_tool(agent, c.function.name, args)
            except Exception as exc:  # noqa: BLE001 - what the voice agent does too: the model sees a tool error
                result = 'Tool error: the lookup failed.'
                entry['error'] = f'{type(exc).__name__}: {str(exc)[:160]}'
            if c.function.name in LIVE_TOOLS:
                entry['result'] = result[:1500]
                rec.retrieved_ids.extend(i for i in dict.fromkeys(int(x) for x in CARD_IN_RESULT.findall(result))
                                         if i not in rec.retrieved_ids)
            rec.tool_calls.append(entry)
            messages.append({'role': 'tool', 'tool_call_id': c.id, 'content': result})
        if msg.content:
            reply = msg.content    # text said alongside the call; replaced if the follow-up answers
    return reply


def decline_texts() -> set:
    return set(DECLINE_TEXT.values())
