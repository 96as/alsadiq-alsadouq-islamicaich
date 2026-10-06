from django.conf import settings
from django.core.management.base import BaseCommand

from demo import content, services


class Command(BaseCommand):
    help = (
        'Create the pool of synthetic demo families. Without --ensure it wipes and '
        're-seeds every family (a full reset). With --ensure it only creates the '
        'families that are missing and only adds missing sources to a seeded one, so it is safe on '
        'every deploy, even while visitors hold a lease. Synthetic data only.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--size', type=int, default=None,
            help=(
                f'Number of families (default DEMO_POOL_SIZE={settings.DEMO_POOL_SIZE}, '
                f'max {len(content.FAMILIES)}).'
            ),
        )
        parser.add_argument(
            '--ensure', action='store_true',
            help='Idempotent: seed only the missing families, only add missing sources to the others.',
        )

    def handle(self, *args, **options):
        if options['ensure']:
            created = services.ensure_pool(options['size'])
            if created is None:
                self.stdout.write('Another process is seeding the demo pool; nothing to do.')
            else:
                have = services.pool_slots()
                self.stdout.write(self.style.SUCCESS(
                    f'Demo pool ready: {len(have)} families '
                    f'(created {len(created)}: {created}).'
                ))
        else:
            slots = services.seed_pool(options['size'])
            self.stdout.write(self.style.SUCCESS(f'Seeded {len(slots)} demo families: {slots}'))
        if not settings.DEMO_MODE:
            self.stdout.write('Note: DEMO_MODE is off, so /api/demo/start answers 404.')
