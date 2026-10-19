# Generated manually for post-session reporting pipeline

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("authentication", "0001_initial"),
        ("reporting", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="sessionreport",
            name="raw_llm_output",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.CreateModel(
            name="ChildSessionMemory",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("rolling_summary", models.TextField(blank=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "child",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="session_memory",
                        to="authentication.childprofile",
                    ),
                ),
            ],
            options={},
        ),
        migrations.AddIndex(
            model_name="childsessionmemory",
            index=models.Index(
                fields=["updated_at"], name="reporting_c_updated_8a1b2c_idx"
            ),
        ),
    ]
