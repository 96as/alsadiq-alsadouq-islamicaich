"""
Legacy pre-bank fixture importer. Use seed_content for the current knowledge bank.

Usage:
    python manage.py seed_content
    python manage.py seed_islamic_knowledge --legacy-i-know --fixture path/to/custom.json

Explicit legacy imports are idempotent and leave all references unverified.
"""
import json
import os

from django.core.management.base import BaseCommand, CommandError

from session_moral_context.models import IslamicReference, MoralTheme

DEFAULT_FIXTURE = os.path.join(
    os.path.dirname(__file__),
    '..', '..', 'fixtures', 'islamic_knowledge_base.json',
)


class Command(BaseCommand):
    help = 'Legacy pre-bank fixture importer (unverified references only); use seed_content instead'

    def add_arguments(self, parser):
        parser.add_argument(
            '--legacy-i-know', action='store_true',
            help='Explicitly import the retired legacy fixture; references remain unverified',
        )
        parser.add_argument(
            '--fixture',
            default=DEFAULT_FIXTURE,
            help='Path to the JSON fixture file (default: fixtures/islamic_knowledge_base.json)',
        )

    def handle(self, *args, **options):
        if not options['legacy_i_know']:
            raise CommandError(
                'Legacy importer disabled. Use seed_content for the current knowledge bank. '
                'Retired fixture imports require --legacy-i-know and remain unverified.'
            )
        self.stderr.write(self.style.WARNING(
            'Legacy import: not the knowledge bank. Use seed_content instead. '
            'All imported references remain unverified.'
        ))
        fixture_path = os.path.abspath(options['fixture'])

        if not os.path.exists(fixture_path):
            self.stderr.write(self.style.ERROR(f'Fixture not found: {fixture_path}'))
            return

        with open(fixture_path, encoding='utf-8') as f:
            data = json.load(f)

        themes_created = 0
        themes_existing = 0
        refs_created = 0
        refs_updated = 0

        for entry in data:
            theme_name = entry['theme'].strip()
            theme_description = entry.get('theme_description', '').strip()

            theme, created = MoralTheme.objects.get_or_create(
                name=theme_name,
                defaults={'description': theme_description},
            )
            if created:
                themes_created += 1
                self.stdout.write(f'  Created theme: {theme_name}')
            else:
                themes_existing += 1
                # Update description if provided and different
                if theme_description and theme.description != theme_description:
                    theme.description = theme_description
                    theme.save(update_fields=['description'])

            for ref_data in entry.get('references', []):
                ref_type = ref_data['type']
                ref_text = ref_data['text'].strip()
                ref_source = ref_data.get('source', '').strip()

                ref, created = IslamicReference.objects.get_or_create(
                    reference_type=ref_type,
                    text=ref_text,
                    defaults={
                        'source': ref_source,
                        'is_verified': False,
                    },
                )

                if created:
                    refs_created += 1
                else:
                    # Fixture provenance cannot establish verification.
                    changed = False
                    if ref.is_verified:
                        ref.is_verified = False
                        changed = True
                        self.stderr.write(self.style.WARNING(
                            f'Legacy reference {ref.pk} downgraded to unverified.'
                        ))
                    if ref_source and not ref.source:
                        ref.source = ref_source
                        changed = True
                    if changed:
                        ref.save(update_fields=['is_verified', 'source'])
                    refs_updated += 1

                ref.themes.add(theme)

        self.stdout.write(self.style.SUCCESS(
            f'\nDone. Themes: {themes_created} created, {themes_existing} existing. '
            f'References: {refs_created} created, {refs_updated} existing/updated.'
        ))
