"""
Management command: seed_admin

Creates a superuser if one doesn't exist. Idempotent: safe to re-run.

Development (DEBUG on): falls back to a well-known default password so a fresh
local stack works with no setup.

Production (DEBUG off): refuses the default. DJANGO_SUPERUSER_PASSWORD must be
set in the environment (and must not be the dev default), otherwise the command
exits with an error and creates nothing.
"""
import os

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from authentication.models import User

# Dev-only fallback. It lives in a public repo, so it is never accepted in production.
DEV_DEFAULT_PASSWORD = "SecurePass123!"


class Command(BaseCommand):
    help = (
        "Create an admin superuser (idempotent). With DEBUG off, "
        "DJANGO_SUPERUSER_PASSWORD is required and the dev default is refused."
    )

    def handle(self, *args, **options):
        username = os.getenv("DJANGO_SUPERUSER_USERNAME", "alsadiqadmin")
        email = os.getenv("DJANGO_SUPERUSER_EMAIL", "admin@alsadiq.dev")
        env_password = os.getenv("DJANGO_SUPERUSER_PASSWORD")

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(
                f"Admin user '{username}' already exists — skipping."
            ))
            return

        if settings.DEBUG:
            password = env_password or DEV_DEFAULT_PASSWORD
        else:
            if not env_password:
                raise CommandError(
                    "DEBUG is off: refusing to create the admin with the default password. "
                    "Set DJANGO_SUPERUSER_PASSWORD in the environment (.env) to a strong "
                    "secret and run seed_admin again."
                )
            if env_password == DEV_DEFAULT_PASSWORD:
                raise CommandError(
                    "DEBUG is off: DJANGO_SUPERUSER_PASSWORD is the public dev default. "
                    "Choose a different, strong password."
                )
            password = env_password

        User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
        )
        self.stdout.write(self.style.SUCCESS(
            f"Admin user '{username}' created successfully."
        ))
