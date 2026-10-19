"""Tests for REASONING_EFFORT: the setting, the one-time check against the API, and the wiring.

No network and no key: the check is replaced by a fake that says what a model accepts. Run from
backend/:

    python manage.py test conversation.agent.test_reasoning_effort \
        --settings=config.settings_sqlite_test
"""
from __future__ import annotations

import os
import unittest
from unittest import mock

from conversation.agent import reasoning_effort as re_mod
from conversation.agent.reasoning_effort import (
    ACCEPTED, REJECTED, UNKNOWN, llm_effort_kwargs, requested_reasoning_effort,
    resolve_reasoning_effort,
)
from conversation.agent.test_model_defaults import _reload
from conversation.agent.test_voice_wiring import _WiringBase


def fake_probe(accepts, calls=None):
    """A probe that accepts the listed values; anything else is rejected."""
    async def probe(model, effort):
        if calls is not None:
            calls.append((model, effort))
        verdict = accepts.get(effort, REJECTED) if isinstance(accepts, dict) else (
            ACCEPTED if effort in accepts else REJECTED)
        return verdict
    return probe


class _EnvCase(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        patcher = mock.patch.dict(os.environ, {}, clear=False)
        patcher.start()
        self.addCleanup(patcher.stop)
        os.environ.pop("REASONING_EFFORT", None)
        re_mod._reset_cache_for_tests()
        self.addCleanup(re_mod._reset_cache_for_tests)


class SettingTests(_EnvCase):
    def test_unset_and_auto_mean_the_lowest_the_model_accepts(self):
        self.assertEqual(requested_reasoning_effort(), "auto")
        for word in ("", "  ", "auto", "AUTO", "lowest"):
            os.environ["REASONING_EFFORT"] = word
            self.assertEqual(requested_reasoning_effort(), "auto")

    def test_explicit_values_and_off(self):
        for value in ("none", "minimal", "low", "medium", "high", "xhigh"):
            os.environ["REASONING_EFFORT"] = value.upper()
            self.assertEqual(requested_reasoning_effort(), value)
        for word in ("off", "default", "0", "false"):
            os.environ["REASONING_EFFORT"] = word
            self.assertEqual(requested_reasoning_effort(), "off")

    def test_garbage_is_logged_and_treated_as_off(self):
        os.environ["REASONING_EFFORT"] = "banana"
        with self.assertLogs("conversation.agent.reasoning_effort", level="WARNING"):
            self.assertEqual(requested_reasoning_effort(), "off")

    def test_kwargs_are_empty_when_there_is_nothing_to_send(self):
        self.assertEqual(llm_effort_kwargs(None), {})
        self.assertEqual(llm_effort_kwargs("low"), {"reasoning_effort": "low"})


class ResolveTests(_EnvCase):
    async def test_auto_picks_none_on_the_newer_models(self):
        # gpt-5.4-mini, gpt-5.6-luna, gpt-6-luna: none and low yes, minimal no.
        calls = []
        got = await resolve_reasoning_effort("m", probe=fake_probe({"none", "low"}, calls))
        self.assertEqual(got, "none")
        self.assertEqual(calls, [("m", "none")])

    async def test_auto_walks_to_minimal_on_an_older_gpt5_model(self):
        got = await resolve_reasoning_effort("m", probe=fake_probe({"minimal", "low"}))
        self.assertEqual(got, "minimal")

    async def test_auto_walks_to_low_when_only_low_is_accepted(self):
        got = await resolve_reasoning_effort("m", probe=fake_probe({"low"}))
        self.assertEqual(got, "low")

    async def test_auto_drops_the_parameter_when_nothing_is_accepted(self):
        with self.assertLogs("conversation.agent.reasoning_effort", level="WARNING") as logs:
            got = await resolve_reasoning_effort("m", probe=fake_probe(set()))
        self.assertIsNone(got)
        self.assertIn("dropped", logs.output[0])

    async def test_an_explicit_value_the_model_rejects_is_logged_and_dropped(self):
        # The case of the lead's rule: never crash, log it and drop the parameter.
        os.environ["REASONING_EFFORT"] = "minimal"
        calls = []
        with self.assertLogs("conversation.agent.reasoning_effort", level="WARNING") as logs:
            got = await resolve_reasoning_effort("m", probe=fake_probe({"none"}, calls))
        self.assertIsNone(got)
        self.assertEqual(calls, [("m", "minimal")])  # it did not try other values
        self.assertIn("minimal", logs.output[0])

    async def test_the_tested_models_are_never_probed(self):
        # Each session runs in a fresh process and a probe took 1 to 3 s: known models skip it.
        calls = []
        for model in ("gpt-5.4-mini", "gpt-5.4-nano", "gpt-5.2", "gpt-5.6-luna", "gpt-6-luna"):
            with self.subTest(model=model):
                re_mod._reset_cache_for_tests()
                got = await resolve_reasoning_effort(model, probe=fake_probe(set(), calls))
                self.assertEqual(got, "none")
        self.assertEqual(calls, [])

    async def test_minimal_on_a_tested_model_is_dropped_without_a_request(self):
        os.environ["REASONING_EFFORT"] = "minimal"
        calls = []
        with self.assertLogs("conversation.agent.reasoning_effort", level="WARNING") as logs:
            got = await resolve_reasoning_effort("gpt-6-luna", probe=fake_probe({"minimal"}, calls))
        self.assertIsNone(got)
        self.assertEqual(calls, [])
        self.assertIn("minimal", logs.output[0])

    async def test_a_value_the_table_does_not_know_is_still_probed(self):
        os.environ["REASONING_EFFORT"] = "high"
        calls = []
        got = await resolve_reasoning_effort("gpt-6-luna", probe=fake_probe({"high"}, calls))
        self.assertEqual(got, "high")
        self.assertEqual(calls, [("gpt-6-luna", "high")])

    async def test_an_explicit_value_the_model_accepts_is_used(self):
        os.environ["REASONING_EFFORT"] = "low"
        self.assertEqual(await resolve_reasoning_effort("m", probe=fake_probe({"low"})), "low")

    async def test_off_sends_nothing_and_never_calls_the_api(self):
        os.environ["REASONING_EFFORT"] = "off"
        calls = []
        self.assertIsNone(await resolve_reasoning_effort("m", probe=fake_probe({"none"}, calls)))
        self.assertEqual(calls, [])

    async def test_an_unknown_answer_drops_it_for_now_and_is_not_remembered(self):
        calls = []
        with self.assertLogs("conversation.agent.reasoning_effort", level="WARNING"):
            first = await resolve_reasoning_effort("m", probe=fake_probe({"none": UNKNOWN}, calls))
        self.assertIsNone(first)
        # The network is back: the next session tries again and gets the value.
        second = await resolve_reasoning_effort("m", probe=fake_probe({"none"}, calls))
        self.assertEqual(second, "none")

    async def test_a_probe_that_raises_never_breaks_the_caller(self):
        async def boom(model, effort):
            raise RuntimeError("network down")
        with self.assertLogs("conversation.agent.reasoning_effort", level="WARNING"):
            self.assertIsNone(await resolve_reasoning_effort("m", probe=boom))

    async def test_a_certain_answer_is_remembered_for_the_process(self):
        calls = []
        probe = fake_probe({"none"}, calls)
        await resolve_reasoning_effort("m", probe=probe)
        await resolve_reasoning_effort("m", probe=probe)
        self.assertEqual(len(calls), 1)
        # Another model is a different question.
        await resolve_reasoning_effort("other", probe=probe)
        self.assertEqual(len(calls), 2)


class ProbeTests(_EnvCase):
    """The real probe against a fake OpenAI SDK: how it reads a 400 from the API."""

    async def _run_probe(self, *, error=None):
        import sys
        from types import ModuleType, SimpleNamespace

        class APIStatusError(Exception):
            def __init__(self, status_code, body, message=""):
                super().__init__(message)
                self.status_code, self.body, self.message = status_code, body, message

        async def create(**kwargs):
            create.kwargs = kwargs
            if error is not None:
                raise error(APIStatusError)
            return SimpleNamespace()

        client = SimpleNamespace(
            chat=SimpleNamespace(completions=SimpleNamespace(create=create)),
            close=mock.AsyncMock(),
        )
        sdk = ModuleType("openai")
        sdk.AsyncOpenAI = lambda **kw: client
        sdk.APIStatusError = APIStatusError
        with mock.patch.dict(sys.modules, {"openai": sdk}):
            verdict = await re_mod.probe_reasoning_effort("m", "minimal")
        return verdict, create

    async def test_a_200_is_accepted_and_sends_a_tiny_request(self):
        verdict, create = await self._run_probe()
        self.assertEqual(verdict, ACCEPTED)
        self.assertEqual(create.kwargs["reasoning_effort"], "minimal")
        self.assertLessEqual(create.kwargs["max_completion_tokens"], 16)

    async def test_a_400_about_reasoning_effort_is_a_rejection(self):
        verdict, _ = await self._run_probe(error=lambda E: E(400, {"param": "reasoning_effort"}))
        self.assertEqual(verdict, REJECTED)

    async def test_a_400_for_another_reason_or_a_401_or_a_404_is_unknown(self):
        for code, body in ((400, {"param": "model"}), (401, {}), (404, {}), (429, None)):
            verdict, _ = await self._run_probe(error=lambda E, c=code, b=body: E(c, b))
            self.assertEqual(verdict, UNKNOWN, code)


class EntrypointWiringTests(_WiringBase):
    async def test_a_resolved_effort_reaches_the_llm_and_the_latency_label(self):
        self.effort_result = "none"
        await self.run_entrypoint()
        self.assertEqual(self.session.kwargs["llm"].reasoning_effort, "none")
        self.resolve_effort.assert_awaited_once_with("gpt-5.4-mini")

    async def test_no_effort_means_the_parameter_is_not_passed_at_all(self):
        self.effort_result = None
        await self.run_entrypoint()
        self.assertFalse(hasattr(self.session.kwargs["llm"], "reasoning_effort"))

    async def test_a_failing_check_never_stops_the_session(self):
        self.effort_result = RuntimeError("the check blew up")
        with self.assertLogs("conversation.agent.entrypoint", level="ERROR"):
            await self.run_entrypoint()
        self.assertIsNotNone(self.session)
        self.assertFalse(hasattr(self.session.kwargs["llm"], "reasoning_effort"))
