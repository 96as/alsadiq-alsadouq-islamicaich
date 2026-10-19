"""The fast STT and LLM defaults are the same in the code and in both env example files.

Task 08: production used to run a slower LLM and STT model than dev because the three places
drifted. This test fails when they drift again. Run from backend/:

    python manage.py test conversation.agent.test_model_defaults \
        --settings=config.settings_sqlite_test
"""
from __future__ import annotations

import os
import re
from pathlib import Path

from conversation.agent.test_voice_wiring import _WiringBase

REPO_ROOT = Path(__file__).resolve().parents[3]
ENV_FILES = (".env.example", ".env.production.example")


def _env_value(path: Path, key: str) -> str | None:
    found = None
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.match(rf"^{re.escape(key)}=(.*)$", line.strip())
        if match:
            found = match.group(1).strip()
    return found


class ModelDefaultsTests(_WiringBase):
    def test_env_examples_match_the_code_defaults(self):
        ep = self.entrypoint
        expected = {
            "LLM_MODEL": ep.DEFAULT_LLM_MODEL,
            "STT_MODEL": ep.DEFAULT_STT_MODEL,
            "STT_REALTIME": "1",
        }
        for name in ENV_FILES:
            path = REPO_ROOT / name
            for key, want in expected.items():
                self.assertEqual(_env_value(path, key), want, f"{name}: {key}")

    def test_env_examples_carry_the_reasoning_effort_default(self):
        for name in ENV_FILES:
            self.assertEqual(_env_value(REPO_ROOT / name, "REASONING_EFFORT"), "auto", name)

    def test_no_gpt4_chat_model_is_suggested_for_the_voice_llm(self):
        # The lead's model rule: no gpt-4.x chat LLMs. (gpt-4o-*-transcribe is a speech model.)
        files = [REPO_ROOT / n for n in ENV_FILES]
        files.append(Path(self.entrypoint.__file__))
        pattern = re.compile(r"gpt-4(?!o-(?:mini-)?transcribe)", re.IGNORECASE)
        for path in files:
            found = [ln for ln in path.read_text(encoding="utf-8").splitlines()
                     if pattern.search(ln) and "gpt-4.x" not in ln]
            self.assertEqual(found, [], f"{path.name} suggests a gpt-4 model")

    def test_the_defaults_are_the_fast_models(self):
        self.assertEqual(self.entrypoint.DEFAULT_LLM_MODEL, "gpt-5.4-mini")
        self.assertEqual(self.entrypoint.DEFAULT_STT_MODEL, "gpt-4o-mini-transcribe")

    async def test_session_uses_the_default_llm_and_stt_when_env_is_unset(self):
        for key in ("LLM_MODEL", "STT_MODEL", "STT_REALTIME"):
            os.environ.pop(key, None)
        self.entrypoint = _reload(self)
        await self.run_entrypoint()
        self.assertEqual(self.session.kwargs["llm"].model, "gpt-5.4-mini")
        factory = self.build_stt.call_args.kwargs["openai_factory"]
        stt = factory()
        self.assertEqual(stt.model, "gpt-4o-mini-transcribe")
        self.assertTrue(stt.use_realtime)

    async def test_llm_model_is_switchable_by_env_alone(self):
        os.environ["LLM_MODEL"] = "gpt-6-luna"
        self.entrypoint = _reload(self)
        await self.run_entrypoint()
        self.assertEqual(self.session.kwargs["llm"].model, "gpt-6-luna")
        self.resolve_effort.assert_awaited_once_with("gpt-6-luna")

    async def test_stt_model_is_switchable_by_env_alone(self):
        os.environ["STT_MODEL"] = "gpt-transcribe"
        self.entrypoint = _reload(self)
        await self.run_entrypoint()
        factory = self.build_stt.call_args.kwargs["openai_factory"]
        self.assertEqual(factory().model, "gpt-transcribe")

    async def test_a_live_only_stt_model_falls_back_to_the_default(self):
        # The 1.5.1 plugin cannot run these (no commit is sent): see stt_models.py.
        for bad in ("gpt-live-transcribe", "gpt-realtime-whisper"):
            os.environ["STT_MODEL"] = bad
            # The setting is read once, when the agent module loads: that is where it is logged.
            with self.assertLogs("conversation.agent.stt_models", level="ERROR"):
                self.entrypoint = _reload(self)
            await self.run_entrypoint()
            factory = self.build_stt.call_args.kwargs["openai_factory"]
            self.assertEqual(factory().model, "gpt-4o-mini-transcribe")

    async def test_blank_env_values_fall_back_to_the_defaults(self):
        os.environ["LLM_MODEL"] = "  "
        os.environ["STT_MODEL"] = ""
        self.entrypoint = _reload(self)
        await self.run_entrypoint()
        self.assertEqual(self.session.kwargs["llm"].model, "gpt-5.4-mini")


def _reload(testcase):
    """Re-import entrypoint so its module-level env reads see the test's environment."""
    import importlib
    import sys

    sys.modules.pop("conversation.agent.entrypoint", None)
    return importlib.import_module("conversation.agent.entrypoint")
