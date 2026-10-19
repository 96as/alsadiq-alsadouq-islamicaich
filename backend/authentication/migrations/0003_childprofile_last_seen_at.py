from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0002_alter_user_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='childprofile',
            name='last_seen_at',
            field=models.DateTimeField(
                blank=True,
                help_text='Updated when the child uses the app (authenticated API activity).',
                null=True,
            ),
        ),
    ]
