"""Avatar signals: the agent's attributes that tell the child's app what Sadiq is doing.

The 3D avatar picks its animation (how it listens, how it talks, the search hologram) from
a handful of short strings that the agent publishes on its own LiveKit participant. The
contract is section 8 of SPEC-EXPERIENCE.md; this module is the backend half of it.

Attributes (set on the agent participant, every key starts with ``al.`` and never with
``lk.``; an empty value would delete a key in LiveKit, so no value is ever empty):

  al.sig_v          "1"                                  once, right after the session starts
  al.activity       idle | searching | found | none      a search's start and end
  al.search_kind    library | folders | web              with every "searching"
  al.talk_style     explain | story | praise | question | gentle     once per reply
  al.reply          "<int>", +1 per reply                with al.talk_style
  al.listen_style   neutral | curious | sad | excited    the child's mood, per turn
  al.turn           "<int>", +1 per child turn           with the turn's first al.listen_style

How it works:

- The classifiers (``classify_listen``, ``classify_talk``) are keyword rules in pure Python:
  no LLM call, no network, no dependency, well under 1 ms.
- ``AvatarSignals.tap_reply`` wraps the text going into the TTS node. It passes every
  chunk through at once (no added await, no added latency), reads the opening of the reply
  on the side, and publishes ``al.talk_style`` + ``al.reply`` as soon as the opening is
  known (a sentence end after 12 characters, 90 characters, 350 ms after the first chunk,
  or the end of the stream). The text that arrives there has already been cleaned for
  speech, so it never carries scripture (verses are replaced by a neutral phrase).
- One pump task owns all the publishing. Items are queued in order; keys queued together
  merge into one ``set_attributes`` call, but two ``al.activity`` changes never merge (so
  "searching" always goes out before "found"), and there is at least 120 ms between calls.
  The pump runs only while there is something to send, so there is no task to shut down.
- Nothing here can break the voice. Every public method swallows its own errors, a failing
  ``set_attributes`` is logged once at warning level (then at debug), and with no room
  bound everything is a no-op.

A reply is one ``tts_node`` call, which is one speech generation of the LLM. With default
livekit nodes that is one per spoken answer (a tool round that speaks gives a second one).
Text-only sessions never call ``tts_node``, so ``al.talk_style`` goes stale there and the
web falls back to ``explain``; the search and listen signals still work.

Adding a new search to a tool (one line each, see docs/hackathon/handoffs/avatar-signals.md)::

    async with self.signals.search("library") as s:
        rows = await fetch()
        s.found = bool(rows)

    self.signals.quick_find("library", found=bool(items))  # an instant lookup, at most 1 / 45 s
"""
from __future__ import annotations

import asyncio
import contextlib
import logging
import re
import time
from collections import deque
from collections.abc import AsyncIterable, AsyncIterator, Callable

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# The contract (SPEC-EXPERIENCE.md section 8.1)
# ---------------------------------------------------------------------------

SIG_VERSION = "1"

KEY_SIG_V = "al.sig_v"
KEY_ACTIVITY = "al.activity"
KEY_SEARCH_KIND = "al.search_kind"
KEY_TALK_STYLE = "al.talk_style"
KEY_REPLY = "al.reply"
KEY_LISTEN_STYLE = "al.listen_style"
KEY_TURN = "al.turn"

ACTIVITIES = ("idle", "searching", "found", "none")
SEARCH_KINDS = ("library", "folders", "web")
TALK_STYLES = ("explain", "story", "praise", "question", "gentle")
LISTEN_STYLES = ("neutral", "curious", "sad", "excited")

# update(**kv) takes the short name; the attribute key is "al." + name.
_SHORT_TO_KEY = {
    "sig_v": KEY_SIG_V,
    "activity": KEY_ACTIVITY,
    "search_kind": KEY_SEARCH_KIND,
    "talk_style": KEY_TALK_STYLE,
    "reply": KEY_REPLY,
    "listen_style": KEY_LISTEN_STYLE,
    "turn": KEY_TURN,
}
_ENUMS = {
    KEY_ACTIVITY: ACTIVITIES,
    KEY_SEARCH_KIND: SEARCH_KINDS,
    KEY_TALK_STYLE: TALK_STYLES,
    KEY_LISTEN_STYLE: LISTEN_STYLES,
}
# Counters change every time, so they are always sent (the web reads the change itself).
_COUNTER_KEYS = frozenset({KEY_REPLY, KEY_TURN})

PUBLISH_MIN_INTERVAL_S = 0.12  # never more than one set_attributes call per 120 ms
PUBLISH_TIMEOUT_S = 5.0
QUICK_FIND_COOLDOWN_S = 45.0
OPENING_MIN_CHARS = 12  # a sentence end only counts after this many characters
OPENING_MAX_CHARS = 90
OPENING_TIMEOUT_S = 0.35  # after the first chunk
OPENING_TERMINATORS = frozenset(".!?؟،;\n")
MIN_LISTEN_TOKENS = 2  # a child line shorter than this is never classified
_MAX_QUEUE = 256

# ---------------------------------------------------------------------------
# Text normalisation (section 8.3), shared with the web's transcript cues
# ---------------------------------------------------------------------------

_STRIP_MARKS = re.compile("[ؗ-ًؚ-ْٰـ]")  # diacritics + tatweel
_FOLD = str.maketrans({
    "أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا",
    "ى": "ي", "ة": "ه", "ؤ": "و", "ئ": "ي",
    "’": "'", "‘": "'",
})
_TOKEN = re.compile(r"[\w']+")
_ARABIC = re.compile("[؀-ۿ]")
_QUESTION_END = re.compile(r"[?؟][\s\"'»”’)\]]*$")


def normalize(text: str | None) -> str:
    """Strip Arabic diacritics and tatweel, fold letter variants, lowercase, collapse spaces."""
    if not text:
        return ""
    folded = _STRIP_MARKS.sub("", str(text)).translate(_FOLD).lower()
    return " ".join(folded.split())


def _tokens(normalized: str) -> list[str]:
    """Runs of word characters and apostrophes (apostrophes at the edges are dropped)."""
    out = []
    for raw in _TOKEN.findall(normalized):
        token = raw.strip("'")
        if token:
            out.append(token)
    return out


def _ends_with_question_mark(text: str | None) -> bool:
    return bool(text) and _QUESTION_END.search(str(text).rstrip()) is not None


# An Arabic token also matches after one clitic prefix, if 3 or more letters remain.
_CLITICS = tuple(sorted((normalize(p) for p in ("وال", "بال", "فال", "كال", "لل", "ال", "و", "ف", "ب", "ل")),
                        key=len, reverse=True))
_MIN_STEM = 3

# Words that flip a SAD or EXCITED hit when they sit within 2 tokens before it.
_NEGATORS = frozenset(normalize(w) for w in (
    "مو مب مش ما لا لست ليس مهو "
    "not no never dont don't isn't wasn't didn't aren't isnt wasnt arent"
).split())
_NEGATION_WINDOW = 2
# "لا" and "no" are also the answer "no": "لا، أنا زعلان" and "No, I'm sad" are sad. These two
# negate only the word right after them ("لا أخاف", "no tears").
_ADJACENT_NEGATORS = frozenset(normalize(w) for w in ("لا", "no"))
_CLAUSE_BREAK = re.compile(r"[,،.!?؟;:]+")  # a negation never reaches across punctuation


class _Lexicon:
    """A set of keywords: single words (with clitic handling) and multi-word phrases."""

    def __init__(self, words: str | tuple[str, ...]) -> None:
        entries = words.split("|") if isinstance(words, str) else words
        self.singles: set[str] = set()
        self.phrases: dict[str, list[tuple[str, ...]]] = {}
        for entry in entries:
            toks = _tokens(normalize(entry))
            if not toks:
                continue
            if len(toks) == 1:
                self.singles.add(toks[0])
            else:
                self.phrases.setdefault(toks[0], []).append(tuple(toks))

    def _word_hit(self, token: str) -> bool:
        if token in self.singles:
            return True
        if _ARABIC.search(token):
            for prefix in _CLITICS:
                if token.startswith(prefix) and len(token) - len(prefix) >= _MIN_STEM \
                        and token[len(prefix):] in self.singles:
                    return True
        return False

    def _phrase_hit(self, tokens: list[str], i: int) -> bool:
        for phrase in self.phrases.get(tokens[i], ()):
            if tuple(tokens[i:i + len(phrase)]) == phrase:
                return True
        return False

    def hit_positions(self, tokens: list[str]) -> list[int]:
        """Index of the first token of every hit."""
        return [i for i, tok in enumerate(tokens) if self._word_hit(tok) or self._phrase_hit(tokens, i)]

    def count(self, tokens: list[str], *, negatable: bool = False) -> int:
        positions = self.hit_positions(tokens)
        if negatable:
            positions = [i for i in positions if not _negated(tokens, i)]
        return len(positions)

    def starts(self, tokens: list[str]) -> bool:
        return bool(tokens) and (self._word_hit(tokens[0]) or self._phrase_hit(tokens, 0))

    def any(self, tokens: list[str]) -> bool:
        return bool(self.hit_positions(tokens))


def _negated(tokens: list[str], index: int) -> bool:
    for j in range(max(0, index - _NEGATION_WINDOW), index):
        tok = tokens[j]
        if tok in _NEGATORS and (j == index - 1 or tok not in _ADJACENT_NEGATORS):
            return True
    return False


# ---------------------------------------------------------------------------
# The keyword lists (natural spelling here; normalised when the lexicon is built).
# Placeholder-free and scripture-free: these are everyday words and praise phrases.
# ---------------------------------------------------------------------------

_SAD = _Lexicon(
    # Arabic
    "حزين|حزينة|زعلان|زعلانة|زعلت|متضايق|متضايقة|ضايقني|خايف|خايفة|خفت|أخاف|قلقان|قلقانة|قلق|أبكي|بكيت|"
    "يبكي|دموع|وحيد|وحيدة|لحالي|تعبان|مقهور|ضربني|ضربوني|يتنمر|يتنمرون|تنمر|يضحكون علي|يكرهني|يكرهوني|"
    "مات|ماتت|توفي|توفيت|فقدت|ضاع|ضاعت|خسرت|غلطت|كذبت|ندمان|مكسور خاطري|محد يحبني|ما أحد يحبني|"
    "ما عندي أصحاب|"
    # stems, so the clitic forms (والحزن, بزعل) match
    "حزن|زعل|"
    # English
    "sad|upset|unhappy|cry|crying|cried|tears|scared|afraid|frightened|worried|nervous|anxious|lonely|"
    "alone|hurt|bullied|bully|teased|hate me|hates me|mean to me|died|passed away|lost|my fault|i lied|"
    "ashamed|embarrassed|angry|nobody likes me|no friends"
)
_EXCITED = _Lexicon(
    "فرحان|فرحانة|مبسوط|مبسوطة|متحمس|متحمسة|وناسة|يا سلام|رهيب|فزت|فزنا|نجحت|جبت الأول|الدرجة الكاملة|"
    "فل مارك|عيدية|هدية|عيد ميلادي|أخيرا|تخيل|تدري وش صار|خمن|"
    "guess what|i won|we won|full marks|first place|i passed|yay|awesome|amazing|so cool|excited|"
    "can't wait|birthday|present|gift|eid|finally|best day"
)
_CURIOUS_WORDS = (
    "ليش|ليه|لماذا|كيف|شلون|وش|ايش|شو|ماذا|متى|وين|أين|مين|هل|كم|ما هو|ما هي|من هو|من هي|قل لي|علمني|"
    "أبي أعرف|أريد أن أعرف|سؤال|"
    "why|how|what|when|where|who|which|can you|could you|do you|does|is it|are you|tell me|explain|"
    "question|i wonder"
)
_CURIOUS = _Lexicon(_CURIOUS_WORDS)
# A reply that starts with a question word is asking back, but "سؤال" / "question" are nouns:
# a reply that opens "سؤال حلو" is saying "good question" and then explaining.
_ASK_START = _Lexicon(tuple(w for w in _CURIOUS_WORDS.split("|") if w not in ("سؤال", "question")))
_EXCLAMATION_END = re.compile(r"![\s\"'»”’)\]]*$")

_PRAISE = _Lexicon(
    "ما شاء الله|ماشاء الله|تبارك الله|أحسنت|برافو|يا بطل|يا بطلة|رائع|رائعة|ممتاز|ممتازة|شاطر|شاطرة|"
    "فخور|فخورة|كفو|جميل جدا|"
    "well done|great job|good job|amazing|awesome|proud of you|brilliant|fantastic|excellent|mashallah|"
    "masha allah|way to go|bravo"
)
_GENTLE = _Lexicon(
    "لا بأس|لا تحزن|لا تخاف|لا تقلق|أفهمك|أفهم شعورك|أعرف أنه صعب|طبيعي تحس|قلبي معك|أنا معك|أنا هنا|"
    "خذ نفس|الله يصبرك|"
    "it's okay|it's ok|don't worry|i understand|that sounds hard|that must be hard|i'm sorry|i'm here|"
    "you're not alone|take a deep breath|it's normal to feel"
)
_STORY = _Lexicon(
    "كان يا ما كان|في يوم من الأيام|يحكى أن|ذات يوم|مرة من المرات|خلني أحكي لك|اسمع هالقصة|قصة|حكاية|"
    "once upon a time|one day|long ago|let me tell you a story|here's a story|there was once|the story of"
)

_LISTEN_PRIORITY = {"neutral": 0, "curious": 1, "excited": 2, "sad": 3}


def classify_listen(text: str | None) -> str:
    """The child's mood from one line of their words: sad > excited > curious > neutral.

    A SAD or EXCITED hit is ignored when a negator sits within 2 tokens before it in the
    same clause ("مو زعلان", "I'm not sad"); "لا" and "no" only when right before it, because
    they are also the answer "no" ("لا أنا زعلان", "No, I'm sad" are sad). A line that ends
    with ? or ؟ counts as curious even without a question word. The caller decides whether
    a line is long enough to publish (``MIN_LISTEN_TOKENS``); this function classifies
    whatever it is given.
    """
    clauses = [_tokens(c) for c in _CLAUSE_BREAK.split(normalize(text))]
    if any(_SAD.count(c, negatable=True) for c in clauses):
        return "sad"
    if any(_EXCITED.count(c, negatable=True) for c in clauses):
        return "excited"
    tokens = [tok for c in clauses for tok in c]
    if _CURIOUS.count(tokens) or _ends_with_question_mark(text):
        return "curious"
    return "neutral"


def classify_talk(opening: str | None, *, listen_style: str = "neutral",
                  hint_praise: bool = False, hint_safety: bool = False) -> str:
    """How Sadiq's reply should look, from the opening of the reply and the turn's hints.

    Priority: safety hint (gentle), praise (hint or marker), gentle (marker or a sad child),
    story, question, explain. A question ends with ? or ؟, or starts with a question word
    without ending in "!" ("What a brave thing to do!" is an exclamation, not asking back).
    """
    if hint_safety:
        return "gentle"
    tokens = _tokens(normalize(opening))
    if hint_praise or _PRAISE.any(tokens):
        return "praise"
    if listen_style == "sad" or _GENTLE.any(tokens):
        return "gentle"
    if _STORY.any(tokens):
        return "story"
    if _ends_with_question_mark(opening):
        return "question"
    if _ASK_START.starts(tokens) and not _EXCLAMATION_END.search(str(opening).rstrip()):
        return "question"
    return "explain"


# ---------------------------------------------------------------------------
# The publisher
# ---------------------------------------------------------------------------


class SearchBox:
    """Yielded by ``AvatarSignals.search``: set ``found`` to True when the search had a result."""

    __slots__ = ("found",)

    def __init__(self) -> None:
        self.found = False


class AvatarSignals:
    """Publishes the ``al.*`` attributes of section 8. See the module docstring."""

    def __init__(
        self,
        *,
        clock: Callable[[], float] = time.monotonic,
        min_interval: float = PUBLISH_MIN_INTERVAL_S,
        quick_cooldown: float = QUICK_FIND_COOLDOWN_S,
        opening_timeout: float = OPENING_TIMEOUT_S,
    ) -> None:
        self._clock = clock  # cooldowns only, injectable for tests
        self._min_interval = min_interval
        self._quick_cooldown = quick_cooldown
        self._opening_timeout = opening_timeout

        self._room = None
        self._queue: deque[dict[str, str]] = deque()
        self._intent: dict[str, str] = {}  # the last value queued or sent per key
        self._pump: asyncio.Task | None = None
        self._pumping = False
        self._last_send_at: float | None = None  # loop time of the last set_attributes call
        self._warned = False

        self._reply = 0
        self._turn = 0
        self._turn_class: str | None = None  # the class published for the current child turn
        self._turn_closed = False  # the agent has started to speak: the next child line is a new turn
        self._hint_praise = False
        self._hint_safety = False

        self._search_depth = 0
        self._search_found = False
        self._last_quick: float | None = None

    # -- wiring -----------------------------------------------------------

    def bind(self, room) -> None:
        """Remember the room whose local participant (the agent) carries the attributes."""
        self._room = room

    def start(self) -> None:
        """Publish the initial batch (``al.sig_v`` last in the contract, first on the wire)."""
        self.update(
            sig_v=SIG_VERSION, activity="idle", search_kind="web", talk_style="explain",
            reply=str(self._reply), listen_style="neutral", turn=str(self._turn),
        )

    def attach(self, session) -> None:
        """Subscribe to the session events that carry the child's turn and the agent's state."""
        try:
            session.on("user_input_transcribed", self._on_user_input_transcribed)
            session.on("agent_state_changed", self._on_agent_state_changed)
            session.on("user_state_changed", self._on_user_state_changed)
        except Exception:
            self._log_failure("attach: could not subscribe to the session events")

    # -- publishing -------------------------------------------------------

    def update(self, **kv) -> None:
        """Queue attribute changes (short names: activity, search_kind, talk_style, ...). Never raises.

        Values that equal the last queued or sent value are dropped, except the counters
        (``reply``, ``turn``). Empty, unknown or out-of-set values are dropped too.
        """
        try:
            item: dict[str, str] = {}
            for short, value in kv.items():
                key = _SHORT_TO_KEY.get(short)
                if key is None or value is None:
                    continue
                text = str(value).strip()
                if not text:
                    continue  # an empty value would delete the key
                allowed = _ENUMS.get(key)
                if allowed is not None and text not in allowed:
                    if key != KEY_SEARCH_KIND:
                        logger.debug("avatar signals: ignoring %s=%r", key, text)
                        continue
                    text = "web"  # an unknown search kind falls back to the generic look
                if key in _COUNTER_KEYS:
                    if not text.isdigit():
                        continue
                elif self._intent.get(key) == text:
                    continue
                item[key] = text
            if not item:
                return
            self._intent.update(item)
            self._queue.append(item)
            while len(self._queue) > _MAX_QUEUE:
                self._queue.popleft()
            self._ensure_pump()
        except Exception:
            self._log_failure("update failed")

    async def flush(self) -> None:
        """Wait until everything queued has been sent (tests and clean shutdowns)."""
        while self._queue or self._pumping:
            task = self._pump
            if task is None or task.done():
                self._ensure_pump()
                task = self._pump
            if task is None:
                return
            await asyncio.wait({task})

    def _ensure_pump(self) -> None:
        if self._pumping:
            return
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return  # nothing is sending without a loop; the next update (or flush) starts the pump
        self._pumping = True
        self._pump = loop.create_task(self._run())

    def _pop_batch(self) -> dict[str, str]:
        """The next call: queued items merged in order, but never two ``al.activity`` changes."""
        batch: dict[str, str] = {}
        while self._queue:
            item = self._queue[0]
            if KEY_ACTIVITY in item and KEY_ACTIVITY in batch:
                break
            batch.update(self._queue.popleft())
        return batch

    async def _run(self) -> None:
        try:
            loop = asyncio.get_running_loop()
            while self._queue:
                if self._last_send_at is not None:
                    wait = self._last_send_at + self._min_interval - loop.time()
                    if wait > 0:
                        await asyncio.sleep(wait)  # items queued meanwhile join the next call
                batch = self._pop_batch()
                if not batch:
                    continue
                self._last_send_at = loop.time()
                await self._send(batch)
        finally:
            self._pumping = False

    async def _send(self, batch: dict[str, str]) -> None:
        room = self._room
        if room is None:
            for key in batch:
                self._intent.pop(key, None)
            return
        try:
            await asyncio.wait_for(room.local_participant.set_attributes(dict(batch)), PUBLISH_TIMEOUT_S)
        except asyncio.CancelledError:
            raise
        except Exception:
            for key in batch:
                self._intent.pop(key, None)  # unknown on the server now: send it again next time
            self._log_failure("set_attributes failed for %s", sorted(batch))

    def _log_failure(self, message: str, *args) -> None:
        if not self._warned:
            self._warned = True
            logger.warning("Avatar signals: " + message, *args, exc_info=True)
        else:
            logger.debug("Avatar signals: " + message, *args, exc_info=True)

    # -- searches ---------------------------------------------------------

    @contextlib.asynccontextmanager
    async def search(self, kind: str) -> AsyncIterator[SearchBox]:
        """Signal a search around a tool call: ``searching`` now, ``found`` or ``none`` at the end.

        ``found`` is read from the yielded box; an exception in the block means ``none``
        (and still propagates). Searches that overlap share one signal: ``searching`` goes
        out with the first, and the end goes out when the last one finishes (``found`` if
        any of them found something).
        """
        box = SearchBox()
        self._search_begin(kind)
        failed = False
        try:
            yield box
        except BaseException:
            failed = True
            raise
        finally:
            self._search_end(bool(box.found) and not failed)

    def _search_begin(self, kind: str) -> None:
        try:
            self._search_depth += 1
            if self._search_depth == 1:
                self._search_found = False
                self.update(activity="searching", search_kind=kind)
        except Exception:
            self._log_failure("search start failed")

    def _search_end(self, found: bool) -> None:
        try:
            self._search_depth = max(0, self._search_depth - 1)
            self._search_found = self._search_found or found
            if self._search_depth == 0:
                result = "found" if self._search_found else "none"
                self._search_found = False
                self.update(activity=result)
        except Exception:
            self._log_failure("search end failed")

    def quick_find(self, kind: str, found: bool) -> bool:
        """An instant lookup (under 10 ms). Signals only when something was found, at most once
        per 45 s, and never while a real search is open. Returns True when it signalled.

        It goes out as ``searching`` then ``found`` (two ordered transitions), so the web sees
        a real change even when the last activity was already ``found``.
        """
        try:
            if not found or self._search_depth:
                return False
            now = self._clock()
            if self._last_quick is not None and now - self._last_quick < self._quick_cooldown:
                return False
            self._last_quick = now
            self.update(activity="searching", search_kind=kind)
            self.update(activity="found")
            return True
        except Exception:
            self._log_failure("quick_find failed")
            return False

    # -- hints from the tools ---------------------------------------------

    def hint_praise(self) -> None:
        """A point was just recorded: the next reply is praise. Resets when used."""
        self._hint_praise = True

    def hint_safety(self) -> None:
        """A safety concern was flagged: the next reply is gentle. Resets when used."""
        self._hint_safety = True

    # -- the reply --------------------------------------------------------

    async def tap_reply(self, text: AsyncIterable[str]) -> AsyncIterator[str]:
        """Pass the reply's text through untouched while reading its opening.

        Adds no await and no delay: each chunk is handed on exactly when the source gives it.
        The opening is the first of: a sentence end after 12 characters, 90 characters,
        350 ms after the first chunk, the end of the stream. Then ``al.talk_style`` and
        ``al.reply`` are published together, once. An empty reply publishes nothing and does
        not count.
        """
        buf: list[str] = []
        state = {"done": False}
        timer: asyncio.TimerHandle | None = None

        def decide(opening: str) -> None:
            state["done"] = True
            try:
                if not opening.strip():
                    state["done"] = False  # nothing to read yet (or ever)
                    return
                style = classify_talk(
                    opening, listen_style=self._turn_class or "neutral",
                    hint_praise=self._hint_praise, hint_safety=self._hint_safety,
                )
                self._hint_praise = self._hint_safety = False
                self._reply += 1
                self.update(talk_style=style, reply=str(self._reply))
            except Exception:
                self._log_failure("reply classification failed")

        def on_timeout() -> None:
            if not state["done"]:
                decide("".join(buf).lstrip())

        completed = False
        try:
            async for chunk in text:
                if not state["done"] and isinstance(chunk, str):
                    try:
                        buf.append(chunk)
                        if timer is None:
                            timer = asyncio.get_running_loop().call_later(self._opening_timeout, on_timeout)
                        cut = _opening_cut("".join(buf).lstrip())
                        if cut is not None:
                            decide("".join(buf).lstrip()[:cut])
                    except Exception:
                        state["done"] = True
                        self._log_failure("tap_reply bookkeeping failed")
                yield chunk
            completed = True
        finally:
            if timer is not None:
                timer.cancel()
            if completed and not state["done"]:
                decide("".join(buf).lstrip())

    # -- the child's turn -------------------------------------------------

    def on_child_text(self, text: str | None, *, new_turn: bool = False) -> str | None:
        """Classify a line of the child's words (an interim or final transcript, or typed chat).

        Publishes ``al.listen_style`` + ``al.turn`` on the turn's first classification (at
        least 2 tokens), then only on an upgrade (sad > excited > curious > neutral). Returns
        the class of this line, or None when it was too short. ``new_turn=True`` marks a
        typed message, which is always a whole turn of its own.
        """
        try:
            if new_turn:
                self._turn_closed = True
            if len(_tokens(normalize(text))) < MIN_LISTEN_TOKENS:
                return None
            self._begin_turn_if_closed()
            cls = classify_listen(text)
            if self._turn_class is None:
                self._turn += 1
                self._turn_class = cls
                self.update(listen_style=cls, turn=str(self._turn))
            elif _LISTEN_PRIORITY[cls] > _LISTEN_PRIORITY[self._turn_class]:
                self._turn_class = cls
                self.update(listen_style=cls)
            return cls
        except Exception:
            self._log_failure("on_child_text failed")
            return None

    def _begin_turn_if_closed(self) -> None:
        if self._turn_closed:
            self._turn_closed = False
            self._turn_class = None
            self._hint_praise = self._hint_safety = False

    def _on_user_input_transcribed(self, event) -> None:
        text = getattr(event, "transcript", None) or getattr(event, "text", None) or ""
        self.on_child_text(text)

    def _on_agent_state_changed(self, event) -> None:
        # Once Sadiq is speaking, the child's turn is over: their next words are a new turn.
        # (Not "thinking": a final transcript can land just after the agent starts thinking,
        # and it still belongs to the turn that just ended.)
        if getattr(event, "new_state", None) == "speaking":
            self._turn_closed = True

    def _on_user_state_changed(self, event) -> None:
        if getattr(event, "new_state", None) == "speaking":
            self._begin_turn_if_closed()


def _opening_cut(buf: str) -> int | None:
    """Where the opening of a reply ends in ``buf`` (already left-stripped), or None if not yet."""
    head = buf[:OPENING_MAX_CHARS]
    for i in range(OPENING_MIN_CHARS, len(head)):
        if head[i] in OPENING_TERMINATORS:
            return i + 1
    if len(buf) >= OPENING_MAX_CHARS:
        return OPENING_MAX_CHARS
    return None
