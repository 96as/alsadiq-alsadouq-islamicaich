"""A fixed line to say when the language model fails (F5, V-02, V-03, UI-12).

Without this, an LLM 429 or a dropped connection ends the turn in silence: the child talks
or types and nothing comes back. livekit already retries inside the stream (conn_options);
this is for when those retries are spent.

What happens:
  * the failure is an livekit APIError (status 429/5xx, connection, timeout) raised before
    the model sent any text: the agent says ONE fixed line instead, chosen by language and by
    kind of turn (see ``classify_turn``), and logs one WARNING (session id and error class
    only, never the child's words);
  * the failure comes after some text already went out: nothing more is said (a second voice
    on top of half a sentence is worse than the pause);
  * any other exception is not touched: it surfaces as before.

The lines are fixed text, not model output, so they cannot invent anything. They say nothing
religious and make no promise about a parent, a teacher or the app.

LEAD REVIEW: every string below is new child-facing wording written by the fixer. The persona,
safety rules and turn rules are untouched; please read these lines once.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

def is_api_error(exc: BaseException) -> bool:
    """True for livekit's APIError family (APIStatusError, APIConnectionError, APITimeoutError...).

    Matched by class name along the MRO so it needs no livekit import (the unit tests run
    against a fake livekit)."""
    return any(
        cls.__name__ == "APIError" and cls.__module__.startswith("livekit")
        for cls in type(exc).__mro__
    )


KIND_GREETING = "greeting"
KIND_SAFETY = "safety"
KIND_RETRY = "retry"

# LEAD REVIEW: child-facing fallback wording. Keep them short: they are spoken.
FALLBACK_LINES: dict[str, dict[str, str]] = {
    KIND_GREETING: {
        "en": "Assalamu alaykum, my friend! I'm Al-Sadiq, an AI friend, not a person. I'm so glad you're here.",
        "ar": "السلام عليكم يا صديقي! أنا الصديق، ذكاء اصطناعي ولست إنسانًا. سعيد جدًا بوجودك هنا.",
    },
    KIND_SAFETY: {
        "en": (
            "I'm so sorry you're going through this. You matter, and you are not alone. "
            "Please tell a grown-up you trust, right now."
        ),
        "ar": (
            "أنا آسف جدًا لأنك تمر بهذا. أنت مهم ولست وحدك. "
            "من فضلك أخبر شخصًا كبيرًا تثق به الآن."
        ),
    },
    KIND_RETRY: {
        "en": "Sorry, I didn't catch that. Can you say it again?",
        "ar": "آسف، لم أفهم جيدًا. هل تعيد كلامك من فضلك؟",
    },
}


def fallback_line(kind: str, language: str) -> str:
    lines = FALLBACK_LINES.get(kind, FALLBACK_LINES[KIND_RETRY])
    return lines.get(language, lines["en"])


def _item_role(item: Any) -> str | None:
    if getattr(item, "type", "message") != "message":
        return None
    return getattr(item, "role", None)


def _item_text(item: Any) -> str:
    text = getattr(item, "text_content", None)
    if text is None:
        content = getattr(item, "content", None)
        if isinstance(content, str):
            text = content
        elif isinstance(content, (list, tuple)):
            text = " ".join(part for part in content if isinstance(part, str))
    return (text or "").strip()


def last_user_text(chat_ctx: Any) -> str | None:
    """The newest child message in the chat, or None when the child has said nothing yet."""
    items = list(getattr(chat_ctx, "items", None) or [])
    for item in reversed(items):
        if _item_role(item) == "user":
            return _item_text(item)
    return None


def classify_turn(chat_ctx: Any, *, safety_turn: bool) -> str | None:
    """Which fixed line fits this failed LLM call, or None to stay quiet.

    greeting : the child has said nothing yet (the agent speaks first);
    safety   : the turn guard put this turn on the safety path (even after a tool round);
    retry    : an ordinary turn the model could not answer;
    None     : an ordinary turn where the assistant already spoke after the child's last
               message (a failed tool follow-up round): nothing to repair.
    """
    items = list(getattr(chat_ctx, "items", None) or [])
    seen_user = False
    spoke_after_child = False
    for item in reversed(items):
        role = _item_role(item)
        if role == "user":
            seen_user = True
            break
        if role == "assistant" and _item_text(item):
            spoke_after_child = True
    if safety_turn:
        return KIND_SAFETY
    if not seen_user:
        return KIND_GREETING
    if spoke_after_child:
        return None
    return KIND_RETRY


def chunk_has_text(chunk: Any) -> bool:
    """True when this llm_node output carries words (a str, or a ChatChunk with delta text)."""
    if isinstance(chunk, str):
        return bool(chunk.strip())
    delta = getattr(chunk, "delta", None)
    content = getattr(delta, "content", None)
    return isinstance(content, str) and bool(content.strip())


async def with_llm_fallback(stream, *, chat_ctx, language_for, safety_turn, session_id, on_fallback=None):
    """Pass ``stream`` (the default llm_node output) through; on an API failure before any
    text, yield the fixed line instead.

    ``language_for(kind)`` returns "ar" or "en". ``safety_turn`` is a zero-argument callable
    read when the failure happens. ``on_fallback`` (optional) is called once when the line is used.
    """
    text_sent = False
    try:
        async for chunk in stream:
            if chunk_has_text(chunk):
                text_sent = True
            yield chunk
    except Exception as exc:
        if not is_api_error(exc):
            raise
        if text_sent:
            logger.warning(
                "llm_node: session %s: %s after the reply had started; nothing more said",
                session_id, type(exc).__name__,
            )
            return
        kind = classify_turn(chat_ctx, safety_turn=bool(safety_turn()))
        if kind is None:
            logger.warning(
                "llm_node: session %s: %s on a follow-up round; staying quiet",
                session_id, type(exc).__name__,
            )
            return
        logger.warning(
            "llm_node: session %s: %s before any text; saying the fixed %s line",
            session_id, type(exc).__name__, kind,
        )
        if on_fallback is not None:
            try:
                on_fallback()
            except Exception:
                logger.debug("llm fallback: on_fallback failed", exc_info=True)
        yield fallback_line(kind, language_for(kind))
    finally:
        close = getattr(stream, "aclose", None)
        if close is not None:
            try:
                await close()
            except Exception:
                logger.debug("llm fallback: closing the LLM stream failed", exc_info=True)
