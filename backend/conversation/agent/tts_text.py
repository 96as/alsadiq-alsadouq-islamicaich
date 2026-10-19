"""Text cleaning that runs just before text is sent to TTS.

Why: eleven_flash_v2_5 does not normalise numbers, reads markdown symbols and
emoji aloud, and cannot say honorific ligatures. Separately, the product rule
is that Quran verses are never synthesised: the app plays recitation audio.

Public API (no livekit import, pure Python):

- prepare_for_tts(text, lang) -> str
      One-shot cleaner for a complete string.
- TTSTextStream(lang)
      Sync state machine: feed(chunk) -> str, flush() -> str.
- tts_text_transform(lang) -> Callable[[AsyncIterable[str]], AsyncIterable[str]]
      The livekit-agents 1.5.1 hook (see below).
- clean_tts_stream(text, lang) -> AsyncIterator[str]
      Same thing as a plain async generator.

``lang`` is "ar", "en" (region suffixes such as "ar-SA" are fine), "auto"
(decide per piece of text from its script), or a zero-argument callable that
returns one of those (use it to follow a language that can change mid-session).

Quran guard: anything between the Quran brackets (U+FD3E / U+FD3F, either
order) is dropped and replaced by one short neutral phrase. Only the bracket
characters are used to detect verses. No verse text is stored here.

Scripture-mark guard (the compliance rule "TTS never speaks scripture"): after the
text is cleaned, words that carry dense Quranic recitation marks (waqf signs, small
high letters, ...) are dropped by the lead's scripture_guard filter and replaced by
the same neutral phrase, so a verse written WITH its marks but WITHOUT brackets is
not synthesised either. scripture_guard.STATS["speech_cleaner_scripture"] counts
the replaced runs (no text is ever stored). The chat transcript is guarded
separately (AlSadiqAgent.transcription_node).

Wiring into livekit-agents 1.5.1 (verified against the 1.5.1 wheel source):

  AgentSession(tts_text_transforms=[speech_tts_text_transform(lambda: agent.language)], ...)

  - Parameter: livekit/agents/voice/agent_session.py:223 (type at :140, stored
    at :362-366). Passing a list REPLACES the default
    ["filter_markdown", "filter_emoji"] (agent_session.py:190); this module
    already strips markdown and emoji, so the list does not need them.
  - Applied per speech segment, before Agent.tts_node, in
    livekit/agents/voice/generation.py:261-264
    (`input = _apply_text_transforms(input, text_transforms)` then
    `node(input, model_settings)`). Each callable gets an AsyncIterable[str]
    and returns an AsyncIterable[str] (voice/transcription/text_transforms.py).
    Every TTS path goes through perform_tts_inference with the session's list:
    LLM replies and generate_reply (agent_activity.py:2189-2196), say()
    (:1980-1987) and realtime replies (:2728-2735).
  - The callable is invoked once per segment (a segment ends at a flush
    sentinel, e.g. around tool calls), inside the speech's own tts task.
    speech_tts_text_transform() keeps the Quran open/closed state per task, so
    a verse that spans two segments of one speech is still suppressed and a
    new speech always starts closed.

Transcript (livekit-agents 1.5.1, checked in agent_activity.py ~1930-1995 and
generation.py ~225-265): the session splits the LLM text into two copies. One goes
through tts_text_transforms and tts_node to the TTS. The other is the transcript
source. With use_tts_aligned_transcript=False the transcript is that LLM copy: this
cleaner does not touch it (digits stay digits), but AlSadiqAgent.transcription_node runs
the compliance guards on it. With use_tts_aligned_transcript=True (and a TTS
that reports word timings) the transcript source is REPLACED by the TTS's timed words,
so digits show as words and a bracketed verse shows as the neutral phrase in the chat,
the DB and the LLM's own chat history. The AlSadiq entrypoint therefore keeps aligned
transcripts off. Use speech_tts_text_transform() for the session (see below).
"""
from __future__ import annotations

import asyncio
import logging
import re
import unicodedata
import weakref
from collections.abc import AsyncIterable, AsyncIterator, Callable
from typing import Union

from conversation.agent.scripture_guard import STATS, _ScriptureFilter

logger = logging.getLogger(__name__)

LangSpec = Union[str, Callable[[], str], None]

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

QURAN_BRACKETS = "\ufd3e\ufd3f"  # ornate parentheses; either may open or close
QURAN_PHRASE = {
    "ar": "استمع إلى التلاوة",
    "en": "listen to the recitation",
}

_DROP_MARK = "\x00"  # internal: a scripture word the filter dropped (never emitted)
_WORD_RE = re.compile(r"\S+\s*")
# Longest stretch of text swallowed after an opening Quran bracket when no closing
# bracket ever arrives; after that a capped guard gives up (and warns). The live
# per-speech guard (speech_tts_text_transform) has no cap; see _QuranGuardState.
_MAX_UNCLOSED_QURAN_CHARS = 400
# A buffer with no whitespace this long is flushed anyway.
_MAX_UNBROKEN_CHARS = 400
# Longest "[text](url" we wait on before giving up on completing a markdown link.
_MAX_LINK_HOLD_CHARS = 300

HONORIFICS = {
    "ar": {
        "\ufdfa": "صلى الله عليه وسلم",
        "\ufdfb": "جل جلاله",
        "\ufdf2": "الله",
    },
    "en": {
        "\ufdfa": "peace be upon him",
        "\ufdfb": "glorified and exalted is He",
        "\ufdf2": "Allah",
    },
}
_BASMALA_LIGATURE = "\ufdfd"  # dropped, never expanded (it is Quran text)

# ---------------------------------------------------------------------------
# Language helpers
# ---------------------------------------------------------------------------


def _norm_lang(lang: str | None) -> str:
    s = (lang or "").strip().lower().replace("_", "-")
    base = s.split("-")[0]
    return base if base in ("ar", "en") else "auto"


def _is_arabic_letter(ch: str) -> bool:
    o = ord(ch)
    return (
        0x0600 <= o <= 0x06FF
        or 0x0750 <= o <= 0x077F
        or 0x08A0 <= o <= 0x08FF
        or 0xFB50 <= o <= 0xFDFF
        or 0xFE70 <= o <= 0xFEFF
    ) and ch.isalpha()


def _detect_lang(text: str, fallback: str) -> str:
    ar = sum(1 for c in text if _is_arabic_letter(c))
    lat = sum(1 for c in text if c.isascii() and c.isalpha())
    if ar > lat:
        return "ar"
    if lat > ar:
        return "en"
    return fallback


# ---------------------------------------------------------------------------
# Numbers to words
# ---------------------------------------------------------------------------

_EN_ONES = [
    "zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
    "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
    "sixteen", "seventeen", "eighteen", "nineteen",
]
_EN_TENS = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy",
            "eighty", "ninety"]
_EN_SCALES = [(10**12, "trillion"), (10**9, "billion"), (10**6, "million"),
              (10**3, "thousand")]


def _en_below_1000(n: int) -> str:
    parts: list[str] = []
    h, r = divmod(n, 100)
    if h:
        parts.append(f"{_EN_ONES[h]} hundred")
    if r:
        if r < 20:
            parts.append(_EN_ONES[r])
        else:
            t, o = divmod(r, 10)
            parts.append(_EN_TENS[t] + (f"-{_EN_ONES[o]}" if o else ""))
    return " ".join(parts)


def _en_cardinal(n: int) -> str:
    if n == 0:
        return "zero"
    parts: list[str] = []
    for scale, name in _EN_SCALES:
        g, n = divmod(n, scale)
        if g:
            parts.append(f"{_en_below_1000(g)} {name}")
    if n:
        parts.append(_en_below_1000(n))
    return " ".join(parts)


_EN_ORDINAL_IRREGULAR = {
    "one": "first", "two": "second", "three": "third", "five": "fifth",
    "eight": "eighth", "nine": "ninth", "twelve": "twelfth",
}


def _en_ordinal(n: int) -> str:
    words = _en_cardinal(n)
    m = re.search(r"([a-z]+)$", words)
    last = m.group(1)
    if last in _EN_ORDINAL_IRREGULAR:
        new = _EN_ORDINAL_IRREGULAR[last]
    elif last.endswith("y"):
        new = last[:-1] + "ieth"
    else:
        new = last + "th"
    return words[: m.start(1)] + new


def _en_year(n: int) -> str:
    """Year style reading for 1100..2099."""
    if 2000 <= n <= 2009 or n % 1000 == 0:
        return _en_cardinal(n)
    hi, lo = divmod(n, 100)
    if lo == 0:
        return f"{_en_cardinal(hi)} hundred"
    if lo < 10:
        return f"{_en_cardinal(hi)} oh {_en_cardinal(lo)}"
    return f"{_en_cardinal(hi)} {_en_cardinal(lo)}"


_AR_ONES = ["صفر", "واحد", "اثنان", "ثلاثة", "أربعة", "خمسة", "ستة", "سبعة",
            "ثمانية", "تسعة"]
_AR_TEENS = {
    10: "عشرة", 11: "أحد عشر", 12: "اثنا عشر", 13: "ثلاثة عشر",
    14: "أربعة عشر", 15: "خمسة عشر", 16: "ستة عشر", 17: "سبعة عشر",
    18: "ثمانية عشر", 19: "تسعة عشر",
}
_AR_TENS = {2: "عشرون", 3: "ثلاثون", 4: "أربعون", 5: "خمسون", 6: "ستون",
            7: "سبعون", 8: "ثمانون", 9: "تسعون"}
_AR_HUNDREDS = {1: "مائة", 2: "مائتان", 3: "ثلاثمائة", 4: "أربعمائة",
                5: "خمسمائة", 6: "ستمائة", 7: "سبعمائة", 8: "ثمانمائة",
                9: "تسعمائة"}
# (value, singular, dual, plural for 3..10, singular-with-tanween for 11..99)
_AR_SCALES = [
    (10**9, ("مليار", "ملياران", "مليارات", "مليارًا")),
    (10**6, ("مليون", "مليونان", "ملايين", "مليونًا")),
    (10**3, ("ألف", "ألفان", "آلاف", "ألفًا")),
]


def _ar_below_1000(n: int) -> str:
    parts: list[str] = []
    h, r = divmod(n, 100)
    if h:
        parts.append(_AR_HUNDREDS[h])
    if r:
        if r < 10:
            parts.append(_AR_ONES[r])
        elif r < 20:
            parts.append(_AR_TEENS[r])
        else:
            t, o = divmod(r, 10)
            parts.append(f"{_AR_ONES[o]} و{_AR_TENS[t]}" if o else _AR_TENS[t])
    return " و".join(parts)


def _ar_group(g: int, forms: tuple[str, str, str, str]) -> str:
    sing, dual, plur, tam = forms
    if g == 1:
        return sing
    if g == 2:
        return dual
    words = _ar_below_1000(g)
    r = g % 100
    if 3 <= r <= 10:
        return f"{words} {plur}"
    if r == 0:
        if words.endswith("مائتان"):
            words = words[: -len("مائتان")] + "مائتا"
        return f"{words} {sing}"
    if r in (1, 2):
        return f"{words} {sing}"
    return f"{words} {tam}"


def _ar_cardinal(n: int) -> str:
    if n == 0:
        return _AR_ONES[0]
    parts: list[str] = []
    for scale, forms in _AR_SCALES:
        g, n = divmod(n, scale)
        if g:
            parts.append(_ar_group(g, forms))
    if n:
        parts.append(_ar_below_1000(n))
    return " و".join(parts)


def _digit_words(digits: str, lang: str) -> str:
    table = _AR_ONES if lang == "ar" else _EN_ONES
    return " ".join(table[int(ch)] for ch in digits)


_NUM_RE = re.compile(
    r"(?P<num>\d+(?:[,\u066c]\d{3}(?!\d))*(?:[.\u066b]\d+)?)"
    r"(?P<suffix>%|(?:st|nd|rd|th)(?![A-Za-z]))?"
)
_TIME_COLON_RE = re.compile(r"(?<=\d):(?=\d)")
_ZERO_DIGITS = "0\u0660\u06f0"


def _number_to_words(m: re.Match, lang: str) -> str:
    raw = m.group("num")
    suffix = m.group("suffix")
    s, e = m.span()
    src = m.string
    prev = src[s - 1] if s > 0 else ""
    nxt = src[e] if e < len(src) else ""
    pad_l = " " if prev.isalpha() else ""
    pad_r = " " if nxt.isalpha() else ""

    grouped = bool(re.search(r"[,\u066c]", raw))
    clean = re.sub(r"[,\u066c]", "", raw).replace("\u066b", ".")
    int_part, _, frac = clean.partition(".")

    if not grouped and (len(int_part) >= 10 or
                        (len(int_part) > 1 and int_part[0] in _ZERO_DIGITS)):
        words = _digit_words(int_part, lang)
    else:
        n = int(int_part)
        if n >= 10**12:
            words = _digit_words(int_part, lang)
        elif (lang == "en" and not grouped and not frac and len(int_part) == 4
              and 1100 <= n <= 2099 and suffix is None):
            words = _en_year(n)
        elif lang == "en" and suffix and suffix != "%" and not frac:
            words = _en_ordinal(n)
            suffix = None
        else:
            words = _en_cardinal(n) if lang == "en" else _ar_cardinal(n)

    if frac:
        point = "point" if lang == "en" else "فاصلة"
        words = f"{words} {point} {_digit_words(frac, lang)}"

    tail = ""
    if suffix == "%":
        tail = " percent" if lang == "en" else " بالمئة"
    elif suffix:  # ordinal suffix that is not spoken as an ordinal here
        tail = " " + suffix
    return f"{pad_l}{words}{tail}{pad_r}"


# A chapter:verse reference ("9:119", "verse 2:255"). The plain colon rule below reads it as two
# bare numbers ("five one hundred nineteen", which in Arabic sounds like 519), so it is spoken
# as "verse one hundred nineteen" (the surah is already named) or "chapter five, verse ...".
_VERSE_REF_RE = re.compile(
    r"(?P<lead>(?:\b(?:verse|ayah|ayat)\s+|(?:الآية|آية)\s+)?)"
    r"(?<![\d:])(?P<ch>\d{1,3}):(?P<v>\d{1,3})(?![\d:])", re.IGNORECASE)
_SURAH_WORD_TAIL_RE = re.compile(r"(?:surah|sura|سورة)[^\d]*$", re.IGNORECASE)
_VERSE_CONTEXT_RE = re.compile(
    r"(?:surah|sura|verse|ayah|ayat|qur.?an|سورة|آية"
    r"|الآية|القرآن)", re.IGNORECASE)
_AR_VERSE = "الآية"      # the verse
_AR_SURAH = "السورة"  # the chapter
_AR_COMMA = "،"


_VERSE_WORD_TAIL_RE = re.compile(r"(?:\b(?:verse|ayah|ayat)|الآية|آية)\s*$", re.IGNORECASE)


def _verse_ref_to_words(m: re.Match, lang: str, context: str = "") -> str:
    # The stream cleans a few words at a time, so the word "verse" or the surah name may sit in
    # an earlier piece: ``context`` is the raw text that came before this piece.
    ch, v = int(m.group("ch")), int(m.group("v"))
    lead = m.group("lead")
    ctx = (context + m.string[:m.start()])[-40:]
    named = bool(_SURAH_WORD_TAIL_RE.search(ctx))
    said_verse = bool(lead) or bool(_VERSE_WORD_TAIL_RE.search(ctx))
    if not (said_verse or _VERSE_CONTEXT_RE.search(ctx)) and ch <= 24 and v <= 59:
        return m.group(0)  # a clock time such as 9:30
    card = _en_cardinal if lang == "en" else _ar_cardinal
    verse_word = "verse" if lang == "en" else _AR_VERSE
    comma = "," if lang == "en" else _AR_COMMA
    if named:  # the surah is already said: only the verse number is left to say
        return f"{lead}{card(v)}" if said_verse else f"{verse_word} {card(v)}"
    return f"{lead}{card(ch)}{comma} {card(v)}"


def numbers_to_words(text: str, lang: str, context: str = "") -> str:
    """Replace digit runs with words. ``lang`` must be "ar" or "en".

    ``context`` is the raw text just before ``text`` (the stream cleans in pieces); it only
    helps to read a chapter:verse reference.
    """
    text = _VERSE_REF_RE.sub(lambda m: _verse_ref_to_words(m, lang, context), text)
    text = _TIME_COLON_RE.sub(" ", text)
    return _NUM_RE.sub(lambda m: _number_to_words(m, lang), text)


# ---------------------------------------------------------------------------
# Markdown, emoji, URLs, honorifics
# ---------------------------------------------------------------------------

_LINE_MARKER_RE = re.compile(
    r"^[ \t]*(?:#{1,6}[ \t]+|[-+*\u2022\u25aa\u25e6\u2023\u25cf][ \t]+|>[ \t]*"
    r"|\d{1,3}[.)][ \t]+)"
)
_IMG_RE = re.compile(r"!\[([^\]]*)\]\([^)]*\)")
_LINK_RE = re.compile(r"\[([^\]]*)\]\([^)]*\)")
_FENCE_RE = re.compile(r"`{3,}[^\s`]*")
_RULE_RE = re.compile(r"[-=_*~]{3,}")
_EMPH_RE = re.compile(r"\*+|~~+|`+")
_UNDERSCORE_RE = re.compile(r"(?<!\w)_+(?=\S)|(?<=\S)_+(?!\w)")
_URL_RE = re.compile(r"(?:https?://|www\.)[^\s<>]+", re.IGNORECASE)
_EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b")
_URL_TRAIL = ".,;:!?)]}'\"\u060c\u061b\u061f"
_INVISIBLE_RE = re.compile("[\u200d\ufe0f\u20e3\u0640]")  # ZWJ, VS16, keycap, tatweel
_EMOJI_RE = re.compile(
    "[\U0001f000-\U0001faff\u2600-\u27bf\u2b00-\u2bff\u2300-\u23ff\u25a0-\u25ff"
    "\u2022]"
)
_EN_ABBREV_RE = re.compile(
    r"\(?\bPBUH\b\)?|\(\s*SAAWS?\s*\)|\(\s*SAWS?\s*\)|\(?\bSWT\b\)?"
)
_SPACE_BEFORE_PUNCT_RE = re.compile(r"[ \t]+([.,!?;:\u060c\u061b\u061f])")
_MULTI_SPACE_RE = re.compile(r"[ \t]{2,}")
_QURAN_STRAY_RE = re.compile("[" + QURAN_BRACKETS + _BASMALA_LIGATURE + "]")
# Kana, CJK ideographs (and extension A), compatibility ideographs and Hangul. The model sometimes
# drops one inside an Arabic word; Sadiq speaks Arabic and English only, so these never belong.
_FOREIGN_SCRIPT_RE = re.compile("[぀-ヿ㐀-鿿豈-﫿가-힯]")


def strip_foreign_script(text: str) -> str:
    """Remove stray Kana/CJK/Hangul characters (removed, not replaced by a space, so the word they
    sat inside stays one word). Arabic, Latin, digits and punctuation are never touched."""
    return _FOREIGN_SCRIPT_RE.sub("", text) if text else text


async def strip_foreign_script_stream(text: AsyncIterable) -> AsyncIterator:
    """The same cleanup for a stream of text chunks (the chat transcript). Anything that is not a
    plain str (a timed chunk, a sentinel) passes through unchanged."""
    async for chunk in text:
        yield strip_foreign_script(chunk) if type(chunk) is str else chunk


# ---------------------------------------------------------------------------
# Off-script characters AFTER the output guards (tidy_off_script)
# ---------------------------------------------------------------------------
# strip_foreign_script above is origin/hackathon's, unchanged. It runs BEFORE the guards (in
# clean_segment for the voice, in AlSadiqAgent.transcription_node for the chat), so every guard
# reads exactly the text it read on origin: the speech cleaner's scripture filter (TTSTextStream),
# the attribution guard and filter_scripture_stream. Everything else origin passed on as it was (a
# Cyrillic, Greek, Hebrew, Thai or Devanagari letter, a Jamo, CJK punctuation, a full-width form)
# is handled by tidy_off_script, which TurnGuardMixin.guard_speech runs LAST, after the
# attribution guard and the scripture filter, for the voice (tts_node) and the chat
# (transcription_node) alike. It only changes how text the guards already passed is said or
# shown; it never changes what a guard reads. (Run before the guards, the same handling hid an
# attribution with a full-width "！" from the attribution guard, and split a marked word that held
# a stray Cyrillic letter, so the scripture filter said a marked word origin dropped: round-2
# review, B1 and B2.)
#
# What is off-script here: Kana, Bopomofo, CJK ideographs and radicals, Hangul (syllables and
# every Jamo block), CJK symbols and compatibility forms, enclosed CJK, half-width Kana and
# Hangul, the supplementary ideograph planes (extension B and later), and Cyrillic, Hebrew,
# Devanagari and Thai letters (a letter that looks like a Latin one is mapped to it first:
# HOMOGLYPHS below; a Devanagari or Thai digit is mapped to the ASCII digit first). A run of
# them is one match (_run_out). Written with escapes so the ranges can be read and checked.
_OFF_SCRIPT_RE = re.compile(
    "["
    "\u0400-\u052f"            # Cyrillic (and supplement)
    "\u0590-\u05ff"            # Hebrew
    "\u0900-\u097f"            # Devanagari
    "\u0e00-\u0e7f"            # Thai
    "\u1100-\u11ff"            # Hangul Jamo
    "\u2e80-\u2fdf"            # CJK radicals, Kangxi radicals
    "\u3000-\u303f"            # CJK symbols and punctuation (the common ones are mapped first)
    "\u3040-\u30ff"            # Hiragana, Katakana
    "\u3100-\u312f\u31a0-\u31bf"   # Bopomofo
    "\u3130-\u318f"            # Hangul compatibility Jamo
    "\u3190-\u319f\u31c0-\u31ff"   # Kanbun, CJK strokes, Katakana extensions
    "\u3200-\u33ff"            # enclosed CJK, CJK compatibility
    "\u3400-\u4dbf"            # CJK extension A
    "\u4dc0-\u4dff"            # Yijing hexagram symbols
    "\u4e00-\u9fff"            # CJK ideographs
    "\ua960-\ua97f"            # Hangul Jamo extended A
    "\uac00-\ud7ff"            # Hangul syllables, Jamo extended B
    "\uf900-\ufaff"            # CJK compatibility ideographs
    "\ufe30-\ufe4f"            # CJK compatibility forms
    "\uff00-\uffef"            # full-width and half-width forms left after the mapping below
    "\U00020000-\U0002ffff"    # CJK extensions B and later, compatibility supplement
    "]+"
)
# Mapped first, one character to one, so a stray full-width mark keeps its meaning instead of
# vanishing: full-width ASCII (U+FF01..U+FF5E) becomes the plain ASCII character, the ideographic
# full stop and comma become "." and ",", the ideographic space becomes a space.
# NOT mapped: the full-width forms whose plain form is markup. By the time this stage runs the
# markup rules have run (on the voice the speech cleaner already took out markdown, links, code
# fences, addresses and emphasis; on the chat the markdown filter did), so a plain form put back
# here would reach the child as markup: the TTS reads "*", "_", "~", "`", "@" or "/" aloud, can
# read "<...>" as a tag, and the chat shows "[...](...)", "{...}" or "**" raw. They fall in the
# U+FF00..U+FFEF range above, so they go like the other off-script characters (_run_out):
#   { } [ ] ( ) < >   ` @ /   * ~ _
# (Before the guards, which is where this mapping ran until round 3, their plain forms also
# started rules that drop reply words: the scripture filter's brace rule, the cleaner's link,
# fence, e-mail and URL rules.)
_NOT_MAPPED = frozenset({0xFF5B, 0xFF5D, 0xFF3B, 0xFF3D, 0xFF08, 0xFF09, 0xFF40, 0xFF20, 0xFF0F,
                         0xFF0A, 0xFF5E, 0xFF3F, 0xFF1C, 0xFF1E})
_OFF_SCRIPT_MAP = {i: i - 0xFEE0 for i in range(0xFF01, 0xFF5F) if i not in _NOT_MAPPED}
_OFF_SCRIPT_MAP.update({0x3001: ",", 0x3002: ".", 0x3000: " "})
# Cyrillic and Greek letters that look like a Latin letter (and five Hebrew and Hangul letters
# that do: ו ן ס, ㅇ ㅣ) become that Latin letter, wherever they are; they never go like the rest
# of their script. The model can put one inside an English word: "trusted аdult" with a Cyrillic
# "а" is said "trusted adult", not "trusted dult" or "trusted d ult". The guards read the
# look-alike as origin's guards did (this runs after them): an attribution written with
# look-alikes ("The Рrophet said", Cyrillic "Р") gets origin's verdict, which is to let it
# through (origin's attribution guard does not read "Рrophet" as "Prophet" either), and is then
# said in Latin letters. The mapping is context-free: one character always gives the same output,
# in any chunk. Effects outside a Latin word: a standalone look-alike ("а" alone) is the Latin
# letter; a word written in Cyrillic keeps its look-alike letters as Latin ones and its other
# letters go (_run_out); a Greek look-alike becomes Latin (Greek is not in the class above; its
# other letters are left as they were).
# Not mapped (a limit): other letters Unicode lists as confusable with a Latin letter; they go
# like the rest of their script, so a Latin word with one of those inside is split in two (a
# mapped one is not: "trusted aduןt", with the Hebrew final nun, is said "trusted adult").
# The Devanagari digit zero "०" is a digit, not a letter: it becomes "0" (the digits below),
# never "o".
HOMOGLYPHS = {
    # Cyrillic capitals
    "А": "A", "В": "B", "Е": "E", "К": "K", "М": "M", "Н": "H",
    "О": "O", "Р": "P", "С": "C", "Т": "T", "У": "Y", "Х": "X",
    "Ё": "Ë", "Ѕ": "S", "І": "I", "Ї": "Ï", "Ј": "J",
    "Ѵ": "V", "Ү": "Y", "Һ": "H", "Ӏ": "I", "Ԛ": "Q", "Ԝ": "W",
    # Cyrillic small letters
    "а": "a", "в": "b", "е": "e", "к": "k", "м": "m", "н": "h",
    "о": "o", "р": "p", "с": "c", "т": "t", "у": "y", "х": "x",
    "ё": "ë", "ѕ": "s", "і": "i", "ї": "ï", "ј": "j",
    "ѵ": "v", "ү": "y", "һ": "h", "ӏ": "l", "ԁ": "d", "ԛ": "q",
    "ԝ": "w",
    # Greek capitals
    "Α": "A", "Β": "B", "Ε": "E", "Ζ": "Z", "Η": "H", "Ι": "I",
    "Κ": "K", "Μ": "M", "Ν": "N", "Ο": "O", "Ρ": "P", "Τ": "T",
    "Υ": "Y", "Χ": "X", "Ϲ": "C", "Ϳ": "J",
    # Greek small letters
    "α": "a", "γ": "y", "ε": "e", "ι": "i", "κ": "k", "ν": "v",
    "ο": "o", "ρ": "p", "τ": "t", "υ": "u", "χ": "x", "ω": "w",
    "ϲ": "c", "ϳ": "j",
    # Hebrew (vav, final nun, samekh) and Hangul compatibility Jamo (ieung, i)
    "ו": "l", "ן": "l", "ס": "o", "ㅇ": "o", "ㅣ": "l",
}
_OFF_SCRIPT_MAP.update({ord(k): v for k, v in HOMOGLYPHS.items()})
# Devanagari and Thai digits (U+0966..U+096F, U+0E50..U+0E59) become the ASCII digit of the
# same value, one to one and context-free like the rest of this mapping, so a number keeps its
# meaning instead of going like the rest of its script: "call ९११" and "call ๙๑๑" are said
# "call 911". Like the whole stage this runs after the guards: what they read is unchanged.
_OFF_SCRIPT_MAP.update({c: str(unicodedata.decimal(chr(c)))
                        for c in (*range(0x0966, 0x0970), *range(0x0E50, 0x0E5A))})
# The characters origin/hackathon already removed (Kana, CJK ideographs and extension A,
# compatibility ideographs, Hangul syllables; origin's own class, _FOREIGN_SCRIPT_RE above,
# written with escapes). On the live chains none is left by the time this stage runs (the strip
# before the guards took them out); a reply given to guard_speech without that strip is the case
# this covers: they are removed, as origin removed them. A run of only these.
_REMOVED_BEFORE_RE = re.compile("[\u3040-\u30ff\u3400-\u9fff\uf900-\ufaff\uac00-\ud7af]+")


def _run_out(text: str, m: re.Match, before: str) -> str:
    """What a run of off-script characters (``m``, a match in ``text``, already mapped) becomes
    in the text the child hears or reads. ``before`` is the character just before ``text`` ("" at
    the start of the reply).

    - Only characters origin/hackathon already removed (_REMOVED_BEFORE_RE: Kana, CJK ideographs,
      Hangul syllables): removed, as origin removed them (the word they sat inside stays one word).
    - Anything else (a Cyrillic, Hebrew, Thai or Devanagari letter with no Latin look-alike, a
      Jamo, Bopomofo, an off-script punctuation mark or symbol, a full-width markup form, or a mix
      with the above): ONE space between two other characters, so it never glues the words on
      its two sides into one ("فعلдذلك" is said "فعل ذلك"); nothing next to a space or a line
      break (so a run between two spaces leaves both spaces), at the start or the end of the
      reply, after an opening bracket or quote, or before a closing one or a sentence mark
      (_OPENING, _CLOSING), so it never adds a space at an end or "word ." (a space stays
      wherever two words, or a word and another symbol, would otherwise touch). A stray letter
      inside a word therefore splits that word in two for the TTS and the chat (the cost;
      origin sent it to the TTS and the chat as it was).

    The guards never read this: it runs after them (guard_speech), on text they already passed.
    """
    run = m.group(0)
    if _REMOVED_BEFORE_RE.fullmatch(run):
        return ""
    start, end = m.span()
    prev = text[start - 1] if start else before
    nxt = text[end] if end < len(text) else ""
    if not prev or not nxt or prev.isspace() or nxt.isspace():
        return ""
    if prev in _OPENING or nxt in _CLOSING:
        return ""           # "(「word」)." is shown "(word)." (no word glued: the mark separates)
    return " "


# Punctuation a run next to it needs no space with: after an opening bracket or quote, before a
# closing one or a sentence mark. Never a letter, a digit or a mark, so no two words are glued.
# Besides ASCII: the guillemets and curly quotes, and in _CLOSING the Arabic comma, semicolon,
# question mark and full stop (U+060C, U+061B, U+061F, U+06D4) and the ellipsis (U+2026).
_OPENING = frozenset("([{«“‘\"'")
_CLOSING = frozenset(")]}»”’\"'.,!?;:،؛؟۔…")


def _tidy_part(text: str, before: str) -> str:
    """Take out each run of off-script characters (_run_out). ``text`` is mapped already;
    ``before`` is the character just before it ("" at the start of the reply)."""
    return _OFF_SCRIPT_RE.sub(lambda m: _run_out(text, m, before), text)


def tidy_off_script(text: str) -> str:
    """The off-script characters origin passed on, taken out of a whole reply AFTER the guards.

    First a mapping, one character to one (_OFF_SCRIPT_MAP): a letter that looks like a Latin
    letter becomes that Latin letter (HOMOGLYPHS: Cyrillic and Greek look-alikes and five Hebrew
    and Hangul ones), so "trusted аdult" is said "trusted adult"; the full-width forms of ASCII
    and the ideographic full stop, comma and space become their plain form, except the full-width
    markup forms (_NOT_MAPPED); a Devanagari or Thai digit becomes the ASCII digit ("call ๙๑๑"
    is said "call 911"). Then each run of the off-script characters left (_OFF_SCRIPT_RE) goes
    (_run_out): removed when it is only what origin removed, else one space between two other
    characters and nothing next to a space (so a run between two spaces leaves both spaces), at
    an end or next to the punctuation that needs no space there. Arabic, Latin, Greek letters
    with no look-alike, the other digits, ASCII punctuation, emoji and every other character are
    never touched.

    Runs only after the guards (TurnGuardMixin.guard_speech; ``OffScriptTidier`` for a stream,
    which gives the same text whatever the chunks). Never use it in front of a guard: the guards
    must read origin's text (see the comment above _OFF_SCRIPT_RE)."""
    if not text:
        return text
    return _tidy_part(text.translate(_OFF_SCRIPT_MAP), "")


_OFF_SCRIPT_TAIL_RE = re.compile(_OFF_SCRIPT_RE.pattern + r"\Z")


class OffScriptTidier:
    """``tidy_off_script`` for a stream, chunk by chunk: the joined output is exactly
    ``tidy_off_script`` of the joined input, whatever the chunks. A run of off-script characters
    at the end of a chunk is held back until the next character settles what it becomes (a
    space, or nothing next to a space or at the end), so only those characters are ever delayed."""

    __slots__ = ("_held", "_last")

    def __init__(self) -> None:
        self._held = ""     # a run of off-script characters at the end of the text so far (mapped)
        self._last = ""     # the last character released ("" before the first)

    def feed(self, chunk: str) -> str:
        if not chunk:
            return ""
        text = self._held + chunk.translate(_OFF_SCRIPT_MAP)
        m = _OFF_SCRIPT_TAIL_RE.search(text)
        cut = m.start() if m else len(text)
        self._held, part = text[cut:], text[:cut]
        if not part:
            return ""
        out = _tidy_part(part, self._last)
        self._last = part[-1]       # never an off-script character: a run at the end is held
        return out

    def flush(self) -> str:
        held, self._held = self._held, ""
        return _tidy_part(held, self._last) if held else ""


async def tidy_off_script_stream(text: AsyncIterable) -> AsyncIterator:
    """``OffScriptTidier`` over a stream of reply chunks: the LAST stage of the voice and the chat
    (TurnGuardMixin.guard_speech), after the card markers, the attribution guard and the
    scripture filter. A text chunk (a plain str) comes out as a plain str; anything else (a
    timed chunk, a sentinel) goes on unchanged, after the held text. Closing
    this stream closes the guard stream it reads, so the scripture filter's count and log still
    run when a speech is cut short."""
    tidier = OffScriptTidier()
    try:
        async for chunk in text:
            if type(chunk) is str:
                out = tidier.feed(chunk)
                if out:
                    yield out
                continue
            tail = tidier.flush()
            if tail:
                yield tail
            yield chunk
        tail = tidier.flush()
        if tail:
            yield tail
    finally:
        close = getattr(text, "aclose", None)
        if close is not None:
            await close()


def _strip_url(m: re.Match) -> str:
    url = m.group(0)
    stripped = url.rstrip(_URL_TRAIL)
    return " " + url[len(stripped):]


def _en_abbrev(m: re.Match) -> str:
    t = m.group(0)
    return " glorified and exalted is He " if "SWT" in t else " peace be upon him "


def clean_segment(text: str, lang: str, at_line_start: bool = True, context: str = "") -> str:
    """Clean one piece of text with a fixed language ("ar" or "en").

    Whitespace at the ends is kept so pieces can be concatenated.
    ``at_line_start`` says whether the first character begins a line, so
    heading and bullet markers are only removed where they really are markers.
    """
    if not text:
        return ""
    lang = "ar" if lang == "ar" else "en"

    text = _QURAN_STRAY_RE.sub("", text)
    text = strip_foreign_script(text)
    for symbol, spoken in HONORIFICS[lang].items():
        text = text.replace(symbol, f" {spoken} ")

    lines = text.split("\n")
    for i, line in enumerate(lines):
        if i > 0 or at_line_start:
            lines[i] = _LINE_MARKER_RE.sub("", line)
    text = "\n".join(lines)

    text = _IMG_RE.sub(r"\1", text)
    text = _LINK_RE.sub(r"\1", text)
    text = _URL_RE.sub(_strip_url, text)
    text = _EMAIL_RE.sub(" ", text)
    text = _FENCE_RE.sub(" ", text)
    text = _RULE_RE.sub(" ", text)
    text = _EMPH_RE.sub("", text)
    text = _UNDERSCORE_RE.sub("", text)
    text = text.replace("|", " ")

    text = _INVISIBLE_RE.sub("", text)
    text = _EMOJI_RE.sub(" ", text)

    if lang == "en":
        text = _EN_ABBREV_RE.sub(_en_abbrev, text)

    text = numbers_to_words(text, lang, context)

    text = _SPACE_BEFORE_PUNCT_RE.sub(r"\1", text)
    text = _MULTI_SPACE_RE.sub(" ", text)
    return text


# ---------------------------------------------------------------------------
# Streaming state machine
# ---------------------------------------------------------------------------


class _QuranGuardState:
    """Open/closed state of a Quran bracket, shareable across segments.

    ``cap`` is how much text an open bracket may swallow before speech resumes.
    ``None`` means never resume: stay silent until a bracket closes the span or the
    speech ends. speech_tts_text_transform() uses ``None`` because its state lives for
    one speech only; with a cap, the tail of a quoted span longer than the cap (a long
    verse with its harakat easily passes 400 characters) would be spoken, and the
    closing bracket would then be read as a new opener.
    """

    __slots__ = ("open", "dropped", "cap", "warned")

    def __init__(self, cap: int | None = _MAX_UNCLOSED_QURAN_CHARS) -> None:
        self.open = False
        self.dropped = 0
        self.cap = cap
        self.warned = False


def _find_bracket(s: str) -> int:
    for i, ch in enumerate(s):
        if ch in QURAN_BRACKETS:
            return i
    return -1


def _unclosed_link_start(buf: str) -> int | None:
    """Index where an unfinished markdown link/image starts, else None."""
    j = buf.rfind("[")
    if j < 0:
        return None
    tail = buf[j:]
    if len(tail) > _MAX_LINK_HOLD_CHARS:
        return None
    k = tail.find("]")
    if k >= 0:
        after = tail[k + 1:]
        if after and not (after.startswith("(") and ")" not in after):
            return None
    return j - 1 if j > 0 and buf[j - 1] == "!" else j


def _line_start_after(raw: str, prev: bool) -> bool:
    i = raw.rfind("\n")
    if i >= 0:
        return raw[i + 1:].strip() == ""
    return prev and raw.strip() == ""


class TTSTextStream:
    """Incremental cleaner. Feed chunks as they arrive, send the result on.

    Text is released only up to the last whitespace, so a number, URL,
    symbol or markdown link split across chunks is cleaned whole. An opening
    Quran bracket emits the neutral phrase at once and everything up to the
    closing bracket is discarded as it arrives (never buffered, never spoken).
    """

    def __init__(self, lang: LangSpec = "auto", *,
                 quran_state: _QuranGuardState | None = None) -> None:
        self._lang_spec = lang
        self._quran = quran_state or _QuranGuardState()
        self._buf = ""
        self._raw_tail = ""  # the last raw characters released, read as context for references
        self._line_start = True
        self._last_char = ""
        self._last_was_phrase = False
        self._last_lang = "ar"
        self._scripture = _ScriptureFilter()

    # -- language ---------------------------------------------------------
    def _configured_lang(self) -> str:
        spec = self._lang_spec
        return _norm_lang(spec() if callable(spec) else spec)

    def _segment_lang(self, raw: str) -> str:
        cfg = self._configured_lang()
        if cfg != "auto":
            self._last_lang = cfg
            return cfg
        self._last_lang = _detect_lang(raw, self._last_lang)
        return self._last_lang

    def _phrase_lang(self) -> str:
        cfg = self._configured_lang()
        return cfg if cfg != "auto" else self._last_lang

    # -- public -----------------------------------------------------------
    def feed(self, chunk: str) -> str:
        if not chunk:
            return ""
        self._buf += chunk
        return self._drain(final=False)

    def flush(self) -> str:
        out = self._drain(final=True) + self._scripture_flush()
        self._buf = ""
        return out

    # -- internals --------------------------------------------------------
    def _drain(self, final: bool) -> str:
        out: list[str] = []
        q = self._quran
        while True:
            if q.open:
                idx = _find_bracket(self._buf)
                budget = None if q.cap is None else q.cap - q.dropped
                if idx < 0 or (budget is not None and idx > budget):
                    if budget is not None and len(self._buf) > budget:
                        self._buf = self._buf[max(budget, 0):]
                        q.open = False
                        logger.warning(
                            "Quran bracket never closed; resuming speech after "
                            "%d dropped chars", q.dropped + max(budget, 0))
                        continue
                    q.dropped += len(self._buf)
                    self._buf = ""
                    if budget is None and not q.warned and q.dropped > _MAX_UNCLOSED_QURAN_CHARS:
                        q.warned = True
                        logger.warning(
                            "Quran bracket still open after %d chars; staying silent until "
                            "it closes or the speech ends", q.dropped)
                    break
                q.dropped += idx
                self._buf = self._buf[idx + 1:]
                q.open = False
                logger.info("Quran bracket closed; suppressed %d chars",
                            q.dropped)
                continue

            idx = _find_bracket(self._buf)
            if idx < 0:
                out.append(self._emit_safe(final))
                break
            pre, self._buf = self._buf[:idx], self._buf[idx + 1:]
            out.append(self._emit(pre))
            out.append(self._scripture_flush())
            q.open = True
            q.dropped = 0
            q.warned = False
            out.append(self._quran_phrase())
        return "".join(out)

    def _quran_phrase(self) -> str:
        logger.info("Quran bracket found in TTS text; speaking neutral phrase")
        if self._last_was_phrase:
            return ""
        phrase = QURAN_PHRASE[self._phrase_lang()]
        lead = " " if self._last_char and not self._last_char.isspace() else ""
        self._last_char = " "
        self._last_was_phrase = True
        return f"{lead}{phrase} "

    def _emit_safe(self, final: bool) -> str:
        buf = self._buf
        if final:
            cut = len(buf)
        else:
            i = len(buf) - 1
            while i >= 0 and not buf[i].isspace():
                i -= 1
            cut = i + 1
            hold = _unclosed_link_start(buf)
            if hold is not None and hold < cut:
                cut = hold
            if cut == 0 and hold is None and len(buf) > _MAX_UNBROKEN_CHARS:
                cut = len(buf)
        if cut <= 0:
            return ""
        raw, self._buf = buf[:cut], buf[cut:]
        return self._emit(raw)

    # -- scripture marks --------------------------------------------------
    def _render_scripture(self, parts: list[str]) -> str:
        """Join filter output, turning each run of drop markers into one neutral phrase."""
        text = "".join(parts)
        if _DROP_MARK not in text:
            return text
        phrase = QURAN_PHRASE[self._phrase_lang()]
        pieces: list[str] = []
        prev_char = self._last_char
        prev_phrase = self._last_was_phrase
        i = 0
        while i < len(text):
            if text[i] != _DROP_MARK:
                j = text.find(_DROP_MARK, i)
                j = len(text) if j < 0 else j
                pieces.append(text[i:j])
                if text[i:j].strip():
                    prev_phrase = False
                prev_char = text[j - 1]
                i = j
                continue
            k = i
            while k < len(text) and (text[k] == _DROP_MARK or text[k].isspace()):
                k += 1
            # whitespace that only separated dropped words goes with them
            if not prev_phrase:
                lead = " " if prev_char and not prev_char.isspace() else ""
                pieces.append(f"{lead}{phrase} ")
                prev_char = " "
                prev_phrase = True
                STATS["speech_cleaner_scripture"] += 1
                logger.warning("speech cleaner replaced scripture marks with the neutral phrase")
            i = k
        return "".join(pieces)

    def _scripture_pass(self, cleaned: str) -> str:
        """Run the lead's scripture filter over cleaned text, word by word."""
        if not cleaned:
            return cleaned
        f = self._scripture
        parts = [cleaned[: len(cleaned) - len(cleaned.lstrip())]]
        for piece in _WORD_RE.findall(cleaned):
            before = f.dropped
            got = f.feed(piece)
            if f.dropped > before:
                parts.append(_DROP_MARK)
            parts.append(got)
        if cleaned[-1:] and not cleaned[-1].isspace():
            # Released mid-word (before a bracket, at the end, or the long-unbroken escape
            # hatch): do not let the filter keep the last word back.
            before = f.dropped
            tail = f.flush()
            if f.dropped > before:
                parts.append(_DROP_MARK)
            parts.append(tail)
        return self._render_scripture(parts)

    def _scripture_flush(self) -> str:
        f = self._scripture
        before = f.dropped
        got = f.flush()
        parts = ([_DROP_MARK] if f.dropped > before else []) + [got]
        out = self._render_scripture(parts)
        if out.strip():
            self._last_was_phrase = out.rstrip().endswith(QURAN_PHRASE[self._phrase_lang()])
            self._last_char = out[-1]
        return out

    def _emit(self, raw: str) -> str:
        if not raw:
            return ""
        lang = self._segment_lang(raw)
        cleaned = clean_segment(raw, lang, at_line_start=self._line_start,
                                context=self._raw_tail)
        self._raw_tail = (self._raw_tail + raw)[-60:]
        cleaned = self._scripture_pass(cleaned)
        if self._last_char.isspace():
            cleaned = cleaned.lstrip(" 	")
        self._line_start = _line_start_after(raw, self._line_start)
        if cleaned:
            self._last_char = cleaned[-1]
            if cleaned.strip():
                self._last_was_phrase = cleaned.rstrip().endswith(
                    QURAN_PHRASE[self._phrase_lang()])
        return cleaned


# ---------------------------------------------------------------------------
# One-shot and async adapters
# ---------------------------------------------------------------------------


def prepare_for_tts(text: str | None, lang: LangSpec = "auto") -> str:
    """Clean a complete string for TTS. Empty or None gives ""."""
    if not text:
        return ""
    stream = TTSTextStream(lang)
    return (stream.feed(text) + stream.flush()).strip()


async def _clean_stream(text: AsyncIterable[str], lang: LangSpec,
                        state: _QuranGuardState) -> AsyncIterator[str]:
    stream = TTSTextStream(lang, quran_state=state)
    async for chunk in text:
        if not isinstance(chunk, str):  # e.g. a flush sentinel: pass through
            tail = stream.flush()
            if tail:
                yield tail
            yield chunk  # type: ignore[misc]
            continue
        out = stream.feed(chunk)
        if out:
            yield out
    tail = stream.flush()
    if tail:
        yield tail


def clean_tts_stream(text: AsyncIterable[str],
                     lang: LangSpec = "auto") -> AsyncIterator[str]:
    """Clean an async stream of text chunks (fresh Quran state)."""
    return _clean_stream(text, lang, _QuranGuardState())


def tts_text_transform(
    lang: LangSpec = "auto",
) -> Callable[[AsyncIterable[str]], AsyncIterable[str]]:
    """Build a livekit-agents ``tts_text_transforms`` entry.

    Create it once per session. The returned callable is invoked once per
    speech segment; the Quran bracket state lives in this closure so a verse
    split across segments stays suppressed.
    """
    state = _QuranGuardState()

    def _transform(text: AsyncIterable[str]) -> AsyncIterable[str]:
        return _clean_stream(text, lang, state)

    return _transform


def speech_tts_text_transform(
    lang: LangSpec = "auto",
) -> Callable[[AsyncIterable[str]], AsyncIterable[str]]:
    """The ``tts_text_transforms`` entry for a whole session. Create it ONCE per session.

    Like tts_text_transform(), but the Quran bracket state is kept per SPEECH, not per
    session. livekit-agents 1.5.1 runs all segments of one speech (segments end at tool
    calls) inside one asyncio task, in order (generation.py ``_tts_inference_task``), and
    calls the transform once per segment. A bracket that opens in one segment therefore
    still suppresses the text in the next segment of the same speech. A new speech (a
    new reply, or preemptive generation) runs in a new task and starts closed.

    A single state per session would let a reply that is interrupted (or discarded by
    preemptive generation) while inside a bracket leave the guard open, and the next
    reply would then be swallowed until a closing bracket or 400 characters. Outside a
    running task (plain sync use) one shared state is used, with that 400-character cap.

    The per-speech state has NO cap: an opening bracket keeps the speech silent until a
    bracket closes the span or the speech ends, however long the span is. A capped guard
    would speak the tail of a quoted span longer than the cap. The worst case is a stray
    bracket silencing the rest of one reply; the next reply starts closed.

    ``lang`` may be a callable, read each time text is released, so the language follows
    the live session language.
    """
    states: weakref.WeakKeyDictionary[asyncio.Task, _QuranGuardState] = (
        weakref.WeakKeyDictionary())
    shared = _QuranGuardState()

    def _state() -> _QuranGuardState:
        try:
            task = asyncio.current_task()
        except RuntimeError:  # no running loop
            return shared
        if task is None:
            return shared
        state = states.get(task)
        if state is None:
            state = states[task] = _QuranGuardState(cap=None)
        return state

    def _transform(text: AsyncIterable[str]) -> AsyncIterable[str]:
        return _clean_stream(text, lang, _state())

    return _transform
