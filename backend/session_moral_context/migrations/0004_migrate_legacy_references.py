from django.db import migrations

from session_moral_context.utils.arabic import normalize_ar

TYPE_MAP = {'hadith': 'hadith', 'quran': 'verse'}


def copy_legacy(apps, schema_editor):
    IslamicReference = apps.get_model('session_moral_context', 'IslamicReference')
    ContentItem = apps.get_model('session_moral_context', 'ContentItem')
    for ref in IslamicReference.objects.all():
        text = ref.text
        if ref.source:
            text += f"\n\n(legacy source: {ref.source})"
        item_type = TYPE_MAP.get(ref.reference_type, ref.reference_type)
        if ContentItem.objects.filter(
                type=item_type, english_text=text,
                verification_status='unverified').exists():
            continue
        ContentItem.objects.create(
            type=item_type, english_text=text, verification_status='unverified',
            search_text_norm=normalize_ar(text).lower())


class Migration(migrations.Migration):

    dependencies = [
        ('session_moral_context', '0003_knowledge_bank'),
    ]

    operations = [
        migrations.RunPython(copy_legacy, migrations.RunPython.noop),
    ]
