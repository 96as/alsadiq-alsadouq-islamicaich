import os
import subprocess
import sys
from io import StringIO
from unittest import mock

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase, TestCase, override_settings

from authentication.models import User


def _env(**values):
    """Patch os.environ so only the given seed_admin vars are set."""
    keys = (
        "DJANGO_SUPERUSER_USERNAME",
        "DJANGO_SUPERUSER_EMAIL",
        "DJANGO_SUPERUSER_PASSWORD",
    )
    env = {k: v for k, v in os.environ.items() if k not in keys}
    env.update(values)
    return mock.patch.dict(os.environ, env, clear=True)


class SeedAdminTests(TestCase):
    def run_seed(self):
        out = StringIO()
        call_command("seed_admin", stdout=out)
        return out.getvalue()

    @override_settings(DEBUG=True)
    def test_dev_uses_default_password(self):
        with _env():
            self.run_seed()
        admin = User.objects.get(username="alsadiqadmin")
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.check_password("SecurePass123!"))

    @override_settings(DEBUG=True)
    def test_dev_prefers_env_password(self):
        with _env(DJANGO_SUPERUSER_PASSWORD="dev-env-pass-1"):
            self.run_seed()
        self.assertTrue(User.objects.get(username="alsadiqadmin").check_password("dev-env-pass-1"))

    @override_settings(DEBUG=False)
    def test_production_refuses_missing_password(self):
        with _env():
            with self.assertRaises(CommandError) as ctx:
                self.run_seed()
        self.assertIn("DJANGO_SUPERUSER_PASSWORD", str(ctx.exception))
        self.assertFalse(User.objects.filter(username="alsadiqadmin").exists())

    @override_settings(DEBUG=False)
    def test_production_refuses_dev_default_password(self):
        with _env(DJANGO_SUPERUSER_PASSWORD="SecurePass123!"):
            with self.assertRaises(CommandError):
                self.run_seed()
        self.assertFalse(User.objects.filter(username="alsadiqadmin").exists())

    @override_settings(DEBUG=False)
    def test_production_accepts_env_password(self):
        with _env(DJANGO_SUPERUSER_PASSWORD="prod-secret-from-env-9"):
            self.run_seed()
        admin = User.objects.get(username="alsadiqadmin")
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.check_password("prod-secret-from-env-9"))

    @override_settings(DEBUG=False)
    def test_production_existing_admin_is_skipped_without_password(self):
        User.objects.create_superuser("alsadiqadmin", "a@example.com", "whatever-existing-1")
        with _env():
            output = self.run_seed()
        self.assertIn("already exists", output)


class HealthEndpointTests(TestCase):
    url = "/api/health/"

    def test_ok_without_auth_when_redis_not_configured(self):
        with mock.patch.dict(os.environ, {"REDIS_HOST": ""}):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "ok")
        self.assertEqual(body["checks"], {"database": "ok", "redis": "skipped"})

    def test_ok_when_redis_pings(self):
        with mock.patch.dict(os.environ, {"REDIS_HOST": "redis"}):
            with mock.patch("redis.Redis") as fake:
                fake.return_value.ping.return_value = True
                response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["checks"]["redis"], "ok")
        fake.return_value.close.assert_called_once()

    def test_head_allowed_for_uptime_monitors(self):
        with mock.patch.dict(os.environ, {"REDIS_HOST": ""}):
            response = self.client.head(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"")

    def test_503_when_redis_is_down(self):
        with mock.patch.dict(os.environ, {"REDIS_HOST": "redis"}):
            with mock.patch("redis.Redis") as fake:
                fake.return_value.ping.side_effect = ConnectionError("secret detail")
                response = self.client.get(self.url)
        self.assertEqual(response.status_code, 503)
        body = response.json()
        self.assertEqual(body["status"], "degraded")
        self.assertEqual(body["checks"]["redis"], "error")
        self.assertNotIn("secret detail", response.content.decode())

    def test_503_when_database_is_down(self):
        with mock.patch.dict(os.environ, {"REDIS_HOST": ""}):
            with mock.patch("config.health.connection.cursor", side_effect=RuntimeError("db gone")):
                response = self.client.get(self.url)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["checks"]["database"], "error")
        self.assertNotIn("db gone", response.content.decode())

    def test_post_not_allowed(self):
        self.assertEqual(self.client.post(self.url).status_code, 405)


class DebugDefaultTests(SimpleTestCase):
    def _debug(self, **env):
        import subprocess
        import sys

        base = {k: v for k, v in os.environ.items() if k != "DEBUG"}
        base.update(DJANGO_SECRET_KEY="x" * 50, DJANGO_ALLOWED_HOSTS="example.com",
                    LIVEKIT_API_SECRET="x" * 40)
        base.update(env)
        out = subprocess.run(
            # Stub load_dotenv so a developer's local .env cannot mask the default.
            [sys.executable, "-c",
             "import dotenv; dotenv.load_dotenv = lambda *a, **k: None\n"
             "import config.settings as s; print(s.DEBUG, "
             "getattr(s, 'SECURE_SSL_REDIRECT', None), getattr(s, 'SESSION_COOKIE_SECURE', None), "
             "getattr(s, 'CSRF_COOKIE_SECURE', None), getattr(s, 'SECURE_HSTS_SECONDS', 0) > 0)"],
            env=base, capture_output=True, text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        )
        self.assertEqual(out.returncode, 0, out.stderr)
        return out.stdout.strip()

    def test_debug_off_when_env_absent(self):
        # DEBUG off also means production security settings (SSL redirect, secure cookies, HSTS).
        self.assertEqual(self._debug(), "False True True True True")

    def test_debug_on_when_explicit(self):
        self.assertEqual(self._debug(DEBUG="1").split()[0], "True")


class EnvListTests(SimpleTestCase):
    def test_env_list_strips_and_drops_empty_items(self):
        from config.settings import _env_list

        with mock.patch.dict(os.environ, {"X_LIST": " https://a.com , ,https://b.com,"}):
            self.assertEqual(_env_list("X_LIST"), ["https://a.com", "https://b.com"])
        with mock.patch.dict(os.environ, {"X_LIST": ""}):
            self.assertEqual(_env_list("X_LIST"), [])


class LiveKitSecretDefaultsTests(SimpleTestCase):
    def _import_settings(self, **extra):
        env = {k: v for k, v in os.environ.items()
               if k not in ("DEBUG", "LIVEKIT_API_KEY", "LIVEKIT_API_SECRET")}
        env.update({"DJANGO_SECRET_KEY": "test-only-django-key", **extra})
        code = "import dotenv; dotenv.load_dotenv = lambda *a, **k: None; from config import settings"
        return subprocess.run([sys.executable, "-c", code], env=env, capture_output=True)

    def test_production_refuses_the_public_dev_livekit_secret(self):
        result = self._import_settings()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(b"LIVEKIT_API_SECRET", result.stderr)

    def test_production_accepts_a_real_livekit_secret(self):
        result = self._import_settings(LIVEKIT_API_KEY="k", LIVEKIT_API_SECRET="x" * 40)
        self.assertEqual(result.returncode, 0, result.stderr.decode())

    def test_production_refuses_an_empty_livekit_secret(self):
        result = self._import_settings(LIVEKIT_API_KEY="k", LIVEKIT_API_SECRET="")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(b"LIVEKIT_API_SECRET", result.stderr)

    def test_debug_keeps_the_dev_livekit_secret(self):
        result = self._import_settings(DEBUG="1")
        self.assertEqual(result.returncode, 0, result.stderr.decode())

    def test_dockerfile_collectstatic_step_imports_settings(self):
        """The image build runs collectstatic with only the env on its RUN line; it must boot."""
        import re
        from pathlib import Path

        dockerfile = Path(__file__).resolve().parent.parent / "Dockerfile"
        run = next(l for l in dockerfile.read_text().splitlines()
                   if l.startswith("RUN ") and "collectstatic" in l)
        build_env = dict(re.findall(r"\b([A-Z][A-Z0-9_]*)=(\S+)", run.split("python")[0]))
        self.assertEqual(build_env.get("DEBUG"), "0")
        code = "import dotenv; dotenv.load_dotenv = lambda *a, **k: None; from config import settings"
        result = subprocess.run([sys.executable, "-c", code], capture_output=True,
                                env={"PATH": os.environ["PATH"], **build_env})
        self.assertEqual(result.returncode, 0, result.stderr.decode())


class ApiRenderersTests(SimpleTestCase):
    """The browsable API is a dev convenience; production answers JSON only."""

    def _renderers(self, debug):
        env = {**os.environ, "DJANGO_SECRET_KEY": "test-only-django-key", "DEBUG": debug,
               "LIVEKIT_API_SECRET": "x" * 40}
        code = (
            "import dotenv; dotenv.load_dotenv = lambda *a, **k: False; "
            "from config import settings as s; "
            "print(','.join(s.REST_FRAMEWORK.get('DEFAULT_RENDERER_CLASSES', ('default',))))"
        )
        result = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr.decode())
        return result.stdout.decode().strip()

    def test_production_is_json_only(self):
        self.assertEqual(self._renderers("0"), "rest_framework.renderers.JSONRenderer")

    def test_debug_keeps_drf_default_renderers(self):
        self.assertEqual(self._renderers("1"), "default")


class ThrottleProxyTests(SimpleTestCase):
    """DRF NUM_PROXIES: unset in dev, 1 behind the single Caddy hop in production."""

    def _num_proxies(self, **extra):
        env = {k: v for k, v in os.environ.items() if k != "DRF_NUM_PROXIES"}
        env.update({"DJANGO_SECRET_KEY": "test-only-django-key", "DEBUG": "1", **extra})
        code = (
            "import dotenv; dotenv.load_dotenv = lambda *a, **k: False; "
            "from config import settings as s; "
            "print(s.REST_FRAMEWORK.get('NUM_PROXIES'))"
        )
        result = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr.decode())
        return result.stdout.decode().strip()

    def test_unset_means_none(self):
        self.assertEqual(self._num_proxies(), "None")

    def test_env_sets_the_proxy_count(self):
        self.assertEqual(self._num_proxies(DRF_NUM_PROXIES="1"), "1")

    def test_explicit_zero_stays_zero(self):
        self.assertEqual(self._num_proxies(DRF_NUM_PROXIES="0"), "0")

    def test_blank_env_means_none(self):
        self.assertEqual(self._num_proxies(DRF_NUM_PROXIES=""), "None")
