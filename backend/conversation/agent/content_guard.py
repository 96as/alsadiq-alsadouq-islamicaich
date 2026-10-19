"""The "never scripture" check (BEHAVIOUR-SPEC 4.4 and 6.2), shared by the gesture planner and the
al.search publisher.

It holds meta-words (words that SAY a text is a verse or a report of the Prophet's words), never any
such text. A string is "scripture-like" when it contains one of the meta-words as a word, or when more
than 20% of its Arabic letters carry harakat (fully vowelled Arabic is how verses are printed).

Pure standard library, no I/O, safe to call on the audio path (a few microseconds per clause).
"""
from __future__ import annotations

import re

DIACRITIC_LIMIT = 0.20

_DIACRITICS = re.compile("[ؐ-ًؚ-ٰٟۖ-ۭ]")
_ARABIC_LETTER = re.compile("[ء-يٱ-ۓۺ-ۼ]")
_TATWEEL_AND_MAP = str.maketrans({
    "ـ": None,
    "أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا",
    "ى": "ي", "ؤ": "و", "ئ": "ي",
    "’": "'", "‘": "'",
})
_WORD = re.compile(r"[\w']+", re.UNICODE)
_ARABIC_PREFIXES = ("وال", "بال", "فال", "كال",
                    "لل", "ال", "و", "ف", "ب", "ل")

# Single meta-words, normalised (diacritics off, alef and ya folded, lower case). The ta marbuta is NOT
# folded: the colloquial "eeh" (what, yes) must not look like "ayah".
_META_WORDS = frozenset([
    # Arabic
    "سورة", "سوره",   # surah (both spellings)
    "اية", "ايات",   # ayah, ayat (not the colloquial "إيه")
    "حديث", "احاديث",   # hadith, hadiths
    "رواه",              # narrated by
    "قران", "قراني", "القران",   # quran
    "تفسير",        # tafsir
    # English
    "quran", "qur'an", "koran", "surah", "surahs", "sura", "ayah", "ayahs", "ayat", "hadith", "hadiths",
    "verse", "verses", "tafsir", "bukhari", "sahih",
])
# Two-word meta phrases (normalised, single spaces).
_META_PHRASES = (
    "قال رسول",      # "the messenger of ... said"
    "قال النبي",
    "قال الله تعالى",
    "قال الله",
    "prophet said", "messenger said", "allah said", "god said", "narrated by",
)
_PHRASE_RES = None


def normalise(text: str) -> str:
    if not text:
        return ""
    s = _DIACRITICS.sub("", str(text)).translate(_TATWEEL_AND_MAP).lower()
    return " ".join(_WORD.findall(s))


def _tokens_match(norm: str) -> bool:
    for tok in norm.split():
        if tok in _META_WORDS:
            return True
        for p in _ARABIC_PREFIXES:                     # والحديث, بالسوره, ...
            if tok.startswith(p) and tok[len(p):] in _META_WORDS:
                return True
    return False


def has_meta_word(text: str) -> bool:
    """True when the text contains a meta-word or meta-phrase (spec 4.4)."""
    norm = normalise(text)
    if not norm:
        return False
    if _tokens_match(norm):
        return True
    padded = " " + norm + " "
    for phrase in _META_PHRASES:
        if (" " + phrase + " ") in padded:
            return True
    return False


def diacritic_ratio(text: str) -> float:
    """Marks per Arabic letter (0 when the text has no Arabic letter)."""
    if not text:
        return 0.0
    letters = len(_ARABIC_LETTER.findall(str(text)))
    if letters == 0:
        return 0.0
    return len(_DIACRITICS.findall(str(text))) / letters


def heavily_vowelled(text: str) -> bool:
    return diacritic_ratio(text) > DIACRITIC_LIMIT


def looks_like_scripture(text: str) -> bool:
    """The whole check: a meta-word, or more than 20% of the Arabic letters carrying harakat."""
    try:
        return has_meta_word(text) or heavily_vowelled(text)
    except Exception:  # never raise on the audio path; an unreadable string is treated as unsafe
        return True
