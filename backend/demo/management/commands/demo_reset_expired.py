from django.core.management.base import BaseCommand

from demo import services


class Command(BaseCommand):
    help = (
        'Reset every demo family whose lease has expired (visitor data is wiped '
        'and the synthetic week is re-seeded). Run from cron every few minutes.'
    )

    def handle(self, *args, **options):
        slots = services.reset_expired()
        self.stdout.write(f'Reset {len(slots)} expired demo families: {slots}')
