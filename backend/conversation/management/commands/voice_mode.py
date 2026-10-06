"""Flip the voice kill switch and show today's demo usage.

    python manage.py voice_mode            show the switch and today's usage
    python manage.py voice_mode status     same
    python manage.py voice_mode text       new sessions are text-only
    python manage.py voice_mode off        new sessions are refused with a friendly message
    python manage.py voice_mode eleven     ElevenLabs voice
    python manage.py voice_mode xai        xAI voice (a manual operator choice, never automatic)
    python manage.py voice_mode auto       clear the switch: follow TTS_PROVIDER from .env

The switch is the Redis key VOICE_MODE. It is read at the start of every session, so it needs
no redeploy and does not touch sessions that are already running. It never changes by itself:
when the ElevenLabs daily budget runs out, new sessions go text-only, not to xAI.

On the server:  docker compose -f docker-compose.prod.yml exec backend python manage.py voice_mode text
"""
from django.core.management.base import BaseCommand, CommandError

from conversation import demo_guards

CHOICES = ("status", "auto", *demo_guards.VOICE_MODES)


class Command(BaseCommand):
    help = "Flip the voice kill switch (VOICE_MODE in Redis) and show today's demo usage."

    def add_arguments(self, parser):
        parser.add_argument("mode", nargs="?", default="status", choices=CHOICES,
                            help="eleven | xai | text | off | auto (clear) | status (default)")

    def handle(self, *args, **options):
        mode = options["mode"]
        if mode != "status":
            if demo_guards.redis_client() is None:
                raise CommandError(
                    "Redis is not reachable (check REDIS_HOST / REDIS_URL). The switch was not changed.")
            value = None if mode == "auto" else mode
            if not demo_guards.set_stored_voice_mode(value):
                raise CommandError("Could not write VOICE_MODE to Redis. The switch was not changed.")
            self.stdout.write(self.style.SUCCESS(
                "VOICE_MODE cleared (following TTS_PROVIDER)." if value is None
                else f"VOICE_MODE set to {value}. New sessions use it."))
        self._print_report()

    def _print_report(self):
        r = demo_guards.usage_report()
        w = self.stdout.write
        if not r["redis"]:
            w(self.style.WARNING(
                "Redis: NOT reachable. Counters and the switch are skipped (guards fail open)."))
        d = r["decision"]
        w(f"day (guard clock):   {r['day']}")
        off = "no (DEBUG=1 or DEMO_GUARDS=0; DEMO_GUARDS=1 turns them on)"
        w(f"guards active:       {'yes' if r['guards_active'] else off}")
        w(f"VOICE_MODE (Redis):  {r['stored_voice_mode'] or 'unset'}")
        w(f"TTS_PROVIDER (env):  {r['env_voice_mode']} (used while VOICE_MODE is unset)")
        w(f"new sessions get:    {d['mode']} (why: {d['reason']})")
        cap = r["eleven_char_cap"]
        chars = r["eleven_chars"]
        w("ElevenLabs chars:    "
          f"{'?' if chars is None else chars} / {cap if cap else 'no cap'} today")
        w(f"sessions today:      {'?' if r['sessions_today'] is None else r['sessions_today']} "
          f"from {'?' if r['children_today'] is None else r['children_today']} children "
          f"(limit {r['daily_sessions_per_child'] or 'none'} per child)")
        w(f"session length:      {r['session_max_seconds'] or 'no limit'} s; "
          f"starts per hour per user: {r['session_start_per_hour'] or 'no limit'}")
