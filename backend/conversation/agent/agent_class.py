import asyncio
import json
import logging
import time

from asgiref.sync import sync_to_async
from livekit.agents import Agent
from livekit.agents.llm import function_tool
from livekit.agents.voice.transcription.filters import filter_emoji, filter_markdown

from conversation.agent import bank_search
from conversation.agent.avatar_signals import AvatarSignals
from conversation.agent.llm_fallback import KIND_GREETING, last_user_text, with_llm_fallback
from conversation.agent.prompt import build_instructions
from conversation.agent.tts_text import strip_foreign_script_stream
from conversation.agent.turn_language import reply_language_follows_child
from conversation.agent.turn_pipeline import TurnGuardMixin, _turn_lang
from content_safety.models import NEUTRAL_ALERT_DESCRIPTION

logger = logging.getLogger(__name__)

# Real-time engagement guard rails: the LLM decides *when* points are
# deserved, these caps decide how often that is allowed to land.
_ENGAGEMENT_COOLDOWN_SECONDS = 25
_ENGAGEMENT_MAX_EVENTS_PER_SESSION = 15
_TOOL_ALERT_KEY = "tool"  # key in _alerted_rules: the tool alerts a parent once a session
_TOOL_MESSAGE_WAIT_SECONDS = 3.0  # how long the tool waits for the turn's child message to be saved

# Ends the record_engagement result when the child reached a new level. speak_first.py keeps
# the model's follow-up round for exactly this case (it celebrates in words) and skips it for
# every ordinary points change.
LEVEL_UP_NOTE = "— celebrate this!"

NO_SOURCES_TOOL_TEXT = ("This turn is about safety or a referral: no sources. "
                        "Follow the turn note.")
# hk/13b: one comfort verse per session; later sad turns get comfort in words only
COMFORT_GIVEN_TOOL_TEXT = ("A comfort verse was already shared in this conversation: comfort in your own "
                           "words only, and do not repeat or mention that verse again.")


class AlSadiqAgent(TurnGuardMixin, Agent):
    def __init__(
        self,
        *,
        db_session_id: int,
        child_id: int,
        session_memory: str | None = None,
        language: str = "en",
        active_quests_text: str | None = None,
        age_band: str | None = None,
        value_index=None,
    ) -> None:
        self._db_session_id = db_session_id
        self._child_id = child_id
        self._language = language
        self._last_child_message_id: int | None = None
        # Set by entrypoint after connecting; used to push live gamification
        # updates to the child's UI over the LiveKit data channel.
        self._room = None
        self._lipsync = None
        self._gestures = None
        self._search = None              # search_results.SearchPublisher (al.search), see set_search
        self._search_provider = None     # the web tool or the dev fixtures, see set_search
        self._safety_flagged_msg: int | None = None   # the child message a safety concern was flagged on
        self._init_turn_guard(language=language, age_band=age_band, value_index=value_index)
        self._engagement_event_count = 0
        self._last_engagement_at = 0.0
        self.signals = AvatarSignals()  # the avatar's al.* attributes (avatar_signals.py)

        super().__init__(instructions=build_instructions(
            language=language, age_band=age_band, session_memory=session_memory,
            active_quests_text=active_quests_text,
            value_names=[v.slug for v in getattr(value_index, "values", [])]))

    def set_room(self, room) -> None:
        self._room = room
        self.signals.bind(room)

    def set_lipsync(self, timeline) -> None:
        """Forward the TTS character timings through `timeline` (lipsync_timeline.LipsyncTimeline)."""
        self._lipsync = timeline

    def set_gestures(self, planner) -> None:
        """Plan word-anchored gestures (gesture_planner.GesturePlanner). They travel on the lip-sync
        timeline, so they only run when one is set."""
        self._gestures = planner

    def set_search(self, publisher, provider) -> None:
        """Wire the web page the avatar holds while searching: `publisher` is a
        search_results.SearchPublisher, `provider` an async (query, lang) -> list of result dicts that declares
        safe_search = True (the web tool, or search_results.DevSearchProvider with SEARCH_DEV_SIM=1)."""
        self._search, self._search_provider = publisher, provider

    def safety_flagged_this_turn(self) -> bool:
        return self._safety_flagged_msg is not None and self._safety_flagged_msg == self._last_child_message_id

    async def web_search(self, query: str) -> int:
        """THE HOOK for a web tool (not a function_tool, so the model cannot call it today). The agent team's tool
        body is `return await self.web_search(query)` once a provider is set; it publishes al.search and, with
        the signals branch merged, drives the searching/found/none activity. Returns the cards shown."""
        if self._search is None or self._search_provider is None:
            return 0
        signals = getattr(self, "signals", None)
        if signals is None:
            return await self._search.search(query, self._search_provider)
        async with signals.search("web") as s:
            shown = await self._search.search(query, self._search_provider)
            s.found = shown > 0
        return shown

    @property
    def llm_fallback_count(self) -> int:
        """How many fixed fallback lines this session has said (read by the latency log)."""
        return self.__dict__.get("_llm_fallback_count", 0)

    def _count_llm_fallback(self) -> None:
        self.__dict__["_llm_fallback_count"] = self.llm_fallback_count + 1

    def llm_node(self, chat_ctx, tools, model_settings):
        """The default LLM node, plus one fixed line when the model fails before saying anything
        (rate limit, dropped connection, timeout): see llm_fallback.py. A normal stream passes
        through unchanged, chunk for chunk."""

        def language_for(kind: str) -> str:
            if kind == KIND_GREETING:
                return self.language
            if reply_language_follows_child():
                return self.reply_language      # the reply language _prepare decided for this turn
            return _turn_lang(last_user_text(chat_ctx) or "", self.language)   # hk/12's, flag off

        return with_llm_fallback(
            Agent.default.llm_node(self, chat_ctx, tools, model_settings),
            chat_ctx=chat_ctx,
            language_for=language_for,
            safety_turn=lambda: self._safety_turn,
            session_id=self._db_session_id,
            on_fallback=self._count_llm_fallback,
        )

    async def tts_node(self, text, model_settings):
        """The default TTS node. With no lip-sync timeline it is exactly the default; with one,
        every frame also goes through it. The frames are never changed, delayed or dropped.
        The text is never changed either: the reply's opening is read on the side for the avatar
        (avatar signals, signals.tap_reply) and, when gestures are on, planned clause by clause
        (gesture planner). All three features share this one node (avatar-integ).

        Before any of that the text goes through the lead's output guards (turn_pipeline.guard_speech):
        the attribution guard (an unlicensed "the Prophet said / Allah says" tail becomes the
        decline line) and the scripture filter again, in case anything slipped past the session's
        tts_text_transforms (conversation/agent/tts_text.py, which already did digits, markdown,
        emoji, honorifics and scripture-shaped spans). The avatar, the timeline and the planner
        therefore see exactly the words that are spoken. This node deliberately does NOT strip
        markdown or emoji a second time."""
        timeline, seg = self._lipsync, None
        text = self.guard_speech(text)
        if timeline is not None and self._gestures is not None:
            seg = self._gestures.segment()  # never raises; None when planning is off
            if seg is not None:
                text = seg.tap_text(text)  # chunks go on first, then each clause is planned
        frames = Agent.default.tts_node(self, self.signals.tap_reply(text), model_settings)
        tapped = self._tapped(timeline, frames, seg)
        try:
            async for frame in tapped:
                yield frame
        finally:
            await tapped.aclose()  # closes the default node too (see _tapped)

    @staticmethod
    async def _tapped(timeline, frames, seg=None):
        if asyncio.iscoroutine(frames):
            frames = await frames
        if frames is None:
            return
        try:
            if timeline is None:
                tapped = frames
            else:
                tapped = timeline.tap(frames) if seg is None else timeline.tap(frames, plan=seg)
            async for frame in tapped:
                yield frame
        finally:
            # The default node cancels its input task when it is closed: pass the close on.
            close = getattr(frames, "aclose", None)
            if close is not None:
                await close()

    @property
    def language(self) -> str:
        """Live session language ("ar" or "en"), read by the speech cleaner.

        The entrypoint's tts_text_transforms entry reads this each time text is released
        for speech, so setting it mid-session changes how numbers are spoken from then on.
        """
        return self._language

    @language.setter
    def language(self, value: str) -> None:
        self._language = (value or "en").strip() or "en"
        self.__dict__.pop("_reply_lang", None)   # the reply language restarts from the new session language

    @property
    def speech_language(self) -> str:
        """The language the speech cleaner reads numbers in and the goodbye line is said in (the
        entrypoint reads it live). REPLY_LANGUAGE_FOLLOWS_CHILD off (the default): the session
        language, exactly as hk/12 read it (``language``). On: the turn's reply language
        (``reply_language``), so an English reply in an Arabic session says its numbers in English."""
        return self.reply_language if reply_language_follows_child() else self.language

    def _aligned_transcript_on(self) -> bool:
        """True when the transcript source is TTS word timings (already speech-cleaned)."""
        own = self.use_tts_aligned_transcript
        if isinstance(own, bool):
            return own
        try:
            return self.session.options.use_tts_aligned_transcript is True
        except Exception:  # agent not running yet
            return False

    def transcription_node(self, text, model_settings):
        """Chat and DB transcript: the LLM text, guarded and without markdown or emoji.

        With use_tts_aligned_transcript=False (the entrypoint setting) this node gets
        the untouched LLM text, not what the cleaner sent to the TTS, so digits stay
        digits and the honorific stays written. The compliance guards (attribution and
        scripture) are applied here too, so the bubble and the saved message never
        show what was blocked from the audio (turn_pipeline.guard_transcript). Markdown
        and emoji are stripped FIRST, so the guards see the same plain words the speech
        guards see after the cleaner ("the **Prophet** said" is declined in both, not only
        in the audio), and the chat never shows stray symbols.

        A plain def returning an async iterable: livekit accepts either an awaitable or
        an iterable from this node. If aligned transcripts are ever switched on, the
        text arriving here is already cleaned and carries word timings, so it passes
        through untouched.
        """
        if self._aligned_transcript_on():
            return Agent.default.transcription_node(self, text, model_settings)
        return Agent.default.transcription_node(
            self,
            self.guard_transcript(strip_foreign_script_stream(filter_markdown(filter_emoji(text)))),
            model_settings,
        )

    async def _publish_gamification(self, payload: dict) -> None:
        """Best-effort push to the child's UI; never break the conversation."""
        if not self._room:
            return
        try:
            await self._room.local_participant.publish_data(
                json.dumps(payload).encode("utf-8"),
                reliable=True,
                topic="gamification",
            )
        except Exception:
            logger.exception(
                "Failed to publish gamification update: session_id=%s",
                self._db_session_id,
            )

    @function_tool
    async def flag_safety_concern(self, flag_type: str, description: str, at_home: bool = False) -> str:
        """Record a content safety flag when a child's message contains concerning content.

        Call this whenever the child says something involving harm, abuse, danger,
        inappropriate topics, or serious emotional distress, unless a SAFETY note
        says it is already recorded. This creates a record for review.

        Args:
            flag_type: One of 'harmful', 'inappropriate', 'sensitive', 'off_topic'
            description: Brief description of the concern in 1-2 sentences
            at_home: True when the person involved is family or lives with the child
        """
        self.signals.hint_safety()
        self._flagged_turn = True  # no sources or cards after a concern in this turn (review of hk/13)
        self._no_comfort = True    # nor a comfort verse later in the session (hk/13b)
        flag_type = (flag_type or "").strip().lower()
        if self._safety_turn:
            return "Already recorded for this message; no need to call again."
        # the message of THIS turn (captured when the turn started), not whichever child
        # message happens to be the newest by the time the model calls the tool
        ref = self._turn_ref
        message_id = None
        if ref is not None:
            message_id = ref.id or await ref.wait(_TOOL_MESSAGE_WAIT_SECONDS)
        message_id = message_id or self._last_child_message_id
        # Every model flag but off_topic alerts a parent (neutral text only), once per session,
        # family cases included (lead decision, hk/12g: parents are trusted; at_home is not used
        # for routing). off_topic is recorded for review only: it never alerts and never uses up
        # the session's alert.
        if not message_id:
            return "No recent message to flag."
        self._safety_flagged_msg = message_id
        notify = flag_type != "off_topic" and _TOOL_ALERT_KEY not in self._alerted_rules
        if notify:
            self._alerted_rules.add(_TOOL_ALERT_KEY)
        try:
            await _create_safety_flag_and_alert(
                message_id=message_id,
                session_id=self._db_session_id,
                child_id=self._child_id,
                flag_type=flag_type,
                description=description,
                notify_parents=notify,
                alert_description=NEUTRAL_ALERT_DESCRIPTION,
            )
        except Exception:
            if notify:
                self._alerted_rules.discard(_TOOL_ALERT_KEY)
            raise
        return "Recorded."  # never tells the model (or the child) whether anyone was notified

    @function_tool
    async def search_bank(self, question: str, topic: str, values: list[str] | None = None) -> str:
        """Search Al-Sadiq's verified Islamic library. Call it before you say anything about Allah, the
        Prophet, the Quran, hadith, worship, du'a, the unseen or a prophet's story. Also call it before
        advice on treating people, or for a value moment. For another one, share an item not shown yet,
        else say that's all you have on this topic.

        Args:
            question: The child's question.
            topic: values, quran, hadith, creed, afterlife, worship, prophets_story, word_meaning
                (only for one Islamic word's meaning), or comfort (a sad, scared or grieving child).
            values: Up to two value names from your instructions.
        """
        lang = self._guard_language  # the parent's choice for the session, not the child's per-turn language
        turn_text = self._turn_text  # read before any await (a new turn may start)
        async with self.signals.search("library") as s:
            if self._refer_turn or self._safety_turn or getattr(self, "_flagged_turn", False):
                return NO_SOURCES_TOOL_TEXT
            comfort = bank_search._topic(topic) == "comfort"
            if comfort and (getattr(self, "_no_comfort", False) or bank_search.comfort_blocked(turn_text, question)):
                self._no_comfort = True
                return NO_SOURCES_TOOL_TEXT   # a disclosure: the safety rules, never a comfort verse
            if comfort and getattr(self, "_comfort_given", False):
                return COMFORT_GIVEN_TOOL_TEXT
            try:
                items = bank_search.search(self._value_index, question, topic, values, lang, self._age_band)
                result = bank_search.format_result(items, lang, self._age_band, topic,
                                                   turns_since_card=self._turns_since_card)
            except Exception:
                logger.exception("search_bank failed: session_id=%s", self._db_session_id)
                items, result = [], bank_search.format_result([], lang, self._age_band, topic)
            self._remember_items(items, bool(items))
            if comfort and items:
                self._comfort_given = True
            s.found = bool(items)
            return result

    @function_tool
    async def record_engagement(self, quality: str, reason: str) -> str:
        """Register a real-time point change for how the conversation is going.

        Call at the moment it is earned: 'excellent' for a brave moment practising
        a value (telling the truth, forgiving, helping, being patient) or deep
        moral engagement, 'good' for positive values-focused engagement,
        'poor' for drifting to unsuitable topics after one redirect,
        'bad' for persistently pushing inappropriate topics. Plain friendly chat and thanks
        earn nothing.

        Args:
            quality: One of 'excellent', 'good', 'poor', 'bad'
            reason: Short child-friendly reason, e.g. 'Told the truth about a mistake'
                or 'Forgave a friend'
        """
        now = time.monotonic()
        if self._engagement_event_count >= _ENGAGEMENT_MAX_EVENTS_PER_SESSION:
            return "Point limit for this session reached; keep encouraging without points."
        if now - self._last_engagement_at < _ENGAGEMENT_COOLDOWN_SECONDS:
            return "Too soon since the last point change; continue the conversation naturally."

        result = await _record_engagement_points(
            child_id=self._child_id,
            session_id=self._db_session_id,
            quality=quality,
            reason=reason,
        )
        if result is None:
            return "Could not record points right now; continue normally."

        self._engagement_event_count += 1
        self._last_engagement_at = now
        if str(quality).strip().lower() in ("excellent", "good"):
            self.signals.hint_praise()

        await self._publish_gamification({
            "type": "points",
            "delta": result["delta_applied"],
            "reason": reason,
            "total_points": result["total_points"],
            "level_number": result["level_number"],
            "level_name": result["level_name"],
            "progress_pct": result["progress_pct"],
            "leveled_up": result["leveled_up"],
            "leveled_down": result["leveled_down"],
        })

        sign = "+" if result["delta_applied"] >= 0 else ""
        msg = f"Recorded {sign}{result['delta_applied']} points (total {result['total_points']})."
        if result["leveled_up"]:
            msg += (
                f" The child just reached level {result['level_number']}: {result['level_name']}"
                f" {LEVEL_UP_NOTE}"
            )
        return msg

    @function_tool
    async def list_my_quests(self) -> str:
        """List the child's current quests with their ids, types, and statuses.

        The open quests are already in your instructions at the start of the session,
        so use this only when you need fresh ids or progress after something changed.
        """
        async with self.signals.search("folders") as s:
            rows = await _get_child_quests(self._child_id)
            s.found = bool(rows)
        if not rows:
            return "The child has no quests yet."
        return "\n".join(rows)

    @function_tool
    async def complete_conversation_quest(self, progress_id: int, summary: str) -> str:
        """Mark a 'conversation' quest as completed after the child genuinely engaged with it.

        Only call when the child truly worked through the quest's purpose with you
        in this conversation — not when they merely claim it is done.

        Args:
            progress_id: The quest progress id from list_my_quests
            summary: One sentence on how the child engaged with the quest
        """
        result = await _complete_companion_quest(
            child_id=self._child_id,
            session_id=self._db_session_id,
            progress_id=progress_id,
        )
        if isinstance(result, str):
            return result

        await self._publish_gamification({
            "type": "quest_completed",
            "quest_title": result["quest_title"],
            "reward_points": result["points"]["delta_applied"],
            "total_points": result["points"]["total_points"],
            "level_number": result["points"]["level_number"],
            "level_name": result["points"]["level_name"],
            "progress_pct": result["points"]["progress_pct"],
            "leveled_up": result["points"]["leveled_up"],
            "new_badges": result["new_badges"],
        })

        msg = (
            f"Quest '{result['quest_title']}' completed — "
            f"+{result['points']['delta_applied']} points "
            f"(total {result['points']['total_points']})."
        )
        if result["points"]["leveled_up"]:
            msg += f" Level up to {result['points']['level_number']}: {result['points']['level_name']}!"
        if result["new_badges"]:
            names = ", ".join(b["name"] for b in result["new_badges"])
            msg += f" New badge(s) earned: {names}. Celebrate with the child!"
        return msg


@sync_to_async
def _create_safety_flag_and_alert(
    message_id: int,
    session_id: int,
    child_id: int,
    flag_type: str,
    description: str,
    notify_parents: bool = True,
    alert_description: str | None = None,
) -> str:
    from authentication.models import ParentChildLink
    from content_safety.models import NEUTRAL_ALERT_DESCRIPTION, Alert, SafetyFlag

    valid_types = {'harmful', 'inappropriate', 'sensitive', 'off_topic'}
    if flag_type not in valid_types:
        flag_type = 'sensitive'

    SafetyFlag.objects.create(
        message_id=message_id,
        flag_type=flag_type,
        description=description,
        is_blocked=False,
    )

    if not notify_parents:
        # Review-only flag: off_topic, or the parent was already alerted for this in the session.
        return "Recorded for review."

    parent_ids = list(
        ParentChildLink.objects
        .filter(child_id=child_id, consent_status='approved')
        .values_list('parent_id', flat=True)
    )

    for parent_id in parent_ids:
        Alert.objects.create(
            session_id=session_id,
            parent_id=parent_id,
            alert_type='safety',
            description=alert_description or NEUTRAL_ALERT_DESCRIPTION,
        )

    return f"Flagged. {len(parent_ids)} parent(s) notified."


@sync_to_async
def _record_engagement_points(
    child_id: int,
    session_id: int,
    quality: str,
    reason: str,
) -> dict | None:
    from authentication.models import ChildProfile
    from conversation.models import Session
    from gamification.services import ENGAGEMENT_DELTAS, award_points

    delta = ENGAGEMENT_DELTAS.get(quality)
    if delta is None:
        return None
    try:
        child = ChildProfile.objects.get(pk=child_id)
        session = Session.objects.filter(pk=session_id).first()
        return award_points(
            child,
            delta,
            reason=reason,
            source='conversation',
            session=session,
        )
    except Exception:
        logger.exception(
            "record_engagement failed: child_id=%s session_id=%s", child_id, session_id
        )
        return None


@sync_to_async
def _get_child_quests(child_id: int) -> list[str]:
    from gamification.models import ChildQuestProgress

    rows = (
        ChildQuestProgress.objects
        .filter(child_id=child_id)
        .exclude(status='completed')
        .select_related('quest')
        .order_by('-id')[:10]
    )
    return [
        (
            f"- progress_id={p.id} | {p.quest.title} | type={p.quest.quest_type} "
            f"| status={p.status} | reward={p.quest.reward_points} pts "
            f"| {p.quest.description[:120]}"
        )
        for p in rows
    ]


@sync_to_async
def _complete_companion_quest(
    child_id: int,
    session_id: int,
    progress_id: int,
):
    """Returns a result dict on success, or an explanatory string for the LLM."""
    from conversation.models import Session
    from gamification.models import ChildQuestProgress
    from gamification.services import complete_quest_progress

    try:
        progress = ChildQuestProgress.objects.select_related('quest').get(
            pk=progress_id, child_id=child_id,
        )
    except ChildQuestProgress.DoesNotExist:
        return "Quest not found for this child; check list_my_quests."

    if progress.status == 'completed':
        return "That quest is already completed."
    if progress.quest.verification_method != 'companion':
        return (
            "This quest is not companion-verified "
            f"(it is {progress.quest.verification_method}-verified); "
            "encourage the child to complete it the right way instead."
        )

    session = Session.objects.filter(pk=session_id).first()
    result = complete_quest_progress(
        progress, verified_by='companion', session=session,
    )
    if result["points"] is None:
        return "That quest is already completed."
    return {
        "quest_title": progress.quest.title,
        "points": result["points"],
        "new_badges": [
            {"id": b.id, "name": b.name, "icon": b.icon, "category": b.category}
            for b in result["new_badges"]
        ],
    }
