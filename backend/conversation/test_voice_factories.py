"""Unit tests for the TTS / STT provider factories (no network, plugins mocked)."""
import importlib.util
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from django.test import SimpleTestCase

from conversation.agent import stt_factory, tts_factory

ELEVEN_ENV_KEYS = (
    "TTS_PROVIDER", "ELEVEN_API_KEY", "ELEVEN_VOICE_ID_AR", "ELEVEN_VOICE_ID_EN",
    "ELEVEN_MODEL", "ELEVEN_STABILITY", "ELEVEN_SIMILARITY", "ELEVEN_SPEED",
    "ELEVEN_STYLE", "ELEVEN_SPEAKER_BOOST", "ELEVEN_TEXT_NORMALIZATION", "ELEVEN_ALIGNMENT", "ELEVEN_LANGUAGE_HINT",
    "XAI_TTS_VOICE", "XAI_TTS_LANGUAGE", "ARABIC_TTS_LOCALE", "STT_LANGUAGE",
    "STT_PROVIDER", "STT_SCRIBE_MODEL", "ELEVEN_KEY_FILE",
)
# scripts/voice lives outside the backend Docker build context, so skip when absent.
_VOICE_COMMON = Path(__file__).resolve().parents[2] / "scripts" / "voice" / "_common.py"


def _fake_elevenlabs():
    return SimpleNamespace(
        TTS=mock.MagicMock(name="ElevenTTS"),
        STT=mock.MagicMock(name="ElevenSTT"),
        VoiceSettings=mock.MagicMock(name="VoiceSettings"),
    )


class _FactoryTestBase(SimpleTestCase):
    def setUp(self):
        env = {k: v for k, v in os.environ.items() if k not in ELEVEN_ENV_KEYS}
        patcher = mock.patch.dict("os.environ", env, clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)
        tts_factory._reset_warnings_for_tests()
        stt_factory._reset_warnings_for_tests()

        self.eleven = _fake_elevenlabs()
        self.xai_cls = mock.MagicMock(name="XaiTTS")
        for target, value in (
            (tts_factory, "_load_elevenlabs_plugin"),
            (stt_factory, "_load_elevenlabs_plugin"),
        ):
            p = mock.patch.object(target, value, return_value=self.eleven)
            p.start()
            self.addCleanup(p.stop)
        p = mock.patch.object(tts_factory, "_load_xai_tts_class", return_value=self.xai_cls)
        p.start()
        self.addCleanup(p.stop)

    def set_env(self, **values):
        patcher = mock.patch.dict("os.environ", values)
        patcher.start()
        self.addCleanup(patcher.stop)


class TtsProviderSelectionTests(_FactoryTestBase):
    def test_default_provider_is_elevenlabs(self):
        self.set_env(ELEVEN_API_KEY="dummy")
        result = tts_factory.build_tts("en")
        self.assertIs(result, self.eleven.TTS.return_value)
        self.xai_cls.assert_not_called()

    def test_xai_provider_uses_existing_client_unchanged(self):
        self.set_env(TTS_PROVIDER="xai", ELEVEN_API_KEY="dummy")
        result = tts_factory.build_tts("en", xai_language="en")
        self.assertIs(result, self.xai_cls.return_value)
        self.xai_cls.assert_called_once_with(voice="leo", language="en")
        self.eleven.TTS.assert_not_called()

    def test_xai_rollback_reads_voice_env_and_derives_language(self):
        self.set_env(TTS_PROVIDER="XAI", XAI_TTS_VOICE="ara", ARABIC_TTS_LOCALE="ar-EG")
        tts_factory.build_tts("ar")
        self.xai_cls.assert_called_once_with(voice="ara", language="ar-EG")

    def test_xai_rollback_needs_no_eleven_key_and_says_it_was_operator_chosen(self):
        self.set_env(TTS_PROVIDER="xai")
        with self.assertNoLogs(tts_factory.logger, level="ERROR"):
            with self.assertLogs(tts_factory.logger, level="WARNING") as logs:
                tts_factory.build_tts("en", xai_language="auto")
        self.assertIn("operator", logs.output[0])

    def test_unknown_provider_uses_elevenlabs_with_warning(self):
        self.set_env(TTS_PROVIDER="bogus", ELEVEN_API_KEY="dummy")
        with self.assertLogs(tts_factory.logger, level="WARNING"):
            result = tts_factory.build_tts("en")
        self.assertIs(result, self.eleven.TTS.return_value)


class ElevenLabsConfigTests(_FactoryTestBase):
    def setUp(self):
        super().setUp()
        self.set_env(ELEVEN_API_KEY="dummy")

    def _kwargs(self):
        return self.eleven.TTS.call_args.kwargs

    def test_arabic_session_uses_arabic_voice(self):
        self.set_env(ELEVEN_VOICE_ID_AR="voice-ar", ELEVEN_VOICE_ID_EN="voice-en")
        tts_factory.build_tts("ar")
        self.assertEqual(self._kwargs()["voice_id"], "voice-ar")
        self.assertEqual(self._kwargs()["language"], "ar")

    def test_english_session_uses_english_voice(self):
        self.set_env(ELEVEN_VOICE_ID_AR="voice-ar", ELEVEN_VOICE_ID_EN="voice-en")
        tts_factory.build_tts("en")
        self.assertEqual(self._kwargs()["voice_id"], "voice-en")
        self.assertEqual(self._kwargs()["language"], "en")

    def test_voice_defaults_when_env_missing(self):
        tts_factory.build_tts("ar")
        self.assertEqual(self._kwargs()["voice_id"], tts_factory.DEFAULT_VOICE_ID_AR)
        tts_factory.build_tts("en")
        self.assertEqual(self._kwargs()["voice_id"], tts_factory.DEFAULT_VOICE_ID_EN)

    def test_default_model_is_flash(self):
        tts_factory.build_tts("en")
        self.assertEqual(self._kwargs()["model"], "eleven_flash_v2_5")

    def test_model_override_and_language_hint_dropped_for_multilingual_v2(self):
        self.set_env(ELEVEN_MODEL="eleven_multilingual_v2")
        tts_factory.build_tts("ar")
        self.assertEqual(self._kwargs()["model"], "eleven_multilingual_v2")
        self.assertNotIn("language", self._kwargs())

    def test_default_voice_settings_match_the_fact_sheet(self):
        # docs/hackathon/handoffs/07-elevenlabs-facts.md, "Recommended settings".
        tts_factory.build_tts("ar")
        self.eleven.VoiceSettings.assert_called_once_with(
            stability=0.65, similarity_boost=0.75, style=0.0, use_speaker_boost=True,
            speed=0.92,
        )
        self.assertIs(self._kwargs()["voice_settings"], self.eleven.VoiceSettings.return_value)

    def test_speaker_boost_can_be_switched_off(self):
        self.set_env(ELEVEN_SPEAKER_BOOST="off")
        tts_factory.build_tts("ar")
        self.assertIs(self.eleven.VoiceSettings.call_args.kwargs["use_speaker_boost"], False)

    def test_v4_turbo_is_never_offered(self):
        self.set_env(ELEVEN_MODEL="eleven_v4_turbo")
        with self.assertLogs(tts_factory.logger, level="WARNING") as logs:
            tts_factory.build_tts("ar")
        self.assertEqual(self._kwargs()["model"], "eleven_flash_v2_5")
        self.assertIn("eleven_v4_turbo", logs.output[0])
        self.assertNotIn("eleven_v4_turbo", tts_factory._LANGUAGE_HINT_MODELS)

    def test_word_timings_are_off_unless_the_transcript_needs_them(self):
        tts_factory.build_tts("ar")
        self.assertIs(self._kwargs()["sync_alignment"], False)
        self.assertNotIn("preferred_alignment", self._kwargs())

    def test_aligned_transcript_turns_word_timings_on(self):
        tts_factory.build_tts("ar", aligned_transcript=True)
        self.assertIs(self._kwargs()["sync_alignment"], True)
        self.assertEqual(self._kwargs()["preferred_alignment"], "original")

    def test_voice_settings_env_overrides(self):
        self.set_env(
            ELEVEN_STABILITY="0.7", ELEVEN_SIMILARITY="0.9",
            ELEVEN_SPEED="0.85", ELEVEN_STYLE="0.1",
        )
        tts_factory.build_tts("ar")
        self.eleven.VoiceSettings.assert_called_once_with(
            stability=0.7, similarity_boost=0.9, style=0.1, use_speaker_boost=True,
            speed=0.85,
        )

    def test_speed_is_clamped_and_bad_numbers_fall_back(self):
        self.set_env(ELEVEN_SPEED="5", ELEVEN_STABILITY="not-a-number")
        with self.assertLogs(tts_factory.logger, level="WARNING"):
            tts_factory.build_tts("ar")
        self.eleven.VoiceSettings.assert_called_once_with(
            stability=0.65, similarity_boost=0.75, style=0.0, use_speaker_boost=True,
            speed=1.2,
        )

    def test_text_normalization_override(self):
        self.set_env(ELEVEN_TEXT_NORMALIZATION="on")
        tts_factory.build_tts("ar")
        self.assertEqual(self._kwargs()["apply_text_normalization"], "on")

    def test_bad_text_normalization_falls_back_to_auto(self):
        self.set_env(ELEVEN_TEXT_NORMALIZATION="yes please")
        with self.assertLogs(tts_factory.logger, level="WARNING"):
            tts_factory.build_tts("ar")
        self.assertEqual(self._kwargs()["apply_text_normalization"], "auto")

    def test_transcript_alignment_defaults_to_original_text(self):
        tts_factory.build_tts("ar", aligned_transcript=True)
        self.assertEqual(self._kwargs()["preferred_alignment"], "original")

    def test_transcript_alignment_override_and_bad_value(self):
        self.set_env(ELEVEN_ALIGNMENT="Normalized")
        tts_factory.build_tts("en", aligned_transcript=True)
        self.assertEqual(self._kwargs()["preferred_alignment"], "normalized")
        self.set_env(ELEVEN_ALIGNMENT="exact")
        with self.assertLogs(tts_factory.logger, level="WARNING"):
            tts_factory.build_tts("en", aligned_transcript=True)
        self.assertEqual(self._kwargs()["preferred_alignment"], "original")

    def test_language_hint_can_be_switched_off(self):
        self.set_env(ELEVEN_LANGUAGE_HINT="off", ELEVEN_VOICE_ID_AR="voice-ar")
        tts_factory.build_tts("ar")
        self.assertNotIn("language", self._kwargs())
        self.assertEqual(self._kwargs()["voice_id"], "voice-ar")

    def test_unknown_session_language_gets_english_voice_and_no_hint(self):
        self.set_env(ELEVEN_VOICE_ID_AR="voice-ar", ELEVEN_VOICE_ID_EN="voice-en")
        tts_factory.build_tts("fr")
        self.assertEqual(self._kwargs()["voice_id"], "voice-en")
        self.assertNotIn("language", self._kwargs())


class TtsNoFallbackTests(_FactoryTestBase):
    """The lead's rule: ElevenLabs is the voice. When it cannot be used, fail clearly, never xAI."""

    def assert_clear_failure(self, code, *needles):
        with self.assertLogs(tts_factory.logger, level="ERROR") as logs:
            with self.assertRaises(tts_factory.VoiceConfigurationError) as ctx:
                tts_factory.build_tts("en", xai_language="en")
        self.assertEqual(ctx.exception.code, code)
        self.assertEqual(len(logs.records), 1)  # exactly one error line
        for needle in needles:
            self.assertIn(needle, logs.output[0])
        self.xai_cls.assert_not_called()  # nothing silently speaks with xAI
        self.eleven.TTS.assert_not_called()
        return logs.output[0]

    def test_missing_key_raises_a_clear_error_and_never_builds_xai(self):
        self.assert_clear_failure("missing_key", "ELEVEN_API_KEY", "No fallback voice")

    def test_every_call_without_a_key_fails_again(self):
        # Each session must fail on its own, not just the first one in the process.
        for _ in range(2):
            self.assert_clear_failure("missing_key")

    def test_missing_key_fails_even_when_an_xai_key_is_configured(self):
        self.set_env(XAI_API_KEY="xai-present-but-must-not-be-used")
        self.assert_clear_failure("missing_key")

    def test_blank_key_counts_as_missing(self):
        self.set_env(ELEVEN_API_KEY="   ")
        self.assert_clear_failure("missing_key")

    def test_example_placeholder_keys_count_as_missing(self):
        for placeholder in ("your-elevenlabs-api-key", "<your-elevenlabs-key>", "key here"):
            self.set_env(ELEVEN_API_KEY=placeholder)
            self.assert_clear_failure("missing_key")

    def test_plugin_build_failure_raises_and_never_builds_xai(self):
        self.set_env(ELEVEN_API_KEY="dummy-key-value-1234")
        self.eleven.TTS.side_effect = RuntimeError("boom")
        with self.assertLogs(tts_factory.logger, level="ERROR") as logs:
            with self.assertRaises(tts_factory.VoiceConfigurationError) as ctx:
                tts_factory.build_tts("en", xai_language="en")
        self.assertEqual(ctx.exception.code, "build_failed")
        self.assertIn("boom", logs.output[0])
        self.assertEqual(len(logs.records), 1)
        self.xai_cls.assert_not_called()

    def test_missing_plugin_raises_and_never_builds_xai(self):
        self.set_env(ELEVEN_API_KEY="dummy-key-value-1234")
        with (
            mock.patch.object(tts_factory, "_load_elevenlabs_plugin", side_effect=ImportError),
            self.assertLogs(tts_factory.logger, level="ERROR") as logs,
            self.assertRaises(tts_factory.VoiceConfigurationError) as ctx,
        ):
            tts_factory.build_tts("en", xai_language="en")
        self.assertEqual(ctx.exception.code, "plugin_unavailable")
        self.assertIn("livekit-plugins-elevenlabs", logs.output[0])
        self.xai_cls.assert_not_called()

    def test_the_key_never_appears_in_the_error_or_the_log(self):
        secret = "sk_super_secret_value_9999"
        self.set_env(ELEVEN_API_KEY=secret)
        self.eleven.TTS.side_effect = RuntimeError(f"bad auth header {secret}")
        with self.assertLogs(tts_factory.logger, level="ERROR") as logs:
            with self.assertRaises(tts_factory.VoiceConfigurationError) as ctx:
                tts_factory.build_tts("en")
        self.assertNotIn(secret, logs.output[0])
        self.assertNotIn(secret, str(ctx.exception))

    def test_unknown_provider_value_never_selects_xai(self):
        self.set_env(TTS_PROVIDER="xia")  # a typo is not an operator choice of xAI
        with self.assertLogs(tts_factory.logger, level="WARNING"):
            with self.assertRaises(tts_factory.VoiceConfigurationError):
                tts_factory.build_tts("en", xai_language="en")
        self.xai_cls.assert_not_called()

    def test_source_has_one_path_to_xai_and_it_is_the_explicit_switch(self):
        import inspect

        source = inspect.getsource(tts_factory.build_tts)
        self.assertEqual(source.count("_build_xai("), 1)
        self.assertIn("chosen == PROVIDER_XAI", source.split("_build_xai(")[0])
        # `chosen` only comes from the operator's explicit provider or TTS_PROVIDER.
        self.assertIn("provider if provider in", source)
        self.assertIn("else selected_provider()", source)

    def test_per_session_provider_elevenlabs_beats_an_xai_env(self):
        self.set_env(TTS_PROVIDER="xai", ELEVEN_API_KEY="dummy-key-value-1234")
        tts_factory.build_tts("en", xai_language="en", provider="elevenlabs")
        self.xai_cls.assert_not_called()
        self.eleven.TTS.assert_called_once()

    def test_per_session_provider_xai_is_an_explicit_operator_choice(self):
        with self.assertLogs(tts_factory.logger, level="WARNING") as logs:
            tts_factory.build_tts("en", xai_language="en", provider="xai")
        self.xai_cls.assert_called_once()
        self.assertIn("VOICE_MODE=xai", logs.output[0])

    def test_per_session_elevenlabs_failure_with_a_working_xai_key_still_fails(self):
        self.set_env(XAI_API_KEY="xai-present-but-must-not-be-used")
        with self.assertLogs(tts_factory.logger, level="ERROR"):
            with self.assertRaises(tts_factory.VoiceConfigurationError):
                tts_factory.build_tts("en", xai_language="en", provider="elevenlabs")
        self.xai_cls.assert_not_called()

    def test_an_unknown_per_session_provider_is_ignored(self):
        with self.assertLogs(tts_factory.logger, level="ERROR"):
            with self.assertRaises(tts_factory.VoiceConfigurationError):
                tts_factory.build_tts("en", xai_language="en", provider="banana")
        self.xai_cls.assert_not_called()

    def test_explicit_xai_switch_still_works_and_says_so_once(self):
        self.set_env(TTS_PROVIDER="xai")
        with self.assertLogs(tts_factory.logger, level="WARNING") as logs:
            tts_factory.build_tts("en", xai_language="en")
            tts_factory.build_tts("en", xai_language="en")
        self.assertEqual(len(logs.records), 1)
        self.assertIn("operator", logs.output[0])


class TtsRuntimeFailureTests(SimpleTestCase):
    """explain_tts_failure names the cause of an error the API raised mid-session."""

    def setUp(self):
        tts_factory._reset_warnings_for_tests()
        self.addCleanup(tts_factory._reset_warnings_for_tests)

    class _Status(Exception):
        def __init__(self, message, status_code=-1, body=None):
            super().__init__(message)
            self.status_code = status_code
            self.body = body

    def test_rejected_key_from_a_handshake_error_wrapped_by_the_plugin(self):
        handshake = self._Status("401, message='Invalid response status'", status_code=401)
        try:
            try:
                raise handshake
            except Exception as inner:
                raise ConnectionError("could not connect to ElevenLabs") from inner
        except ConnectionError as outer:
            code, cause = tts_factory.explain_tts_failure(outer)
        self.assertEqual(code, "key_rejected")
        self.assertIn("ELEVEN_API_KEY", cause)

    def test_rejected_key_from_an_api_message(self):
        code, _ = tts_factory.explain_tts_failure(RuntimeError("invalid_api_key: bad key"))
        self.assertEqual(code, "key_rejected")

    def test_rejected_voice(self):
        code, cause = tts_factory.explain_tts_failure(RuntimeError("Voice not found: abc"))
        self.assertEqual(code, "voice_rejected")
        self.assertIn("ELEVEN_VOICE_ID", cause)

    def test_quota_and_plan_problems(self):
        for exc in (self._Status("x", status_code=402), RuntimeError("quota_exceeded"),
                    RuntimeError("paid_plan_required")):
            self.assertEqual(tts_factory.explain_tts_failure(exc)[0], "quota_or_plan")

    def test_network_problem(self):
        code, _ = tts_factory.explain_tts_failure(TimeoutError("timed out"))
        self.assertEqual(code, "unreachable")

    def _plugin_logs_an_api_error(self, reason, message):
        # What livekit-plugins-elevenlabs 1.5.1 really logs when ElevenLabs refuses a request.
        import logging

        tts_factory.install_api_error_capture()
        logging.getLogger("livekit.plugins.elevenlabs").error(
            "elevenlabs tts returned error",
            extra={"context_id": "c", "error": reason,
                   "data": {"message": message, "error": reason, "code": 1008}},
        )

    def test_the_real_reason_logged_by_the_plugin_beats_the_generic_connection_closed(self):
        generic = self._Status("connection closed")  # what the session finally sees
        self._plugin_logs_an_api_error("invalid_api_key", "Invalid API key")
        self.assertEqual(tts_factory.explain_tts_failure(generic)[0], "key_rejected")
        self._plugin_logs_an_api_error(
            "voice_id_does_not_exist", "A voice with voice_id abc does not exist.")
        self.assertEqual(tts_factory.explain_tts_failure(generic)[0], "voice_rejected")

    def test_an_old_api_reason_is_not_blamed_for_a_new_failure(self):
        self._plugin_logs_an_api_error("invalid_api_key", "Invalid API key")
        with mock.patch.object(tts_factory.time, "monotonic",
                               return_value=tts_factory._last_api_error["at"] + 10_000):
            code, _ = tts_factory.explain_tts_failure(ValueError("something odd"))
        self.assertEqual(code, "failed")

    def test_anything_else_is_reported_without_the_message_text(self):
        code, cause = tts_factory.explain_tts_failure(ValueError("something odd"))
        self.assertEqual(code, "failed")
        self.assertNotIn("something odd", cause)
        self.assertEqual(tts_factory.explain_tts_failure(None)[0], "failed")


class SttFactoryTests(_FactoryTestBase):
    def setUp(self):
        super().setUp()
        self.openai_stt = mock.MagicMock(name="OpenAISTT")
        self.openai_factory = mock.MagicMock(return_value=self.openai_stt)

    def test_default_is_openai(self):
        self.set_env(ELEVEN_API_KEY="dummy")
        result = stt_factory.build_stt("ar", openai_factory=self.openai_factory)
        self.assertIs(result, self.openai_stt)
        self.eleven.STT.assert_not_called()

    def test_scribe_uses_realtime_model_language_and_keyterms(self):
        self.set_env(STT_PROVIDER="scribe", ELEVEN_API_KEY="dummy")
        result = stt_factory.build_stt(
            "ar", openai_factory=self.openai_factory, theme_names=["Honesty", "Patience"],
        )
        self.assertIs(result, self.eleven.STT.return_value)
        kwargs = self.eleven.STT.call_args.kwargs
        self.assertEqual(kwargs["model_id"], "scribe_v2_realtime")
        self.assertEqual(kwargs["language_code"], "ar")
        self.assertIn("Honesty", kwargs["keyterms"])
        self.assertIn("الصبر", kwargs["keyterms"])
        self.openai_factory.assert_not_called()

    def test_scribe_english_has_only_english_theme_keyterms(self):
        self.set_env(STT_PROVIDER="scribe", ELEVEN_API_KEY="dummy", STT_SCRIBE_MODEL="scribe_v2")
        stt_factory.build_stt("en", openai_factory=self.openai_factory, theme_names=["Kindness"])
        kwargs = self.eleven.STT.call_args.kwargs
        self.assertEqual(kwargs["model_id"], "scribe_v2")
        self.assertEqual(kwargs["language_code"], "en")
        self.assertEqual(kwargs["keyterms"], ["Kindness"])

    def test_scribe_without_key_fails_clearly_and_never_uses_openai(self):
        self.set_env(STT_PROVIDER="scribe")
        for _ in range(2):  # every session fails on its own
            with self.assertLogs(tts_factory.logger, level="ERROR") as logs:
                with self.assertRaises(tts_factory.VoiceConfigurationError) as ctx:
                    stt_factory.build_stt("ar", openai_factory=self.openai_factory)
            self.assertEqual(ctx.exception.code, "missing_key")
            self.assertEqual(len(logs.records), 1)
            self.assertIn("STT_PROVIDER=scribe", logs.output[0])
        self.openai_factory.assert_not_called()

    def test_scribe_with_placeholder_key_fails_clearly(self):
        self.set_env(STT_PROVIDER="scribe", ELEVEN_API_KEY="your-elevenlabs-api-key")
        with self.assertLogs(tts_factory.logger, level="ERROR"):
            with self.assertRaises(tts_factory.VoiceConfigurationError):
                stt_factory.build_stt("ar", openai_factory=self.openai_factory)
        self.openai_factory.assert_not_called()
        self.eleven.STT.assert_not_called()

    def test_scribe_plugin_failure_fails_clearly_and_never_uses_openai(self):
        self.set_env(STT_PROVIDER="scribe", ELEVEN_API_KEY="dummy-key-value-1234")
        self.eleven.STT.side_effect = RuntimeError("boom")
        with self.assertLogs(tts_factory.logger, level="ERROR") as logs:
            with self.assertRaises(tts_factory.VoiceConfigurationError) as ctx:
                stt_factory.build_stt("ar", openai_factory=self.openai_factory)
        self.assertEqual(ctx.exception.code, "build_failed")
        self.assertIn("boom", logs.output[0])
        self.openai_factory.assert_not_called()

    def test_keyterms_are_deduplicated_capped_and_limited_in_length(self):
        names = ["Honesty", "honesty", "", "x" * 60, "one two three four five six"]
        names += [f"term{i}" for i in range(80)]
        terms = stt_factory.build_keyterms("en", names)
        self.assertEqual(terms.count("Honesty"), 1)
        self.assertNotIn("", terms)
        self.assertLessEqual(len(terms), stt_factory.MAX_KEYTERMS)
        self.assertTrue(all(len(t) < 50 and len(t.split()) <= 5 for t in terms))


@unittest.skipUnless(_VOICE_COMMON.is_file(), "scripts/voice not in this checkout")
class VoiceToolKeyFileTests(SimpleTestCase):
    """scripts/voice reads the key file; Windows editors and PowerShell add BOMs."""

    def setUp(self):
        spec = importlib.util.spec_from_file_location("voice_common_under_test", _VOICE_COMMON)
        self.common = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.common)
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.path = Path(tmp.name) / "eleven-key.txt"
        env = {k: v for k, v in os.environ.items() if k not in ELEVEN_ENV_KEYS}
        env["ELEVEN_KEY_FILE"] = str(self.path)
        patcher = mock.patch.dict("os.environ", env, clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_key_file_encodings(self):
        fake = "sk_test_not_a_real_key"
        for raw in (
            fake.encode() + b"\n",
            b"\xef\xbb\xbf" + fake.encode() + b"\r\n",
            b"\xff\xfe" + (fake + "\r\n").encode("utf-16-le"),
            f'ELEVEN_API_KEY="{fake}"\n'.encode(),
        ):
            self.path.write_bytes(raw)
            self.assertEqual(self.common.load_eleven_key(), fake)

    def test_missing_or_empty_key_file(self):
        self.assertIsNone(self.common.load_eleven_key())
        self.path.write_bytes(b"\r\n")
        self.assertIsNone(self.common.load_eleven_key())

    def test_environment_wins_over_file(self):
        self.path.write_bytes(b"from-file")
        with mock.patch.dict("os.environ", {"ELEVEN_API_KEY": "from-env"}):
            self.assertEqual(self.common.load_eleven_key(), "from-env")
