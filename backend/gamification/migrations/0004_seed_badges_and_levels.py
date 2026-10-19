"""Seed default levels and the locked-badge catalog (streak/honesty/quest/level/conversation)."""
from django.db import migrations

LEVELS = [
    (1, 'New Friend', 0),
    (2, 'Kind Companion', 50),
    (3, 'Honest Helper', 120),
    (4, 'Brave Heart', 220),
    (5, 'Wise Explorer', 350),
    (6, 'Patient Star', 520),
    (7, 'Noble Guide', 730),
    (8, 'Radiant Soul', 1000),
]

# (name, description, category, requirement_type, requirement_value, sort_order)
BADGES = [
    # Streak
    ('First Spark', 'Talk with Al-Sadiq two days in a row.', 'streak', 'streak_days', 2, 1),
    ('Three-Day Glow', 'Keep a 3-day streak going.', 'streak', 'streak_days', 3, 2),
    ('Steadfast Week', 'A full week of daily visits — 7-day streak.', 'streak', 'streak_days', 7, 3),
    ('Two-Week Champion', 'Fourteen days in a row of showing up.', 'streak', 'streak_days', 14, 4),
    ('Moon of Consistency', 'A whole month — 30-day streak. Amazing patience!', 'streak', 'streak_days', 30, 5),
    # Honesty
    ('Truthful Heart', 'Have your first fully honest conversation.', 'honesty', 'honesty_sessions', 1, 1),
    ('Honest Soul', 'Five conversations where you were open and truthful.', 'honesty', 'honesty_sessions', 5, 2),
    ('As-Sadiq Companion', 'Fifteen honest conversations — truthfulness is your habit now.', 'honesty', 'honesty_sessions', 15, 3),
    # Quests
    ('First Quest', 'Complete your very first quest.', 'quest', 'quests_completed', 1, 1),
    ('Quest Explorer', 'Complete 5 quests.', 'quest', 'quests_completed', 5, 2),
    ('Quest Hero', 'Complete 15 quests.', 'quest', 'quests_completed', 15, 3),
    ('Quest Legend', 'Complete 30 quests — a true doer of good deeds.', 'quest', 'quests_completed', 30, 4),
    # Levels
    ('Rising Star', 'Reach level 2.', 'level', 'level_reached', 2, 1),
    ('Bright Moon', 'Reach level 4.', 'level', 'level_reached', 4, 2),
    ('Radiant Sun', 'Reach level 6.', 'level', 'level_reached', 6, 3),
    ('Wisdom Seeker', 'Reach level 8 — the highest rank!', 'level', 'level_reached', 8, 4),
    # Conversation
    ('First Hello', 'Finish your first conversation with Al-Sadiq.', 'conversation', 'sessions_count', 1, 1),
    ('Good Listener', 'Finish 10 conversations.', 'conversation', 'sessions_count', 10, 2),
    ('Heart to Heart', 'Finish 25 conversations — Al-Sadiq knows you well now.', 'conversation', 'sessions_count', 25, 3),
]


def seed(apps, schema_editor):
    Level = apps.get_model('gamification', 'Level')
    Badge = apps.get_model('gamification', 'Badge')

    if not Level.objects.exists():
        for number, name, required in LEVELS:
            Level.objects.create(number=number, name=name, required_points=required)

    for name, desc, category, req_type, req_value, sort in BADGES:
        Badge.objects.update_or_create(
            name=name,
            defaults={
                'description': desc,
                'category': category,
                'requirement_type': req_type,
                'requirement_value': req_value,
                'sort_order': sort,
            },
        )


def unseed(apps, schema_editor):
    Badge = apps.get_model('gamification', 'Badge')
    Badge.objects.filter(name__in=[b[0] for b in BADGES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('gamification', '0003_alter_badge_options_alter_childquestprogress_options_and_more'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
