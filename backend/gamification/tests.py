"""Tests for the gamification engine: points, streaks, badges, quest flows."""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from authentication.models import ChildProfile, ParentChildLink, ParentProfile
from conversation.models import QUIET_AUDIT_MODE, Session, TurnAudit
from reporting.models import SessionReport
from session_moral_context.models import MoralTheme, Value
from .models import (
    Badge,
    ChildBadge,
    ChildQuestProgress,
    ChildStreak,
    Level,
    Points,
    PointsEvent,
    Quest,
)
from .services import (
    _child_stat,
    award_points,
    complete_quest_progress,
    evaluate_badges,
    gamification_state,
    update_streak,
)

User = get_user_model()


def make_child(username="gam_child"):
    user = User.objects.create_user(
        username=username, password="testpass123", is_child=True,
    )
    return ChildProfile.objects.create(
        user=user, nickname=username.title(), gender="male", birth_year=2015,
    )


def make_linked_parent(child, username="gam_parent"):
    user = User.objects.create_user(
        username=username, password="testpass123", is_parent=True,
    )
    parent = ParentProfile.objects.create(user=user, name=username.title())
    ParentChildLink.objects.create(
        parent=parent, child=child, consent_status="approved",
    )
    return parent


class AwardPointsTests(TestCase):
    def setUp(self):
        self.child = make_child()

    def test_awards_points_and_writes_ledger(self):
        result = award_points(self.child, 10, reason="Honest moment", source="conversation")
        self.assertEqual(result["total_points"], 10)
        self.assertEqual(result["delta_applied"], 10)
        event = PointsEvent.objects.get(child=self.child)
        self.assertEqual(event.delta, 10)
        self.assertEqual(event.source, "conversation")

    def test_negative_delta_never_goes_below_zero(self):
        award_points(self.child, 5, source="conversation")
        result = award_points(self.child, -20, source="conversation")
        self.assertEqual(result["total_points"], 0)
        self.assertEqual(result["delta_applied"], -5)

    def test_zero_applied_delta_writes_no_ledger_row(self):
        award_points(self.child, -10, source="conversation")
        self.assertEqual(PointsEvent.objects.filter(child=self.child).count(), 0)

    def test_level_up_detection(self):
        # Seed migration provides level 2 at 50 points.
        result = award_points(self.child, 60, source="quest")
        self.assertTrue(result["leveled_up"])
        self.assertGreaterEqual(result["level_number"], 2)


class StreakTests(TestCase):
    def setUp(self):
        self.child = make_child("streak_child")

    def test_first_session_starts_streak_and_awards_bonus(self):
        result = update_streak(self.child)
        self.assertEqual(result["current_streak"], 1)
        self.assertTrue(result["extended"])
        self.assertTrue(
            PointsEvent.objects.filter(child=self.child, source="streak").exists()
        )

    def test_same_day_does_not_double_count(self):
        update_streak(self.child)
        result = update_streak(self.child)
        self.assertEqual(result["current_streak"], 1)
        self.assertFalse(result["extended"])
        self.assertEqual(
            PointsEvent.objects.filter(child=self.child, source="streak").count(), 1
        )

    def test_consecutive_day_extends(self):
        today = timezone.localdate()
        ChildStreak.objects.create(
            child=self.child,
            current_streak=3,
            longest_streak=3,
            last_active_date=today - timedelta(days=1),
        )
        result = update_streak(self.child)
        self.assertEqual(result["current_streak"], 4)
        self.assertEqual(result["longest_streak"], 4)

    def test_gap_resets_streak_but_keeps_longest(self):
        today = timezone.localdate()
        ChildStreak.objects.create(
            child=self.child,
            current_streak=5,
            longest_streak=5,
            last_active_date=today - timedelta(days=3),
        )
        result = update_streak(self.child)
        self.assertEqual(result["current_streak"], 1)
        self.assertEqual(result["longest_streak"], 5)


class BadgeEngineTests(TestCase):
    def setUp(self):
        self.child = make_child("badge_child")

    def test_streak_badge_awarded(self):
        ChildStreak.objects.create(
            child=self.child, current_streak=3, longest_streak=3,
            last_active_date=timezone.localdate(),
        )
        new = evaluate_badges(self.child)
        names = {b.name for b in new}
        self.assertIn("First Spark", names)   # 2-day requirement
        self.assertIn("Three-Day Glow", names)
        self.assertNotIn("Steadfast Week", names)

    def test_quest_badge_awarded_on_completion(self):
        quest = Quest.objects.create(
            title="Be kind", reward_points=10,
            quest_type="reflection", verification_method="self",
        )
        progress = ChildQuestProgress.objects.create(child=self.child, quest=quest)
        result = complete_quest_progress(progress, verified_by="child")
        self.assertEqual(result["points"]["total_points"], 10)
        self.assertIn("First Quest", {b.name for b in result["new_badges"]})
        progress.refresh_from_db()
        self.assertEqual(progress.status, "completed")
        self.assertEqual(progress.verified_by, "child")

    def test_badges_not_awarded_twice(self):
        ChildStreak.objects.create(
            child=self.child, current_streak=2, longest_streak=2,
            last_active_date=timezone.localdate(),
        )
        first = evaluate_badges(self.child)
        second = evaluate_badges(self.child)
        self.assertTrue(first)
        self.assertEqual(second, [])

    def _complete_value_quest(self, slug, title):
        value = Value.objects.get_or_create(
            slug=slug, defaults={"name_en": slug.title(), "name_ar": slug}
        )[0]
        quest = Quest.objects.create(
            title=title, reward_points=5, quest_type="reflection",
            verification_method="self", value=value,
        )
        progress = ChildQuestProgress.objects.create(child=self.child, quest=quest)
        return complete_quest_progress(progress, verified_by="child")

    def _values_badges(self):
        return set(
            ChildBadge.objects.filter(
                child=self.child, badge__requirement_type="values_practised"
            ).values_list("badge__name", flat=True)
        )

    def test_values_practised_counts_distinct_values(self):
        # Two quests on the same value = one value practised.
        first = self._complete_value_quest("honesty", "Tell the truth today")
        self.assertIn("First Value Practised", {b.name for b in first["new_badges"]})
        self._complete_value_quest("honesty", "Admit a mistake")
        self.assertEqual(_child_stat(self.child, "values_practised"), 1)
        self._complete_value_quest("kindness", "Help a sibling")
        self.assertEqual(_child_stat(self.child, "values_practised"), 2)

    def test_quest_without_value_does_not_count(self):
        quest = Quest.objects.create(title="No value", reward_points=5)
        progress = ChildQuestProgress.objects.create(child=self.child, quest=quest)
        result = complete_quest_progress(progress, verified_by="child")
        self.assertEqual(_child_stat(self.child, "values_practised"), 0)
        self.assertNotIn("First Value Practised", {b.name for b in result["new_badges"]})

    def test_values_badges_awarded_at_1_5_15(self):
        expected = {1: "First Value Practised", 5: "Five Values Practised",
                    15: "Fifteen Values Practised"}
        for n in range(1, 16):
            self._complete_value_quest(f"value-{n}", f"Quest {n}")
            earned = self._values_badges()
            self.assertEqual(
                earned, {name for k, name in expected.items() if k <= n}, n
            )

    def test_honesty_score_never_awards_values_badge(self):
        session = Session.objects.create(
            child=self.child, status="ended", livekit_room_name="legacy_room",
        )
        SessionReport.objects.create(
            session=session, insight_summary="S", recommendations="R",
            honesty_score=1.0,
        )
        evaluate_badges(self.child)
        self.assertEqual(self._values_badges(), set())


def _migration_0005():
    import importlib
    return importlib.import_module(
        "gamification.migrations.0005_quest_value_values_practised_badges"
    )


class ValuesPractisedMigrationTests(TestCase):
    """Data step of 0005: theme -> Value mapping and the badge track conversion."""

    OLD_NEW = [(old, new) for old, new, *_ in _migration_0005().VALUE_BADGES]

    @staticmethod
    def _forwards():
        from django.apps import apps
        _migration_0005().forwards(apps, None)

    @staticmethod
    def _backwards():
        from django.apps import apps
        _migration_0005().backwards(apps, None)

    def _themed_quest(self, theme_name):
        theme = MoralTheme.objects.get_or_create(name=theme_name)[0]
        return Quest.objects.create(title=theme_name, moral_theme=theme)

    def _complete_value_quests(self, child, slugs):
        for slug in slugs:
            value = Value.objects.get_or_create(
                slug=slug, defaults={"name_en": slug.title(), "name_ar": slug}
            )[0]
            quest = Quest.objects.create(title=slug, value=value)
            ChildQuestProgress.objects.create(child=child, quest=quest, status="completed")

    def _badge_names(self, child):
        return set(ChildBadge.objects.filter(child=child).values_list("badge__name", flat=True))

    def test_backwards_restores_honesty_track_and_forwards_again(self):
        self._backwards()
        old = Badge.objects.filter(requirement_type="honesty_sessions", category="honesty")
        self.assertEqual(
            set(old.values_list("name", flat=True)), {o for o, _ in self.OLD_NEW}
        )
        self.assertFalse(Badge.objects.filter(requirement_type="values_practised").exists())
        self.assertEqual(Level.objects.get(number=3).name, "Honest Helper")
        self._forwards()
        self.assertEqual(
            set(Badge.objects.filter(requirement_type="values_practised")
                .values_list("name", flat=True)),
            {n for _, n in self.OLD_NEW},
        )
        self.assertEqual(Level.objects.get(number=3).name, "Helpful Heart")

    def test_old_honesty_awards_are_dropped_and_recomputed(self):
        self._backwards()  # pre-0005 state: badges are the honesty track
        kept = make_child("kept_child")       # held "Truthful Heart", no value quests
        earner = make_child("earner_child")   # 5 distinct values -> two badges
        one = make_child("one_child")         # 2 quests, same value -> one badge
        truthful = Badge.objects.get(name="Truthful Heart")
        for child in (kept, earner, one):
            ChildBadge.objects.create(child=child, badge=truthful)
        self._complete_value_quests(earner, [f"v{i}" for i in range(5)])
        self._complete_value_quests(one, ["honesty", "honesty"])
        Quest.objects.create(title="no value")  # never counts

        self._forwards()

        self.assertEqual(self._badge_names(kept), set())
        self.assertEqual(
            self._badge_names(earner), {"First Value Practised", "Five Values Practised"}
        )
        self.assertEqual(self._badge_names(one), {"First Value Practised"})
        self.assertEqual(ChildBadge.objects.filter(badge__name="Truthful Heart").count(), 0)

    def test_rename_collision_merges_into_existing_badge(self):
        self._backwards()
        child = make_child("merge_child")
        old = Badge.objects.get(name="Truthful Heart")
        new = Badge.objects.create(name="First Value Practised", requirement_type="manual")
        ChildBadge.objects.create(child=child, badge=old)
        ChildBadge.objects.create(child=child, badge=new)
        self._complete_value_quests(child, ["patience"])

        self._forwards()

        self.assertFalse(Badge.objects.filter(name="Truthful Heart").exists())
        merged = Badge.objects.get(name="First Value Practised")
        self.assertEqual(merged.pk, new.pk)
        self.assertEqual(
            (merged.requirement_type, merged.category, merged.requirement_value),
            ("values_practised", "values", 1),
        )
        self.assertEqual(self._badge_names(child), {"First Value Practised"})

    def test_orphan_honesty_badge_becomes_manual_special(self):
        orphan = Badge.objects.create(
            name="Honesty Star", category="honesty", requirement_type="honesty_sessions",
            requirement_value=3,
        )
        self._forwards()
        orphan.refresh_from_db()
        self.assertEqual((orphan.requirement_type, orphan.category), ("manual", "special"))
        # Reverse leaves it alone (it is not one of the three), but keeps the three in sync.
        self._backwards()
        orphan.refresh_from_db()
        self.assertEqual(orphan.requirement_type, "manual")

    def test_backwards_skips_rename_when_old_name_taken(self):
        Badge.objects.create(name="Truthful Heart", requirement_type="manual")
        self._backwards()
        badge = Badge.objects.get(name="First Value Practised")  # name kept
        self.assertEqual(
            (badge.category, badge.requirement_type), ("honesty", "honesty_sessions")
        )
        self.assertEqual(Badge.objects.filter(name="Truthful Heart").count(), 1)

    def test_theme_names_map_to_values(self):
        honesty = Value.objects.create(slug="honesty", name_en="Honesty", name_ar="الصدق")
        kindness = Value.objects.create(slug="kindness", name_en="Kindness", name_ar="اللطف")
        quests = {
            name: self._themed_quest(name)
            for name in ("Honesty", "truthfulness", "الصدق", "kindness", "Unknown Theme")
        }
        self._forwards()
        for q in quests.values():
            q.refresh_from_db()
        self.assertEqual(quests["Honesty"].value, honesty)
        self.assertEqual(quests["truthfulness"].value, honesty)
        self.assertEqual(quests["الصدق"].value, honesty)
        self.assertEqual(quests["kindness"].value, kindness)
        self.assertIsNone(quests["Unknown Theme"].value)
        # Legacy FK is left in place.
        self.assertEqual(quests["Honesty"].moral_theme.name, "Honesty")

    def test_honesty_badges_became_values_track(self):
        self._forwards()  # idempotent on an already-migrated DB
        self.assertFalse(Badge.objects.filter(requirement_type="honesty_sessions").exists())
        self.assertFalse(Badge.objects.filter(category="honesty").exists())
        track = Badge.objects.filter(requirement_type="values_practised").order_by("sort_order")
        self.assertEqual(
            [(b.name, b.requirement_value, b.category) for b in track],
            [("First Value Practised", 1, "values"), ("Five Values Practised", 5, "values"),
             ("Fifteen Values Practised", 15, "values")],
        )
        for b in track:  # no verdict on the child's conversations
            for verdict in ("honest conversation", "truthful", "open and"):
                self.assertNotIn(verdict, b.description.lower())
        self.assertEqual(Level.objects.get(number=3).name, "Helpful Heart")


class SeedContentBackfillTests(TestCase):
    """Values seeded after 0005 ran: seed_content maps the legacy quests."""

    def test_seed_content_maps_legacy_quests(self):
        import json
        import tempfile
        from io import StringIO
        from pathlib import Path
        from django.core.management import call_command

        theme = MoralTheme.objects.create(name="Honesty")
        quest = Quest.objects.create(title="Tell the truth", moral_theme=theme)
        already = Quest.objects.create(
            title="Mapped", moral_theme=theme,
            value=Value.objects.create(slug="kindness", name_en="Kindness", name_ar="اللطف"),
        )
        self.assertIsNone(quest.value)

        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "items").mkdir()
            (Path(tmp) / "values.json").write_text(json.dumps(
                [{"slug": "honesty", "name_ar": "الصدق", "name_en": "Honesty"}]
            ))
            out = StringIO()
            call_command("seed_content", "--dir", tmp, stdout=out)

        self.assertIn("legacy quests mapped to values 1", out.getvalue())
        quest.refresh_from_db()
        already.refresh_from_db()
        self.assertEqual(quest.value.slug, "honesty")
        self.assertEqual(already.value.slug, "kindness")  # never overwritten


class QuestCompleteViewTests(TestCase):
    def setUp(self):
        self.child = make_child("quest_child")
        self.client = APIClient()
        self.client.force_authenticate(self.child.user)

    def _make_progress(self, quest_type, verification):
        quest = Quest.objects.create(
            title=f"{quest_type} quest", reward_points=15,
            quest_type=quest_type, verification_method=verification,
        )
        return ChildQuestProgress.objects.create(child=self.child, quest=quest)

    def test_self_verified_quest_completes_and_awards(self):
        progress = self._make_progress("reflection", "self")
        res = self.client.patch(f"/api/gamification/quests/{progress.id}/complete/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["quest"]["status"], "completed")
        self.assertEqual(res.data["points"]["total_points"], 15)
        self.assertTrue(
            PointsEvent.objects.filter(child=self.child, source="quest").exists()
        )

    def test_parent_verified_quest_goes_pending(self):
        progress = self._make_progress("real_world", "parent")
        res = self.client.patch(
            f"/api/gamification/quests/{progress.id}/complete/",
            {"proof_note": "I helped my brother with homework"},
            format="json",
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["quest"]["status"], "pending_verification")
        self.assertIsNone(res.data["points"])
        progress.refresh_from_db()
        self.assertEqual(progress.proof_note, "I helped my brother with homework")

    def test_companion_verified_quest_rejected_from_api(self):
        progress = self._make_progress("conversation", "companion")
        res = self.client.patch(f"/api/gamification/quests/{progress.id}/complete/")
        self.assertEqual(res.status_code, 400)
        progress.refresh_from_db()
        self.assertEqual(progress.status, "not_started")


class ParentVerificationTests(TestCase):
    def setUp(self):
        self.child = make_child("verify_child")
        self.parent = make_linked_parent(self.child, "verify_parent")
        quest = Quest.objects.create(
            title="Tidy your room", reward_points=20,
            quest_type="real_world", verification_method="parent",
        )
        self.progress = ChildQuestProgress.objects.create(
            child=self.child, quest=quest, status="pending_verification",
            proof_note="Done before dinner",
        )
        self.client = APIClient()
        self.client.force_authenticate(self.parent.user)

    def test_parent_sees_pending_quests(self):
        res = self.client.get(
            f"/api/gamification/parent/children/{self.child.id}/quests/",
            {"status": "pending_verification"},
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["proof_note"], "Done before dinner")

    def test_approve_completes_and_awards(self):
        res = self.client.patch(
            f"/api/gamification/parent/quests/{self.progress.id}/verify/",
            {"action": "approve"},
            format="json",
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["quest"]["status"], "completed")
        self.assertEqual(res.data["points"]["total_points"], 20)
        self.progress.refresh_from_db()
        self.assertEqual(self.progress.verified_by, "parent")

    def test_reject_returns_to_in_progress(self):
        res = self.client.patch(
            f"/api/gamification/parent/quests/{self.progress.id}/verify/",
            {"action": "reject"},
            format="json",
        )
        self.assertEqual(res.status_code, 200)
        self.progress.refresh_from_db()
        self.assertEqual(self.progress.status, "in_progress")
        self.assertEqual(Points.objects.filter(child=self.child).count(), 0)

    def _stale(self):
        return ChildQuestProgress.objects.select_related("quest", "child").get(pk=self.progress.pk)

    def _verify_with_stale_row(self, action, stale):
        """The view loaded the row as pending_verification; by the time it writes, the DB differs."""
        from unittest import mock
        real = ChildQuestProgress.objects

        class StaleManager:
            def select_related(self, *args):
                return mock.Mock(get=mock.Mock(return_value=stale))

            def __getattr__(self, name):
                return getattr(real, name)

        manager = StaleManager()
        fake_model = mock.Mock(objects=manager, DoesNotExist=ChildQuestProgress.DoesNotExist)
        with mock.patch("gamification.views.ChildQuestProgress", fake_model):
            return self.client.patch(
                f"/api/gamification/parent/quests/{self.progress.id}/verify/",
                {"action": action}, format="json",
            )

    def test_reject_after_approve_does_not_uncomplete_a_paid_quest(self):
        stale = self._stale()
        complete_quest_progress(self.progress, verified_by="parent")  # the other parent approved
        self.assertEqual(Points.objects.get(child=self.child).total, 20)
        res = self._verify_with_stale_row("reject", stale)
        self.assertEqual(res.status_code, 400)
        self.progress.refresh_from_db()
        self.assertEqual(self.progress.status, "completed")
        # a second approve cannot be paid again either
        res = self.client.patch(
            f"/api/gamification/parent/quests/{self.progress.id}/verify/",
            {"action": "approve"}, format="json",
        )
        self.assertEqual(res.status_code, 400)
        self.assertEqual(Points.objects.get(child=self.child).total, 20)

    def test_approve_after_reject_pays_nothing(self):
        stale = self._stale()
        ChildQuestProgress.objects.filter(pk=self.progress.pk).update(status="in_progress")
        res = self._verify_with_stale_row("approve", stale)
        self.assertEqual(res.status_code, 400)
        self.progress.refresh_from_db()
        self.assertEqual(self.progress.status, "in_progress")
        self.assertFalse(Points.objects.filter(child=self.child).exists())

    def test_child_and_companion_completion_still_work_from_in_progress(self):
        for verified_by in ("child", "companion"):
            with self.subTest(verified_by=verified_by):
                ChildQuestProgress.objects.filter(pk=self.progress.pk).update(status="in_progress")
                self.progress.refresh_from_db()
                result = complete_quest_progress(self.progress, verified_by=verified_by)
                self.assertIsNotNone(result["points"])

    def test_unlinked_parent_forbidden(self):
        other_user = User.objects.create_user(
            username="other_parent", password="testpass123", is_parent=True,
        )
        ParentProfile.objects.create(user=other_user, name="Other")
        client = APIClient()
        client.force_authenticate(other_user)
        res = client.patch(
            f"/api/gamification/parent/quests/{self.progress.id}/verify/",
            {"action": "approve"},
            format="json",
        )
        self.assertEqual(res.status_code, 403)


class BadgeListViewTests(TestCase):
    def setUp(self):
        self.child = make_child("badgelist_child")
        self.client = APIClient()
        self.client.force_authenticate(self.child.user)

    def test_badges_include_category_and_progress(self):
        res = self.client.get("/api/gamification/badges/")
        self.assertEqual(res.status_code, 200)
        self.assertGreater(len(res.data), 0)
        row = res.data[0]
        for key in ("category", "requirement_type", "requirement_value", "progress_current"):
            self.assertIn(key, row)
        categories = {r["category"] for r in res.data}
        self.assertTrue({"streak", "values", "quest", "level"} <= categories)


class LevelViewTests(TestCase):
    def setUp(self):
        self.child = make_child("level_child")
        self.client = APIClient()
        self.client.force_authenticate(self.child.user)

    def test_level_includes_streak(self):
        ChildStreak.objects.create(
            child=self.child, current_streak=4, longest_streak=6,
            last_active_date=timezone.localdate(),
        )
        res = self.client.get("/api/gamification/level/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["current_streak"], 4)


class ParentDashboardTests(TestCase):
    def setUp(self):
        self.child = make_child("dash_child")
        self.parent = make_linked_parent(self.child, "dash_parent")
        self.client = APIClient()
        self.client.force_authenticate(self.parent.user)

    def test_dashboard_shape(self):
        now = timezone.now()
        session = Session.objects.create(
            child=self.child, status="ended",
            livekit_room_name="dash_room_1",
        )
        Session.objects.filter(pk=session.pk).update(
            started_at=now - timedelta(minutes=10), ended_at=now,
        )
        award_points(self.child, 25, reason="test", source="conversation")

        res = self.client.get(f"/api/reporting/dashboard/{self.child.id}/")
        self.assertEqual(res.status_code, 200)
        for key in (
            "sessions", "streak", "level", "quests", "badges",
            "points_timeline", "recent_activity",
        ):
            self.assertIn(key, res.data)
        self.assertEqual(res.data["sessions"]["total"], 1)
        self.assertEqual(len(res.data["points_timeline"]), 14)
        self.assertEqual(res.data["recent_activity"][0]["delta"], 25)

    def test_parent_never_sees_the_raw_llm_reason(self):
        marker = "ZZ-MARKER-DISCLOSURE"
        session = Session.objects.create(child=self.child, livekit_room_name="dash_room_2")
        award_points(self.child, 10, reason=marker, source="conversation", session=session)
        award_points(self.child, 5, reason=marker, source="conversation")
        award_points(self.child, 7, reason=marker, source="adjustment")
        res = self.client.get(f"/api/reporting/dashboard/{self.child.id}/")
        self.assertNotIn(marker, res.content.decode())
        by_delta = {e["delta"]: e for e in res.data["recent_activity"]}
        self.assertIn("/", by_delta[5]["reason"])
        self.assertEqual(set(by_delta[5]), {"delta", "reason", "source", "created_at"})
        # a harm-flagged session shows no wording at all
        TurnAudit.objects.create(session=session, level="", mode=QUIET_AUDIT_MODE, safety=True)
        res = self.client.get(f"/api/reporting/dashboard/{self.child.id}/")
        self.assertNotIn(marker, res.content.decode())
        by_delta = {e["delta"]: e for e in res.data["recent_activity"]}
        self.assertEqual(by_delta[10]["reason"], "")
        self.assertNotEqual(by_delta[5]["reason"], "")

    def test_dashboard_forbidden_for_unlinked(self):
        other_child = make_child("dash_child_2")
        res = self.client.get(f"/api/reporting/dashboard/{other_child.id}/")
        self.assertEqual(res.status_code, 403)


class GamificationStateTests(TestCase):
    def test_state_for_child_with_no_rows(self):
        child = make_child("state_child")
        state = gamification_state(child)
        self.assertEqual(state["total_points"], 0)
        self.assertEqual(state["current_streak"], 0)
        self.assertIn("level_number", state)
