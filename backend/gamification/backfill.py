"""Map legacy ``Quest.moral_theme`` rows to bank ``Value`` rows.

Shared by migration 0005 (historical models) and ``seed_content`` (live
models), so quests created before the Values were seeded still get mapped
the next time the bank is seeded. Idempotent: only ``value IS NULL`` quests.
"""
from django.db.models import Q

# Theme labels that are not a Value name but clearly mean one.
THEME_ALIASES = {'truthfulness': 'honesty'}


def backfill_quest_values(apps=None) -> int:
    """Set ``Quest.value`` from ``moral_theme.name`` (case-insensitive name_en,
    exact name_ar, or slug, with THEME_ALIASES). Returns how many were mapped.

    ``apps`` is a migration state registry; None uses the live models.
    """
    if apps is None:
        from gamification.models import Quest
        from session_moral_context.models import Value
    else:
        Quest = apps.get_model('gamification', 'Quest')
        Value = apps.get_model('session_moral_context', 'Value')

    mapped = 0
    quests = Quest.objects.filter(
        value__isnull=True, moral_theme__isnull=False
    ).select_related('moral_theme')
    for quest in quests:
        name = quest.moral_theme.name.strip()
        slug = THEME_ALIASES.get(name.lower(), name)
        value = Value.objects.filter(
            Q(name_en__iexact=name) | Q(name_ar=name) | Q(slug__iexact=slug)
        ).first()
        if value:
            quest.value = value
            quest.save(update_fields=['value'])
            mapped += 1
    return mapped
