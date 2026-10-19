"""Post-session pipeline: LLM report, message cleanup, rolling memory, AI quests.

Runs in a background thread from ``conversation.services.end_session`` (see
``run_post_session_pipeline``). Swap the thread for Celery later without
changing ``post_session_pipeline`` logic.
"""
from __future__ import annotations

import json
import logging
import re
import threading
import unicodedata
from typing import Any

from django.conf import settings
from django.db import IntegrityError, close_old_connections, transaction
from django.utils import timezone

from reporting.llm import call_llm
from reporting.models import ChildSessionMemory, SessionReport, WeeklySummary
from reporting.prompts import (
    QUEST_GENERATION_SYSTEM,
    QUEST_GENERATION_USER_TEMPLATE,
    ROLLING_SUMMARY_SYSTEM,
    ROLLING_SUMMARY_USER_TEMPLATE,
    SESSION_REPORT_SYSTEM,
    SESSION_REPORT_USER_TEMPLATE,
    WEEKLY_SUMMARY_SYSTEM,
    WEEKLY_SUMMARY_USER_TEMPLATE,
)

logger = logging.getLogger(__name__)

# --- Scripture post-filter (plan 7.5): generated text must never carry scripture ---
_SCRIPTURE_MARKERS = (
    "\ufd3e", "\ufd3f",  # ornate parentheses used around verses
    "قال رسول الله",
    "قال الله تعالى",
    "قال النبي",
    "ﷺ",
    "صلى الله عليه وسلم",
    "the prophet said",
    "(peace be upon him)",
    "allah says",
    "allah said",
    "the quran says",
)
# Fail-safe by design: neutral mentions such as "your child asked whether the
# Prophet said ..." are stripped too. Over-stripping is acceptable; leaking
# scripture-like text to parents or back into the agent context is not.
_SCRIPTURE_PATTERNS = (
    re.compile(r"prophet\b[^.]{0,40}\bsaid", re.IGNORECASE),
    re.compile(r"(قال|يقول|قالت)\s+[^.\n]{0,20}(النبي|رسول الله|الله تعالى)"),
)
_QURANIC_MARKS_RE = re.compile("[\u06d6-\u06ed]")
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?؟۔])\s+|\n+")
SCRIPTURE_FILTER_COUNTER = {"stripped": 0}


def contains_scripture_markers(text: str) -> bool:
    if not text:
        return False
    lowered = text.lower()
    if any(m in lowered for m in _SCRIPTURE_MARKERS):
        return True
    if any(p.search(text) for p in _SCRIPTURE_PATTERNS):
        return True
    return len(_QURANIC_MARKS_RE.findall(text)) >= 3


def strip_scripture_sentences(text: str, fallback: str = "") -> str:
    """Drop sentences containing scripture markers; return fallback if nothing is left."""
    if not text or not contains_scripture_markers(text):
        return text
    kept = [
        s for s in _SENTENCE_SPLIT_RE.split(text) if not contains_scripture_markers(s)
    ]
    SCRIPTURE_FILTER_COUNTER["stripped"] += 1
    logger.warning(
        "Scripture markers stripped from generated text (count=%s)",
        SCRIPTURE_FILTER_COUNTER["stripped"],
    )
    return " ".join(kept).strip() or fallback


def filter_suggested_topics(topics: list) -> list:
    """Drop suggested topics that contain scripture markers."""
    out = []
    for t in topics:
        if isinstance(t, str) and contains_scripture_markers(t):
            strip_scripture_sentences(t)  # counts and logs
            continue
        out.append(t)
    return out


# --- Child-text echo guard: parents never see the child's own words ---
_WORD_RE = re.compile(r"\w+", re.UNICODE)
_ECHO_RUN = 6  # this many consecutive words copied from one child message is an echo
_ECHO_MIN_WORDS = 4  # shorter child messages ("okay thanks") are too common to match


# Includes Persian yeh ی and kaf ک, which STT and keyboards mix with Arabic ي and ك.
_ARABIC_FOLD = str.maketrans("أإآٱىةیک", "اااايهيك")


# Echo-path sentence breaks: Arabic and CJK punctuation, ellipsis, newlines, bullets. Splits
# need no following space ("جدا؟لأن"), so a break never hides a clause from the remover.
# A "." between digits (3.5) is a decimal point, not a break.
_ECHO_SPLIT_RE = re.compile(r"(?<=[!?؟۔…؛،;。！？])|(?<=\.)(?<!\d\.)|(?<=\d\.)(?!\d)|[\n\r\u2028\u2029\u0085•·▪◦‣●]+")


def _norm_words(text) -> list[str]:
    """Words with Arabic spelling variants folded (hamza, harakat, tatweel, ى/ي, ة/ه) so STT and model spellings match.

    Invisible format characters (Unicode Cf: zero-width space/joiners, BOM, bidi marks, soft
    hyphen) are deleted, or they would split a word and hide an echo from the matcher.
    """
    text = unicodedata.normalize("NFKC", text or "")
    text = "".join(c for c in text if unicodedata.category(c) not in ("Mn", "Cf") and c != "\u0640")
    return _WORD_RE.findall(text.translate(_ARABIC_FOLD).casefold())


def _echo_keys(child_texts) -> set[str]:
    """Every run of up to _ECHO_RUN consecutive words of each child message, space padded."""
    keys = set()
    for text in child_texts:
        words = _norm_words(text)
        if len(words) < _ECHO_MIN_WORDS:
            continue
        k = min(len(words), _ECHO_RUN)
        for i in range(len(words) - k + 1):
            keys.add(" " + " ".join(words[i:i + k]) + " ")
    return keys


def echoes_child_text(text: str, keys: set[str]) -> bool:
    if not text or not keys:
        return False
    padded = " " + " ".join(_norm_words(text)) + " "
    return any(k in padded for k in keys)


def _echo_sentences(text: str) -> list[str]:
    return [p for p in (s.strip() for s in _ECHO_SPLIT_RE.split(text)) if p]


def _echoing_sentence_indexes(sentences: list[str], keys: set[str]) -> set[int]:
    """Indexes of every sentence that holds part of an echo, including one that spans sentences.

    Matches over the words of the whole text (the same windows echoes_child_text tests), then
    maps each hit back to the sentences it touches. Judging sentence by sentence would miss an
    echo split by a break, even though echoes_child_text(text) flagged it.
    """
    words: list[str] = []
    owner: list[int] = []
    for i, sentence in enumerate(sentences):
        w = _norm_words(sentence)
        words += w
        owner += [i] * len(w)
    hit: set[int] = set()
    for n in {len(k.split()) for k in keys}:
        for j in range(len(words) - n + 1):
            if " " + " ".join(words[j:j + n]) + " " in keys:
                hit.update(owner[j:j + n])
    return hit


def strip_child_echo(text: str, child_texts, fallback: str = "") -> str:
    """Drop sentences that copy the child's own words; return fallback if nothing is left."""
    keys = _echo_keys(child_texts)
    if not text or not echoes_child_text(text, keys):
        return text
    kept = _echo_sentences(text)
    while kept:  # repeat: removing a sentence can join its neighbours into a new echo
        hit = _echoing_sentence_indexes(kept, keys)
        if not hit:
            break
        kept = [s for i, s in enumerate(kept) if i not in hit]
    logger.warning("Child text echo stripped from generated text")
    return " ".join(kept).strip() or fallback


def filter_child_echo_topics(topics: list, child_texts) -> list:
    """Keep only string topics that do not echo the child; anything else is dropped (fail closed)."""
    keys = _echo_keys(child_texts)
    return [t for t in topics if isinstance(t, str) and not echoes_child_text(t, keys)]


PARENT_VIEW_KEY = "parent_view"


def _parent_view(raw: dict[str, Any], child_texts) -> dict[str, Any]:
    """Echo-free copy of the child-derived free text that later reaches the weekly LLM.

    Built while the session's messages still exist (they are deleted right after the
    report is saved). key_moments / memorable_facts in `raw` stay untouched: they are
    agent memory (rolling summary) and never shown to parents.
    """
    keys = _echo_keys(child_texts)
    emo = raw.get("emotional_progression")
    return {
        "emotional_progression": strip_child_echo(emo, child_texts) if isinstance(emo, str) else "",
        "themes_discussed": filter_child_echo_topics(
            [t for t in raw.get("themes_discussed") or [] if isinstance(t, str)], child_texts),
        "key_moments": [
            m for m in raw.get("key_moments") or []
            if isinstance(m, str) and not echoes_child_text(m, keys)
        ],
    }


def should_generate_quests_for_child(child, report: SessionReport) -> bool:
    """Hard gates only — whether MORE quests are actually useful is the LLM's
    decision (it sees the child's full open-quest board and may return "skip").

    Gates kept here: master switch, per-report idempotency, an open-quest
    backstop that avoids pointless LLM calls, and two legacy throttles that
    are now opt-in (daily cap, pending threshold).
    """
    from gamification.models import ChildQuestProgress, Quest

    if not settings.REPORTING_GENERATE_QUESTS:
        logger.info("Quest generation skipped: REPORTING_GENERATE_QUESTS is off")
        return False

    if Quest.objects.filter(is_ai_generated=True, session_report=report).exists():
        logger.info(
            "Quest generation skipped: AI quests already exist for report_id=%s",
            report.id,
        )
        return False

    max_open = settings.REPORTING_QUESTS_MAX_OPEN
    if max_open > 0:
        open_count = ChildQuestProgress.objects.filter(
            child=child,
            quest__is_ai_generated=True,
        ).exclude(status="completed").count()
        if open_count >= max_open:
            logger.info(
                "Quest generation skipped: child_id=%s has %s open AI quests "
                "(backstop=%s) — no LLM call needed",
                child.id,
                open_count,
                max_open,
            )
            return False

    if settings.REPORTING_QUESTS_SKIP_IF_PENDING:
        threshold = max(1, settings.REPORTING_QUESTS_MAX_PENDING)
        pending = ChildQuestProgress.objects.filter(
            child=child,
            quest__is_ai_generated=True,
            status__in=("not_started", "in_progress"),
        ).count()
        if pending >= threshold:
            logger.info(
                "Quest generation skipped: child_id=%s has %s pending AI quests (threshold=%s)",
                child.id,
                pending,
                threshold,
            )
            return False

    if settings.REPORTING_QUESTS_DAILY_CAP:
        day = timezone.localdate(report.created_at)
        if (
            Quest.objects.filter(
                is_ai_generated=True,
                session_report__session__child=child,
                session_report__created_at__date=day,
            )
            .exclude(session_report=report)
            .exists()
        ):
            logger.info(
                "Quest generation skipped: child_id=%s already has AI quests from another "
                "report on %s (daily cap)",
                child.id,
                day,
            )
            return False

    return True


def _open_quests_for_prompt(child) -> tuple[str, int]:
    """Full picture of the child's non-completed quests for the decision LLM."""
    from gamification.models import ChildQuestProgress

    now = timezone.now()
    rows = (
        ChildQuestProgress.objects.filter(child=child)
        .exclude(status="completed")
        .select_related("quest", "quest__session_report")
        .order_by("-id")
    )
    lines = []
    for p in rows:
        created = getattr(p.quest.session_report, "created_at", None)
        days_old = (now - created).days if created else "?"
        lines.append(
            f"- \"{p.quest.title}\" | type={p.quest.quest_type} | status={p.status} "
            f"| reward={p.quest.reward_points} pts | {days_old} day(s) old "
            f"| {p.quest.description[:140]}"
        )
    return ("\n".join(lines) if lines else "(none — the child's plate is empty)"), len(lines)


def _completed_quests_text_for_prompt(child, limit: int) -> str:
    from gamification.models import ChildQuestProgress

    if limit <= 0:
        return "(none)"
    rows = (
        ChildQuestProgress.objects.filter(child=child, status="completed")
        .select_related("quest")
        .order_by("-completed_at", "-id")[:limit]
    )
    lines = [f"- {p.quest.title}" for p in rows]
    return "\n".join(lines) if lines else "(none yet)"


def format_transcript(messages: list[dict[str, Any]]) -> str:
    lines = []
    for m in messages:
        lines.append(f"[{m['sender']}] ({m['input_type']}): {m['content']}")
    return "\n".join(lines)


def _fallback_report_data(messages: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(messages)
    child_count = sum(1 for m in messages if m.get("sender") == "child")
    return {
        "insight_summary": (
            f"Session contained {total} messages "
            f"({child_count} from child, {total - child_count} from system)."
        ),
        "recommendations": "",
        "raw_llm_output": {
            "fallback": True,
            "message_count": total,
        },
    }


# Plan s11 decision 8: the child's honesty is not graded. These legacy keys are never
# stored or shown to an LLM again; SessionReport.honesty_score stays null.
_LEGACY_HONESTY_KEYS = ("honesty_score", "honesty_indicators")
MAX_VALUES_TO_REVISIT = 3


# Devotional values are never offered to the session-report LLM for
# values_to_revisit: a parent summary must not read as a judgment of the child's
# religious practice. Quests still get the full list (the child may raise them).
DEVOTIONAL_VALUE_SLUGS = frozenset(
    {"prayer", "remembering-allah", "trust-in-allah", "love-of-the-prophet"}
)


def _value_choices(*, include_devotional: bool = False) -> dict[str, str]:
    """Bank value slug -> English name, in bank order."""
    from session_moral_context.models import Value

    qs = Value.objects.order_by("order", "slug")
    if not include_devotional:
        qs = qs.exclude(slug__in=DEVOTIONAL_VALUE_SLUGS)
    return dict(qs.values_list("slug", "name_en"))


def _values_list_text(values: dict[str, str]) -> str:
    return "\n".join(f"- {slug}: {name}" for slug, name in values.items()) or "(none)"


def clean_values_to_revisit(raw: Any, valid_slugs) -> list[str]:
    """Keep only known Value slugs (unknowns dropped), deduped, at most 3."""
    if not isinstance(raw, list):
        return []
    out: list[str] = []
    for slug in raw:
        slug = slug.strip().lower() if isinstance(slug, str) else ""
        if slug in valid_slugs and slug not in out:
            out.append(slug)
    return out[:MAX_VALUES_TO_REVISIT]


def _raw_for_prompt(report: SessionReport) -> dict[str, Any]:
    """raw_llm_output minus legacy honesty keys (old rows may still carry them) and the parent view."""
    return {
        k: v
        for k, v in (report.raw_llm_output or {}).items()
        if k not in _LEGACY_HONESTY_KEYS and k != PARENT_VIEW_KEY
    }


def _map_llm_to_report_fields(
    data: dict[str, Any], valid_slugs=()
) -> dict[str, Any] | None:
    if data.get("parse_error"):
        return None
    summary = (data.get("summary") or "").strip()
    rec = (data.get("recommendations") or "").strip()
    raw = {k: v for k, v in data.items() if k not in _LEGACY_HONESTY_KEYS}
    raw["values_to_revisit"] = clean_values_to_revisit(
        data.get("values_to_revisit"), valid_slugs
    )
    return {
        "insight_summary": summary,
        "recommendations": rec,
        "raw_llm_output": raw,
    }


def _generate_report_dict(messages: list[dict[str, Any]]) -> dict[str, Any]:
    if not messages:
        return _fallback_report_data(messages)
    try:
        transcript = format_transcript(messages)
        values = _value_choices()
        user = SESSION_REPORT_USER_TEMPLATE.format(
            values_list=_values_list_text(values),
            transcript=transcript,
        )
        data = call_llm(SESSION_REPORT_SYSTEM, user)
        mapped = _map_llm_to_report_fields(data, values)
        if mapped is None:
            return _fallback_report_data(messages)
        child_texts = [m["content"] for m in messages if m.get("sender") == "child"]
        for key in ("insight_summary", "recommendations"):
            mapped[key] = strip_child_echo(mapped[key], child_texts)
        # The weekly prompt prefers raw["summary"]/["recommendations"]; strip those copies too.
        # key_moments / memorable_facts are agent memory and stay untouched in raw;
        # parents' weekly input reads the echo-free parent_view instead.
        raw = mapped["raw_llm_output"]
        raw[PARENT_VIEW_KEY] = _parent_view(raw, child_texts)
        for key in ("summary", "recommendations"):
            if isinstance(raw.get(key), str):
                raw[key] = strip_child_echo(raw[key], child_texts)
        return mapped
    except Exception:
        logger.exception("LLM session report failed; using fallback")
        return _fallback_report_data(messages)


NEUTRAL_SUMMARY = "A conversation took place. / جرت محادثة."


def session_has_no_parent_flag(session) -> bool:
    from content_safety.models import NO_PARENT_NOTIFY_PREFIX, SafetyFlag
    from conversation.models import QUIET_AUDIT_MODE, TurnAudit

    # Either marker is enough: the audit row is written by the guard itself and survives a
    # skipped or failed SafetyFlag write.
    return (
        SafetyFlag.objects.filter(
            message__session=session,
            description__startswith=NO_PARENT_NOTIFY_PREFIX,
        ).exists()
        or TurnAudit.objects.filter(session=session, mode=QUIET_AUDIT_MODE).exists()
    )


def _neutral_report_data() -> dict[str, Any]:
    """Report for a no-parent-notify session: no LLM, no transcript, no detail."""
    return {
        "insight_summary": NEUTRAL_SUMMARY,
        "recommendations": "",
        "raw_llm_output": {
            "neutral": True,
            "summary": NEUTRAL_SUMMARY,
            "key_moments": [],
            "memorable_facts": [],
            "safety_notes": [],
        },
    }


def _is_neutral(report: SessionReport) -> bool:
    return bool((report.raw_llm_output or {}).get("neutral"))


def _cleanup_messages(session) -> None:
    from content_safety.models import SafetyFlag
    from conversation.models import Message

    flagged_message_ids = SafetyFlag.objects.filter(
        message__session=session,
    ).values_list("message_id", flat=True)
    Message.objects.filter(session=session).exclude(
        id__in=flagged_message_ids,
    ).delete()


def _update_rolling_summary(report: SessionReport) -> None:
    if _is_neutral(report):
        return
    child = report.session.child
    existing_obj, _ = ChildSessionMemory.objects.get_or_create(child=child)
    existing = existing_obj.rolling_summary or ""
    report_json = json.dumps(
        _raw_for_prompt(report),
        ensure_ascii=False,
        indent=2,
    )
    try:
        user = ROLLING_SUMMARY_USER_TEMPLATE.format(
            existing_summary=existing or "(none yet)",
            report_json=report_json,
        )
        data = call_llm(ROLLING_SUMMARY_SYSTEM, user)
        new_summary = (data.get("rolling_summary") or "").strip()
        new_summary = strip_scripture_sentences(new_summary).strip()
        if not new_summary:
            return
        existing_obj.rolling_summary = new_summary[:20000]
        existing_obj.save()
    except Exception:
        logger.exception("Rolling summary LLM failed for child_id=%s", child.id)


def _generate_quests_for_report(report: SessionReport, child_texts=()) -> None:
    from gamification.models import ChildQuestProgress, Quest
    from session_moral_context.models import MoralTheme, Value

    if _is_neutral(report):
        return
    child = report.session.child
    if not should_generate_quests_for_child(child, report):
        return

    current_year = timezone.now().year
    child_age = (current_year - child.birth_year) if child.birth_year else "unknown"

    report_json = json.dumps(
        {
            "insight_summary": report.insight_summary,
            "recommendations": report.recommendations,
            "values_to_revisit": (report.raw_llm_output or {}).get("values_to_revisit", []),
            "raw": _raw_for_prompt(report),
        },
        ensure_ascii=False,
        indent=2,
    )
    open_quests, open_count = _open_quests_for_prompt(child)
    completed_quests = _completed_quests_text_for_prompt(
        child, settings.REPORTING_QUESTS_RECENT_LIMIT
    )
    try:
        values = _value_choices(include_devotional=True)
        user = QUEST_GENERATION_USER_TEMPLATE.format(
            values_list=_values_list_text(values),
            child_age=child_age,
            report_json=report_json,
            open_count=open_count,
            open_quests=open_quests,
            completed_quests=completed_quests,
        )
        data = call_llm(QUEST_GENERATION_SYSTEM, user)

        decision = (data.get("decision") or "add").strip().lower()
        if decision == "skip":
            logger.info(
                "Quest generation: LLM decided to skip for child_id=%s (open=%s)",
                child.id,
                open_count,
            )
            return

        quests = data.get("quests") or []
        if not isinstance(quests, list):
            return
        for item in quests[:3]:
            if not isinstance(item, dict):
                continue
            title = (item.get("title") or "").strip()[:100]
            if not title:
                continue
            desc = (item.get("description") or "").strip()[:2000]
            if contains_scripture_markers(title):
                strip_scripture_sentences(title)
                continue
            desc = strip_scripture_sentences(desc, "Talk it through with Al-Sadiq next time.")
            # Parents see quests: drop any title/sentence that copies the child's own words.
            title = strip_child_echo(title, child_texts)
            if not title:
                continue
            desc = strip_child_echo(desc, child_texts, "Talk it through with Al-Sadiq next time.")
            try:
                points = int(item.get("reward_points", 10))
            except (TypeError, ValueError):
                points = 10
            points = max(5, min(50, points))
            # value_slug must be one of the bank slugs offered; anything else is null.
            slug = (item.get("value_slug") or "").strip().lower()
            value = Value.objects.filter(slug=slug).first() if slug in values else None
            # Legacy theme FK: lookup only, keyed on the Value's name. The LLM's
            # free text never creates or picks a MoralTheme.
            moral_theme = (
                MoralTheme.objects.filter(name__iexact=value.name_en).first()
                if value else None
            )
            quest_type = (item.get("quest_type") or "").strip()
            if quest_type not in ("conversation", "real_world", "reflection"):
                quest_type = "real_world"
            verification = {
                "conversation": "companion",
                "real_world": "parent",
                "reflection": "self",
            }[quest_type]
            quest = Quest.objects.create(
                title=title,
                description=desc,
                reward_points=points,
                quest_type=quest_type,
                verification_method=verification,
                moral_theme=moral_theme,
                value=value,
                session_report=report,
                is_ai_generated=True,
            )
            ChildQuestProgress.objects.get_or_create(
                child=child,
                quest=quest,
                defaults={"status": "not_started"},
            )
    except Exception:
        logger.exception("Quest generation failed for report_id=%s", report.id)


def _arabic_sessions_phrase(count: int) -> str:
    """The count of sessions with correct Arabic number agreement (one, two, 3-10, 11+)."""
    if count == 0:
        return "لا جلسات"
    if count == 1:
        return "جلسة واحدة"
    if count == 2:
        return "جلستان"
    if 3 <= count <= 10:
        return f"{count} جلسات"
    return f"{count} جلسة"


def _fallback_weekly_summary(session_count: int, lang: str = "en") -> dict[str, Any]:
    """Plain summary used when the model fails or returns nothing usable.

    `lang` is the child's language preference; anything but "ar" gets the English text.
    """
    if (lang or "en").lower().startswith("ar"):
        summary = (
            f"كان لطفلك {_arabic_sessions_phrase(session_count)} هذا الأسبوع. "
            "سيتوفر ملخص مفصّل قريبًا."
        )
    else:
        summary = (
            f"Your child had {session_count} session(s) this week. "
            "A detailed summary will be available soon."
        )
    return {"summary": summary, "suggested_topics": []}


def _build_reports_json(week_reports) -> str:
    items = []
    for r in week_reports:
        raw = r.raw_llm_output or {}
        if raw.get("neutral"):
            items.append({"summary": "A session took place."})
            continue
        # Child-derived free text comes only from the write-time echo-filtered copy. Rows
        # without one (older reports; their messages are gone) get none: fail closed.
        view = raw.get(PARENT_VIEW_KEY) if isinstance(raw.get(PARENT_VIEW_KEY), dict) else {}
        items.append({
            "themes_discussed": view.get("themes_discussed", []),
            "emotional_progression": view.get("emotional_progression", ""),
            "key_moments": view.get("key_moments", []),
            "recommendations": raw.get("recommendations", r.recommendations),
            "summary": raw.get("summary", r.insight_summary),
            "values_to_revisit": raw.get("values_to_revisit", []),
        })
    return json.dumps(items, ensure_ascii=False, indent=2)


def _update_weekly_summary(report: SessionReport) -> None:
    from authentication.models import ParentChildLink
    from datetime import timedelta

    if not settings.REPORTING_GENERATE_WEEKLY_SUMMARY:
        logger.info("Weekly summary generation skipped: REPORTING_GENERATE_WEEKLY_SUMMARY is off")
        return

    child = report.session.child
    report_date = timezone.localdate(report.created_at)
    week_start = report_date - timedelta(days=report_date.weekday())  # Monday

    parent_links = ParentChildLink.objects.filter(
        child=child, consent_status="approved",
    ).select_related("parent")
    if not parent_links.exists():
        logger.info(
            "Weekly summary skipped: no approved parents for child_id=%s", child.id
        )
        return

    throttle_hours = settings.REPORTING_WEEKLY_SUMMARY_THROTTLE_HOURS
    if throttle_hours > 0:
        cutoff = timezone.now() - timedelta(hours=throttle_hours)
        if WeeklySummary.objects.filter(
            child=child,
            week_start=week_start,
            updated_at__gte=cutoff,
        ).exists():
            logger.info(
                "Weekly summary skipped: child_id=%s has fresh summary within %sh throttle window",
                child.id,
                throttle_hours,
            )
            return

    week_reports = list(
        SessionReport.objects.filter(
            session__child=child,
            created_at__date__gte=week_start,
            created_at__date__lt=week_start + timedelta(days=7),
        ).order_by("created_at")
    )
    if not week_reports:
        return

    lang = getattr(child, "language_preference", "en") or "en"
    current_year = timezone.now().year
    child_age = (current_year - child.birth_year) if child.birth_year else "unknown"

    try:
        reports_json = _build_reports_json(week_reports)
        user_content = WEEKLY_SUMMARY_USER_TEMPLATE.format(
            nickname=child.nickname,
            age=child_age,
            week_start=week_start.isoformat(),
            session_count=len(week_reports),
            reports_json=reports_json,
        )
        data = call_llm(WEEKLY_SUMMARY_SYSTEM, user_content)
        summary_text = (data.get("summary") or "").strip()
        suggested_topics = data.get("suggested_topics") or []
        if not isinstance(suggested_topics, list):
            suggested_topics = []
        fallback_text = _fallback_weekly_summary(len(week_reports), lang)["summary"]
        summary_text = strip_scripture_sentences(summary_text, fallback_text)
        suggested_topics = filter_suggested_topics(suggested_topics)
        from conversation.models import Message
        child_texts = list(Message.objects.filter(
            session__in=[r.session_id for r in week_reports], sender="child",
        ).values_list("content", flat=True))
        summary_text = strip_child_echo(summary_text, child_texts, fallback_text)
        suggested_topics = filter_child_echo_topics(suggested_topics, child_texts)
        if not summary_text:
            fallback = _fallback_weekly_summary(len(week_reports), lang)
            summary_text = fallback["summary"]
            suggested_topics = fallback["suggested_topics"]
    except Exception:
        logger.exception("Weekly summary LLM failed for child_id=%s", child.id)
        fallback = _fallback_weekly_summary(len(week_reports), lang)
        summary_text = fallback["summary"]
        suggested_topics = fallback["suggested_topics"]

    for link in parent_links:
        try:
            ws, _ = WeeklySummary.objects.update_or_create(
                child=child,
                parent=link.parent,
                week_start=week_start,
                defaults={
                    "summary": summary_text,
                    "suggested_topics": suggested_topics,
                },
            )
            ws.sessions.set(week_reports)
        except Exception:
            logger.exception(
                "Failed to save WeeklySummary for child_id=%s parent_id=%s",
                child.id,
                link.parent_id,
            )


# ---------------------------------------------------------------------------
# Parent-facing sources and "questions to discuss" (task 04). Database only.
# ---------------------------------------------------------------------------

TRUST_LINE = {
    "en": (
        "Verses and hadith shown on a source card come from approved sources; "
        "explanations are AI-generated and simplified."
    ),
    "ar": (
        "الآيات والأحاديث المعروضة في بطاقات المصدر مأخوذة من مصادر معتمدة، "
        "أما الشروح فيولّدها الذكاء الاصطناعي بصورة مبسّطة."
    ),
}
SUMMARY_LABEL = {
    "en": "Written by AI from the week's sessions; may contain mistakes",
    "ar": "كُتب بواسطة الذكاء الاصطناعي من جلسات الأسبوع، وقد يحتوي على أخطاء",
}
SUGGESTED_TOPICS_LABEL = {
    "en": "Suggested by AI",
    "ar": "اقتراحات من الذكاء الاصطناعي",
}
REVIEWED_LABEL = {
    "en": "Checked against the source by our team",
    "ar": "طابقه فريقنا مع المصدر",
}
NOT_SCHOLAR_REVIEWED_LABEL = {
    "en": "Not reviewed by a scholar",
    "ar": "لم يراجعه عالم",
}
SOURCES_FOOTER = {
    "en": "Reviewed means checked against the source by our team, not reviewed by a scholar.",
    "ar": "«مُراجَع» يعني أن فريقنا طابقه مع المصدر، ولا يعني أن عالمًا راجعه.",
}
NO_SOURCES_LABEL = {
    "en": "No sources were used this week",
    "ar": "لم تُستخدم مصادر هذا الأسبوع",
}
QUESTIONS_TITLE = {
    "en": "Questions Al-Sadiq asked you to discuss",
    "ar": "أسئلة طلب منك الصديق مناقشتها مع طفلك",
}
REFERRAL_MODES = ("REFER", "DISAGREE_AND_REFER", "DECLINE_NO_SOURCE")
QUESTION_LEVEL_LABEL = {
    "en": {
        "D": "a question about your family's own situation",
        "C": "scholars differ on the details",
    },
    "ar": {
        "D": "سؤال عن وضع أسرتك الخاص",
        "C": "العلماء يختلفون في التفاصيل",
    },
}
QUESTION_DEFAULT_LABEL = {
    "en": "a question Al-Sadiq sent to you",
    "ar": "سؤال أحاله إليك الصديق",
}
QUESTIONS_CAP = 5


def _snapshot_item(item, value_names: list[str], times: int) -> dict[str, Any]:
    from conversation.agent.retrieval import replace_verse_markers

    # Verse items keep their text; other excerpts never show a raw {{verse:S:A}} marker.
    plain = (lambda t, lang: t) if item.type == "verse" else replace_verse_markers
    return {
        "id": item.pk,
        "type": item.type,
        "kind": "scripture" if item.type in ("verse", "hadith") else "source_excerpt",
        "arabic_text": plain(item.arabic_text, "ar"),
        "english_text": plain(item.english_text, "en"),
        "translation_name": item.translation_name,
        "translation_source_url": item.translation_source_url,
        "surah": item.surah,
        "ayah": item.ayah,
        "book": item.book,
        "number": item.number,
        "grade": item.grade,
        "grader": item.grader,
        "source_site": item.source_site,
        "source_url": item.source_url,
        "content_level": item.content_level,
        # Same as the child payload: verse cards carry no title; no raw markers in either field.
        "title": "" if item.type == "verse" else plain(item.title_ar or item.title_en, "ar"),
        "disagreement_note": plain(item.disagreement_note_ar or item.disagreement_note_en, "ar"),
        "verification_status": item.verification_status,
        "value_name": value_names[0] if value_names else "",
        "value_names": value_names,
        "times_discussed": times,
    }


def build_sources_snapshot(session) -> list[dict[str, Any]]:
    """Snapshot of the items served in a session, from ServedReference only.

    One entry per item; ``times_discussed`` counts the session's references.
    Child explanations are deliberately left out (child tier). Never raises.
    """
    try:
        from collections import Counter

        from session_moral_context.models import ServedReference

        refs = list(
            ServedReference.objects.filter(session=session)
            .select_related("item")
            .order_by("served_at", "pk")
        )
        counts = Counter(r.item_id for r in refs)
        items = {}
        for r in refs:
            items.setdefault(r.item_id, r.item)
        out = []
        for item_id, item in items.items():
            names = list(
                item.values.order_by("valueitem__order", "slug")
                .values_list("name_en", flat=True)
            )
            out.append(_snapshot_item(item, names, counts[item_id]))
        return out
    except Exception:
        logger.exception("build_sources_snapshot failed for session %s", session.pk)
        return []


def _week_start_today():
    from datetime import timedelta

    today = timezone.localdate()
    return today - timedelta(days=today.weekday())


def weekly_sources(child) -> list[dict[str, Any]]:
    """This week's unique sources for a child, deduped by item id.

    Built from ``SessionReport.sources_used`` snapshots. An entry is kept only
    if it was ``reviewed`` at snapshot time, or is still servable now; entries
    whose live item is currently unverified, or that were unverified in the
    snapshot, are dropped. Seeded verses therefore show while they stay
    servable. Missing live items fall back to the snapshot rule.
    """
    from session_moral_context.models import ContentItem

    reports = SessionReport.objects.filter(
        session__child=child,
        session__started_at__date__gte=_week_start_today(),
    ).order_by("session__started_at")
    merged: dict[int, dict[str, Any]] = {}
    for report in reports:
        for snap in report.sources_used or []:
            if not isinstance(snap, dict) or "id" not in snap:
                continue
            cur = merged.get(snap["id"])
            if cur is None:
                merged[snap["id"]] = dict(snap, times_discussed=snap.get("times_discussed", 1))
            else:
                cur["times_discussed"] += snap.get("times_discussed", 1)
    if not merged:
        return []
    live = {i.pk: i for i in ContentItem.objects.filter(pk__in=merged)}
    servable_ids = set(
        ContentItem.objects.servable().filter(pk__in=merged).values_list("pk", flat=True)
    )
    out = []
    for item_id, snap in merged.items():
        status = snap.get("verification_status")
        if status not in ("seeded", "reviewed"):
            continue
        item = live.get(item_id)
        if item is not None and item.verification_status == "unverified":
            continue
        if status != "reviewed" and item_id not in servable_ids:
            continue
        if item is not None and "disagreement_note" not in snap:
            # Snapshots written before title/note existed: fill them from the live item,
            # so a level-C source the child saw this week is not dropped on the parent page.
            fresh = _snapshot_item(item, [], 0)
            snap = {**snap, "title": fresh["title"], "disagreement_note": fresh["disagreement_note"]}
        out.append(snap)
    out.sort(key=lambda s: (-s["times_discussed"], s["id"]))
    return out


def questions_to_discuss(child) -> list[dict[str, Any]]:
    """Neutral list of turns where Sadiq referred the child to a parent.

    Uses TurnAudit labels only: never message text. Rows with safety=True are
    excluded entirely, as are all rows of a session that has a safety Alert or
    a SafetyFlag (second guard). Grouped by topic (value name from served
    items), newest first, capped at QUESTIONS_CAP.
    """
    from django.db.models import Q

    from content_safety.models import Alert, SafetyFlag
    from conversation.models import Session, TurnAudit
    from session_moral_context.models import Value

    session_ids = list(
        Session.objects.filter(
            child=child, started_at__date__gte=_week_start_today()
        ).values_list("pk", flat=True)
    )
    if not session_ids:
        return []
    flagged = set(
        Alert.objects.filter(session_id__in=session_ids, alert_type="safety")
        .values_list("session_id", flat=True)
    ) | set(
        SafetyFlag.objects.filter(message__session_id__in=session_ids)
        .values_list("message__session_id", flat=True)
    )
    audits = (
        TurnAudit.objects.filter(session_id__in=session_ids, safety=False)
        .filter(Q(level="D") | Q(mode__in=REFERRAL_MODES))
        .exclude(session_id__in=flagged)
        .exclude(mode__in=("SAFETY", "SAFETY_QUIET"))  # belt and braces: the guard's safety modes
        .order_by("-created_at")
    )
    groups: dict[str, dict[str, Any]] = {}
    for a in audits:
        ids = [i for i in (a.served_item_ids or []) if isinstance(i, int)]
        value = None
        if ids:
            value = (
                Value.objects.filter(items__pk__in=ids).order_by("order", "slug").first()
            )
        key = value.slug if value else ""
        g = groups.get(key)
        if g is None:
            level_label = QUESTION_LEVEL_LABEL
            g = groups[key] = {
                "topic": key,
                "topic_en": value.name_en if value else "",
                "topic_ar": value.name_ar if value else "",
                "mode": a.mode,
                "level": a.level,
                "description_en": level_label["en"].get(a.level, QUESTION_DEFAULT_LABEL["en"]),
                "description_ar": level_label["ar"].get(a.level, QUESTION_DEFAULT_LABEL["ar"]),
                "date": timezone.localtime(a.created_at).date().isoformat(),
                "count": 0,
            }
        g["count"] += 1
    return list(groups.values())[:QUESTIONS_CAP]


def post_session_pipeline(session_id: int) -> None:
    from conversation.models import Message, Session

    try:
        close_old_connections()
        session = Session.objects.select_related("child").get(pk=session_id)
        if session.status != "ended":
            logger.warning(
                "post_session_pipeline: session %s not ended, skipping",
                session_id,
            )
            return

        messages = list(
            Message.objects.filter(session=session)
            .order_by("created_at")
            .values("sender", "content", "input_type", "created_at")
        )
        logger.info(
            "post_session_pipeline: session_id=%s message_count=%s before report",
            session_id,
            len(messages),
        )

        if session_has_no_parent_flag(session):
            report_defaults = _neutral_report_data()
        else:
            report_defaults = _generate_report_dict(messages)
        # Sources come from the database (ServedReference), never from the LLM.
        report_defaults["sources_used"] = build_sources_snapshot(session)

        with transaction.atomic():
            report, _ = SessionReport.objects.update_or_create(
                session=session,
                defaults=report_defaults,
            )

        _cleanup_messages(session)
        _update_rolling_summary(report)
        _generate_quests_for_report(
            report, [m["content"] for m in messages if m.get("sender") == "child"]
        )
        _update_weekly_summary(report)

        try:
            from gamification.services import evaluate_badges

            evaluate_badges(session.child)
        except Exception:
            logger.exception(
                "Badge evaluation failed for child_id=%s", session.child_id
            )

    except Session.DoesNotExist:
        logger.error("post_session_pipeline: session %s not found", session_id)
    except IntegrityError:
        # A demo "Start fresh" (or an account delete, which cascades) can remove the
        # session while this thread is still writing its report. That is not a failure.
        if _session_is_gone(session_id):
            logger.info(
                "post_session_pipeline: session %s deleted before its report was saved; skipped",
                session_id,
            )
        else:
            _log_pipeline_failure(session_id)
    except Exception:
        _log_pipeline_failure(session_id)
    finally:
        close_old_connections()


def _session_is_gone(session_id: int) -> bool:
    from conversation.models import Session

    try:
        return not Session.objects.filter(pk=session_id).exists()
    except Exception:
        return False


def _log_pipeline_failure(session_id: int) -> None:
    """Log the failure with its traceback (call from inside an except block), then clean up."""
    from conversation.models import Session

    logger.exception("post_session_pipeline failed for session %s", session_id)
    try:
        sess = Session.objects.get(pk=session_id)
        _cleanup_messages(sess)
    except Exception:
        logger.exception(
            "post_session_pipeline: cleanup after failure failed session %s",
            session_id,
        )


def run_post_session_pipeline(session_id: int) -> None:
    thread = threading.Thread(
        target=post_session_pipeline,
        args=(session_id,),
        daemon=True,
        name=f"post_session_pipeline_{session_id}",
    )
    thread.start()
