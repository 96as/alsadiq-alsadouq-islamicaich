"""Each new demo visitor gets the full daily allowance; "Start over" does not reset it."""
from types import SimpleNamespace
from unittest import mock

from django.test import SimpleTestCase

from demo import services


class VisitorAllowanceTests(SimpleTestCase):
    def test_new_visitor_clears_the_family_daily_count(self):
        child = SimpleNamespace(pk=42)
        with mock.patch.object(services, 'acquire_slot', return_value=(3, 'lease')), \
                mock.patch.object(services, 'reset_family', return_value=(object(), child)), \
                mock.patch.object(services, 'build_payload', return_value={}), \
                mock.patch('conversation.demo_guards.clear_daily_sessions') as clear:
            services.start_demo()
        clear.assert_called_once_with(42)

    def test_start_over_keeps_the_count(self):
        child = SimpleNamespace(pk=42)
        with mock.patch.object(services, 'lease_holder_matches', return_value=True), \
                mock.patch.object(services, 'extend_lease'), \
                mock.patch.object(services, 'reset_family', return_value=(object(), child)), \
                mock.patch.object(services, 'build_payload', return_value={}), \
                mock.patch('conversation.demo_guards.clear_daily_sessions') as clear:
            services.restart_demo(3, 'lease')
        clear.assert_not_called()
