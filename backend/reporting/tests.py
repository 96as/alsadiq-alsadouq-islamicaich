import uuid
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from authentication.models import ChildProfile, ParentChildLink, ParentProfile
from conversation.models import Message, Session
from conversation.services import end_session
from content_safety.models import SafetyFlag
from gamification.models import ChildQuestProgress, Quest
from reporting.models import SessionReport, WeeklySummary
from session_moral_context.models import MoralTheme, Value
from reporting.services import (
    _cleanup_messages,
    _fallback_report_data,
    _fallback_weekly_summary,
    format_transcript,
    post_session_pipeline,
    should_generate_quests_for_child,
)

User = get_user_model()


def _unique_room():
    return f"test_room_{uuid.uuid4().hex[:16]}"


class ReportingHelpersTests(TestCase):
    def test_format_transcript(self):
        messages = [
            {"sender": "child", "content": "Hello", "input_type": "text"},
            {"sender": "system", "content": "Hi!", "input_type": "voice"},
        ]
        out = format_transcript(messages)
        self.assertIn("[child]", out)
        self.assertIn("Hello", out)

    def test_fallback_report_data_empty(self):
        d = _fallback_report_data([])
        self.assertIn("insight_summary", d)
        self.assertEqual(d["raw_llm_output"]["message_count"], 0)


class MessageCleanupSafetyTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="cleanup_child",
            password="testpass123",
            is_child=True,
        )
        self.child = ChildProfile.objects.create(
            user=self.user,
            nickname="CleanupKid",
            gender="male",
            birth_year=2015,
        )
        self.session = Session.objects.create(
            child=self.child,
            status="ended",
            livekit_room_name=_unique_room(),
        )

    def test_cleanup_keeps_flagged_child_message_and_deletes_unflagged_messages(self):
        flagged = Message.objects.create(
            session=self.session,
            sender="child",
            content="unsafe topic",
            input_type="voice",
        )
        Message.objects.create(
            session=self.session,
            sender="child",
            content="ordinary child message",
            input_type="voice",
        )
        Message.objects.create(
            session=self.session,
            sender="system",
            content="ordinary assistant message",
            input_type="voice",
        )
        SafetyFlag.objects.create(
            message=flagged,
            flag_type="sensitive",
            description="Needs parent follow-up.",
        )

        _cleanup_messages(self.session)

        remaining = list(Message.objects.filter(session=self.session))
        self.assertEqual(remaining, [flagged])


class EndSessionSchedulesPipelineTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="report_pipeline_child",
            password="testpass123",
            is_child=True,
        )
        self.child = ChildProfile.objects.create(
            user=self.user,
            nickname="Kid",
            gender="male",
            birth_year=2015,
        )
        self.session = Session.objects.create(child=self.child, status="active")

    @patch("reporting.services.run_post_session_pipeline")
    def test_end_session_marks_ended_and_schedules_pipeline(self, mock_run):
        end_session(self.session)
        self.session.refresh_from_db()
        self.assertEqual(self.session.status, "ended")
        self.assertIsNotNone(self.session.ended_at)
        mock_run.assert_called_once_with(self.session.id)


@patch("reporting.services.close_old_connections")
class PostSessionReportTranscriptTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="report_transcript_child",
            password="testpass123",
            is_child=True,
        )
        self.child = ChildProfile.objects.create(
            user=self.user,
            nickname="ReportKid",
            gender="male",
            birth_year=2015,
        )
        self.session = Session.objects.create(
            child=self.child,
            status="ended",
            livekit_room_name=_unique_room(),
        )
        Message.objects.create(
            session=self.session,
            sender="child",
            content="I felt calm today.",
            input_type="voice",
        )
        Message.objects.create(
            session=self.session,
            sender="system",
            content="That is good to hear.",
            input_type="voice",
        )

    @override_settings(
        REPORTING_GENERATE_QUESTS=False,
        REPORTING_GENERATE_WEEKLY_SUMMARY=False,
    )
    @patch("reporting.services.call_llm")
    def test_pipeline_uses_llm_report_when_transcript_messages_exist(
        self,
        mock_llm,
        _mock_close,
    ):
        mock_llm.side_effect = [_llm_report(), _llm_memory()]

        post_session_pipeline(self.session.id)

        report = SessionReport.objects.get(session=self.session)
        self.assertEqual(report.insight_summary, "S")
        self.assertEqual(report.raw_llm_output["summary"], "S")
        self.assertNotEqual(report.raw_llm_output.get("fallback"), True)


def _llm_report():
    return {"summary": "S", "recommendations": "R", "values_to_revisit": []}


def _llm_memory():
    return {"rolling_summary": "Memory line"}


def _llm_quests():
    return {
        "quests": [
            {
                "title": "Quest One",
                "description": "Do a kind thing",
                "reward_points": 10,
                "moral_theme": "Kindness",
            }
        ]
    }


def _llm_weekly_summary():
    return {
        "summary": "Your child had a wonderful week exploring kindness and gratitude.",
        "suggested_topics": [
            "Ask about a kind thing they did today",
            "Discuss what gratitude means to them",
            "Share a story about helping others",
        ],
    }


class ShouldGenerateQuestsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="quest_guard_child",
            password="testpass123",
            is_child=True,
        )
        self.child = ChildProfile.objects.create(
            user=self.user,
            nickname="QKid",
            gender="male",
            birth_year=2015,
        )
        self.session = Session.objects.create(
            child=self.child,
            status="ended",
            livekit_room_name=_unique_room(),
        )
        self.report = SessionReport.objects.create(
            session=self.session,
            insight_summary="x",
            recommendations="",
        )

    @override_settings(REPORTING_GENERATE_QUESTS=False)
    def test_off_when_master_switch_disabled(self):
        self.assertFalse(
            should_generate_quests_for_child(self.child, self.report)
        )

    @override_settings(
        REPORTING_GENERATE_QUESTS=True,
        REPORTING_QUESTS_DAILY_CAP=True,
        REPORTING_QUESTS_SKIP_IF_PENDING=False,
    )
    def test_false_when_quests_already_on_report(self):
        Quest.objects.create(
            title="Existing",
            is_ai_generated=True,
            session_report=self.report,
        )
        self.assertFalse(
            should_generate_quests_for_child(self.child, self.report)
        )

    @override_settings(
        REPORTING_GENERATE_QUESTS=True,
        REPORTING_QUESTS_DAILY_CAP=True,
        REPORTING_QUESTS_SKIP_IF_PENDING=True,
        REPORTING_QUESTS_MAX_PENDING=1,
    )
    def test_false_when_pending_ai_quests_and_flag_on(self):
        other_session = Session.objects.create(
            child=self.child,
            status="ended",
            livekit_room_name=_unique_room(),
        )
        other_report = SessionReport.objects.create(session=other_session)
        q = Quest.objects.create(
            title="Pending Q",
            is_ai_generated=True,
            session_report=other_report,
        )
        ChildQuestProgress.objects.create(
            child=self.child, quest=q, status="not_started"
        )
        self.assertFalse(
            should_generate_quests_for_child(self.child, self.report)
        )

    @override_settings(
        REPORTING_GENERATE_QUESTS=True,
        REPORTING_QUESTS_DAILY_CAP=False,
        REPORTING_QUESTS_SKIP_IF_PENDING=False,
    )
    def test_true_when_pending_but_flag_off(self):
        other_session = Session.objects.create(
            child=self.child,
            status="ended",
            livekit_room_name=_unique_room(),
        )
        other_report = SessionReport.objects.create(session=other_session)
        q = Quest.objects.create(
            title="Pending Q",
            is_ai_generated=True,
            session_report=other_report,
        )
        ChildQuestProgress.objects.create(
            child=self.child, quest=q, status="not_started"
        )
        self.assertTrue(
            should_generate_quests_for_child(self.child, self.report)
        )

    @override_settings(
        REPORTING_GENERATE_QUESTS=True,
        REPORTING_QUESTS_DAILY_CAP=True,
        REPORTING_QUESTS_SKIP_IF_PENDING=False,
    )
    def test_false_daily_cap_other_report_same_day(self):
        s1 = Session.objects.create(
            child=self.child,
            status="ended",
            livekit_room_name=_unique_room(),
        )
        r1 = SessionReport.objects.create(session=s1)
        Quest.objects.create(
            title="From earlier session",
            is_ai_generated=True,
            session_report=r1,
        )
        s2 = Session.objects.create(
            child=self.child,
            status="ended",
            livekit_room_name=_unique_room(),
        )
        r2 = SessionReport.objects.create(session=s2)
        self.assertFalse(should_generate_quests_for_child(self.child, r2))


@patch("reporting.services.close_old_connections")
class PostSessionQuestThrottleIntegrationTests(TestCase):
    """post_session_pipeline + call_llm call counts (quest step optional)."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="quest_pipe_child",
            password="testpass123",
            is_child=True,
        )
        self.child = ChildProfile.objects.create(
            user=self.user,
            nickname="PipeKid",
            gender="male",
            birth_year=2015,
        )
        self.session = Session.objects.create(
            child=self.child,
            status="ended",
            livekit_room_name=_unique_room(),
        )
        Message.objects.create(
            session=self.session,
            sender="child",
            content="Hello",
            input_type="text",
        )

    @override_settings(REPORTING_GENERATE_QUESTS=False)
    @patch("reporting.services.call_llm")
    def test_quest_llm_skipped_when_disabled(self, mock_llm, _mock_close):
        mock_llm.side_effect = [_llm_report(), _llm_memory()]
        post_session_pipeline(self.session.id)
        self.assertEqual(mock_llm.call_count, 2)

    @override_settings(
        REPORTING_GENERATE_QUESTS=True,
        REPORTING_QUESTS_DAILY_CAP=True,
        REPORTING_QUESTS_SKIP_IF_PENDING=False,
    )
    @patch("reporting.services.call_llm")
    def test_second_session_same_day_skips_quest_llm(self, mock_llm, _mock_close):
        mock_llm.side_effect = [
            _llm_report(),
            _llm_memory(),
            _llm_quests(),
            _llm_report(),
            _llm_memory(),
        ]
        post_session_pipeline(self.session.id)
        session_b = Session.objects.create(
            child=self.child,
            status="ended",
            livekit_room_name=_unique_room(),
        )
        Message.objects.create(
            session=session_b,
            sender="child",
            content="Again",
            input_type="text",
        )
        post_session_pipeline(session_b.id)
        self.assertEqual(mock_llm.call_count, 5)
        self.assertEqual(Quest.objects.filter(is_ai_generated=True).count(), 1)

    @override_settings(
        REPORTING_GENERATE_QUESTS=True,
        REPORTING_QUESTS_DAILY_CAP=False,
        REPORTING_QUESTS_SKIP_IF_PENDING=False,
    )
    @patch("reporting.services.call_llm")
    def test_second_session_runs_quest_when_daily_cap_off(self, mock_llm, _mock_close):
        mock_llm.side_effect = [
            _llm_report(),
            _llm_memory(),
            _llm_quests(),
            _llm_report(),
            _llm_memory(),
            _llm_quests(),
        ]
        post_session_pipeline(self.session.id)
        session_b = Session.objects.create(
            child=self.child,
            status="ended",
            livekit_room_name=_unique_room(),
        )
        Message.objects.create(
            session=session_b,
            sender="child",
            content="Again",
            input_type="text",
        )
        post_session_pipeline(session_b.id)
        self.assertEqual(mock_llm.call_count, 6)
        self.assertEqual(Quest.objects.filter(is_ai_generated=True).count(), 2)


class WeeklySummaryFallbackTests(TestCase):
    def test_fallback_returns_session_count(self):
        result = _fallback_weekly_summary(3)
        self.assertIn("3 session(s)", result["summary"])
        self.assertEqual(result["suggested_topics"], [])

    def test_fallback_zero_sessions(self):
        result = _fallback_weekly_summary(0)
        self.assertIn("0 session(s)", result["summary"])

    def test_arabic_fallback_is_arabic_with_number_agreement(self):
        for count, phrase in [
            (0, "لا جلسات"),
            (1, "جلسة واحدة"),
            (2, "جلستان"),
            (3, "3 جلسات"),
            (10, "10 جلسات"),
            (11, "11 جلسة"),
        ]:
            result = _fallback_weekly_summary(count, "ar")
            self.assertIn(phrase, result["summary"])
            self.assertNotRegex(result["summary"], r"[A-Za-z]")
            self.assertEqual(result["suggested_topics"], [])

    def test_unknown_or_missing_language_falls_back_to_english(self):
        self.assertIn("3 session(s)", _fallback_weekly_summary(3, "en")["summary"])
        self.assertIn("3 session(s)", _fallback_weekly_summary(3, "")["summary"])
        self.assertIn("3 session(s)", _fallback_weekly_summary(3, "fr")["summary"])


def _create_parent_child_pair(child_username, parent_username):
    """Helper to create a child + parent + approved link."""
    child_user = User.objects.create_user(
        username=child_username, password="testpass123", is_child=True,
    )
    child = ChildProfile.objects.create(
        user=child_user, nickname=child_username, gender="male", birth_year=2015,
    )
    parent_user = User.objects.create_user(
        username=parent_username, password="testpass123", is_parent=True,
    )
    parent = ParentProfile.objects.create(user=parent_user, name=parent_username)
    link = ParentChildLink.objects.create(
        parent=parent, child=child, consent_status="approved",
    )
    return child, parent, link


@patch("reporting.services.close_old_connections")
class WeeklySummaryPipelineTests(TestCase):
    """Test weekly summary generation inside the post-session pipeline."""

    def setUp(self):
        self.child, self.parent, self.link = _create_parent_child_pair(
            "ws_child", "ws_parent",
        )
        self.session = Session.objects.create(
            child=self.child, status="ended", livekit_room_name=_unique_room(),
        )
        Message.objects.create(
            session=self.session,
            sender="child",
            content="Hello",
            input_type="text",
        )

    @override_settings(
        REPORTING_GENERATE_QUESTS=False,
        REPORTING_GENERATE_WEEKLY_SUMMARY=True,
    )
    @patch("reporting.services.call_llm")
    def test_pipeline_creates_weekly_summary(self, mock_llm, _mock_close):
        mock_llm.side_effect = [_llm_report(), _llm_memory(), _llm_weekly_summary()]
        post_session_pipeline(self.session.id)

        ws = WeeklySummary.objects.get(child=self.child, parent=self.parent)
        self.assertIn("wonderful week", ws.summary)
        self.assertEqual(len(ws.suggested_topics), 3)
        self.assertEqual(ws.sessions.count(), 1)

    @override_settings(
        REPORTING_GENERATE_QUESTS=False,
        REPORTING_GENERATE_WEEKLY_SUMMARY=True,
        REPORTING_WEEKLY_SUMMARY_THROTTLE_HOURS=0,
    )
    @patch("reporting.services.call_llm")
    def test_second_session_updates_same_weekly_summary(self, mock_llm, _mock_close):
        mock_llm.side_effect = [
            _llm_report(), _llm_memory(), _llm_weekly_summary(),
            _llm_report(), _llm_memory(), _llm_weekly_summary(),
        ]
        post_session_pipeline(self.session.id)

        session_b = Session.objects.create(
            child=self.child, status="ended", livekit_room_name=_unique_room(),
        )
        Message.objects.create(
            session=session_b, sender="child", content="Again", input_type="text",
        )
        post_session_pipeline(session_b.id)

        self.assertEqual(WeeklySummary.objects.filter(child=self.child).count(), 1)
        ws = WeeklySummary.objects.get(child=self.child, parent=self.parent)
        self.assertEqual(ws.sessions.count(), 2)

    @override_settings(
        REPORTING_GENERATE_QUESTS=False,
        REPORTING_GENERATE_WEEKLY_SUMMARY=True,
    )
    @patch("reporting.services.call_llm")
    def test_multiple_parents_get_separate_summaries(self, mock_llm, _mock_close):
        parent_user_2 = User.objects.create_user(
            username="ws_parent2", password="testpass123", is_parent=True,
        )
        parent_2 = ParentProfile.objects.create(user=parent_user_2, name="Parent Two")
        ParentChildLink.objects.create(
            parent=parent_2, child=self.child, consent_status="approved",
        )

        mock_llm.side_effect = [_llm_report(), _llm_memory(), _llm_weekly_summary()]
        post_session_pipeline(self.session.id)

        self.assertEqual(WeeklySummary.objects.filter(child=self.child).count(), 2)
        ws1 = WeeklySummary.objects.get(child=self.child, parent=self.parent)
        ws2 = WeeklySummary.objects.get(child=self.child, parent=parent_2)
        self.assertEqual(ws1.summary, ws2.summary)
        self.assertEqual(mock_llm.call_count, 3)  # One LLM call, not per parent

    @override_settings(
        REPORTING_GENERATE_QUESTS=False,
        REPORTING_GENERATE_WEEKLY_SUMMARY=False,
    )
    @patch("reporting.services.call_llm")
    def test_weekly_summary_skipped_when_disabled(self, mock_llm, _mock_close):
        mock_llm.side_effect = [_llm_report(), _llm_memory()]
        post_session_pipeline(self.session.id)

        self.assertEqual(mock_llm.call_count, 2)
        self.assertFalse(WeeklySummary.objects.filter(child=self.child).exists())

    @override_settings(
        REPORTING_GENERATE_QUESTS=False,
        REPORTING_GENERATE_WEEKLY_SUMMARY=True,
    )
    @patch("reporting.services.call_llm")
    def test_weekly_summary_uses_fallback_on_llm_failure(self, mock_llm, _mock_close):
        mock_llm.side_effect = [
            _llm_report(),
            _llm_memory(),
            Exception("LLM down"),
        ]
        post_session_pipeline(self.session.id)

        ws = WeeklySummary.objects.get(child=self.child, parent=self.parent)
        self.assertIn("1 session(s)", ws.summary)
        self.assertEqual(ws.suggested_topics, [])

    @override_settings(
        REPORTING_GENERATE_QUESTS=False,
        REPORTING_GENERATE_WEEKLY_SUMMARY=True,
    )
    @patch("reporting.services.call_llm")
    def test_weekly_summary_fallback_is_arabic_for_an_arabic_child(self, mock_llm, _mock_close):
        ChildProfile.objects.filter(pk=self.child.pk).update(language_preference="ar")
        mock_llm.side_effect = [
            _llm_report(),
            _llm_memory(),
            Exception("LLM down"),
        ]
        post_session_pipeline(self.session.id)

        ws = WeeklySummary.objects.get(child=self.child, parent=self.parent)
        self.assertIn("جلسة واحدة", ws.summary)
        self.assertNotIn("session(s)", ws.summary)
        self.assertEqual(ws.suggested_topics, [])

    @override_settings(
        REPORTING_GENERATE_QUESTS=False,
        REPORTING_GENERATE_WEEKLY_SUMMARY=True,
        REPORTING_WEEKLY_SUMMARY_THROTTLE_HOURS=24,
    )
    @patch("reporting.services.call_llm")
    def test_throttle_skips_regeneration_within_window(self, mock_llm, _mock_close):
        mock_llm.side_effect = [
            _llm_report(), _llm_memory(), _llm_weekly_summary(),
            _llm_report(), _llm_memory(),
        ]
        post_session_pipeline(self.session.id)

        ws_before = WeeklySummary.objects.get(child=self.child, parent=self.parent)
        updated_at_before = ws_before.updated_at

        session_b = Session.objects.create(
            child=self.child, status="ended", livekit_room_name=_unique_room(),
        )
        Message.objects.create(
            session=session_b, sender="child", content="Again", input_type="text",
        )
        post_session_pipeline(session_b.id)

        # Only 1 weekly-summary LLM call should have fired (throttled on second session)
        self.assertEqual(mock_llm.call_count, 5)
        ws_after = WeeklySummary.objects.get(child=self.child, parent=self.parent)
        self.assertEqual(ws_after.updated_at, updated_at_before)

    @override_settings(
        REPORTING_GENERATE_QUESTS=False,
        REPORTING_GENERATE_WEEKLY_SUMMARY=True,
        REPORTING_WEEKLY_SUMMARY_THROTTLE_HOURS=24,
    )
    @patch("reporting.services.call_llm")
    def test_throttle_allows_regeneration_after_window(self, mock_llm, _mock_close):
        from datetime import timedelta
        from django.utils import timezone

        mock_llm.side_effect = [
            _llm_report(), _llm_memory(), _llm_weekly_summary(),
            _llm_report(), _llm_memory(), _llm_weekly_summary(),
        ]
        post_session_pipeline(self.session.id)

        # Backdate updated_at to 25 hours ago so the throttle window has passed
        stale_time = timezone.now() - timedelta(hours=25)
        WeeklySummary.objects.filter(child=self.child).update(updated_at=stale_time)

        session_b = Session.objects.create(
            child=self.child, status="ended", livekit_room_name=_unique_room(),
        )
        Message.objects.create(
            session=session_b, sender="child", content="Again", input_type="text",
        )
        post_session_pipeline(session_b.id)

        # Both pipelines should have fired a weekly-summary LLM call
        self.assertEqual(mock_llm.call_count, 6)

    @override_settings(
        REPORTING_GENERATE_QUESTS=False,
        REPORTING_GENERATE_WEEKLY_SUMMARY=True,
        REPORTING_WEEKLY_SUMMARY_THROTTLE_HOURS=0,
    )
    @patch("reporting.services.call_llm")
    def test_throttle_disabled_when_zero(self, mock_llm, _mock_close):
        mock_llm.side_effect = [
            _llm_report(), _llm_memory(), _llm_weekly_summary(),
            _llm_report(), _llm_memory(), _llm_weekly_summary(),
        ]
        post_session_pipeline(self.session.id)

        session_b = Session.objects.create(
            child=self.child, status="ended", livekit_room_name=_unique_room(),
        )
        Message.objects.create(
            session=session_b, sender="child", content="Again", input_type="text",
        )
        post_session_pipeline(session_b.id)

        # Both sessions should trigger weekly-summary LLM calls (throttle disabled)
        self.assertEqual(mock_llm.call_count, 6)


class LLMQuestDecisionTests(TestCase):
    """The quest LLM decides add/skip itself; mechanical gates are backstops."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="decision_child",
            password="testpass123",
            is_child=True,
        )
        self.child = ChildProfile.objects.create(
            user=self.user,
            nickname="DecKid",
            gender="male",
            birth_year=2015,
        )
        self.session = Session.objects.create(
            child=self.child,
            status="ended",
            livekit_room_name=_unique_room(),
        )
        self.report = SessionReport.objects.create(
            session=self.session,
            insight_summary="x",
            recommendations="",
        )

    def _add_open_ai_quests(self, n):
        for i in range(n):
            other_session = Session.objects.create(
                child=self.child, status="ended",
                livekit_room_name=_unique_room(),
            )
            other_report = SessionReport.objects.create(session=other_session)
            q = Quest.objects.create(
                title=f"Open quest {i}",
                is_ai_generated=True,
                session_report=other_report,
            )
            ChildQuestProgress.objects.create(
                child=self.child, quest=q, status="not_started",
            )

    @override_settings(
        REPORTING_GENERATE_QUESTS=True,
        REPORTING_QUESTS_MAX_OPEN=5,
        REPORTING_QUESTS_DAILY_CAP=False,
        REPORTING_QUESTS_SKIP_IF_PENDING=False,
    )
    def test_backstop_skips_llm_when_too_many_open(self):
        self._add_open_ai_quests(5)
        self.assertFalse(
            should_generate_quests_for_child(self.child, self.report)
        )

    @override_settings(
        REPORTING_GENERATE_QUESTS=True,
        REPORTING_QUESTS_MAX_OPEN=5,
        REPORTING_QUESTS_DAILY_CAP=False,
        REPORTING_QUESTS_SKIP_IF_PENDING=False,
    )
    def test_under_backstop_allows_llm_call(self):
        self._add_open_ai_quests(2)
        self.assertTrue(
            should_generate_quests_for_child(self.child, self.report)
        )

    @override_settings(
        REPORTING_GENERATE_QUESTS=True,
        REPORTING_QUESTS_MAX_OPEN=5,
        REPORTING_QUESTS_DAILY_CAP=False,
        REPORTING_QUESTS_SKIP_IF_PENDING=False,
    )
    @patch("reporting.services.call_llm")
    def test_llm_skip_decision_creates_nothing(self, mock_llm):
        from reporting.services import _generate_quests_for_report

        mock_llm.return_value = {
            "decision": "skip",
            "reason": "Child already has relevant open quests",
            "quests": [],
        }
        _generate_quests_for_report(self.report)
        self.assertEqual(
            Quest.objects.filter(session_report=self.report).count(), 0
        )
        # The decision LLM received the open-quest board in its prompt.
        user_prompt = mock_llm.call_args[0][1]
        self.assertIn("CURRENT OPEN QUESTS", user_prompt)

    @override_settings(
        REPORTING_GENERATE_QUESTS=True,
        REPORTING_QUESTS_MAX_OPEN=5,
        REPORTING_QUESTS_DAILY_CAP=False,
        REPORTING_QUESTS_SKIP_IF_PENDING=False,
    )
    @patch("reporting.services.call_llm")
    def test_llm_add_decision_creates_quests(self, mock_llm):
        from reporting.services import _generate_quests_for_report

        Value.objects.create(slug="honesty", name_en="Honesty", name_ar="الصدق")
        Value.objects.create(slug="prayer", name_en="Prayer", name_ar="الصلاة")
        self._add_open_ai_quests(1)
        mock_llm.return_value = {
            "decision": "add",
            "reason": "Session surfaced an honesty struggle with no open quest",
            "quests": [
                {
                    "title": "Tell Al-Sadiq about your day",
                    "description": "Share one true thing.",
                    "reward_points": 10,
                    "value_slug": "honesty",
                    "quest_type": "conversation",
                }
            ],
        }
        _generate_quests_for_report(self.report)
        created = Quest.objects.filter(session_report=self.report)
        self.assertEqual(created.count(), 1)
        quest = created.first()
        self.assertEqual(quest.quest_type, "conversation")
        self.assertEqual(quest.verification_method, "companion")
        self.assertEqual(quest.value.slug, "honesty")
        # Open-quest context and the full bank Value list (devotional included;
        # quests may follow a topic the child raised) went into the prompt.
        user_prompt = mock_llm.call_args[0][1]
        self.assertIn("Open quest 0", user_prompt)
        self.assertIn("- honesty: Honesty", user_prompt)
        self.assertIn("- prayer: Prayer", user_prompt)

    def _run_with_value_slug(self, mock_llm, slug):
        from reporting.services import _generate_quests_for_report

        mock_llm.return_value = {
            "decision": "add",
            "reason": "x",
            "quests": [
                {
                    "title": "Value quest",
                    "description": "d",
                    "reward_points": 10,
                    "value_slug": slug,
                    "quest_type": "conversation",
                }
            ],
        }
        _generate_quests_for_report(self.report)
        return Quest.objects.get(session_report=self.report)

    @override_settings(
        REPORTING_GENERATE_QUESTS=True,
        REPORTING_QUESTS_MAX_OPEN=5,
        REPORTING_QUESTS_DAILY_CAP=False,
        REPORTING_QUESTS_SKIP_IF_PENDING=False,
    )
    @patch("reporting.services.call_llm")
    def test_unknown_value_slug_is_rejected(self, mock_llm):
        Value.objects.create(slug="honesty", name_en="Honesty", name_ar="الصدق")
        before = MoralTheme.objects.count()
        quest = self._run_with_value_slug(mock_llm, "made-up-value")
        self.assertIsNone(quest.value)
        self.assertIsNone(quest.moral_theme)
        self.assertEqual(MoralTheme.objects.count(), before)

    @override_settings(
        REPORTING_GENERATE_QUESTS=True,
        REPORTING_QUESTS_MAX_OPEN=5,
        REPORTING_QUESTS_DAILY_CAP=False,
        REPORTING_QUESTS_SKIP_IF_PENDING=False,
    )
    @patch("reporting.services.call_llm")
    def test_value_slug_sets_value_and_bridges_existing_theme(self, mock_llm):
        value = Value.objects.create(slug="honesty", name_en="Honesty", name_ar="الصدق")
        theme = MoralTheme.objects.create(name="honesty")  # case differs on purpose
        before = MoralTheme.objects.count()
        quest = self._run_with_value_slug(mock_llm, "Honesty")
        self.assertEqual(quest.value, value)
        self.assertEqual(quest.moral_theme, theme)
        self.assertEqual(MoralTheme.objects.count(), before)

    @override_settings(
        REPORTING_GENERATE_QUESTS=True,
        REPORTING_QUESTS_MAX_OPEN=5,
        REPORTING_QUESTS_DAILY_CAP=False,
        REPORTING_QUESTS_SKIP_IF_PENDING=False,
    )
    @patch("reporting.services.call_llm")
    def test_value_without_theme_never_creates_one(self, mock_llm):
        value = Value.objects.create(slug="gratitude", name_en="Gratitude", name_ar="الشكر")
        quest = self._run_with_value_slug(mock_llm, "gratitude")
        self.assertEqual(quest.value, value)
        self.assertIsNone(quest.moral_theme)
        self.assertFalse(MoralTheme.objects.filter(name__iexact="gratitude").exists())

    @override_settings(
        REPORTING_GENERATE_QUESTS=True,
        REPORTING_QUESTS_MAX_OPEN=5,
        REPORTING_QUESTS_DAILY_CAP=False,
        REPORTING_QUESTS_SKIP_IF_PENDING=False,
    )
    @patch("reporting.services.call_llm")
    def test_missing_decision_defaults_to_add(self, mock_llm):
        """Old-format LLM responses (no decision key) still work."""
        from reporting.services import _generate_quests_for_report

        mock_llm.return_value = {
            "quests": [
                {
                    "title": "Help at home",
                    "description": "Help with one chore.",
                    "reward_points": 15,
                    "moral_theme": "Kindness",
                    "quest_type": "real_world",
                }
            ],
        }
        _generate_quests_for_report(self.report)
        self.assertEqual(
            Quest.objects.filter(session_report=self.report).count(), 1
        )


class ArabicNicknameTests(TestCase):
    """Lead decision 5 Oct: the companion is الصديق (from الصديق الصدوق), never صادق."""

    def test_parent_copy_uses_al_sadiq_nickname(self):
        from reporting.services import QUESTION_DEFAULT_LABEL, QUESTIONS_TITLE

        for text in (QUESTIONS_TITLE["ar"], QUESTION_DEFAULT_LABEL["ar"]):
            self.assertIn("الصديق", text)
            self.assertNotIn("صادق", text)
