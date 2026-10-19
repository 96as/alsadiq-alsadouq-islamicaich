"""F13: typed text is cut for the model and the database, but the guard still reads all of it."""
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from conversation.agent import turn_pipeline
from conversation.agent.agent_class import AlSadiqAgent
from conversation.agent.turn_guard import SAFETY, GuardHit

LIMIT = turn_pipeline.TYPED_TEXT_LLM_MAX_CHARS
DISCLOSURE = "I wish I could just disappear"


class CapTypedTextTests(SimpleTestCase):
    def test_short_text_is_unchanged(self):
        self.assertEqual(turn_pipeline.cap_typed_text("hello there"), "hello there")
        self.assertEqual(turn_pipeline.cap_typed_text("x" * LIMIT), "x" * LIMIT)

    def test_long_text_is_cut(self):
        self.assertEqual(len(turn_pipeline.cap_typed_text("y" * 3000)), LIMIT)

    def test_none_is_empty(self):
        self.assertEqual(turn_pipeline.cap_typed_text(None), "")


class LongTypedMessageTests(SimpleTestCase):
    def _send(self, text):
        agent = AlSadiqAgent(db_session_id=1, child_id=1)
        session = MagicMock()
        seen = []

        def check(t):  # stands in for the guard: records what it was given
            seen.append(t)
            if DISCLOSURE in t:
                return GuardHit(kind=SAFETY, rule_id="self_harm", level="D", flag_type="harmful", note="NOTE")

        with patch.object(turn_pipeline, "check", check):
            agent.reply_to_typed(session, text)
        message = session.generate_reply.call_args.kwargs["user_input"]
        return agent, message, seen

    def test_a_safety_rule_at_the_end_of_3000_characters_still_fires(self):
        text = ("I like my dog and my cat. " * 120)[:2900] + " " + DISCLOSURE
        self.assertGreater(len(text), 2900)
        agent, message, seen = self._send(text)
        self.assertEqual(seen, [text])  # the guard read all of it
        self.assertTrue(agent._safety_turn)
        self.assertEqual(agent.last_hit.kind, SAFETY)
        self.assertLessEqual(len(message.text_content), LIMIT)
        self.assertNotIn(DISCLOSURE, message.text_content)  # it was past the cut: only the guard saw it

    def test_a_normal_message_reaches_the_model_unchanged(self):
        agent, message, _seen = self._send("I scored a goal today")
        self.assertEqual(message.text_content, "I scored a goal today")
        self.assertFalse(agent._safety_turn)
