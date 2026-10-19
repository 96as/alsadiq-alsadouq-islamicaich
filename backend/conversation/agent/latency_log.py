"""
Notes Section for the file:
- Per-turn latency logging for the voice agent (task 08, step "log the real numbers").
  ONE log line per exchange (a child's turn and the companion's reply), as
  ``turn_latency {json}``, so a run can be summed up with grep and a few lines of Python.

- What a line holds (seconds, rounded to milliseconds; a field is null when it could not be
  measured):
    kind            "reply" (after the child spoke), "greeting" (the first one of the session)
                    or "text" (a reply to typed text).
    language        the session language ("ar" or "en") when the reply started.
    eou_delay_s     end_of_utterance_delay: the child's last voiced moment to the end-of-turn
                    decision (Silero's 0.55 s silence runs inside it).
    stt_delay_s     transcription_delay: the child's last voiced moment to the final transcript.
    llm_ttft_s      time to first token of the FIRST LLM call of the exchange.
    llm_rounds      how many LLM calls the exchange used (more than 1 = a tool round).
    tts_ttfb_s      time to first audio byte of the FIRST TTS segment.
    total_s         the child's last voiced moment to the first agent audio (the number the
                    child feels). Null for greetings, typed turns and replies that never spoke.
    reply_s         the agent going to "thinking" to the first agent audio (LLM and TTS part).
    tool_called     true when any tool ran in the exchange; tools lists the tool NAMES.
    spoke           false when the exchange ended without any agent audio (cancelled).
    llm_model, stt_model, prompt_profile, reasoning_effort   so an A/B run labels itself.

- What a line never holds: the transcript, the reply text, tool arguments or results, the
  child's name or id. Only timings, a language code, tool names and model names. It is safe
  to keep in server logs.

- Switch: LATENCY_LOG=1 forces it on, LATENCY_LOG=0 forces it off. Unset means ON while
  DEBUG is on (development) and OFF otherwise, the same rule as DEMO_GUARDS.

- How it works: it listens to the session events of livekit-agents 1.5.1 (metrics_collected,
  user_state_changed, agent_state_changed, function_tools_executed, close). The child's last
  voiced moment is the created_at of the user_state_changed "listening" event (livekit sets it
  to the VAD end of speech minus the silence window). The exchange opens when the agent goes
  to "thinking" (or "speaking") and closes when it returns to "listening" or "idle".
"""
from __future__ import annotations

import json
import logging
import os
import time
from collections.abc import Callable
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

LOG_MARKER = "turn_latency"


def latency_log_enabled() -> bool:
    """LATENCY_LOG=1 on, 0 off. Unset: on while DEBUG is on (dev), off otherwise."""
    flag = (os.getenv("LATENCY_LOG") or "").strip().lower()
    if flag in ("1", "true", "yes", "on"):
        return True
    if flag in ("0", "false", "no", "off"):
        return False
    # Same rule as settings.py: DEBUG unset counts as off (production).
    return (os.getenv("DEBUG", "0") or "").strip() == "1"


def _round(value: float | None) -> float | None:
    return None if value is None else round(float(value), 3)


@dataclass
class _Exchange:
    opened_at: float
    kind: str
    user_stopped_at: float | None = None
    eou_delay: float | None = None
    stt_delay: float | None = None
    llm_ttfts: list[float] = field(default_factory=list)
    tts_ttfb: float | None = None
    first_audio_at: float | None = None
    language: str | None = None
    tools: list[str] = field(default_factory=list)
    fallback_base: int = 0


class TurnLatencyLogger:
    """Collects the session events of one exchange and writes one log line for it.

    ``emit`` receives the finished line (a string). It defaults to this module's logger at
    INFO. ``language`` is read when the exchange opens, so a mid-session language change is
    reported correctly. ``clock`` exists for tests.
    """

    def __init__(
        self,
        *,
        language: Callable[[], str] | None = None,
        session_id: int | None = None,
        llm_model: str | None = None,
        stt_model: str | None = None,
        prompt_profile: str | None = None,
        reasoning_effort: str | None = None,
        fallback_count: Callable[[], int] | None = None,
        emit: Callable[[str], None] | None = None,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self._language = language
        self._fallback_count = fallback_count
        self._labels = {
            "session_id": session_id,
            "llm_model": llm_model,
            "stt_model": stt_model,
            "prompt_profile": prompt_profile,
            "reasoning_effort": reasoning_effort,
        }
        self._emit = emit or (lambda line: logger.info("%s", line))
        self._clock = clock
        self._exchange: _Exchange | None = None
        self._exchanges_seen = 0
        # Input side that can arrive before the exchange opens (preemptive generation).
        self._pending_user_stopped_at: float | None = None
        self._pending_eou: tuple[float, float] | None = None
        self._lines_written = 0

    # -- wiring -----------------------------------------------------------------

    def attach(self, session) -> None:
        session.on("metrics_collected", self.on_metrics_collected)
        session.on("user_state_changed", self.on_user_state_changed)
        session.on("agent_state_changed", self.on_agent_state_changed)
        session.on("function_tools_executed", self.on_function_tools_executed)
        session.on("close", self.on_close)

    # -- event handlers (never raise: logging must not break a conversation) ----------

    def on_user_state_changed(self, event) -> None:
        try:
            if getattr(event, "new_state", None) == "listening":
                self._pending_user_stopped_at = getattr(event, "created_at", None) or self._clock()
        except Exception:
            logger.debug("latency log: user_state_changed failed", exc_info=True)

    def on_agent_state_changed(self, event) -> None:
        try:
            new_state = getattr(event, "new_state", None)
            at = getattr(event, "created_at", None) or self._clock()
            if new_state in ("thinking", "speaking"):
                ex = self._open(at)
                if new_state == "speaking" and ex.first_audio_at is None:
                    ex.first_audio_at = at
            elif new_state in ("listening", "idle"):
                self._flush()
        except Exception:
            logger.debug("latency log: agent_state_changed failed", exc_info=True)

    def on_metrics_collected(self, event) -> None:
        try:
            metrics = getattr(event, "metrics", event)
            kind = getattr(metrics, "type", "")
            if kind == "eou_metrics":
                values = (
                    float(metrics.end_of_utterance_delay or 0.0),
                    float(metrics.transcription_delay or 0.0),
                )
                if self._exchange is not None and self._exchange.eou_delay is None:
                    self._exchange.eou_delay, self._exchange.stt_delay = values
                    if self._exchange.kind == "text":
                        self._exchange.kind = "reply"
                else:
                    self._pending_eou = values
            elif kind == "llm_metrics" and not getattr(metrics, "cancelled", False):
                if self._exchange is not None:
                    self._exchange.llm_ttfts.append(float(metrics.ttft))
            elif kind == "tts_metrics" and not getattr(metrics, "cancelled", False):
                ex = self._exchange
                ttfb = float(metrics.ttfb)
                # livekit 1.5.1 reports -1 for a segment that ended before any audio arrived.
                if ex is not None and ex.tts_ttfb is None and ttfb >= 0:
                    ex.tts_ttfb = ttfb
        except Exception:
            logger.debug("latency log: metrics_collected failed", exc_info=True)

    def on_function_tools_executed(self, event) -> None:
        try:
            ex = self._exchange
            if ex is None:
                return
            for call in getattr(event, "function_calls", []) or []:
                name = getattr(call, "name", None)
                if name:
                    ex.tools.append(str(name))
        except Exception:
            logger.debug("latency log: function_tools_executed failed", exc_info=True)

    def on_close(self, _event=None) -> None:
        try:
            self._flush()
        except Exception:
            logger.debug("latency log: close failed", exc_info=True)

    # -- internals ---------------------------------------------------------------

    def _open(self, at: float) -> _Exchange:
        if self._exchange is not None:
            return self._exchange
        has_voice_turn = self._pending_user_stopped_at is not None or self._pending_eou is not None
        if has_voice_turn:
            kind = "reply"
        elif self._exchanges_seen == 0:
            kind = "greeting"
        else:
            kind = "text"
        ex = _Exchange(opened_at=at, kind=kind)
        ex.fallback_base = self._read_fallback_count()
        ex.user_stopped_at = self._pending_user_stopped_at
        if self._pending_eou is not None:
            ex.eou_delay, ex.stt_delay = self._pending_eou
        try:
            ex.language = self._language() if self._language else None
        except Exception:
            ex.language = None
        self._pending_user_stopped_at = None
        self._pending_eou = None
        self._exchange = ex
        self._exchanges_seen += 1
        return ex

    def _read_fallback_count(self) -> int:
        try:
            return int(self._fallback_count()) if self._fallback_count else 0
        except Exception:
            return 0

    def _flush(self) -> None:
        ex, self._exchange = self._exchange, None
        if ex is None:
            return
        total = None
        if ex.user_stopped_at is not None and ex.first_audio_at is not None:
            total = max(ex.first_audio_at - ex.user_stopped_at, 0.0)
        reply = None
        if ex.first_audio_at is not None:
            reply = max(ex.first_audio_at - ex.opened_at, 0.0)
        record = {
            "session_id": self._labels["session_id"],
            "kind": ex.kind,
            "language": ex.language,
            "eou_delay_s": _round(ex.eou_delay),
            "stt_delay_s": _round(ex.stt_delay),
            "llm_ttft_s": _round(ex.llm_ttfts[0]) if ex.llm_ttfts else None,
            "llm_rounds": len(ex.llm_ttfts),
            "tts_ttfb_s": _round(ex.tts_ttfb),
            "total_s": _round(total),
            "reply_s": _round(reply),
            "tool_called": bool(ex.tools),
            "tools": ex.tools,
            "spoke": ex.first_audio_at is not None,
            "fallback": self._read_fallback_count() > ex.fallback_base,
            "llm_model": self._labels["llm_model"],
            "stt_model": self._labels["stt_model"],
            "prompt_profile": self._labels["prompt_profile"],
            "reasoning_effort": self._labels["reasoning_effort"],
        }
        self._lines_written += 1
        self._emit(f"{LOG_MARKER} {json.dumps(record, ensure_ascii=False, sort_keys=False)}")


def attach_latency_logger(session, **kwargs) -> TurnLatencyLogger | None:
    """Attach a TurnLatencyLogger to the session when LATENCY_LOG says so."""
    if not latency_log_enabled():
        return None
    tracker = TurnLatencyLogger(**kwargs)
    tracker.attach(session)
    return tracker
