"""Tests for speak-first handling (speak_first.py) and the prompt changes that go with it.

The gate tests use plain event objects. One class drives the REAL livekit event and
AgentSession emitter when livekit-agents is installed.

No Quran text appears here.

Run from backend/:  python manage.py test conversation.agent.test_speak_first \
    --settings=config.settings_sqlite_test
"""
from __future__ import annotations

import unittest
from types import SimpleNamespace

from conversation.agent import speak_first
from conversation.agent.speak_first import SpeakFirstGate
from conversation.agent.test_voice_wiring import (
    _HAS_LIVEKIT,
    _import_agent_modules_against_fake_livekit,
    _WiringBase,
)

LEVEL_UP = "- celebrate this!"


def _state(old, new):
    return SimpleNamespace(old_state=old, new_state=new)


def _item(role, text):
    return SimpleNamespace(item=SimpleNamespace(role=role, text_content=text))


class _Event:
    """Shaped like FunctionToolsExecutedEvent: records cancel_tool_reply."""

    def __init__(self, *names, outputs=None):
        self.function_calls = [SimpleNamespace(name=n) for n in names]
        outputs = outputs if outputs is not None else ["Recorded +5 points (total 5)."] * len(names)
        self.function_call_outputs = [SimpleNamespace(output=o) for o in outputs]
        self.reply_required = True

    def cancel_tool_reply(self):
        self.reply_required = False


def _gate():
    return SpeakFirstGate(level_up_note=LEVEL_UP)


def _after_spoken_reply(gate):
    gate.on_agent_state_changed(_state("listening", "thinking"))
    gate.on_agent_state_changed(_state("thinking", "speaking"))
    gate.on_conversation_item_added(_item("assistant", "Ma sha Allah, well done."))
    gate.on_agent_state_changed(_state("speaking", "thinking"))  # the pause while tools run


class SpeakFirstGateTests(unittest.TestCase):
    def test_points_after_the_words_get_no_second_round(self):
        gate = _gate()
        _after_spoken_reply(gate)
        event = _Event("record_engagement")
        gate.on_function_tools_executed(event)
        self.assertFalse(event.reply_required)
        self.assertEqual(gate.cancelled_rounds, 1)

    def test_text_only_session_counts_the_assistant_message_as_heard(self):
        gate = _gate()
        gate.on_agent_state_changed(_state("listening", "thinking"))
        gate.on_conversation_item_added(_item("assistant", "That was brave of you."))
        event = _Event("record_engagement")
        gate.on_function_tools_executed(event)
        self.assertFalse(event.reply_required)

    def test_points_before_any_words_keep_the_round_so_the_child_gets_an_answer(self):
        gate = _gate()
        gate.on_agent_state_changed(_state("listening", "thinking"))
        event = _Event("record_engagement")
        gate.on_function_tools_executed(event)
        self.assertTrue(event.reply_required)
        self.assertEqual(gate.cancelled_rounds, 0)

    def test_a_new_turn_forgets_the_last_turns_words(self):
        gate = _gate()
        _after_spoken_reply(gate)
        gate.on_agent_state_changed(_state("speaking", "listening"))
        gate.on_agent_state_changed(_state("listening", "thinking"))  # next turn, tool first
        event = _Event("record_engagement")
        gate.on_function_tools_executed(event)
        self.assertTrue(event.reply_required)

    def test_a_child_line_during_the_greeting_starts_a_new_turn(self):
        # livekit's echo warm-up keeps interruptions off for the greeting's first seconds, so a
        # child's turn can start thinking straight from "speaking". The greeting's words must
        # not count as the answer to the child.
        gate = _gate()
        gate.on_agent_state_changed(_state("listening", "thinking"))
        gate.on_agent_state_changed(_state("thinking", "speaking"))  # the greeting
        gate.on_conversation_item_added(_item("user", "I broke the vase today"))
        gate.on_agent_state_changed(_state("speaking", "thinking"))
        event = _Event("record_engagement")  # tool first, no words yet
        gate.on_function_tools_executed(event)
        self.assertTrue(event.reply_required)

    def test_level_up_keeps_the_round_so_the_model_can_celebrate(self):
        gate = _gate()
        _after_spoken_reply(gate)
        event = _Event("record_engagement", outputs=[f"Recorded +10 points. Level 2: Friend {LEVEL_UP}"])
        gate.on_function_tools_executed(event)
        self.assertTrue(event.reply_required)

    def test_other_tools_are_never_cancelled(self):
        for name in ("flag_safety_concern", "get_islamic_reference",
                     "complete_conversation_quest", "list_my_quests"):
            with self.subTest(tool=name):
                gate = _gate()
                _after_spoken_reply(gate)
                event = _Event(name)
                gate.on_function_tools_executed(event)
                self.assertTrue(event.reply_required)

    def test_a_mixed_turn_is_never_cancelled(self):
        gate = _gate()
        _after_spoken_reply(gate)
        event = _Event("record_engagement", "flag_safety_concern")
        gate.on_function_tools_executed(event)
        self.assertTrue(event.reply_required)

    def test_child_messages_do_not_count_as_heard(self):
        gate = _gate()
        gate.on_agent_state_changed(_state("listening", "thinking"))
        gate.on_conversation_item_added(_item("user", "hello"))
        event = _Event("record_engagement")
        gate.on_function_tools_executed(event)
        self.assertTrue(event.reply_required)

    def test_broken_events_never_raise(self):
        gate = _gate()
        gate.on_agent_state_changed(None)
        gate.on_conversation_item_added(None)
        gate.on_function_tools_executed(None)
        gate.on_function_tools_executed(SimpleNamespace(function_calls=[SimpleNamespace(name="record_engagement")],
                                                         function_call_outputs=[]))

    def test_attach_registers_the_three_events(self):
        events = []
        session = SimpleNamespace(on=lambda name, cb=None, **kw: events.append(name))
        speak_first.attach_speak_first(session, level_up_note=LEVEL_UP)
        self.assertEqual(
            sorted(events),
            ["agent_state_changed", "conversation_item_added", "function_tools_executed"],
        )


class SpeakFirstWiringTests(_WiringBase):
    async def test_entrypoint_attaches_the_gate_with_the_agents_level_up_note(self):
        await self.run_entrypoint()
        self.assertIn("function_tools_executed", self.session.handlers)
        self.assertIn("conversation_item_added", self.session.handlers)
        # The note the tool appends is the one the gate looks for.
        self.assertTrue(self.agent_class.LEVEL_UP_NOTE.strip())


class QuestPrefetchAndPromptTests(unittest.TestCase):
    def setUp(self):
        self.agent_class, _ = _import_agent_modules_against_fake_livekit(self)

    def _prompt(self, **kw):
        agent = self.agent_class.AlSadiqAgent(db_session_id=1, child_id=2, **kw)
        return agent._instructions

    def test_prompt_says_the_quests_are_already_listed(self):
        text = self._prompt(active_quests_text="- progress_id=4 | Tell the truth | type=conversation")
        self.assertIn("open quests are listed below", text)
        self.assertIn("progress_id=4", text)
        self.assertNotIn("check list_my_quests", text)

    def test_prompt_says_speak_first_then_record_engagement(self):
        text = self._prompt()
        self.assertIn("AFTER your spoken words", text)
        self.assertIn("never before them", text)

    def test_the_level_up_note_is_in_the_tool_result(self):
        import inspect

        source = inspect.getsource(self.agent_class.AlSadiqAgent.record_engagement)
        self.assertIn("LEVEL_UP_NOTE", source)

    def test_islamic_content_comes_from_the_search_tool_not_an_injection(self):
        self.assertTrue(hasattr(self.agent_class.AlSadiqAgent, "search_bank"))
        self.assertIn("search_bank", self._prompt())


@unittest.skipUnless(_HAS_LIVEKIT, "livekit-agents is not installed (or cannot be imported)")
class RealLivekitGateTests(unittest.IsolatedAsyncioTestCase):
    def _emit(self, session, *calls):
        from livekit.agents.llm import FunctionCall, FunctionCallOutput
        from livekit.agents.voice.events import FunctionToolsExecutedEvent

        event = FunctionToolsExecutedEvent(
            function_calls=[FunctionCall(call_id=f"c{i}", name=n, arguments="{}")
                            for i, (n, _o) in enumerate(calls)],
            function_call_outputs=[FunctionCallOutput(call_id=f"c{i}", name=n, output=o, is_error=False)
                                   for i, (n, o) in enumerate(calls)],
        )
        event._reply_required = True
        session.emit("function_tools_executed", event)
        return event

    async def test_real_event_loses_its_reply_when_only_points_were_recorded(self):
        from livekit.agents import AgentSession

        session = AgentSession()
        gate = speak_first.attach_speak_first(session, level_up_note=LEVEL_UP)
        gate.on_agent_state_changed(_state("listening", "thinking"))
        gate.on_agent_state_changed(_state("thinking", "speaking"))
        event = self._emit(session, ("record_engagement", "Recorded +5 points (total 5)."))
        self.assertFalse(event._reply_required)

    async def test_real_event_keeps_its_reply_for_another_tool(self):
        from livekit.agents import AgentSession

        session = AgentSession()
        gate = speak_first.attach_speak_first(session, level_up_note=LEVEL_UP)
        gate.on_agent_state_changed(_state("listening", "thinking"))
        gate.on_agent_state_changed(_state("thinking", "speaking"))
        event = self._emit(session, ("get_islamic_reference", "some reference"))
        self.assertTrue(event._reply_required)
