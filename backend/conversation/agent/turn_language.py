"""The reply language of a turn: the PARENT's language, unless REPLY_LANGUAGE_FOLLOWS_CHILD is on.

The lead's design, and the default: the parent chooses the companion's language for the session,
and the prompt, the TTS, the speech cleaner, the guards and the fixed lines keep to it. (With the
speech-to-text on "auto", background noise came out as gibberish that the model read as another
language, for example Chinese, and replied in. A pinned language cannot do that.)

FLAG REPLY_LANGUAGE_FOLLOWS_CHILD (env var, default "0" = off; ``reply_language_follows_child``,
read on every call; "1", "on", "true" or "yes" = on).

- Off (the default): nothing in this module decides anything. Every language is exactly
  hk/12's: the session language for the prompt's LANGUAGE paragraph (prompt.build_instructions),
  the TTS, the speech cleaner, the attribution guard's decline line, the goodbye line, search_bank
  and the cards; hk/12's script check (turn_pipeline._turn_lang) for the fixed fallback lines.
  ``_prepare`` returns hk/12's turn note and nothing else: no TURN LANGUAGE line is added.
- On: ``decide_reply_language`` picks the reply language of each turn, under these rules:

  1. The parent's language (the session language) is the default: the first reply is in it.
  2. Only Arabic and English, never any other language.
  3. The reply moves AWAY from the parent's language only on a message that is clearly in the
     other supported language: a typed message of at least TYPED_MIN_WORDS real words, or a
     spoken turn of at least SPOKEN_MIN_WORDS real words, and those words are at least three
     quarters of the message's words (a short or mostly-noise fragment never switches). One word
     never switches, typed or spoken. A move to ENGLISH also needs English evidence: at least one
     word of ``EN_EVIDENCE`` (common English words that are not also common words of French,
     Spanish, German, Italian, Portuguese, Turkish or Indonesian), so a sentence in another
     Latin-script language ("je veux jouer avec toi", "saya mau main game") does not switch an
     Arabic session to English; it keeps the last reply language (rule 7).
  4. Letters of any other script (CJK, Kana, Hangul, Cyrillic, Greek, Hebrew, ...) are speech-to-
     text noise: they never count as a language, and they count against the three quarters. So do
     Latin tokens that are no real word (no vowel, a filler like "uh", a single letter other
     than "a" or "I").
  5. Arabic written in Latin letters (Arabizi: "marhaba habibi kifak") is never a reason to switch
     to English, nor to switch an English session to Arabic (rule 3 asks for the other language
     in its own script); in an Arabic session it brings the reply back to Arabic.
  6. Back to the parent's language: a message whose words are at least three quarters in the
     parent's language; one real word is enough (the parent's language is the default, and the
     speech-to-text, fixed to it, writes in it).
  7. Anything else (unclear, mixed, noise, emoji, digits only) keeps the language of the last
     reply: the parent's language until the child has clearly switched.
  8. A spoken turn that holds a phrase speech-to-text models are known to invent from silence,
     music or noise (``STT_HALLUCINATIONS``: "thank you for watching", "اشتركوا في القناة", ...)
     keeps the language of the last reply, whatever else it holds. Beyond that list a spoken
     switch trusts the speech-to-text's words (it is pinned to the parent's language, so it
     rarely writes the other one).

Pure and synchronous. No scripture, no model call, no I/O.
"""
from __future__ import annotations

import os
import re

FOLLOWS_CHILD_ENV = "REPLY_LANGUAGE_FOLLOWS_CHILD"
_ON_VALUES = ("1", "on", "true", "yes")

TYPED_MIN_WORDS = 2     # a typed message: at least two real words of the other language
SPOKEN_MIN_WORDS = 3    # a spoken turn: several real words, never a single word or a fragment


def reply_language_follows_child() -> bool:
    """Does the reply language follow the child (the CEO's rule)? Off unless the env var
    ``REPLY_LANGUAGE_FOLLOWS_CHILD`` is "1" (or on/true/yes). Read on every call, never cached."""
    return (os.getenv(FOLLOWS_CHILD_ENV) or "0").strip().lower() in _ON_VALUES


_ARABIC_RE = re.compile("[؀-ۿݐ-ݿࢠ-ࣿﭐ-﷿ﹰ-﻿]")
_LATIN_RE = re.compile("[A-Za-zÀ-ɏ]")
_EDGE_RE = re.compile(r"^[^\w]+|[^\w]+$")

# Sounds, not words: the speech-to-text writes them for breath, hesitation and background noise.
_FILLERS = frozenset({
    "uh", "uhh", "uhm", "um", "umm", "er", "erm", "eh", "ah", "ahh", "aah", "oh", "ohh", "ooh", "oo",
    "ha", "haha", "hahaha", "hehe", "huh", "mhm", "aw", "ow",
    "اه", "آه", "أه", "ام", "امم", "مم", "ممم", "هه", "ههه", "هههه", "اوه", "أوه",
})

# Arabizi digits stand for Arabic letters (3 = ع, 5 = خ, 7 = ح, 9 = ق). A token with at least
# three letters and such a digit BEFORE its last letter is a strong signal ("7abibi", "5ayef");
# "3rd", "5th", "mp3" are not. A digit only at the END of the token ("level5", "grade5", "lvl3",
# "top3", "covid19") is the way English names levels and numbers, so it is a weak signal.
_ARABIZI_DIGIT_RE = re.compile(r"^[a-z]*(?:[3579][a-z]*)+$")
_TRAILING_DIGITS_ONLY_RE = re.compile(r"^[a-z]+[0-9]+$")
# Words that are not English. Single hits are weak (a child can quote one), two are strong.
_ARABIZI_WORDS = frozenset({
    "marhaba", "mar7aba", "habibi", "habibti", "7abibi", "7abibti", "kifak", "kifik", "kifek",
    "shlonak", "shlonik", "shlonek", "inta", "enta", "inti", "enti", "yalla", "yallah", "wallah",
    "walla", "shukran", "shokran", "ahlan", "tamam", "lesh", "leish", "laish", "tayeb", "tayyeb",
    "aywa", "kwayyes", "kwayes", "mabsoot", "mabsout", "shu", "shou", "ya3ni", "yaani",
    "habibe", "ana", "hayda", "hada", "haida", "mish", "ktir", "kteer", "bas", "zaki", "zaky",
})
# "ana", "bas", "hada" and "mish" are Arabizi but also short English or names: they count only
# next to another hit, never alone.
_WEAK_ONLY = frozenset({"ana", "bas", "hada", "mish", "zaki", "zaky", "shu", "shou"})
# Some of the words above are also names ("Tayeb", "Habibi", "Inti", "Haida"). Next to plain
# English words a listed word is read as a name, not as Arabizi: "I'm Tayeb", "hi habibi",
# "my cat Habibi is sleeping". (The digit spellings, "7abibi", are never names and still count.)
_EN_CONTEXT = frozenset({
    "i", "i'm", "im", "i’m", "my", "name", "name's", "is", "it's", "its", "it’s", "me", "call", "called",
    "hi", "hello", "hey", "the", "a", "this", "that", "he", "she", "he's", "she's", "his", "her",
    "mr", "mrs", "ms", "dear", "friend", "with", "and", "to", "from", "for", "of", "you", "your",
    "we", "our", "they", "their", "cat", "dog", "brother", "sister", "cousin", "teacher",
})


# English evidence for a move to English (rule 3). Common English words, lower case, that are not
# also a common word of French, Spanish, German, Italian, Portuguese, Turkish or Indonesian: left
# out on purpose are "a", "i", "in", "on", "to", "so", "no", "me", "do", "can", "come", "was",
# "will", "die", "man", "an", "also", "kind", "name", "hand", "bad", "see", "red", "son", "game",
# "question" and "secret".
EN_EVIDENCE = frozenset({
    # function words
    "the", "and", "you", "your", "you're", "youre", "my", "we", "our", "they", "their", "them",
    "he", "she", "his", "her", "him", "it", "it's", "its", "i'm", "im", "i've", "i'll", "i'd",
    "is", "are", "am", "were", "been", "have", "has", "had", "does", "did", "don't", "dont",
    "doesn't", "didn't", "can't", "cant", "could", "would", "should", "let's", "lets",
    "what", "what's", "whats", "how", "why", "when", "where", "who", "which", "this", "that",
    "these", "those", "there", "here", "with", "about", "from", "not", "just", "very", "really",
    "because", "some", "something", "more", "again",
    # words a child says often
    "want", "wanna", "like", "love", "know", "think", "feel", "need", "tell", "say", "said", "says",
    "speak", "talk", "help", "play", "make", "made", "learn", "read", "draw", "sing", "watch",
    "listen", "look", "give", "take", "get", "got", "go", "ask", "answer",
    "please", "thanks", "thank", "sorry", "hello", "hi", "hey", "yes", "yeah",
    "good", "happy", "sad", "scared", "afraid", "funny", "joke", "song", "story", "friend",
    "mom", "mum", "dad", "brother", "sister", "teacher", "school", "home", "cat", "dog",
    "today", "tomorrow", "yesterday", "night", "morning", "food", "eat", "sleep",
    "hurt", "hurts", "hit", "hits", "touch", "touches", "touched", "alone",
})

# Phrases speech-to-text models write for silence, music or noise (rule 8). Only spoken turns are
# checked; matched after ``_norm_phrase`` on both sides, as whole words.
STT_HALLUCINATIONS = (
    "thank you for watching", "thanks for watching", "thank you so much for watching",
    "please subscribe", "subscribe to my channel", "like and subscribe",
    "see you in the next video",
    "ترجمة نانسي قنقر", "نانسي قنقر", "اشتركوا في القناة", "اشترك في القناة",
    "شكرا للمشاهدة", "شكرا على المشاهدة", "لا تنسوا الاشتراك",
)
_TASHKEEL_RE = re.compile("[ؐ-ًؚ-ٰٟـ]")
_NOT_LETTER_RE = re.compile(r"[\W\d_]+")


def _norm_phrase(text: str) -> str:
    """Lower case, no tashkeel or tatweel, alef forms to "ا", "ة" to "ه", "ى" to "ي", every run of
    non-letters to one space, with a space at each end (so a phrase matches whole words only)."""
    text = _TASHKEEL_RE.sub("", (text or "").lower())
    for a, b in (("أ", "ا"), ("إ", "ا"), ("آ", "ا"), ("ة", "ه"), ("ى", "ي")):
        text = text.replace(a, b)
    return " " + " ".join(_NOT_LETTER_RE.sub(" ", text).split()) + " "


_HALLUCINATIONS_NORM = tuple(_norm_phrase(p) for p in STT_HALLUCINATIONS)


def _is_hallucination(text: str) -> bool:
    norm = _norm_phrase(text)
    return any(p in norm for p in _HALLUCINATIONS_NORM)


def _norm(lang: str | None) -> str:
    return "ar" if (lang or "").strip().lower().startswith("ar") else "en"


def _kind(tok: str) -> str:
    """"ar" or "en" for a real word, "noise" for a token that is no word of either language, ""
    for a token that counts for nothing (digits, emoji, punctuation, one Arabic letter)."""
    ar = en = other = 0
    for ch in tok:
        if not ch.isalpha():
            continue
        if _ARABIC_RE.match(ch):
            ar += 1
        elif _LATIN_RE.match(ch):
            en += 1
        else:
            other += 1                  # CJK, Kana, Hangul, Cyrillic, Greek, Hebrew, ...
    if other or (ar and en):
        return "noise"
    low = tok.lower()
    if ar:
        if low in _FILLERS:
            return "noise"
        return "ar" if ar >= 2 else ""
    if en:
        if en == 1:
            return "en" if low in ("a", "i") else "noise"
        if low in _FILLERS or not any(v in low for v in "aeiouyàáâäèéêëìíîïòóôöùúûü"):
            return "noise"
        return "en"
    return ""


def _is_arabizi(latin_tokens: list[str]) -> bool:
    """One or two Latin tokens: a single strong signal is enough. Three or more: two signals
    (a plain English sentence with one odd token stays English). A listed word next to plain
    English words is a name (``_EN_CONTEXT``): in a one- or two-word message it never counts, in
    a longer one it does not count when capitalised after the first word."""
    strong = weak = 0
    english = any(tok.lower() in _EN_CONTEXT for tok in latin_tokens)
    for idx, tok in enumerate(latin_tokens):
        low = tok.lower()
        letters = sum(1 for ch in low if "a" <= ch <= "z")
        if letters >= 3 and _ARABIZI_DIGIT_RE.match(low) and any(d in low for d in "3579"):
            if _TRAILING_DIGITS_ONLY_RE.match(low):
                weak += 1                   # level5, grade5, lvl3, top3
            else:
                strong += 1                 # 7abibi, 5ayef, ma3rafsh
        elif low in _ARABIZI_WORDS:
            if english and (len(latin_tokens) <= 2 or (idx > 0 and tok[:1].isupper())):
                continue                    # a name: "I'm Tayeb", "my cat Habibi is asleep"
            if low in _WEAK_ONLY:
                weak += 1
            else:
                strong += 1
    if len(latin_tokens) <= 2:
        return strong >= 1
    return strong >= 2 or (strong >= 1 and weak >= 1)


def decide_reply_language(text: str, parent: str | None, previous: str | None = None, *,
                          typed: bool = False) -> str:
    """"ar" or "en": the reply language of this turn, with REPLY_LANGUAGE_FOLLOWS_CHILD on.

    ``parent`` is the session language the parent chose; ``previous`` the reply language of the
    turn before (the parent's language when None); ``typed`` is True for a typed message, False
    for a spoken turn (the speech-to-text's words). The rules are in the module docstring."""
    parent = _norm(parent)
    known = (previous or "").strip().lower()[:2] in ("ar", "en")
    prev = _norm(previous) if known else parent        # an unknown previous language: the parent's
    other = "en" if parent == "ar" else "ar"
    if not typed and _is_hallucination(text):
        return prev                                       # rule 8
    counts = {"ar": 0, "en": 0, "noise": 0}
    latin_tokens: list[str] = []
    english_evidence = False
    for raw in (text or "").split():
        tok = _EDGE_RE.sub("", raw)
        if not tok:
            continue
        kind = _kind(tok)
        if kind:
            counts[kind] += 1
        if kind == "en" and tok.lower().replace("’", "'") in EN_EVIDENCE:
            english_evidence = True
        if _LATIN_RE.search(tok) and not any(
                ch.isalpha() and not _LATIN_RE.match(ch) for ch in tok):
            latin_tokens.append(tok)
    total = counts["ar"] + counts["en"] + counts["noise"]

    def clear(lang: str, minimum: int) -> bool:
        n = counts[lang]
        return n >= minimum and n * 4 >= total * 3

    if not counts["ar"] and latin_tokens and _is_arabizi(latin_tokens):
        return "ar" if parent == "ar" else prev           # rule 5
    if clear(other, TYPED_MIN_WORDS if typed else SPOKEN_MIN_WORDS) and (
            other == "ar" or english_evidence):
        return other                                      # rule 3
    if clear(parent, 1):
        return parent                                     # rule 6
    return prev                                           # rule 7


LANG_NAME = {"ar": "Arabic", "en": "English"}


def language_line(lang: str) -> str:
    """The per-turn instruction, added (flag on only) after the turn note, on its own line, when the
    reply language differs from the session's or from the last turn's."""
    name = LANG_NAME.get(lang, "English")
    return (
        f"TURN LANGUAGE: reply in {name} on this turn, including any 'I am an AI' line. Never reply "
        "in a language other than Arabic or English."
    )


__all__ = ["FOLLOWS_CHILD_ENV", "TYPED_MIN_WORDS", "SPOKEN_MIN_WORDS", "EN_EVIDENCE", "STT_HALLUCINATIONS",
           "reply_language_follows_child", "decide_reply_language", "language_line", "LANG_NAME"]
