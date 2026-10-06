from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0003_childprofile_last_seen_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='childprofile',
            name='language_preference',
            field=models.CharField(
                choices=[
                    ('auto', 'Auto'),
                    ('en', 'English'),
                    ('ar', 'Arabic'),
                ],
                default='auto',
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name='childprofile',
            name='profile_icon',
            field=models.CharField(
                choices=[
                    ('sparkles', 'Sparkles'),
                    ('star', 'Star'),
                    ('heart', 'Heart'),
                    ('smile', 'Smile'),
                    ('cat', 'Cat'),
                    ('rainbow', 'Rainbow'),
                ],
                default='sparkles',
                max_length=20,
            ),
        ),
    ]
