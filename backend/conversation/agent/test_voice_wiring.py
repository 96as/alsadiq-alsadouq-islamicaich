"""Tests for how the speech cleaner and the transcript are wired into the voice agent.

Two kinds of test:

- Wiring tests run everywhere. They import entrypoint.py and agent_class.py against a
  tiny fake of livekit (no livekit install needed) and check what the entrypoint hands to
  AgentSession and how the agent behaves.
- RealLivekitTests run only where livekit-agents 1.5.1 (and the ElevenLabs plugin) is
  installed. They drive the REAL livekit code paths: perform_tts_inference (which applies
  the text transforms), the default tts_node, the real filters and the real plugin.

No Quran text appears here. Placeholder words stand in for verses.

Run from backend/:  python manage.py test conversation.agent.test_voice_wiring \
    --settings=config.settings_sqlite_test
"""
from __future__ import annotations

import asyncio
import importlib
import importlib.util
import inspect
import json
import os
import sys
import unittest
from types import ModuleType, SimpleNamespace
from unittest import mock

from conversation import demo_guards
from conversation.agent import tts_factory
from conversation.agent.tts_text import (
    QURAN_PHRASE,
    prepare_for_tts,
    speech_tts_text_transform,
    tts_text_transform,
)

OPEN = "﴿"
CLOSE = "﴾"
PBUH = "ﷺ"
EN_PHRASE = QURAN_PHRASE["en"]
AR_PHRASE = QURAN_PHRASE["ar"]
PLACEHOLDER = "PLACEHOLDER_VERSE"

_ELEVEN_ENV = (
    "TTS_PROVIDER", "ELEVEN_API_KEY", "ELEVEN_VOICE_ID_AR", "ELEVEN_VOICE_ID_EN",
    "ELEVEN_MODEL", "ELEVEN_STABILITY", "ELEVEN_SIMILARITY", "ELEVEN_SPEED",
    "ELEVEN_STYLE", "ELEVEN_SPEAKER_BOOST", "ELEVEN_TEXT_NORMALIZATION", "ELEVEN_ALIGNMENT",
    "ELEVEN_LANGUAGE_HINT",
)


async def _agen(*chunks):
    for chunk in chunks:
        yield chunk


async def _collect(stream) -> str:
    return "".join([piece async for piece in stream])


# ---------------------------------------------------------------------------
# A minimal fake of livekit, just enough to import entrypoint.py and agent_class.py
# ---------------------------------------------------------------------------


class _NotGiven:
    def __repr__(self):
        return "NOT_GIVEN"


NOT_GIVEN = _NotGiven()


class _FakeAgent:
    """Mirrors the parts of livekit.agents.Agent that AlSadiqAgent relies on."""

    class default:
        @staticmethod
        async def transcription_node(agent, text, model_settings):
            async for delta in text:
                yield delta

        @staticmethod
        async def tts_node(agent, text, model_settings):
            # The real one turns text into audio frames; the fake hands the text on.
            async for delta in text:
                yield delta

    def __init__(self, *, instructions, use_tts_aligned_transcript=NOT_GIVEN):
        self._instructions = instructions
        self._use_tts_aligned_transcript = use_tts_aligned_transcript
        self._fake_session = None

    @property
    def use_tts_aligned_transcript(self):
        return self._use_tts_aligned_transcript

    @property
    def chat_ctx(self):
        # a typed turn with a TURN POLICY (a comforted "i feel so sad") copies the agent's chat context
        from unittest import mock
        return mock.MagicMock(name="chat_ctx")

    @property
    def session(self):
        if self._fake_session is None:
            raise RuntimeError("no activity context found, the agent is not running")
        return self._fake_session


class _FakeAgentSession:
    instances: list = []

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.options = SimpleNamespace(
            use_tts_aligned_transcript=kwargs.get("use_tts_aligned_transcript"),
            tts_text_transforms=kwargs.get("tts_text_transforms"),
        )
        self.start_kwargs = None
        self.handlers = {}
        self.audio_input = []  # set_audio_enabled calls
        self.input = SimpleNamespace(set_audio_enabled=self.audio_input.append)
        self.interrupts = []  # the force flag of each interrupt() call
        self.cleared_turns = 0
        self.current_speech = None  # nothing playing when the clock fires
        self.replies = []
        _FakeAgentSession.instances.append(self)

    def interrupt(self, *, force=False):
        self.interrupts.append(force)

    def clear_user_turn(self):
        self.cleared_turns += 1

    def on(self, event, callback=None, **_kwargs):
        self.handlers.setdefault(event, []).append(callback)
        return callback

    async def start(self, **kwargs):
        self.start_kwargs = kwargs

    async def generate_reply(self, **kwargs):
        self.replies.append(kwargs)
        return None

    def say(self, text, **kwargs):
        self.said = getattr(self, "said", [])
        self.said.append((text, kwargs))
        return None


async def _fake_filter_markdown(text):
    async for chunk in text:
        yield chunk.replace("**", "")


async def _fake_filter_emoji(text):
    async for chunk in text:
        yield chunk


class _FakeTimedString(str):
    """Stands in for livekit.agents.types.TimedString (a str subclass with word timings)."""


def _fake_function_tool(fn=None, **_kwargs):
    return fn if fn is not None else (lambda f: f)


def _fake_livekit_modules() -> dict[str, ModuleType]:
    def module(name, **attrs):
        mod = ModuleType(name)
        mod.__dict__.update(attrs)
        return mod

    room_io = SimpleNamespace(
        RoomOptions=lambda **kw: kw, TextInputOptions=lambda **kw: kw,
    )
    plugins_openai = SimpleNamespace(
        LLM=lambda **kw: SimpleNamespace(kind="llm", **kw),
        STT=lambda **kw: SimpleNamespace(kind="openai-stt", **kw),
    )
    plugins_silero = SimpleNamespace(VAD=SimpleNamespace(load=lambda: object()))
    return {
        "livekit": module("livekit"),
        "livekit.agents": module(
            "livekit.agents", Agent=_FakeAgent, AgentSession=_FakeAgentSession,
            JobContext=object, JobProcess=object, room_io=room_io,
        ),
        "livekit.agents.llm": module(
            "livekit.agents.llm", function_tool=_fake_function_tool,
            ChatMessage=lambda **kw: SimpleNamespace(**kw),  # reply_to_typed builds the child's message
        ),
        "livekit.agents.types": module("livekit.agents.types", TimedString=_FakeTimedString),
        "livekit.agents.voice": module("livekit.agents.voice"),
        "livekit.agents.voice.transcription": module("livekit.agents.voice.transcription"),
        "livekit.agents.voice.transcription.filters": module(
            "livekit.agents.voice.transcription.filters",
            filter_markdown=_fake_filter_markdown, filter_emoji=_fake_filter_emoji,
        ),
        "livekit.plugins": module(
            "livekit.plugins", openai=plugins_openai, silero=plugins_silero,
        ),
    }


_AGENT_MODULES = ("conversation.agent.agent_class", "conversation.agent.entrypoint")


def _import_agent_modules_against_fake_livekit(testcase: unittest.TestCase):
    """Import agent_class and entrypoint with the fake livekit, then restore everything."""
    import conversation.agent as agent_pkg

    saved_attrs = {n: agent_pkg.__dict__.get(n.rsplit(".", 1)[1]) for n in _AGENT_MODULES}
    patcher = mock.patch.dict(sys.modules, _fake_livekit_modules())
    patcher.start()
    for name in _AGENT_MODULES:
        sys.modules.pop(name, None)

    def _restore():
        patcher.stop()  # also drops the fake-based modules from sys.modules
        for name, value in saved_attrs.items():
            attr = name.rsplit(".", 1)[1]
            if value is None:
                agent_pkg.__dict__.pop(attr, None)
            else:
                setattr(agent_pkg, attr, value)

    testcase.addCleanup(_restore)
    agent_class = importlib.import_module("conversation.agent.agent_class")
    entrypoint = importlib.import_module("conversation.agent.entrypoint")
    return agent_class, entrypoint


class _WiringBase(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        env_patch = mock.patch.dict(
            os.environ, {k: v for k, v in os.environ.items() if k not in _ELEVEN_ENV},
            clear=True,
        )
        env_patch.start()
        self.addCleanup(env_patch.stop)
        _FakeAgentSession.instances.clear()
        self.agent_class, self.entrypoint = _import_agent_modules_against_fake_livekit(self)

    async def run_entrypoint(self, language_preference="ar", *, build_tts_error=None,
                             build_stt_error=None, session_state="default", decision=None,
                             started_at=None, memory_text=""):
        """session_state is what the backend stored for the session (the demo guards).

        The default is a plain ElevenLabs session with no time limit, so the tests above
        never touch Redis.
        """
        ep = self.entrypoint
        if session_state == "default":
            session_state = {"mode": "eleven", "max_seconds": 0}
        # session_state=None means the backend stored nothing: the agent decides itself.
        if decision is None:
            decision = demo_guards.VoiceDecision("eleven", "env")
        self.shutdown_callbacks = []
        db_session = SimpleNamespace(
            id=1, child_id=2, started_at=started_at,
            child=SimpleNamespace(nickname="Zubayr-Nick", language_preference=language_preference,
                                  birth_year=2016),
        )
        self.publish_data = mock.AsyncMock()
        self.set_attributes = mock.AsyncMock()  # the avatar signals' attributes
        self.ctx = ctx = SimpleNamespace(
            connect=mock.AsyncMock(),
            room=SimpleNamespace(
                name="room-1",
                local_participant=SimpleNamespace(
                    publish_data=self.publish_data, set_attributes=self.set_attributes),
            ),
            proc=SimpleNamespace(userdata={"vad": object()}),
            shutdown=mock.MagicMock(name="shutdown"),
            add_shutdown_callback=self.shutdown_callbacks.append,
            delete_room=mock.AsyncMock(name="delete_room"),
        )
        self.build_tts = mock.MagicMock(name="build_tts", side_effect=build_tts_error)
        self.build_stt = mock.MagicMock(name="build_stt", side_effect=build_stt_error)
        # The reasoning-effort check makes one real API call: never in these tests. A test sets
        # self.effort_result before run_entrypoint to choose what the check answers.
        result = getattr(self, "effort_result", None)
        self.resolve_effort = mock.AsyncMock(
            name="resolve_reasoning_effort",
            **({"side_effect": result} if isinstance(result, BaseException) else {"return_value": result}),
        )
        with (
            mock.patch.object(ep, "resolve_reasoning_effort", self.resolve_effort),
            mock.patch.object(ep, "_get_session", mock.AsyncMock(return_value=db_session)),
            mock.patch.object(ep, "_get_child_session_memory_text",
                              mock.AsyncMock(return_value=memory_text)),
            mock.patch.object(ep, "_get_value_index", mock.AsyncMock(return_value=None)),
            mock.patch.object(ep, "_get_active_quests_text", mock.AsyncMock(return_value="")),
            mock.patch.object(ep, "build_tts", self.build_tts),
            mock.patch.object(ep, "build_stt", self.build_stt),
            mock.patch.object(demo_guards, "load_session_state", return_value=session_state),
            mock.patch.object(demo_guards, "resolve_voice", return_value=decision),
        ):
            await ep.entrypoint(ctx)
            # Let a started session clock run its first step (it is cancelled on shutdown).
            await asyncio.sleep(0)
            for callback in self.shutdown_callbacks:
                await callback()
        if not _FakeAgentSession.instances:
            self.session = None
            return None
        self.session = _FakeAgentSession.instances[-1]
        self.agent = self.session.start_kwargs["agent"]
        self.transforms = self.session.kwargs["tts_text_transforms"]
        return self.session


class ArabicGreetingTests(_WiringBase):
    """Sadiq greets first, so he opens with the initiating salam, never the reply form."""

    REPLY_FORM = "وعليكم"  # "and upon you": what you answer to someone else's salam
    OPENING = "السلام عليكم"

    def test_arabic_opening_instruction_is_the_initiating_salam(self):
        text = self.entrypoint._GREETING_INSTRUCTIONS["ar"]
        self.assertIn(self.OPENING, text)
        self.assertNotIn(self.REPLY_FORM, text)
        # He is told he starts the greeting, and to say the salam first.
        self.assertIn("أنت من يبدأ التحية", text)
        self.assertLess(text.index("أول كلمات"), text.index(self.OPENING))
        # The old wording ("سلّم بالسلام عليكم") read like an answer to a salam.
        self.assertNotIn("سلّم بالسلام", text)

    def test_arabic_opening_keeps_the_rest_of_the_rules(self):
        text = self.entrypoint._GREETING_INSTRUCTIONS["ar"]
        self.assertIn("جملتان كحد أقصى", text)
        self.assertIn("اسأل عنه بشكل طبيعي", text)
        self.assertIn("لا تعرض قائمة مواضيع", text)

    def test_english_opening_is_untouched(self):
        # PR #52 (B6) reworded the salam: 'Assalamu alaikum' in English letters, never Arabic script
        text = self.entrypoint._GREETING_INSTRUCTIONS["en"]
        self.assertIn("'Assalamu alaikum' in English letters", text)
        self.assertIn("plus one short sentence, two sentences max", text)

    def test_english_opening_stays_english_when_the_memory_is_arabic(self):
        # Live finding (2026-10-05): the demo families' remembered notes are Arabic, and an
        # English session greeted in Arabic because nothing told the model to stay in English.
        text = self.entrypoint._GREETING_INSTRUCTIONS["en"]
        self.assertIn("Speak English", text)
        self.assertIn("memory notes may be written in Arabic", text)

    async def test_an_arabic_session_greets_with_that_instruction(self):
        session = await self.run_entrypoint("ar")
        self.assertEqual(len(session.replies), 1)
        # no memory yet = first meeting, so the AI-disclosure line (01) is appended
        self.assertEqual(session.replies[0]["instructions"],
                         self.entrypoint._GREETING_INSTRUCTIONS["ar"]
                         + self.entrypoint._FIRST_MEETING_AI_LINE["ar"])

    async def test_an_english_session_still_gets_the_english_instruction(self):
        session = await self.run_entrypoint("en")
        self.assertEqual(session.replies[0]["instructions"],
                         self.entrypoint._GREETING_INSTRUCTIONS["en"]
                         + self.entrypoint._FIRST_MEETING_AI_LINE["en"])


class EntrypointWiringTests(_WiringBase):
    async def test_join_log_does_not_include_child_nickname(self):
        with self.assertLogs("conversation.agent.entrypoint", level="INFO") as captured:
            await self.run_entrypoint()
        logged = "\n".join(captured.output)
        self.assertNotIn("Zubayr-Nick", logged)

    async def test_session_installs_one_cleaner_and_replaces_the_default_filters(self):
        await self.run_entrypoint()
        self.assertEqual(len(self.transforms), 1)
        self.assertTrue(callable(self.transforms[0]))
        # A string entry would mean the livekit defaults ("filter_markdown", ...) came back.
        self.assertFalse(any(isinstance(t, str) for t in self.transforms))

    async def test_aligned_transcripts_are_off_for_the_session_and_the_tts(self):
        await self.run_entrypoint()
        self.assertIs(self.session.kwargs["use_tts_aligned_transcript"], False)
        self.build_tts.assert_called_once()
        self.assertIs(self.build_tts.call_args.kwargs["aligned_transcript"], False)

    async def test_avatar_signals_are_attached_and_started(self):
        session = await self.run_entrypoint()
        self.assertEqual(set(session.handlers) & {"user_input_transcribed", "agent_state_changed",
                                                  "user_state_changed"},
                         {"user_input_transcribed", "agent_state_changed", "user_state_changed"})
        await self.agent.signals.flush()
        first = self.set_attributes.await_args_list[0].args[0]
        self.assertEqual(first["al.sig_v"], "1")
        self.assertEqual(first["al.activity"], "idle")
        self.assertEqual(first["al.reply"], "0")
        for call in self.set_attributes.await_args_list:
            self.assertTrue(all(k.startswith("al.") and v for k, v in call.args[0].items()))

    async def test_typed_chat_is_classified_for_the_avatar(self):
        session = await self.run_entrypoint()
        self.set_attributes.reset_mock()
        callback = session.start_kwargs["room_options"]["text_input"]["text_input_cb"]
        chat = mock.MagicMock(name="session")
        with mock.patch.object(self.entrypoint, "_save_message",
                               mock.AsyncMock(return_value=SimpleNamespace(id=9))):
            callback(chat, SimpleNamespace(text="i feel so sad today"))
            await asyncio.sleep(0)
        await self.agent.signals.flush()
        merged = {}
        for call in self.set_attributes.await_args_list:
            merged.update(call.args[0])
        self.assertEqual(merged["al.listen_style"], "sad")
        self.assertEqual(merged["al.turn"], "1")

    async def test_agent_is_created_with_the_child_language(self):
        await self.run_entrypoint("ar")
        self.assertEqual(self.agent.language, "ar")

    async def test_transform_cleans_what_is_spoken(self):
        await self.run_entrypoint("en")
        spoken = await _collect(self.transforms[0](_agen("I am **12** years old")))
        self.assertEqual(spoken.strip(), "I am twelve years old")

    async def test_language_follows_the_live_agent_language(self):
        await self.run_entrypoint("en")
        transform = self.transforms[0]
        self.assertEqual((await _collect(transform(_agen("12 ")))).strip(),
                         prepare_for_tts("12", "en"))
        self.agent.language = "ar"
        arabic = (await _collect(transform(_agen("12 ")))).strip()
        self.assertEqual(arabic, prepare_for_tts("12", "ar"))
        self.assertNotEqual(arabic, prepare_for_tts("12", "en"))
        self.agent.language = "en-US"  # region suffixes are fine
        self.assertEqual((await _collect(transform(_agen("12 ")))).strip(),
                         prepare_for_tts("12", "en"))

    async def test_neutral_phrase_follows_the_live_language_too(self):
        await self.run_entrypoint("ar")
        transform = self.transforms[0]
        text = f"x {OPEN}{PLACEHOLDER}{CLOSE} y"
        self.assertIn(AR_PHRASE, await _collect(transform(_agen(text))))
        self.agent.language = "en"
        self.assertIn(EN_PHRASE, await _collect(transform(_agen(text))))

    async def test_quran_guard_holds_across_segments_of_one_speech(self):
        await self.run_entrypoint("en")
        transform = self.transforms[0]

        async def one_speech():
            # livekit applies the transform once per segment, in order, inside ONE task.
            first = await _collect(transform(_agen(f"Listen {OPEN}{PLACEHOLDER}")))
            second = await _collect(transform(_agen(f"{PLACEHOLDER}_MORE {CLOSE} then more")))
            return first, second

        first, second = await asyncio.create_task(one_speech())
        self.assertIn(EN_PHRASE, first)
        self.assertNotIn(PLACEHOLDER, first + second)
        self.assertNotIn("MORE", second)
        self.assertIn("then more", second)

    async def test_quran_guard_does_not_leak_into_the_next_speech(self):
        # An interrupted (or discarded, preemptive) speech can end inside a bracket.
        await self.run_entrypoint("en")
        transform = self.transforms[0]

        async def interrupted_speech():
            return await _collect(transform(_agen(f"Listen {OPEN}{PLACEHOLDER}")))

        async def next_speech():
            return await _collect(transform(_agen("Hello my friend, how are you today?")))

        await asyncio.create_task(interrupted_speech())
        spoken = await asyncio.create_task(next_speech())
        self.assertEqual(spoken.strip(), "Hello my friend, how are you today?")

    async def test_concurrent_speeches_keep_separate_guards(self):
        await self.run_entrypoint("en")
        transform = self.transforms[0]
        gate = asyncio.Event()

        async def verse_speech():
            async def slow():
                yield f"Listen {OPEN}{PLACEHOLDER} "
                gate.set()
                await asyncio.sleep(0)
                yield f"{PLACEHOLDER}{CLOSE} done"

            return await _collect(transform(slow()))

        async def plain_speech():
            await gate.wait()  # runs while the first speech is inside its bracket
            return await _collect(transform(_agen("Plain words only.")))

        verse, plain = await asyncio.gather(verse_speech(), plain_speech())
        self.assertNotIn(PLACEHOLDER, verse)
        self.assertEqual(plain.strip(), "Plain words only.")

    async def test_session_wide_transform_would_leak_which_is_why_it_is_per_speech(self):
        # Documents the failure the per-speech state avoids.
        shared = tts_text_transform("en")

        async def interrupted():
            return await _collect(shared(_agen(f"Listen {OPEN}{PLACEHOLDER}")))

        async def next_speech():
            return await _collect(shared(_agen("Hello my friend.")))

        await asyncio.create_task(interrupted())
        self.assertEqual((await asyncio.create_task(next_speech())).strip(), "")


class NoFallbackVoiceTests(_WiringBase):
    """When the voice cannot be used the session fails visibly. Nothing else speaks."""

    def published(self):
        self.publish_data.assert_awaited_once()
        call = self.publish_data.await_args
        return json.loads(call.args[0].decode()), call.kwargs

    async def test_missing_eleven_key_ends_the_job_and_tells_the_room(self):
        error = tts_factory.VoiceConfigurationError("missing_key", "ELEVEN_API_KEY is missing.")
        session = await self.run_entrypoint(build_tts_error=error)
        self.assertIsNone(session)  # no AgentSession, so nobody speaks and nobody listens
        self.ctx.shutdown.assert_called_once()
        message, kwargs = self.published()
        self.assertEqual(message, {"type": "voice_unavailable", "provider": "elevenlabs",
                                   "code": "missing_key"})
        self.assertEqual(kwargs["topic"], "voice_error")
        self.assertTrue(kwargs["reliable"])

    async def test_scribe_failure_also_ends_the_job_without_another_engine(self):
        error = tts_factory.VoiceConfigurationError("missing_key", "scribe key missing")
        session = await self.run_entrypoint(build_stt_error=error)
        self.assertIsNone(session)
        self.ctx.shutdown.assert_called_once()
        self.assertEqual(self.published()[0]["code"], "missing_key")

    async def test_an_unexpected_error_is_not_swallowed_into_a_fallback(self):
        with self.assertRaises(RuntimeError):
            await self.run_entrypoint(build_tts_error=RuntimeError("not a config error"))
        self.ctx.shutdown.assert_not_called()

    async def test_a_working_voice_does_not_publish_anything(self):
        await self.run_entrypoint()
        self.publish_data.assert_not_awaited()
        self.ctx.shutdown.assert_not_called()

    def tts_error_event(self, exc, recoverable):
        return SimpleNamespace(error=SimpleNamespace(type="tts_error", error=exc,
                                                     recoverable=recoverable))

    async def test_a_key_rejected_mid_session_is_named_once_and_ends_the_session(self):
        session = await self.run_entrypoint()
        (handler,) = session.handlers["error"]
        secret = "sk_secret_value_that_must_not_leak"
        exc = RuntimeError(f"401 invalid_api_key {secret}")
        with self.assertLogs(self.entrypoint.logger, level="ERROR") as logs:
            handler(self.tts_error_event(exc, recoverable=True))   # livekit still retrying
            handler(self.tts_error_event(exc, recoverable=False))  # gave up
            handler(self.tts_error_event(exc, recoverable=False))  # a repeat changes nothing
            await asyncio.sleep(0)
            await asyncio.sleep(0)
        self.assertEqual(len(logs.records), 1)
        self.assertIn("key_rejected", logs.output[0])
        self.assertIn("No fallback voice", logs.output[0])
        self.assertNotIn(secret, logs.output[0])
        message, kwargs = self.published()
        self.assertEqual(message["code"], "key_rejected")
        self.assertEqual(kwargs["topic"], "voice_error")
        self.ctx.shutdown.assert_called_once()

    async def test_a_recoverable_error_alone_does_not_end_the_session(self):
        session = await self.run_entrypoint()
        (handler,) = session.handlers["error"]
        with self.assertLogs(self.entrypoint.logger, level="ERROR"):
            handler(self.tts_error_event(TimeoutError("timed out"), recoverable=True))
        await asyncio.sleep(0)
        self.publish_data.assert_not_awaited()
        self.ctx.shutdown.assert_not_called()

    async def test_errors_from_other_parts_are_ignored_by_the_voice_handler(self):
        session = await self.run_entrypoint()
        (handler,) = session.handlers["error"]
        handler(SimpleNamespace(error=SimpleNamespace(type="llm_error", error=RuntimeError("x"),
                                                      recoverable=False)))
        await asyncio.sleep(0)
        self.publish_data.assert_not_awaited()
        self.ctx.shutdown.assert_not_called()

    async def test_entrypoint_has_no_xai_fallback_path(self):
        source = inspect.getsource(self.entrypoint)
        self.assertNotIn("XaiStreamingTTS", source)
        self.assertNotIn("xai_tts_streaming", source)


class DemoGuardWiringTests(_WiringBase):
    """The backend's per-session decision (eleven | xai | text | off) reaches the agent."""

    def setUp(self):
        super().setUp()
        # These tests are about the voice mode and the session clock, not lip sync. Since #68 the
        # timeline is on by default, and then whether the entrypoint also registers
        # LipsyncTimeline.aclose as a shutdown callback depends on whether the real ElevenLabs
        # plugin 1.5.1 is already in sys.modules (another test module imports it), so on test
        # order. Pinned off here; the timeline-on case is its own test, with the patch mocked.
        env_patch = mock.patch.dict(os.environ, {"LIPSYNC_TIMELINE": "0"})
        env_patch.start()
        self.addCleanup(env_patch.stop)

    def published(self):
        self.publish_data.assert_awaited_once()
        call = self.publish_data.await_args
        return json.loads(call.args[0].decode()), call.kwargs

    async def test_text_mode_builds_no_voice_and_turns_audio_off(self):
        session = await self.run_entrypoint(session_state={"mode": "text", "max_seconds": 0})
        self.assertIsNotNone(session)
        self.build_tts.assert_not_called()
        self.build_stt.assert_not_called()
        self.assertIsNone(session.kwargs["tts"])
        self.assertIsNone(session.kwargs["stt"])
        self.assertIsNone(session.kwargs["vad"])
        options = session.start_kwargs["room_options"]
        self.assertIs(options["audio_input"], False)
        self.assertIs(options["audio_output"], False)
        self.assertIn("text_input", options)
        self.publish_data.assert_not_awaited()
        self.ctx.shutdown.assert_not_called()

    async def test_text_mode_does_not_count_characters(self):
        session = await self.run_entrypoint(session_state={"mode": "text", "max_seconds": 0})
        self.assertNotIsInstance(session.kwargs["tts_text_transforms"][0],
                                 sys.modules["conversation.agent.demo_limits"].UsageCountingTransform)

    async def test_off_mode_ends_the_job_with_one_clear_error_and_a_message(self):
        with self.assertLogs(self.entrypoint.logger, level="ERROR") as logs:
            session = await self.run_entrypoint(session_state={"mode": "off", "max_seconds": 0})
        self.assertIsNone(session)
        self.assertEqual(len(logs.records), 1)
        self.assertIn("voice_off", logs.output[0])
        message, kwargs = self.published()
        self.assertEqual(message, {"type": "voice_unavailable", "provider": "none",
                                   "code": "voice_off"})
        self.assertEqual(kwargs["topic"], "voice_error")
        self.ctx.shutdown.assert_called_once()
        self.build_tts.assert_not_called()

    async def test_eleven_mode_asks_for_elevenlabs_and_counts_what_it_speaks(self):
        added = []
        with mock.patch.object(demo_guards, "add_eleven_chars", added.append):
            session = await self.run_entrypoint(
                "en", session_state={"mode": "eleven", "max_seconds": 0})
            self.assertEqual(self.build_tts.call_args.kwargs["provider"], "elevenlabs")
            self.assertEqual(len(session.kwargs["tts_text_transforms"]), 1)
            spoken = await _collect(self.transforms[0](_agen("I am **12** years old")))
            await self.transforms[0].drain()  # the count is written off the event loop
        self.assertEqual(spoken.strip(), "I am twelve years old")
        self.assertEqual(sum(added), len(spoken))
        self.assertNotIn("audio_input", session.start_kwargs["room_options"])

    async def test_xai_mode_is_used_only_when_the_backend_says_an_operator_chose_it(self):
        await self.run_entrypoint(session_state={"mode": "xai", "max_seconds": 0})
        self.assertEqual(self.build_tts.call_args.kwargs["provider"], "xai")

    async def test_a_failed_elevenlabs_build_never_retries_with_xai(self):
        error = tts_factory.VoiceConfigurationError("build_failed", "plugin failed")
        session = await self.run_entrypoint(
            build_tts_error=error, session_state={"mode": "eleven", "max_seconds": 0})
        self.assertIsNone(session)
        self.build_tts.assert_called_once()
        self.assertEqual(self.build_tts.call_args.kwargs["provider"], "elevenlabs")
        self.assertEqual(self.published()[0]["provider"], "elevenlabs")

    async def test_without_a_stored_decision_the_agent_resolves_it_itself(self):
        decision = demo_guards.VoiceDecision("text", "eleven_daily_cap", "voice_resting")
        session = await self.run_entrypoint(session_state=None, decision=decision)
        self.build_tts.assert_not_called()
        self.assertIs(session.start_kwargs["room_options"]["audio_output"], False)

    async def test_the_session_clock_starts_with_a_time_limit_and_is_stopped_on_shutdown(self):
        session = await self.run_entrypoint(session_state={"mode": "eleven", "max_seconds": 300})
        self.assertIsNotNone(session)
        self.assertEqual(len(self.shutdown_callbacks), 1)
        self.ctx.shutdown.assert_not_called()  # the clock was cancelled before the limit

    async def test_with_the_timeline_on_the_clock_is_still_stopped_on_shutdown(self):
        # The default since #68: a time-limited session also registers the lip-sync close. The two
        # callbacks share nothing (livekit runs them concurrently, after closing the session).
        ep = self.entrypoint
        clock = {}

        async def held(**_kwargs):
            clock["task"] = asyncio.current_task()
            await asyncio.Event().wait()  # runs until it is cancelled

        with (
            mock.patch.dict(os.environ, {"LIPSYNC_TIMELINE": "1"}),
            mock.patch.object(ep.lipsync_timeline, "install_char_timing_patch", return_value=True),
            mock.patch.object(ep, "run_session_clock", held),
        ):
            session = await self.run_entrypoint(session_state={"mode": "eleven", "max_seconds": 300})
        await asyncio.wait({clock["task"]}, timeout=1)
        self.assertIsNotNone(session)
        self.assertIsInstance(self.agent._lipsync, ep.lipsync_timeline.LipsyncTimeline)
        self.assertEqual(len(self.shutdown_callbacks), 2)
        self.assertIn(self.agent._lipsync.aclose, self.shutdown_callbacks)
        self.assertTrue(clock["task"].cancelled())
        self.ctx.shutdown.assert_not_called()

    async def test_no_clock_without_a_time_limit(self):
        await self.run_entrypoint(session_state={"mode": "eleven", "max_seconds": 0})
        self.assertEqual(self.shutdown_callbacks, [])

    async def test_clock_says_goodbye_then_closes_the_room(self):
        ep = self.entrypoint
        original = ep.run_session_clock

        async def instant(**kwargs):
            kwargs["sleep"] = mock.AsyncMock()
            return await original(**kwargs)

        with mock.patch.object(ep, "run_session_clock", instant):
            session = await self.run_entrypoint(
                "en", session_state={"mode": "eleven", "max_seconds": 300})
            for _ in range(10):
                await asyncio.sleep(0)
        (text, kwargs), = session.said
        self.assertEqual(text, demo_guards.goodbye_for("en"))
        self.assertIs(kwargs["allow_interruptions"], False)
        topics = [c.kwargs["topic"] for c in self.publish_data.await_args_list]
        self.assertEqual(topics, ["session_limit", "session_limit"])
        self.ctx.delete_room.assert_awaited_once()
        self.ctx.shutdown.assert_called_once()

    async def test_goodbye_follows_the_language_the_child_switched_to(self):
        ep = self.entrypoint
        original = ep.run_session_clock
        holder = {}

        async def instant(**kwargs):
            holder["language"] = kwargs["language"]
            kwargs["sleep"] = mock.AsyncMock()
            return await original(**kwargs)

        with mock.patch.object(ep, "run_session_clock", instant):
            await self.run_entrypoint(
                "en", session_state={"mode": "eleven", "max_seconds": 300})
        self.assertEqual(holder["language"](), "en")
        self.agent.language = "ar"
        self.assertEqual(holder["language"](), "ar")

    async def _run_to_the_limit(self, mode):
        """Run a session whose clock fires at once; return (session, text input callback)."""
        ep = self.entrypoint
        original = ep.run_session_clock

        async def instant(**kwargs):
            kwargs["sleep"] = mock.AsyncMock()
            return await original(**kwargs)

        with mock.patch.object(ep, "run_session_clock", instant):
            session = await self.run_entrypoint(
                "en", session_state={"mode": mode, "max_seconds": 300})
            for _ in range(10):
                await asyncio.sleep(0)
        return session, session.start_kwargs["room_options"]["text_input"]["text_input_cb"]

    async def _type(self, callback, text):
        """Send a chat line through the text input callback; return the session mock."""
        chat = mock.MagicMock(name="session")
        with mock.patch.object(self.entrypoint, "_save_message",
                               mock.AsyncMock(return_value=SimpleNamespace(id=9))) as save:
            callback(chat, SimpleNamespace(text=text))
            await asyncio.sleep(0)
        save.assert_awaited_once()  # the line is still saved
        return chat

    async def test_goodbye_stops_new_turns_and_clears_the_queue_before_closing(self):
        session, text_input = await self._run_to_the_limit("eleven")
        self.assertEqual(session.audio_input, [False])  # the mic stops being heard
        self.assertEqual(session.cleared_turns, 1)  # a half-said line gets no reply
        self.assertEqual(session.interrupts, [True])  # nothing queued behind the goodbye
        self.ctx.delete_room.assert_awaited_once()
        chat = await self._type(text_input, "one more question")
        chat.interrupt.assert_not_called()  # the goodbye cannot be interrupted
        chat.generate_reply.assert_not_called()

    async def test_text_mode_goodbye_leaves_the_audio_input_alone(self):
        session, text_input = await self._run_to_the_limit("text")
        (text, _kwargs), = session.said
        self.assertEqual(text, demo_guards.goodbye_for("en"))
        self.assertEqual(session.audio_input, [])
        self.assertEqual(session.cleared_turns, 0)
        self.assertEqual(session.interrupts, [True])
        chat = await self._type(text_input, "bye")
        chat.generate_reply.assert_not_called()

    async def test_before_the_limit_a_chat_line_still_gets_a_reply(self):
        session = await self.run_entrypoint(session_state={"mode": "text", "max_seconds": 0})
        text_input = session.start_kwargs["room_options"]["text_input"]["text_input_cb"]
        chat = await self._type(text_input, "I like football")  # not courtesy: no injection
        chat.interrupt.assert_called_once()
        chat.generate_reply.assert_called_once()
        self.assertEqual(chat.generate_reply.call_args.kwargs["user_input"].content, ["I like football"])

    async def test_a_session_already_past_its_limit_closes_without_speaking(self):
        from datetime import timedelta

        from django.utils import timezone

        session = await self.run_entrypoint(
            session_state={"mode": "eleven", "max_seconds": 300},
            started_at=timezone.now() - timedelta(seconds=400))
        self.assertIsNone(session)  # no AgentSession: no greeting, nothing billed
        self.build_tts.assert_not_called()
        self.build_stt.assert_not_called()
        message, kwargs = json.loads(self.publish_data.await_args.args[0].decode()), \
            self.publish_data.await_args.kwargs
        self.assertEqual(message, {"type": "session_ended"})
        self.assertEqual(kwargs["topic"], "session_limit")
        self.ctx.delete_room.assert_awaited_once()
        self.ctx.shutdown.assert_called_once()

    async def test_a_session_with_time_left_runs_with_the_clock(self):
        from datetime import timedelta

        from django.utils import timezone

        session = await self.run_entrypoint(
            session_state={"mode": "eleven", "max_seconds": 300},
            started_at=timezone.now() - timedelta(seconds=100))
        self.assertIsNotNone(session)
        self.assertEqual(len(self.shutdown_callbacks), 1)
        self.ctx.delete_room.assert_not_awaited()

    async def test_the_entrypoint_still_has_no_xai_fallback_path(self):
        source = inspect.getsource(self.entrypoint)
        self.assertNotIn("XaiStreamingTTS", source)
        self.assertNotIn("xai_tts_streaming", source)
        self.assertNotIn("selected_provider", source)


class AgentTranscriptTests(_WiringBase):
    """The chat and DB transcript is the LLM text, guarded (fake livekit filters)."""

    def make_agent(self, language="en"):
        return self.agent_class.AlSadiqAgent(db_session_id=1, child_id=2, language=language)

    async def test_transcript_keeps_digits_and_honorific_but_not_a_bracketed_span(self):
        # Digits and the honorific stay written (only the speech is spelled out). A bracketed
        # span is scripture-shaped text: the compliance guard keeps it out of the chat too.
        agent = self.make_agent()
        original = f"We met on day 12 {PBUH} and read {OPEN}{PLACEHOLDER}{CLOSE} together."
        shown = await _collect(agent.transcription_node(_agen(original), None))
        self.assertIn(f"day 12 {PBUH}", shown)
        self.assertNotIn(PLACEHOLDER, shown)
        self.assertNotIn(OPEN, shown)
        self.assertEqual(" ".join(shown.split()), f"We met on day 12 {PBUH} and read together.")

    async def test_speech_of_the_same_text_is_cleaned(self):
        agent = self.make_agent()
        original = f"We met on day 12 {PBUH} and read {OPEN}{PLACEHOLDER}{CLOSE} together."
        spoken = await _collect(speech_tts_text_transform(lambda: agent.language)(_agen(original)))
        self.assertIn("twelve", spoken)
        self.assertIn(EN_PHRASE, spoken)
        self.assertNotIn("12", spoken)
        self.assertNotIn(PLACEHOLDER, spoken)
        self.assertNotIn(OPEN, spoken)
        self.assertNotIn(PBUH, spoken)

    async def test_transcript_drops_stray_cjk_inside_an_arabic_word_but_keeps_arabic_and_latin(self):
        agent = self.make_agent("ar")
        shown = await _collect(agent.transcription_node(
            _agen("مرحبا يا صدي中文ق، hello カタ 12 world 한!"), None))
        self.assertEqual(shown, "مرحبا يا صديق، hello  12 world !")

    async def test_transcript_still_drops_markdown_symbols(self):
        agent = self.make_agent()
        shown = await _collect(agent.transcription_node(_agen("This is **great** news"), None))
        self.assertEqual(shown, "This is great news")

    async def test_aligned_transcript_text_is_passed_through_untouched(self):
        agent = self.make_agent()
        agent._use_tts_aligned_transcript = True
        timed = ["already ", "**kept**"]
        shown = await _collect(agent.transcription_node(_agen(*timed), None))
        self.assertEqual(shown, "already **kept**")  # no second filtering of timed words

    async def test_session_flag_decides_when_the_agent_has_none(self):
        agent = self.make_agent()
        agent._fake_session = SimpleNamespace(
            options=SimpleNamespace(use_tts_aligned_transcript=True))
        self.assertTrue(agent._aligned_transcript_on())
        agent._fake_session = SimpleNamespace(
            options=SimpleNamespace(use_tts_aligned_transcript=False))
        self.assertFalse(agent._aligned_transcript_on())

    async def test_not_running_agent_counts_as_not_aligned(self):
        self.assertFalse(self.make_agent()._aligned_transcript_on())

    async def test_language_setter_defaults_to_english(self):
        agent = self.make_agent("ar")
        self.assertEqual(agent.language, "ar")
        agent.language = ""
        self.assertEqual(agent.language, "en")

    async def test_speech_cleaning_is_not_done_twice(self):
        # The old tts_node override ran filter_markdown/filter_emoji again after the
        # session transforms. The cleaner covers both, so the override that exists now
        # (avatar signals and the lip-sync timeline share it) must hand the text on untouched:
        # markdown is not stripped here. See test_lipsync_timeline.py for the frame side.
        agent = self.make_agent()
        spoken = await _collect(agent.tts_node(_agen("This is **great** ", "news"), None))
        self.assertEqual(spoken, "This is **great** news")
        source = inspect.getsource(self.agent_class.AlSadiqAgent.tts_node)
        self.assertNotIn("filter_markdown", source)
        self.assertNotIn("filter_emoji", source)
        self.assertIn("Agent.default.tts_node(self, self.signals.tap_reply(text), model_settings)", source)

    async def test_tts_node_taps_the_reply_for_the_avatar(self):
        agent = self.make_agent()
        sent = []
        agent.signals.update = lambda **kv: sent.append(kv)
        reply = "Well done, that was very brave of you. Tell me more."
        spoken = await _collect(agent.tts_node(_agen(reply), None))
        self.assertEqual(spoken, reply)
        self.assertEqual(sent, [{"talk_style": "praise", "reply": "1"}])


    async def test_tts_node_is_the_scripture_backstop(self):
        agent = self.make_agent()
        spoken = await _collect(agent.tts_node(
            _agen(f"Look {OPEN}{PLACEHOLDER}{CLOSE} done"), None))
        self.assertNotIn(PLACEHOLDER, spoken)
        self.assertIn("done", spoken)


# ---------------------------------------------------------------------------
# Real livekit-agents 1.5.1
# ---------------------------------------------------------------------------


def _real_livekit_available() -> bool:
    if importlib.util.find_spec("livekit.agents") is None:
        return False
    try:
        import av  # noqa: F401
    except Exception:  # noqa: BLE001 - Windows application control can block the PyAV DLL
        for name in ("av", "av.audio", "av.audio.frame", "av.audio.resampler", "av.container",
                     "av.error", "av.filter", "av.codec", "av.codec.context"):
            sys.modules.setdefault(name, mock.MagicMock())
    try:
        import livekit.agents  # noqa: F401
        from livekit.agents.voice import generation  # noqa: F401
        return True
    except Exception:  # noqa: BLE001
        return False


_HAS_LIVEKIT = _real_livekit_available()
_HAS_ELEVEN_PLUGIN = _HAS_LIVEKIT and importlib.util.find_spec("livekit.plugins.elevenlabs") is not None


@unittest.skipUnless(_HAS_LIVEKIT, "livekit-agents is not installed (or cannot be imported)")
class RealLivekitTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        env_patch = mock.patch.dict(
            os.environ, {k: v for k, v in os.environ.items() if k not in _ELEVEN_ENV},
            clear=True,
        )
        env_patch.start()
        self.addCleanup(env_patch.stop)
        tts_factory._reset_warnings_for_tests()

    def test_livekit_agents_is_still_the_reviewed_pin(self):
        # The transcript and per-speech guard behaviour was verified against 1.5.1
        # (voice/agent_activity.py, voice/generation.py). Re-check both before upgrading.
        import livekit.agents as lk

        self.assertEqual(lk.__version__, "1.5.1")

    async def _run_speech(self, transforms, *segments):
        """Run one speech through livekit's real perform_tts_inference.

        Returns the text each segment handed to the TTS node.
        """
        from livekit.agents.types import FlushSentinel
        from livekit.agents.voice.generation import perform_tts_inference

        received: list[str] = []

        async def node(text, model_settings):
            received.append("".join([piece async for piece in text]))
            return
            yield  # makes this an (empty) async generator

        async def source():
            for i, segment in enumerate(segments):
                if i:
                    yield FlushSentinel()
                yield segment

        task, _data = perform_tts_inference(
            node=node, input=source(), model_settings=SimpleNamespace(),
            text_transforms=transforms,
        )
        await task
        return received

    async def test_session_accepts_the_transform_list(self):
        from livekit.agents import AgentSession

        transform = speech_tts_text_transform("en")
        session = AgentSession(tts_text_transforms=[transform], use_tts_aligned_transcript=False)
        self.assertEqual(list(session.options.tts_text_transforms), [transform])
        self.assertIs(session.options.use_tts_aligned_transcript, False)

    async def test_cleaner_runs_before_the_tts_node_and_replaces_the_defaults(self):
        received = await self._run_speech(
            [speech_tts_text_transform("en")], "I am **12** and I like 3 cats")
        self.assertEqual([r.strip() for r in received], ["I am twelve and I like three cats"])

    async def test_quran_guard_holds_across_real_flush_segments(self):
        received = await self._run_speech(
            [speech_tts_text_transform("en")],
            f"Listen {OPEN}{PLACEHOLDER}", f"{PLACEHOLDER}_MORE{CLOSE} and then more")
        joined = " ".join(received)
        self.assertEqual(len(received), 2)  # two segments, one speech
        self.assertIn(EN_PHRASE, received[0])
        self.assertNotIn(PLACEHOLDER, joined)
        self.assertNotIn("MORE", joined)
        self.assertIn("and then more", received[1])

    async def test_next_real_speech_is_not_swallowed_after_an_interrupted_one(self):
        transform = speech_tts_text_transform("en")
        await self._run_speech([transform], f"Listen {OPEN}{PLACEHOLDER}")  # ends inside
        received = await self._run_speech([transform], "Hello my friend.")
        self.assertEqual([r.strip() for r in received], ["Hello my friend."])

    async def test_language_callable_is_read_live_in_the_real_pipeline(self):
        lang = {"value": "en"}
        transform = speech_tts_text_transform(lambda: lang["value"])
        english = await self._run_speech([transform], "12 ")
        lang["value"] = "ar"
        arabic = await self._run_speech([transform], "12 ")
        self.assertEqual(english[0].strip(), prepare_for_tts("12", "en"))
        self.assertEqual(arabic[0].strip(), prepare_for_tts("12", "ar"))
        self.assertNotEqual(english, arabic)

    async def test_a_bracketed_quote_is_never_spoken_in_the_real_pipeline(self):
        received = await self._run_speech(
            [speech_tts_text_transform("en")],
            f"Here it is: {OPEN}{PLACEHOLDER}{CLOSE} Lovely, right?")
        joined = " ".join(received)
        self.assertNotIn(PLACEHOLDER, joined)
        self.assertIn(EN_PHRASE, joined)
        self.assertIn("Lovely, right?", joined)

    async def test_real_agent_transcript_is_guarded_and_cleaned_of_markdown(self):
        from conversation.agent.agent_class import AlSadiqAgent

        agent = AlSadiqAgent(db_session_id=1, child_id=2, language="ar")
        original = f"Day 12 {PBUH} and {OPEN}{PLACEHOLDER}{CLOSE} with **bold** text"
        shown = await _collect(agent.transcription_node(_agen(original), None))
        self.assertNotIn(PLACEHOLDER, shown)
        self.assertEqual(" ".join(shown.split()), f"Day 12 {PBUH} and with bold text")

    async def test_real_agent_tts_node_taps_the_cleaned_text_and_stays_silent_about_verses(self):
        from livekit.agents import Agent
        from livekit.agents.types import FlushSentinel
        from livekit.agents.voice.generation import perform_tts_inference

        from conversation.agent.agent_class import AlSadiqAgent

        agent = AlSadiqAgent(db_session_id=1, child_id=2, language="en")
        published: list[dict] = []
        agent.signals.update = lambda **kv: published.append(kv)
        seen: list[str] = []

        async def default_tts_node(_agent, text, _model_settings):
            seen.append("".join([piece async for piece in text]))
            return
            yield  # an (empty) async generator, like the real node's type

        async def source():
            yield f"Well done, you told the truth {OPEN}{PLACEHOLDER}{CLOSE} and that is brave. "
            yield FlushSentinel()
            yield "Here is more."

        with mock.patch.object(Agent.default, "tts_node", staticmethod(default_tts_node)):
            task, _data = perform_tts_inference(
                node=agent.tts_node, input=source(), model_settings=SimpleNamespace(),
                text_transforms=[speech_tts_text_transform(lambda: agent.language)],
            )
            await task
        self.assertEqual(len(seen), 2)  # one node call per flush segment
        self.assertNotIn(PLACEHOLDER, " ".join(seen))
        self.assertIn(EN_PHRASE, seen[0])
        # Each node call is a "reply" for the signals (see the module docstring).
        self.assertEqual(published, [{"talk_style": "praise", "reply": "1"},
                                     {"talk_style": "explain", "reply": "2"}])

    def test_agent_tts_node_matches_the_livekit_signature(self):
        from livekit.agents import Agent

        from conversation.agent.agent_class import AlSadiqAgent

        ours = inspect.signature(AlSadiqAgent.tts_node)
        base = inspect.signature(Agent.tts_node)
        self.assertEqual(list(ours.parameters), list(base.parameters))
        self.assertTrue(inspect.isasyncgenfunction(AlSadiqAgent.tts_node))

    def test_default_tts_node_uses_the_streaming_path(self):
        from livekit.agents import Agent

        source = inspect.getsource(Agent.default.tts_node)
        self.assertIn(".stream(", source)
        self.assertNotIn(".synthesize(", source)
        # Non-streaming TTS would be wrapped in a StreamAdapter that calls synthesize().
        self.assertIn("capabilities.streaming", source)

    @unittest.skipUnless(_HAS_ELEVEN_PLUGIN, "livekit-plugins-elevenlabs is not installed")
    def test_real_elevenlabs_plugin_is_streaming_without_word_timings(self):
        os.environ["ELEVEN_API_KEY"] = "dummy-key-for-offline-test"
        tts = tts_factory.build_tts("ar")
        self.assertEqual(type(tts).__module__.split(".")[-2:], ["elevenlabs", "tts"])
        self.assertTrue(tts.capabilities.streaming)
        self.assertFalse(tts.capabilities.aligned_transcript)
        self.assertEqual(tts.model, "eleven_flash_v2_5")

    @unittest.skipUnless(_HAS_ELEVEN_PLUGIN, "livekit-plugins-elevenlabs is not installed")
    def test_real_plugin_gets_the_fact_sheet_voice_settings(self):
        os.environ["ELEVEN_API_KEY"] = "dummy-key-for-offline-test"
        tts = tts_factory.build_tts("en")
        settings = tts._opts.voice_settings
        self.assertEqual(
            (settings.stability, settings.similarity_boost, settings.style,
             settings.use_speaker_boost, settings.speed),
            (0.65, 0.75, 0.0, True, 0.92),
        )
        self.assertEqual(tts._opts.apply_text_normalization, "auto")
        self.assertFalse(tts._opts.sync_alignment)

    @unittest.skipUnless(_HAS_ELEVEN_PLUGIN, "livekit-plugins-elevenlabs is not installed")
    def test_real_plugin_never_gets_v4_turbo(self):
        os.environ["ELEVEN_API_KEY"] = "dummy-key-for-offline-test"
        os.environ["ELEVEN_MODEL"] = "eleven_v4_turbo"
        with self.assertLogs(tts_factory.logger, level="WARNING"):
            tts = tts_factory.build_tts("ar")
        self.assertEqual(tts.model, "eleven_flash_v2_5")
