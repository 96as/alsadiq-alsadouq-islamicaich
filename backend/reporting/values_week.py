"""Neutral, database-only values for parent insights. Never reads child text."""
from collections import Counter

from gamification.models import ChildQuestProgress
from session_moral_context.models import ContentItem, Value

from .models import SessionReport
from .services import _week_start_today


def values_this_week(child) -> list[dict]:
    """Count source references, revisit slugs (once/report), and completed quests.

    Each source's ``times_discussed`` contributes to every named bank value.
    Apply weekly_sources' drop rules to each snapshot before counting, so an
    unverified snapshot cannot contribute even if another snapshot is reviewed.
    Ties use the value slug. Output contains bank names only, never LLM wording.
    """
    week_start = _week_start_today()
    values = {v.slug: v for v in Value.objects.all()}
    by_name = {v.name_en: v.slug for v in values.values()}
    counts = Counter()
    snapshots = []
    reports = SessionReport.objects.filter(
        session__child=child, session__started_at__date__gte=week_start,
    ).values_list("sources_used", "raw_llm_output")
    for sources, raw in reports:
        if isinstance(sources, list):
            snapshots.extend(
                snap for snap in sources
                if isinstance(snap, dict) and type(snap.get("id")) is int
            )
        slugs = raw.get("values_to_revisit", []) if isinstance(raw, dict) else []
        if isinstance(slugs, list):
            counts.update({s for s in slugs if isinstance(s, str) and s in values})

    item_ids = {snap["id"] for snap in snapshots}
    live_status = dict(ContentItem.objects.filter(pk__in=item_ids).values_list(
        "pk", "verification_status"))
    servable_ids = set(ContentItem.objects.servable().filter(
        pk__in=item_ids).values_list("pk", flat=True))
    for snap in snapshots:
        status = snap.get("verification_status")
        if status not in ("seeded", "reviewed"):
            continue
        if live_status.get(snap["id"]) == "unverified":
            continue
        if status != "reviewed" and snap["id"] not in servable_ids:
            continue
        names = snap.get("value_names", [])
        times = snap.get("times_discussed", 1)
        if not isinstance(names, list) or type(times) is not int or times < 1:
            continue
        for slug in {by_name[n] for n in names if isinstance(n, str) and n in by_name}:
            counts[slug] += times

    counts.update(ChildQuestProgress.objects.filter(
        child=child, status="completed", completed_at__date__gte=week_start,
        quest__value__isnull=False,
    ).values_list("quest__value__slug", flat=True))
    return [
        {"slug": slug, "name_en": values[slug].name_en,
         "name_ar": values[slug].name_ar, "count": count}
        for slug, count in sorted(counts.items(), key=lambda row: (-row[1], row[0]))
    ]
