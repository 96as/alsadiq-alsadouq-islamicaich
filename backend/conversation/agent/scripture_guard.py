"""Output-side guards that keep scripture out of the child's ears and eyes.

Two independent defences, both applied to the reply text stream (``tts_node``
for the audio and ``transcription_node`` for the chat bubble / saved message,
see ``turn_pipeline.TurnGuardMixin``):

(a) ``filter_scripture_stream``: drops ornate-bracket spans and runs of Arabic
    carrying dense Quranic marks, so a verse written with its recitation marks
    is never synthesised. Verses are only ever played as recitation audio.
    KNOWN LIMITATION: a verse written in plain script (no waqf marks, no
    ornate brackets) is NOT detected; fuzzy matching against the Quran text is
    not done. The prompt rules and the attribution check below are the defence
    for that case.
(b) ``guard_attribution_stream``: if the reply attributes a saying to the
    Prophet, Allah, the Quran or "a hadith" ("the Prophet said", "قال رسول
    الله" ...) in a turn where nothing was served from the bank, the rest of
    the reply is dropped and replaced with the DECLINE template. The prompt asks
    the model not to do this; this is the check that does not depend on the
    model obeying. It only knows the phrasings listed below.

KNOWN LIMITATION (false positive only, never a miss): the name of Yahya is recognised as
"يحيى بن/ابن زكريا" or "يحيى عليه السلام"; the spelling "زكرياء" (with the final hamza) is not read as
his father's name, so "كان النبي يحيى ابن زكرياء ..." is declined like a claim. A needless decline line
is the safe side; it is left as is.

Pure functions and async stream wrappers, no Django, no network, no text in logs.
"""
from __future__ import annotations

import logging
import re
from collections import Counter
from collections.abc import AsyncIterable, Callable

logger = logging.getLogger(__name__)

# Counters for eval / ops (no text is ever stored).
STATS: Counter = Counter()

ORNATE_OPEN = "\ufd3f"   # ornate right parenthesis, opens a Quran span in print
ORNATE_CLOSE = "\ufd3e"  # ornate left parenthesis, closes it
# Waqf/recitation marks, small high letters, dagger alef, extended Arabic marks.
_QMARK = re.compile("[\u0615-\u061a\u06d6-\u06ed\u0670\u08d3-\u08ff]")
_PIECE = re.compile(r"\S+\s*")
_BRACE_CAP = 40  # longest "{{...}}" marker body dropped in one go, a stray "{{" must not eat the reply
_ARABIC = re.compile("[\u0600-\u06ff]")

DECLINE_TEXT = {
    "en": (
        "That's a beautiful question. "
        "I couldn't find that in my library right now."
    ),
    "ar": (
        "هذا سؤال جميل. "
        "لم أجد ذلك في مكتبتي الآن."
    ),
}


def qmark_count(token: str) -> int:
    return len(_QMARK.findall(token))


# ---------------------------------------------------------------- (a) filter

def strip_scripture(text: str) -> str:
    """Pure helper: remove ornate-bracket spans and dense-Quranic-mark runs."""
    f = _ScriptureFilter()
    return f.feed(text) + f.flush()


class _ScriptureFilter:
    """Stateful so spans and words can cross streaming chunk boundaries."""

    def __init__(self) -> None:
        self.in_span = False
        self.brace_n = 0         # 0 outside braces, 1 after "{", 2 after "{{" (a verse marker)
        self.brace_len = 0       # chars swallowed inside the current brace span
        self.brace_closing = False  # saw one "}" of a closing "}}"
        self.carry = ""          # visible text of an unfinished word
        self.held: str | None = None  # a lone single-mark word, undecided
        self.prev_dropped = False
        self.dropped = 0
        self.braces_dropped = 0  # {...} spans, counted apart from scripture drops

    def _despan(self, chunk: str) -> str:
        out = []
        for ch in chunk:
            # ornate spans first: a brace inside one is span content, and an ornate bracket
            # inside a brace span ends the brace (so neither can swallow the rest of a reply)
            if self.in_span:
                if ch == ORNATE_CLOSE:
                    self.in_span = False
                continue
            if ch == ORNATE_OPEN:
                self.brace_n = 0
                self.in_span = True
                self.dropped += 1
                continue
            if ch == ORNATE_CLOSE:
                continue
            # braces are never speech. A "{{...}}" marker is dropped whole (spaces inside
            # included, at most _BRACE_CAP chars, then speech resumes); a single "{" drops
            # only up to the next space. State survives chunk splits.
            if self.brace_n:
                if self.brace_n == 1:
                    if ch == "{" and self.brace_len == 0:
                        self.brace_n = 2
                        continue
                    if ch == "}" or ch.isspace():
                        self.brace_n = 0
                        if ch.isspace():
                            out.append(ch)
                        continue
                    self.brace_len += 1
                    continue
                if ch == "}":
                    if self.brace_closing:
                        self.brace_n = 0
                    self.brace_closing = not self.brace_closing
                    continue
                self.brace_closing = False
                self.brace_len += 1
                if self.brace_len <= _BRACE_CAP:
                    continue
                self.brace_n = 0  # unterminated: drop what was swallowed, resume with ch
            if ch == "{":
                self.braces_dropped += 1
                self.brace_n, self.brace_len, self.brace_closing = 1, 0, False
                continue
            if ch == "}":
                continue
            out.append(ch)
        return "".join(out)

    def _piece(self, piece: str) -> str:
        q = qmark_count(piece)
        if q >= 2:
            self.dropped += 1
            self.held = None
            self.prev_dropped = True
            return ""
        if q == 1:
            if self.prev_dropped:
                self.dropped += 1
                self.held = None
                return ""
            if self.held is not None:
                self.dropped += 2
                self.held = None
                self.prev_dropped = True
                return ""
            self.held = piece
            return ""
        out = (self.held or "") + piece
        self.held = None
        self.prev_dropped = False
        return out

    def feed(self, chunk: str) -> str:
        s = self.carry + self._despan(chunk)
        pieces = _PIECE.findall(s)
        self.carry = ""
        if pieces and not pieces[-1][-1].isspace():
            self.carry = pieces.pop()
        return "".join(self._piece(p) for p in pieces)

    def flush(self) -> str:
        out = ""
        if self.carry:
            out += self._piece(self.carry)
            self.carry = ""
        if self.held is not None:
            out += self.held
            self.held = None
        return out


async def filter_scripture_stream(text: AsyncIterable[str], count: bool = True) -> AsyncIterable[str]:
    """Drop scripture-like spans from a reply. ``count=False`` for the second copy of
    the same reply (the transcript) so the counter and log record it once."""
    f = _ScriptureFilter()
    try:
        async for chunk in text:
            out = f.feed(chunk)
            if out:
                yield out
        tail = f.flush()
        if tail:
            yield tail
    finally:
        if f.dropped and count:
            STATS["scripture_stripped"] += f.dropped
            logger.warning("tts scripture filter dropped %d span(s)", f.dropped)
        if f.braces_dropped and count:
            STATS["braces_dropped"] += f.braces_dropped
            logger.warning("tts guard dropped %d brace span(s)", f.braces_dropped)


# ------------------------------------------------------- (b) attribution check
# English runs on the lower-cased text. Arabic runs on normalised text: no
# tashkeel, alef variants -> ا, ى -> ي, ة -> ه (\ufdfa is dropped before matching).
# A subject may be followed by a short blessing or adverb ("peace be upon him",
# "once", "also") before the verb; only those words are tolerated in the gap.
#
# Two kinds of attribution, licensed separately by what was served this turn:
#   "hadith": words put in the Prophet's mouth, "a hadith says", narrations
#   "quran":  "Allah says", "the Quran says"
# A verse licenses "quran" only, a hadith item licenses "hadith" only. Excerpt
# items (faq, tafsir, aqidah, fiqh, sirah) license both; terms and stories neither.

KINDS = frozenset({"hadith", "quran"})

# Separators that may sit around a blessing: whitespace, commas, brackets, the three dashes and the
# sentence punctuation ("النبي -صلى الله عليه وسلم- قال", "the Prophet -peace be upon him- said",
# "The Prophet: of Allah said", "The Prophet！ of Allah said"). Each is a separator like a comma, so an
# attribution cannot be split from its verb by punctuation. Escapes only, no literal Arabic in a class:
# ASCII : ; ! ? . / full-width ！ ： ； ？ ， ． / Arabic ، ؛ ؟ / the ellipsis …
_SEP = (r"\s,()\-\u2013\u2014:;!?."
        r"\uff01\uff1a\uff1b\uff1f\uff0c\uff0e"
        r"\u060c\u061b\u061f\u2026")
_DASHES = "-\u2013\u2014"
_EN_GAP = (
    r"(?:[" + _SEP + r"]+(?:peace|be|upon|him|pbuh|saw|may|allah|bless|blessings|and|grant|"
    r"once|also|often|always|really|then|again|just|of|muhammad|usually|sometimes))*[" + _SEP + r"]*"
)
# adverbs that may stand between "used to" / "would" and the verb ("would often say", "used to always tell")
_EN_ADV = r"(?:(?:also|often|always|once|really|just|then|again|usually|sometimes)\s+)*"
_EN_SAY = (
    r"(?:said|says|say|told|tells|taught|teaches|mentioned|narrated|stated|advised|"
    r"commanded|reported|used\s+to\s+" + _EN_ADV + r"(?:say|tell|teach)|would\s+" + _EN_ADV + r"say)\b"
)
_EN_HADITH = [
    r"\b(?:(?:the|our)\s+)?(?:(?:holy|beloved|dear|last)\s+)?(?:prophet|messenger)\b"
    + _EN_GAP + _EN_SAY,
    r"\b(?:a|the|this|that|one)\s+(?:famous\s+|well\s+known\s+)?hadith\s+(?:that\s+)?"
    r"(?:says|said|tells|states|mentions|teaches)\b",
    r"\bthere\s+is\s+a\s+(?:famous\s+|well\s+known\s+)?hadith\b",
    r"\bin\s+(?:a|the)\s+hadith\b",
    r"\b(?:the|this)\s+hadith\s+(?:is\s+)?(?:on|in|shown\s+on)\s+(?:your|the)\s+(?:screen|card)\b",
    r"\baccording\s+to\s+(?:a\s+|the\s+)?(?:hadith|sunnah)\b",
    r"\bit\s+is\s+narrated\b",
    r"\bnarrated\s+that\b",
]
_EN_QURAN = [
    # "the Messenger of Allah said" is a hadith attribution, not "Allah says"
    r"(?<!of\s)\ballah(?:[" + _SEP + r"]+(?:the\s+)?(?:almighty|exalted|most\s+high|most\s+merciful|swt|subhanahu\s+wa\s+ta'?ala))?[" + _SEP + r"]+"
    r"(?:says|said|tells\s+us|told\s+us|commands|commanded|teaches|taught|promises|"
    r"promised|orders|ordered|reminds\s+us)\b",
    r"\bin\s+the\s+quran\b[\s,]*(?:it\s+|allah\s+)?(?:says|said|tells|teaches|mentions|states|reminds)\b",
    r"\bin\s+the\s+quran,?\s+allah\b",
    r"\bthe\s+quran\s+(?:says|tells|teaches|mentions|states|reminds)\b",
    r"\baccording\s+to\s+(?:a\s+|the\s+)?quran\b",
]
_AR_GAP = (
    r"(?:[" + _SEP + r"]+(?:عليه|عليها|السلام|الصلاه|والسلام|صلي|الله|وسلم|مره|ايضا|دائما|احيانا|كان|محمد|الكريم|واله|وصحبه))*[" + _SEP + r"]*"
)
# one Arabic letter (hamza to ya), built from code points so no literal range sits in the source
_AR_LETTER = "[" + chr(0x621) + "-" + chr(0x64A) + "]"
_AR_SAY = r"(?:قال|يقول|علمنا|اخبرنا|امرنا|اوصي|اوصانا|حدثنا|نصحنا)"
# "لأن/بأن/وأن/فإن" (a proclitic directly glued to "أن"/"إن") normalise to "لان"/"بان"/
# "وان"/"فان": the letter survives in front of "ان", so the lead-in rules below are given
# this optional one-letter prefix too. Without it, "لأن النبي كان يحب كذا" still matches as
# a whole string (the normalised "ان" sits right there, one letter in), but the match
# starts one letter late: on the streaming path that stray letter (the proclitic's "ل"/
# "ب"/"و"/"ف") would be emitted before the decline (see review follow-up, round 2).
_AR_PROCLITIC = r"(?:[لبوف])?"
# The pieces of the verb-first / subject-first rules. _AR_NO_LETTER_BEFORE keeps "النبي"/"كان"
# from matching inside a longer word; the optional one-letter prefix is "و/ف" (and "ب" on the
# subject) so "وكان النبي" and "والنبي كان" match from their first letter, not one letter in.
_AR_NO_LETTER_BEFORE = r"(?<!" + _AR_LETTER + r")"
_AR_NO_LETTER_AFTER = r"(?!" + _AR_LETTER + r")"
# The same check for text that is still streaming. A word that touches the end of the buffer is
# not finished: the next token may extend it. The reply is streamed as raw model tokens, and
# o200k splits an Arabic word below word level ("يتيما" arrives as " ي" + "تي" + "ما"), so at
# "...كان النبي يتي" the letters seen so far already look like an imperfect verb. In live mode a
# word-final check therefore demands a real non-letter after the word and does not pass at the
# end of the buffer: a match that ends on a partial word is undecided (held), and the same rule
# decides it once the word completes. The final check (a complete text) uses _AR_NO_LETTER_AFTER.
_AR_WORD_DONE_LIVE = r"(?=[^" + chr(0x621) + "-" + chr(0x64A) + r"])"


def _word_end(live: bool) -> str:
    return _AR_WORD_DONE_LIVE if live else _AR_NO_LETTER_AFTER


_AR_SUBJ = r"(?:رسول\s+الله|النبي|الرسول|نبينا|نبي\s+الله)" + _AR_NO_LETTER_AFTER
_AR_Y_WHOLE_NAMES = r"(?:يوسف|يعقوب|يونس|يوشع)" + _AR_NO_LETTER_AFTER
# "يحيى" is the name when «عليه السلام» or «بن» / «ابن» + «زكريا» ("son of Zakariya", his only
# father) follows it. A bare «ابن» is NOT the marker: «يحيي ابن عمه» / «يحيي ابنته» is the verb "greets".
_AR_Y_YAHYA_NAME = (
    r"يحيي(?=[" + _SEP + r"]+(?:عليه[" + _SEP + r"]+السلام|ا?بن[" + _SEP + r"]+زكريا)"
    + _AR_NO_LETTER_AFTER + r")"
)
# While a reply is still streaming, "كان النبي يحيى " may be followed by "عليه السلام" that has not
# arrived yet. The live variant treats a "يحيي" whose remainder is empty, or only the start of
# "عليه السلام" / "بن زكريا" / "ابن زكريا" (down to the partial «ابن زكري»), as undecided (see
# find_attribution(final=False)); the stream then holds the text instead of cutting. The final check
# (the whole reply, and the flush at the end of the stream) never uses the live variant, so
# "كان النبي يحيي" at the end of a reply is still caught. While the marker is partial the FINAL rule
# already reads «يحيي ابن» as the verb (only «ابن زكريا» is the name), so the wrapper holds the whole
# pending text until the next token settles it: «ابن» + «ته» ("his daughter") is then a claim.
_AR_Y_YAHYA_UNDECIDED = (
    r"يحيي(?=[" + _SEP + r"]*(?:ا?(?:ب(?:ن(?:[" + _SEP + r"]+(?:ز(?:ك(?:ر(?:ي)?)?)?)?)?)?)?"
    r"|ع(?:ل(?:ي(?:ه(?:[" + _SEP + r"]+(?:ا(?:ل(?:س(?:ل(?:ا(?:م)?)?)?)?)?)?)?)?)?)?)$)"
)


def _impf(y_names: str, live: bool = False) -> str:
    """An imperfect verb (ي + two or more letters), minus the whole-word ي-nouns and the
    ي-names, optionally negated. ``live`` (text still streaming) also demands that the verb
    is a finished word: a trailing partial word is undecided, not a verb (see _AR_WORD_DONE_LIVE)."""
    return (
        r"(?:(?:لا|لم|ما|قد)[\s,()]+)?"
        r"(?!(?:(?:يتيم|يقين|يهودي|يمني)ا?" + _AR_NO_LETTER_AFTER + r")|" + y_names + r")ي"
        + _AR_LETTER + r"{2,}" + (_word_end(True) if live else "")
    )


_AR_KANA = r"كان(?=[" + _SEP + r"])"


def _idha(live: bool) -> str:
    return r"اذا" + _word_end(live)


def _faala(live: bool) -> str:
    return r"فعل" + _word_end(live)


def _subj_first(impf: str, live: bool = False) -> str:
    # "النبي كان يحب كذا" / "النبي فعل كذا" (also after "ان النبي ..." and "والنبي ...")
    return (
        r"(?:" + _AR_NO_LETTER_BEFORE + r"[لبوف]?ان\s+)?" + _AR_NO_LETTER_BEFORE + r"(?:[وفب])?" + _AR_SUBJ
        + _AR_GAP + r"(?:" + _AR_KANA + _AR_GAP + r"(?:" + impf + r"|" + _idha(live) + r")|" + _faala(live) + r")"
    )


def _verb_first(impf: str, live: bool = False) -> str:
    # "كان النبي يحب كذا" (also "وكان النبي ...", "ما كان النبي يفعل")
    return (
        _AR_NO_LETTER_BEFORE + r"(?:[وف])?" + _AR_KANA + r"\s+" + _AR_SUBJ + _AR_GAP
        + r"(?:" + impf + r"|" + _idha(live) + r")"
    )


def _an_nabi_kana(live: bool = False) -> str:
    # "ان النبي كان يحب الحلواء": the lead-in form of the same claim (any imperfect verb after كان)
    return (
        _AR_PROCLITIC + r"ان\s+(?:النبي|رسول\s+الله)" + _AR_GAP + _AR_KANA + _AR_GAP
        + r"(?!(?:يتيم|يقين|يهودي|يمني)ا?(?!" + _AR_LETTER + r"))ي" + _AR_LETTER + r"{2,}"
        + (_word_end(True) if live else "")
    )


def _an_nabi_faala(live: bool = False) -> str:
    return _AR_PROCLITIC + r"ان\s+(?:النبي|رسول\s+الله)" + _AR_GAP + r"فعل" + _word_end(live)


# Prophets' names that start with ي ("كان النبي يوسف عليه السلام يحب اباه" retells a story, it
# does not say what "the Prophet" did) are excluded as WHOLE words so they are not read as an
# imperfect verb. "يحيى" normalises to "يحيي", the same letters as the verb "يحيي" (he revives:
# "كان النبي يحيي الليل", a real claim), so that one is excluded only when "عليه السلام" or
# "بن" / "ابن" + "زكريا" follows it, which marks the name.
_AR_IMPF = _impf(_AR_Y_WHOLE_NAMES + r"|" + _AR_Y_YAHYA_NAME)
_AR_IMPF_LIVE = _impf(_AR_Y_WHOLE_NAMES + r"|" + _AR_Y_YAHYA_NAME + r"|" + _AR_Y_YAHYA_UNDECIDED, live=True)
_AR_SUBJ_FIRST = _subj_first(_AR_IMPF)
_AR_VERB_FIRST = _verb_first(_AR_IMPF)
_AR_AN_NABI_KANA = _an_nabi_kana()
_AR_AN_NABI_FAALA = _an_nabi_faala()


_AR_HADITH = [
    r"قال\s+(?:رسول\s+الله|النبي|الرسول|نبينا)",
    # the separators (comma, brackets, dashes) may sit between these words too: "قال -صلى الله عليه وسلم-: كذا"
    r"قال[" + _SEP + r"]+صلي[" + _SEP + r"]+الله[" + _SEP + r"]+عليه[" + _SEP + r"]+وسلم",
    r"قال[" + _SEP + r"]+عليه[" + _SEP + r"]+(?:الصلاه|السلام)",
    r"يقول\s+(?:النبي|الرسول|نبينا|رسول\s+الله)",
    r"(?:رسول\s+الله|النبي|الرسول|نبينا|نبي\s+الله)" + _AR_GAP + _AR_SAY,
    r"عن\s+(?:النبي|رسول\s+الله)",
    # "ان النبي" ("that the Prophet ...") is a narration lead-in only when an instruction or a
    # saying follows. "ان النبي كان رحيما" describes a served verse and is not an attribution.
    # The same blessing/adverb gap as above is tolerated before the verb, and the imperfect
    # forms count too ("ان النبي <blessing> نهي", "ان النبي كان ينهي"): the lead's rule is that
    # "the Prophet taught/forbade ..." is a hadith attribution. The leading "ان" also takes
    # the optional proclitic letter (see _AR_PROCLITIC) so "لأن/بأن/وأن/فإن النبي ..." match
    # from their own first letter, not one letter in.
    _AR_PROCLITIC + r"ان\s+(?:النبي|رسول\s+الله)" + _AR_GAP
    + r"(?:نهي|امر|اوصي|وصي|حث|حذر|علم|بين|اخبر|قال|يقول|ينهي|يامر|يوصي|يحث|يحذر|يعلم|يبين|يخبر)",
    # "ان النبي كان يحب الحلواء" / "ان النبي فعل كذا" claim what the Prophet did, which is a
    # hadith attribution whatever the verb. So "كان" + ANY imperfect verb counts (the gap
    # tolerates blessings and adverbs on both sides of كان), and so does a bare "فعل" verb.
    # "كان" + an adjective ("رحيما", "لطيفا") stays allowed: it describes a served verse. An
    # imperfect verb is ي + two or more letters; the few ي-initial nouns/adjectives a child
    # topic could use ("يتيما" orphan, "يقينا", "يهوديا", "يمنيا") are excluded on purpose, but
    # only as a WHOLE word (bare, or with the "ا" accusative ending), never as a prefix: the
    # exclusion is followed by a "not a letter" check, so a real imperfect verb that happens to
    # share the same four letters ("يتيمم" tayammum, "يتيمن", "يمنيهم"/"يمنيه" he-gives-false-
    # hope-to-them/him) is still caught, while "يتيما"/"يقينا"/"يهوديا"/"يمنيا" stay allowed. An
    # ambiguous word like "يسير" (walks / easy) is NOT excluded: a false cut only gives the
    # decline line, a missed hadith claim reaches the child. "فعل" must be a whole word, so
    # "فعلا" (indeed) and "فعله" (his act, a noun) pass. These allows hold for finished words,
    # so while a reply streams the same rules are decided on a COMPLETE word only (the live
    # variants: a trailing partial word, "يتي" or "فعل" before "ا", is undecided and held, not
    # cut; see _AR_WORD_DONE_LIVE). The exclusion list itself is NOT shortened to a
    # prefix, because "يمنع", "يهوى" and "يقي" are real imperfect verbs that share those
    # prefixes. The leading "ان" also takes the optional proclitic letter, same as above.
    _AR_AN_NABI_KANA,
    _AR_AN_NABI_FAALA,
    # Verb-first "كان النبي يحب كذا" and subject-first "النبي كان يحب كذا" describe what the
    # Prophet did, the same claim as the "ان النبي ..." forms above (lead: catch both orders;
    # a served hadith licenses both). Same shape of rule: "كان" + an imperfect verb, or a bare
    # "فعل"; "كان" + an adjective or noun ("رحيما", "يتيما") stays allowed. The subjects are the
    # ones the "قال" rule already takes (رسول الله / النبي / الرسول / نبينا / نبي الله). "نبي الله
    # موسى" does not match: a name is not a gap word, so only the Prophet's own title directly
    # followed by the verb counts. Beyond the plain forms, "كان النبي لا/لم/ما/قد يفعل" and
    # "كان النبي اذا ..." are the same claim and are caught too. "فعل" is subject-first only
    # ("النبي فعل كذا"): the verb-first "فعل النبي" is also the noun "the Prophet's act" ("ان فعل
    # النبي كان رحمة", allowed above), so it is not a claim on its own.
    _AR_SUBJ_FIRST,
    _AR_VERB_FIRST,
    r"رواه\s+(?:البخاري|مسلم)",
    r"في\s+(?:الحديث|حديث)",
    r"حديث\s+(?:الذي\s+|اللي\s+|الي\s+)?(?:علي|في)\s+(?:الشاشه|شاشتك|البطاقه|بطاقتك)",
    r"ورد\s+في\s+(?:الحديث|السنه)",
    r"حديث\s+(?:شريف|نبوي)",
]
_AR_QURAN = [
    # the separators (spaces, commas, brackets, dashes) may sit between «قال» and the divine name or epithet,
    # and inside a two-word epithet: «قال -تعالى-:», «قال (تعالى):», «وقال —سبحانه—:», «قال -عز وجل-:»
    r"قال[" + _SEP + r"]+(?:الله|ربنا|تعالي|سبحانه|تبارك|عز[" + _SEP + r"]+وجل|جل[" + _SEP + r"]+(?:وعلا|جلاله))",
    r"يقول\s+(?:الله|ربنا)",
    # "رسول الله قال" / "نبي الله قال" are hadith attributions, not "قال الله"
    r"(?<!رسول\s)(?<!نبي\s)(?<!عبد\s)الله(?:[" + _SEP + r"]+(?:سبحانه|عز|جل|تعالي|وتعالي|وعلا|وجل)){0,3}[" + _SEP + r"]+(?:يقول|قال|يامر|امر|وعد|يخبرنا|يعلمنا)",
    r"(?:في\s+)?القران(?:\s+الكريم)?\s+(?:يقول|يعلمنا|يخبرنا|ان)",
    r"ورد\s+في\s+القران",
]
_PATTERNS = (
    [(re.compile(p), "hadith") for p in _EN_HADITH + _AR_HADITH]
    + [(re.compile(p), "quran") for p in _EN_QURAN + _AR_QURAN]
)
# The same list for text that is still streaming: only the rules that end on a ي-verb, "فعل" or
# "اذا" differ. They are decided on a complete word (see _AR_WORD_DONE_LIVE) and, for "يحيى", on
# what follows it (see _AR_Y_YAHYA_UNDECIDED). A live match is always also a final match, and for
# a finished text the live and final answers agree except for those undecided tails.
_LIVE_SWAP = {
    _AR_SUBJ_FIRST: _subj_first(_AR_IMPF_LIVE, live=True),
    _AR_VERB_FIRST: _verb_first(_AR_IMPF_LIVE, live=True),
    _AR_AN_NABI_KANA: _an_nabi_kana(live=True),
    _AR_AN_NABI_FAALA: _an_nabi_faala(live=True),
}
_PATTERNS_LIVE = (
    [(re.compile(_LIVE_SWAP.get(p, p)), "hadith") for p in _EN_HADITH + _AR_HADITH]
    + [(re.compile(p), "quran") for p in _EN_QURAN + _AR_QURAN]
)

# Words that may start a trigger. A reply tail is held back (for a moment) only
# while it could still turn into one: strong words always, weak lead-ins only
# when the tail so far is a prefix of a known lead phrase.
_STRONG_START = frozenset({
    "prophet", "messenger", "allah", "quran", "hadith", "narrated",
    "قال", "وقال", "فقال", "يقول", "ويقول", "فيقول", "رواه", "النبي", "الرسول", "رسول", "نبينا", "الله", "القران",
    "ورد", "حديث", "نبي",
    # the subject with a glued proclitic ("والنبي كان يحب"): the word itself is not "النبي", so
    # without these it would be spoken at once and the tail would lose its subject
    "والنبي", "فالنبي", "بالنبي", "والرسول", "فالرسول", "بالرسول",
    "ورسول", "فرسول", "برسول", "ونبينا", "فنبينا",
    # "ونبي الله كان يحب": the glued و/ف/ب on "نبي" (the subject rules take the same prefix)
    "ونبي", "فنبي", "بنبي",
    # "بنبينا كان يحب": the glued ب on "نبينا" (the subject rules take the same prefix)
    "بنبينا",
})
_LEADS = [
    s.split() for s in (
        "the prophet", "our prophet", "the holy prophet", "the messenger", "the beloved prophet",
        "in the quran", "in the hadith", "in a hadith", "a hadith", "the hadith",
        "this hadith", "that hadith", "one hadith", "there is a hadith", "there is a famous hadith",
        "it is narrated", "according to the hadith", "according to a hadith",
        "according to the quran", "according to the sunnah", "the quran",
        "عن النبي", "ان النبي", "عن رسول", "ان رسول", "في الحديث", "في حديث", "في القران",
        "القران الكريم", "ورد في",
        # proclitic forms of "ان" ("لأن"/"بأن"/"وأن"/"فإن" normalise to "لان"/"بان"/"وان"/
        # "فان"): the word itself is neither a strong word nor plain "ان", so without these
        # it would be spoken immediately on the streaming path, ahead of the claim it leads.
        "لان النبي", "لان رسول", "بان النبي", "بان رسول",
        "وان النبي", "وان رسول", "فان النبي", "فان رسول",
        # verb-first "كان النبي يحب كذا": "كان" is an everyday word, so it is held for one word
        # only, until the next word shows whether it is the subject
        # (the step-back in _safe_upto keeps "كان" with the subject through a long blessing)
        *(f"{lead} {subj}"
          for lead in ("كان", "وكان", "فكان")
          for subj in ("النبي", "رسول", "الرسول", "نبينا", "نبي")),
        # the subject-first rule takes "ان" (and the proclitic forms) before ALL its subjects, so
        # the lead-in is held for the other subjects too, or "ان" / "لان" would be spoken first
        *(f"{lead} {subj}"
          for lead in ("ان", "لان", "بان", "وان", "فان")
          for subj in ("الرسول", "نبينا", "نبي")),
    )
]
_HOLD_WORDS = 7
# punctuation stripped off a streamed word before it is compared with the strong words and gap words;
# the same marks as _SEP (a word like "prophet！" must still read as "prophet")
_WORD_PUNCT = ".,;:!?()\"'\uff01\uff1a\uff1b\uff1f\uff0c\uff0e\u060c\u061b\u061f\u2026"
_HOLD_MAX_WORDS = 40  # upper bound when a blessing phrase stretches the hold (see _safe_upto)
# Words that _EN_GAP / _AR_GAP tolerate between the subject and the verb. A strong start
# word followed only by these (a long blessing) must keep being held, however long it is.
_GAP_WORDS = frozenset(
    "peace be upon him pbuh saw may allah bless blessings and grant once also often "
    "always really then again just of muhammad "
    # the verb phrases _EN_SAY accepts ("used to say", "would say"): a long blessing followed by them must
    # not push the subject out of the hold window before the verb arrives
    "used to would usually sometimes "
    "عليه عليها السلام الصلاه والسلام صلي الله وسلم مره ايضا دائما احيانا كان "
    "محمد الكريم واله وصحبه".split()
    # "يحيي" is the verb "greets" or the start of the name «يحيى ابن زكريا / عليه السلام»: its tail may
    # still be arriving, so the subject in front of it stays held while it is the last complete word
    + ["يحيي"]
    # a bare comma or a bracketed blessing sign strips down to nothing; the gap regexes allow it, so the hold does too
    + [""]
    # the negations that may stand between "كان" and the verb ("النبي صلى الله عليه وسلم كان لا يحب"):
    # without them the run of gap words breaks at "لا", a long blessing pushes the subject out of the
    # hold window, and a character-level stream spoke the whole claim before it was recognised
    + "لا لم ما قد".split()
)
_AR_MAP = str.maketrans({
    "أ": "ا", "إ": "ا", "آ": "ا",
    "ى": "ي", "ة": "ه", "ٱ": "ا",
    # the Arabic comma is the usual separator around a blessing ("النبي، صلى الله عليه وسلم، قال");
    # a 1:1 mapping, so the index map in _norm_with_map stays aligned
    chr(0x60C): ",",
})
_DROP = re.compile("[\u064b-\u065f\u0670\u0640\u06d6-\u06ed\ufdfa]")


def _norm_with_map(s: str) -> tuple[str, list[int]]:
    out: list[str] = []
    idx: list[int] = []
    for i, ch in enumerate(s):
        if _DROP.match(ch):
            continue
        out.append(ch.lower().translate(_AR_MAP))
        idx.append(i)
    return "".join(out), idx


def find_attribution(text: str, allowed=frozenset(), final: bool = True) -> int | None:
    """Index in ``text`` where an UNLICENSED attribution phrase starts, else None.

    ``allowed`` is the set of kinds ("hadith", "quran") the served items license.
    ``final=False`` is for a reply that is still streaming: a ي-verb, "فعل" or "اذا" that touches
    the end of the text may be a partial word ("يتي" before "ما"), and a "يحيي" at the very end
    may still become the name "يحيى عليه السلام"; neither is a claim yet. Every other caller wants
    the default.
    """
    norm, idx = _norm_with_map(text)
    best: int | None = None
    for p, kind in (_PATTERNS if final else _PATTERNS_LIVE):
        if kind in allowed:
            continue
        m = p.search(norm)
        if m and (best is None or m.start() < best):
            best = m.start()
    return idx[best] if best is not None and best < len(idx) else None


def has_attribution(text: str, allowed=frozenset()) -> bool:
    return find_attribution(text, allowed) is not None


def _lead_hold(tail: list[str]) -> bool:
    """True if the tail is a prefix of a lead phrase or starts with a whole one."""
    return any(
        (len(tail) <= len(lead) and lead[: len(tail)] == tail)
        or (len(tail) > len(lead) and tail[: len(lead)] == lead)
        for lead in _LEADS
    )


def _safe_upto(pending: str) -> int:
    """How much of ``pending`` can be emitted without cutting a possible trigger."""
    norm, idx = _norm_with_map(pending)
    # the three dashes separate words like a space does, so a blessing between dashes, glued or not,
    # reads as separate words (see the dash tests in test_turn_guard_fixes.py)
    words = [(m.start(), m.group().strip(_WORD_PUNCT)) for m in re.finditer(r"[^\s\-\u2013\u2014]+", norm)]
    n = len(pending)
    if not words:
        return n
    cut = len(norm)
    # a trailing unfinished word is never emitted (could be a prefix of a trigger)
    if not (norm[-1].isspace() or norm[-1] in _DASHES):
        cut = words[-1][0]
    complete = [w for w in words if w[0] < cut]
    # the hold normally covers the last few words, but a strong start word followed by
    # nothing except blessing/adverb words ("the Prophet, peace and blessings of Allah
    # be upon him, once ...") is held for as long as that run lasts
    first = max(len(complete) - _HOLD_WORDS, 0)
    j = len(complete)
    while j > 0 and complete[j - 1][1] in _GAP_WORDS and len(complete) - j < _HOLD_MAX_WORDS:
        j -= 1
    s = max(min(first, j - 1), 0)
    # the run stops at the strong word (رسول, النبي), but a weak lead-in just before it
    # ("ان") is part of the trigger: step back over any lead phrase that reaches into the window
    ws = [x[1] for x in complete]
    for lead in _LEADS:
        for k in range(1, len(lead)):
            seg = ws[s - k:s - k + len(lead)] if s - k >= 0 else []
            if len(seg) > k and seg == lead[:len(seg)]:
                s -= k
                break
    window = complete[s:]
    for i, (start, w) in enumerate(window):
        tail = [x[1] for x in window[i:]]
        if w in _STRONG_START or _lead_hold(tail):
            cut = min(cut, start)
            break
    if cut >= len(norm):
        return n
    return idx[cut] if cut < len(idx) else n


def decline_for(text: str, lang: str = "en") -> str:
    if _ARABIC.search(text or ""):
        return DECLINE_TEXT["ar"]
    return DECLINE_TEXT.get(lang, DECLINE_TEXT["en"])


def _licence(served) -> frozenset:
    """``served`` may return a bool (True = everything licensed) or a set of kinds."""
    v = served()
    if v is True:
        return KINDS
    if not v:
        return frozenset()
    return frozenset(v)


async def guard_attribution_stream(
    text: AsyncIterable[str],
    served: Callable[[], object],
    lang: str = "en",
    count: bool = True,
) -> AsyncIterable[str]:
    """Pass the reply through; cut it at an unlicensed attribution phrase.

    Holds back only the short tail that could still turn into a trigger, so
    ordinary replies are delayed by at most a few words. ``count=False`` is used
    for the second copy of the same reply (the transcript) so the counter and log
    record one event per reply, not one per output.
    """
    pending = ""
    seen = ""
    blocked = False

    def _note() -> None:
        if count:
            STATS["attribution_blocked"] += 1
            logger.warning("output check: unlicensed attribution replaced with decline")

    async for chunk in text:
        if blocked:
            continue  # drain the LLM stream silently
        allowed = _licence(served)
        if allowed >= KINDS:
            if pending:
                yield pending
                pending = ""
            yield chunk
            continue
        pending += chunk
        seen += chunk
        pos = find_attribution(pending, allowed)
        if pos is not None and find_attribution(pending, allowed, final=False) is None:
            # undecided: a "يحيي" at the end may still turn into the name "يحيى عليه السلام".
            # Nothing is emitted until the next chunk settles it; the end-of-stream check below
            # uses the final rules.
            continue
        if pos is not None:
            blocked = True
            _note()
            if pending[:pos].strip():
                yield pending[:pos]
            yield decline_for(seen, lang)
            pending = ""
            continue
        upto = _safe_upto(pending)
        if upto > 0:
            yield pending[:upto]
            pending = pending[upto:]
    if not blocked and pending:
        pos = find_attribution(pending, _licence(served))
        if pos is not None:
            _note()
            if pending[:pos].strip():
                yield pending[:pos]
            yield decline_for(seen, lang)
        else:
            yield pending
