"""Parent sources, questions-to-discuss and privacy (task 04). Synthetic data only."""
import json
import uuid
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from authentication.models import ChildProfile, ParentChildLink, ParentProfile
from content_safety.models import Alert
from conversation.models import Message, Session, TurnAudit
from reporting.models import SessionReport
from reporting.services import build_sources_snapshot, post_session_pipeline
from session_moral_context.models import (
    ContentItem, ServedReference, Value, ValueItem,
)

User = get_user_model()
MARKER = "CHILD-MARKER-9f3a1c"


def _item(**kw):
    base = dict(
        type="hadith", arabic_text="نص تجريبي", english_text="PLACEHOLDER TEXT 1",
        translation_name="Placeholder translation", book="Placeholder book",
        number="1", grade="sahih", grader="Placeholder grader",
        source_site="dorar.net", source_url="https://dorar.net/placeholder/1",
        content_level="A", verification_status="reviewed",
    )
    base.update(kw)
    return ContentItem.objects.create(**base)


class SourcesBase(TestCase):
    def setUp(self):
        cu = User.objects.create_user(username="src_child", password="x", is_child=True)
        self.child = ChildProfile.objects.create(
            user=cu, nickname="Kid", gender="male", birth_year=2015)
        pu = User.objects.create_user(username="src_parent", password="x", is_parent=True)
        self.parent = ParentProfile.objects.create(user=pu, name="P")
        ParentChildLink.objects.create(
            parent=self.parent, child=self.child, consent_status="approved")
        self.client = APIClient()
        self.client.force_authenticate(pu)
        self.value = Value.objects.create(
            slug="honesty", name_ar="الصدق", name_en="Honesty")

    def session(self):
        return Session.objects.create(
            child=self.child, livekit_room_name=f"r_{uuid.uuid4().hex[:12]}",
            status="ended")

    def report(self, session, **kw):
        return SessionReport.objects.create(session=session, **kw)

    def insights(self):
        r = self.client.get(f"/api/reporting/insights/{self.child.pk}/")
        self.assertEqual(r.status_code, 200)
        return r


class SnapshotTests(SourcesBase):
    def test_snapshot_from_served_references(self):
        item = _item()
        ValueItem.objects.create(value=self.value, item=item)
        s = self.session()
        ServedReference.objects.create(session=s, item=item, via="inject")
        ServedReference.objects.create(session=s, item=item, via="tool")
        snap = build_sources_snapshot(s)
        self.assertEqual(len(snap), 1)
        self.assertEqual(snap[0]["id"], item.pk)
        self.assertEqual(snap[0]["times_discussed"], 2)
        self.assertEqual(snap[0]["value_name"], "Honesty")
        self.assertEqual(snap[0]["kind"], "scripture")
        self.assertNotIn("child_explanation_en", snap[0])

    def test_snapshot_has_title_and_note(self):
        item = _item(
            type="faq", title_ar="عنوان", disagreement_note_ar="ملاحظة",
            content_level="C", grade="", grader="")
        s = self.session()
        ServedReference.objects.create(session=s, item=item, via="inject")
        self.report(s, sources_used=build_sources_snapshot(s))
        snap = build_sources_snapshot(s)[0]
        self.assertEqual((snap["title"], snap["disagreement_note"]), ("عنوان", "ملاحظة"))
        src = self.insights().json()["sources"][0]
        self.assertEqual((src["title"], src["disagreement_note"]), ("عنوان", "ملاحظة"))

    def test_old_snapshot_without_note_is_filled_from_the_live_item(self):
        item = _item(
            type="faq", title_en="Old title", disagreement_note_en="Old note",
            content_level="C", grade="", grader="")
        s = self.session()
        ServedReference.objects.create(session=s, item=item, via="inject")
        old = [{k: v for k, v in snap.items() if k not in ("title", "disagreement_note")}
               for snap in build_sources_snapshot(s)]
        self.report(s, sources_used=old)
        src = self.insights().json()["sources"][0]
        self.assertEqual((src["title"], src["disagreement_note"]), ("Old title", "Old note"))

    def test_snapshot_empty(self):
        self.assertEqual(build_sources_snapshot(self.session()), [])

    @patch("reporting.services.close_old_connections")
    @patch("reporting.services._generate_report_dict")
    def test_pipeline_stores_sources_not_from_llm(self, gen, _c):
        item = _item()
        s = self.session()
        s.ended_at = s.started_at
        s.save()
        ServedReference.objects.create(session=s, item=item, via="inject")
        gen.return_value = {
            "insight_summary": "x",
            "raw_llm_output": {},
            "sources_used": [{"id": 999}],  # must be overwritten from the DB
        }
        with patch("reporting.services._update_rolling_summary"), \
                patch("reporting.services._generate_quests_for_report"), \
                patch("reporting.services._update_weekly_summary"):
            post_session_pipeline(s.pk)
        self.assertEqual(
            [x["id"] for x in SessionReport.objects.get(session=s).sources_used],
            [item.pk])


class InsightsSourcesTests(SourcesBase):
    def test_dedupe_and_times_discussed(self):
        item = _item()
        for _ in range(2):
            s = self.session()
            ServedReference.objects.create(session=s, item=item, via="inject")
            self.report(s, sources_used=build_sources_snapshot(s))
        data = self.insights().json()
        self.assertEqual(len(data["sources"]), 1)
        self.assertEqual(data["sources"][0]["times_discussed"], 2)
        for f in ("kind", "translation_name", "translation_source_url",
                  "content_level", "verification_status", "source_url", "grade"):
            self.assertIn(f, data["sources"][0])

    def test_unverified_excluded(self):
        good = _item()
        bad = _item(number="2", verification_status="unverified")
        s = self.session()
        for it in (good, bad):
            ServedReference.objects.create(session=s, item=it, via="inject")
        self.report(s, sources_used=build_sources_snapshot(s))
        ids = [x["id"] for x in self.insights().json()["sources"]]
        self.assertEqual(ids, [good.pk])

    def test_item_downgraded_later_is_dropped(self):
        item = _item()
        s = self.session()
        ServedReference.objects.create(session=s, item=item, via="inject")
        self.report(s, sources_used=build_sources_snapshot(s))
        ContentItem.objects.filter(pk=item.pk).update(verification_status="unverified")
        self.assertEqual(self.insights().json()["sources"], [])

    def test_no_sources_report_works(self):
        self.report(self.session())
        data = self.insights().json()
        self.assertEqual(data["sources"], [])
        self.assertEqual(data["questions_to_discuss"], [])

    def test_labels_present(self):
        data = self.insights().json()
        self.assertIn("approved sources", data["trust_line"]["en"])
        self.assertIn("الذكاء الاصطناعي", data["trust_line"]["ar"])
        self.assertIn("may contain mistakes", data["summary_label"]["en"])
        self.assertTrue(data["summary_label"]["ar"])


class QuestionsTests(SourcesBase):
    def test_questions_grouped_and_safety_excluded(self):
        item = _item()
        ValueItem.objects.create(value=self.value, item=item)
        s = self.session()
        TurnAudit.objects.create(
            session=s, level="D", mode="REFER", served_item_ids=[item.pk])
        TurnAudit.objects.create(
            session=s, level="B", mode="DECLINE_NO_SOURCE", served_item_ids=[item.pk])
        TurnAudit.objects.create(session=s, level="A", mode="ANSWER")
        TurnAudit.objects.create(
            session=s, level="D", mode="REFER", served_item_ids=[item.pk], safety=True)
        qs = self.insights().json()["questions_to_discuss"]
        self.assertEqual(len(qs), 1)
        self.assertEqual(qs[0]["topic_en"], "Honesty")
        self.assertEqual(qs[0]["count"], 2)  # safety row not counted

    def test_safety_only_yields_nothing(self):
        s = self.session()
        TurnAudit.objects.create(session=s, level="D", mode="REFER", safety=True)
        self.assertEqual(self.insights().json()["questions_to_discuss"], [])

    def test_session_with_safety_alert_excluded(self):
        s = self.session()
        TurnAudit.objects.create(session=s, level="D", mode="REFER")
        Alert.objects.create(session=s, parent=self.parent, alert_type="safety")
        self.assertEqual(self.insights().json()["questions_to_discuss"], [])


class PrivacyTests(SourcesBase):
    def test_no_message_text_in_response(self):
        item = _item()
        s = self.session()
        Message.objects.create(
            session=s, sender="child", content=f"hello {MARKER}", input_type="text")
        ServedReference.objects.create(session=s, item=item, via="inject")
        TurnAudit.objects.create(session=s, level="D", mode="REFER", served_item_ids=[item.pk])
        self.report(s, sources_used=build_sources_snapshot(s))
        body = self.insights().content.decode()
        self.assertNotIn(MARKER, body)
        json.loads(body)


class NoParentNotifyTests(SourcesBase):
    PREFIX = "[no-parent-notify] "

    def _flagged_session(self):
        from content_safety.models import SafetyFlag
        s = self.session()
        s.ended_at = s.started_at
        s.save()
        m = Message.objects.create(
            session=s, sender="child", content=f"private {MARKER}", input_type="text")
        SafetyFlag.objects.create(
            message=m, flag_type="harmful", description=self.PREFIX + "rule_xyz")
        return s, m

    def _run(self, s):
        with patch("reporting.services.close_old_connections"), \
                patch("reporting.services.call_llm") as llm:
            llm.side_effect = AssertionError("LLM must not be called")
            post_session_pipeline(s.pk)

    def test_neutral_report_no_llm_keeps_sources_and_flagged_message(self):
        item = _item()
        s, m = self._flagged_session()
        ServedReference.objects.create(session=s, item=item, via="inject")
        Message.objects.create(session=s, sender="system", content="other", input_type="text")
        self._run(s)
        r = SessionReport.objects.get(session=s)
        self.assertTrue(r.raw_llm_output["neutral"])
        self.assertEqual(r.raw_llm_output["safety_notes"], [])
        self.assertNotIn(MARKER, json.dumps(r.raw_llm_output, ensure_ascii=False))
        self.assertNotIn("rule_xyz", r.insight_summary + json.dumps(r.raw_llm_output))
        self.assertIsNone(r.honesty_score)
        self.assertEqual([x["id"] for x in r.sources_used], [item.pk])
        self.assertTrue(Message.objects.filter(pk=m.pk).exists())  # staff retention
        self.assertEqual(Message.objects.filter(session=s).count(), 1)

    def test_excluded_from_memory_and_weekly_llm_input(self):
        from reporting.models import ChildSessionMemory
        from reporting.services import _build_reports_json
        s, _ = self._flagged_session()
        self._run(s)
        self.assertFalse(
            ChildSessionMemory.objects.filter(child=self.child, rolling_summary__gt="").exists())
        out = _build_reports_json([SessionReport.objects.get(session=s)])
        self.assertIn("A session took place.", out)
        self.assertNotIn("rule_xyz", out)

    def test_alert_endpoint_neutral_description(self):
        s, _ = self._flagged_session()
        Alert.objects.create(
            session=s, parent=self.parent, alert_type="safety",
            description="raw detail rule_xyz")
        body = self.client.get("/api/alerts/").content.decode()
        self.assertNotIn("rule_xyz", body)
        self.assertNotIn("raw detail", body)
        Alert.objects.create(
            session=self.session(), parent=self.parent, alert_type="safety",
            description=self.PREFIX + "rule_abc")
        self.assertNotIn("rule_abc", self.client.get("/api/alerts/").content.decode())


class SnapshotMarkerTests(TestCase):
    def test_snapshot_never_shows_raw_verse_marker(self):
        from reporting.services import _snapshot_item

        faq = _item(type="faq", arabic_text="نص {{verse:2:153}} تجريبي",
                    english_text="text {{verse:2:153}} here", book="", number="")
        snap = _snapshot_item(faq, [], 1)
        self.assertNotIn("{", snap["arabic_text"] + snap["english_text"])
        self.assertIn("2:153", snap["english_text"])
