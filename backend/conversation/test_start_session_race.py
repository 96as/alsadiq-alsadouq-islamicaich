"""start_session must survive near-simultaneous starts (load rehearsal finding).

``Session.livekit_room_name`` is unique. The old code created the row with the
blank default and set ``session_<id>`` afterwards, so two starts inside the same
instant both held '' and one hit the unique constraint (HTTP 500).
"""
import threading
import unittest
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import connection, connections
from django.test import TestCase, TransactionTestCase

from authentication.models import ChildProfile
from conversation.models import Session
from conversation.services import start_session

User = get_user_model()


def _make_child(tag):
    user = User.objects.create_user(username=f'race_{tag}', password='x', is_child=True)
    return ChildProfile.objects.create(
        user=user, nickname=f'Kid{tag}', gender='male', birth_year=2015)


class StartSessionPlaceholderTests(TestCase):
    """Deterministic version of the race: the second start arrives before the
    first one has written its final room name."""

    def test_two_starts_before_final_name_is_written_do_not_collide(self):
        a, b = _make_child('a'), _make_child('b')
        real_save = Session.save

        def save_without_final_name(self_, *args, **kwargs):
            # Swallow only the second write of start_session (the room name
            # update), leaving each row at its first-insert value.
            if kwargs.get('update_fields') == ['livekit_room_name']:
                return None
            return real_save(self_, *args, **kwargs)

        with patch.object(Session, 'save', save_without_final_name):
            s1, _, _ = start_session(a)
            s2, _, _ = start_session(b)  # IntegrityError before the fix

        # The in-memory objects already carry the final name; read the rows.
        n1 = Session.objects.get(pk=s1.pk).livekit_room_name
        n2 = Session.objects.get(pk=s2.pk).livekit_room_name
        self.assertNotEqual(n1, n2)
        self.assertTrue(n1.startswith('pending_'))
        self.assertTrue(n2.startswith('pending_'))

    def test_final_room_name_is_unchanged(self):
        session, token, created = start_session(_make_child('c'))
        self.assertTrue(created)
        self.assertEqual(session.livekit_room_name, f'session_{session.id}')
        session.refresh_from_db()
        self.assertEqual(session.livekit_room_name, f'session_{session.id}')
        self.assertTrue(token)


@unittest.skipIf(
    connection.vendor == 'sqlite',
    'in-memory SQLite locks whole tables across threads ("database table is locked"); '
    'the deterministic test above covers the race on SQLite, this one runs on Postgres',
)
class StartSessionConcurrencyTests(TransactionTestCase):
    """Several children press Start at once, from real threads (Postgres)."""

    N = 8

    def test_simultaneous_starts_all_succeed_with_final_names(self):
        children = [_make_child(str(i)) for i in range(self.N)]
        barrier = threading.Barrier(self.N)
        results, errors = [], []
        lock = threading.Lock()

        def worker(child):
            try:
                barrier.wait(timeout=10)
                session, _, _ = start_session(child)
                with lock:
                    results.append(session)
            except Exception as exc:  # noqa: BLE001 - collected and asserted below
                with lock:
                    errors.append(exc)
            finally:
                connections.close_all()

        threads = [threading.Thread(target=worker, args=(c,)) for c in children]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30)

        self.assertEqual(errors, [], f'start_session raised under concurrency: {errors!r}')
        self.assertEqual(len(results), self.N)
        names = [s.livekit_room_name for s in results]
        self.assertEqual(len(set(names)), self.N)
        for session in results:
            self.assertEqual(session.livekit_room_name, f'session_{session.id}')
