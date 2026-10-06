"""Quest.value FK + the "values practised" badge track (r6 audit G1/G3, lead decisions 5 Oct).

Data step (forwards):
- Quest.moral_theme.name -> Value (gamification.backfill.backfill_quest_values).
  Unmatched quests keep value=NULL; a later ``seed_content`` maps them.
- The three honesty badges become the value-agnostic "values practised" track
  (1 / 5 / 15 distinct values across completed quests). The child is never
  graded on honesty, so no badge copy may read as a character verdict.
  If a badge with the new name already exists the old one is merged into it
  (old row deleted). Awards of the three badges are dropped and recomputed
  under the new rule, so nobody keeps an "honest conversations" badge under a
  "values practised" name.
- Any other ``honesty_sessions`` badge (renamed by hand) becomes a manual
  'special' badge; it can no longer be auto-awarded.
- Level 3 "Honest Helper" -> "Helpful Heart" (audit G2, cosmetic).

Backwards restores the three names, category='honesty' and
requirement_type='honesty_sessions' (skipping a rename when the old name is
taken) and the level name. ChildBadge rows and the old descriptions are NOT
restored: the honesty-session awards are gone for good once migrated.
"""
import django.db.models.deletion
from django.db import migrations, models
from django.db.models import Count

from gamification.backfill import backfill_quest_values

# (old name, new name, description, requirement_value, sort_order)
VALUE_BADGES = [
    ('Truthful Heart', 'First Value Practised',
     'Complete your first quest about a value, like kindness, patience or honesty.', 1, 1),
    ('Honest Soul', 'Five Values Practised',
     'Complete quests about five different values.', 5, 2),
    ('As-Sadiq Companion', 'Fifteen Values Practised',
     'Complete quests about fifteen different values. A whole garden of good habits!', 15, 3),
]


def recompute_values_badges(apps):
    """Award the values-practised track from scratch: distinct non-null
    quest values over completed progress rows per child."""
    Badge = apps.get_model('gamification', 'Badge')
    ChildBadge = apps.get_model('gamification', 'ChildBadge')
    ChildQuestProgress = apps.get_model('gamification', 'ChildQuestProgress')

    track = list(Badge.objects.filter(requirement_type='values_practised'))
    ChildBadge.objects.filter(badge__in=track).delete()
    counts = (
        ChildQuestProgress.objects.filter(status='completed', quest__value__isnull=False)
        .values('child_id')
        .annotate(n=Count('quest__value', distinct=True))
    )
    for row in counts:
        for badge in track:
            if badge.requirement_value > 0 and row['n'] >= badge.requirement_value:
                ChildBadge.objects.get_or_create(child_id=row['child_id'], badge=badge)


def forwards(apps, schema_editor):
    Badge = apps.get_model('gamification', 'Badge')
    Level = apps.get_model('gamification', 'Level')

    backfill_quest_values(apps)

    for old, new, desc, req, sort in VALUE_BADGES:
        old_badge = Badge.objects.filter(name=old).first()
        if old_badge is not None:
            if Badge.objects.filter(name=new).exists():
                old_badge.delete()  # merge: `new` already exists (unique name)
            else:
                old_badge.name = new
                old_badge.save(update_fields=['name'])
        Badge.objects.update_or_create(
            name=new,
            defaults={
                'description': desc,
                'category': 'values',
                'requirement_type': 'values_practised',
                'requirement_value': req,
                'sort_order': sort,
            },
        )

    # Orphans: honesty badges someone renamed by hand. No rule can award them now.
    Badge.objects.filter(requirement_type='honesty_sessions').update(requirement_type='manual')
    Badge.objects.filter(category='honesty').update(category='special')

    recompute_values_badges(apps)

    Level.objects.filter(number=3, name='Honest Helper').update(name='Helpful Heart')


def backwards(apps, schema_editor):
    Badge = apps.get_model('gamification', 'Badge')
    Level = apps.get_model('gamification', 'Level')

    for old, new, _desc, _req, _sort in VALUE_BADGES:
        fields = {'category': 'honesty', 'requirement_type': 'honesty_sessions'}
        if not Badge.objects.filter(name=old).exists():
            fields['name'] = old
        Badge.objects.filter(name=new).update(**fields)

    Level.objects.filter(number=3, name='Helpful Heart').update(name='Honest Helper')


class Migration(migrations.Migration):

    dependencies = [
        ('gamification', '0004_seed_badges_and_levels'),
        ('session_moral_context', '0007_fill_content_level'),
    ]

    operations = [
        migrations.AddField(
            model_name='quest',
            name='value',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='quests', to='session_moral_context.value'),
        ),
        migrations.AlterField(
            model_name='badge',
            name='category',
            field=models.CharField(choices=[('streak', 'Streak'), ('values', 'Values'), ('quest', 'Quest'), ('level', 'Level'), ('conversation', 'Conversation'), ('special', 'Special')], default='special', max_length=20),
        ),
        migrations.AlterField(
            model_name='badge',
            name='requirement_type',
            field=models.CharField(choices=[('streak_days', 'Streak of N days'), ('quests_completed', 'N quests completed'), ('level_reached', 'Level N reached'), ('values_practised', 'N distinct values practised'), ('sessions_count', 'N sessions held'), ('points_total', 'N total points'), ('manual', 'Manually awarded')], default='manual', max_length=30),
        ),
        migrations.RunPython(forwards, backwards),
    ]
