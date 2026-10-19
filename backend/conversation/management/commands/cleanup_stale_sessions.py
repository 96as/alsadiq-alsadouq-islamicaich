from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Max, Q
from datetime import timedelta

from conversation.models import Session
from conversation.services import end_session


class Command(BaseCommand):
    help = 'End active sessions that were not properly closed (stale session cleanup).'

    def add_arguments(self, parser):
        parser.add_argument('--hard-cap-hours', type=int, default=2,
                            help='End sessions older than this many hours (default: 2)')
        parser.add_argument('--idle-minutes', type=int, default=15,
                            help='No message within this many minutes = idle (default: 15)')
        parser.add_argument('--min-age-minutes', type=int, default=30,
                            help='Session must be at least this old for idle check (default: 30)')
        parser.add_argument('--dry-run', action='store_true',
                            help='Print sessions that would be ended without ending them')

    def handle(self, *args, **options):
        now = timezone.now()
        hard_cap_threshold = now - timedelta(hours=options['hard_cap_hours'])
        min_age_threshold = now - timedelta(minutes=options['min_age_minutes'])
        idle_threshold = now - timedelta(minutes=options['idle_minutes'])
        dry_run = options['dry_run']

        # Condition 1: hard cap — session running longer than 2 hours
        hard_cap_qs = Session.objects.filter(
            status='active',
            started_at__lt=hard_cap_threshold,
        )

        # Condition 2: idle — old enough AND no recent messages
        idle_qs = (
            Session.objects.filter(status='active', started_at__lt=min_age_threshold)
            .annotate(last_msg_at=Max('messages__created_at'))
            .filter(
                Q(last_msg_at__isnull=True) | Q(last_msg_at__lt=idle_threshold)
            )
        )

        stale_sessions = (hard_cap_qs | idle_qs).distinct()
        count = stale_sessions.count()

        if count == 0:
            self.stdout.write('No stale sessions found.')
            return

        prefix = '[DRY RUN] ' if dry_run else ''
        self.stdout.write(f'{prefix}Found {count} stale session(s).')

        for session in stale_sessions:
            if dry_run:
                self.stdout.write(
                    f'  [DRY RUN] Would end session {session.id} '
                    f'(child={session.child_id}, started={session.started_at.isoformat()})'
                )
            else:
                try:
                    end_session(session)
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  Ended session {session.id} '
                            f'(child={session.child_id}, started={session.started_at.isoformat()})'
                        )
                    )
                except Exception as exc:
                    self.stdout.write(
                        self.style.ERROR(
                            f'  Failed to end session {session.id}: {exc}'
                        )
                    )
