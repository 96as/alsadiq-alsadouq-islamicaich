"""Tests for the demo credit and safety guards.

Redis is replaced by a small in-memory fake (fakeredis is not a dependency). No livekit
install is needed: the agent half is tested through injected callables.

Run from backend/:  python manage.py test conversation.test_demo_guards \
    --settings=config.settings_sqlite_test
"""
from __future__ import annotations

import asyncio
import io
import json
import os
import unittest
from datetime import timedelta
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.cache import caches
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from authentication.models import ChildProfile
from conversation import demo_guards
from conversation.agent import demo_limits
from conversation.models import Session
from conversation.throttles import SessionStartThrottle

User = get_user_model()

_GUARD_ENV = (
    "DEMO_GUARDS", "DEBUG", "DEMO_SESSION_MAX_SECONDS", "DEMO_DAILY_SESSIONS",
    "ELEVEN_DAILY_CHAR_CAP", "DEMO_SESSION_START_PER_HOUR", "DEMO_GOODBYE_LEAD_SECONDS",
    "DEMO_SESSION_GRACE_SECONDS", "DEMO_DAY_UTC_OFFSET_HOURS", "TTS_PROVIDER",
    "REDIS_URL", "REDIS_HOST", "JUDGE_DAILY_SESSIONS", "JUDGE_SESSION_START_PER_HOUR",
)


class FakeRedis:
    """Just the commands demo_guards uses, in memory."""

    def __init__(self):
        self.data: dict[str, str] = {}
        self.ttl: dict[str, int] = {}

    def get(self, key):
        return self.data.get(key)

    def set(self, key, value, ex=None):
        self.data[key] = str(value)
        if ex:
            self.ttl[key] = ex
        return True

    def delete(self, key):
        self.data.pop(key, None)

    def incr(self, key):
        return self.incrby(key, 1)

    def incrby(self, key, amount):
        self.data[key] = str(int(self.data.get(key, 0)) + amount)
        return int(self.data[key])

    def decr(self, key):
        return self.incrby(key, -1)

    def expire(self, key, seconds):
        self.ttl[key] = seconds

    def scan_iter(self, match=None, count=None):
        import fnmatch

        return iter([k for k in list(self.data) if fnmatch.fnmatch(k, match or "*")])


class BrokenRedis:
    def __getattr__(self, name):
        def boom(*args, **kwargs):
            raise ConnectionError("redis is down")
        return boom


class GuardTestCase(TestCase):
    """Guards ON, Redis faked, env clean."""

    env: dict = {}
    redis_class = FakeRedis

    def setUp(self):
        base = {k: v for k, v in os.environ.items() if k not in _GUARD_ENV}
        base["DEBUG"] = "0"
        base.update(self.env)
        patcher = mock.patch.dict(os.environ, base, clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)
        demo_guards._reset_for_tests()
        self.addCleanup(demo_guards._reset_for_tests)
        self.redis = self.redis_class()
        rpatch = mock.patch.object(demo_guards, "redis_client", lambda: self.redis)
        rpatch.start()
        self.addCleanup(rpatch.stop)
        caches["guards"].clear()
        self.addCleanup(caches["guards"].clear)
        caches["throttle"].clear()
        self.addCleanup(caches["throttle"].clear)


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------


class ConfigTests(GuardTestCase):
    def test_defaults(self):
        cfg = demo_guards.config()
        self.assertTrue(cfg.active)
        self.assertEqual(cfg.session_max_seconds, 300)
        self.assertEqual(cfg.daily_sessions, 3)
        self.assertEqual(cfg.eleven_daily_chars, 20000)
        self.assertEqual(cfg.session_start_per_hour, 6)

    @mock.patch.dict(os.environ, {"DEMO_SESSION_MAX_SECONDS": "90", "DEMO_DAILY_SESSIONS": "2",
                                  "ELEVEN_DAILY_CHAR_CAP": "500",
                                  "DEMO_SESSION_START_PER_HOUR": "4"})
    def test_every_limit_is_env_configurable(self):
        cfg = demo_guards.config()
        self.assertEqual((cfg.session_max_seconds, cfg.daily_sessions, cfg.eleven_daily_chars,
                          cfg.session_start_per_hour), (90, 2, 500, 4))

    @mock.patch.dict(os.environ, {"DEMO_DAILY_SESSIONS": "banana"})
    def test_a_bad_number_falls_back_to_the_default(self):
        self.assertEqual(demo_guards.config().daily_sessions, 3)

    @mock.patch.dict(os.environ, {"DEBUG": "1"})
    def test_guards_are_off_when_debug_is_on(self):
        cfg = demo_guards.config()
        self.assertFalse(cfg.active)
        self.assertEqual((cfg.session_max_seconds, cfg.daily_sessions, cfg.eleven_daily_chars,
                          cfg.session_start_per_hour), (0, 0, 0, 0))

    @mock.patch.dict(os.environ, {"DEBUG": "1", "DEMO_GUARDS": "1"})
    def test_demo_guards_1_turns_them_on_even_with_debug(self):
        self.assertTrue(demo_guards.config().active)
        self.assertEqual(demo_guards.config().daily_sessions, 3)

    @mock.patch.dict(os.environ, {"DEBUG": "0", "DEMO_GUARDS": "0"})
    def test_demo_guards_0_turns_them_off(self):
        self.assertFalse(demo_guards.config().active)

    def test_unset_debug_counts_as_off_so_guards_are_on(self):
        os.environ.pop("DEBUG")
        self.assertTrue(demo_guards.guards_active())

    @mock.patch.dict(os.environ, {"DEMO_DAY_UTC_OFFSET_HOURS": "0"})
    def test_day_follows_the_offset(self):
        a = demo_guards.today()
        os.environ["DEMO_DAY_UTC_OFFSET_HOURS"] = "14"
        b = demo_guards.today()
        self.assertRegex(a, r"^\d{4}-\d{2}-\d{2}$")
        self.assertRegex(b, r"^\d{4}-\d{2}-\d{2}$")

    def test_messages_exist_in_both_languages_without_scripture(self):
        for code in ("daily_limit", "rate_limited", "voice_resting", "voice_off"):
            message = demo_guards.message_for(code)
            self.assertTrue(message["ar"] and message["en"], code)
        self.assertNotIn("﴿", json.dumps(demo_guards.GOODBYE, ensure_ascii=False))
        self.assertTrue(demo_guards.goodbye_for("ar"))
        self.assertTrue(demo_guards.goodbye_for("en-US"))
        self.assertEqual(demo_guards.goodbye_for(None), demo_guards.goodbye_for("en"))
        self.assertNotEqual(demo_guards.goodbye_for("ar"), demo_guards.goodbye_for("en"))


# ---------------------------------------------------------------------------
# Voice mode: kill switch, env, budget. Never xAI on its own.
# ---------------------------------------------------------------------------


class ResolveVoiceTests(GuardTestCase):
    def test_default_is_elevenlabs(self):
        decision = demo_guards.resolve_voice()
        self.assertEqual((decision.mode, decision.reason), ("eleven", "env"))
        self.assertIsNone(decision.notice)

    def test_env_xai_is_honoured_only_because_an_operator_set_it(self):
        os.environ["TTS_PROVIDER"] = "xai"
        self.assertEqual(demo_guards.resolve_voice().mode, "xai")

    def test_unknown_env_provider_is_elevenlabs(self):
        os.environ["TTS_PROVIDER"] = "something-else"
        self.assertEqual(demo_guards.resolve_voice().mode, "eleven")

    def test_redis_switch_wins_over_env(self):
        os.environ["TTS_PROVIDER"] = "xai"
        for mode in ("eleven", "text", "off", "xai"):
            self.redis.set("VOICE_MODE", mode)
            decision = demo_guards.resolve_voice()
            self.assertEqual((decision.mode, decision.reason), (mode, "operator"))

    def test_switch_value_is_trimmed_and_case_insensitive(self):
        self.redis.set("VOICE_MODE", "  TEXT ")
        self.assertEqual(demo_guards.resolve_voice().mode, "text")

    def test_a_garbage_switch_is_ignored(self):
        self.redis.set("VOICE_MODE", "banana")
        self.assertEqual(demo_guards.resolve_voice().mode, "eleven")

    def test_text_and_off_carry_a_notice(self):
        self.redis.set("VOICE_MODE", "text")
        self.assertEqual(demo_guards.resolve_voice().notice, "voice_resting")
        self.redis.set("VOICE_MODE", "off")
        self.assertEqual(demo_guards.resolve_voice().notice, "voice_off")

    def test_budget_used_up_goes_text_only_never_xai(self):
        self.redis.set(f"demo:eleven_chars:{demo_guards.today()}", 20000)
        decision = demo_guards.resolve_voice()
        self.assertEqual(decision.mode, "text")
        self.assertEqual(decision.reason, "eleven_daily_cap")
        self.assertEqual(decision.notice, "voice_resting")

    def test_budget_used_up_with_an_xai_env_is_still_not_changed_by_the_cap(self):
        # The cap guards ElevenLabs. An operator who chose xai by hand keeps xai.
        os.environ["TTS_PROVIDER"] = "xai"
        self.redis.set(f"demo:eleven_chars:{demo_guards.today()}", 999999)
        self.assertEqual(demo_guards.resolve_voice().mode, "xai")

    def test_below_the_budget_stays_elevenlabs(self):
        self.redis.set(f"demo:eleven_chars:{demo_guards.today()}", 19999)
        self.assertEqual(demo_guards.resolve_voice().mode, "eleven")

    @mock.patch.dict(os.environ, {"ELEVEN_DAILY_CHAR_CAP": "0"})
    def test_zero_cap_means_no_cap(self):
        self.redis.set(f"demo:eleven_chars:{demo_guards.today()}", 10**9)
        self.assertEqual(demo_guards.resolve_voice().mode, "eleven")

    def test_a_new_day_starts_with_a_fresh_budget(self):
        self.redis.set("demo:eleven_chars:2000-01-01", 10**9)
        self.assertEqual(demo_guards.resolve_voice().mode, "eleven")

    def test_add_eleven_chars_counts_and_sets_an_expiry(self):
        demo_guards.add_eleven_chars(120)
        demo_guards.add_eleven_chars(30)
        demo_guards.add_eleven_chars(0)
        key = f"demo:eleven_chars:{demo_guards.today()}"
        self.assertEqual(demo_guards.eleven_chars_today(), 150)
        self.assertIn(key, self.redis.ttl)

    def test_set_and_clear_the_stored_mode(self):
        self.assertTrue(demo_guards.set_stored_voice_mode("text"))
        self.assertEqual(demo_guards.stored_voice_mode(), "text")
        self.assertTrue(demo_guards.set_stored_voice_mode(None))
        self.assertIsNone(demo_guards.stored_voice_mode())
        with self.assertRaises(ValueError):
            demo_guards.set_stored_voice_mode("banana")

    def test_the_module_never_picks_xai_by_itself(self):
        import inspect

        source = inspect.getsource(demo_guards.resolve_voice)
        self.assertNotIn("MODE_XAI", source)


class RedisDownTests(GuardTestCase):
    redis_class = BrokenRedis

    def test_everything_fails_open(self):
        decision = demo_guards.resolve_voice()
        self.assertEqual(decision.mode, "eleven")
        self.assertIsNone(demo_guards.eleven_chars_today())
        demo_guards.add_eleven_chars(10)  # no exception
        self.assertIsNone(demo_guards.load_session_state(1))

    def test_daily_cap_falls_back_to_counting_sessions(self):
        user = User.objects.create_user(username="kid", password="x", is_child=True)
        child = ChildProfile.objects.create(
            user=user, nickname="K", gender="male", birth_year=2015)
        for _ in range(3):
            Session.objects.create(child=child, livekit_room_name=f"r{_}")
        demo_guards._reset_for_tests()
        self.assertFalse(demo_guards.reserve_daily_session(child.id))
        other = ChildProfile.objects.create(
            user=User.objects.create_user(username="kid2", password="x", is_child=True),
            nickname="K2", gender="male", birth_year=2015)
        demo_guards._reset_for_tests()
        self.assertTrue(demo_guards.reserve_daily_session(other.id))

    def test_the_status_command_says_redis_is_down(self):
        out = io.StringIO()
        call_command("voice_mode", stdout=out)
        self.assertIn("NOT reachable", out.getvalue())


# ---------------------------------------------------------------------------
# Daily sessions per child
# ---------------------------------------------------------------------------


class RedisNotConfiguredTests(unittest.TestCase):
    """No REDIS_HOST / REDIS_URL at all (for example an agent container without it)."""

    def setUp(self):
        env = {k: v for k, v in os.environ.items() if k not in _GUARD_ENV}
        patcher = mock.patch.dict(os.environ, env, clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)
        demo_guards._reset_for_tests()
        self.addCleanup(demo_guards._reset_for_tests)

    def test_guards_on_without_redis_log_one_clear_error(self):
        os.environ["DEBUG"] = "0"
        with self.assertLogs(demo_guards.logger, level="ERROR") as logs:
            self.assertIsNone(demo_guards.redis_client())
            self.assertIsNone(demo_guards.redis_client())
            demo_guards.add_eleven_chars(10)
        self.assertEqual(len(logs.records), 1)
        self.assertIn("REDIS_HOST", logs.output[0])

    def test_guards_off_without_redis_stay_quiet(self):
        os.environ["DEBUG"] = "1"
        with self.assertNoLogs(demo_guards.logger, level="ERROR"):
            self.assertIsNone(demo_guards.redis_client())


class DailySessionTests(GuardTestCase):
    def test_three_then_refused_and_a_refusal_is_not_counted(self):
        results = [demo_guards.reserve_daily_session(7) for _ in range(5)]
        self.assertEqual(results, [True, True, True, False, False])
        self.assertEqual(self.redis.get(f"demo:sessions:7:{demo_guards.today()}"), "3")

    def test_children_are_counted_separately(self):
        for _ in range(3):
            demo_guards.reserve_daily_session(1)
        self.assertTrue(demo_guards.reserve_daily_session(2))

    def test_release_gives_the_slot_back(self):
        for _ in range(3):
            demo_guards.reserve_daily_session(1)
        demo_guards.release_daily_session(1)
        self.assertTrue(demo_guards.reserve_daily_session(1))

    @mock.patch.dict(os.environ, {"DEMO_DAILY_SESSIONS": "0"})
    def test_zero_is_unlimited(self):
        self.assertTrue(all(demo_guards.reserve_daily_session(1) for _ in range(20)))

    @mock.patch.dict(os.environ, {"DEBUG": "1"})
    def test_off_in_debug(self):
        self.assertTrue(all(demo_guards.reserve_daily_session(1) for _ in range(20)))

    def test_check_session_start_order_and_grant(self):
        grant = demo_guards.check_session_start(5)
        self.assertEqual(grant.max_seconds, 300)
        self.assertTrue(grant.reserved)
        self.assertEqual(grant.decision.mode, "eleven")

    def test_check_session_start_off_is_refused_before_a_slot_is_used(self):
        self.redis.set("VOICE_MODE", "off")
        with self.assertRaises(demo_guards.GuardDenied) as ctx:
            demo_guards.check_session_start(5)
        self.assertEqual((ctx.exception.code, ctx.exception.http_status), ("voice_off", 503))
        self.assertIsNone(self.redis.get(f"demo:sessions:5:{demo_guards.today()}"))

    def test_check_session_start_daily_limit(self):
        for _ in range(3):
            demo_guards.check_session_start(5)
        with self.assertRaises(demo_guards.GuardDenied) as ctx:
            demo_guards.check_session_start(5)
        self.assertEqual((ctx.exception.code, ctx.exception.http_status), ("daily_limit", 429))

    def test_budget_used_up_is_a_text_grant_not_a_denial(self):
        self.redis.set(f"demo:eleven_chars:{demo_guards.today()}", 20000)
        grant = demo_guards.check_session_start(5)
        self.assertEqual(grant.decision.mode, "text")


class SessionStateTests(GuardTestCase):
    def test_round_trip(self):
        grant = demo_guards.SessionGrant(
            demo_guards.VoiceDecision("text", "operator", "voice_resting"), 300, True)
        demo_guards.save_session_state(11, grant)
        state = demo_guards.load_session_state(11)
        self.assertEqual((state["mode"], state["max_seconds"]), ("text", 300))
        self.assertIn("demo:session:11", self.redis.ttl)

    def test_missing_or_garbled_state_is_none(self):
        self.assertIsNone(demo_guards.load_session_state(99))
        self.redis.set("demo:session:12", "{not json")
        self.assertIsNone(demo_guards.load_session_state(12))
        self.redis.set("demo:session:13", json.dumps({"mode": "banana"}))
        self.assertIsNone(demo_guards.load_session_state(13))


class UsageReportTests(GuardTestCase):
    def test_report(self):
        demo_guards.reserve_daily_session(1)
        demo_guards.reserve_daily_session(1)
        demo_guards.reserve_daily_session(2)
        demo_guards.add_eleven_chars(42)
        report = demo_guards.usage_report()
        self.assertEqual(report["sessions_today"], 3)
        self.assertEqual(report["children_today"], 2)
        self.assertEqual(report["eleven_chars"], 42)
        self.assertEqual(report["eleven_char_cap"], 20000)
        self.assertTrue(report["redis"])
        self.assertEqual(report["decision"]["mode"], "eleven")


# ---------------------------------------------------------------------------
# manage.py voice_mode
# ---------------------------------------------------------------------------


class VoiceModeCommandTests(GuardTestCase):
    def run_command(self, *args):
        out = io.StringIO()
        call_command("voice_mode", *args, stdout=out)
        return out.getvalue()

    def test_status_shows_usage_and_changes_nothing(self):
        demo_guards.add_eleven_chars(77)
        text = self.run_command()
        self.assertIn("ElevenLabs chars:    77 / 20000", text)
        self.assertIn("VOICE_MODE (Redis):  unset", text)
        self.assertIsNone(self.redis.get("VOICE_MODE"))

    def test_each_mode_is_written_to_redis(self):
        for mode in ("text", "off", "eleven", "xai"):
            text = self.run_command(mode)
            self.assertEqual(self.redis.get("VOICE_MODE"), mode)
            self.assertIn(f"VOICE_MODE set to {mode}", text)
            self.assertIn(f"new sessions get:    {mode}", text)

    def test_auto_clears_the_switch(self):
        self.run_command("text")
        text = self.run_command("auto")
        self.assertIsNone(self.redis.get("VOICE_MODE"))
        self.assertIn("cleared", text)

    def test_an_unknown_mode_is_rejected(self):
        with self.assertRaises(CommandError):
            self.run_command("banana")

    def test_no_redis_is_an_error_not_a_silent_success(self):
        with mock.patch.object(demo_guards, "redis_client", lambda: None):
            with self.assertRaises(CommandError):
                self.run_command("text")


# ---------------------------------------------------------------------------
# The session start endpoint
# ---------------------------------------------------------------------------


class StartSessionEndpointTests(GuardTestCase):
    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(
            username="demo_kid", password="pass12345", is_child=True)
        self.child = ChildProfile.objects.create(
            user=self.user, nickname="Kid", gender="male", birth_year=2015,
            language_preference="en")
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.url = reverse("conversation:start_session")
        pipeline = mock.patch("reporting.services.run_post_session_pipeline")
        pipeline.start()
        self.addCleanup(pipeline.stop)

    def test_success_carries_mode_limit_and_end_time(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertEqual(body["voice_mode"], "eleven")
        self.assertIsNone(body["notice"])
        self.assertEqual(body["max_seconds"], 300)
        self.assertTrue(body["session_ends_at"])
        self.assertTrue(body["livekit_token"])
        state = demo_guards.load_session_state(body["session_id"])
        self.assertEqual((state["mode"], state["max_seconds"]), ("eleven", 300))

    def test_token_lives_a_little_longer_than_the_session(self):
        import jwt

        body = self.client.post(self.url).json()
        claims = jwt.decode(body["livekit_token"], options={"verify_signature": False})
        self.assertLessEqual(claims["exp"] - claims["nbf"], 300 + 120 + 5)

    def test_fourth_session_of_the_day_is_refused_with_both_languages(self):
        for _ in range(3):
            self.assertEqual(self.client.post(self.url).status_code, 201)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 429)
        body = response.json()
        self.assertEqual(body["code"], "daily_limit")
        self.assertEqual(body["detail"], body["message"]["en"])  # the child prefers English
        self.assertTrue(body["message"]["ar"])
        self.assertEqual(Session.objects.filter(child=self.child).count(), 3)

    def test_arabic_child_gets_the_arabic_text_in_detail(self):
        self.child.language_preference = "ar"
        self.child.save()
        for _ in range(3):
            self.client.post(self.url)
        body = self.client.post(self.url).json()
        self.assertEqual(body["detail"], body["message"]["ar"])

    def test_off_is_503_and_creates_no_session(self):
        self.redis.set("VOICE_MODE", "off")
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["code"], "voice_off")
        self.assertEqual(Session.objects.count(), 0)

    def test_text_mode_has_a_friendly_notice(self):
        self.redis.set("VOICE_MODE", "text")
        body = self.client.post(self.url).json()
        self.assertEqual(body["voice_mode"], "text")
        self.assertEqual(body["notice"]["code"], "voice_resting")
        self.assertTrue(body["notice"]["ar"] and body["notice"]["en"])

    def test_a_child_can_ask_for_a_text_chat(self):
        body = self.client.post(self.url, {"text_only": True}, format="json").json()
        self.assertEqual(body["voice_mode"], "text")
        self.assertIsNone(body["notice"])
        state = demo_guards.load_session_state(body["session_id"])
        self.assertEqual((state["mode"], state["reason"]), ("text", "child_choice"))

    def test_text_only_does_not_get_around_the_kill_switch_or_the_daily_cap(self):
        self.redis.set("VOICE_MODE", "off")
        response = self.client.post(self.url, {"text_only": True}, format="json")
        self.assertEqual(response.status_code, 503)
        self.redis.set("VOICE_MODE", "eleven")
        for _ in range(3):
            self.assertEqual(
                self.client.post(self.url, {"text_only": True}, format="json").status_code, 201)
        response = self.client.post(self.url, {"text_only": True}, format="json")
        self.assertEqual(response.status_code, 429)

    def test_text_only_never_turns_a_voice_on(self):
        self.redis.set("VOICE_MODE", "text")
        body = self.client.post(self.url, {"text_only": False}, format="json").json()
        self.assertEqual(body["voice_mode"], "text")
        self.assertEqual(body["notice"]["code"], "voice_resting")

    def test_budget_used_up_starts_a_text_session_not_xai(self):
        self.redis.set(f"demo:eleven_chars:{demo_guards.today()}", 20000)
        body = self.client.post(self.url).json()
        self.assertEqual(body["voice_mode"], "text")
        self.assertEqual(demo_guards.load_session_state(body["session_id"])["mode"], "text")

    @mock.patch.dict(os.environ, {"DEMO_DAILY_SESSIONS": "100"})
    def test_seventh_start_in_an_hour_is_throttled(self):
        codes = [self.client.post(self.url).status_code for _ in range(7)]
        self.assertEqual(codes, [201] * 6 + [429])
        response = self.client.post(self.url)
        body = response.json()
        self.assertEqual(body["code"], "rate_limited")
        self.assertTrue(body["message"]["ar"] and body["message"]["en"])
        self.assertTrue(response.headers.get("Retry-After"))

    @mock.patch.dict(os.environ, {"DEMO_DAILY_SESSIONS": "100", "DEMO_SESSION_START_PER_HOUR": "2"})
    def test_the_hourly_limit_is_configurable(self):
        codes = [self.client.post(self.url).status_code for _ in range(3)]
        self.assertEqual(codes, [201, 201, 429])

    @mock.patch.dict(os.environ, {"DEBUG": "1"})
    def test_guards_off_in_debug(self):
        for _ in range(8):
            response = self.client.post(self.url)
            self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertIsNone(body["max_seconds"])
        self.assertIsNone(body["session_ends_at"])

    @mock.patch.dict(os.environ, {"DEBUG": "1", "DEMO_GUARDS": "1"})
    def test_demo_guards_1_forces_them_on_in_debug(self):
        for _ in range(3):
            self.client.post(self.url)
        self.assertEqual(self.client.post(self.url).status_code, 429)

    def test_a_failed_start_gives_the_daily_slot_back(self):
        with mock.patch("conversation.views.start_session", side_effect=RuntimeError("boom")):
            client = APIClient(raise_request_exception=False)
            client.force_authenticate(self.user)
            self.assertEqual(client.post(self.url).status_code, 500)
        self.assertEqual(self.redis.get(f"demo:sessions:{self.child.id}:{demo_guards.today()}"), "0")

    def test_the_throttle_fails_open_when_its_cache_is_broken(self):
        broken = mock.Mock()
        broken.get.side_effect = ConnectionError("cache down")
        broken.set.side_effect = ConnectionError("cache down")
        with mock.patch.object(SessionStartThrottle, "cache", new_callable=mock.PropertyMock,
                               return_value=broken):
            with self.assertLogs("conversation.throttles", level="ERROR"):
                self.assertEqual(self.client.post(self.url).status_code, 201)


# ---------------------------------------------------------------------------
# Agent half
# ---------------------------------------------------------------------------


def run(coro):
    return asyncio.run(coro)


class _FakeSpeech:
    """A livekit SpeechHandle stand-in: playing until wait_for_playout() has run."""

    def __init__(self, test, name, finishes=True):
        self.test, self.name, self.finishes, self._done = test, name, finishes, False

    def done(self):
        return self._done

    async def wait_for_playout(self):
        if not self.finishes:
            await asyncio.sleep(3600)
        await asyncio.sleep(0)
        self._done = True
        self.test.events.append(("played", self.name))


class SessionClockTests(unittest.TestCase):
    def make(self, language="en", say_result=None, publish_error=None, remaining=100,
             lead=20, grace=10):
        self.events = []
        self.sleeps = []

        async def sleep(seconds):
            self.sleeps.append(seconds)

        async def publish(payload):
            self.events.append(("publish", payload))
            if publish_error:
                raise publish_error

        async def close_room():
            self.events.append(("close", None))

        def say(text):
            self.events.append(("say", text))
            return say_result

        return dict(remaining_seconds=remaining, lead_seconds=lead, grace_seconds=grace,
                    language=lambda: language, say=say, publish=publish,
                    close_room=close_room, sleep=sleep)

    def test_waits_then_says_goodbye_in_the_session_language_then_closes(self):
        class Handle:
            async def wait_for_playout(self):
                return None

        for language in ("en", "ar"):
            kwargs = self.make(language, say_result=Handle())
            run(demo_limits.run_session_clock(**kwargs))
            self.assertEqual(self.sleeps, [80])
            kinds = [e[0] for e in self.events]
            self.assertEqual(kinds, ["publish", "say", "publish", "close"])
            self.assertEqual(self.events[0][1], {"type": "session_ending", "seconds_left": 20})
            self.assertEqual(self.events[1][1], demo_guards.goodbye_for(language))
            self.assertEqual(self.events[2][1], {"type": "session_ended"})

    def test_a_goodbye_that_never_finishes_does_not_keep_the_room_open(self):
        class Stuck:
            async def wait_for_playout(self):
                await asyncio.sleep(3600)

        kwargs = self.make(say_result=Stuck(), lead=0.01, grace=0.01)
        kwargs["goodbye_seconds"] = 0.05
        with self.assertLogs(demo_limits.logger, level="ERROR"):
            run(demo_limits.run_session_clock(**kwargs))
        self.assertEqual(self.events[-1][0], "close")

    def test_the_goodbye_has_its_own_short_budget(self):
        class Stuck:
            async def wait_for_playout(self):
                await asyncio.sleep(3600)

        # A long lead and grace must not stretch the goodbye's own wait.
        kwargs = self.make(say_result=Stuck(), remaining=100, lead=100, grace=100)
        kwargs["goodbye_seconds"] = 0.05
        with self.assertLogs(demo_limits.logger, level="ERROR"):
            run(asyncio.wait_for(demo_limits.run_session_clock(**kwargs), timeout=5))
        self.assertEqual(self.events[-1][0], "close")

    def test_a_reply_in_progress_finishes_before_the_goodbye(self):
        reply = _FakeSpeech(self, "reply")
        kwargs = self.make()
        kwargs["current_speech"] = lambda: None if reply.done() else reply
        kwargs["cut_speech"] = lambda: self.events.append(("cut", None))
        run(demo_limits.run_session_clock(**kwargs))
        self.assertEqual([e[0] for e in self.events],
                         ["publish", "played", "say", "publish", "close"])

    def test_a_reply_that_runs_far_too_long_is_cut_so_the_goodbye_is_heard(self):
        reply = _FakeSpeech(self, "reply", finishes=False)
        kwargs = self.make(lead=0.01, grace=0.01)  # waits max(1, lead + grace) = 1 s
        kwargs["current_speech"] = lambda: reply
        kwargs["cut_speech"] = lambda: self.events.append(("cut", None))
        with self.assertLogs(demo_limits.logger, level="WARNING"):
            run(demo_limits.run_session_clock(**kwargs))
        self.assertEqual([e[0] for e in self.events], ["publish", "cut", "say", "publish", "close"])

    def test_a_failing_say_still_closes(self):
        kwargs = self.make()

        def bad_say(text):
            raise RuntimeError("no tts")

        kwargs["say"] = bad_say
        with self.assertLogs(demo_limits.logger, level="ERROR"):
            run(demo_limits.run_session_clock(**kwargs))
        self.assertEqual(self.events[-1][0], "close")

    def test_a_failing_publish_does_not_stop_the_goodbye(self):
        kwargs = self.make(publish_error=RuntimeError("data channel closed"))
        with self.assertLogs(demo_limits.logger, level="ERROR"):
            run(demo_limits.run_session_clock(**kwargs))
        self.assertIn("say", [e[0] for e in self.events])
        self.assertEqual(self.events[-1][0], "close")

    def test_little_time_left_means_no_waiting(self):
        kwargs = self.make(remaining=5)
        run(demo_limits.run_session_clock(**kwargs))
        self.assertEqual(self.sleeps, [0.0])
        self.assertEqual(self.events[0][1]["seconds_left"], 5)

    def test_cancelling_the_clock_never_closes_the_room(self):
        async def main():
            kwargs = self.make(remaining=1000)

            async def long_sleep(seconds):
                await asyncio.sleep(3600)

            kwargs["sleep"] = long_sleep
            task = asyncio.ensure_future(demo_limits.run_session_clock(**kwargs))
            await asyncio.sleep(0)
            task.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await task

        run(main())
        self.assertEqual(self.events, [])

    def test_turns_stop_right_before_the_goodbye(self):
        class Handle:
            async def wait_for_playout(self):
                return None

        kwargs = self.make(say_result=Handle())
        kwargs["before_goodbye"] = lambda: self.events.append(("stop", None))
        run(demo_limits.run_session_clock(**kwargs))
        self.assertEqual([e[0] for e in self.events], ["publish", "stop", "say", "publish", "close"])

    def test_a_failing_stop_still_says_goodbye_and_closes(self):
        kwargs = self.make()

        def bad_stop():
            raise RuntimeError("session not running")

        kwargs["before_goodbye"] = bad_stop
        with self.assertLogs(demo_limits.logger, level="ERROR"):
            run(demo_limits.run_session_clock(**kwargs))
        self.assertEqual([e[0] for e in self.events], ["publish", "say", "publish", "close"])

    def test_goodbye_has_no_scripture_marks(self):
        for text in demo_guards.GOODBYE.values():
            for mark in ("﴿", "﴾", "ﷺ"):
                self.assertNotIn(mark, text)


class UsageCountingTransformTests(unittest.TestCase):
    def test_counts_characters_and_passes_text_through(self):
        added = []

        async def inner(text):
            async for chunk in text:
                yield chunk.upper()

        async def source():
            for chunk in ("hello ", "", "world"):
                yield chunk

        async def main():
            transform = demo_limits.UsageCountingTransform(inner, add_chars=added.append)
            out = [c async for c in transform(source())]
            await transform.drain()
            return out, transform

        out, transform = run(main())
        self.assertEqual("".join(out), "HELLO WORLD")
        self.assertEqual(added, [11])  # one write at the end of the segment
        self.assertEqual(transform.total, 11)

    def test_counts_in_batches_and_never_on_the_event_loop_thread(self):
        import threading

        calls = []  # (count, thread id)

        async def inner(text):
            async for chunk in text:
                yield chunk

        async def source():
            for _ in range(300):
                yield "ab "

        async def main():
            transform = demo_limits.UsageCountingTransform(
                inner, add_chars=lambda n: calls.append((n, threading.get_ident())))
            out = [c async for c in transform(source())]
            await transform.drain()
            return out, threading.get_ident()

        out, loop_thread = run(main())
        self.assertEqual(len(out), 300)  # every chunk passes through unchanged
        self.assertEqual(sum(n for n, _ in calls), 900)
        self.assertLessEqual(len(calls), 900 // demo_limits.UsageCountingTransform.FLUSH_CHARS + 1)
        self.assertTrue(all(thread != loop_thread for _, thread in calls))

    def test_an_interrupted_reply_still_counts_what_was_sent(self):
        added = []

        async def inner(text):
            async for chunk in text:
                yield chunk

        async def source():
            for chunk in ("abc", "de", "never sent"):
                yield chunk

        async def main():
            transform = demo_limits.UsageCountingTransform(inner, add_chars=added.append)
            stream = transform(source())
            await stream.__anext__()
            await stream.__anext__()
            await stream.aclose()  # what livekit does when the child interrupts
            await transform.drain()

        run(main())
        self.assertEqual(added, [5])

    def test_a_counting_error_never_stops_the_voice(self):
        async def inner(text):
            async for chunk in text:
                yield chunk

        async def source():
            yield "abc"

        def boom(n):
            raise ConnectionError("redis down")

        async def main():
            transform = demo_limits.UsageCountingTransform(inner, add_chars=boom)
            out = [c async for c in transform(source())]
            await transform.drain()
            return out

        with self.assertLogs(demo_limits.logger, level="ERROR"):
            self.assertEqual(run(main()), ["abc"])

    def test_default_counter_writes_to_redis(self):
        fake = FakeRedis()
        with mock.patch.dict(os.environ, {"DEBUG": "0"}), \
                mock.patch.object(demo_guards, "redis_client", lambda: fake):
            async def inner(text):
                async for chunk in text:
                    yield chunk

            async def source():
                yield "twelve"

            async def main():
                transform = demo_limits.UsageCountingTransform(inner)
                out = [c async for c in transform(source())]
                await transform.drain()
                return out

            run(main())
            self.assertEqual(fake.get(f"demo:eleven_chars:{demo_guards.today()}"), "6")


class TokenTtlTests(TestCase):
    def test_start_session_applies_the_ttl(self):
        import jwt

        user = User.objects.create_user(username="ttl_kid", password="x", is_child=True)
        child = ChildProfile.objects.create(
            user=user, nickname="T", gender="male", birth_year=2015)
        _session, token, _created = __import__(
            "conversation.services", fromlist=["start_session"]).start_session(
            child, token_ttl_seconds=420)
        claims = jwt.decode(token, options={"verify_signature": False})
        self.assertEqual(claims["exp"] - claims["nbf"], 420)
        self.assertGreater(timedelta(seconds=claims["exp"] - claims["nbf"]), timedelta(0))
