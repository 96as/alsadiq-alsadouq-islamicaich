from unittest import mock

from asgiref.sync import async_to_sync
from django.contrib.auth import get_user_model
from django.test import TestCase

from authentication.models import ChildProfile
from conversation.agent.agent_class import _complete_companion_quest
from gamification import services
from gamification.models import ChildQuestProgress, Points, Quest

User = get_user_model()


class CompanionQuestRaceTests(TestCase):
    def test_quest_completed_by_another_caller_mid_call_returns_a_message(self):
        """The child taps 'done' while the companion completes the same quest.

        complete_quest_progress then returns points=None; the agent tool must say so
        instead of raising TypeError on result["points"]["delta_applied"].
        """
        user = User.objects.create_user(username='race_kid', password='x', is_child=True)
        child = ChildProfile.objects.create(user=user, nickname='R', gender='male', birth_year=2015)
        quest = Quest.objects.create(
            title='Talk quest', reward_points=10, quest_type='conversation',
            verification_method='companion',
        )
        progress = ChildQuestProgress.objects.create(child=child, quest=quest, status='in_progress')
        real = services.complete_quest_progress

        def other_caller_wins(prog, **kwargs):
            real(ChildQuestProgress.objects.get(pk=prog.pk), verified_by='child')
            return real(prog, **kwargs)  # the stale row loses the conditional UPDATE

        with mock.patch.object(services, 'complete_quest_progress', side_effect=other_caller_wins):
            result = async_to_sync(_complete_companion_quest)(
                child_id=child.pk, session_id=0, progress_id=progress.pk,
            )

        self.assertEqual(result, "That quest is already completed.")
        self.assertEqual(Points.objects.get(child=child).total, 10)
