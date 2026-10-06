"""Tests for the ElevenLabs websocket warm-up (tts_warmup.py) and its wiring.

Run from backend/:  python manage.py test conversation.agent.test_tts_warmup \
    --settings=config.settings_sqlite_test
"""
from __future__ import annotations

import asyncio
import os
import unittest
from types import SimpleNamespace
from unittest import mock

from conversation.agent import tts_warmup
from conversation.agent.test_voice_wiring import _FakeAgentSession, _WiringBase


class WarmUpTests(unittest.IsolatedAsyncioTestCase):
    async def test_opens_the_connection(self):
        tts = SimpleNamespace(current_connection=mock.AsyncMock())
        self.assertTrue(await tts_warmup.warm_up_tts(tts))
        tts.current_connection.assert_awaited_once()

    async def test_a_failure_is_swallowed_and_logged_without_the_message(self):
        secret = "sk-this-must-not-be-logged"
        tts = SimpleNamespace(current_connection=mock.AsyncMock(side_effect=RuntimeError(secret)))
        with self.assertLogs(tts_warmup.logger, level="WARNING") as logs:
            self.assertFalse(await tts_warmup.warm_up_tts(tts))
        text = "\n".join(logs.output)
        self.assertIn("RuntimeError", text)
        self.assertNotIn(secret, text)

    async def test_a_slow_connection_times_out_instead_of_hanging(self):
        async def never():
            await asyncio.sleep(3600)

        tts = SimpleNamespace(current_connection=never)
        with mock.patch.object(tts_warmup, "WARMUP_TIMEOUT_SECONDS", 0.01):
            with self.assertLogs(tts_warmup.logger, level="WARNING"):
                self.assertFalse(await tts_warmup.warm_up_tts(tts))

    async def test_a_tts_without_current_connection_is_left_alone(self):
        self.assertFalse(await tts_warmup.warm_up_tts(SimpleNamespace()))

    async def test_cancelling_the_task_is_not_swallowed(self):
        started = asyncio.Event()

        async def slow():
            started.set()
            await asyncio.sleep(3600)

        task = asyncio.create_task(tts_warmup.warm_up_tts(SimpleNamespace(current_connection=slow)))
        await started.wait()
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task


class StartTests(unittest.IsolatedAsyncioTestCase):
    async def test_only_elevenlabs_starts_a_task(self):
        tts = SimpleNamespace(current_connection=mock.AsyncMock())
        task = tts_warmup.start_tts_warmup(tts, is_elevenlabs=True)
        self.assertIsNotNone(task)
        await task
        tts.current_connection.assert_awaited_once()

    async def test_xai_gets_nothing(self):
        tts = SimpleNamespace(current_connection=mock.AsyncMock())
        self.assertIsNone(tts_warmup.start_tts_warmup(tts, is_elevenlabs=False))
        tts.current_connection.assert_not_called()

    async def test_no_tts_gets_nothing(self):
        self.assertIsNone(tts_warmup.start_tts_warmup(None, is_elevenlabs=True))

    async def test_switch_turns_it_off(self):
        tts = SimpleNamespace(current_connection=mock.AsyncMock())
        with mock.patch.dict(os.environ, {"TTS_WARMUP": "0"}):
            self.assertIsNone(tts_warmup.start_tts_warmup(tts, is_elevenlabs=True))
        with mock.patch.dict(os.environ, {"TTS_WARMUP": "1"}):
            task = tts_warmup.start_tts_warmup(tts, is_elevenlabs=True)
            self.assertIsNotNone(task)
            await task


class WarmUpWiringTests(_WiringBase):
    async def _run(self, **kwargs):
        spy = mock.MagicMock(wraps=self.entrypoint.start_tts_warmup)
        with mock.patch.object(self.entrypoint, "start_tts_warmup", spy):
            await self.run_entrypoint(**kwargs)
        return spy

    async def test_elevenlabs_session_warms_the_voice_it_built(self):
        spy = await self._run()
        spy.assert_called_once()
        self.assertIs(spy.call_args.args[0], self.build_tts.return_value)
        self.assertIs(spy.call_args.kwargs["is_elevenlabs"], True)

    async def test_xai_session_is_not_warmed(self):
        spy = await self._run(session_state={"mode": "xai", "max_seconds": 0})
        spy.assert_called_once()
        self.assertIs(spy.call_args.kwargs["is_elevenlabs"], False)

    async def test_text_only_session_has_no_voice_to_warm(self):
        spy = await self._run(session_state={"mode": "text", "max_seconds": 0})
        spy.assert_called_once()
        self.assertIsNone(spy.call_args.args[0])

    async def test_warm_up_starts_before_the_session_does(self):
        order = []
        real_start = self.entrypoint.start_tts_warmup

        def spy(*args, **kwargs):
            # Right after the voice is built: no AgentSession exists yet, so the socket opens
            # while the agent, the reasoning effort and the session start are still going on.
            order.append("warmup" if not _FakeAgentSession.instances else "late")
            return real_start(*args, **kwargs)

        with mock.patch.object(self.entrypoint, "start_tts_warmup", spy):
            await self.run_entrypoint()
        self.assertEqual(order, ["warmup"])
        self.assertIsNotNone(self.session.start_kwargs)
