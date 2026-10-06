# Generated manually for post-session reporting pipeline

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("gamification", "0001_initial"),
        ("reporting", "0002_childsessionmemory_raw_llm_output"),
    ]

    operations = [
        migrations.AddField(
            model_name="quest",
            name="is_ai_generated",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="quest",
            name="session_report",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="generated_quests",
                to="reporting.sessionreport",
            ),
        ),
    ]
