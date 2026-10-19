"""Privacy / no-religious-judgement tests (plan 7.5). Synthetic strings only."""
import uuid
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase

from authentication.models import ChildProfile, ParentChildLink, ParentProfile
from conversation.models import Message, Session
from conversation.serializers import ParentSessionSummarySerializer
from rest_framework.test import APIClient
from reporting import prompts
from reporting.models import SessionReport
from reporting.services import (
    _update_weekly_summary,
    contains_scripture_markers,
    filter_suggested_topics,
    strip_scripture_sentences,
)

User = get_user_model()

ALL_PROMPTS = {
    "session": prompts.SESSION_REPORT_SYSTEM,
    "memory": prompts.ROLLING_SUMMARY_SYSTEM,
    "quests": prompts.QUEST_GENERATION_SYSTEM,
    "weekly": prompts.WEEKLY_SUMMARY_SYSTEM,
}


class PromptRulesTests(SimpleTestCase):
    def test_every_prompt_forbids_inferring_religious_practice(self):
        for name, text in ALL_PROMPTS.items():
            low = text.lower()
            self.assertIn("prayer habits", low, name)
            self.assertIn("never infer", low, name)

    def test_every_prompt_forbids_scripture_and_rulings(self):
        for name, text in ALL_PROMPTS.items():
            low = text.lower()
            self.assertIn("scripture", low, name)
            self.assertIn("fatwa", low, name)

    def test_memory_keeps_only_child_stated_facts(self):
        self.assertIn("only facts the CHILD stated", prompts.ROLLING_SUMMARY_SYSTEM)
        self.assertIn("companion's statements", prompts.ROLLING_SUMMARY_SYSTEM)

    def test_quests_use_religion_only_via_existing_value(self):
        self.assertIn("naming an existing Value", prompts.QUEST_GENERATION_SYSTEM)

    def test_json_contracts_intact(self):
        self.assertIn('"values_to_revisit"', prompts.SESSION_REPORT_SYSTEM)
        self.assertIn('"rolling_summary"', prompts.ROLLING_SUMMARY_SYSTEM)
        self.assertIn('"decision"', prompts.QUEST_GENERATION_SYSTEM)
        self.assertIn('"suggested_topics"', prompts.WEEKLY_SUMMARY_SYSTEM)


class ScripturePostFilterTests(SimpleTestCase):
    def test_detects_markers(self):
        for text in (
            "x ﴾ نص تجريبي ﴿ y",
            "قال رسول الله نص تجريبي",
            "قال الله تعالى نص تجريبي",
            "The Prophet said PLACEHOLDER",
            "Allah says PLACEHOLDER",
            "aۖbۗcۘ",
        ):
            self.assertTrue(contains_scripture_markers(text), text)

    def test_clean_text_untouched(self):
        text = "Your child talked about a cat named Luna. They enjoyed it."
        self.assertFalse(contains_scripture_markers(text))
        self.assertEqual(strip_scripture_sentences(text), text)

    def test_strips_only_offending_sentence(self):
        out = strip_scripture_sentences(
            "Good week overall. The Prophet said PLACEHOLDER. Keep chatting."
        )
        self.assertEqual(out, "Good week overall. Keep chatting.")

    def test_fallback_when_nothing_left(self):
        out = strip_scripture_sentences("Allah says PLACEHOLDER.", "Neutral.")
        self.assertEqual(out, "Neutral.")

    def test_newline_split_keeps_other_paragraphs(self):
        out = strip_scripture_sentences("سطر عادي\nقال النبي نص تجريبي\nسطر آخر")
        self.assertEqual(out, "سطر عادي سطر آخر")

    def test_filters_topics(self):
        topics = ["Ask about school", "قال رسول الله نص تجريبي"]
        self.assertEqual(filter_suggested_topics(topics), ["Ask about school"])


class ParentPreviewPrivacyTests(TestCase):
    def test_preview_has_no_message_text(self):
        user = User.objects.create_user(
            username="priv_child", password="testpass123", is_child=True
        )
        child = ChildProfile.objects.create(
            user=user, nickname="K", gender="male", birth_year=2015
        )
        session = Session.objects.create(
            child=child, livekit_room_name=f"r_{uuid.uuid4().hex[:12]}"
        )
        Message.objects.create(
            session=session, sender="child", content="SECRET CHILD TEXT", input_type="text"
        )
        data = ParentSessionSummarySerializer(session).data
        self.assertIn("preview", data)
        self.assertEqual(data["preview"], "")
        self.assertNotIn("SECRET CHILD TEXT", str(data))


class WeeklySummaryPrivacyTests(TestCase):
    def test_model_echo_cannot_send_child_sentence_to_parent(self):
        child_user = User.objects.create_user(username="echo_child", is_child=True)
        child = ChildProfile.objects.create(user=child_user, nickname="K", birth_year=2015)
        parent_user = User.objects.create_user(username="echo_parent", is_parent=True)
        parent = ParentProfile.objects.create(user=parent_user, name="P")
        ParentChildLink.objects.create(parent=parent, child=child, consent_status="approved")
        session = Session.objects.create(child=child, livekit_room_name="echo_room", status="ended")
        private_sentence = "My blue backpack holds a secret paper crane."
        Message.objects.create(session=session, sender="child", content=private_sentence)
        report = SessionReport.objects.create(
            session=session,
            raw_llm_output={"key_moments": [private_sentence]},
        )
        with patch("reporting.services.call_llm", return_value={
            "summary": private_sentence, "suggested_topics": [private_sentence],
        }):
            _update_weekly_summary(report)

        client = APIClient()
        client.force_authenticate(parent_user)
        response = client.get(f"/api/reporting/insights/{child.pk}/", secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(private_sentence, response.content.decode())


class QuestLogPrivacyTests(TestCase):
    def test_model_skip_reason_cannot_echo_child_text_into_logs(self):
        from reporting.services import _generate_quests_for_report

        child_user = User.objects.create_user(username="log_child", is_child=True)
        child = ChildProfile.objects.create(user=child_user, nickname="K", birth_year=2015)
        session = Session.objects.create(child=child, livekit_room_name="log_room")
        private_sentence = "My blue backpack holds a secret paper crane."
        report = SessionReport.objects.create(
            session=session, raw_llm_output={"key_moments": [private_sentence]},
        )
        with patch("reporting.services.should_generate_quests_for_child", return_value=True), \
                patch("reporting.services._open_quests_for_prompt", return_value=("", 0)), \
                patch("reporting.services._completed_quests_text_for_prompt", return_value=""), \
                patch("reporting.services._value_choices", return_value={}), \
                patch("reporting.services.call_llm", return_value={
                    "decision": "skip", "reason": private_sentence,
                }), \
                self.assertLogs("reporting.services", level="INFO") as captured:
            _generate_quests_for_report(report)
        self.assertNotIn(private_sentence, "\n".join(captured.output))


class RollingSummaryFilterTests(TestCase):
    def _child(self):
        user = User.objects.create_user(
            username="mem_child", password="testpass123", is_child=True
        )
        child = ChildProfile.objects.create(
            user=user, nickname="M", gender="male", birth_year=2015
        )
        session = Session.objects.create(
            child=child, livekit_room_name=f"r_{uuid.uuid4().hex[:12]}"
        )
        return child, session

    def _run(self, summary):
        from unittest.mock import patch
        from reporting.models import ChildSessionMemory, SessionReport
        from reporting.services import _update_rolling_summary

        child, session = self._child()
        report = SessionReport.objects.create(session=session, insight_summary="x")
        with patch("reporting.services.call_llm", return_value={"rolling_summary": summary}):
            _update_rolling_summary(report)
        return ChildSessionMemory.objects.get(child=child).rolling_summary

    def test_scripture_sentence_stripped_from_memory(self):
        saved = self._run("Has a cat named Luna. Allah says PLACEHOLDER.")
        self.assertEqual(saved, "Has a cat named Luna.")

    def test_empty_after_filter_not_saved(self):
        self.assertFalse(self._run("Allah says PLACEHOLDER."))


class SessionReportEchoTests(SimpleTestCase):
    def test_model_echo_is_stripped_from_session_report(self):
        from reporting.services import _generate_report_dict

        said = "My blue backpack holds a secret paper crane."
        messages = [{"sender": "child", "content": said, "input_type": "voice", "created_at": None}]
        with patch("reporting.services._value_choices", return_value={}), \
                patch("reporting.services.call_llm", return_value={
                    "summary": f"They talked about school. {said}", "recommendations": said,
                }):
            data = _generate_report_dict(messages)
        self.assertEqual(data["insight_summary"], "They talked about school.")
        self.assertEqual(data["recommendations"], "")
        # The weekly prompt reads these copies, so they must be clean too.
        self.assertEqual(data["raw_llm_output"]["summary"], "They talked about school.")
        self.assertEqual(data["raw_llm_output"]["recommendations"], "")

    def test_arabic_spelling_variants_are_still_an_echo(self):
        from reporting.services import _generate_report_dict

        said = "انا ضربت اخي الصغير في المدرسة اليوم"  # STT: no hamza
        echo = "أنا ضَرَبتُ أخي الصغير في المدرسة اليوم"  # model: hamza + harakat
        messages = [{"sender": "child", "content": said, "input_type": "voice", "created_at": None}]
        with patch("reporting.services._value_choices", return_value={}), \
                patch("reporting.services.call_llm", return_value={
                    "summary": f"تحدثا عن المدرسة. {echo}", "recommendations": echo,
                }):
            data = _generate_report_dict(messages)
        self.assertEqual(data["insight_summary"], "تحدثا عن المدرسة.")
        self.assertEqual(data["recommendations"], "")
