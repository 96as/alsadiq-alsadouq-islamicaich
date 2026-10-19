from types import SimpleNamespace

from asgiref.sync import async_to_sync
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase
from types import SimpleNamespace
from unittest.mock import patch
from rest_framework.test import APIClient

from conversation.agent.transcript_persistence import _persist_conversation_item
from authentication.models import ChildProfile
from conversation.agent.language_config import resolve_speech_languages
from conversation.models import Message, Session
from conversation.services import start_session

User = get_user_model()


class StartSessionStartFreshTests(TestCase):
    """A new start should not re-enter an already active session."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='child_resume_test',
            password='testpass123',
            is_child=True,
        )
        self.child = ChildProfile.objects.create(
            user=self.user,
            nickname='TestKid',
            gender='male',
            birth_year=2015,
        )

    def test_first_call_creates_session(self):
        session, token, created = start_session(self.child)
        self.assertTrue(created)
        self.assertEqual(Session.objects.filter(child=self.child).count(), 1)
        self.assertEqual(session.status, 'active')
        self.assertTrue(session.livekit_room_name)
        self.assertTrue(token)

    @patch("reporting.services.run_post_session_pipeline")
    def test_second_call_ends_active_session_and_creates_new_row(self, mock_pipeline):
        s1, t1, c1 = start_session(self.child)
        self.assertTrue(c1)
        s2, t2, c2 = start_session(self.child)
        self.assertTrue(c2)
        self.assertNotEqual(s1.pk, s2.pk)
        s1.refresh_from_db()
        self.assertEqual(s1.status, 'ended')
        self.assertIsNotNone(s1.ended_at)
        self.assertEqual(s2.status, 'active')
        self.assertEqual(Session.objects.filter(child=self.child, status='active').count(), 1)
        self.assertTrue(t1 and t2)
        mock_pipeline.assert_called_once_with(s1.id)


class ResolveSpeechLanguagesTests(TestCase):
    def test_english_preference_maps_to_english(self):
        stt, tts = resolve_speech_languages(
            "en",
            default_stt_language="en",
            default_tts_language="auto",
            arabic_tts_locale="ar-SA",
        )
        self.assertEqual(stt, "en")
        self.assertEqual(tts, "en")

    def test_arabic_preference_maps_to_arabic(self):
        stt, tts = resolve_speech_languages(
            "ar",
            default_stt_language="en",
            default_tts_language="auto",
            arabic_tts_locale="ar-SA",
        )
        self.assertEqual(stt, "ar")
        self.assertEqual(tts, "ar-SA")

    def test_unknown_preference_falls_back_to_defaults(self):
        stt, tts = resolve_speech_languages(
            "auto",
            default_stt_language="en",
            default_tts_language="auto",
            arabic_tts_locale="ar-SA",
        )
        self.assertEqual(stt, "en")
        self.assertEqual(tts, "auto")


class ConversationItemPersistenceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='voice_item_child',
            password='testpass123',
            is_child=True,
        )
        self.child = ChildProfile.objects.create(
            user=self.user,
            nickname='VoiceKid',
            gender='male',
            birth_year=2015,
        )
        self.session = Session.objects.create(child=self.child, status='active')
        self.agent = SimpleNamespace(_last_child_message_id=None)
        self.seen_item_ids = set()

    def _item(self, *, role, text, item_id='lk-item-1'):
        return SimpleNamespace(role=role, text_content=text, id=item_id)

    def test_user_conversation_item_creates_child_message_and_tracks_flag_target(self):
        saved = async_to_sync(_persist_conversation_item)(
            self.session,
            self.agent,
            self._item(role='user', text='I need help'),
            self.seen_item_ids,
        )

        self.assertIsNotNone(saved)
        self.assertEqual(saved.sender, 'child')
        self.assertEqual(saved.content, 'I need help')
        self.assertEqual(saved.input_type, 'voice')
        self.assertEqual(self.agent._last_child_message_id, saved.id)

    def test_assistant_conversation_item_creates_system_message(self):
        saved = async_to_sync(_persist_conversation_item)(
            self.session,
            self.agent,
            self._item(role='assistant', text='I am here with you.'),
            self.seen_item_ids,
        )

        self.assertIsNotNone(saved)
        self.assertEqual(saved.sender, 'system')
        self.assertEqual(saved.content, 'I am here with you.')
        self.assertIsNone(self.agent._last_child_message_id)

    def test_empty_conversation_item_does_not_create_message(self):
        saved = async_to_sync(_persist_conversation_item)(
            self.session,
            self.agent,
            self._item(role='user', text='   '),
            self.seen_item_ids,
        )

        self.assertIsNone(saved)
        self.assertFalse(Message.objects.filter(session=self.session).exists())

    def test_duplicate_livekit_item_id_does_not_create_duplicate_message(self):
        item = self._item(role='user', text='Only once', item_id='same-livekit-id')

        first = async_to_sync(_persist_conversation_item)(
            self.session,
            self.agent,
            item,
            self.seen_item_ids,
        )
        second = async_to_sync(_persist_conversation_item)(
            self.session,
            self.agent,
            item,
            self.seen_item_ids,
        )

        self.assertIsNotNone(first)
        self.assertIsNone(second)
        self.assertEqual(Message.objects.filter(session=self.session).count(), 1)

    def test_child_text_already_saved_by_text_input_handler_is_not_duplicated(self):
        skipped_text = {'Already saved text'}

        saved = async_to_sync(_persist_conversation_item)(
            self.session,
            self.agent,
            self._item(
                role='user',
                text='Already saved text',
                item_id='text-livekit-id',
            ),
            self.seen_item_ids,
            skipped_text,
        )

        self.assertIsNone(saved)
        self.assertFalse(Message.objects.filter(session=self.session).exists())
        self.assertEqual(skipped_text, set())
        self.assertIn('text-livekit-id', self.seen_item_ids)


class LiveKitWebhookSessionEndTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='child_webhook_test',
            password='testpass123',
            is_child=True,
        )
        self.child = ChildProfile.objects.create(
            user=self.user,
            nickname='WebhookKid',
            gender='female',
            birth_year=2016,
        )
        self.session = Session.objects.create(
            child=self.child,
            status='active',
            livekit_room_name='session_webhook_test',
        )

    @patch("reporting.services.run_post_session_pipeline")
    @patch("conversation.views.WebhookReceiver.receive")
    def test_child_participant_left_ends_active_session(self, mock_receive, mock_pipeline):
        mock_receive.return_value = SimpleNamespace(
            event='participant_left',
            room=SimpleNamespace(name=self.session.livekit_room_name),
            participant=SimpleNamespace(identity=f'child_{self.user.id}'),
        )

        response = self.client.post(
            reverse('conversation:livekit_webhook'),
            data='{}',
            content_type='application/json',
            HTTP_AUTHORIZATION='Bearer webhook-token',
        )

        self.assertEqual(response.status_code, 200)
        self.session.refresh_from_db()
        self.assertEqual(self.session.status, 'ended')
        self.assertIsNotNone(self.session.ended_at)
        mock_pipeline.assert_called_once_with(self.session.id)

    @patch("reporting.services.run_post_session_pipeline")
    @patch("conversation.views.WebhookReceiver.receive")
    def test_agent_participant_left_does_not_end_session(self, mock_receive, mock_pipeline):
        mock_receive.return_value = SimpleNamespace(
            event='participant_left',
            room=SimpleNamespace(name=self.session.livekit_room_name),
            participant=SimpleNamespace(identity='agent-AJ_test'),
        )

        response = self.client.post(
            reverse('conversation:livekit_webhook'),
            data='{}',
            content_type='application/json',
            HTTP_AUTHORIZATION='Bearer webhook-token',
        )

        self.assertEqual(response.status_code, 200)
        self.session.refresh_from_db()
        self.assertEqual(self.session.status, 'active')
        mock_pipeline.assert_not_called()
