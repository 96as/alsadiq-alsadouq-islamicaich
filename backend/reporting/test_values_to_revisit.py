"""Plan s11 decision 8: no honesty grading. The session report carries a neutral
``values_to_revisit`` list (Value slugs from the bank). Synthetic data, LLM mocked."""
import json
from unittest.mock import patch

from django.test import SimpleTestCase, TestCase, override_settings

from conversation.models import Message, Session
from gamification.models import Quest
from reporting import prompts
from reporting.models import SessionReport
from reporting.services import (
    DEVOTIONAL_VALUE_SLUGS,
    _build_reports_json,
    _generate_quests_for_report,
    _value_choices,
    clean_values_to_revisit,
    post_session_pipeline,
)
from reporting.tests import _create_parent_child_pair, _unique_room
from session_moral_context.models import Value

ALL_PROMPTS = {
    "session": prompts.SESSION_REPORT_SYSTEM + prompts.SESSION_REPORT_USER_TEMPLATE,
    "memory": prompts.ROLLING_SUMMARY_SYSTEM,
    "quests": prompts.QUEST_GENERATION_SYSTEM,
    "weekly": prompts.WEEKLY_SUMMARY_SYSTEM,
}
SLUGS = ["honesty", "patience", "gratitude", "kindness"]


class NoHonestyGradingPromptTests(SimpleTestCase):
    def test_no_honesty_scoring_instruction_in_any_prompt(self):
        for name, text in ALL_PROMPTS.items():
            low = text.lower()
            for term in ("honesty_score", "honesty_indicators", "honesty score", "dishonest", "penali"):
                self.assertNotIn(term, low, f"{name}: {term}")

    def test_session_contract_has_values_to_revisit_and_is_topic_only(self):
        sys = prompts.SESSION_REPORT_SYSTEM
        self.assertIn('"values_to_revisit"', sys)
        self.assertIn("never a judgment of the child", sys)
        self.assertIn("Value list", sys)
        self.assertIn("{values_list}", prompts.SESSION_REPORT_USER_TEMPLATE)

    def test_downstream_prompts_know_values_to_revisit(self):
        for text in (prompts.QUEST_GENERATION_SYSTEM, prompts.WEEKLY_SUMMARY_SYSTEM,
                     prompts.ROLLING_SUMMARY_SYSTEM):
            self.assertIn("values_to_revisit", text)


class CleanValuesTests(SimpleTestCase):
    def test_unknown_dropped_deduped_capped_normalised(self):
        out = clean_values_to_revisit(
            ["made-up", " Patience ", "patience", 7, None, "honesty", "gratitude", "kindness"],
            set(SLUGS),
        )
        self.assertEqual(out, ["patience", "honesty", "gratitude"])

    def test_non_list_gives_empty(self):
        for bad in (None, "patience", {"patience": 1}, 3):
            self.assertEqual(clean_values_to_revisit(bad, set(SLUGS)), [])


class _Base(TestCase):
    def setUp(self):
        for i, slug in enumerate(SLUGS):
            Value.objects.create(slug=slug, name_en=slug.title(), name_ar=slug, order=i)
        self.child, self.parent, _ = _create_parent_child_pair("v2r_child", "v2r_parent")
        self.session = Session.objects.create(
            child=self.child, status="ended", livekit_room_name=_unique_room())
        Message.objects.create(
            session=self.session, sender="child", content="Hello", input_type="text")


@patch("reporting.services.close_old_connections")
class ReportPipelineValuesTests(_Base):
    LLM_REPORT = {
        "summary": "S", "recommendations": "R",
        "values_to_revisit": ["patience", "made-up", "honesty", "patience", "gratitude", "kindness"],
        # a stale / misbehaving model still answering the old contract
        "honesty_score": 0.0, "honesty_indicators": "avoided the question",
    }

    def _dispatch(self, calls):
        def fake(system, user):
            calls[system] = user
            if system == prompts.SESSION_REPORT_SYSTEM:
                return dict(self.LLM_REPORT)
            if system == prompts.ROLLING_SUMMARY_SYSTEM:
                return {"rolling_summary": "Memory line"}
            if system == prompts.QUEST_GENERATION_SYSTEM:
                return {"decision": "skip", "reason": "x", "quests": []}
            return {"summary": "Weekly.", "suggested_topics": ["a", "b", "c"]}
        return fake

    @override_settings(
        REPORTING_GENERATE_QUESTS=True, REPORTING_QUESTS_MAX_OPEN=5,
        REPORTING_QUESTS_DAILY_CAP=False, REPORTING_QUESTS_SKIP_IF_PENDING=False,
        REPORTING_GENERATE_WEEKLY_SUMMARY=True, REPORTING_WEEKLY_SUMMARY_THROTTLE_HOURS=0,
    )
    def test_stores_values_validated_and_never_honesty(self, _close):
        calls = {}
        with patch("reporting.services.call_llm", side_effect=self._dispatch(calls)):
            post_session_pipeline(self.session.id)

        r = SessionReport.objects.get(session=self.session)
        self.assertEqual(r.raw_llm_output["values_to_revisit"], ["patience", "honesty", "gratitude"])
        self.assertIsNone(r.honesty_score)
        for key in ("honesty_score", "honesty_indicators"):
            self.assertNotIn(key, r.raw_llm_output)

        # The bank's slugs + English names are given to the report LLM.
        report_prompt = calls[prompts.SESSION_REPORT_SYSTEM]
        for slug in SLUGS:
            self.assertIn(f"- {slug}: {slug.title()}", report_prompt)

        # Every downstream LLM input carries values_to_revisit and no honesty score/indicators.
        for system in (prompts.ROLLING_SUMMARY_SYSTEM, prompts.QUEST_GENERATION_SYSTEM,
                       prompts.WEEKLY_SUMMARY_SYSTEM):
            user = calls[system]
            self.assertIn("values_to_revisit", user)
            self.assertIn("patience", user)
            self.assertNotIn("honesty_score", user)
            self.assertNotIn("honesty_indicators", user)
            self.assertNotIn("made-up", user)

    @override_settings(
        REPORTING_GENERATE_QUESTS=False, REPORTING_GENERATE_WEEKLY_SUMMARY=False)
    def test_missing_values_key_gives_empty_list(self, _close):
        with patch("reporting.services.call_llm",
                   side_effect=[{"summary": "S", "recommendations": "R"}, {"rolling_summary": "m"}]):
            post_session_pipeline(self.session.id)
        r = SessionReport.objects.get(session=self.session)
        self.assertEqual(r.raw_llm_output["values_to_revisit"], [])
        self.assertIsNone(r.honesty_score)


class LegacyRowsNotExposedTests(_Base):
    """Old rows may still hold honesty_score / honesty_indicators: never passed on."""

    def _legacy_report(self):
        return SessionReport.objects.create(
            session=self.session, insight_summary="S", recommendations="R",
            honesty_score=0.5,
            raw_llm_output={
                "summary": "S", "themes_discussed": ["school"],
                "values_to_revisit": ["kindness"],
                "honesty_score": 0.5, "honesty_indicators": "mixed",
            },
        )

    def test_weekly_items_use_values_not_score(self):
        items = json.loads(_build_reports_json([self._legacy_report()]))
        self.assertEqual(items[0]["values_to_revisit"], ["kindness"])
        self.assertNotIn("honesty_score", items[0])
        self.assertNotIn("honesty", json.dumps(items))

    @override_settings(
        REPORTING_GENERATE_QUESTS=True, REPORTING_QUESTS_MAX_OPEN=5,
        REPORTING_QUESTS_DAILY_CAP=False, REPORTING_QUESTS_SKIP_IF_PENDING=False)
    def test_quest_input_uses_values_not_score(self):
        report = self._legacy_report()
        with patch("reporting.services.call_llm",
                   return_value={"decision": "skip", "quests": []}) as llm:
            _generate_quests_for_report(report)
        user = llm.call_args[0][1]
        self.assertIn('"values_to_revisit"', user)
        self.assertIn("kindness", user)
        for leak in ("honesty_score", "honesty_indicators", "mixed"):
            self.assertNotIn(leak, user)
        self.assertFalse(Quest.objects.filter(session_report=report).exists())


class DevotionalValuesTests(_Base):
    """Devotional values are never offered for values_to_revisit (a parent summary
    must not read as a judgment of religious practice); quests still see them."""

    def setUp(self):
        super().setUp()
        for i, slug in enumerate(sorted(DEVOTIONAL_VALUE_SLUGS), start=100):
            Value.objects.create(slug=slug, name_en=slug.title(), name_ar=slug, order=i)

    def test_value_choices_exclude_devotional_by_default(self):
        self.assertEqual(set(_value_choices()), set(SLUGS))
        self.assertEqual(
            set(_value_choices(include_devotional=True)), set(SLUGS) | DEVOTIONAL_VALUE_SLUGS
        )

    @override_settings(
        REPORTING_GENERATE_QUESTS=True, REPORTING_QUESTS_MAX_OPEN=5,
        REPORTING_QUESTS_DAILY_CAP=False, REPORTING_QUESTS_SKIP_IF_PENDING=False,
        REPORTING_GENERATE_WEEKLY_SUMMARY=False,
    )
    @patch("reporting.services.close_old_connections")
    def test_report_prompt_omits_devotional_and_drops_them_from_output(self, _close):
        calls = {}

        def fake(system, user):
            calls[system] = user
            if system == prompts.SESSION_REPORT_SYSTEM:
                return {"summary": "S", "recommendations": "R",
                        "values_to_revisit": ["prayer", "patience"]}
            if system == prompts.ROLLING_SUMMARY_SYSTEM:
                return {"rolling_summary": "m"}
            return {"decision": "skip", "reason": "x", "quests": []}

        with patch("reporting.services.call_llm", side_effect=fake):
            post_session_pipeline(self.session.id)

        report_prompt = calls[prompts.SESSION_REPORT_SYSTEM]
        quest_prompt = calls[prompts.QUEST_GENERATION_SYSTEM]
        for slug in DEVOTIONAL_VALUE_SLUGS:
            self.assertNotIn(f"- {slug}:", report_prompt)
            self.assertIn(f"- {slug}:", quest_prompt)
        r = SessionReport.objects.get(session=self.session)
        self.assertEqual(r.raw_llm_output["values_to_revisit"], ["patience"])
