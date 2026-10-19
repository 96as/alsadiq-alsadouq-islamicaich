"""Tests for forwarding ElevenLabs character timings to the avatar's lip sync (lipsync_timeline.py,
LIPSYNC_TIMELINE).

- The timeline, plugin-patch, tts_factory and wiring tests run everywhere: they use a tiny fake of
  livekit (the same one test_voice_wiring uses) and a fake ElevenLabs plugin.
- RealLivekitTests run only where livekit-agents 1.5.1 and the ElevenLabs plugin are installed.

No scripture appears here; the Arabic words are ordinary vocabulary.

Run from backend/:  python manage.py test conversation.agent.test_lipsync_timeline \
    --settings=config.settings_sqlite_test
"""
from __future__ import annotations

import asyncio
import importlib.util
import json
import os
import sys
import unittest
from types import ModuleType, SimpleNamespace
from unittest import mock

from conversation.agent import lipsync_timeline as lt
from conversation.agent import tts_factory
from conversation.agent.test_voice_wiring import _ELEVEN_ENV, _FakeAgent, _WiringBase


class _TimedString(str):
    """Stands in for livekit.agents.types.TimedString (a str that takes attributes)."""

    def __new__(cls, text, start_time=None, end_time=None):
        obj = super().__new__(cls, text)
        obj.start_time = start_time
        obj.end_time = end_time
        return obj


class _Frame:
    def __init__(self, duration_s=0.1, words=None):
        self.duration = duration_s
        self.userdata = {} if words is None else {lt.USERDATA_KEY: words}


def _word(text, chars):
    """A word carrying its characters, the way the patched plugin produces it."""
    w = _TimedString(text)
    w.char_ms = chars
    return w


def _spread(text, start=0, step=50, dur=50):
    return [(ch, start + i * step, dur) for i, ch in enumerate(text)]


async def _agen(*items, error=None):
    for item in items:
        yield item
    if error is not None:
        raise error


class _Room:
    def __init__(self, fail=False):
        self.publish_data = mock.AsyncMock(side_effect=RuntimeError("down") if fail else None)
        self.local_participant = SimpleNamespace(publish_data=self.publish_data)

    def messages(self):
        out = []
        for call in self.publish_data.await_args_list:
            self_check = call.kwargs
            assert self_check["topic"] == lt.TOPIC and self_check["reliable"] is True
            out.append(json.loads(call.args[0].decode("utf-8")))
        return out


def _fresh_logs():
    lt._logged.clear()


# ---------------------------------------------------------------------------
# enabled()
# ---------------------------------------------------------------------------


class EnabledTests(unittest.TestCase):
    def test_on_unless_turned_off(self):
        for value in (None, "", "1", "on"):
            env = {k: v for k, v in os.environ.items() if k != "LIPSYNC_TIMELINE"}
            if value is not None:
                env["LIPSYNC_TIMELINE"] = value
            with mock.patch.dict(os.environ, env, clear=True):
                self.assertTrue(lt.enabled(), value)

    def test_off_values(self):
        for value in ("0", "off", "OFF", "false", " No "):
            env = {k: v for k, v in os.environ.items() if k != "LIPSYNC_TIMELINE"}
            if value is not None:
                env["LIPSYNC_TIMELINE"] = value
            with mock.patch.dict(os.environ, env, clear=True):
                self.assertFalse(lt.enabled(), value)


# ---------------------------------------------------------------------------
# The plugin patch (against a fake of the plugin's private function)
# ---------------------------------------------------------------------------


def _fake_to_timed_words(text, start_times_ms, durations_ms, flush=False):
    """Same contract as the plugin's: words are text[start:end] for consecutive word starts, the last
    word stays in the remaining text until flush."""
    if not text:
        return [], ""
    stamps = list(start_times_ms) + [start_times_ms[-1] + durations_ms[-1]]
    starts = [0] + [i + 1 for i, ch in enumerate(text) if ch == " " and i + 1 < len(text)]
    words = []
    end = 0
    for a, b in zip(starts[:-1], starts[1:]):
        words.append(_TimedString(text[a:b], stamps[a] / 1000, stamps[b] / 1000))
        end = b
    if flush:
        words.append(_TimedString(text[end:], stamps[end] / 1000, stamps[-1] / 1000))
        end = len(text)
    return words, text[end:]


def _fake_plugin_modules(version="1.5.1"):
    tts_mod = ModuleType("livekit.plugins.elevenlabs.tts")
    tts_mod._to_timed_words = _fake_to_timed_words
    version_mod = ModuleType("livekit.plugins.elevenlabs.version")
    version_mod.__version__ = version
    pkg = ModuleType("livekit.plugins.elevenlabs")
    pkg.tts = tts_mod
    pkg.version = version_mod
    plugins = ModuleType("livekit.plugins")
    plugins.elevenlabs = pkg
    return tts_mod, {
        "livekit": ModuleType("livekit"),
        "livekit.plugins": plugins,
        "livekit.plugins.elevenlabs": pkg,
        "livekit.plugins.elevenlabs.tts": tts_mod,
        "livekit.plugins.elevenlabs.version": version_mod,
    }


class PluginPatchTests(unittest.TestCase):
    def setUp(self):
        _fresh_logs()
        p = mock.patch.object(lt, "_patched", False)
        p.start()
        self.addCleanup(p.stop)

    def _install(self, version="1.5.1"):
        self.tts_mod, modules = _fake_plugin_modules(version)
        p = mock.patch.dict(sys.modules, modules)
        p.start()
        self.addCleanup(p.stop)
        return lt.install_char_timing_patch()

    def test_words_carry_their_characters(self):
        self.assertTrue(self._install())
        text = "ab cd e"
        starts = [0, 10, 20, 30, 45, 60, 70]
        durs = [10, 10, 10, 15, 15, 10, 10]
        words, rest = self.tts_mod._to_timed_words(text, starts, durs)
        self.assertEqual([str(w) for w in words], ["ab ", "cd "])
        self.assertEqual(rest, "e")
        self.assertEqual(words[0].char_ms, [("a", 0, 10), ("b", 10, 10), (" ", 20, 10)])
        self.assertEqual(words[1].char_ms, [("c", 30, 15), ("d", 45, 15), (" ", 60, 10)])
        # The words' own timings and text are what the plugin made.
        self.assertEqual(words[0].start_time, 0.0)
        self.assertEqual(words[0].end_time, 0.03)

    def test_flush_gives_the_last_word_its_characters_too(self):
        self.assertTrue(self._install())
        words, rest = self.tts_mod._to_timed_words("ab c", [0, 5, 10, 15], [5, 5, 5, 5], flush=True)
        self.assertEqual(rest, "")
        self.assertEqual([w.char_ms[0][0] for w in words], ["a", "c"])
        self.assertEqual(words[-1].char_ms, [("c", 15, 5)])

    def test_arabic_characters_and_multi_codepoint_marks(self):
        self.assertTrue(self._install())
        text = "مرحبا بك"
        starts = list(range(0, 10 * len(text), 10))
        words, _ = self.tts_mod._to_timed_words(text, starts, [10] * len(text), flush=True)
        got = "".join(c for w in words for c, _, _ in w.char_ms)
        self.assertEqual(got, text)

    def test_idempotent(self):
        self.assertTrue(self._install())
        first = self.tts_mod._to_timed_words
        self.assertTrue(lt.install_char_timing_patch())
        self.assertIs(self.tts_mod._to_timed_words, first)
        self.assertTrue(first._lipsync_wrapped)

    def test_a_second_install_in_a_fresh_process_state_does_not_double_wrap(self):
        self.assertTrue(self._install())
        wrapped = self.tts_mod._to_timed_words
        with mock.patch.object(lt, "_patched", False):
            self.assertTrue(lt.install_char_timing_patch())
        self.assertIs(self.tts_mod._to_timed_words, wrapped)

    def test_other_plugin_versions_are_left_alone(self):
        self.assertFalse(self._install("1.6.0"))
        self.assertIs(self.tts_mod._to_timed_words, _fake_to_timed_words)

    def test_no_plugin_is_a_quiet_false(self):
        with mock.patch.dict(sys.modules, {"livekit.plugins.elevenlabs": None}):
            with self.assertLogs(lt.logger, level="WARNING"):
                self.assertFalse(lt.install_char_timing_patch())

    def test_a_text_the_timings_do_not_match_gives_no_characters_and_no_error(self):
        self.assertTrue(self._install())
        # Fewer timings than text: the plugin never does this, but it must not raise, and the words
        # that cannot be matched get no characters.
        words = [_TimedString("ab "), _TimedString("cd ")]
        lt._attach_chars(words, "ab cd ", [0, 10, 20], [10, 10, 10])
        self.assertEqual(len(words[0].char_ms), 3)
        self.assertFalse(hasattr(words[1], "char_ms"))
        words = [_TimedString("xx ")]
        lt._attach_chars(words, "ab cd ", [0] * 6, [1] * 6)
        self.assertFalse(hasattr(words[0], "char_ms"))
        with mock.patch.object(lt, "_attach_chars", side_effect=ValueError("boom")):
            with self.assertLogs(lt.logger, level="WARNING"):
                words, _ = self.tts_mod._to_timed_words("ab cd", [0, 1, 2, 3, 4], [1] * 5, flush=True)
        self.assertEqual([str(w) for w in words], ["ab ", "cd"])

    def test_empty_text(self):
        self.assertTrue(self._install())
        self.assertEqual(self.tts_mod._to_timed_words("", [], []), ([], ""))


# ---------------------------------------------------------------------------
# tap() and the messages
# ---------------------------------------------------------------------------


class TapTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        _fresh_logs()
        self.room = _Room()
        self.sp = "speech_1"
        self.tl = lt.LipsyncTimeline(self.room, lang=lambda: "ar", speech_id=lambda: self.sp)

    async def tap_all(self, *frames):
        out = [f async for f in self.tl.tap(_agen(*frames))]
        await self.tl.flush()
        return out

    async def asyncTearDown(self):
        await self.tl.aclose()

    async def test_frames_pass_through_unchanged_and_in_order(self):
        frames = [_Frame(0.02, [_word("ab ", _spread("ab "))]), _Frame(0.02), _Frame(0.02)]
        before = [dict(f.userdata) for f in frames]
        out = await self.tap_all(*frames)
        self.assertEqual(len(out), 3)
        for a, b in zip(out, frames):
            self.assertIs(a, b)
        self.assertEqual([f.userdata for f in frames], before)

    async def test_publishes_characters_on_the_topic(self):
        await self.tap_all(_Frame(0.1, [_word("ab ", _spread("ab ")), _word("cd", _spread("cd", 150))]))
        (msg,) = self.room.messages()
        self.assertEqual(msg["v"], 1)
        self.assertEqual(msg["sp"], "speech_1")
        self.assertEqual(msg["seq"], 0)
        self.assertEqual(msg["lang"], "ar")
        self.assertEqual(msg["t"][0], ["a", 0, 50])
        self.assertEqual([t[0] for t in msg["t"]], list("ab cd"))
        self.assertEqual(msg["t"][3], ["c", 150, 50])

    async def test_json_is_compact_utf8_and_carries_no_extra_fields(self):
        await self.tap_all(_Frame(0.1, [_word("مر", _spread("مر"))]))
        raw = self.room.publish_data.await_args.args[0]
        self.assertIsInstance(raw, bytes)
        text = raw.decode("utf-8")
        self.assertNotIn(" ", text)
        self.assertIn("مر"[0], text)
        self.assertEqual(set(json.loads(text)), {"v", "sp", "seq", "lang", "t"})

    async def test_a_second_call_of_the_same_speech_continues_after_the_audio_so_far(self):
        # One speech, two tts_node calls (two ElevenLabs contexts, each counting from 0).
        await self.tap_all(_Frame(0.2, [_word("ab ", _spread("ab "))]), _Frame(0.3))
        await self.tap_all(_Frame(0.1, [_word("cd", _spread("cd"))]))
        first, second = self.room.messages()
        self.assertEqual((first["seq"], second["seq"]), (0, 1))
        self.assertEqual(first["t"][0][1], 0)
        # 0.2 s + 0.3 s of audio came before: 500 ms.
        self.assertEqual(second["t"][0], ["c", 500, 50])
        self.assertEqual(second["t"][1], ["d", 550, 50])

    async def test_a_new_speech_starts_at_zero_with_seq_zero(self):
        await self.tap_all(_Frame(0.2, [_word("ab", _spread("ab"))]))
        self.sp = "speech_2"
        await self.tap_all(_Frame(0.2, [_word("cd", _spread("cd"))]))
        first, second = self.room.messages()
        self.assertEqual((second["sp"], second["seq"], second["t"][0][1]), ("speech_2", 0, 0))

    async def test_an_interrupted_call_still_counts_the_audio_it_produced(self):
        gen = self.tl.tap(_agen(_Frame(0.25), _Frame(0.25)))
        await gen.__anext__()
        await gen.aclose()
        await self.tap_all(_Frame(0.1, [_word("x", _spread("x"))]))
        (msg,) = self.room.messages()
        self.assertEqual(msg["t"][0][1], 250)

    async def test_long_timelines_are_split_in_packets_of_at_most_120(self):
        chars = _spread("a" * 300, step=10, dur=10)
        await self.tap_all(_Frame(1.0, [_word("a" * 300, chars)]))
        msgs = self.room.messages()
        self.assertEqual([len(m["t"]) for m in msgs], [120, 120, 60])
        self.assertEqual([m["seq"] for m in msgs], [0, 1, 2])
        self.assertEqual(msgs[1]["t"][0][1], 1200)
        # Order and content survive the split.
        self.assertEqual([t[1] for m in msgs for t in m["t"]], [i * 10 for i in range(300)])

    async def test_frames_without_timings_publish_nothing(self):
        await self.tap_all(_Frame(0.1), _Frame(0.1, []), _Frame(0.1, [_TimedString("plain")]))
        self.assertEqual(self.room.messages(), [])

    async def test_language_code_is_ar_or_en(self):
        for given, expected in (("ar", "ar"), ("en", "en"), ("en-US", "en"), ("fr", "ar"), (None, "ar")):
            room = _Room()
            tl = lt.LipsyncTimeline(room, lang=lambda g=given: g, speech_id=lambda: "s")
            async for _ in tl.tap(_agen(_Frame(0.1, [_word("a", _spread("a"))]))):
                pass
            await tl.flush()
            self.assertEqual(room.messages()[0]["lang"], expected, given)
            await tl.aclose()

    async def test_publishing_does_not_block_the_audio(self):
        gate = asyncio.Event()

        async def slow(*_a, **_k):
            await gate.wait()

        self.room.publish_data.side_effect = slow
        got = []
        async for f in self.tl.tap(_agen(*[_Frame(0.1, [_word("a", _spread("a"))]) for _ in range(5)])):
            got.append(f)
        self.assertEqual(len(got), 5)  # all frames came through while publishing is still stuck
        gate.set()
        await self.tl.flush()

    async def test_a_failing_publish_is_logged_once_and_the_frames_keep_flowing(self):
        room = _Room(fail=True)
        tl = lt.LipsyncTimeline(room, speech_id=lambda: "s")
        frames = [_Frame(0.1, [_word("a", _spread("a"))]) for _ in range(4)]
        with self.assertLogs(lt.logger, level="WARNING") as logs:
            out = [f async for f in tl.tap(_agen(*frames))]
            await tl.flush()
        self.assertEqual(len(out), 4)
        self.assertEqual(len([m for m in logs.output if "publish_data failed" in m]), 1)
        self.assertEqual(room.publish_data.await_count, 4)
        await tl.aclose()

    async def test_odd_frames_never_raise(self):
        class Odd:
            duration = "not a number"
            userdata = {lt.USERDATA_KEY: [_word("a", [("a", "x", None)])]}

        class NoUserdata:
            pass

        class BadUserdata:
            userdata = 5

        frames = [Odd(), NoUserdata(), BadUserdata(), _Frame(0.1, [_word("a", _spread("a"))])]
        with self.assertLogs(lt.logger, level="WARNING"):
            out = await self.tap_all(*frames)
        self.assertEqual(len(out), 4)
        self.assertEqual(len(self.room.messages()), 1)  # the good frame still published

    async def test_an_error_from_upstream_still_reaches_the_caller(self):
        class Boom(Exception):
            pass

        seen = []
        with self.assertRaises(Boom):
            async for f in self.tl.tap(_agen(_Frame(0.1), error=Boom())):
                seen.append(f)
        self.assertEqual(len(seen), 1)

    async def test_speech_id_falls_back_to_the_session_then_to_a_question_mark(self):
        tl = lt.LipsyncTimeline(self.room, speech_id=lambda: None)
        tl._session = SimpleNamespace(current_speech=SimpleNamespace(id="speech_9"))
        self.assertEqual(tl._current_speech_id(), "speech_9")
        tl._session = None
        self.assertEqual(tl._current_speech_id(), "?")
        # The default getter (livekit's speech handle) must not raise when there is no speech.
        tl2 = lt.LipsyncTimeline(self.room)
        self.assertEqual(tl2._current_speech_id(), "?")

    async def test_only_the_last_few_speeches_are_remembered(self):
        for i in range(20):
            self.sp = f"s{i}"
            await self.tap_all(_Frame(0.1))
        self.assertLessEqual(len(self.tl._speeches), 8)


# ---------------------------------------------------------------------------
# go and stop
# ---------------------------------------------------------------------------


class _Handle:
    def __init__(self, sp, interrupted=False):
        self.id = sp
        self.interrupted = interrupted
        self.callbacks = []

    def add_done_callback(self, cb):
        self.callbacks.append(cb)

    def finish(self):
        for cb in self.callbacks:
            cb(self)


class AgentStateTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        _fresh_logs()
        self.room = _Room()
        self.tl = lt.LipsyncTimeline(self.room, speech_id=lambda: "x")
        self.session = SimpleNamespace(current_speech=None)

    async def asyncTearDown(self):
        await self.tl.aclose()

    def state(self, new):
        self.tl.on_agent_state(SimpleNamespace(new_state=new, old_state="thinking"), self.session)

    async def test_speaking_publishes_go_with_the_speech_id(self):
        self.session.current_speech = _Handle("speech_7")
        self.state("speaking")
        await self.tl.flush()
        self.assertEqual(self.room.messages(), [{"v": 1, "sp": "speech_7", "go": 1}])

    async def test_other_states_publish_nothing(self):
        self.session.current_speech = _Handle("speech_7")
        for s in ("listening", "thinking", "idle", "initializing"):
            self.state(s)
        await self.tl.flush()
        self.assertEqual(self.room.messages(), [])

    async def test_no_current_speech_publishes_nothing(self):
        self.state("speaking")
        await self.tl.flush()
        self.assertEqual(self.room.messages(), [])

    async def test_the_same_speech_gets_one_go(self):
        self.session.current_speech = _Handle("speech_7")
        self.state("speaking")
        self.state("speaking")
        await self.tl.flush()
        self.assertEqual(len(self.room.messages()), 1)

    async def test_an_interrupted_speech_sends_stop_when_it_is_done(self):
        handle = self.session.current_speech = _Handle("speech_7", interrupted=True)
        self.state("speaking")
        handle.finish()
        await self.tl.flush()
        self.assertEqual(self.room.messages()[-1], {"v": 1, "sp": "speech_7", "stop": 1})

    async def test_a_speech_that_finished_normally_sends_no_stop(self):
        handle = self.session.current_speech = _Handle("speech_7", interrupted=False)
        self.state("speaking")
        handle.finish()
        await self.tl.flush()
        self.assertEqual(self.room.messages(), [{"v": 1, "sp": "speech_7", "go": 1}])

    async def test_messages_keep_their_order(self):
        self.session.current_speech = _Handle("a")
        self.state("speaking")
        async for _ in self.tl.tap(_agen(_Frame(0.1, [_word("x", _spread("x"))]))):
            pass
        await self.tl.flush()
        kinds = ["go" if "go" in m else "t" for m in self.room.messages()]
        self.assertEqual(kinds, ["go", "t"])

    async def test_a_broken_event_never_raises(self):
        self.tl.on_agent_state(object(), None)
        self.tl.on_agent_state(SimpleNamespace(new_state="speaking"), SimpleNamespace(current_speech=5))
        await self.tl.flush()


# ---------------------------------------------------------------------------
# tts_factory: the flag
# ---------------------------------------------------------------------------


class FactoryFlagTests(unittest.TestCase):
    def setUp(self):
        env = {k: v for k, v in os.environ.items() if k not in _ELEVEN_ENV}
        env["ELEVEN_API_KEY"] = "dummy"
        p = mock.patch.dict(os.environ, env, clear=True)
        p.start()
        self.addCleanup(p.stop)
        tts_factory._reset_warnings_for_tests()
        self.eleven = SimpleNamespace(TTS=mock.MagicMock(name="TTS"), VoiceSettings=mock.MagicMock())
        p = mock.patch.object(tts_factory, "_load_elevenlabs_plugin", return_value=self.eleven)
        p.start()
        self.addCleanup(p.stop)

    def kwargs(self):
        return self.eleven.TTS.call_args.kwargs

    def test_flag_off_gives_byte_identical_arguments(self):
        tts_factory.build_tts("ar")
        default = dict(self.kwargs())
        self.eleven.TTS.reset_mock()
        tts_factory.build_tts("ar", lipsync_alignment=False)
        self.assertEqual(self.kwargs(), default)
        self.assertIs(default["sync_alignment"], False)
        self.assertNotIn("preferred_alignment", default)
        self.assertEqual(
            sorted(default),
            ["apply_text_normalization", "language", "model", "sync_alignment", "voice_id",
             "voice_settings"],
        )

    def test_flag_on_asks_for_character_timings(self):
        tts_factory.build_tts("ar", lipsync_alignment=True)
        self.assertIs(self.kwargs()["sync_alignment"], True)
        self.assertEqual(self.kwargs()["preferred_alignment"], "original")

    def test_flag_on_only_adds_the_two_arguments(self):
        tts_factory.build_tts("ar")
        off = dict(self.kwargs())
        self.eleven.TTS.reset_mock()
        tts_factory.build_tts("ar", lipsync_alignment=True)
        on = dict(self.kwargs())
        changed = {k for k in set(on) | set(off) if on.get(k) != off.get(k)}
        self.assertEqual(changed, {"sync_alignment", "preferred_alignment"})

    def test_the_alignment_choice_is_honoured_and_a_bad_one_falls_back(self):
        with mock.patch.dict(os.environ, {"ELEVEN_ALIGNMENT": "normalized"}):
            tts_factory.build_tts("ar", lipsync_alignment=True)
        self.assertEqual(self.kwargs()["preferred_alignment"], "normalized")
        with mock.patch.dict(os.environ, {"ELEVEN_ALIGNMENT": "nonsense"}):
            with self.assertLogs(tts_factory.logger, level="WARNING"):
                tts_factory.build_tts("ar", lipsync_alignment=True)
        self.assertEqual(self.kwargs()["preferred_alignment"], "original")

    def test_the_transcript_flag_still_works_alone(self):
        tts_factory.build_tts("ar", aligned_transcript=True)
        self.assertIs(self.kwargs()["sync_alignment"], True)
        self.assertEqual(self.kwargs()["preferred_alignment"], "original")


# ---------------------------------------------------------------------------
# entrypoint and agent wiring (against the fake livekit of test_voice_wiring)
# ---------------------------------------------------------------------------


async def _fake_default_tts_node(agent, text, model_settings):
    async for chunk in text:
        yield f"frame:{chunk}"


class LipsyncWiringTests(_WiringBase):
    def setUp(self):
        super().setUp()
        p = mock.patch.object(_FakeAgent.default, "tts_node", staticmethod(_fake_default_tts_node),
                              create=True)
        p.start()
        self.addCleanup(p.stop)

    def timeline_state_handlers(self):
        """The session's agent_state_changed handlers that are the timeline's. The avatar signals,
        the latency logger and speak-first register bound methods of their own; the timeline's is
        the entrypoint's lambda."""
        return [h for h in self.session.handlers.get("agent_state_changed", [])
                if getattr(h, "__name__", "") == "<lambda>"]

    async def run_with_flag(self, value="1", *, installed=True, **kwargs):
        env = {"LIPSYNC_TIMELINE": value} if value is not None else {}
        with mock.patch.dict(os.environ, env):
            with mock.patch.object(lt, "install_char_timing_patch", return_value=installed) as patch:
                session = await self.run_entrypoint(**kwargs)
        self.install_patch = patch
        return session

    async def test_unset_is_on(self):
        await self.run_with_flag(None)
        self.assertIs(self.build_tts.call_args.kwargs["lipsync_alignment"], True)
        self.assertIsInstance(self.agent._lipsync, lt.LipsyncTimeline)

    async def test_flag_zero_is_off_nothing_changes(self):
        await self.run_with_flag("0")
        self.install_patch.assert_not_called()
        self.assertEqual(self.timeline_state_handlers(), [])
        self.assertIs(self.session.kwargs["use_tts_aligned_transcript"], False)
        self.assertIs(self.build_tts.call_args.kwargs["lipsync_alignment"], False)
        self.assertIsNone(self.agent._lipsync)

    async def test_on_asks_for_timings_and_wires_the_agent_and_the_state_handler(self):
        await self.run_with_flag("1")
        self.install_patch.assert_called_once()
        self.assertIs(self.build_tts.call_args.kwargs["lipsync_alignment"], True)
        self.assertIsInstance(self.agent._lipsync, lt.LipsyncTimeline)
        self.assertEqual(len(self.timeline_state_handlers()), 1)
        # The chat transcript is still the LLM's own text.
        self.assertIs(self.session.kwargs["use_tts_aligned_transcript"], False)
        self.assertIs(self.build_tts.call_args.kwargs["aligned_transcript"], False)

    async def test_the_state_handler_publishes_go(self):
        await self.run_with_flag("1")
        handle = _Handle("speech_3")
        self.session.current_speech = handle
        (handler,) = self.timeline_state_handlers()
        handler(SimpleNamespace(new_state="speaking", old_state="thinking"))
        await self.agent._lipsync.flush()
        sent = [c for c in self.publish_data.await_args_list if c.kwargs.get("topic") == lt.TOPIC]
        self.assertEqual([json.loads(c.args[0]) for c in sent], [{"v": 1, "sp": "speech_3", "go": 1}])

    async def test_a_plugin_that_cannot_be_patched_leaves_the_voice_audio_only(self):
        await self.run_with_flag("1", installed=False)
        self.assertIs(self.build_tts.call_args.kwargs["lipsync_alignment"], False)
        self.assertIsNone(self.agent._lipsync)

    async def test_the_xai_rollback_voice_never_gets_it(self):
        await self.run_with_flag("1", session_state={"mode": "xai", "max_seconds": 0})
        self.assertIs(self.build_tts.call_args.kwargs["lipsync_alignment"], False)
        self.assertIsNone(self.agent._lipsync)

    async def test_text_only_sessions_never_get_it(self):
        await self.run_with_flag("1", session_state={"mode": "text", "max_seconds": 0})
        self.build_tts.assert_not_called()
        self.assertIsNone(self.agent._lipsync)

    async def test_without_a_timeline_the_agent_returns_the_default_node_untouched(self):
        await self.run_with_flag(None)
        frames = self.agent.tts_node(_agen("a", "b"), None)
        # the lead's speech guard (turn_pipeline.guard_speech) holds text back until a sentence
        # ends, so the two unpunctuated chunks reach the default node as one
        self.assertEqual([f async for f in frames], ["frame:ab"])

    async def test_with_a_timeline_every_frame_passes_through_it_unchanged(self):
        await self.run_with_flag("1")
        seen = []

        class Spy:
            async def tap(self, frames, plan=None):  # plan: the gesture segment (BEHAVIOUR-SPEC 3.3)
                async for f in frames:
                    seen.append(f)
                    yield f

        self.agent.set_lipsync(Spy())
        out = [f async for f in self.agent.tts_node(_agen("a", "b", "c"), None)]
        self.assertEqual(out, ["frame:abc"])  # the speech guard joins unpunctuated chunks
        self.assertEqual(seen, out)

    async def test_closing_the_node_closes_the_default_node(self):
        await self.run_with_flag("1")
        closed = []

        async def default(agent, text, model_settings):
            try:
                yield 1
                yield 2
            finally:
                closed.append(True)

        with mock.patch.object(_FakeAgent.default, "tts_node", staticmethod(default)):
            node = self.agent.tts_node(_agen(), None)
            await node.__anext__()
            await node.aclose()
        self.assertEqual(closed, [True])

    async def test_a_coroutine_returning_node_is_awaited(self):
        await self.run_with_flag("1")

        async def default(agent, text, model_settings):
            return _agen("x", "y")

        with mock.patch.object(_FakeAgent.default, "tts_node", staticmethod(default)):
            out = [f async for f in self.agent.tts_node(_agen(), None)]
        self.assertEqual(out, ["x", "y"])


# ---------------------------------------------------------------------------
# The real livekit and plugin
# ---------------------------------------------------------------------------


def _can_import(name):
    try:
        return importlib.util.find_spec(name) is not None
    except Exception:
        return False


def _importable(name):
    try:
        importlib.import_module(name)
        return True
    except Exception:
        return False


_HAS_LIVEKIT = _can_import("livekit.agents") and _importable("livekit.agents")
_HAS_PLUGIN = _HAS_LIVEKIT and _can_import("livekit.plugins.elevenlabs") and _importable(
    "livekit.plugins.elevenlabs"
)


@unittest.skipUnless(_HAS_PLUGIN, "livekit-agents and livekit-plugins-elevenlabs are not installed")
class RealLivekitTests(unittest.TestCase):
    def setUp(self):
        _fresh_logs()
        from livekit.plugins.elevenlabs import tts as eleven_tts

        self.eleven_tts = eleven_tts
        self.original = eleven_tts._to_timed_words
        self.addCleanup(setattr, eleven_tts, "_to_timed_words", self.original)
        p = mock.patch.object(lt, "_patched", False)
        p.start()
        self.addCleanup(p.stop)

    def test_the_reviewed_pins(self):
        import livekit.agents as lk
        from livekit.plugins.elevenlabs import version

        self.assertEqual(lk.__version__, lt.PLUGIN_VERSION)
        self.assertEqual(version.__version__, lt.PLUGIN_VERSION)

    def test_the_userdata_key_and_speech_handle_var_exist(self):
        from livekit.agents.voice.agent_activity import _SpeechHandleContextVar
        from livekit.agents.voice.generation import USERDATA_TIMED_TRANSCRIPT

        self.assertEqual(USERDATA_TIMED_TRANSCRIPT, lt.USERDATA_KEY)
        self.assertTrue(hasattr(_SpeechHandleContextVar, "get"))

    def test_the_real_plugin_function_gets_characters(self):
        self.assertTrue(lt.install_char_timing_patch())
        text = "مرحبا بك يا صديقي"
        n = len(text)
        starts = [i * 40 for i in range(n)]
        words, rest = self.eleven_tts._to_timed_words(text, starts, [40] * n, flush=True)
        self.assertEqual(rest, "")
        self.assertEqual("".join(c for w in words for c, _, _ in w.char_ms), text)
        for w in words:
            self.assertEqual(w.char_ms[0][1], round(w.start_time * 1000))

    def test_a_real_timed_string_takes_the_attribute(self):
        from livekit.agents.types import TimedString

        w = TimedString("a", start_time=0.0, end_time=0.1)
        w.char_ms = [("a", 0, 100)]
        self.assertEqual(w.char_ms, [("a", 0, 100)])


if __name__ == "__main__":
    unittest.main()
