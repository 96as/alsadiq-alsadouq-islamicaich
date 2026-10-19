"""Wiring of the turn guard and the ``search_bank`` card markers into the agent (task 03, hk/12).

``TurnGuardMixin`` is mixed into ``AlSadiqAgent`` and owns everything that runs
around a child turn, so ``agent_class.py`` and ``entrypoint.py`` only need small
hooks. The guard (``turn_guard.check``) only speaks up for serious safety, personal rulings and
creed disputes; the model fetches Islamic content itself with ``search_bank`` and cites it with
``{{card:ID}}`` (a card is shown only for a cited item):

- ``on_user_turn_completed``  spoken turns (livekit-agents 1.5.1 calls it from the
  STT turn path only);
- ``reply_to_typed``          typed turns. ``AgentSession.generate_reply(user_input=)``
  never calls ``on_user_turn_completed`` in 1.5.1, so the typed handler calls this
  instead, which runs the SAME ``_prepare`` and passes the turn note through ``chat_ctx=``;
- ``guard_speech``            wraps the text stream in ``tts_node`` (card markers, attribution
  check, scripture filter, then LAST the off-script tidy).

Everything slow (DB writes, data events, the safety flag) is fire-and-forget.
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
import time
from datetime import date

from asgiref.sync import sync_to_async
from content_safety.models import NEUTRAL_ALERT_DESCRIPTION

from .bank_search import comfort_blocked
from .retrieval import EMPTY_INDEX, ValueIndex, card_payload, item_level, max_level, verse_refs
from .scripture_guard import filter_scripture_stream, guard_attribution_stream
from .text_match import has_arabic
from .tts_text import tidy_off_script_stream
from .turn_guard import REFER, SAFETY, GuardHit, check
from .turn_language import decide_reply_language, language_line, reply_language_follows_child

# TurnAudit modes written when a reply is committed after a search_bank call
ANSWER = "ANSWER"
DISAGREE_AND_REFER = "DISAGREE_AND_REFER"
DECLINE_NO_SOURCE = "DECLINE_NO_SOURCE"
MAX_CARDS_PER_TURN = 2
GUARD_ERROR = "GUARD_ERROR"
# Injected when the guard itself failed: fail closed, let the model do the safety reading.
GUARD_ERROR_NOTE = (
    "The safety check could not run on this message. Read it carefully: if anything in it is "
    "concerning, comfort the child first and call flag_safety_concern."
)

logger = logging.getLogger(__name__)

_FLAG_WAIT_SECONDS = 20.0
# The most typed characters that reach the model and the saved transcript. The guard still reads the
# WHOLE message (a disclosure late in a long text must not be missed); this only stops a modified
# client from sending a huge message to the LLM. The app's own field allows 500.
TYPED_TEXT_LLM_MAX_CHARS = 1000


def cap_typed_text(text: str | None) -> str:
    """The typed message as the model and the database see it (unchanged when short)."""
    text = text or ""
    return text if len(text) <= TYPED_TEXT_LLM_MAX_CHARS else text[:TYPED_TEXT_LLM_MAX_CHARS]


class TurnRef:
    """The child message that belongs to one turn.

    Created when the turn starts, bound to the FIRST new child message id saved after
    that (the persistence handlers save in order), and never rebound: a later message
    must not become the target of this turn's flag.
    """

    def __init__(self, prev_id: int | None) -> None:
        self.prev_id = prev_id
        self.id: int | None = None

    def offer(self, new_id) -> None:
        if self.id is None and new_id and new_id != self.prev_id:
            self.id = new_id

    async def wait(self, timeout: float) -> int | None:
        deadline = time.monotonic() + timeout
        while self.id is None and time.monotonic() < deadline:
            await asyncio.sleep(0.1)
        return self.id


_EXCERPT_TYPES = {"faq", "aqidah", "fiqh", "sirah"}


def annotate_linked_types(index) -> None:
    """Record, on each indexed ContentItem, the types of the items it links to (sync, DB).

    ``licensed_kinds`` runs inside the event loop and must not query, so the
    ``related`` links of the excerpt items are read once, when the session's index is
    built. Failure is harmless: without it an excerpt only licenses what its own text
    cites (verse markers).
    """
    from session_moral_context.models import ContentItem

    through = ContentItem.related.through
    pks = [pk for pk, e in index.items.items() if e.type in _EXCERPT_TYPES]
    if not pks:
        return
    types: dict[int, set] = {}
    for src, typ in through.objects.filter(from_contentitem_id__in=pks).values_list(
            "from_contentitem_id", "to_contentitem__type"):
        types.setdefault(src, set()).add(typ)
    for pk, found in types.items():
        index.items[pk].obj._linked_types = frozenset(found)


def licensed_kinds(items) -> frozenset:
    """Which attribution kinds the served items license.

    A verse licenses "Allah says" wording only and a hadith "the Prophet said" wording
    only. A tafsir excerpt explains verses, so it licenses "quran" only. The other
    excerpts (faq, aqidah, fiqh, sirah) license nothing by themselves: only the kind
    of what they link to or cite (a verse marker or a related verse, a related hadith).
    Terms and stories license neither. An unlicensed kind keeps the output gate on.
    """
    kinds: set[str] = set()
    for it in items:
        if it.type == "verse":
            kinds.add("quran")
        elif it.type == "hadith":
            kinds.add("hadith")
        elif it.type == "tafsir":
            kinds.add("quran")
        elif it.type in _EXCERPT_TYPES:
            linked = getattr(it, "_linked_types", ())
            if "verse" in linked or verse_refs(getattr(it, "arabic_text", "")) \
                    or verse_refs(getattr(it, "english_text", "")):
                kinds.add("quran")
            if "hadith" in linked:
                kinds.add("hadith")
    return frozenset(kinds)


def age_band_from_birth_year(birth_year: int | None, today: date | None = None) -> str | None:
    """6-9 or 10-13 from the child's birth year (the band is all we keep)."""
    if not birth_year:
        return None
    age = (today or date.today()).year - int(birth_year)
    return "6-9" if age <= 9 else "10-13"


def _turn_lang(text: str, session_lang: str) -> str:
    """Language of the sources we inject: the language the child just used."""
    if has_arabic(text):
        return "ar"
    if any("a" <= ch.lower() <= "z" for ch in text):
        return "en"
    return session_lang if session_lang in ("ar", "en") else "en"


# ``{{card:12}}`` is the marker. A stray ``[card:12]`` (the model echoing a label) is stripped the same
# way; in the SPEECH stream the cleaner has already turned its digits into words ("[card:twelve]"), so
# a bracket form is stripped whatever its inner text and cited only when that text is a number.
_CARD_MARKER = re.compile(r"\{\{\s*card\s*:\s*(\d+)\s*\}\}|\[\s*card\s*:\s*([^\[\]{}]{0,16}?)\s*\]", re.I)
_PARTIAL_BRACKET = re.compile(r"\[\s*(?:c(?:a(?:r(?:d(?:\s*:[^\[\]{}]{0,16})?)?)?)?)?\s*", re.I)
_OPENER = re.compile(r"\{\{|\[")
# "{{card:12}" with ONE closing brace: still a marker, or the scripture filter would hold the open
# "{{" and silence the rest of the reply (review of b96795a6, M4)
_HALF_MARKER = re.compile(r"\{\{\s*card\s*:\s*(\d+)\s*\}(?!\})", re.I)
_MARKER_HOLD = 28  # an opener is held at most this many characters while we wait for its closer


async def strip_card_markers(text, on_card):
    """Remove ``{{card:ID}}`` (and a stray ``[card:ID]``) from a text stream; ``await on_card(id)`` for each.

    A marker split across chunks is held from its opener until its closer or ``_MARKER_HOLD`` characters,
    then released as plain text if it is not a card marker (so the scripture filter still sees every
    other brace). Only card markers are ever removed. Non-text items (flush sentinels) pass through.
    """
    buf = ""
    eat_space = False  # a marker sat between two spaces: drop one of them
    last = " "         # the last character let through
    async for chunk in text:
        if not isinstance(chunk, str):
            yield chunk
            continue
        buf += chunk
        if eat_space and buf:
            buf = buf[1:] if buf[0] == " " else buf
            eat_space = False
        out = ""
        while True:
            m = _OPENER.search(buf)
            if not m:
                keep = 1 if buf.endswith("{") else 0  # a lone "{" may be the start of "{{"
                out += buf[:len(buf) - keep]
                buf = buf[len(buf) - keep:]
                break
            out += buf[:m.start()]
            buf = buf[m.start():]
            mh = _HALF_MARKER.match(buf)
            if mh and mh.end() < len(buf):  # the next character is known and is not "}"
                await on_card(int(mh.group(1)))
                buf = buf[mh.end():]
                if (out[-1] if out else last).isspace() and buf[:1] == " ":
                    buf = buf[1:]
                continue
            closer = "}}" if buf[0] == "{" else "]"
            j = buf.find(closer)
            end = j + len(closer)
            if 0 <= j and end <= _MARKER_HOLD:
                mm = _CARD_MARKER.fullmatch(buf[:end])
                if mm:
                    inner = mm.group(1) or (mm.group(2) or "").strip()
                    if inner.isdigit():
                        await on_card(int(inner))
                    buf = buf[end:]
                    if (out[-1] if out else last).isspace():
                        if buf[:1] == " ":
                            buf = buf[1:]
                        elif not buf:
                            eat_space = True
                else:
                    out += buf[:end]
                    buf = buf[end:]
                continue
            if buf[0] == "[" and not _PARTIAL_BRACKET.fullmatch(buf):  # not the start of a card marker
                out += "["
                buf = buf[1:]
                continue
            if len(buf) >= _MARKER_HOLD:  # no close in sight: plain text; look again after the opener
                step = 2 if buf[0] == "{" else 1
                out += buf[:step]
                buf = buf[step:]
                continue
            break  # hold the partial marker for the next chunk
        if out:
            last = out[-1]
            yield out
    if buf:
        mh = _HALF_MARKER.fullmatch(buf)
        if mh:  # the reply ended right after "{{card:12}"
            await on_card(int(mh.group(1)))
        else:
            yield buf


@sync_to_async
def _write_turn_records(session_id: int, hit: GuardHit) -> None:
    from conversation.models import TurnAudit

    TurnAudit.objects.create(
        session_id=session_id, level=hit.level or "", mode=hit.kind, served_item_ids=[],
        safety=hit.kind == SAFETY,
    )


@sync_to_async
def _write_reply_audit(session_id: int, mode: str, level: str, item_ids: list[int]) -> None:
    from conversation.models import TurnAudit

    TurnAudit.objects.create(
        session_id=session_id, level=level, mode=mode, served_item_ids=item_ids, safety=False)


@sync_to_async
def _write_served_reference(session_id: int, item_id: int) -> None:
    from session_moral_context.models import ServedReference

    ServedReference.objects.create(session_id=session_id, item_id=item_id, via="tool")


class TurnGuardMixin:
    """Mix in before ``Agent``: ``class AlSadiqAgent(TurnGuardMixin, Agent)``."""

    def _init_turn_guard(self, *, language: str = "en", age_band: str | None = None,
                         value_index: ValueIndex | None = None) -> None:
        self._guard_language = language if language in ("ar", "en") else "en"
        self._age_band = age_band
        self._value_index = value_index or EMPTY_INDEX
        self._turn_language = self._guard_language  # language of the child's current turn
        self._turn_text = ""          # the child's words this turn (flag_safety_concern's family check)
        self._flagged_turn = False    # flag_safety_concern ran this turn: no sources or cards
        self._turn_items: list = []   # items search_bank returned this turn ...
        self._prev_items: list = []   # ... and last turn (a "why?" follow-up may still cite them)
        self._tool_ran = False        # search_bank ran this turn (not a REFER turn)
        self._tool_found = False      # ... and found something
        self._cards: list[int] = []   # ids cited with a valid marker this turn (the audit's "cited")
        self._cards_published: list[int] = []  # ids whose card was published THIS turn
        self._shown_card_ids: set[int] = set()  # ids whose card was published in this SESSION (once each)
        self._marker_seen: set[int] = set()  # every {{card:N}} id seen this turn, valid or not
        self._turn_no = 0                  # child turns so far this session (counted in _prepare)
        self._last_card_turn = None        # the turn number a source card was last published, None: never
        self._turn_audited = False
        self._refer_turn = False           # this turn is a REFER turn: no sources
        self._safety_turn = False          # this turn is mode=SAFETY (flag handled by the guard)
        self._no_comfort = False           # sticky: a safety turn, flag or disclosure: no comfort verse after it
        self._comfort_given = False        # sticky: one comfort verse per session
        self._alerted_rules: set[str] = set()  # rules that already alerted a parent (once each)
        self._guard_tasks: set[asyncio.Task] = set()
        self._turn_ref: TurnRef | None = None  # the child message of the turn in progress
        self.last_hit: GuardHit | None = None

    @property
    def _last_child_message_id(self) -> int | None:
        return self.__dict__.get("_child_msg_id")

    @_last_child_message_id.setter
    def _last_child_message_id(self, value) -> None:
        self.__dict__["_child_msg_id"] = value
        ref = self.__dict__.get("_turn_ref")
        if ref is not None:
            ref.offer(value)

    # -------------------------------------------------------------- lifecycle

    async def on_enter(self) -> None:
        # The reply is done once its assistant message is committed: audit it then.
        def _committed(event) -> None:
            if getattr(event.item, "role", None) == "assistant":
                self._audit_reply()

        self.session.on("conversation_item_added", _committed)

    # ---------------------------------------------------------------- core

    def _prepare(self, text: str, typed: bool = False) -> str:
        """Run the guard, fire the side effects, return the text to inject ("" when none).

        REPLY_LANGUAGE_FOLLOWS_CHILD off (the default): hk/12's guard turn and nothing else
        (``_guard_turn``): the same turn note, the same side effects; ``typed`` is not read, the
        TTS is not touched and no TURN LANGUAGE line is added. On: the reply language of the turn
        is decided too (turn_language.decide_reply_language; ``typed`` is True for a typed
        message, ``reply_to_typed``, False for a spoken turn), the TTS language hint follows it,
        and a TURN LANGUAGE line goes after the turn note, on its own line (the note's text is
        not touched), when the reply language differs from the session's or from the last turn's.
        A context change cancels a preemptive generation, so an ordinary turn in the session
        language adds nothing."""
        note = self._guard_turn(text)
        if not reply_language_follows_child():
            return note
        previous = self.reply_language
        lang = decide_reply_language(text, self._guard_language, previous, typed=typed)
        self.__dict__["_reply_lang"] = lang
        self._follow_voice_language(lang)
        if lang != self._guard_language or lang != previous:
            line = language_line(lang)
            return f"{note}\n\n{line}" if note else line
        return note

    @property
    def reply_language(self) -> str:
        """The reply language of the turn ("ar" or "en").

        REPLY_LANGUAGE_FOLLOWS_CHILD off (the default): the live session language, whatever the
        child says. On: the reply language ``_prepare`` decided for the child's latest message;
        the session language until the child has said something. (``_turn_language`` is another
        thing: hk/12's script check of the child's words, kept as it was.)"""
        if reply_language_follows_child():
            value = self.__dict__.get("_reply_lang")
            if value in ("ar", "en"):
                return value
        live = str(self.__dict__.get("_language") or "").strip().lower()[:2]   # the live session language
        return live if live in ("ar", "en") else self._guard_language

    def _guard_reply_language(self) -> str:
        """The language of the attribution guard's decline line: hk/12's session language
        (``_guard_language``) with REPLY_LANGUAGE_FOLLOWS_CHILD off, the turn's reply language on."""
        return self.reply_language if reply_language_follows_child() else self._guard_language

    def _follow_voice_language(self, lang: str) -> None:
        """Point the TTS at the reply language of this turn, where the voice supports it.
        Called with REPLY_LANGUAGE_FOLLOWS_CHILD on only.

        Only the ElevenLabs "language_code" hint needs this (tts_factory sets it for the session
        language; without it ElevenLabs already detects per sentence): an English reply spoken
        with language_code "ar" would be mispronounced, so not following is the worse choice.
        The voice id itself stays the parent's (session) language voice, so Sadiq sounds like
        Sadiq in either language. The plugin opens a new connection after a change (one
        reconnect on the turn the language switches). Only an "ar" or "en" hint is followed:
        any other value (none, "auto", a provider without update_options) is left alone. The STT
        language is NOT switched: it is fixed per session (stt_factory, detect_language off), so
        a child speaking the other language is transcribed with the session language's model.
        Never raises: the reply still goes out in the old language setting."""
        try:
            tts = self.session.tts
            opts = getattr(tts, "_opts", None)
            current = str(getattr(opts, "language", "") or "").lower().split("-")[0]
            if current not in ("ar", "en") or not hasattr(tts, "update_options"):
                return                      # no ar/en hint set (or another provider): nothing to follow
            if current == lang:
                return
            tts.update_options(language=lang)
        except Exception:  # noqa: BLE001 - voice follow-up is best effort
            logger.debug("turn guard: could not follow the turn language in the TTS", exc_info=True)

    def _guard_turn(self, text: str) -> str:
        """Run the guard, fire the side effects, return the turn note to inject ("" when none)."""
        started = time.perf_counter()
        self._turn_no += 1
        self._prev_items, self._turn_items = self._turn_items, []
        self._tool_ran = self._tool_found = self._turn_audited = False
        self._cards, self._marker_seen, self._cards_published = [], set(), []
        self._safety_turn = self._refer_turn = False
        self._flagged_turn = False  # the model called flag_safety_concern this turn: no sources either
        self._turn_language = _turn_lang(text, self._guard_language)
        self._turn_text = text
        if comfort_blocked(text):
            self._no_comfort = True  # a disclosure: no comfort verse for the rest of the session (hk/13b)
        ref = TurnRef(self._last_child_message_id)
        self._turn_ref = ref
        try:
            hit = check(text)
        except Exception:
            # fail closed: no silent pass. The model is told to read the message for safety itself.
            logger.exception("turn guard failed: session_id=%s", getattr(self, "_db_session_id", None))
            self.last_hit = None
            self._spawn(_write_reply_audit(self._db_session_id, GUARD_ERROR, "", []))
            return GUARD_ERROR_NOTE
        self.last_hit = hit
        if hit is None:
            return ""
        if hit.kind == SAFETY:
            self._safety_turn = self._no_comfort = True
        elif hit.kind == REFER:
            self._refer_turn = True
        logger.info("turn guard: kind=%s level=%s rule=%s ms=%.1f", hit.kind, hit.level or "-",
                    hit.rule_id or "-", (time.perf_counter() - started) * 1000)
        if hit.kind in (SAFETY, REFER):
            # the new child message is saved after this returns: the TurnRef binds to it
            self._spawn(self._after_turn(hit, ref))
        return hit.note

    def _spawn(self, coro) -> None:
        try:
            task = asyncio.get_running_loop().create_task(coro)
        except RuntimeError:
            coro.close()
            return
        self._guard_tasks.add(task)
        task.add_done_callback(self._guard_tasks.discard)

    async def _after_turn(self, hit: GuardHit, ref: TurnRef) -> None:
        """Audit row and, for a safety hit, the flag."""
        if hit.kind == SAFETY:
            self._spawn(self._flag_safety(hit, ref))
        try:
            await _write_turn_records(self._db_session_id, hit)
        except Exception:
            logger.exception("turn guard: could not write audit rows: session_id=%s", self._db_session_id)

    async def _publish_event(self, topic: str, payload: dict) -> None:
        room = getattr(self, "_room", None)
        if not room:
            return
        try:
            await room.local_participant.publish_data(
                json.dumps(payload).encode("utf-8"), reliable=True, topic=topic)
        except Exception:
            logger.exception("turn guard: failed to publish %s event: session_id=%s",
                             topic, self._db_session_id)

    async def _flag_safety(self, hit: GuardHit, ref: TurnRef) -> None:
        """Run the existing flag flow without waiting for the LLM.

        The child's message row is written by the persistence handler after this
        hook returns, so wait (bounded) for the id the turn's ``TurnRef`` binds to. If
        none arrives the flag is skipped (never attached to another message) and
        logged.

        Every disclosure gets a SafetyFlag on its own message and a parent Alert (always the
        neutral text), at most once per rule per session. Family cases alert the parent too
        (lead decision, hk/12g: parents are trusted); there is no staff-only path.
        """
        from .agent_class import _create_safety_flag_and_alert

        msg_id = await ref.wait(_FLAG_WAIT_SECONDS)
        if not msg_id:
            logger.warning("turn guard: safety flag skipped, no new message id: session_id=%s rule=%s",
                           self._db_session_id, hit.rule_id)
            return
        notify = hit.rule_id not in self._alerted_rules
        if notify:
            self._alerted_rules.add(hit.rule_id)
        try:
            await _create_safety_flag_and_alert(
                message_id=msg_id,
                session_id=self._db_session_id,
                child_id=self._child_id,
                flag_type=hit.flag_type or "sensitive",
                description=f"Automatic turn guard, staff review: matched the "
                            f"'{hit.rule_id}' safety pattern.",
                notify_parents=notify,
                alert_description=NEUTRAL_ALERT_DESCRIPTION,
            )
        except Exception:
            if notify:
                self._alerted_rules.discard(hit.rule_id)
            logger.exception("turn guard: safety flag failed: session_id=%s", self._db_session_id)

    # ----------------------------------------------------- search_bank bookkeeping

    @property
    def _turns_since_card(self) -> int | None:
        """Turns since a source card was last shown (0: this turn); None when none was shown yet."""
        return None if self._last_card_turn is None else self._turn_no - self._last_card_turn

    def _remember_items(self, items: list, found: bool) -> None:
        """search_bank ran: keep what it returned for the card check, the licence and the audit."""
        self._turn_items = self._turn_items + [i for i in items if i not in self._turn_items]
        self._tool_ran = True
        self._tool_found = self._tool_found or found

    async def _cite(self, item_id: int) -> None:
        """A ``{{card:ID}}`` marker was seen in the reply: show that card.

        At most two cited items a turn, and a card is published (with its ServedReference row) only the
        first time the item is cited in the SESSION: a re-cited id is stripped silently, but still counts
        as cited for the audit and the licence.
        """
        if self._safety_turn or self._refer_turn or getattr(self, "_flagged_turn", False):
            return  # a safety, flagged or referral turn shows no sources: the marker is stripped, nothing cited
        if item_id in self._marker_seen:
            return
        self._marker_seen.add(item_id)
        item = next((i for i in self._turn_items + self._prev_items if i.pk == item_id), None)
        if item is None:
            logger.info("card marker dropped: id=%s is not an item search_bank returned (session_id=%s)",
                        item_id, self._db_session_id)
            return
        if len(self._cards) >= MAX_CARDS_PER_TURN:
            return
        self._cards.append(item_id)
        if item_id in self._shown_card_ids:
            return
        self._shown_card_ids.add(item_id)
        self._cards_published.append(item_id)
        self._last_card_turn = self._turn_no
        try:  # a card problem must never break the speech or transcript stream
            await self._publish_event("reference", card_payload(
                item, self._guard_language, self._age_band, self._value_index))
            self._spawn(_write_served_reference(self._db_session_id, item_id))
        except Exception:
            logger.exception("card could not be published: id=%s session_id=%s", item_id, self._db_session_id)

    def _audit_reply(self) -> None:
        """When the reply is committed: one TurnAudit row for a turn that used search_bank."""
        if not self._tool_ran or self._turn_audited or self._safety_turn:
            return
        self._turn_audited = True
        by_pk = {i.pk: i for i in self._prev_items + self._turn_items}
        cited = [by_pk[k] for k in self._cards if k in by_pk]
        basis = cited or self._turn_items
        if not self._tool_found:
            mode, level = DECLINE_NO_SOURCE, ""
        else:
            mode = DISAGREE_AND_REFER if any(item_level(i) == "C" for i in basis) else ANSWER
            level = max_level(basis)
        self._spawn(_write_reply_audit(self._db_session_id, mode, level, [i.pk for i in cited]))

    # ------------------------------------------------------------ entry points

    async def on_user_turn_completed(self, turn_ctx, new_message) -> None:
        text = (new_message.text_content or "").strip()
        if not text:
            return
        injection = self._prepare(text)
        if injection:
            turn_ctx.add_message(role="system", content=injection)

    def reply_to_typed(self, session, text: str):
        """Typed-text twin of ``on_user_turn_completed`` (same ``_prepare``).

        A turn note goes into a copy of the chat context passed as ``chat_ctx=``
        (not ``instructions=``): in 1.5.1 the tool-call follow-up request resets the
        instructions to the agent's own but reuses the chat_ctx, so only this way
        does the note survive a function call, as it does on the voice path.
        """
        from livekit.agents import llm

        text = text or ""
        injection = self._prepare(text.strip(), typed=True)  # the guard reads the FULL text
        message = llm.ChatMessage(role="user", content=[cap_typed_text(text)])
        if not injection:
            return session.generate_reply(user_input=message)
        ctx = self.chat_ctx.copy()
        ctx.add_message(role="system", content=injection)
        return session.generate_reply(user_input=message, chat_ctx=ctx)

    def _licence(self):
        """Attribution kinds the items search_bank returned THIS turn license (last turn's items only
        validate a card id in ``_cite``): a follow-up with no search cannot say "the Prophet said"."""
        if (getattr(self, "_safety_turn", False) or getattr(self, "_refer_turn", False)
                or getattr(self, "_flagged_turn", False)):
            return frozenset()  # no sources on a safety or referral turn
        items = self._turn_items
        return licensed_kinds(items) if items else frozenset()

    def guard_speech(self, text, count: bool = True):
        """Output guards for the reply text: card markers first (the scripture filter would
        drop a short ``{{...}}``), then the attribution check, then the scripture filter, then
        LAST the off-script characters the strip before the guards passed on
        (tts_text.tidy_off_script_stream: look-alike letters to Latin, full-width forms to plain
        ones, Devanagari and Thai digits to ASCII, other off-script runs out). That last stage
        never feeds a guard: the card markers, the attribution guard and the scripture filter
        read exactly the text they read before it existed. ``count`` is True for the voice
        (tts_node), False for the chat transcript (guard_transcript). The decline line is in the
        session language (``_guard_language``), as on hk/12; with REPLY_LANGUAGE_FOLLOWS_CHILD on,
        in the turn's reply language (``_guard_reply_language``)."""
        return tidy_off_script_stream(filter_scripture_stream(
            guard_attribution_stream(
                strip_card_markers(text, self._cite), self._licence, self._guard_reply_language(), count=count),
            count=count))

    async def guard_transcript(self, text):
        """Same guards for the chat transcript.

        With a streaming TTS (no aligned transcript) the transcript is the raw LLM
        text, not what the TTS received, so ``transcription_node`` must apply the
        same filter or the bubble and the saved message would show what was blocked
        from the audio. Aligned (timed) chunks come from the guarded TTS input and
        pass through untouched.
        """
        from livekit.agents.types import TimedString

        it = text.__aiter__()
        try:
            first = await it.__anext__()
        except StopAsyncIteration:
            return
        if isinstance(first, TimedString):
            yield first
            async for chunk in it:
                yield chunk
            return

        async def _chunks():
            yield first
            async for chunk in it:
                yield chunk

        async for out in self.guard_speech(_chunks(), count=False):
            yield out
