"""Legacy scores stay hidden; bank value metadata is read-only."""
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.test import RequestFactory, TestCase
from rest_framework.test import APIClient

from authentication.models import ChildProfile
from conversation.models import Session
from reporting.models import SessionReport
from session_moral_context.models import Value
from superadmin.serializers import SessionReportSerializer

User = get_user_model()


class SessionReportBase(TestCase):
    def setUp(self):
        admin = User.objects.create_superuser(
            username="sa_admin", password="testpass123", email="sa@example.com",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=admin)
        child_user = User.objects.create_user(
            username="sa_child", password="testpass123", is_child=True,
        )
        child = ChildProfile.objects.create(
            user=child_user, nickname="Sa Child", gender="male", birth_year=2015,
        )
        self.session = Session.objects.create(
            child=child, status="ended", livekit_room_name="sa_room",
        )


class SessionReportWritesAreRefusedTests(SessionReportBase):
    def test_patch_and_create_are_405_and_change_nothing(self):
        report = SessionReport.objects.create(
            session=self.session, insight_summary="S", recommendations="R",
        )
        res = self.client.patch(
            f"/superadmin/api/session-reports/{report.id}/",
            {"honesty_score": 1.0, "insight_summary": "Updated"},
            format="json",
        )
        self.assertEqual(res.status_code, 405)
        report.refresh_from_db()
        self.assertIsNone(report.honesty_score)
        self.assertEqual(report.insight_summary, "S")
        res = self.client.post(
            "/superadmin/api/session-reports/",
            {"session": self.session.id, "honesty_score": 0.5, "insight_summary": "S"},
            format="json",
        )
        self.assertEqual(res.status_code, 405)
        self.assertEqual(SessionReport.objects.count(), 1)


class SessionReportValuesReadOnlyTests(SessionReportBase):
    def setUp(self):
        super().setUp()
        for slug in ("kindness", "patience", "sharing", "gratitude", "prayer"):
            Value.objects.create(slug=slug, name_en=slug.title(), name_ar="قيمة تجريبية")

    def test_get_detail_and_list_hide_score_and_show_only_bank_slugs(self):
        marker = "CHILD-MARKER-9f3a1c"
        report = SessionReport.objects.create(
            session=self.session, honesty_score=0.8,
            raw_llm_output={"values_to_revisit": [" Kindness ", marker, "prayer", "kindness"]})
        for path in (f"/superadmin/api/session-reports/{report.pk}/", "/superadmin/api/session-reports/"):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                data = response.data
                if "results" in data:
                    data = data["results"][0]
                elif isinstance(data, list):
                    data = data[0]
                self.assertNotIn("honesty_score", data)
                self.assertEqual(data["values_to_revisit"], ["kindness"])
                self.assertNotIn(marker, data["values_to_revisit"])

    def test_metadata_is_normalized_deduped_capped_and_robust_to_malformed_json(self):
        model_admin = admin.site._registry[SessionReport]
        cases = [
            (None, []), ([], []), ("child text", []),
            ({"values_to_revisit": "kindness"}, []),
            ({"values_to_revisit": [None, {}, ["kindness"], "unknown", "prayer"]}, []),
            ({"values_to_revisit": [" Kindness ", "kindness", "patience", "sharing", "gratitude"]},
             ["kindness", "patience", "sharing"]),
        ]
        for raw, expected in cases:
            with self.subTest(raw=raw):
                report = SessionReport(session=self.session, raw_llm_output=raw)
                self.assertEqual(SessionReportSerializer(report).data["values_to_revisit"], expected)
                self.assertEqual(model_admin.values_to_revisit(report), expected)
        self.assertEqual(model_admin.values_to_revisit(None), [])

    def test_admin_exposes_values_readonly_and_excludes_legacy_score_from_form(self):
        model_admin = admin.site._registry[SessionReport]
        request = RequestFactory().get("/")
        request.user = User.objects.get(username="sa_admin")
        form = model_admin.get_form(request)
        self.assertIn("values_to_revisit", model_admin.readonly_fields)
        self.assertNotIn("values_to_revisit", form.base_fields)
        self.assertNotIn("honesty_score", form.base_fields)
        self.assertNotIn("honesty_score", model_admin.readonly_fields)

    def test_dashboard_values_column_is_display_only(self):
        html = render_to_string("superadmin/dashboard.html")
        config = html.split("'session-reports': {", 1)[1].split("'child-session-memories':", 1)[0]
        self.assertIn("'values_to_revisit'", config)
        self.assertNotIn("honesty_score", html)
