"""post_session_pipeline racing a demo "Start fresh" / account delete: quiet skip, no traceback."""
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TransactionTestCase

from authentication.models import ChildProfile
from conversation.models import Message, Session
from reporting import services
from reporting.models import SessionReport
from reporting.tests import _unique_room

User = get_user_model()


@patch("reporting.services.close_old_connections")
class PipelineDeletedSessionTests(TransactionTestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="race_kid", password="x", is_child=True)
        self.child = ChildProfile.objects.create(
            user=self.user, nickname="RaceKid", gender="male", birth_year=2015,
        )
        self.session = Session.objects.create(
            child=self.child, status="ended", livekit_room_name=_unique_room(),
        )
        Message.objects.create(session=self.session, sender="child", content="Hello", input_type="text")

    def _delete_family(self, *_a, **_k):
        self.user.delete()  # cascades to the child, the session and its messages
        return services._neutral_report_data()

    def test_report_for_deleted_session_is_skipped_quietly(self, _close):
        with patch("reporting.services._generate_report_dict", side_effect=self._delete_family), \
                patch("reporting.services._cleanup_messages") as cleanup, \
                self.assertLogs("reporting.services", level="INFO") as logs:
            services.post_session_pipeline(self.session.id)
        self.assertFalse(any(r.levelname in ("ERROR", "CRITICAL") for r in logs.records), logs.output)
        self.assertTrue(any("deleted before its report was saved" in m for m in logs.output))
        self.assertFalse(SessionReport.objects.filter(session_id=self.session.id).exists())
        cleanup.assert_not_called()

    def test_weekly_summary_fk_for_deleted_family_is_skipped_quietly(self, _close):
        def weekly(_report):
            self.user.delete()
            raise IntegrityError("FOREIGN KEY constraint failed")

        with patch("reporting.services._generate_report_dict", return_value=services._neutral_report_data()), \
                patch("reporting.services._update_rolling_summary"), \
                patch("reporting.services._generate_quests_for_report"), \
                patch("reporting.services._update_weekly_summary", side_effect=weekly), \
                patch("reporting.services._cleanup_messages") as cleanup, \
                self.assertLogs("reporting.services", level="INFO") as logs:
            services.post_session_pipeline(self.session.id)
        self.assertFalse(any(r.levelname in ("ERROR", "CRITICAL") for r in logs.records), logs.output)
        # Only the normal step-2 cleanup ran; the failure path (which would touch a gone row) did not.
        cleanup.assert_called_once()

    def test_other_integrity_errors_still_log_the_failure_and_clean_up(self, _close):
        with patch("reporting.services._generate_report_dict", return_value=services._neutral_report_data()), \
                patch("reporting.services._update_rolling_summary", side_effect=IntegrityError("dup key")), \
                patch("reporting.services._cleanup_messages") as cleanup, \
                self.assertLogs("reporting.services", level="INFO") as logs:
            services.post_session_pipeline(self.session.id)
        self.assertTrue(any(r.levelname == "ERROR" and r.exc_info for r in logs.records))
        self.assertEqual(cleanup.call_count, 2)  # normal step + the failure-path cleanup
