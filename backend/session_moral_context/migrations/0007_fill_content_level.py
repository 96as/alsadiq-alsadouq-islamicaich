from django.db import migrations

DEFAULT_CONTENT_LEVEL = {
    'verse': 'A', 'hadith': 'A', 'term': 'A', 'story': 'A', 'sirah': 'A',
    'aqidah': 'A', 'tafsir': 'B', 'faq': 'B', 'fiqh': 'B',
}


def fill_content_level(apps, schema_editor):
    Item = apps.get_model('session_moral_context', 'ContentItem')
    for t, level in DEFAULT_CONTENT_LEVEL.items():
        Item.objects.filter(type=t, content_level='').update(content_level=level)


class Migration(migrations.Migration):

    dependencies = [('session_moral_context', '0006_knowledge_bank_schema_v2')]

    operations = [migrations.RunPython(fill_content_level, migrations.RunPython.noop)]
