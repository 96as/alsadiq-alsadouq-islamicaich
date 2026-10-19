"""Tests for the soft thinking sounds (filler.py), the committed clips and the wiring.

No audio is played: the player is a fake. No Quran text appears here.

Run from backend/:  python manage.py test conversation.agent.test_filler \
    --settings=config.settings_sqlite_test
"""
from __future__ import annotations

import asyncio
import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from conversation.agent import filler
from conversation.agent.filler import FillerController, FillerSettings
from conversation.agent.test_voice_wiring import _WiringBase


def _user(new):
    return SimpleNamespace(new_state=new, old_state=None)


def _agent(old, new):
    return SimpleNamespace(old_state=old, new_state=new)


class _Handle:
    def __init__(self, clip):
        self.clip = clip
        self.stopped = False

    def stop(self):
        self.stopped = True


class _Rng:
    """random() returns the given value; choice() takes the first option."""

    def __init__(self, value=0.0):
        self.value = value

    def random(self):
        return self.value

    def choice(self, options):
        return options[0]


class _Clock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


def _controller(*, probability=1.0, delay_s=0.0, clips=("a.ogg", "b.ogg"), rng=None, clock=None):
    played = []

    def play(path):
        handle = _Handle(path)
        played.append(handle)
        return handle

    controller = FillerController(
        play, list(clips), probability=probability, delay_s=delay_s,
        rng=rng or _Rng(0.0), clock=clock or _Clock(),
    )
    return controller, played


def _child_speaks_then_agent_thinks(controller):
    controller.on_user_state_changed(_user("speaking"))
    controller.on_user_state_changed(_user("listening"))
    controller.on_agent_state_changed(_agent("listening", "thinking"))


class SettingsTests(unittest.TestCase):
    def _load(self, **env):
        base = {k: v for k, v in os.environ.items() if not k.startswith("FILLER_")}
        base.update(env)
        with mock.patch.dict(os.environ, base, clear=True):
            return filler.load_filler_settings()

    def test_defaults_are_hum_at_half_probability(self):
        s = self._load()
        self.assertEqual(s.mode, "hum")
        self.assertEqual(s.probability, 0.5)
        self.assertGreater(s.delay_s, 0)
        self.assertLessEqual(s.volume, 1.0)

    def test_off(self):
        self.assertEqual(self._load(FILLER_MODE="off").mode, "off")

    def test_mode_is_case_and_space_insensitive(self):
        self.assertEqual(self._load(FILLER_MODE=" HUM ").mode, "hum")

    def test_spoken_is_not_built_and_behaves_as_off(self):
        with self.assertLogs(filler.logger, level="WARNING") as logs:
            self.assertEqual(self._load(FILLER_MODE="spoken").mode, "off")
        self.assertIn("content team", "\n".join(logs.output))

    def test_unknown_mode_is_off(self):
        with self.assertLogs(filler.logger, level="WARNING"):
            self.assertEqual(self._load(FILLER_MODE="loud").mode, "off")

    def test_probability_is_clamped_and_bad_values_fall_back(self):
        self.assertEqual(self._load(FILLER_PROBABILITY="2").probability, 1.0)
        self.assertEqual(self._load(FILLER_PROBABILITY="-1").probability, 0.0)
        self.assertEqual(self._load(FILLER_PROBABILITY="0.25").probability, 0.25)
        with self.assertLogs(filler.logger, level="WARNING"):
            self.assertEqual(self._load(FILLER_PROBABILITY="often").probability, 0.5)
        self.assertEqual(self._load(FILLER_PROBABILITY="nan").probability, 0.5)


class ControllerTests(unittest.TestCase):
    def test_a_spoken_turn_plays_a_hum(self):
        controller, played = _controller()
        _child_speaks_then_agent_thinks(controller)
        self.assertEqual(len(played), 1)

    def test_the_greeting_never_gets_a_hum(self):
        controller, played = _controller()
        # Nobody has spoken: the agent starts thinking to say hello.
        controller.on_agent_state_changed(_agent("initializing", "thinking"))
        controller.on_agent_state_changed(_agent("idle", "thinking"))
        controller.on_agent_state_changed(_agent("listening", "thinking"))
        self.assertEqual(played, [])

    def test_a_typed_message_gets_no_hum(self):
        controller, played = _controller()
        _child_speaks_then_agent_thinks(controller)
        controller.on_agent_state_changed(_agent("thinking", "speaking"))
        controller.on_agent_state_changed(_agent("speaking", "listening"))
        self.assertEqual(len(played), 1)
        # Next turn is typed: no user speech, so no hum.
        controller.on_agent_state_changed(_agent("listening", "thinking"))
        self.assertEqual(len(played), 1)

    def test_the_pause_while_a_tool_runs_gets_no_hum(self):
        controller, played = _controller()
        _child_speaks_then_agent_thinks(controller)
        controller.on_agent_state_changed(_agent("thinking", "speaking"))
        controller.on_agent_state_changed(_agent("speaking", "thinking"))
        self.assertEqual(len(played), 1)

    def test_the_hum_stops_when_the_reply_starts(self):
        controller, played = _controller()
        _child_speaks_then_agent_thinks(controller)
        self.assertFalse(played[0].stopped)
        controller.on_agent_state_changed(_agent("thinking", "speaking"))
        self.assertTrue(played[0].stopped)

    def test_the_hum_stops_when_the_child_speaks_again(self):
        controller, played = _controller()
        _child_speaks_then_agent_thinks(controller)
        controller.on_user_state_changed(_user("speaking"))
        self.assertTrue(played[0].stopped)

    def test_the_hum_stops_when_the_agent_goes_back_to_listening(self):
        controller, played = _controller()
        _child_speaks_then_agent_thinks(controller)
        controller.on_agent_state_changed(_agent("thinking", "listening"))
        self.assertTrue(played[0].stopped)

    def test_probability_zero_and_the_roll(self):
        controller, played = _controller(probability=0.0)
        _child_speaks_then_agent_thinks(controller)
        self.assertEqual(played, [])
        controller, played = _controller(probability=0.5, rng=_Rng(0.9))  # roll above: no hum
        _child_speaks_then_agent_thinks(controller)
        self.assertEqual(played, [])
        controller, played = _controller(probability=0.5, rng=_Rng(0.1))  # roll below: hum
        _child_speaks_then_agent_thinks(controller)
        self.assertEqual(len(played), 1)

    def test_no_clips_no_hum(self):
        controller, played = _controller(clips=())
        _child_speaks_then_agent_thinks(controller)
        self.assertEqual(played, [])

    def test_the_same_clip_never_plays_twice_in_a_row(self):
        import random

        played = []
        controller = FillerController(
            lambda p: played.append(p) or _Handle(p), ["a", "b", "c"], probability=1.0,
            delay_s=0.0, rng=random.Random(7),
        )
        for _ in range(30):
            _child_speaks_then_agent_thinks(controller)
            controller.on_agent_state_changed(_agent("thinking", "speaking"))
            controller.on_agent_state_changed(_agent("speaking", "listening"))
        self.assertEqual(len(played), 30)
        for first, second in zip(played, played[1:]):
            self.assertNotEqual(first, second)

    def test_a_stale_spoken_flag_does_not_count(self):
        clock = _Clock()
        controller, played = _controller(clock=clock)
        controller.on_user_state_changed(_user("speaking"))
        controller.on_user_state_changed(_user("listening"))
        clock.now += filler.VOICE_TURN_WINDOW_S + 1  # long ago, then a typed turn
        controller.on_agent_state_changed(_agent("listening", "thinking"))
        self.assertEqual(played, [])

    def test_broken_events_and_a_failing_player_never_raise(self):
        controller, _ = _controller()
        controller.on_user_state_changed(None)
        controller.on_agent_state_changed(None)

        def boom(_path):
            raise RuntimeError("no audio device")

        controller = FillerController(boom, ["a"], probability=1.0, delay_s=0.0, rng=_Rng(0.0))
        _child_speaks_then_agent_thinks(controller)
        controller.on_agent_state_changed(_agent("thinking", "speaking"))

    def test_attach_registers_the_two_state_events(self):
        events = []
        controller, _ = _controller()
        controller.attach(SimpleNamespace(on=lambda name, cb=None, **kw: events.append(name)))
        self.assertEqual(sorted(events), ["agent_state_changed", "user_state_changed"])


class ControllerDelayTests(unittest.IsolatedAsyncioTestCase):
    async def test_a_fast_reply_never_gets_a_hum(self):
        controller, played = _controller(delay_s=0.05)
        _child_speaks_then_agent_thinks(controller)
        controller.on_agent_state_changed(_agent("thinking", "speaking"))  # reply is ready
        await asyncio.sleep(0.12)
        self.assertEqual(played, [])

    async def test_a_slow_reply_gets_the_hum_after_the_delay(self):
        controller, played = _controller(delay_s=0.03)
        _child_speaks_then_agent_thinks(controller)
        self.assertEqual(played, [])
        await asyncio.sleep(0.1)
        self.assertEqual(len(played), 1)
        controller.on_agent_state_changed(_agent("thinking", "speaking"))
        self.assertTrue(played[0].stopped)

    async def test_the_child_speaking_during_the_delay_cancels_it(self):
        controller, played = _controller(delay_s=0.05)
        _child_speaks_then_agent_thinks(controller)
        controller.on_user_state_changed(_user("speaking"))
        await asyncio.sleep(0.12)
        self.assertEqual(played, [])


class _FakePlayer:
    instances: list = []

    def __init__(self, **kwargs):
        self.started_with = None
        self.closed = False
        self.plays = []
        _FakePlayer.instances.append(self)

    async def start(self, *, room, agent_session=None):
        self.started_with = room

    def play(self, audio, *, loop=False):
        self.plays.append(audio)
        return _Handle(audio)

    async def aclose(self):
        self.closed = True


def _fake_livekit_agents(player_cls=_FakePlayer):
    def audio_config(source, volume=1.0, probability=1.0):
        return SimpleNamespace(source=source, volume=volume, probability=probability)

    agents = SimpleNamespace(BackgroundAudioPlayer=player_cls, AudioConfig=audio_config)
    return {"livekit": SimpleNamespace(), "livekit.agents": agents}


class _Session:
    def __init__(self):
        self.handlers = {}

    def on(self, name, cb=None, **kw):
        self.handlers.setdefault(name, []).append(cb)


HUM = FillerSettings(mode="hum", probability=1.0, delay_s=0.0, volume=0.5)


class StartFillerTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        _FakePlayer.instances.clear()

    async def _start(self, **kwargs):
        kwargs.setdefault("is_elevenlabs", True)
        kwargs.setdefault("text_only", False)
        kwargs.setdefault("settings", HUM)
        with mock.patch.dict(sys.modules, _fake_livekit_agents()):
            return await filler.start_filler(_Session(), object(), **kwargs)

    async def test_text_only_and_xai_get_nothing(self):
        self.assertIsNone(await self._start(text_only=True))
        self.assertIsNone(await self._start(is_elevenlabs=False))
        self.assertEqual(_FakePlayer.instances, [])

    async def test_off_and_zero_probability_get_nothing(self):
        self.assertIsNone(await self._start(settings=HUM._replace(mode="off")))
        self.assertIsNone(await self._start(settings=HUM._replace(probability=0.0)))
        self.assertEqual(_FakePlayer.instances, [])

    async def test_no_clips_gets_nothing(self):
        import tempfile

        with tempfile.TemporaryDirectory() as empty:
            with self.assertLogs(filler.logger, level="WARNING"):
                self.assertIsNone(await self._start(clips_dir=empty))

    async def test_starts_the_player_hooks_the_session_and_closes_cleanly(self):
        session = _Session()
        room = object()
        with mock.patch.dict(sys.modules, _fake_livekit_agents()):
            close = await filler.start_filler(
                session, room, is_elevenlabs=True, text_only=False, settings=HUM)
        self.assertIsNotNone(close)
        player = _FakePlayer.instances[0]
        self.assertIs(player.started_with, room)
        self.assertIn("agent_state_changed", session.handlers)
        self.assertIn("user_state_changed", session.handlers)
        # A spoken turn plays one of the committed clips at the configured volume.
        for handler in session.handlers["user_state_changed"]:
            handler(_user("speaking"))
        for handler in session.handlers["agent_state_changed"]:
            handler(_agent("listening", "thinking"))
        self.assertEqual(len(player.plays), 1)
        self.assertEqual(player.plays[0].volume, 0.5)
        self.assertTrue(player.plays[0].source.endswith(".ogg"))
        await close()
        self.assertTrue(player.closed)

    async def test_a_player_that_cannot_start_never_breaks_the_session(self):
        class Broken(_FakePlayer):
            async def start(self, *, room, agent_session=None):
                raise RuntimeError("cannot publish")

        with mock.patch.dict(sys.modules, _fake_livekit_agents(Broken)):
            with self.assertLogs(filler.logger, level="WARNING") as logs:
                result = await filler.start_filler(
                    _Session(), object(), is_elevenlabs=True, text_only=False, settings=HUM)
        self.assertIsNone(result)
        self.assertIn("RuntimeError", "\n".join(logs.output))
        self.assertNotIn("cannot publish", "\n".join(logs.output))

    async def test_a_livekit_without_a_background_player_never_breaks_the_session(self):
        with mock.patch.dict(sys.modules, {"livekit": SimpleNamespace(),
                                           "livekit.agents": SimpleNamespace()}):
            with self.assertLogs(filler.logger, level="WARNING"):
                result = await filler.start_filler(
                    _Session(), object(), is_elevenlabs=True, text_only=False, settings=HUM)
        self.assertIsNone(result)

    async def test_background_start_closes_the_player_when_the_session_closes(self):
        session = _Session()
        with mock.patch.dict(sys.modules, _fake_livekit_agents()):
            task = filler.start_filler_in_background(
                session, object(), is_elevenlabs=True, text_only=False, settings=HUM)
            await task
        self.assertIn("close", session.handlers)
        player = _FakePlayer.instances[0]
        self.assertFalse(player.closed)
        session.handlers["close"][0](SimpleNamespace())
        await asyncio.sleep(0)
        await asyncio.sleep(0)
        self.assertTrue(player.closed)


class _QueuedSource:
    """Stands in for the rtc.AudioSource inside livekit's player: counts queue drops."""

    def __init__(self):
        self.drops = 0

    def clear_queue(self):
        self.drops += 1


class _PlayerWithQueue(_FakePlayer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._audio_source = _QueuedSource()


class HardStopTests(unittest.IsolatedAsyncioTestCase):
    """livekit keeps about 400 ms of the hum queued: a stop must drop that queue too."""

    def setUp(self):
        _FakePlayer.instances.clear()

    async def _started(self, player_cls=_PlayerWithQueue):
        session = _Session()
        with mock.patch.dict(sys.modules, _fake_livekit_agents(player_cls)):
            close = await filler.start_filler(
                session, object(), is_elevenlabs=True, text_only=False, settings=HUM)
        return session, _FakePlayer.instances[0], close

    @staticmethod
    def _fire(session, name, event):
        for handler in session.handlers[name]:
            handler(event)

    async def test_the_reply_starting_drops_the_queued_hum_at_once_and_again_shortly(self):
        session, player, _close = await self._started()
        self._fire(session, "user_state_changed", _user("speaking"))
        self._fire(session, "user_state_changed", _user("listening"))
        self._fire(session, "agent_state_changed", _agent("listening", "thinking"))
        self.assertEqual(len(player.plays), 1)
        self.assertEqual(player._audio_source.drops, 0)
        self._fire(session, "agent_state_changed", _agent("thinking", "speaking"))
        self.assertEqual(player._audio_source.drops, 1)  # at once, not 400 ms later
        await asyncio.sleep(max(filler.DROP_QUEUE_AGAIN_AFTER_S) + 0.05)
        self.assertEqual(player._audio_source.drops, 1 + len(filler.DROP_QUEUE_AGAIN_AFTER_S))

    async def test_the_child_speaking_again_drops_the_queued_hum(self):
        session, player, _close = await self._started()
        self._fire(session, "user_state_changed", _user("speaking"))
        self._fire(session, "user_state_changed", _user("listening"))
        self._fire(session, "agent_state_changed", _agent("listening", "thinking"))
        self._fire(session, "user_state_changed", _user("speaking"))
        self.assertEqual(player._audio_source.drops, 1)

    async def test_a_late_drop_never_cuts_a_newer_hum(self):
        session, player, _close = await self._started()
        hums = filler._HumPlayer(player, lambda path, volume: path, 0.5)
        first = hums.play("a.ogg")
        first.stop()
        hums.play("b.ogg")  # a new hum before the late drops
        await asyncio.sleep(max(filler.DROP_QUEUE_AGAIN_AFTER_S) + 0.05)
        self.assertEqual(player._audio_source.drops, 1)

    async def test_a_player_without_a_queue_still_stops(self):
        class Recording(_FakePlayer):
            def play(self, audio, *, loop=False):
                self.handle = super().play(audio, loop=loop)
                return self.handle

        session, player, _close = await self._started(Recording)
        self._fire(session, "user_state_changed", _user("speaking"))
        self._fire(session, "user_state_changed", _user("listening"))
        self._fire(session, "agent_state_changed", _agent("listening", "thinking"))
        self._fire(session, "agent_state_changed", _agent("thinking", "speaking"))
        self.assertTrue(player.handle.stopped)
        await asyncio.sleep(max(filler.DROP_QUEUE_AGAIN_AFTER_S) + 0.05)

    async def test_a_failing_queue_drop_never_raises(self):
        class Broken(_QueuedSource):
            def clear_queue(self):
                raise RuntimeError("source closed")

        session, player, _close = await self._started()
        player._audio_source = Broken()
        hums = filler._HumPlayer(player, lambda path, volume: path, 0.5)
        hums.play("a.ogg").stop()
        await asyncio.sleep(max(filler.DROP_QUEUE_AGAIN_AFTER_S) + 0.05)


class ClipFileTests(unittest.TestCase):
    def test_there_are_six_to_eight_small_clips(self):
        clips = filler.list_clips()
        self.assertTrue(6 <= len(clips) <= 8, clips)
        for clip in clips:
            self.assertLess(os.path.getsize(clip), 20_000, clip)

    def test_every_clip_is_under_eight_tenths_of_a_second(self):
        try:
            import av
        except ImportError:
            self.skipTest("PyAV is not installed")
        for clip in filler.list_clips():
            with self.subTest(clip=Path(clip).name):
                samples = 0
                rate = 48000
                with av.open(clip) as container:
                    for frame in container.decode(audio=0):
                        samples += frame.samples
                        rate = frame.sample_rate
                self.assertGreater(samples / rate, 0.15)
                self.assertLess(samples / rate, 0.8)

    def test_the_readme_names_the_voice_and_how_they_were_made(self):
        text = (filler.CLIPS_DIR / "README.md").read_text(encoding="utf-8")
        self.assertIn("pCKbQ4EPGE06zpEPGNvS", text)
        self.assertIn("eleven_flash_v2_5", text)
        self.assertIn("render_fillers.py", text)

    def test_the_render_script_holds_no_key(self):
        text = (filler.CLIPS_DIR / "render_fillers.py").read_text(encoding="utf-8")
        self.assertNotIn("sk_", text)
        self.assertNotIn("print(key", text)


class FillerWiringTests(_WiringBase):
    async def _run(self, **kwargs):
        spy = mock.MagicMock(return_value=None)
        with mock.patch.object(self.entrypoint, "start_filler_in_background", spy):
            await self.run_entrypoint(**kwargs)
        return spy

    async def test_elevenlabs_session_starts_the_filler_with_the_room(self):
        spy = await self._run()
        spy.assert_called_once()
        self.assertIs(spy.call_args.args[0], self.session)
        self.assertIs(spy.call_args.args[1], self.ctx.room)
        self.assertIs(spy.call_args.kwargs["is_elevenlabs"], True)
        self.assertIs(spy.call_args.kwargs["text_only"], False)

    async def test_xai_session_is_not_elevenlabs(self):
        spy = await self._run(session_state={"mode": "xai", "max_seconds": 0})
        self.assertIs(spy.call_args.kwargs["is_elevenlabs"], False)

    async def test_text_only_session_is_flagged_text_only(self):
        spy = await self._run(session_state={"mode": "text", "max_seconds": 0})
        self.assertIs(spy.call_args.kwargs["text_only"], True)

    async def test_filler_starts_after_the_session_and_before_the_greeting(self):
        order = []

        def spy(*args, **kwargs):
            order.append("started" if self.session_started() else "early")

        self.session_started = lambda: _last_session().start_kwargs is not None
        with mock.patch.object(self.entrypoint, "start_filler_in_background", spy):
            await self.run_entrypoint()
        self.assertEqual(order, ["started"])


def _last_session():
    from conversation.agent.test_voice_wiring import _FakeAgentSession

    return _FakeAgentSession.instances[-1]
