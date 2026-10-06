"""Values counts, verification rules and parent privacy. Synthetic data only."""
from datetime import datetime, time, timedelta
import uuid
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from authentication.models import ChildProfile, ParentChildLink, ParentProfile
from conversation.models import Message, Session
from gamification.models import ChildQuestProgress, Quest
from reporting.models import SessionReport
from reporting.services import _snapshot_item, _week_start_today
from reporting.values_week import values_this_week
from session_moral_context.models import ContentItem, Value

MARKER = "CHILD-MARKER-9f3a1c"


class ValuesWeekTests(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_user(username="values_child", is_child=True)
        self.child = ChildProfile.objects.create(
            user=user, nickname="Kid", gender="male", birth_year=2015)
        parent_user = get_user_model().objects.create_user(
            username="values_parent", is_parent=True)
        parent = ParentProfile.objects.create(user=parent_user, name="P")
        ParentChildLink.objects.create(
            parent=parent, child=self.child, consent_status="approved")
        self.client = APIClient()
        self.client.force_authenticate(parent_user)
        self.kindness = Value.objects.create(
            slug="kindness", name_en="Kindness", name_ar="الرفق")
        self.patience = Value.objects.create(
            slug="patience", name_en="Patience", name_ar="الصبر")
        self.sharing = Value.objects.create(
            slug="sharing", name_en="Sharing", name_ar="المشاركة")
        self.week_start = _week_start_today()
        self.monday = timezone.make_aware(datetime.combine(self.week_start, time.min))

    def report(self, **kwargs):
        session = Session.objects.create(
            child=self.child, livekit_room_name=f"values_{uuid.uuid4().hex}", status="ended")
        return SessionReport.objects.create(session=session, **kwargs)

    def snapshot(self, values, times=1, status="reviewed", **item_kwargs):
        item = ContentItem.objects.create(
            type=item_kwargs.pop("type", "term"), verification_status=status, **item_kwargs)
        return _snapshot_item(item, [v.name_en for v in values], times)

    def quest(self, value, **kwargs):
        quest = Quest.objects.create(title="Synthetic quest", value=value)
        data = {"status": "completed", "completed_at": self.monday}
        data.update(kwargs)
        return ChildQuestProgress.objects.create(child=self.child, quest=quest, **data)

    def insights(self):
        response = self.client.get(f"/api/reporting/insights/{self.child.pk}/")
        self.assertEqual(response.status_code, 200)
        return response

    def test_two_sessions_three_values_and_all_count_sources(self):
        self.report(
            sources_used=[self.snapshot([self.kindness, self.patience], times=2)],
            raw_llm_output={"values_to_revisit": ["sharing", "kindness", "kindness"]})
        self.report(
            sources_used=[self.snapshot([self.kindness])],
            raw_llm_output={"values_to_revisit": ["patience"]})
        self.quest(self.sharing)
        self.assertEqual(self.insights().json()["values_this_week"], [
            {"slug": "kindness", "name_en": "Kindness", "name_ar": "الرفق", "count": 4},
            {"slug": "patience", "name_en": "Patience", "name_ar": "الصبر", "count": 3},
            {"slug": "sharing", "name_en": "Sharing", "name_ar": "المشاركة", "count": 2},
        ])

    def test_empty_and_fixed_bilingual_label_without_llm(self):
        with patch("reporting.services.call_llm", side_effect=AssertionError("No LLM")):
            data = self.insights().json()
        self.assertEqual(data["values_this_week"], [])
        self.assertEqual(data["labels"]["values_this_week"], {
            "en": "Values this week", "ar": "قيم هذا الأسبوع"})
        self.report()
        self.assertEqual(values_this_week(self.child), [])

    def test_unverified_snapshot_never_counted_even_after_review(self):
        snapshot = self.snapshot([self.kindness], status="unverified")
        ContentItem.objects.filter(pk=snapshot["id"]).update(verification_status="reviewed")
        self.report(sources_used=[snapshot])
        self.assertEqual(values_this_week(self.child), [])
        self.report(sources_used=[dict(snapshot, verification_status="reviewed")])
        self.assertEqual(values_this_week(self.child)[0]["count"], 1)

    def test_live_unverified_drops_reviewed_snapshot(self):
        snapshot = self.snapshot([self.kindness])
        self.report(sources_used=[snapshot])
        ContentItem.objects.filter(pk=snapshot["id"]).update(verification_status="unverified")
        self.assertEqual(values_this_week(self.child), [])

    def test_missing_reviewed_survives_but_missing_seeded_drops(self):
        reviewed = self.snapshot([self.kindness])
        seeded = self.snapshot([self.sharing], status="seeded", type="verse", surah=1, ayah=1)
        self.report(sources_used=[reviewed, seeded])
        ContentItem.objects.filter(pk__in=[reviewed["id"], seeded["id"]]).delete()
        self.assertEqual([row["slug"] for row in values_this_week(self.child)], ["kindness"])

    def test_seeded_snapshot_requires_current_servable_item(self):
        self.report(sources_used=[
            self.snapshot([self.kindness], status="seeded", type="verse", surah=1, ayah=1),
            self.snapshot([self.sharing], status="seeded"),
        ])
        self.assertEqual([row["slug"] for row in values_this_week(self.child)], ["kindness"])

    def test_unknown_names_and_slugs_ignored_and_ties_sorted_by_slug(self):
        snapshot = self.snapshot([self.sharing, self.kindness])
        snapshot["value_names"] += ["Unknown value", "Kindness"]
        # value_name is the legacy duplicate of the first value_names entry.
        self.report(sources_used=[snapshot], raw_llm_output={"values_to_revisit": ["unknown"]})
        self.assertEqual([(r["slug"], r["count"]) for r in values_this_week(self.child)], [
            ("kindness", 1), ("sharing", 1)])

    def test_week_and_child_scope_and_only_dated_completed_quests(self):
        old = self.report(raw_llm_output={"values_to_revisit": ["kindness"]})
        Session.objects.filter(pk=old.session_id).update(started_at=self.monday - timedelta(seconds=1))
        current = self.report(raw_llm_output={"values_to_revisit": ["patience"]})
        Session.objects.filter(pk=current.session_id).update(started_at=self.monday)
        self.quest(self.sharing)
        self.quest(self.kindness, completed_at=self.monday - timedelta(seconds=1))
        self.quest(self.kindness, status="in_progress")
        self.quest(self.kindness, completed_at=None)
        self.quest(None)
        other_user = get_user_model().objects.create_user(username="other_values", is_child=True)
        other = ChildProfile.objects.create(
            user=other_user, nickname="Other", gender="female", birth_year=2015)
        other_report = self.report(raw_llm_output={"values_to_revisit": ["kindness"]})
        Session.objects.filter(pk=other_report.session_id).update(child=other)
        other_progress = self.quest(self.kindness)
        ChildQuestProgress.objects.filter(pk=other_progress.pk).update(child=other)
        self.assertEqual([(r["slug"], r["count"]) for r in values_this_week(self.child)], [
            ("patience", 1), ("sharing", 1)])

    def test_malformed_json_does_not_become_values_or_raise(self):
        snapshot = self.snapshot([self.kindness])
        self.report(sources_used=[None, {}, {"id": []}, dict(snapshot, value_names="Kindness"),
                                  dict(snapshot, times_discussed="2")], raw_llm_output=[])
        self.report(sources_used={}, raw_llm_output={"values_to_revisit": "kindness"})
        self.report(raw_llm_output={"values_to_revisit": [None, {}, ["kindness"]]})
        self.assertEqual(values_this_week(self.child), [])

    def test_json_response_contains_no_child_or_generated_wording(self):
        report = self.report(
            sources_used=[self.snapshot([self.kindness])],
            insight_summary=MARKER, recommendations=MARKER,
            raw_llm_output={"values_to_revisit": ["patience", MARKER], "message": MARKER})
        Message.objects.create(
            session=report.session, sender="child", content=f"hello {MARKER}", input_type="text")
        progress = self.quest(self.sharing, proof_note=MARKER)
        Quest.objects.filter(pk=progress.quest_id).update(title=MARKER, description=MARKER)
        response = self.insights()
        self.assertNotIn(MARKER, response.content.decode())
        self.assertEqual(len(response.json()["values_this_week"]), 3)
