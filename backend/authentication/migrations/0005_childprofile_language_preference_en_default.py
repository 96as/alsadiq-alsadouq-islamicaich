from django.db import migrations, models


def forwards_set_auto_to_en(apps, schema_editor):
    ChildProfile = apps.get_model('authentication', 'ChildProfile')
    ChildProfile.objects.filter(language_preference='auto').update(language_preference='en')


class Migration(migrations.Migration):
    dependencies = [
        ('authentication', '0004_childprofile_language_preference_profile_icon'),
    ]

    operations = [
        migrations.RunPython(forwards_set_auto_to_en, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='childprofile',
            name='language_preference',
            field=models.CharField(
                choices=[('en', 'English'), ('ar', 'Arabic')],
                default='en',
                max_length=10,
            ),
        ),
    ]
