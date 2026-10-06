"""The ``search_bank`` tool's lookup and result text (hk/12 hybrid companion).

Pure: no DB, no network. The model calls the tool with a question, a topic and optionally
value names; ``search`` ranks the session's in-memory ``ValueIndex``; ``format_result`` writes
what the model sees. A verse's Arabic and a source excerpt never appear (``retrieval._llm_text``
enforces that); the card on screen carries them once the model cites the item with
``{{card:ID}}``.
"""
from __future__ import annotations

from functools import lru_cache
from itertools import zip_longest
from pathlib import Path
from typing import Mapping

from .retrieval import (
    MAX_ITEMS, _TYPE_RANK, _explanation, _llm_text, citation, item_level, items_for_values,
    match_values, replace_verse_markers,
)
from .text_match import make_term, term_in, token_forms

GUIDANCE_DIR = Path(__file__).resolve().parent / "guidance"
MAX_RESULT_WORDS = 300

TOPICS = ("values", "quran", "hadith", "creed", "afterlife", "worship", "prophets_story", "word_meaning", "comfort")
TOPIC_TYPES = {
    "hadith": ("hadith",),
    "quran": ("verse", "tafsir"),
    "creed": ("aqidah", "faq", "verse"),
    "worship": ("fiqh", "faq"),
    "prophets_story": ("sirah", "story"),
    "word_meaning": ("term",),
    "afterlife": ("aqidah", "faq", "verse", "hadith"),
    "values": ("verse", "hadith"),
    "comfort": ("verse",),   # only the COMFORT set below, never keyword matches
}
# The topic's own guidance file (the others have none: their type file is enough).
TOPIC_GUIDANCE = {"creed": "creed", "afterlife": "afterlife", "worship": "fiqh", "prophets_story": "story",
                  "comfort": "comfort"}

NOT_FOUND = ("NOT FOUND. Nothing verified in the library for this. Do not state any Islamic fact, "
             "verse, hadith, du'a wording or story.")


def _topic(topic: str) -> str:
    t = (topic or "").strip().lower().replace(" ", "_").replace("-", "_")
    return t if t in TOPIC_TYPES else "values"


RELATED_TYPES = ("verse", "hadith")   # what a related-item fallback may offer
RELATED_MAX = 2
# What the child asked for, in the header of a related-item result ("NO verse FOUND for this").
ASKED = {"quran": "verse", "hadith": "hadith", "values": "verse or hadith", "creed": "creed item",
         "afterlife": "afterlife item", "worship": "worship item", "prophets_story": "story",
         "word_meaning": "word meaning", "comfort": "comfort verse"}


class Results(list):
    """The items ``search`` found. ``related`` is True when they are NOT of the kind asked for:
    the topic filter left nothing, and these come from the same value (see ``search``)."""
    related = False


def _value_slugs(index, values) -> list[str]:
    """Slugs of the values the model named, at most two, one per name, in the model's order.

    A name matches a value loosely: by its slug or its English or Arabic name, else by one of the value's
    keywords (case, Arabic diacritics, ال/و/ب clitics and singular/plural do not matter: ``text_match``).
    "honest", "الصدق" and "truthfulness" (once a keyword) all find honesty. Unknown names are ignored.
    """
    out: list[str] = []
    for raw in values or []:
        name = str(raw).strip()
        tf = token_forms(name)
        if not tf:
            continue
        best, best_score = None, 0
        for v in index.values:
            named = [make_term((v.slug or "").replace("-", " ")), make_term(v.name_en or ""), make_term(v.name_ar or "")]
            score = 100 if any(t and term_in(t, tf) for t in named) else sum(
                t.weight for t in v.terms if term_in(t, tf))  # weak words (mom, friend) never name a value alone
            if score > best_score:   # strict: on a tie the earlier value (index order) wins
                best, best_score = v.slug, score
        if best and best not in out:
            out.append(best)
    return out[:2]


def _gather(index, question, slugs, lang, age_band, types) -> list:
    """Candidates of the given types: the question's keyword matches and the named values' items.

    The named values' items are interleaved (one value's best, the next value's best, ...). Ranked
    reviewed first, then items both the question and a named value point to, then verse before
    hadith, then having an explanation in the session language."""
    matched = list(match_values(question, lang, age_band, index, types=types))
    per_value = [[it for it in items_for_values(index, [slug], lang, age_band, limit=len(index.items))
                  if it.type in types] for slug in slugs]
    named: list = []
    for row in zip_longest(*per_value):
        named += [it for it in row if it is not None and it.pk not in {n.pk for n in named}]
    found = matched + [it for it in named if it.pk not in {m.pk for m in matched}]
    both = {it.pk for it in matched} & {it.pk for it in named}
    lang_attr = "child_explanation_ar" if lang == "ar" else "child_explanation_en"
    pool = [it for it in found if not (age_band == "6-9" and index.items[it.pk].age_band == "10-13")]
    # stable: items the question itself matched stay ahead of the rest on equal keys
    pool.sort(key=lambda o: (
        0 if index.items[o.pk].reviewed else 1,
        0 if o.pk in both else 1,
        _TYPE_RANK.get(o.type, 2),
        0 if getattr(o, lang_attr, "") else 1,
    ))
    return pool


NAMED_VALUE_ONLY = frozenset({"creed", "word_meaning", "prophets_story"})

# Comfort verses (hk/13b, lead decision): for a sad, scared, worried or grieving child, a fixed set of
# reviewed bank verses chosen by reference, never by keyword. The feeling words below only order the set.
# (feeling, words in the model's question, (surah, ayah) best first); the last row is the default.
COMFORT = (
    ("grief", ("died", "dead", "death", "passed away", "miss", "مات", "ماتت", "توفي", "توفت", "متوفي", "الموت",
               "اشتقت", "فقدت"), ((2, 153), (13, 28))),
    ("fear", ("scared", "afraid", "fear", "dark", "nightmare", "خايف", "خايفة", "أخاف", "خوف", "الظلام", "كابوس"),
     ((20, 46), (13, 28))),
    ("worry", ("worried", "worry", "nervous", "stress", "stressed", "exam", "test", "قلق", "قلقان", "متوتر",
               "امتحان", "اختبار"), ((65, 3), (13, 28))),
    ("hardship", ("hard", "sick", "ill", "tired", "صعب", "تعبان", "تعبانة", "مريض", "مريضة"), ((39, 10), (2, 153))),
    ("sadness", (), ((13, 28), (3, 139))),
)
# Disclosures get the safety rules, never a comfort verse, even before the model flags the turn. Comfort only:
# the turn guard and flag_safety_concern stay the safety net.
COMFORT_BLOCK = (
    "secret", "secrets", "don't tell", "dont tell", "keep it between us", "between us", "no one must know",
    "nobody can know", "hits me", "hit me", "hitting me", "beats me", "he hurt me", "hurt me", "hurts me",
    "he smacked me", "smacked me", "touched me", "touch me", "touches me", "kiss me", "kisses me",
    "take off my clothes", "clothes", "in front of him", "photos", "photo", "pictures of me", "photos of me",
    "pics", "kill myself", "hurt myself", "want to die",
    "سر", "سري", "أسرار", "لا تقول", "لا تقولي", "لا تخبر", "لا تخبر أحد", "ما أقول لأحد", "ما تقول لماما",
    "ما تقول لبابا", "يضربني", "يضربوني", "ضربني", "ضربوني", "تضربني", "يؤذيني", "يأذيني", "يلمسني", "لمسني",
    "صور", "صورة", "صوري", "صورني", "صور لي", "أقتل نفسي", "اقتل نفسي", "أذيت نفسي", "آذي نفسي", "أؤذي نفسي",
    "أبي أموت", "أبغى أموت", "بدي موت",
)


def comfort_blocked(*texts: str) -> bool:
    """True when the child's words or the model's question disclose a secret, being hit or touched, or
    self-harm: no comfort verse on such a turn."""
    tf = token_forms(" ".join(t or "" for t in texts))
    return any(term_in(make_term(w), tf) for w in COMFORT_BLOCK)


def comfort(index, question: str, age_band: str | None = None) -> Results:
    """Up to 2 reviewed verses of the COMFORT set, the best for the feeling in ``question`` first."""
    tf = token_forms(question or "")
    refs = next(r for _f, words, r in COMFORT if not words or any(term_in(make_term(w), tf) for w in words))
    out = Results()
    for ref in refs:
        obj = index.verses.get(ref)
        it = index.items.get(obj.pk) if obj is not None else None
        if it and it.reviewed and not (age_band == "6-9" and it.age_band == "10-13"):
            out.append(it.obj)
    return out


def search(index, question: str, topic: str, values, lang: str = "en",
           age_band: str | None = None) -> Results:
    """Up to 3 servable ContentItems for the question, empty when the bank has nothing.

    Candidates are the question's keyword matches plus the items of the values the model named. The
    topic keeps its own item types. When it leaves nothing but a verse or hadith of the same
    value(s) exists, up to 2 of those come back as ``Results(related=True)`` so the model can
    say it found no verse and still offer the hadith.
    """
    if not index:
        return Results()
    if _topic(topic) == "comfort":
        return comfort(index, question, age_band)
    allowed = TOPIC_TYPES[_topic(topic)]
    slugs = _value_slugs(index, values)
    pool = _gather(index, question, slugs, lang, age_band, allowed)
    if pool:
        return Results(pool[:MAX_ITEMS])
    others = tuple(t for t in RELATED_TYPES if t not in allowed)
    related = _gather(index, question, slugs, lang, age_band, others) if others else []
    if _topic(topic) in NAMED_VALUE_ONLY:
        # a creed, word or story question: offer only items of the values the model named, so
        # "RELATED items from the same value" is true (review of #76)
        related = [it for it in related if set(slugs) & set(index.items[it.pk].value_slugs)]
    out = Results(related[:RELATED_MAX])
    out.related = bool(out)
    return out


@lru_cache(maxsize=1)
def load_guidance() -> Mapping[str, str]:
    """name -> text of every ``guidance/*.md`` (empty when the folder is missing)."""
    try:
        return {p.stem: p.read_text(encoding="utf-8").strip() for p in GUIDANCE_DIR.glob("*.md")}
    except OSError:
        return {}


def guidance_names(items, topic: str) -> list[str]:
    """Which guidance files go with this result, at most two (precedence in the plan, section 3)."""
    topic_file = TOPIC_GUIDANCE.get(_topic(topic))
    if not items:
        return ["no_source"] + ([topic_file] if topic_file else [])
    names = [topic_file] if topic_file else []
    if any(item_level(it) == "C" for it in items):
        names.append("disagreement")
    elif any(it.type == "verse" for it in items):
        names.append("verse")
    elif any(it.type == "hadith" for it in items):
        names.append("hadith")
    return names[:2]


def _words(s: str) -> int:
    return len(s.split())


def _clip(s: str, n: int) -> str:
    w = (s or "").split()
    return " ".join(w) if len(w) <= n else " ".join(w[:n]).rstrip(" ,.;:") + "..."


def card_hint(turns_since_card: int | None) -> str:
    """How long ago a source card was last shown, so the model can space them out (None: none yet)."""
    if turns_since_card is None:
        return "No card shown yet this session."
    return ("Last card shown: this turn." if turns_since_card == 0 else
            f"Last card shown: {turns_since_card} turn{'s' if turns_since_card != 1 else ''} ago.")


def format_result(items, lang: str, age_band: str | None, topic: str,
                  found_guidance: Mapping[str, str] | None = None, turns_since_card: int | None = None) -> str:
    """The tool's answer to the model, at most ~300 words."""
    guide = found_guidance if found_guidance is not None else load_guidance()
    texts = [guide[n] for n in guidance_names(items, topic) if guide.get(n)]
    tail = "GUIDANCE:\n" + "\n".join(texts) if texts else ""
    if not items:
        return NOT_FOUND + ("\n" + tail if tail else "")
    lead = (f"NO {ASKED[_topic(topic)]} FOUND for this; RELATED items from the same value:"
            if getattr(items, "related", False) else f"FOUND {len(items)}.")
    head = (f"{lead} {card_hint(turns_since_card)} Only these may be quoted or attributed this turn. Say only "
            "what their simple explanations say: add no reasons, examples or claims of your own.")
    most = 1 if _topic(topic) == "comfort" else 2
    foot = (f"Show an item by writing its marker exactly as shown, where you mention it (at most {most}). "
            "Then say simply what it means and its value, from its simple explanation; never read or reword it.")
    budget = MAX_RESULT_WORDS - _words(head) - _words(foot) - _words(tail)
    each = max(25, budget // len(items))
    lines = []
    for it in items:
        label = "{{card:%d}}" % it.pk  # the exact marker: if the model echoes it, it is the right form
        fixed = f"{it.type} · {citation(it, lang)}"
        body = max(8, each - _words(fixed) - 6)
        expl = _clip(_explanation(it, lang, age_band), body * 6 // 10)
        text = _clip(_llm_text(it, lang), max(0, body - _words(expl)))
        parts = [fixed]
        if text:
            parts.append(text)
        if expl:
            parts.append("our simple explanation: " + expl)
        note = (it.disagreement_note_ar if lang == "ar" else it.disagreement_note_en) or (
            it.disagreement_note_en or it.disagreement_note_ar)
        if item_level(it) == "C" and note:
            parts.append("all agree: " + _clip(note, 20))
        lines.append(label + " " + replace_verse_markers(" · ".join(parts), lang))  # no stray braces
    return "\n".join([head, *lines, foot] + ([tail] if tail else []))
