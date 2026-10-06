"""Tests for the per-turn latency log (latency_log.py) and how the entrypoint wires it.

latency_log.py imports no livekit code, so the logger tests use plain event objects shaped
like the livekit-agents 1.5.1 events. The wiring tests use the same fake livekit as
test_voice_wiring.py.

Run from backend/:  python manage.py test conversation.agent.test_latency_log \
    --settings=config.settings_sqlite_test
"""
from __future__ import annotations

import json
import os
import unittest
from types import SimpleNamespace
from unittest import mock

from conversation.agent import latency_log
from conversation.agent.latency_log import LOG_MARKER, TurnLatencyLogger, latency_log_enabled
from conversation.agent.test_voice_wiring import _WiringBase


def _user_state(new_state, at):
    return SimpleNamespace(old_state="speaking", new_state=new_state, created_at=at)


def _agent_state(new_state, at):
    return SimpleNamespace(old_state="idle", new_state=new_state, created_at=at)


def _eou(delay, transcription):
    return SimpleNamespace(metrics=SimpleNamespace(
        type="eou_metrics", end_of_utterance_delay=delay, transcription_delay=transcription,
        on_user_turn_completed_delay=0.0, speech_id="s1",
    ))


def _llm(ttft, cancelled=False):
    return SimpleNamespace(metrics=SimpleNamespace(
        type="llm_metrics", ttft=ttft, cancelled=cancelled, speech_id="s1",
    ))


def _tts(ttfb, cancelled=False):
    return SimpleNamespace(metrics=SimpleNamespace(
        type="tts_metrics", ttfb=ttfb, cancelled=cancelled, speech_id="s1",
    ))


def _tools(*names):
    return SimpleNamespace(function_calls=[SimpleNamespace(name=n, arguments="SECRET") for n in names])


class _Harness:
    def __init__(self, language="ar"):
        self.lines = []
        self.language = language
        self.log = TurnLatencyLogger(
            language=lambda: self.language, session_id=7, llm_model="llm-x", stt_model="stt-x",
            prompt_profile="full", reasoning_effort="none", emit=self.lines.append,
        )

    def records(self):
        out = []
        for line in self.lines:
            marker, _, payload = line.partition(" ")
            assert marker == LOG_MARKER, line
            out.append(json.loads(payload))
        return out


class TurnLatencyLoggerTests(unittest.TestCase):
    def test_a_voice_turn_writes_one_line_with_every_number(self):
        h = _Harness("en")
        h.log.on_user_state_changed(_user_state("listening", 100.0))
        h.log.on_metrics_collected(_eou(0.62, 0.41))
        h.log.on_agent_state_changed(_agent_state("thinking", 100.62))
        h.log.on_metrics_collected(_llm(0.5))
        h.log.on_metrics_collected(_tts(0.2))
        h.log.on_agent_state_changed(_agent_state("speaking", 101.3))
        h.log.on_agent_state_changed(_agent_state("listening", 105.0))
        (rec,) = h.records()
        self.assertEqual(rec["kind"], "reply")
        self.assertEqual(rec["language"], "en")
        self.assertEqual(rec["eou_delay_s"], 0.62)
        self.assertEqual(rec["stt_delay_s"], 0.41)
        self.assertEqual(rec["llm_ttft_s"], 0.5)
        self.assertEqual(rec["llm_rounds"], 1)
        self.assertEqual(rec["tts_ttfb_s"], 0.2)
        self.assertEqual(rec["total_s"], 1.3)
        self.assertEqual(rec["reply_s"], 0.68)
        self.assertFalse(rec["tool_called"])
        self.assertTrue(rec["spoke"])
        self.assertEqual((rec["llm_model"], rec["stt_model"], rec["prompt_profile"]),
                         ("llm-x", "stt-x", "full"))
        self.assertEqual(rec["reasoning_effort"], "none")

    def test_eou_metrics_that_arrive_after_thinking_still_join_the_exchange(self):
        h = _Harness()
        h.log.on_user_state_changed(_user_state("listening", 10.0))
        h.log.on_agent_state_changed(_agent_state("thinking", 10.5))
        h.log.on_metrics_collected(_eou(0.5, 0.3))
        h.log.on_agent_state_changed(_agent_state("speaking", 11.0))
        h.log.on_agent_state_changed(_agent_state("listening", 12.0))
        (rec,) = h.records()
        self.assertEqual(rec["eou_delay_s"], 0.5)
        self.assertEqual(rec["total_s"], 1.0)

    def test_a_tts_segment_without_audio_does_not_count_as_the_first_byte(self):
        # livekit 1.5.1 reports ttfb=-1 for a segment that ended before any audio arrived.
        h = _Harness()
        h.log.on_agent_state_changed(_agent_state("thinking", 1.0))
        h.log.on_metrics_collected(_tts(-1.0))
        h.log.on_metrics_collected(_tts(0.35))
        h.log.on_agent_state_changed(_agent_state("speaking", 1.8))
        h.log.on_agent_state_changed(_agent_state("listening", 4.0))
        (rec,) = h.records()
        self.assertEqual(rec["tts_ttfb_s"], 0.35)

    def test_first_exchange_without_a_child_turn_is_the_greeting(self):
        h = _Harness()
        h.log.on_agent_state_changed(_agent_state("thinking", 1.0))
        h.log.on_metrics_collected(_llm(0.4))
        h.log.on_metrics_collected(_tts(0.3))
        h.log.on_agent_state_changed(_agent_state("speaking", 1.8))
        h.log.on_agent_state_changed(_agent_state("listening", 4.0))
        (rec,) = h.records()
        self.assertEqual(rec["kind"], "greeting")
        self.assertIsNone(rec["total_s"])  # no child speech to measure from
        self.assertEqual(rec["reply_s"], 0.8)

    def test_typed_reply_after_the_greeting_is_text(self):
        h = _Harness()
        h.log.on_agent_state_changed(_agent_state("thinking", 1.0))
        h.log.on_agent_state_changed(_agent_state("speaking", 2.0))
        h.log.on_agent_state_changed(_agent_state("listening", 3.0))
        h.log.on_agent_state_changed(_agent_state("thinking", 9.0))
        h.log.on_agent_state_changed(_agent_state("speaking", 9.9))
        h.log.on_agent_state_changed(_agent_state("listening", 12.0))
        kinds = [r["kind"] for r in h.records()]
        self.assertEqual(kinds, ["greeting", "text"])
        self.assertIsNone(h.records()[1]["total_s"])

    def test_tool_round_is_reported_with_names_only(self):
        h = _Harness()
        h.log.on_user_state_changed(_user_state("listening", 50.0))
        h.log.on_agent_state_changed(_agent_state("thinking", 50.4))
        h.log.on_metrics_collected(_llm(0.45))
        h.log.on_function_tools_executed(_tools("record_engagement"))
        h.log.on_metrics_collected(_llm(0.9))
        h.log.on_agent_state_changed(_agent_state("speaking", 52.0))
        h.log.on_agent_state_changed(_agent_state("listening", 55.0))
        (rec,) = h.records()
        self.assertTrue(rec["tool_called"])
        self.assertEqual(rec["tools"], ["record_engagement"])
        self.assertEqual(rec["llm_rounds"], 2)
        self.assertEqual(rec["llm_ttft_s"], 0.45)  # the first call, the one before any tool
        self.assertNotIn("SECRET", h.lines[0])

    def test_cancelled_calls_do_not_count(self):
        h = _Harness()
        h.log.on_user_state_changed(_user_state("listening", 1.0))
        h.log.on_agent_state_changed(_agent_state("thinking", 1.5))
        h.log.on_metrics_collected(_llm(9.9, cancelled=True))
        h.log.on_metrics_collected(_tts(9.9, cancelled=True))
        h.log.on_metrics_collected(_llm(0.5))
        h.log.on_agent_state_changed(_agent_state("speaking", 2.5))
        h.log.on_agent_state_changed(_agent_state("listening", 4.0))
        (rec,) = h.records()
        self.assertEqual(rec["llm_ttft_s"], 0.5)
        self.assertEqual(rec["llm_rounds"], 1)
        self.assertIsNone(rec["tts_ttfb_s"])

    def test_an_exchange_that_never_spoke_is_reported_as_such(self):
        h = _Harness()
        h.log.on_user_state_changed(_user_state("listening", 1.0))
        h.log.on_agent_state_changed(_agent_state("thinking", 1.5))
        h.log.on_agent_state_changed(_agent_state("listening", 3.0))
        (rec,) = h.records()
        self.assertFalse(rec["spoke"])
        self.assertIsNone(rec["total_s"])
        self.assertIsNone(rec["reply_s"])

    def test_close_flushes_an_open_exchange_once(self):
        h = _Harness()
        h.log.on_agent_state_changed(_agent_state("thinking", 1.0))
        h.log.on_agent_state_changed(_agent_state("speaking", 2.0))
        h.log.on_close(None)
        h.log.on_close(None)
        self.assertEqual(len(h.lines), 1)

    def test_language_is_read_when_the_exchange_opens(self):
        h = _Harness("ar")
        h.log.on_agent_state_changed(_agent_state("thinking", 1.0))
        h.language = "en"
        h.log.on_agent_state_changed(_agent_state("speaking", 2.0))
        h.log.on_agent_state_changed(_agent_state("listening", 3.0))
        self.assertEqual(h.records()[0]["language"], "ar")

    def test_the_line_says_whether_a_fixed_fallback_line_was_used(self):
        count = [0]
        h = _Harness()
        h.log = TurnLatencyLogger(language=lambda: "en", fallback_count=lambda: count[0], emit=h.lines.append)
        h.log.on_agent_state_changed(_agent_state("thinking", 1.0))
        h.log.on_agent_state_changed(_agent_state("listening", 2.0))
        count[0] = 1  # the next exchange uses the fallback line
        h.log.on_agent_state_changed(_agent_state("thinking", 3.0))
        count[0] = 2
        h.log.on_agent_state_changed(_agent_state("speaking", 3.5))
        h.log.on_agent_state_changed(_agent_state("listening", 4.0))
        h.log.on_agent_state_changed(_agent_state("thinking", 5.0))
        h.log.on_agent_state_changed(_agent_state("listening", 6.0))
        self.assertEqual([r["fallback"] for r in h.records()], [False, True, False])

    def test_line_never_carries_text(self):
        h = _Harness()
        h.log.on_user_state_changed(_user_state("listening", 1.0))
        h.log.on_agent_state_changed(_agent_state("thinking", 1.5))
        h.log.on_agent_state_changed(_agent_state("speaking", 2.0))
        h.log.on_agent_state_changed(_agent_state("listening", 3.0))
        allowed = {
            "session_id", "kind", "language", "eou_delay_s", "stt_delay_s", "llm_ttft_s",
            "llm_rounds", "tts_ttfb_s", "total_s", "reply_s", "tool_called", "tools", "spoke", "fallback",
            "llm_model", "stt_model", "prompt_profile", "reasoning_effort",
        }
        self.assertEqual(set(h.records()[0]), allowed)

    def test_a_broken_event_never_raises(self):
        h = _Harness()
        h.log.on_metrics_collected(object())
        h.log.on_agent_state_changed(None)
        h.log.on_user_state_changed(None)
        h.log.on_function_tools_executed(None)
        self.assertEqual(h.lines, [])

    def test_attach_registers_every_event(self):
        events = []
        session = SimpleNamespace(on=lambda name, cb=None, **kw: events.append(name))
        TurnLatencyLogger().attach(session)
        self.assertEqual(
            sorted(events),
            ["agent_state_changed", "close", "function_tools_executed",
             "metrics_collected", "user_state_changed"],
        )


class LatencyLogSwitchTests(unittest.TestCase):
    def _enabled(self, **env):
        with mock.patch.dict(os.environ, env, clear=True):
            return latency_log_enabled()

    def test_unset_follows_debug_and_unset_debug_counts_as_off(self):
        self.assertFalse(self._enabled())
        self.assertTrue(self._enabled(DEBUG="1"))
        self.assertFalse(self._enabled(DEBUG="0"))

    def test_explicit_flag_wins_over_debug(self):
        self.assertTrue(self._enabled(LATENCY_LOG="1", DEBUG="0"))
        self.assertFalse(self._enabled(LATENCY_LOG="0", DEBUG="1"))

    def test_attach_helper_respects_the_switch(self):
        session = SimpleNamespace(on=mock.MagicMock())
        with mock.patch.dict(os.environ, {"LATENCY_LOG": "0"}):
            self.assertIsNone(latency_log.attach_latency_logger(session))
        session.on.assert_not_called()
        with mock.patch.dict(os.environ, {"LATENCY_LOG": "1"}):
            self.assertIsNotNone(latency_log.attach_latency_logger(session))
        self.assertEqual(session.on.call_count, 5)


class LatencyLogWiringTests(_WiringBase):
    async def test_session_gets_the_latency_logger_by_default_in_dev(self):
        await self.run_entrypoint()
        for event in ("metrics_collected", "agent_state_changed", "user_state_changed",
                      "function_tools_executed", "close"):
            self.assertIn(event, self.session.handlers)

    async def test_switch_off_attaches_nothing(self):
        os.environ["LATENCY_LOG"] = "0"
        await self.run_entrypoint()
        self.assertNotIn("metrics_collected", self.session.handlers)
