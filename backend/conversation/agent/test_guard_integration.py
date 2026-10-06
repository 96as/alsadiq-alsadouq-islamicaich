"""Integration tests: the compliance guards inside the live voice path.

Covers the join between the lead's guard modules (scripture_guard.py, turn_pipeline.py)
and the ElevenLabs voice work (tts_text.py, entrypoint.py):

- the speech cleaner replaces scripture-marked words (no brackets needed) with the
  neutral phrase, so TTS never speaks scripture;
- the order of the layers: session transform (cleaner) first, then tts_node (guards);
- the AI disclosure survives the merge (prompt rule and first-meeting line);
- the entrypoint passes the age band and the value index to the agent and routes typed
  messages through the turn guard.

No Quran or hadith text appears here. Placeholder words and bare Quranic mark characters
(U+06D6 and friends, which are punctuation of the script, not text) stand in for verses.

Run from backend/:  python manage.py test conversation.agent.test_guard_integration \
    --settings=config.settings_sqlite_test
"""
from __future__ import annotations

import asyncio
import logging
import unittest
from types import SimpleNamespace
from unittest import mock

from conversation.agent import scripture_guard
from conversation.agent import test_voice_wiring as vw
from conversation.agent.tts_text import (
    QURAN_PHRASE,
    TTSTextStream,
    clean_tts_stream,
    prepare_for_tts,
)

MARK = "ۖ"  # a waqf sign: one of the dense recitation marks the filter looks for
MARKED = "PLACEHOLDER" + MARK * 2  # a word carrying two marks: scripture-shaped
SINGLE = "PLACEHOLDER" + MARK  # a word with one mark: held, kept when nothing follows
EN = QURAN_PHRASE["en"]
AR = QURAN_PHRASE["ar"]
# A bracketed span longer than the old 400-character cap (a long verse with harakat).
LONG_SPAN = " ".join(["PLACEHOLDER"] * 80)
DECLINE_EN = scripture_guard.DECLINE_TEXT["en"].split(".")[0]

_agen = vw._agen
_collect = vw._collect


def stream(text: str, size: int | None, lang: str = "en") -> str:
    """Feed ``text`` to a TTSTextStream in chunks of ``size`` characters."""
    s = TTSTextStream(lang)
    if size is None:
        return s.feed(text) + s.flush()
    out = [s.feed(text[i:i + size]) for i in range(0, len(text), size)]
    return "".join(out) + s.flush()


def norm(text: str) -> str:
    return " ".join(text.split())


class ScriptureMarksInCleanerTests(unittest.TestCase):
    def test_marked_word_becomes_the_neutral_phrase(self):
        out = prepare_for_tts(f"before {MARKED} after", "en")
        self.assertEqual(norm(out), f"before {EN} after")
        self.assertNotIn("PLACEHOLDER", out)
        self.assertNotIn(MARK, out)

    def test_arabic_session_gets_the_arabic_phrase(self):
        out = prepare_for_tts(f"hello {MARKED} bye", "ar")
        self.assertIn(AR, out)
        self.assertNotIn(EN, out)

    def test_a_run_of_marked_words_gets_one_phrase(self):
        out = prepare_for_tts(f"start {MARKED} {MARKED} {MARKED} end", "en")
        self.assertEqual(norm(out), f"start {EN} end")

    def test_two_separate_runs_get_two_phrases(self):
        out = prepare_for_tts(f"a {MARKED} b and c {MARKED} d", "en")
        self.assertEqual(norm(out), f"a {EN} b and c {EN} d")

    def test_result_does_not_depend_on_how_the_text_is_chunked(self):
        text = f"first part {MARKED} {MARKED} then plain words {MARKED} the end."
        expected = norm(stream(text, None))
        self.assertEqual(expected, f"first part {EN} then plain words {EN} the end.")
        for size in (1, 2, 3, 5, 7, 11):
            self.assertEqual(norm(stream(text, size)), expected, size)

    def test_a_marked_word_at_the_very_end_is_still_replaced(self):
        self.assertEqual(norm(stream(f"the end {MARKED}", None)), f"the end {EN}")
        self.assertEqual(norm(stream(f"the end {MARKED}", 4)), f"the end {EN}")

    def test_a_lone_single_mark_word_is_not_treated_as_scripture(self):
        out = prepare_for_tts(f"say {SINGLE} to me", "en")
        self.assertNotIn(EN, out)
        self.assertIn("PLACEHOLDER", out)

    def test_ordinary_arabic_with_harakat_is_untouched(self):
        word = "مَرْحَبًا"  # an ordinary greeting
        out = prepare_for_tts(f"{word} {word}", "ar")
        self.assertEqual(out, f"{word} {word}")

    def test_plain_text_is_not_delayed_or_changed(self):
        s = TTSTextStream("en")
        self.assertEqual(s.feed("Hello "), "Hello ")
        self.assertEqual(s.feed("wor"), "")
        self.assertEqual(s.feed("ld and "), "world and ")

    def test_spacing_around_the_phrase_is_clean(self):
        out = prepare_for_tts(f"one {MARKED} two", "en")
        self.assertEqual(out, f"one {EN} two")  # single spaces, nothing glued

    def test_bracket_and_marks_in_one_reply_give_two_phrases(self):
        text = f"x {vw.OPEN}PLACEHOLDER{vw.CLOSE} y {MARKED} z"
        out = norm(stream(text, 3))
        self.assertEqual(out, f"x {EN} y {EN} z")

    def test_marked_word_split_by_a_flush_sentinel_is_still_replaced(self):
        async def run():
            async def source():
                yield f"before {MARKED}"
                yield object()  # a flush sentinel (not a str): passes through
                yield "after"

            return [c async for c in clean_tts_stream(source(), "en")]

        import asyncio
        pieces = asyncio.run(run())
        text = "".join(p for p in pieces if isinstance(p, str))
        self.assertEqual(norm(text), f"before {EN} after")
        self.assertEqual(sum(1 for p in pieces if not isinstance(p, str)), 1)

    def test_counter_counts_runs_and_logs_carry_no_text(self):
        scripture_guard.STATS.clear()
        with self.assertLogs("conversation.agent.tts_text", level=logging.WARNING) as cm:
            prepare_for_tts(f"a {MARKED} {MARKED} b {MARKED} c", "en")
        self.assertEqual(scripture_guard.STATS["speech_cleaner_scripture"], 2)
        self.assertNotIn("PLACEHOLDER", "\n".join(cm.output))


class LayerOrderTests(vw._WiringBase):
    """Cleaner (session transform) runs first, tts_node guards run on what it produced."""

    def make_agent(self, language="en"):
        return self.agent_class.AlSadiqAgent(db_session_id=1, child_id=2, language=language)

    async def _speak(self, agent, text):
        cleaned = vw.speech_tts_text_transform(lambda: agent.language)(_agen(text))
        return await _collect(agent.tts_node(cleaned, None))

    async def test_scripture_never_reaches_the_voice(self):
        agent = self.make_agent()
        spoken = await self._speak(agent, f"Listen {vw.OPEN}PLACEHOLDER{vw.CLOSE} and {MARKED} ok")
        self.assertNotIn("PLACEHOLDER", spoken)
        self.assertNotIn(vw.OPEN, spoken)
        self.assertNotIn(MARK, spoken)
        self.assertEqual(spoken.count(EN), 2)

    async def test_cleaner_output_is_what_the_guards_see(self):
        agent = self.make_agent()
        spoken = await self._speak(agent, "I am **12** years old")
        self.assertEqual(spoken.strip(), "I am twelve years old")

    async def test_unlicensed_attribution_is_replaced_in_the_spoken_reply(self):
        agent = self.make_agent()
        spoken = await self._speak(agent, "Nice day. The Prophet said to always be kind.")
        self.assertNotIn("The Prophet said", spoken)
        self.assertIn(scripture_guard.DECLINE_TEXT["en"].split(".")[0], spoken)

    async def test_attribution_licensed_by_a_served_item_passes(self):
        agent = self.make_agent()
        # a verse and a hadith that search_bank returned license both kinds
        agent._turn_items = [SimpleNamespace(type="verse"), SimpleNamespace(type="hadith")]
        spoken = await self._speak(agent, "Nice day. The Prophet said to always be kind.")
        self.assertIn("The Prophet said", spoken)

    async def test_transcript_gets_the_same_guards_as_the_speech(self):
        agent = self.make_agent()
        reply = f"Look {vw.OPEN}PLACEHOLDER{vw.CLOSE} and {MARKED} and the Prophet said be kind."
        shown = await _collect(agent.transcription_node(_agen(reply), None))
        self.assertNotIn("PLACEHOLDER", shown)
        self.assertNotIn("Prophet said", shown)

    async def test_timed_words_from_an_aligned_tts_pass_through(self):
        agent = self.make_agent()
        agent._use_tts_aligned_transcript = True
        timed = [vw._FakeTimedString("already "), vw._FakeTimedString("cleaned")]
        shown = await _collect(agent.transcription_node(_agen(*timed), None))
        self.assertEqual(shown, "already cleaned")

    async def test_markdown_does_not_hide_an_attribution_from_the_transcript(self):
        # Review fix: markdown is stripped before the transcript guard, as the cleaner does
        # before the speech guard, so the chat never shows what the audio declined.
        reply = "Nice day. The **Prophet** said to always be kind."
        spoken = await self._speak(self.make_agent(), reply)
        shown = await _collect(self.make_agent().transcription_node(_agen(reply), None))
        for out in (spoken, shown):
            self.assertNotIn("Prophet", out)
            self.assertIn(DECLINE_EN, out)


async def _one_speech(transform, *chunks) -> str:
    """Run the transform in its own task, as livekit runs each speech."""
    async def run():
        return await _collect(transform(_agen(*chunks)))

    return await asyncio.create_task(run())


class LongBracketedSpanTests(unittest.IsolatedAsyncioTestCase):
    """Review fix: the live per-speech bracket guard never resumes inside a span."""

    def chunks(self, text, size=7):
        return [text[i:i + size] for i in range(0, len(text), size)]

    async def test_a_span_longer_than_the_old_cap_is_never_spoken(self):
        transform = vw.speech_tts_text_transform("en")
        text = f"Listen {vw.OPEN}{LONG_SPAN}{vw.CLOSE} then be kind."
        out = await _one_speech(transform, *self.chunks(text))
        self.assertNotIn("PLACEHOLDER", out)
        self.assertIn("then be kind.", out)
        self.assertEqual(out.count(EN), 1)

    async def test_a_long_span_split_over_two_segments_of_one_speech(self):
        transform = vw.speech_tts_text_transform("en")

        async def speech():
            first = await _collect(transform(_agen(f"Listen {vw.OPEN}", LONG_SPAN[:500])))
            second = await _collect(transform(_agen(LONG_SPAN[500:], f"{vw.CLOSE} after")))
            return first + second

        out = await asyncio.create_task(speech())
        self.assertNotIn("PLACEHOLDER", out)
        self.assertIn("after", out)

    async def test_an_unclosed_bracket_silences_only_the_rest_of_its_own_speech(self):
        transform = vw.speech_tts_text_transform("en")
        with self.assertLogs("conversation.agent.tts_text", level=logging.WARNING) as cm:
            first = await _one_speech(transform, "Hi ", vw.OPEN, *self.chunks(LONG_SPAN),
                                      " more words")
        self.assertNotIn("PLACEHOLDER", first)
        self.assertNotIn("more words", first)
        self.assertNotIn("PLACEHOLDER", "\n".join(cm.output))  # logs carry no text
        second = await _one_speech(transform, "Hello again.")
        self.assertEqual(second.strip(), "Hello again.")


class DisclosureAndGuardWiringTests(vw._WiringBase):
    async def test_prompt_carries_the_ai_disclosure_rule(self):
        await self.run_entrypoint("en")
        self.assertIn("I'm Al-Sadiq, an AI friend, not a person.", self.agent._instructions)

    async def test_first_meeting_greeting_says_it_is_an_ai(self):
        for lang in ("en", "ar"):
            await self.run_entrypoint(lang, memory_text="")
            greeting = self.session.replies[-1]["instructions"]
            self.assertIn(self.entrypoint._FIRST_MEETING_AI_LINE[lang], greeting, lang)

    async def test_returning_child_greeting_has_no_disclosure_line(self):
        await self.run_entrypoint("en", memory_text="Remembers the cat.")
        greeting = self.session.replies[-1]["instructions"]
        self.assertNotIn(self.entrypoint._FIRST_MEETING_AI_LINE["en"], greeting)

    async def test_agent_gets_the_age_band_and_value_index_slots(self):
        await self.run_entrypoint("en")
        expected = self.entrypoint.age_band_from_birth_year(2016)
        self.assertEqual(self.agent._age_band, expected)
        self.assertIsNotNone(self.agent._value_index)  # EMPTY_INDEX when the bank is unreadable

    async def test_the_turn_guard_hooks_come_from_the_mixin(self):
        from conversation.agent.turn_pipeline import TurnGuardMixin

        cls = self.agent_class.AlSadiqAgent
        self.assertIs(cls.on_user_turn_completed, TurnGuardMixin.on_user_turn_completed)
        self.assertIs(cls.guard_speech, TurnGuardMixin.guard_speech)
        self.assertLess(cls.__mro__.index(TurnGuardMixin), cls.__mro__.index(vw._FakeAgent))

    async def test_typed_messages_go_through_the_turn_guard(self):
        await self.run_entrypoint("en")
        callback = self.session.start_kwargs["room_options"]["text_input"]["text_input_cb"]
        fake_session = SimpleNamespace(interrupt=mock.MagicMock())
        with (
            mock.patch.object(self.entrypoint, "_save_message",
                              mock.AsyncMock(return_value=SimpleNamespace(id=7))),
            mock.patch.object(self.agent, "reply_to_typed", mock.MagicMock()) as reply,
        ):
            callback(fake_session, SimpleNamespace(text="hello there"))
            import asyncio
            await asyncio.sleep(0)
        fake_session.interrupt.assert_called_once()
        reply.assert_called_once_with(fake_session, "hello there")

    async def test_long_typed_message_is_saved_capped_but_the_guard_gets_all_of_it(self):
        from conversation.agent.turn_pipeline import TYPED_TEXT_LLM_MAX_CHARS

        await self.run_entrypoint("en")
        callback = self.session.start_kwargs["room_options"]["text_input"]["text_input_cb"]
        fake_session = SimpleNamespace(interrupt=mock.MagicMock())
        long_text = "word " * 600
        save = mock.AsyncMock(return_value=SimpleNamespace(id=8))
        with (
            mock.patch.object(self.entrypoint, "_save_message", save),
            mock.patch.object(self.agent, "reply_to_typed", mock.MagicMock()) as reply,
        ):
            callback(fake_session, SimpleNamespace(text=long_text))
            import asyncio
            await asyncio.sleep(0)
        reply.assert_called_once_with(fake_session, long_text)  # the full text: the guard reads all of it
        saved = save.await_args.args[2]
        self.assertEqual(len(saved), TYPED_TEXT_LLM_MAX_CHARS)

    async def test_no_second_voice_and_no_bank_bracket_helper_remain(self):
        # 01 removed the get_islamic_reference tool, so the bracket helper from 07 is gone.
        self.assertFalse(hasattr(self.agent_class, "_format_islamic_reference"))
        self.assertFalse(hasattr(self.agent_class, "_query_islamic_references"))


@unittest.skipUnless(vw._HAS_LIVEKIT, "livekit-agents is not installed (or cannot be imported)")
class RealPipelineGuardTests(unittest.IsolatedAsyncioTestCase):
    """The same layers through livekit's real perform_tts_inference and the real agent."""

    def _agent(self, language="en"):
        from conversation.agent.agent_class import AlSadiqAgent

        return AlSadiqAgent(db_session_id=1, child_id=2, language=language)

    async def _speak(self, agent, *segments):
        from livekit.agents.types import FlushSentinel
        from livekit.agents.voice.generation import perform_tts_inference

        received: list[str] = []

        async def node(text, model_settings):  # what the agent's tts_node feeds the TTS
            received.append("".join([piece async for piece in agent.guard_speech(text)]))
            return
            yield  # an (empty) async generator

        async def source():
            for i, segment in enumerate(segments):
                if i:
                    yield FlushSentinel()
                yield segment

        task, _data = perform_tts_inference(
            node=node, input=source(), model_settings=SimpleNamespace(),
            text_transforms=[vw.speech_tts_text_transform(lambda: agent.language)],
        )
        await task
        return received

    async def test_marks_and_brackets_never_reach_the_tts_input(self):
        received = await self._speak(
            self._agent(), f"Listen {vw.OPEN}PLACEHOLDER{vw.CLOSE} and {MARKED} then 12 cats")
        joined = " ".join(received)
        self.assertNotIn("PLACEHOLDER", joined)
        self.assertNotIn(MARK, joined)
        self.assertEqual(joined.count(EN), 2)
        self.assertIn("twelve cats", joined)

    async def test_unlicensed_attribution_is_declined_in_the_tts_input(self):
        received = await self._speak(self._agent(), "Hello. The Prophet said to be kind.")
        self.assertNotIn("The Prophet said", " ".join(received))

    async def test_real_timed_words_pass_through_the_transcript_node(self):
        from livekit.agents.types import TimedString

        agent = self._agent()
        agent._use_tts_aligned_transcript = True
        timed = [TimedString("kept "), TimedString("as is")]
        shown = await _collect(agent.transcription_node(_agen(*timed), None))
        self.assertEqual(shown, "kept as is")

    async def test_a_long_bracketed_span_never_reaches_the_tts_input(self):
        received = await self._speak(
            self._agent(), f"Listen {vw.OPEN}{LONG_SPAN[:500]}",
            f"{LONG_SPAN[500:]}{vw.CLOSE} then be kind.")
        joined = " ".join(received)
        self.assertNotIn("PLACEHOLDER", joined)
        self.assertIn("then be kind.", joined)

    async def test_real_transcript_declines_a_markdown_wrapped_attribution(self):
        for reply in ("Nice. The **Prophet** said be kind.", "Nice. The _Prophet_ said be kind."):
            shown = await _collect(self._agent().transcription_node(_agen(reply), None))
            self.assertNotIn("Prophet", shown, reply)
            self.assertIn(DECLINE_EN, shown, reply)

    async def test_real_transcript_is_guarded(self):
        agent = self._agent()
        shown = await _collect(agent.transcription_node(
            _agen(f"A {vw.OPEN}PLACEHOLDER{vw.CLOSE} B {MARKED} C **bold**"), None))
        self.assertNotIn("PLACEHOLDER", shown)
        self.assertNotIn(MARK, shown)
        self.assertIn("bold", shown)
        self.assertNotIn("**", shown)


if __name__ == "__main__":
    unittest.main()
