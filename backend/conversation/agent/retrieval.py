"""Deterministic retrieval over the knowledge bank (task 03).

``build_value_index()`` runs once per session (sync, DB) and snapshots every
servable ContentItem plus the keywords of every Value into memory.
``match_values()`` then runs on each child turn with no DB and no network, in
well under 10 ms. The formatting helpers build the VERIFIED SOURCES block for
the LLM (never the Arabic text of a verse) and the card payload for the
``reference`` data event (which does carry the Arabic).
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

from .scripture_guard import strip_scripture
from .surah_names import surah_name
from .text_match import Term, TermIndex, make_term, term_in, token_forms

logger = logging.getLogger(__name__)

MAX_VALUES = 2
MAX_ITEMS = 3
_TYPE_RANK = {"verse": 0, "hadith": 1}
_FALLBACK_LEVEL = {
    "verse": "A", "hadith": "A", "term": "A", "story": "A", "sirah": "A",
    "aqidah": "A", "tafsir": "B", "faq": "B", "fiqh": "B",
}
_LEVEL_ORDER = {"": 0, "A": 1, "B": 2, "C": 3, "D": 4}


def item_level(item) -> str:
    """Item content level; a blank level falls back to the default per type."""
    lvl = (getattr(item, "content_level", "") or "").strip().upper()
    if lvl in ("A", "B", "C"):
        return lvl
    return _FALLBACK_LEVEL.get(getattr(item, "type", ""), "A")


def max_level(items) -> str:
    best = ""
    for it in items:
        lvl = item_level(it)
        if _LEVEL_ORDER[lvl] > _LEVEL_ORDER[best]:
            best = lvl
    return best


@dataclass(frozen=True)
class WeakKeywords:
    """Words that name a person or role (mom, dad, brother, family ...).

    Said on their own they only mean "someone was mentioned" ("my mom is tired", "we
    played with my dad"), so a keyword in ``words`` counts toward a value only when the
    same message also has a value cue: a non-weak keyword of that value, or a behaviour
    or question cue from ``cues`` (respect, obey, help, "should I" ...).
    """
    words: frozenset = frozenset()   # normalised keyword texts (Term.text)
    cues: TermIndex = TermIndex()
    # death, fear, secrecy, hospital, bullying: a message with one of these is a moment for comfort
    # (or the safety rules), never a value card, so its own words match nothing (review of #76)
    veto: TermIndex = TermIndex()

    def __bool__(self) -> bool:
        return bool(self.words)


NO_WEAK = WeakKeywords()


def _terms(*lists) -> tuple[Term, ...]:
    out = []
    for lst in lists:
        for k in lst or []:
            if isinstance(k, str):
                t = make_term(k)
                if t:
                    out.append(t)
    return tuple(out)


def _split_terms(weak: WeakKeywords, *lists) -> tuple[tuple[Term, ...], tuple[Term, ...]]:
    """(strong terms, weak terms) of the keyword lists."""
    strong, soft = [], []
    for t in _terms(*lists):
        (soft if t.text in weak.words else strong).append(t)
    return tuple(strong), tuple(soft)


@dataclass
class IndexedValue:
    slug: str
    name_ar: str
    name_en: str
    terms: tuple[Term, ...]
    order: int = 0
    weak_terms: tuple[Term, ...] = ()


@dataclass
class IndexedItem:
    obj: object
    pk: int
    type: str
    level: str
    reviewed: bool
    age_band: str
    terms: tuple[Term, ...]
    value_slugs: list[str] = field(default_factory=list)
    weak_terms: tuple[Term, ...] = ()


class ValueIndex:
    def __init__(self, values: list[IndexedValue], items: dict[int, IndexedItem],
                 links: dict[str, list[tuple[int, int]]], weak: WeakKeywords = NO_WEAK,
                 verses: dict | None = None):
        self.values = values
        self.items = items
        self.links = links  # value slug -> [(order, item pk)]
        self.weak = weak
        self.verses = verses or {}  # (surah, ayah) -> servable bank verse, for {{verse:S:A}}

    def __bool__(self) -> bool:
        return bool(self.items)

    def value_names(self, lang: str = "en") -> list[str]:
        key = "name_ar" if lang == "ar" else "name_en"
        return [getattr(v, key) for v in self.values if getattr(v, key)]

    def value_name_for(self, pk: int, lang: str = "en") -> str:
        it = self.items.get(pk)
        if not it or not it.value_slugs:
            return ""
        by_slug = {v.slug: v for v in self.values}
        v = by_slug.get(it.value_slugs[0])
        return (v.name_ar if lang == "ar" else v.name_en) if v else ""

    @classmethod
    def from_records(cls, values, items, links, synonyms=None,
                     weak: WeakKeywords | None = None) -> "ValueIndex":
        """Build from model instances or look-alikes.

        ``links`` is an iterable of ``(value_slug, item_pk, order)``. ``synonyms`` is
        ``{slug: {"en": [...], "ar": [...]}}``: extra keywords merged into the value's own.
        ``weak`` (see ``WeakKeywords``) marks person and role words that need a value cue.
        """
        synonyms = synonyms or {}
        weak = weak if weak is not None else NO_WEAK   # not ``or``: a veto-only list is falsy
        items = list(items)
        verses = {(getattr(it, "surah", None), getattr(it, "ayah", None)): it
                  for it in items if it.type == "verse"}
        ivals = []
        for v in values:
            strong, soft = _split_terms(
                weak, getattr(v, "keywords_ar", []), getattr(v, "keywords_en", []),
                (synonyms.get(v.slug) or {}).get("ar", []),
                (synonyms.get(v.slug) or {}).get("en", []))
            ivals.append(IndexedValue(
                slug=v.slug, name_ar=getattr(v, "name_ar", ""),
                name_en=getattr(v, "name_en", ""), terms=strong,
                order=getattr(v, "order", 0), weak_terms=soft))
        iitems: dict[int, IndexedItem] = {}
        for it in items:
            pk = it.pk
            bad = unresolved_markers(it, verses)
            if bad:
                # no source, no answer: a marker without a servable bank verse is a hole
                logger.warning("knowledge bank: item excluded, unresolved verse marker: "
                               "item=%s type=%s refs=%s", pk, it.type, ",".join(bad))
                continue
            strong, soft = _split_terms(
                weak, getattr(it, "keywords_ar", []), getattr(it, "keywords_en", []))
            iitems[pk] = IndexedItem(
                obj=it, pk=pk, type=it.type, level=item_level(it),
                reviewed=getattr(it, "verification_status", "") == "reviewed",
                age_band=getattr(it, "age_band", "all") or "all",
                terms=strong, weak_terms=soft)
        lk: dict[str, list[tuple[int, int]]] = {}
        for slug, pk, order in links:
            if pk in iitems:
                lk.setdefault(slug, []).append((order, pk))
                iitems[pk].value_slugs.append(slug)
        for lst in lk.values():
            lst.sort()
        return cls(ivals, iitems, lk, weak, verses)


EMPTY_INDEX = ValueIndex([], {}, {})


def _has_text(item) -> bool:
    if item.type == "verse":
        return bool(item.arabic_text)
    return bool(item.arabic_text or item.english_text)


def load_synonyms() -> dict:
    """Extra per-value keywords from turn_rules.json (lead-editable, words only)."""
    import json
    from pathlib import Path
    try:
        path = Path(__file__).resolve().parents[2] / "session_moral_context" / "content" / "turn_rules.json"
        raw = json.loads(path.read_text(encoding="utf-8")).get("retrieval_synonyms", {})
    except Exception:
        return {}
    return {k: v for k, v in raw.items() if not k.startswith("_") and isinstance(v, dict)}


def load_weak_keywords() -> WeakKeywords:
    """The ``weak_keywords`` section of turn_rules.json, normalised (see ``WeakKeywords``).

    A word may be ``@name`` to include the shared list ``vocab.name``. Set
    RETRIEVAL_WEAK_KEYWORDS=0 to switch the gating off (every keyword counts again); the
    ``veto`` list stays on whatever the flag.
    """
    import json
    import os
    from pathlib import Path
    try:
        path = Path(__file__).resolve().parents[2] / "session_moral_context" / "content" / "turn_rules.json"
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return NO_WEAK
    cfg = raw.get("weak_keywords") or {}
    veto = TermIndex(t for lang in ("en", "ar")
                     for t in (make_term(c) for c in (cfg.get("veto") or {}).get(lang, [])) if t)
    if os.getenv("RETRIEVAL_WEAK_KEYWORDS", "1").strip().lower() in ("0", "off", "false", "no"):
        return WeakKeywords(veto=veto)
    vocab = raw.get("vocab", {})
    words: set[str] = set()
    cues: list[Term] = []
    for lang in ("en", "ar"):
        for w in cfg.get(lang, []):
            for p in (vocab.get(w[1:], {}).get(lang, []) if w.startswith("@") else [w]):
                t = make_term(p)
                if t:
                    words.add(t.text)
        cues.extend(t for t in (make_term(c) for c in (cfg.get("cues") or {}).get(lang, [])) if t)
    return WeakKeywords(frozenset(words), TermIndex(cues), veto)


def build_value_index() -> ValueIndex:
    """Load values and servable items from the DB (sync; call once per session)."""
    from session_moral_context.models import ContentItem, Value, ValueItem

    items = [i for i in ContentItem.objects.servable() if _has_text(i)]
    pks = {i.pk for i in items}
    values = list(Value.objects.all())
    links = [
        (slug, item_id, order)
        for slug, item_id, order in ValueItem.objects.filter(item_id__in=pks)
        .values_list("value__slug", "item_id", "order")
    ]
    return ValueIndex.from_records(values, items, links, load_synonyms(), load_weak_keywords())


def items_for_values(index: ValueIndex | None, slugs, lang: str = "en",
                     age_band: str | None = None, limit: int = MAX_ITEMS) -> list:
    """Servable items linked to the given value slugs (no text matching).

    Used by turn rules that name the values to serve, so that unrelated words in the
    child's sentence cannot pull in other values' verses.
    """
    if not index or not slugs:
        return []
    out: list = []
    for slug in slugs:
        for _order, pk in index.links.get(slug, []):
            it = index.items[pk]
            if age_band == "6-9" and it.age_band == "10-13":
                continue
            if it.obj not in out:
                out.append(it.obj)
    out.sort(key=lambda o: (
        0 if index.items[o.pk].reviewed else 1,
        _TYPE_RANK.get(o.type, 2),
        0 if getattr(o, "child_explanation_ar" if lang == "ar" else "child_explanation_en", "") else 1,
    ))
    return out[:limit]


def match_values(text: str, lang: str = "en", age_band: str | None = None,
                 index: ValueIndex | None = None, types: tuple | None = None) -> list:
    """Top servable ContentItems for the child's turn (no DB, no network).

    Both keyword languages are always tried because children mix them. ``lang``
    only breaks ties (items with an explanation in the session language first).
    ``types`` keeps only those item types BEFORE the top-3 cut, so a search for hadith is not
    left empty because the three best matches happened to be verses.
    """
    if not index or not text:
        return []
    tf = token_forms(text)
    if not tf or index.weak.veto.any_in(tf):
        return []

    # Person and role words (mom, dad, brother ...) only count next to a value cue: a
    # strong keyword of the same value, or a behaviour / question cue in the message.
    cue = index.weak.cues.any_in(tf)
    strong_hit: set[str] = set()
    vscore: dict[str, int] = {}
    for v in index.values:
        s = sum(t.weight for t in v.terms if term_in(t, tf))
        if s:
            strong_hit.add(v.slug)
        if v.weak_terms and (s or cue):
            s += sum(t.weight for t in v.weak_terms if term_in(t, tf))
        if s:
            vscore[v.slug] = s
    top_values: list[str] = []
    if vscore:
        order = {v.slug: (v.order, v.slug) for v in index.values}
        ranked = sorted(vscore, key=lambda k: (-vscore[k], order[k]))
        top_values.append(ranked[0])
        if len(ranked) > 1 and vscore[ranked[1]] * 2 >= vscore[ranked[0]]:
            top_values.append(ranked[1])
    top_values = top_values[:MAX_VALUES]

    cand: dict[int, float] = {}
    for slug in top_values:
        for _order, pk in index.links.get(slug, []):
            cand[pk] = max(cand.get(pk, 0), vscore[slug])
    for pk, it in index.items.items():
        if not (it.terms or it.weak_terms):
            continue
        s = sum(t.weight for t in it.terms if term_in(t, tf))
        if it.weak_terms and (cue or s or strong_hit.intersection(it.value_slugs)):
            s += sum(t.weight for t in it.weak_terms if term_in(t, tf))
        if s:
            cand[pk] = cand.get(pk, 0) + 2 * s

    lang_attr = "child_explanation_ar" if lang == "ar" else "child_explanation_en"

    def key(pk: int):
        it = index.items[pk]
        band_pref = 0 if it.age_band == age_band else (1 if it.age_band == "all" else 2)
        return (
            -cand[pk],
            0 if it.reviewed else 1,
            _TYPE_RANK.get(it.type, 2),
            band_pref,
            0 if getattr(it.obj, lang_attr, "") else 1,
            pk,
        )

    pool = []
    for pk in cand:
        it = index.items[pk]
        if age_band == "6-9" and it.age_band == "10-13":
            continue  # never serve older-child material to a younger child
        if types is not None and it.type not in types:
            continue
        pool.append(pk)
    pool.sort(key=key)
    return [index.items[pk].obj for pk in pool[:MAX_ITEMS]]


# ------------------------------------------------------------- formatting

_GRADE_EN = {"صحيح": "sahih"}

# Organiser ruling 2026-10-05: everyayah.com recitation is accepted "with the source name and link
# stated clearly". Every verse recitation in the bank is the Husary (normal-pace murattal) folder there.
RECITATION_SOURCE_URL = "https://everyayah.com/"
RECITATION_CREDIT = {
    "en": "Recitation: Mahmoud Khalil Al-Husary, everyayah.com",
    "ar": "التلاوة: محمود خليل الحصري، everyayah.com",
}


def audio_credit(audio_urls, lang: str = "en") -> tuple[str, str]:
    """(credit text, source link) for recitation audio, or ('', '') when none is everyayah."""
    if any("everyayah.com/" in (u or "") for u in audio_urls):
        return RECITATION_CREDIT["ar" if lang == "ar" else "en"], RECITATION_SOURCE_URL
    return "", ""

# FAQ items may hold {{verse:S:A}} where the source PDF drew a verse as glyphs.
_VERSE_MARKER = re.compile(r"\{\{\s*verse\s*:\s*(\d{1,3})\s*:\s*(\d{1,3})\s*\}\}")


def verse_refs(text: str) -> list[str]:
    """['S:A', ...] for every {{verse:S:A}} marker in ``text`` (in order, unique)."""
    seen: list[str] = []
    for s_, a_ in _VERSE_MARKER.findall(text or ""):
        ref = f"{int(s_)}:{int(a_)}"
        if ref not in seen:
            seen.append(ref)
    return seen


def _reference(n: int, a_: int, lang: str) -> str:
    """Localized reference only; never any verse text."""
    name = surah_name(n, lang)
    return f"(سورة {name} {n}:{a_})" if lang == "ar" else f"(Surah {name} {n}:{a_})"


# a malformed marker or stray braces: dropped, so no "{{" ever reaches a child, LLM or TTS
_STRAY_BRACES = re.compile(r"\{\{[^{}]*\}\}|[{}]")


def replace_verse_markers(text: str, lang: str = "en") -> str:
    """Plain-text fallback: swap each marker for a localized reference, no braces left."""
    out = _VERSE_MARKER.sub(lambda m: _reference(int(m.group(1)), int(m.group(2)), lang), text or "")
    return _STRAY_BRACES.sub("", out)


def unresolved_markers(item, verses: dict) -> list[str]:
    """Marker refs of a non-verse item that have no servable bank verse in ``verses``.

    A marker that does not parse as ``{{verse:S:A}}`` counts as unresolved ("?").
    """
    if item.type == "verse":
        return []
    bad: list[str] = []
    for f in ("arabic_text", "english_text"):
        t = getattr(item, f, "") or ""
        bad += [r for r in verse_refs(t) if tuple(map(int, r.split(":"))) not in verses]
        if "{{" in _VERSE_MARKER.sub("", t):
            bad.append("?")
    return bad


def text_segments(text: str, lang: str = "ar", index: ValueIndex | None = None) -> list[dict]:
    """Ordered ``text`` / ``verse`` segments of ``text``; ``[]`` when it has no marker.

    A verse segment carries the bank verse's reference and audio, never its text. A
    marker without a bank verse (not expected: such items are not indexed) becomes a
    text segment holding the localized reference.
    """
    text = text or ""
    if not _VERSE_MARKER.search(text):
        return []
    out: list[dict] = []
    pos = 0
    for m in _VERSE_MARKER.finditer(text):
        seg = _STRAY_BRACES.sub("", text[pos:m.start()])
        if seg:
            out.append({"type": "text", "text": seg})
        n, a_ = int(m.group(1)), int(m.group(2))
        v = index.verses.get((n, a_)) if index else None
        if v:
            out.append({"type": "verse", "surah": n, "ayah": a_, "ref": f"{n}:{a_}",
                        "item_key": f"verse:{n}:{a_}", "id": v.pk,
                        "surah_name": surah_name(n, "ar"), "audio_url": v.audio_url})
        else:
            out.append({"type": "text", "text": _reference(n, a_, lang)})
        pos = m.end()
    tail = _STRAY_BRACES.sub("", text[pos:])
    if tail:
        out.append({"type": "text", "text": tail})
    return out


def _explanation_with_lang(item, lang: str, age_band: str | None) -> tuple[str, str]:
    older = age_band == "10-13"
    order = ("ar", "en") if lang == "ar" else ("en", "ar")
    for code in order:
        if older:
            t = getattr(item, f"child_explanation_older_{code}", "")
            if t:
                return t, code
        t = getattr(item, f"child_explanation_{code}", "")
        if t:
            return t, code
    return "", lang


def _explanation(item, lang: str, age_band: str | None) -> str:
    return _explanation_with_lang(item, lang, age_band)[0]


def citation(item, lang: str = "en") -> str:
    """Short source name the agent can say aloud."""
    if item.type == "verse":
        name = surah_name(item.surah, lang)
        ref = f"{item.surah}:{item.ayah}"
        return f"سورة {name} ({ref})" if lang == "ar" else f"Surah {name} ({ref})"
    title = (item.title_ar if lang == "ar" else item.title_en) or ""
    if item.type == "hadith":
        grade = (item.grade or "").strip(" []()")
        if lang != "ar":
            grade = _GRADE_EN.get(grade, grade)
        bits = [b for b in (item.book, f"#{item.number}" if item.number else "") if b]
        who = f" ({item.grader})" if item.grader else ""
        label = " ".join(bits)
        if lang == "ar":
            return f"{label}، {grade}{who}".strip("، ")
        return f"{label}, graded {grade}{who}".strip(", ")
    base = title or item.type
    where = " ".join(b for b in (item.book, item.number) if b) or item.source_site
    return f"{base} ({where})" if where else base


def _clip(s: str, n: int = 600) -> str:
    s = (s or "").strip()
    return s if len(s) <= n else s[: n - 1].rstrip() + "..."


# Source excerpts quote verses and hadith inline in plain script (no brackets, no waqf marks), so
# strip_scripture cannot catch them. The excerpt goes on the card only; the LLM gets the citation
# and our own child explanation (plan 7.3: no Arabic scripture in the LLM context).
_CARD_ONLY_TYPES = frozenset({"tafsir", "sirah", "aqidah", "fiqh", "faq"})


def _llm_text(item, lang: str) -> str:
    """Text the LLM may see. Never the Arabic of a verse, never a source excerpt."""
    if item.type == "verse":
        return item.english_text if lang != "ar" and item.translation_name else ""
    if item.type in _CARD_ONLY_TYPES:
        return ""
    if lang == "ar":
        return strip_scripture(replace_verse_markers(item.arabic_text, lang))
    if not item.translation_name:
        return ""
    return strip_scripture(replace_verse_markers(item.english_text, lang))


def format_sources_block(items, lang: str = "en", age_band: str | None = None) -> str:
    if not items:
        return ""
    lines = [
        "VERIFIED SOURCES (quote only these; say the short source aloud; never recite "
        "the Arabic text of a verse, say you will play it; the card on screen shows the "
        "details). These are the ONLY sources you may attribute anything to this turn:"
    ]
    for n, it in enumerate(items, 1):
        parts = [f"[{n}] id={it.pk} type={it.type} level={item_level(it)}",
                 f"source: {citation(it, lang)}"]
        text = _llm_text(it, lang)
        if text:
            tn = f" ({it.translation_name})" if it.type == "verse" and it.translation_name else ""
            parts.append(f"text{tn}: {_clip(text)}")
        elif it.type == "verse":
            parts.append("text: (shown and played on the card; do not recite it)")
        expl = _explanation(it, lang, age_band)
        if expl:
            parts.append(f"simple explanation (ours, not the source's words): {_clip(expl, 400)}")
        note = (it.disagreement_note_ar if lang == "ar" else it.disagreement_note_en) or (
            it.disagreement_note_en or it.disagreement_note_ar)
        if item_level(it) == "C" and note:
            parts.append(f"scholars differ here; what all agree on: {_clip(note, 300)}")
        lines.append("\n    ".join(parts))
    # one last pass over everything the LLM is shown (text, title, explanation, notes)
    return replace_verse_markers("\n".join(lines), lang)


def card_payload(item, lang: str = "en", age_band: str | None = None,
                 index: ValueIndex | None = None) -> dict:
    """Payload of the ``reference`` data event (topic ``reference``, one per item).

    This is the only place Arabic scripture leaves the backend (the LLM never
    sees a verse's Arabic). Contract with the web/mobile cards
    (docs/hackathon/handoffs/05-cards-ai-privacy.md section 2). Keys:

      id, type, kind ('scripture' for verse/hadith, else 'source_excerpt'),
      arabic_text, english_text (blank unless translation_name is set),
      translation_name, translation_source_url, surah, ayah, surah_name (Arabic),
      audio_url, audio_credit + audio_source_url (the recitation credit text and its everyayah.com
      link, in the session language; '' when the card has no recitation, also covers the
      recitation of verse segments),
      book, number, grade, grader, source_site, source_url,
      content_level ('A'|'B'|'C'), value (value name in the session language),
      title (non-verse only), explanation (child explanation for the age band),
      explanation_lang ('ar'|'en'), explanation_origin ('generated'),
      disagreement_note (level C, session language), verification_status,
      verse_refs (['S:A', ...] for every {{verse:S:A}} marker in arabic_text),
      segments ([] when arabic_text has no marker; see below).

    FAQ items may contain ``{{verse:S:A}}`` markers where the source PDF drew a verse
    as glyphs. No text field of the payload ever holds a raw marker. ``segments`` is the
    ordered rendering of ``arabic_text``: ``{"type": "text", "text"}`` and
    ``{"type": "verse", "surah", "ayah", "ref" ('S:A'), "item_key" ('verse:S:A'), "id",
    "surah_name" (Arabic), "audio_url"}`` (the bank verse's reference and recitation, no
    verse text). ``arabic_text`` itself is the plain-text fallback, each marker already
    replaced by the localized reference (see ``replace_verse_markers``). The LLM and TTS
    never see the marker either.

    Empty strings / None mean "not applicable"; the UI renders no block for them.
    """
    kind = "scripture" if item.type in ("verse", "hadith") else "source_excerpt"
    expl, expl_lang = _explanation_with_lang(item, lang, age_band)
    other = "en" if lang == "ar" else "ar"
    title = ""
    if item.type != "verse":
        title = getattr(item, f"title_{lang}", "") or getattr(item, f"title_{other}", "")
    note = ""
    if item_level(item) == "C":
        note = (getattr(item, f"disagreement_note_{lang}", "")
                or getattr(item, f"disagreement_note_{other}", ""))
    segments = text_segments(item.arabic_text, "ar", index)
    credit, credit_url = audio_credit(
        [item.audio_url] + [g.get("audio_url", "") for g in segments if g["type"] == "verse"], lang)
    return {
        "id": item.pk,
        "type": item.type,
        "kind": kind,
        "arabic_text": item.arabic_text if item.type == "verse"
        else replace_verse_markers(item.arabic_text, "ar"),
        "english_text": (item.english_text if item.type == "verse"
                         else replace_verse_markers(item.english_text, "en")) if item.translation_name else "",
        "translation_name": item.translation_name,
        "translation_source_url": item.translation_source_url,
        "surah": item.surah,
        "ayah": item.ayah,
        "surah_name": surah_name(item.surah, "ar"),
        "audio_url": item.audio_url,
        "audio_credit": credit,
        "audio_source_url": credit_url,
        "book": item.book,
        "number": item.number,
        "grade": item.grade,
        "grader": item.grader,
        "source_site": item.source_site,
        "source_url": item.source_url,
        "content_level": item_level(item),
        "value": index.value_name_for(item.pk, lang) if index else "",
        "title": replace_verse_markers(title, lang),
        "explanation": replace_verse_markers(expl, expl_lang),
        "explanation_lang": expl_lang if expl else "",
        "explanation_origin": "generated",
        "disagreement_note": replace_verse_markers(note, lang),
        "verification_status": item.verification_status,
        "verse_refs": verse_refs(item.arabic_text),
        "segments": segments,
    }
