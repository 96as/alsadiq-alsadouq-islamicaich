"""Rate limits and abuse: DRF throttles count in one cache shared by every gunicorn worker.

Without this each of the 3 workers keeps its own LocMem counters, so the 5/minute login limit
really allows about 15/minute. See the security audit, PR #62 (M4).
"""
import os
import subprocess
import sys
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.cache import caches
from django.test import SimpleTestCase, TestCase
from django.urls import URLPattern, URLResolver, get_resolver
from rest_framework.settings import api_settings
from rest_framework.test import APIClient
from rest_framework.throttling import ScopedRateThrottle, UserRateThrottle

from authentication.models import ChildProfile
from config.throttling import SharedCacheThrottleMixin

User = get_user_model()
RATES = api_settings.DEFAULT_THROTTLE_RATES


def _clear_throttle_cache():
    caches['throttle'].clear()


def _settings_value(expr, **env):
    base = {k: v for k, v in os.environ.items()
            if k not in ('REDIS_URL', 'REDIS_HOST', 'REDIS_PORT', 'REDIS_GUARDS_DB')}
    base.update({"DJANGO_SECRET_KEY": "test-only-django-key", "DEBUG": "1", **env})
    code = ("import dotenv; dotenv.load_dotenv = lambda *a, **k: False; "
            f"from config import settings as s; print({expr})")
    result = subprocess.run([sys.executable, "-c", code], env=base, capture_output=True)
    assert result.returncode == 0, result.stderr.decode()
    return result.stdout.decode().strip()


class ThrottleCacheSettingsTests(SimpleTestCase):
    def test_locmem_without_redis(self):
        self.assertIn('LocMem', _settings_value("s.CACHES['throttle']['BACKEND']"))

    def test_redis_when_redis_url_is_set(self):
        out = _settings_value("s.CACHES['throttle']['BACKEND']", REDIS_URL='redis://r:6379/3')
        self.assertIn('RedisCache', out)

    def test_redis_when_redis_host_is_set(self):
        loc = _settings_value("s.CACHES['throttle']['LOCATION']", REDIS_HOST='redis')
        self.assertTrue(loc.startswith('redis://redis:6379/'))

    def test_redis_calls_time_out_fast(self):
        timeout = _settings_value("s.CACHES['throttle']['OPTIONS']['socket_timeout']",
                                  REDIS_HOST='redis')
        self.assertLessEqual(float(timeout), 0.5)

    def test_throttle_keys_do_not_collide_with_guards(self):
        env = dict(REDIS_HOST='redis')
        self.assertNotEqual(_settings_value("s.CACHES['throttle']['KEY_PREFIX']", **env),
                            _settings_value("s.CACHES['guards']['KEY_PREFIX']", **env))

    def test_default_throttle_classes_are_the_shared_ones(self):
        for cls in api_settings.DEFAULT_THROTTLE_CLASSES:
            self.assertTrue(issubclass(cls, SharedCacheThrottleMixin), cls)


def _views():
    """Every API view class reachable from the URL conf."""
    seen = set()

    def walk(patterns):
        for p in patterns:
            if isinstance(p, URLResolver):
                yield from walk(p.url_patterns)
            elif isinstance(p, URLPattern):
                cb = p.callback
                cls = getattr(cb, 'cls', None) or getattr(cb, 'view_class', None)
                if cls is not None and hasattr(cls, 'throttle_classes') and cls not in seen:
                    seen.add(cls)
                    yield cls

    return list(walk(get_resolver().url_patterns))


class EveryThrottleUsesTheSharedCacheTests(SimpleTestCase):
    # SessionStartThrottle counts in the Redis "guards" cache and fails open by itself.
    OWN_CACHE = {'SessionStartThrottle'}

    def test_found_the_views(self):
        self.assertGreater(len(_views()), 20)

    def test_all_view_throttles_use_the_throttle_cache(self):
        for view in _views():
            for throttle in view.throttle_classes:
                if throttle.__name__ in self.OWN_CACHE:
                    continue
                with self.subTest(view=view.__name__, throttle=throttle.__name__):
                    self.assertTrue(issubclass(throttle, SharedCacheThrottleMixin))
                    self.assertIs(throttle().cache, caches['throttle'])


class FailureModeTests(TestCase):
    """Redis down must not take the site down: the throttle steps aside and logs."""

    def setUp(self):
        from config import throttling
        throttling._fallback.clear()
        self.addCleanup(throttling._fallback.clear)

    def _broken_caches(self):
        broken = mock.Mock()
        broken.get.side_effect = ConnectionError('redis down')
        broken.set.side_effect = ConnectionError('redis down')
        return mock.patch('config.throttling.caches', {'throttle': broken})

    def test_throttle_degrades_to_a_per_process_limit_when_its_cache_errors(self):
        """Redis down: login brute force is still limited (per worker), and no request is a 500."""
        client = APIClient(raise_request_exception=False)
        with self._broken_caches(), self.assertLogs('config.throttling', level='WARNING') as logs:
            codes = [client.post('/api/auth/login/', {'username': 'a', 'password': 'b'},
                                 format='json', REMOTE_ADDR='5.5.5.5').status_code
                     for _ in range(7)]
            other_ip = client.post('/api/auth/login/', {'username': 'a', 'password': 'b'},
                                   format='json', REMOTE_ADDR='5.5.5.6').status_code
        self.assertEqual(codes, [401] * 5 + [429] * 2)
        self.assertEqual(other_ip, 401)
        self.assertIn('ConnectionError', logs.output[0])
        self.assertNotIn('redis down', ''.join(logs.output))

    def test_scoped_throttle_falls_back_instead_of_allowing_everything(self):
        from config.throttling import SharedScopedRateThrottle
        view = mock.Mock(throttle_scope='auth')
        request = mock.Mock()
        request.user.is_authenticated = False
        request.META = {'REMOTE_ADDR': '1.2.3.4'}
        with self._broken_caches():
            allowed = [SharedScopedRateThrottle().allow_request(request, view) for _ in range(6)]
        self.assertEqual(allowed, [True] * 5 + [False])


class RateEnvTests(SimpleTestCase):
    def test_empty_rate_env_values_fall_back_to_the_defaults(self):
        """A var that is set but empty (docker compose `VAR=`) must not become rate '' (a 500)."""
        env = {'SESSION_START_USER_RATE': '', 'DEMO_START_RATE': '', 'DEMO_RESET_RATE': ''}
        rates = _settings_value(
            "[s.REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'][k] for k in "
            "('session_start_user', 'demo_start', 'demo_reset')]", **env)
        self.assertEqual(rates, "['30/hour', '120/hour', '120/hour']")

    def test_explicit_rate_env_values_still_win(self):
        rates = _settings_value(
            "s.REST_FRAMEWORK['DEFAULT_THROTTLE_RATES']['demo_start']", DEMO_START_RATE='7/hour')
        self.assertEqual(rates, '7/hour')

    def test_auth_rate_env_unset_or_empty_gives_the_default_and_explicit_wins(self):
        expr = "s.REST_FRAMEWORK['DEFAULT_THROTTLE_RATES']['auth']"
        self.assertEqual(_settings_value(expr), '5/minute')
        self.assertEqual(_settings_value(expr, AUTH_RATE=''), '5/minute')
        self.assertEqual(_settings_value(expr, AUTH_RATE='30/minute'), '30/minute')

    def test_default_user_rate_keeps_the_old_effective_limit(self):
        """Before the shared cache each of ~3 workers allowed 60/min (about 180/min in total)."""
        self.assertEqual(RATES['user'], '180/minute')
        self.assertEqual(RATES['anon'], '30/minute')


class RateTableTests(SimpleTestCase):
    """Each endpoint has a scope, and the scope has the rate we decided on."""

    def test_scoped_endpoints(self):
        from authentication import views as auth
        from demo import views as demo
        table = [
            (auth.ParentRegisterView, 'registration', '3/minute'),
            (auth.CustomTokenObtainPairView, 'auth', '5/minute'),
            (auth.ThrottledTokenRefreshView, 'token_refresh', '30/minute'),
            (auth.PasswordResetRequestView, 'password_reset', '3/minute'),
            (auth.PasswordResetConfirmView, 'password_reset_confirm', '5/minute'),
            (auth.ChildPasswordChangeView, 'password_change', '5/hour'),
            (demo.DemoStartView, 'demo_start', '120/hour'),
            (demo.DemoResetView, 'demo_reset', '120/hour'),
        ]
        for view, scope, rate in table:
            with self.subTest(view=view.__name__):
                self.assertEqual(view.throttle_scope, scope)
                self.assertTrue(issubclass(view.throttle_classes[0], ScopedRateThrottle))
                self.assertEqual(RATES[scope], rate)

    def test_password_reset_also_counts_per_target_email(self):
        from authentication import views as auth
        names = [t.__name__ for t in auth.PasswordResetRequestView.throttle_classes]
        self.assertIn('PasswordResetEmailThrottle', names)
        self.assertEqual(RATES['password_reset_email'], '3/hour')

    def test_session_start_has_an_always_on_per_user_cap(self):
        from conversation import views as conv
        from conversation.throttles import StartSessionRateThrottle
        self.assertIn(StartSessionRateThrottle, conv.StartSessionView.throttle_classes)
        self.assertTrue(issubclass(StartSessionRateThrottle, UserRateThrottle))
        self.assertEqual(StartSessionRateThrottle.scope, 'session_start_user')
        if not os.getenv('SESSION_START_USER_RATE'):
            self.assertEqual(RATES['session_start_user'], '30/hour')


class ThrottleBehaviourTests(TestCase):
    def setUp(self):
        _clear_throttle_cache()
        self.addCleanup(_clear_throttle_cache)
        self.client = APIClient()

    def test_token_refresh_is_throttled_per_ip(self):
        with mock.patch.dict(ScopedRateThrottle.THROTTLE_RATES, {'token_refresh': '2/minute'}):
            codes = [self.client.post('/api/auth/token/refresh/', {'refresh': 'x'},
                                      format='json', REMOTE_ADDR='7.7.7.7').status_code
                     for _ in range(3)]
        self.assertEqual(codes, [401, 401, 429])

    def test_counters_live_in_the_throttle_cache(self):
        self.client.post('/api/auth/login/', {'username': 'a', 'password': 'b'},
                         format='json', REMOTE_ADDR='6.6.6.6')
        self.assertTrue(caches['throttle'].get('throttle_auth_6.6.6.6'))
        self.assertIsNone(caches['default'].get('throttle_auth_6.6.6.6'))

    def test_password_reset_email_is_limited_across_ips(self):
        with mock.patch('authentication.views.send_mail'):
            codes = [self.client.post('/api/auth/password-reset/',
                                      {'email': 'Victim@Example.com' if i % 2 else 'victim@example.com'},
                                      format='json', REMOTE_ADDR=f'10.0.0.{i}').status_code
                     for i in range(1, 6)]
            other = self.client.post('/api/auth/password-reset/', {'email': 'other@example.com'},
                                     format='json', REMOTE_ADDR='10.0.0.99').status_code
        self.assertEqual(codes, [200, 200, 200, 429, 429])
        self.assertEqual(other, 200)

    def test_password_reset_email_key_is_keyed_with_the_secret_key(self):
        """Unsalted SHA-256 of an address can be matched offline against a leaked Redis dump."""
        import hashlib
        from django.test import override_settings
        with override_settings(SECRET_KEY='key-one'):
            one = self._key('someone@example.com')
        with override_settings(SECRET_KEY='key-two'):
            two = self._key('someone@example.com')
        self.assertNotEqual(one, two)
        plain = hashlib.sha256(b'email:someone@example.com').hexdigest()
        self.assertNotIn(plain, one)

    def test_password_reset_email_key_is_a_hash_not_the_address(self):
        from authentication.throttles import PasswordResetEmailThrottle
        request = mock.Mock(data={'email': ' Victim@Example.com '})
        key = PasswordResetEmailThrottle().get_cache_key(request, None)
        self.assertNotIn('victim', key.lower())
        self.assertNotIn('example', key.lower())
        same = mock.Mock(data={'email': 'victim@example.com'})
        self.assertEqual(key, PasswordResetEmailThrottle().get_cache_key(same, None))
        self.assertIsNone(PasswordResetEmailThrottle().get_cache_key(mock.Mock(data=[1]), None))

    VARIANTS = [
        'victim@example.com',
        'VICTIM@EXAMPLE.COM',
        '  victim@example.com\t\n',
        'Victim@Example.COM',
        'victim@EXAMPLE.com',
        '\u3000victim@example.com\u3000',   # ideographic spaces
        '\uff56ictim@example.com',          # fullwidth v (NFKC compatibility form)
        'VICTIM@example.com',
    ]

    def _key(self, email):
        from authentication.throttles import PasswordResetEmailThrottle
        return PasswordResetEmailThrottle().get_cache_key(mock.Mock(data={'email': email}), None)

    def test_email_variants_share_one_bucket_when_the_account_exists(self):
        User.objects.create_user(username='victim', password='x', email='victim@example.com',
                                 is_parent=True)
        self.assertEqual({self._key(e) for e in self.VARIANTS}, {self._key('victim@example.com')})

    def test_email_variants_share_one_bucket_when_no_account_exists(self):
        self.assertEqual({self._key(e) for e in self.VARIANTS}, {self._key('victim@example.com')})

    def test_bucket_is_the_account_even_if_stored_email_has_odd_case(self):
        User.objects.create_user(username='odd', password='x', email='Odd@Example.com', is_parent=True)
        self.assertEqual(self._key('odd@example.com'), self._key('ODD@EXAMPLE.COM'))

    def test_variants_cannot_bypass_the_per_email_limit(self):
        User.objects.create_user(username='victim', password='x', email='victim@example.com',
                                 is_parent=True)
        with mock.patch('authentication.views.send_mail') as send:
            codes = [self.client.post('/api/auth/password-reset/', {'email': e}, format='json',
                                      REMOTE_ADDR=f'10.1.0.{i}').status_code
                     for i, e in enumerate(self.VARIANTS[:5], 1)]
        self.assertEqual(codes[:3], [200, 200, 200])
        self.assertNotIn(200, codes[3:])
        self.assertEqual(send.call_count, 3)

    def test_unknown_and_known_accounts_look_the_same(self):
        User.objects.create_user(username='victim', password='x', email='victim@example.com',
                                 is_parent=True)
        with mock.patch('authentication.views.send_mail'):
            known = [self.client.post('/api/auth/password-reset/', {'email': 'victim@example.com'},
                                      format='json', REMOTE_ADDR='10.2.0.1') for _ in range(4)]
            unknown = [self.client.post('/api/auth/password-reset/', {'email': 'nobody@example.com'},
                                        format='json', REMOTE_ADDR='10.2.0.2') for _ in range(4)]
        self.assertEqual([r.status_code for r in known], [r.status_code for r in unknown])
        self.assertEqual(known[0].json(), unknown[0].json())

    def test_child_password_change_is_limited_per_child(self):
        user = User.objects.create_user(username='pw_kid', password='x', is_child=True)
        ChildProfile.objects.create(user=user, nickname='Pw', gender='male', birth_year=2015)
        self.client.force_authenticate(user=user)
        with mock.patch.dict(ScopedRateThrottle.THROTTLE_RATES, {'password_change': '2/hour'}):
            codes = [self.client.post('/api/auth/profile/child/password/',
                                      {'new_password': 'short'}, format='json').status_code
                     for _ in range(3)]
        self.assertEqual(codes, [400, 400, 429])

    def test_session_start_user_cap(self):
        user = User.objects.create_user(username='ss_kid', password='x', is_child=True)
        ChildProfile.objects.create(user=user, nickname='Ss', gender='male', birth_year=2015)
        self.client.force_authenticate(user=user)
        client = APIClient(raise_request_exception=False)
        client.force_authenticate(user=user)
        with mock.patch.dict(UserRateThrottle.THROTTLE_RATES, {'session_start_user': '2/hour'}), \
                mock.patch('conversation.views.start_session', side_effect=RuntimeError('x')):
            codes = [client.post('/api/conversation/sessions/').status_code for _ in range(3)]
        self.assertEqual(codes, [500, 500, 429])
