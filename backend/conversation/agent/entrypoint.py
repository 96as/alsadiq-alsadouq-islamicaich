"""
Notes Section for the file:
- LiveKit agent entrypoint worker job: join room, run AgentSession, persist messages.

- TTS: built by tts_factory.build_tts. TTS_PROVIDER=elevenlabs (default, ELEVEN_API_KEY)
or xai (an explicit operator rollback, never chosen automatically). The xAI client speaks
the WebSocket protocol documented at
https://docs.x.ai/developers/model-capabilities/audio/text-to-speech#streaming-tts-websocket
(Not livekit-plugins-xai — it uses a legacy text_chunk wire format that no longer returns audio.)

- STT: OpenAI by default; STT_PROVIDER=scribe switches to ElevenLabs Scribe (stt_factory).
- LLM: OpenAI. Auth: OPENAI_API_KEY, ELEVEN_API_KEY, XAI_API_KEY (only if TTS_PROVIDER=xai).

- NO FALLBACK VOICE (lead's rule). If ElevenLabs cannot be used, the factories raise
  VoiceConfigurationError. The entrypoint then publishes one "voice_error" data message to the
  room (topic below, code only, no key) and ends the job, so the child's app can say the voice
  is unavailable. The same happens if ElevenLabs rejects the key, voice or plan during the
  session (the session "error" event): ONE error log with the cause, then the same message.
  Nothing quietly speaks with another voice.

- DEMO GUARDS (conversation/demo_guards.py; the agent half is agent/demo_limits.py). The
  backend decides at session start how the session talks (eleven | xai | text | off) and
  stores it in Redis; the agent reads that decision here. "text" builds a session with no
  TTS, no STT and no VAD (chat only). "off" ends the job with a voice_error. "xai" can only
  come from an operator (VOICE_MODE=xai or TTS_PROVIDER=xai). A clock
  (DEMO_SESSION_MAX_SECONDS) says a short goodbye and closes the room, and the characters
  sent to ElevenLabs are counted per day. Nothing here ever chooses another voice by itself.

- Speech text: the session's tts_text_transforms runs tts_text.speech_tts_text_transform
(digits to words, markdown/emoji, honorifics, Quran-bracket and scripture-mark guards:
verses are never spoken), then AlSadiqAgent.tts_node adds the attribution guard. Aligned
transcripts stay OFF so the chat and the DB keep the LLM's wording (digits, honorific);
the same compliance guards are applied to it in AlSadiqAgent.transcription_node (see
_USE_TTS_ALIGNED_TRANSCRIPT below).

- Latency: silero VAD is loaded once per process in ``prewarm`` (not per job),
  per-child DB context is fetched concurrently, and ``preemptive_generation``
  starts LLM/TTS work while the end of the child's turn is still being
  confirmed.
"""
import asyncio
import json
import logging
import os

from asgiref.sync import sync_to_async
from livekit.agents import AgentSession, JobContext, JobProcess, room_io
from livekit.plugins import openai, silero

from conversation import demo_guards
from conversation.agent.agent_class import LEVEL_UP_NOTE, AlSadiqAgent
from conversation.agent.demo_limits import (
    SESSION_LIMIT_TOPIC,
    UsageCountingTransform,
    run_session_clock,
)
from conversation.agent import gesture_planner, lipsync_timeline, search_results
from conversation.agent.language_config import resolve_speech_languages
from conversation.agent.filler import start_filler_in_background
from conversation.agent.latency_log import attach_latency_logger
from conversation.agent.reasoning_effort import llm_effort_kwargs, resolve_reasoning_effort
from conversation.agent.speak_first import attach_speak_first
from conversation.agent.retrieval import build_value_index
from conversation.agent.stt_factory import build_stt
from conversation.agent.stt_models import DEFAULT_STT_MODEL, resolve_stt_model
from conversation.agent.transcript_persistence import (
    _persist_conversation_item,
    _save_message,
)
from conversation.agent.tts_factory import (
    PROVIDER_ELEVENLABS,
    PROVIDER_XAI,
    VoiceConfigurationError,
    build_tts,
    explain_tts_failure,
)
from conversation.agent.tts_text import speech_tts_text_transform
from conversation.agent.tts_warmup import start_tts_warmup
from conversation.agent.turn_pipeline import age_band_from_birth_year, annotate_linked_types, cap_typed_text

logger = logging.getLogger(__name__)

# Data-channel topic the child's app listens on to learn the voice is unavailable.
VOICE_ERROR_TOPIC = "voice_error"

# xAI voice and the other TTS settings are read inside tts_factory (XAI_TTS_VOICE, ...).
# They are used only when the operator sets TTS_PROVIDER=xai.
# Required on the xAI WS endpoint: BCP-47 (e.g. en) or auto.
_XAI_TTS_LANGUAGE = os.getenv("XAI_TTS_LANGUAGE", "auto").strip() or "auto"

# Language for the STT
_STT_LANGUAGE = os.getenv("STT_LANGUAGE", "en").strip() or "en"

# Arabic locale for xAI TTS when child selects Arabic (only with TTS_PROVIDER=xai)
_ARABIC_TTS_LOCALE = os.getenv("ARABIC_TTS_LOCALE", "ar-SA").strip() or "ar-SA"

# One fast model pair, the same default in this file, .env.example and
# .env.production.example (test_model_defaults.py keeps them equal).
#
# Conversation LLM. To A/B another model set LLM_MODEL only (candidates on the team key:
# gpt-5.4-mini, gpt-5.6-luna, gpt-6-luna; gpt-5.2 is the slow reference), restart the agent and
# compare the turn_latency lines (they carry the model and the reasoning effort). Older chat
# models (gpt-4.x) are out by the lead's rule. How long the model thinks before its first word
# is REASONING_EFFORT, see reasoning_effort.py (default: the lowest the model accepts).
DEFAULT_LLM_MODEL = "gpt-5.4-mini"
_LLM_MODEL = os.getenv("LLM_MODEL", DEFAULT_LLM_MODEL).strip() or DEFAULT_LLM_MODEL

# STT model: gpt-4o-mini-transcribe is the fast default. gpt-4o-transcribe is more accurate but
# slower and gpt-transcribe is a fair A/B; set STT_MODEL to switch. gpt-live-transcribe and
# gpt-realtime-whisper are refused (the 1.5.1 plugin cannot run them), see stt_models.py.
_STT_MODEL = resolve_stt_model(os.getenv("STT_MODEL"), default=DEFAULT_STT_MODEL)

# Realtime STT: transcribe over a websocket WHILE the child is speaking, so the
# transcript is ready the instant the turn ends (vs. uploading buffered audio
# after end-of-speech). Disable with STT_REALTIME=0 if the WS connection is flaky.
_STT_REALTIME = os.getenv("STT_REALTIME", "1").strip() != "0"

# Transcript source. False = the chat and the saved transcript are the LLM's text (digits
# stay digits, the honorific stays written), passed through the same compliance guards as
# the speech in AlSadiqAgent.transcription_node; only the speech is spelled out by the
# cleaner. True = the transcript is rebuilt from the TTS's word
# timings, which are made from the cleaned TTS text (numbers as words, the neutral phrase
# where a Quran bracket was). Cost of False: captions are paced by livekit's estimate of
# the speaking rate instead of exact word times. Details in tts_text.py.
_USE_TTS_ALIGNED_TRANSCRIPT = False

# Turn endpointing: how long of a pause confirms the child finished speaking.
_MIN_ENDPOINTING_DELAY = float(os.getenv("AGENT_MIN_ENDPOINTING_DELAY", "0.4"))
_MAX_ENDPOINTING_DELAY = float(os.getenv("AGENT_MAX_ENDPOINTING_DELAY", "3.0"))

_GREETING_INSTRUCTIONS = {
    "ar": (
        "ابدأ كصديق حقيقي. أنت من يبدأ التحية لأن الطفل لم يقل شيئًا بعد: "
        "أول كلمات تنطقها «السلام عليكم» حرفيًا (تحية المبتدئ، لا صيغة الرد)، "
        "ثم جملة قصيرة واحدة؛ جملتان كحد أقصى. "
        "إذا كنت تتذكر شيئًا من آخر لقاء — اختبار، صديق، قطة، حدث — اسأل عنه بشكل طبيعي "
        "بدلًا من سؤال عام. لا تعرض قائمة مواضيع أبدًا ولا تسأل ماذا تريد أن نتحدث اليوم."
    ),
    "en": (
        "Open like a real friend: say 'Assalamu alaikum' in English letters (never in Arabic "
        "script) plus one short sentence, two sentences max. "
        "Speak English (only the salam is Arabic words, in English letters): your memory notes may be "
        "written in Arabic, so say anything you remember in English. "
        "If you remember something from last time — a test, a friend, their cat, an event — "
        "ask about that naturally instead of a generic question. Never list topic options "
        "and never ask 'what do you want to talk about today'."
    ),
}


# Added to the greeting on the first meeting (no memory yet): AI disclosure.
_FIRST_MEETING_AI_LINE = {
    "ar": " وفي جملة قصيرة واحدة قل إنك الصديق، ذكاء اصطناعي ولست إنسانًا.",
    "en": " Also, in one short sentence, say you are Al-Sadiq, an AI friend, not a person.",
}


def prewarm(proc: JobProcess):
    """Load heavyweight resources once per worker process, not per session."""
    proc.userdata["vad"] = silero.VAD.load()


@sync_to_async
def _get_session(room_name):
    from conversation.models import Session
    return Session.objects.select_related('child').get(
        livekit_room_name=room_name, status='active',
    )


@sync_to_async
def _get_child_session_memory_text(child_id):
    from reporting.models import ChildSessionMemory
    try:
        mem = ChildSessionMemory.objects.get(child_id=child_id)
        return (mem.rolling_summary or "").strip()
    except ChildSessionMemory.DoesNotExist:
        return ""


@sync_to_async
def _get_value_index():
    # Servable knowledge-bank items + value keywords, snapshotted once per session.
    try:
        index = build_value_index()
    except Exception:
        logger.exception("Could not build the value index; running without sources")
        return None
    try:
        annotate_linked_types(index)
    except Exception:
        logger.exception("Could not read item links; excerpts license only their own citations")
    return index


@sync_to_async
def _get_active_quests_text(child_id):
    from gamification.models import ChildQuestProgress

    rows = (
        ChildQuestProgress.objects
        .filter(child_id=child_id)
        .exclude(status='completed')
        .select_related('quest')
        .order_by('-id')[:10]
    )
    return "\n".join(
        (
            f"- progress_id={p.id} | {p.quest.title} | type={p.quest.quest_type} "
            f"| status={p.status} | reward={p.quest.reward_points} pts "
            f"| {p.quest.description[:120]}"
        )
        for p in rows
    )


async def _publish_voice_error(room, code: str, provider: str) -> None:
    """Best-effort: tell the child's app the voice is unavailable. Code only, never a key."""
    try:
        await room.local_participant.publish_data(
            json.dumps({"type": "voice_unavailable", "provider": provider, "code": code}).encode(),
            reliable=True,
            topic=VOICE_ERROR_TOPIC,
        )
    except Exception:
        logger.exception("Failed to publish the voice_error message to the room")


def _remaining_seconds(db_session, max_seconds: int) -> float:
    """Time left until the demo limit, counted from when the session was created."""
    from django.utils import timezone

    started = getattr(db_session, "started_at", None)
    elapsed = (timezone.now() - started).total_seconds() if started else 0.0
    return max(0.0, max_seconds - max(0.0, elapsed))


DEV_SEARCH_TOPIC = "al.dev.search"


def _wire_dev_search(room, agent) -> None:
    """Dev/demo only (SEARCH_DEV_SIM=1): there is no web tool yet, so the avatar's web page is fed from the
    kid-safe FIXTURES in search_results.py. The browser's dev panel sends {"q": "..."} on the data topic
    al.dev.search and the agent runs web_search(q), exactly as a real web tool would. No network, no key."""
    publisher = search_results.SearchPublisher(
        room, lang=lambda: agent.language, safety_flagged=agent.safety_flagged_this_turn
    )
    agent.set_search(publisher, search_results.DevSearchProvider(delay_s=0.9))
    tasks: set = set()

    def on_data(packet) -> None:
        try:
            if getattr(packet, "topic", None) != DEV_SEARCH_TOPIC:
                return
            query = str(json.loads(bytes(packet.data).decode("utf-8")).get("q", ""))[:200]
            if not query.strip():
                return
            task = asyncio.ensure_future(agent.web_search(query))
            tasks.add(task)
            task.add_done_callback(tasks.discard)
        except Exception:
            logger.warning("dev search: could not read the request.", exc_info=True)

    room.on("data_received", on_data)
    logger.warning("SEARCH_DEV_SIM is on: the avatar's web page shows FIXTURES, not real search results.")


async def entrypoint(ctx: JobContext):
    await ctx.connect()

    # Which reasoning effort the LLM accepts: from a table for the tested models (no request),
    # else one tiny request while the database reads below run. Awaited where the LLM is
    # built; never raises. See reasoning_effort.py.
    effort_task = asyncio.get_running_loop().create_task(resolve_reasoning_effort(_LLM_MODEL))

    room_name = ctx.room.name

    try:
        db_session = await _get_session(room_name)
    except Exception:
        logger.error("No active session for room: %s", room_name)
        return

    logger.info(
        "Agent joining session_id=%s, room=%s",
        db_session.id, room_name,
    )

    # Independent context lookups — run concurrently to shave join latency.
    memory_text, value_index, active_quests_text = await asyncio.gather(
        _get_child_session_memory_text(db_session.child_id),
        _get_value_index(),
        _get_active_quests_text(db_session.child_id),
    )
    resolved_stt_language, resolved_tts_language = resolve_speech_languages(
        db_session.child.language_preference,
        default_stt_language=_STT_LANGUAGE,
        default_tts_language=_XAI_TTS_LANGUAGE,
        arabic_tts_locale=_ARABIC_TTS_LOCALE,
    )

    child_lang = db_session.child.language_preference or "en"
    # Value names from the knowledge bank: the STT keyterms.
    available_themes = value_index.value_names(child_lang) if value_index else None

    # How does this session talk? The backend decided at session start (kill switch, daily
    # ElevenLabs budget) and stored it. Without that record (a session made outside the
    # guarded API) decide the same way here. xAI can only come from an operator's choice.
    state = await asyncio.to_thread(demo_guards.load_session_state, db_session.id)
    if state is None:
        decision = await asyncio.to_thread(demo_guards.resolve_voice)
        voice_mode = decision.mode
        max_seconds = demo_guards.config().session_max_seconds
    else:
        voice_mode = state["mode"]
        max_seconds = int(state.get("max_seconds") or 0)
    logger.info(
        "Voice mode for session_id=%s: %s (time limit %s)",
        db_session.id, voice_mode, f"{max_seconds}s" if max_seconds else "none",
    )

    if voice_mode == demo_guards.MODE_OFF:
        logger.error(
            "Voice unavailable (voice_off): the operator switched the voice off "
            "(VOICE_MODE=off). session_id=%s", db_session.id,
        )
        await _publish_voice_error(ctx.room, "voice_off", "none")
        ctx.shutdown(reason="voice unavailable: voice_off")
        return

    if max_seconds and _remaining_seconds(db_session, max_seconds) <= 0:
        # The session's time is already up (a rejoin with the old token, or a job dispatched
        # again after the limit). Close without greeting: nothing is spoken or billed.
        logger.info("Session %s is past its %ss limit: closing the room without a reply",
                    db_session.id, max_seconds)
        try:
            await ctx.room.local_participant.publish_data(
                json.dumps({"type": "session_ended"}).encode(), reliable=True,
                topic=SESSION_LIMIT_TOPIC,
            )
        except Exception:
            logger.exception("Could not publish the session_ended notice")
        try:
            await ctx.delete_room()
        except Exception:
            logger.exception("Could not delete the room of an expired session")
        ctx.shutdown(reason="demo session time limit")
        return

    text_only = voice_mode == demo_guards.MODE_TEXT
    provider = PROVIDER_XAI if voice_mode == demo_guards.MODE_XAI else PROVIDER_ELEVENLABS

    # Build the voice first. ElevenLabs is the only voice: if it cannot be used the factory
    # has already logged one error naming the cause, and the session ends here, visibly,
    # instead of speaking with another voice. Text-only sessions need no STT, TTS or VAD.
    stt = tts = vad = None
    # LIPSYNC_TIMELINE=1: ask ElevenLabs for character timings and forward them to the avatar.
    # Only ElevenLabs gives them, and a text-only session has no voice.
    lipsync_on = (
        lipsync_timeline.enabled() and not text_only and provider == PROVIDER_ELEVENLABS
    )
    if lipsync_on:
        lipsync_on = lipsync_timeline.install_char_timing_patch()
    if not text_only:
        try:
            stt = build_stt(
                resolved_stt_language,
                openai_factory=lambda: openai.STT(
                    model=_STT_MODEL,
                    detect_language=False,
                    language=resolved_stt_language,
                    use_realtime=_STT_REALTIME,
                ),
                theme_names=available_themes,
            )
            tts = build_tts(
                resolved_stt_language,
                xai_language=resolved_tts_language,
                aligned_transcript=_USE_TTS_ALIGNED_TRANSCRIPT,
                provider=provider,
                lipsync_alignment=lipsync_on,
            )
        except VoiceConfigurationError as exc:
            await _publish_voice_error(ctx.room, exc.code, provider)
            ctx.shutdown(reason=f"voice unavailable: {exc.code}")
            return

        vad = ctx.proc.userdata.get("vad") if ctx.proc.userdata else None
        if vad is None:
            vad = silero.VAD.load()

    # Warm-up: open the ElevenLabs websocket now, in the background, as soon as the voice is
    # built, so the greeting does not pay the connection set-up and the socket opens while the
    # rest of the start-up runs. Not for xAI (a manual operator choice) and not for text-only.
    # The task ends by itself (it has a timeout) and never raises, so it needs no cleanup.
    start_tts_warmup(tts, is_elevenlabs=provider == PROVIDER_ELEVENLABS)

    agent = AlSadiqAgent(
        db_session_id=db_session.id,
        child_id=db_session.child_id,
        session_memory=memory_text or None,
        language=child_lang,
        active_quests_text=active_quests_text or None,
        age_band=age_band_from_birth_year(db_session.child.birth_year),
        value_index=value_index,
    )
    agent.set_room(ctx.room)
    lipsync = None
    if lipsync_on:
        lipsync = lipsync_timeline.LipsyncTimeline(ctx.room, lang=lambda: agent.language)
        agent.set_lipsync(lipsync)
        if gesture_planner.enabled():  # GESTURE_EVENTS, default: on
            try:
                planner = gesture_planner.GesturePlanner(
                    lang=lambda: agent.language, speech_id=lipsync.current_speech_id
                )
                if planner.available:
                    agent.set_gestures(planner)
            except Exception:  # the avatar's gestures must never stop a session from starting
                logger.warning("gesture planner could not start; no gesture events.", exc_info=True)

    if search_results.dev_enabled():  # SEARCH_DEV_SIM=1: fixtures for the avatar's web page, never a real search
        try:
            _wire_dev_search(ctx.room, agent)
        except Exception:
            logger.warning("dev search fixtures could not start.", exc_info=True)

    # Replaces the default ["filter_markdown", "filter_emoji"]; the cleaner does both.
    # One transform per session; the language is read live from the agent (speech_language: the
    # session language, or the turn's reply language with REPLY_LANGUAGE_FOLLOWS_CHILD on). With ElevenLabs
    # the same transform also counts the characters sent to it (the daily budget).
    speech_transform = speech_tts_text_transform(lambda: agent.speech_language)
    if voice_mode == demo_guards.MODE_ELEVEN:
        speech_transform = UsageCountingTransform(speech_transform)

    try:
        reasoning_effort = await effort_task
    except Exception:  # noqa: BLE001 - the effort is an optimisation, never a reason to fail
        logger.exception("Reasoning effort check failed: sending none")
        reasoning_effort = None

    agent_session = AgentSession(
        vad=vad,
        stt=stt,
        tts=tts,
        llm=openai.LLM(model=_LLM_MODEL, **llm_effort_kwargs(reasoning_effort)),
        tts_text_transforms=[speech_transform],
        use_tts_aligned_transcript=_USE_TTS_ALIGNED_TRANSCRIPT,
        preemptive_generation=True,
        min_endpointing_delay=_MIN_ENDPOINTING_DELAY,
        max_endpointing_delay=_MAX_ENDPOINTING_DELAY,
    )

    agent.signals.attach(agent_session)  # avatar signals: child mood + agent state events
    # One structured "turn_latency {json}" line per exchange: timings, language and tool names
    # only (no transcript, no child data). LATENCY_LOG=1/0 forces it; unset follows DEBUG.
    attach_latency_logger(
        agent_session,
        language=lambda: agent.language,
        fallback_count=lambda: agent.llm_fallback_count,
        session_id=db_session.id,
        llm_model=_LLM_MODEL,
        stt_model=_STT_MODEL if not text_only else None,
        prompt_profile="hybrid",  # one prompt now; the field stays so old logs line up
        reasoning_effort=reasoning_effort,
    )

    # Speak first: a turn whose only tool is record_engagement, called after the words, does
    # not get a second LLM round (see speak_first.py).
    attach_speak_first(agent_session, level_up_note=LEVEL_UP_NOTE)

    seen_conversation_item_ids: set[str] = set()
    skipped_child_text_contents: set[str] = set()

    def _on_conversation_item_added(event):
        asyncio.get_running_loop().create_task(
            _persist_conversation_item(
                db_session,
                agent,
                event.item,
                seen_conversation_item_ids,
                skipped_child_text_contents,
            )
        )

    agent_session.on("conversation_item_added", _on_conversation_item_added)
    if lipsync is not None:
        agent_session.on(
            "agent_state_changed", lambda event: lipsync.on_agent_state(event, agent_session)
        )
        ctx.add_shutdown_callback(lipsync.aclose)

    voice_failure = {"logged": False, "ended": False}

    def _on_session_error(event):
        # The ElevenLabs API can still reject the key, voice or plan after the session started
        # (the plugin only finds out when it connects). Name the cause once and tell the
        # child's app. There is deliberately no other voice to switch to.
        error = getattr(event, "error", None)
        if getattr(error, "type", None) != "tts_error":
            return
        if provider == PROVIDER_ELEVENLABS:
            code, cause = explain_tts_failure(getattr(error, "error", None))
        else:
            code, cause = "failed", "The xAI voice (chosen by the operator) failed."
        if not voice_failure["logged"]:
            voice_failure["logged"] = True
            logger.error(
                "Voice unavailable (%s): %s No fallback voice is used. session_id=%s",
                code, cause, db_session.id,
            )
        if getattr(error, "recoverable", False) or voice_failure["ended"]:
            return  # livekit is still retrying; report only if it gives up
        voice_failure["ended"] = True
        asyncio.get_running_loop().create_task(_end_session_without_voice(code, provider))

    async def _end_session_without_voice(code: str, provider: str):
        await _publish_voice_error(ctx.room, code, provider)
        ctx.shutdown(reason=f"voice unavailable: {code}")

    agent_session.on("error", _on_session_error)

    # Set when the time-limit goodbye starts: no new turns after it (see _begin_goodbye).
    closing = {"on": False}

    def _on_text_input(session, event):
        async def _persist_and_track():
            saved_msg = await _save_message(db_session, 'child', cap_typed_text(event.text), 'text')
            agent._last_child_message_id = saved_msg.id
            logger.info("Saved child text message: session_id=%s, msg_id=%s", db_session.id, saved_msg.id)

        text = cap_typed_text(event.text).strip()  # what the model and the database get
        if text:
            skipped_child_text_contents.add(text)
        asyncio.get_running_loop().create_task(_persist_and_track())
        agent.signals.on_child_text(event.text, new_turn=True)
        if closing["on"]:
            # The goodbye is playing and cannot be interrupted; the room closes right after.
            return
        session.interrupt()
        # generate_reply(user_input=) skips on_user_turn_completed in 1.5.1, so the
        # typed path runs the same turn guard through the agent.
        agent.reply_to_typed(session, event.text)

    room_options = {
        "text_input": room_io.TextInputOptions(text_input_cb=_on_text_input),
    }
    if text_only:
        # Chat only: the microphone is not listened to and nothing is spoken.
        room_options.update(audio_input=False, audio_output=False)

    await agent_session.start(
        room=ctx.room,
        agent=agent,
        room_options=room_io.RoomOptions(**room_options),
    )
    agent.signals.start()

    # Soft "hmm" while a slow answer is on its way (FILLER_MODE=off|hum, see filler.py). Started
    # in the background so the greeting is not held up; only for the ElevenLabs voice and never
    # before the child has spoken, so never during the greeting or for typed messages.
    start_filler_in_background(
        agent_session,
        ctx.room,
        is_elevenlabs=provider == PROVIDER_ELEVENLABS,
        text_only=text_only,
    )

    if max_seconds:
        guard_cfg = demo_guards.config()

        async def _publish_limit(payload: dict) -> None:
            await ctx.room.local_participant.publish_data(
                json.dumps(payload).encode(), reliable=True, topic=SESSION_LIMIT_TOPIC,
            )

        def _begin_goodbye() -> None:
            # Stop taking turns: a child's line said now would only get a reply that the
            # close cuts off (and that is billed). A reply already playing still finishes:
            # the clock waits for it (current_speech) before the goodbye.
            closing["on"] = True
            if not text_only:
                agent_session.input.set_audio_enabled(False)
                agent_session.clear_user_turn()

        async def _close_room() -> None:
            try:
                # Drop anything still queued behind the goodbye before the room goes away.
                agent_session.interrupt(force=True)
            except Exception:
                logger.exception("Could not clear queued speech at the session time limit")
            try:
                await ctx.delete_room()
            except Exception:
                logger.exception("Could not delete the room at the session time limit")
            ctx.shutdown(reason="demo session time limit")

        clock = asyncio.get_running_loop().create_task(run_session_clock(
            remaining_seconds=_remaining_seconds(db_session, max_seconds),
            lead_seconds=guard_cfg.goodbye_lead_seconds,
            grace_seconds=guard_cfg.hard_grace_seconds,
            language=lambda: agent.speech_language,   # the session language (the reply language, flag on)
            say=lambda text: agent_session.say(text, allow_interruptions=False),
            publish=_publish_limit,
            close_room=_close_room,
            before_goodbye=_begin_goodbye,
            current_speech=lambda: agent_session.current_speech,
            cut_speech=lambda: agent_session.interrupt(force=True),
        ))

        async def _stop_clock() -> None:
            clock.cancel()

        ctx.add_shutdown_callback(_stop_clock)

    greeting = _GREETING_INSTRUCTIONS.get(child_lang, _GREETING_INSTRUCTIONS["en"])
    if not memory_text:
        greeting += _FIRST_MEETING_AI_LINE.get(child_lang, _FIRST_MEETING_AI_LINE["en"])
    await agent_session.generate_reply(
        instructions=greeting,
        allow_interruptions=True,
    )
