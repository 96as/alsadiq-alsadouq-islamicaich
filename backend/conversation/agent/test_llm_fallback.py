"""Tests for the fixed line said when the LLM fails (llm_fallback.py, AlSadiqAgent.llm_node).

The agent is built against the same fake livekit as test_voice_wiring.py; the default
llm_node is replaced by a fake stream that raises like livekit's APIStatusError (429) or
APIConnectionError. A real-livekit check runs only where livekit-agents is installed.

Run from backend/:  python manage.py test conversation.agent.test_llm_fallback \
    --settings=config.settings_sqlite_test
"""
from __future__ import annotations

import importlib.util
import unittest
from types import SimpleNamespace
from unittest import mock

from conversation.agent import llm_fallback
from conversation.agent.llm_fallback import (
    FALLBACK_LINES,
    KIND_GREETING,
    KIND_RETRY,
    KIND_SAFETY,
    classify_turn,
    fallback_line,
)
from conversation.agent.test_voice_wiring import _import_agent_modules_against_fake_livekit


class APIError(Exception):
    """Same name and module family as livekit.agents.APIError (matched by name)."""


APIError.__module__ = "livekit.agents._exceptions"


class APIStatusError(APIError):
    def __init__(self, message="rate limited", status_code=429):
        super().__init__(message)
        self.status_code = status_code


class APIConnectionError(APIError):
    pass


APIStatusError.__module__ = APIConnectionError.__module__ = "livekit.agents._exceptions"


def _msg(role, text):
    return SimpleNamespace(type="message", role=role, text_content=text)


def _ctx(*items):
    return SimpleNamespace(items=list(items))


def _chunk(text):
    return SimpleNamespace(id="c", delta=SimpleNamespace(role="assistant", content=text, tool_calls=[]))


def _tool_chunk():
    return SimpleNamespace(id="c", delta=SimpleNamespace(role="assistant", content=None, tool_calls=[object()]))


def _stream(*items, then_raise=None):
    async def gen():
        for item in items:
            yield item
        if then_raise is not None:
            raise then_raise
    return gen()


async def _collect(stream):
    return [piece async for piece in stream]


class FallbackTextTests(unittest.TestCase):
    def test_every_kind_has_both_languages_and_no_scripture_marks(self):
        for kind in (KIND_GREETING, KIND_SAFETY, KIND_RETRY):
            for lang in ("ar", "en"):
                line = FALLBACK_LINES[kind][lang]
                self.assertTrue(line.strip())
                self.assertNotIn("﴿", line)
                self.assertNotIn("﴾", line)
                self.assertLess(len(line), 140)  # spoken, so short

    def test_the_safety_line_comforts_and_points_to_a_grown_up_naming_nobody(self):
        en = fallback_line(KIND_SAFETY, "en").lower()
        self.assertIn("grown-up", en)
        for name in ("mom", "dad", "parent", "teacher", "mother", "father"):
            self.assertNotIn(name, en)
        ar = fallback_line(KIND_SAFETY, "ar")
        for word in ("أمك", "أبوك", "والد", "معلم"):
            self.assertNotIn(word, ar)

    def test_the_greeting_line_says_it_is_an_ai(self):
        self.assertIn("AI", fallback_line(KIND_GREETING, "en"))
        self.assertIn("ذكاء اصطناعي", fallback_line(KIND_GREETING, "ar"))

    def test_an_unknown_language_falls_back_to_english(self):
        self.assertEqual(fallback_line(KIND_RETRY, "fr"), FALLBACK_LINES[KIND_RETRY]["en"])


class ClassifyTurnTests(unittest.TestCase):
    def test_no_child_message_yet_is_the_greeting(self):
        self.assertEqual(classify_turn(_ctx(_msg("system", "persona")), safety_turn=False), KIND_GREETING)

    def test_a_child_message_is_a_retry(self):
        self.assertEqual(classify_turn(_ctx(_msg("user", "hi")), safety_turn=False), KIND_RETRY)

    def test_a_safety_turn_is_safety_even_for_the_greeting_shape(self):
        self.assertEqual(classify_turn(_ctx(_msg("user", "x")), safety_turn=True), KIND_SAFETY)

    def test_a_follow_up_round_after_spoken_words_stays_quiet(self):
        ctx = _ctx(_msg("user", "hi"), _msg("assistant", "Hello there"))
        self.assertIsNone(classify_turn(ctx, safety_turn=False))

    def test_a_tool_item_is_not_a_message(self):
        ctx = _ctx(_msg("user", "hi"), SimpleNamespace(type="function_call_output", output="ok"))
        self.assertEqual(classify_turn(ctx, safety_turn=False), KIND_RETRY)


class LlmNodeTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.agent_class, _ = _import_agent_modules_against_fake_livekit(self)

    def _agent(self, language="en"):
        return self.agent_class.AlSadiqAgent(db_session_id=5, child_id=2, language=language)

    async def _run(self, agent, chat_ctx, stream):
        factory = mock.Mock(return_value=stream)
        with mock.patch.object(self.agent_class.Agent.default, "llm_node", factory, create=True):
            return await _collect(agent.llm_node(chat_ctx, [], None))

    async def test_a_normal_stream_passes_through_unchanged(self):
        agent = self._agent()
        chunks = [_chunk("Hello"), "plain str", _tool_chunk(), _chunk(" there")]
        out = await self._run(agent, _ctx(_msg("user", "hi")), _stream(*chunks))
        self.assertEqual(out, chunks)
        self.assertEqual(agent.llm_fallback_count, 0)

    async def test_a_429_before_any_text_says_the_retry_line_in_english(self):
        agent = self._agent("en")
        with self.assertLogs(llm_fallback.logger, "WARNING") as logs:
            out = await self._run(
                agent, _ctx(_msg("user", "tell me about my day")),
                _stream(then_raise=APIStatusError(status_code=429)),
            )
        self.assertEqual(out, [FALLBACK_LINES[KIND_RETRY]["en"]])
        self.assertEqual(agent.llm_fallback_count, 1)
        text = "\n".join(logs.output)
        self.assertIn("session 5", text)
        self.assertIn("APIStatusError", text)
        self.assertNotIn("my day", text)  # the child's words never reach the log

    async def test_a_connection_error_says_the_retry_line_in_arabic(self):
        agent = self._agent("ar")
        out = await self._run(
            agent, _ctx(_msg("user", "مرحبا كيف حالك")),
            _stream(then_raise=APIConnectionError("down")),
        )
        self.assertEqual(out, [FALLBACK_LINES[KIND_RETRY]["ar"]])

    async def test_the_line_follows_the_language_the_child_used(self):
        agent = self._agent("ar")  # session Arabic, child wrote English
        out = await self._run(
            agent, _ctx(_msg("user", "can you help me")),
            _stream(then_raise=APIConnectionError("down")),
        )
        self.assertEqual(out, [FALLBACK_LINES[KIND_RETRY]["en"]])

    async def test_the_greeting_failing_says_the_fixed_hello_in_the_session_language(self):
        for lang in ("ar", "en"):
            agent = self._agent(lang)
            out = await self._run(
                agent, _ctx(_msg("system", "persona")),
                _stream(then_raise=APIStatusError(status_code=429)),
            )
            self.assertEqual(out, [FALLBACK_LINES[KIND_GREETING][lang]])

    async def test_a_safety_turn_failing_says_the_comfort_line(self):
        for lang, child in (("en", "i feel so sad"), ("ar", "أنا حزين جدا")):
            agent = self._agent(lang)
            agent._safety_turn = True
            out = await self._run(
                agent, _ctx(_msg("user", child)),
                _stream(then_raise=APIStatusError(status_code=429)),
            )
            self.assertEqual(out, [FALLBACK_LINES[KIND_SAFETY][lang]])

    async def test_a_safety_turn_failing_in_the_tool_follow_up_still_comforts(self):
        agent = self._agent("en")
        agent._safety_turn = True
        ctx = _ctx(_msg("user", "i feel so sad"), SimpleNamespace(type="function_call_output", output="ok"))
        out = await self._run(agent, ctx, _stream(then_raise=APIConnectionError("down")))
        self.assertEqual(out, [FALLBACK_LINES[KIND_SAFETY]["en"]])

    async def test_an_error_after_text_started_adds_nothing(self):
        agent = self._agent()
        first = _chunk("Well, ")
        with self.assertLogs(llm_fallback.logger, "WARNING"):
            out = await self._run(
                agent, _ctx(_msg("user", "hi")),
                _stream(first, then_raise=APIConnectionError("dropped")),
            )
        self.assertEqual(out, [first])
        self.assertEqual(agent.llm_fallback_count, 0)

    async def test_a_tool_call_only_round_that_errors_falls_back(self):
        agent = self._agent()
        tool = _tool_chunk()
        out = await self._run(
            agent, _ctx(_msg("user", "hi")),
            _stream(tool, then_raise=APIConnectionError("dropped")),
        )
        self.assertEqual(out, [tool, FALLBACK_LINES[KIND_RETRY]["en"]])

    async def test_a_failed_follow_up_round_after_the_assistant_spoke_stays_quiet(self):
        agent = self._agent()
        ctx = _ctx(_msg("user", "hi"), _msg("assistant", "Hello!"))
        out = await self._run(agent, ctx, _stream(then_raise=APIStatusError(status_code=500)))
        self.assertEqual(out, [])

    async def test_other_exceptions_are_not_swallowed(self):
        agent = self._agent()
        with self.assertRaises(ValueError):
            await self._run(agent, _ctx(_msg("user", "hi")), _stream(then_raise=ValueError("bug")))

    async def test_the_fixed_line_is_a_plain_string_the_speech_and_chat_nodes_accept(self):
        agent = self._agent("en")
        out = await self._run(
            agent, _ctx(_msg("user", "hi")), _stream(then_raise=APIStatusError(status_code=429)),
        )
        self.assertTrue(all(isinstance(piece, str) for piece in out))


@unittest.skipUnless(importlib.util.find_spec("livekit.agents"), "livekit-agents is not installed")
class RealLivekitErrorTests(unittest.IsolatedAsyncioTestCase):
    async def test_real_api_errors_are_recognised(self):
        from livekit.agents import APIConnectionError as RealConn
        from livekit.agents import APIStatusError as RealStatus
        from livekit.agents import APITimeoutError as RealTimeout

        for exc in (RealStatus("rate limited", status_code=429), RealConn("down"), RealTimeout("slow")):
            self.assertTrue(llm_fallback.is_api_error(exc), type(exc).__name__)
        self.assertFalse(llm_fallback.is_api_error(ValueError("x")))

        out = await _collect(llm_fallback.with_llm_fallback(
            _stream(then_raise=RealStatus("rate limited", status_code=429)),
            chat_ctx=_ctx(_msg("user", "hi")), language_for=lambda kind: "en",
            safety_turn=lambda: False, session_id=1,
        ))
        self.assertEqual(out, [FALLBACK_LINES[KIND_RETRY]["en"]])


if __name__ == "__main__":
    unittest.main()
