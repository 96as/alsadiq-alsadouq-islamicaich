"""
Notes Section for the file:
- REASONING_EFFORT for the voice LLM (task 08). On the GPT-5 and GPT-6 families the hidden
  "thinking" step is the biggest part of the time to the first word, so the voice LLM should
  think as little as the model allows.

- What the 1.5.1 plugin does: openai.LLM(reasoning_effort=...) is sent to the API as is. When
  nothing is given it only fills a value for a short fixed list of models (gpt-5.4, gpt-5.2,
  gpt-5.1, gpt-5 and the mini/nano of gpt-5), so gpt-5.4-mini, gpt-5.6-luna and gpt-6-luna get
  NOTHING from the plugin and think at the model's own default.

- What the API does (checked on the team key, 4 Oct 2026): gpt-5.4-mini, gpt-5.4-nano,
  gpt-5.2, gpt-5.6-luna and gpt-6-luna accept none and low and REJECT minimal with a 400
  ("Unsupported value ... Supported values are: none, low, medium, high, xhigh"). Older GPT-5
  models are the other way round (minimal yes, none no). A rejected value would fail every
  reply, so the value is tested before it is used.

- REASONING_EFFORT values:
    unset or "auto"  the lowest the model accepts, tried in the order none, minimal, low
                     (the default).
    none | minimal | low | medium | high | xhigh
                     exactly that value. If the model rejects it: ONE warning, the parameter
                     is dropped (the model's own default applies). Never a crash.
    off              send nothing (what the plugin did before this change).
  Any other text is logged and treated as off.

- Known models are NOT tested at start-up. VERIFIED_VERDICTS below holds the answers checked
  live on the team key (4 Oct 2026, builder and reviewer, all five models). The test request
  took 1.0 to 3.3 s from the dev PC, and livekit runs every session in a fresh job process,
  so testing on each start would hold up every greeting by that much. If OpenAI ever changes
  one of these models, set REASONING_EFFORT=off and update the table.

- How the test works for any OTHER model: one tiny non-streaming request (a few tokens) with
  the value, before the session's LLM is built (awaited, so it delays that session's start).
  The answer is remembered for the life of the process. If the test cannot tell (no network,
  a timeout, the key rejected) the value is dropped for this session and tried again next
  time. The probe uses OPENAI_API_KEY from the environment and never logs it or any message
  text.

- The voice model itself is the lead's call (gpt-4.x chat models are out). This file only
  decides the effort for whichever LLM_MODEL is set.
"""
from __future__ import annotations

import asyncio
import logging
import os
from typing import Awaitable, Callable

logger = logging.getLogger(__name__)

# Lowest first: "none" is the lowest the newer models accept, "minimal" the lowest of the
# older GPT-5 models, "low" is accepted by both.
AUTO_LADDER = ("none", "minimal", "low")
EXPLICIT_VALUES = ("none", "minimal", "low", "medium", "high", "xhigh")
_OFF_WORDS = {"off", "default", "false", "0", "no"}
_AUTO_WORDS = {"", "auto", "lowest"}
PROBE_TIMEOUT_SECONDS = 8.0

# The probe answers: the value works, the model rejected the value, or we cannot tell.
ACCEPTED, REJECTED, UNKNOWN = "accepted", "rejected", "unknown"
Probe = Callable[[str, str], Awaitable[str]]

# Checked live on the team key, 4 Oct 2026: these models take none and low and reject minimal
# (HTTP 400). They are never probed. Any value not listed here is probed as before.
_NONE_LOW_NOT_MINIMAL = {"none": ACCEPTED, "minimal": REJECTED, "low": ACCEPTED}
VERIFIED_VERDICTS: dict[str, dict[str, str]] = {
    model: _NONE_LOW_NOT_MINIMAL
    for model in ("gpt-5.4-mini", "gpt-5.4-nano", "gpt-5.2", "gpt-5.6-luna", "gpt-6-luna")
}

# (model, requested) -> the value to send, or None for "send nothing". Process-wide.
_cache: dict[tuple[str, str], str | None] = {}


def known_verdict(model: str, effort: str) -> str | None:
    """ACCEPTED or REJECTED when the table already knows the answer, else None (probe it)."""
    return VERIFIED_VERDICTS.get((model or "").strip().lower(), {}).get(effort)


def requested_reasoning_effort() -> str:
    """The normalised REASONING_EFFORT setting: "auto", "off" or one explicit value."""
    raw = (os.getenv("REASONING_EFFORT") or "").strip().lower()
    if raw in _AUTO_WORDS:
        return "auto"
    if raw in _OFF_WORDS:
        return "off"
    if raw in EXPLICIT_VALUES:
        return raw
    logger.warning(
        "REASONING_EFFORT=%r is not one of %s, auto or off: no reasoning effort is sent.",
        raw[:20], ", ".join(EXPLICIT_VALUES),
    )
    return "off"


async def probe_reasoning_effort(model: str, effort: str) -> str:
    """Ask the API once whether `model` takes `effort`. Returns ACCEPTED, REJECTED or UNKNOWN."""
    try:
        import openai as openai_sdk  # the plain SDK, installed with livekit-plugins-openai
    except ImportError:
        return UNKNOWN
    client = openai_sdk.AsyncOpenAI(max_retries=0, timeout=PROBE_TIMEOUT_SECONDS)
    try:
        await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "hi"}],
            max_completion_tokens=16,
            reasoning_effort=effort,
        )
        return ACCEPTED
    except openai_sdk.APIStatusError as exc:
        body = getattr(exc, "body", None)
        param = body.get("param") if isinstance(body, dict) else None
        message = str(getattr(exc, "message", "") or "")
        if exc.status_code == 400 and (param == "reasoning_effort" or "reasoning_effort" in message):
            return REJECTED
        return UNKNOWN
    except Exception:  # noqa: BLE001 - a probe must never break a session
        return UNKNOWN
    finally:
        try:
            await client.close()
        except Exception:  # noqa: BLE001
            pass


async def _first_accepted(model: str, candidates: tuple[str, ...], probe: Probe) -> tuple[str | None, bool]:
    """Walk the candidates. Returns (value or None, certain). certain=False means a probe could
    not tell, so the result must not be remembered."""
    for effort in candidates:
        verdict = known_verdict(model, effort)
        if verdict is None:
            try:
                verdict = await asyncio.wait_for(
                    probe(model, effort), timeout=PROBE_TIMEOUT_SECONDS + 2)
            except Exception:  # noqa: BLE001 - includes a timeout
                verdict = UNKNOWN
        if verdict == ACCEPTED:
            return effort, True
        if verdict == UNKNOWN:
            return None, False
    return None, True


async def resolve_reasoning_effort(
    model: str,
    *,
    requested: str | None = None,
    probe: Probe | None = None,
) -> str | None:
    """The reasoning_effort to give openai.LLM for `model`, or None to give nothing."""
    requested = requested or requested_reasoning_effort()
    if requested == "off":
        return None
    key = (model, requested)
    if key in _cache:
        return _cache[key]
    probe = probe or probe_reasoning_effort
    candidates = AUTO_LADDER if requested == "auto" else (requested,)
    value, certain = await _first_accepted(model, candidates, probe)
    if value is None:
        if certain:
            logger.warning(
                "LLM %s does not accept reasoning effort %s: the parameter is dropped and the "
                "model's own default applies.",
                model, "none/minimal/low" if requested == "auto" else requested,
            )
        else:
            logger.warning(
                "Could not test reasoning effort for LLM %s (API unreachable or key rejected): "
                "not sending one for this session.", model,
            )
    else:
        logger.info("LLM %s: reasoning effort %s", model, value)
    if certain:
        _cache[key] = value
    return value


def llm_effort_kwargs(effort: str | None) -> dict:
    """Keyword arguments for openai.LLM: empty when there is nothing to send."""
    return {"reasoning_effort": effort} if effort else {}


def _reset_cache_for_tests() -> None:
    _cache.clear()
