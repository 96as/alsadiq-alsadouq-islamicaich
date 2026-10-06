"""Child-echo filtering at WRITE time (sec2 area 1). Synthetic strings only.

The session's messages are deleted right after its report is written, so everything
parent-facing (weekly LLM input, quests) must already be echo-free by then.
"""
import json
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from authentication.models import ChildProfile, ParentChildLink, ParentProfile
from conversation.models import Message, Session
from gamification.models import Quest
from reporting.models import SessionReport, WeeklySummary
from reporting.services import (
    _build_reports_json,
    _cleanup_messages,
    _generate_quests_for_report,
    _generate_report_dict,
    _update_weekly_summary,
    post_session_pipeline,
)

User = get_user_model()

EN = "My blue backpack holds a secret paper crane."
AR = "أحب اللعب مع صديقي الجديد في المدرسة كل يوم"
AR_STT = "احب اللعب مع صديقى الجديد فى المدرسه كل يوم"  # STT-style spelling of AR


def _msgs(*child_texts):
    return [
        {"sender": "child", "content": t, "input_type": "text", "created_at": None}
        for t in child_texts
    ] + [{"sender": "system", "content": "Tell me more!", "input_type": "text", "created_at": None}]


def _llm_report(sentence):
    return {
        "summary": "A friendly chat.",
        "recommendations": "Ask about school.",
        "themes_discussed": ["school", sentence],
        "emotional_progression": f"Happy.\n{sentence}\nStayed calm.",
        "key_moments": [sentence, "Mentioned a pet cat"],
        "memorable_facts": [sentence, "Has a cat named Luna"],
        "values_to_revisit": [],
    }


class SessionReportWriteTimeTests(TestCase):
    def test_parent_view_is_echo_free_and_memory_fields_stay_intact(self):
        for sentence in (EN, AR):
            with self.subTest(sentence=sentence), \
                    patch("reporting.services.call_llm", return_value=_llm_report(sentence)):
                raw = _generate_report_dict(_msgs(sentence))["raw_llm_output"]
            # Agent memory input is unchanged.
            self.assertEqual(raw["key_moments"], [sentence, "Mentioned a pet cat"])
            self.assertEqual(raw["memorable_facts"], [sentence, "Has a cat named Luna"])
            # Parent / weekly-LLM copy has no echo, but keeps the harmless parts.
            view = raw["parent_view"]
            self.assertNotIn(sentence, json.dumps(view, ensure_ascii=False))
            self.assertEqual(view["key_moments"], ["Mentioned a pet cat"])
            self.assertEqual(view["themes_discussed"], ["school"])
            self.assertIn("Stayed calm.", view["emotional_progression"])

    def test_arabic_spelling_variant_is_still_caught(self):
        with patch("reporting.services.call_llm", return_value=_llm_report(AR_STT)):
            raw = _generate_report_dict(_msgs(AR))["raw_llm_output"]
        self.assertEqual(raw["parent_view"]["key_moments"], ["Mentioned a pet cat"])

    def test_rolling_summary_prompt_does_not_carry_the_duplicate_view(self):
        from reporting.services import _raw_for_prompt

        with patch("reporting.services.call_llm", return_value=_llm_report(EN)):
            data = _generate_report_dict(_msgs(EN))
        report = SessionReport(raw_llm_output=data["raw_llm_output"])
        prompt_raw = _raw_for_prompt(report)
        self.assertNotIn("parent_view", prompt_raw)
        self.assertEqual(prompt_raw["key_moments"][0], EN)

    def test_weekly_json_never_reads_unfiltered_fields(self):
        """Legacy rows (no parent_view) fail closed: child-derived free text is omitted."""
        report = SessionReport(raw_llm_output={
            "summary": "S", "key_moments": [EN], "emotional_progression": EN,
            "themes_discussed": [EN],
        })
        out = _build_reports_json([report])
        self.assertNotIn(EN, out)

    def test_weekly_json_uses_parent_view(self):
        with patch("reporting.services.call_llm", return_value=_llm_report(EN)):
            raw = _generate_report_dict(_msgs(EN))["raw_llm_output"]
        item = json.loads(_build_reports_json([SessionReport(raw_llm_output=raw)]))[0]
        self.assertEqual(item["key_moments"], ["Mentioned a pet cat"])
        self.assertEqual(item["themes_discussed"], ["school"])
        self.assertNotIn(EN, json.dumps(item))


class WeeklyAfterCleanupTests(TestCase):
    def _setup(self):
        child_user = User.objects.create_user(username="wk_child", is_child=True)
        child = ChildProfile.objects.create(user=child_user, nickname="K", birth_year=2015)
        parent_user = User.objects.create_user(username="wk_parent", is_parent=True)
        parent = ParentProfile.objects.create(user=parent_user, name="P")
        ParentChildLink.objects.create(parent=parent, child=child, consent_status="approved")
        return child

    @override_settings(REPORTING_GENERATE_WEEKLY_SUMMARY=True, REPORTING_WEEKLY_SUMMARY_THROTTLE_HOURS=0)
    def test_weekly_llm_input_is_echo_free_after_messages_are_deleted(self):
        child = self._setup()
        for i, sentence in enumerate((EN, AR)):
            session = Session.objects.create(
                child=child, livekit_room_name=f"wk_room_{i}", status="ended")
            Message.objects.create(session=session, sender="child", content=sentence)
            with patch("reporting.services.call_llm", return_value=_llm_report(sentence)):
                data = _generate_report_dict(_msgs(sentence))
            report = SessionReport.objects.create(session=session, **data)
            _cleanup_messages(session)
        self.assertFalse(Message.objects.filter(sender="child").exists())

        with patch("reporting.services.call_llm", return_value={
                "summary": "A good week.", "suggested_topics": []}) as llm:
            _update_weekly_summary(report)
        sent = llm.call_args.args[1]
        self.assertNotIn(EN, sent)
        self.assertNotIn(AR, sent)
        self.assertTrue(WeeklySummary.objects.filter(child=child).exists())


def _quest_llm(sentence):
    return {"decision": "add", "quests": [
        {"title": sentence, "description": sentence, "reward_points": 10,
         "quest_type": "reflection"},
        {"title": "Kind words", "description": f"Practise kindness.\n{sentence}\nTry again.",
         "reward_points": 10, "quest_type": "reflection"},
    ]}


class QuestWriteTimeTests(TestCase):
    def _report(self, name):
        user = User.objects.create_user(username=name, is_child=True)
        child = ChildProfile.objects.create(user=user, nickname="K", birth_year=2015)
        session = Session.objects.create(child=child, livekit_room_name=f"{name}_room")
        return SessionReport.objects.create(session=session, raw_llm_output={})

    def _generate(self, report, sentence, child_texts):
        with patch("reporting.services.should_generate_quests_for_child", return_value=True), \
                patch("reporting.services._open_quests_for_prompt", return_value=("", 0)), \
                patch("reporting.services._completed_quests_text_for_prompt", return_value=""), \
                patch("reporting.services.call_llm", return_value=_quest_llm(sentence)):
            _generate_quests_for_report(report, child_texts)

    def test_quest_title_and_description_are_echo_free(self):
        for i, sentence in enumerate((EN, AR)):
            with self.subTest(sentence=sentence):
                report = self._report(f"q_child_{i}")
                self._generate(report, sentence, [sentence])
                quests = list(Quest.objects.filter(session_report=report))
                self.assertEqual([q.title for q in quests], ["Kind words"])  # echo title dropped
                self.assertEqual(quests[0].description, "Practise kindness. Try again.")
                for q in quests:
                    self.assertNotIn(sentence, q.title + q.description)

    def test_pipeline_filters_quests_even_though_messages_are_deleted(self):
        report = self._report("q_pipe_child")
        session = report.session
        session.status = "ended"
        session.save()
        report.delete()
        Message.objects.create(session=session, sender="child", content=EN)
        Message.objects.create(session=session, sender="system", content="Tell me more!")

        def fake_llm(system, user, **kw):
            if "quest" in system.lower() and '"decision"' in system:
                return _quest_llm(EN)
            if "rolling_summary" in system:
                return {"rolling_summary": ""}
            return _llm_report(EN)

        with patch("reporting.services.should_generate_quests_for_child", return_value=True), \
                patch("reporting.services._open_quests_for_prompt", return_value=("", 0)), \
                patch("reporting.services._completed_quests_text_for_prompt", return_value=""), \
                patch("reporting.services.call_llm", side_effect=fake_llm):
            post_session_pipeline(session.pk)
        self.assertFalse(Message.objects.filter(session=session, sender="child").exists())
        quests = Quest.objects.filter(session_report__session=session)
        self.assertTrue(quests.exists())
        for q in quests:
            self.assertNotIn(EN, q.title + q.description)
