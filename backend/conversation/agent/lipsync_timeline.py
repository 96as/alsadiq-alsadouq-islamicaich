"""Forwards the ElevenLabs per-character timings of what the agent says to the browser, so the
avatar's mouth can be timed by the text (frontend: avatar/lipsync/timelineSync.js). Off unless
LIPSYNC_TIMELINE=1.

How it works
- ElevenLabs returns, with the audio, the start time and duration of every character of the text it
  spoke. The livekit plugin (1.5.1) collapses them to words; install_char_timing_patch() wraps the
  collapse so each word also carries its characters (`char_ms`).
- AlSadiqAgent.tts_node passes every audio frame through LipsyncTimeline.tap(). The frames are
  yielded untouched. The timings riding on a frame are read first, put on a queue, and a sender task
  publishes them on the data topic `lk.lipsync`. Nothing is awaited on the audio path.
- LipsyncTimeline.on_agent_state() publishes `go` when the agent starts speaking and `stop` when that
  speech is cut off. The browser shows a timeline only after its `go`.

Times are ms from the first sample of the speech. One speech can need several tts_node calls (one per
text segment); each call is a new ElevenLabs context that counts from 0, so the audio already
produced for the speech is added as an offset.

Messages (JSON, UTF-8, topic lk.lipsync, reliable, at most 120 characters per packet):
  {"v":1,"sp":"<speech id>","seq":0,"lang":"ar","t":[["c",startMs,durMs],...]}
  {"v":1,"sp":"<speech id>","go":1}
  {"v":1,"sp":"<speech id>","stop":1}
Gesture events (optional, GESTURE_EVENTS, BEHAVIOUR-SPEC 3.2): a packet may also carry
  "g":[[ci,n,"id",k,"h"],...]   a gesture on the word whose first character is item ci (n items long)
  "u":[[ci,"talk_style","expression"],...]   a sentence starting at item ci
where ci is the speech-global item index (every `t` item of the speech counted from 0 in seq order). An
event rides in the packet that holds its anchor character. A clause planned after its words went out is
sent as {"v":1,"sp":"<speech id>","g":[...],"u":[...]}: it never carries `t` or `seq`, because the
browser's TimelineSync treats a message with `t` and no `seq` as a new timeline. Old browsers ignore g and u.
The text of the reply is in them (the browser already shows it). No key, no child data.

Nothing in here may break the voice: every failure is logged once and the frames keep flowing.
livekit is imported lazily, so this module imports without it.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from collections import OrderedDict

try:  # the word-anchoring helpers live with the planner; the timeline works without it
    from conversation.agent.gesture_planner import word_len as _word_len, word_norm as _word_norm
except Exception:  # pragma: no cover - only if the planner module is missing
    _word_len = _word_norm = None

logger = logging.getLogger(__name__)

TOPIC = "lk.lipsync"
USERDATA_KEY = "lk.timed_transcripts"  # livekit.agents.voice.generation.USERDATA_TIMED_TRANSCRIPT
MAX_ITEMS = 120
PLUGIN_VERSION = "1.5.1"
_OFF_VALUES = ("0", "off", "false", "no")
_QUEUE_MAX = 256
_SPEECHES_KEPT = 8

_logged: set[str] = set()


def _log_once(key: str, message: str, *args, exc: BaseException | None = None) -> None:
    if key in _logged:
        return
    _logged.add(key)
    logger.warning(message, *args, exc_info=exc)


def enabled() -> bool:
    """LIPSYNC_TIMELINE switches the whole feature; the default is ON (0/off/false/no turns it off)."""
    return os.environ.get("LIPSYNC_TIMELINE", "").strip().lower() not in _OFF_VALUES


# ---------------------------------------------------------------------------
# The plugin patch
# ---------------------------------------------------------------------------

_patched = False


def _attach_chars(words, text: str, start_times_ms, durations_ms) -> None:
    """Give each word (a TimedString) `char_ms`: [(char, start_ms, duration_ms), ...]."""
    if not words:
        return
    first = str(words[0])
    idx = text.find(first)
    if idx < 0 or idx > 3:
        return
    n_times = min(len(start_times_ms), len(durations_ms))
    for word in words:
        w = str(word)
        end = idx + len(w)
        if end > n_times or text[idx:end] != w:
            return  # the text and the timings do not line up: leave the rest without characters
        word.char_ms = [
            (text[i], int(start_times_ms[i]), int(durations_ms[i])) for i in range(idx, end)
        ]
        idx = end


def install_char_timing_patch() -> bool:
    """Make the ElevenLabs plugin's timed words carry their characters. Idempotent.

    Only plugin 1.5.1 is patched (the function it wraps is private); on any other version, or if the
    plugin cannot be imported, it logs once and returns False, and the lip sync stays audio-only.
    """
    global _patched
    if _patched:
        return True
    try:
        from livekit.plugins.elevenlabs import tts as eleven_tts
        from livekit.plugins.elevenlabs import version as eleven_version
    except Exception as exc:  # no plugin, or livekit cannot be imported here
        _log_once("patch-import", "lip sync timeline: ElevenLabs plugin not importable (%s).",
                  type(exc).__name__)
        return False
    found = getattr(eleven_version, "__version__", None)
    original = getattr(eleven_tts, "_to_timed_words", None)
    if found != PLUGIN_VERSION or not callable(original):
        _log_once(
            "patch-version",
            "lip sync timeline: livekit-plugins-elevenlabs %s is not %s, character timings are "
            "not forwarded.", found, PLUGIN_VERSION,
        )
        return False
    if getattr(original, "_lipsync_wrapped", False):
        _patched = True
        return True

    def _to_timed_words_with_chars(text, start_times_ms, durations_ms, flush=False):
        words, rest = original(text, start_times_ms, durations_ms, flush)
        try:
            _attach_chars(words, text, start_times_ms, durations_ms)
        except Exception as exc:
            _log_once("patch-attach", "lip sync timeline: could not read character timings.", exc=exc)
        return words, rest

    _to_timed_words_with_chars._lipsync_wrapped = True
    eleven_tts._to_timed_words = _to_timed_words_with_chars
    _patched = True
    return True


# ---------------------------------------------------------------------------
# The publisher
# ---------------------------------------------------------------------------


def _frame_ms(frame) -> float:
    duration = getattr(frame, "duration", None)
    if isinstance(duration, (int, float)):
        return float(duration) * 1000.0
    try:
        return 1000.0 * frame.samples_per_channel / frame.sample_rate
    except Exception:
        return 0.0


def _pack(message: dict) -> bytes:
    return json.dumps(message, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


class LipsyncTimeline:
    """Publishes the lip-sync timeline of the speech being played. See the module docstring."""

    def __init__(self, room, *, lang=None, speech_id=None):
        """room: the livekit room (local_participant.publish_data).
        lang: optional callable returning the session language ("ar", "en", "en-US"...).
        speech_id: optional callable returning the id of the speech being generated; the default
            reads livekit's own speech handle."""
        self._room = room
        self._lang = lang
        self._speech_id_fn = speech_id
        self._session = None
        self._speeches: OrderedDict[str, dict] = OrderedDict()
        self._queue: asyncio.Queue | None = None
        self._sender: asyncio.Task | None = None
        self._went: set[str] = set()

    # -- state per speech --------------------------------------------------

    def _speech(self, sp: str) -> dict:
        st = self._speeches.get(sp)
        if st is None:
            st = {"off": 0.0, "seq": 0, "n_items": 0}
            self._speeches[sp] = st
            while len(self._speeches) > _SPEECHES_KEPT:
                self._speeches.popitem(last=False)
        return st

    def _current_speech_id(self) -> str:
        try:
            if self._speech_id_fn is not None:
                value = self._speech_id_fn()
                if value:
                    return str(value)
            else:
                from livekit.agents.voice.agent_activity import _SpeechHandleContextVar

                handle = _SpeechHandleContextVar.get(None)
                if handle is not None:
                    return str(handle.id)
        except Exception:
            pass
        try:
            current = getattr(self._session, "current_speech", None)
            if current is not None:
                return str(current.id)
        except Exception:
            pass
        return "?"

    def _lang_code(self) -> str:
        try:
            value = self._lang() if self._lang else "ar"
        except Exception:
            value = "ar"
        return "en" if str(value or "").lower().startswith("en") else "ar"

    # -- the queue and the sender -----------------------------------------

    def _enqueue(self, message: dict) -> None:
        try:
            if self._queue is None:
                self._queue = asyncio.Queue(maxsize=_QUEUE_MAX)
            if self._sender is None or self._sender.done():
                self._sender = asyncio.get_running_loop().create_task(self._send_loop())
            self._queue.put_nowait(_pack(message))
        except asyncio.QueueFull:
            _log_once("queue-full", "lip sync timeline: send queue full, dropping a message.")
        except Exception as exc:
            _log_once("enqueue", "lip sync timeline: could not queue a message.", exc=exc)

    async def _send_loop(self) -> None:
        queue = self._queue
        while True:
            payload = await queue.get()
            try:
                await self._room.local_participant.publish_data(
                    payload, reliable=True, topic=TOPIC
                )
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                _log_once("publish", "lip sync timeline: publish_data failed.", exc=exc)
            finally:
                queue.task_done()

    async def flush(self) -> None:
        """Wait until everything queued has been published (tests, shutdown)."""
        if self._queue is not None:
            await self._queue.join()

    async def aclose(self) -> None:
        sender, self._sender = self._sender, None
        if sender is not None and not sender.done():
            sender.cancel()
            try:
                await sender
            except BaseException:
                pass

    # -- the audio path ----------------------------------------------------

    def current_speech_id(self) -> str:
        """The id of the speech being generated ("?" if unknown); also what the gesture planner keys on."""
        return self._current_speech_id()

    async def tap(self, frames, plan=None):
        """Yield `frames` unchanged and publish the character timings that ride on them.

        plan: optional gesture_planner.GestureSegment of this tts_node call. Its events are attached to
        the packets (g, u); a clause planned late goes out as a g-only message."""
        sp = "?"
        st = None
        base = 0.0
        played = 0.0
        seg = {"word_ix": 0, "plan": None}
        try:
            sp = self._current_speech_id()
            st = self._speech(sp)
            base = st["off"]
            if plan is not None and _word_norm is not None:
                seg["plan"] = plan
                plan.bind_sink(lambda g, u, sp=sp: self._enqueue_late(sp, g, u))
        except Exception as exc:
            _log_once("tap-start", "lip sync timeline: tap could not start.", exc=exc)
        try:
            async for frame in frames:
                try:
                    if st is not None:
                        self._publish_frame(sp, st, base, frame, seg)
                    played += _frame_ms(frame)
                except Exception as exc:
                    _log_once("tap-frame", "lip sync timeline: tap failed on a frame.", exc=exc)
                yield frame
        finally:
            if st is not None:
                st["off"] = base + played

    def _publish_frame(self, sp: str, st: dict, base: float, frame, seg: dict | None = None) -> None:
        userdata = getattr(frame, "userdata", None)
        if not userdata:
            return
        words = userdata.get(USERDATA_KEY)
        if not words:
            return
        plan = seg["plan"] if seg else None
        items = []
        events = []  # (position of the anchor item in `items`, g events, u events)
        for word in words:
            ix = None
            if seg is not None:
                ix = seg["word_ix"]  # counted even when the word has no characters
                seg["word_ix"] = ix + 1
            chars = getattr(word, "char_ms", None)
            if not chars:
                continue
            first = len(items)
            for ch, start, dur in chars:
                items.append([ch, int(round(base + start)), int(dur)])
            if plan is not None:
                try:
                    norm = _word_norm(word)
                    taken = plan.take(ix, norm)
                    n = _word_len(word, len(chars))
                    if taken is None:
                        plan.note_word(ix, norm, st["n_items"] + first, n)
                    else:
                        g, u = taken
                        events.append((first, [[e[0], e[1], e[2]] for e in g], [list(e) for e in u], n))
                except Exception as exc:
                    plan = None
                    _log_once("tap-plan", "lip sync timeline: gesture events failed, none are sent for "
                                          "this segment.", exc=exc)
        if not items:
            return
        lang = self._lang_code()
        total = st["n_items"]
        for i in range(0, len(items), MAX_ITEMS):
            message = {"v": 1, "sp": sp, "seq": st["seq"], "lang": lang, "t": items[i:i + MAX_ITEMS]}
            g_out, u_out = [], []
            for pos, g, u, n in events:
                if i <= pos < i + MAX_ITEMS:
                    ci = total + pos
                    g_out.extend([ci, n, e[0], e[1], e[2]] for e in g)
                    u_out.extend([ci, e[0], e[1]] for e in u)
            if g_out:
                message["g"] = g_out
            if u_out:
                message["u"] = u_out
            st["seq"] += 1
            self._enqueue(message)
        st["n_items"] = total + len(items)

    def _enqueue_late(self, sp: str, g: list, u: list) -> None:
        """A clause planned after its words were published: events only, never `t` and never `seq`."""
        message = {"v": 1, "sp": sp}
        if g:
            message["g"] = g
        if u:
            message["u"] = u
        if len(message) > 2:
            self._enqueue(message)

    # -- the agent state ---------------------------------------------------

    def on_agent_state(self, event, session=None) -> None:
        """Handler for AgentSession's "agent_state_changed". Never raises."""
        try:
            if session is not None:
                self._session = session
            if getattr(event, "new_state", None) != "speaking":
                return
            handle = getattr(self._session, "current_speech", None)
            if handle is None:
                return
            sp = str(handle.id)
            if sp in self._went:
                return
            self._went.add(sp)
            if len(self._went) > 64:
                self._went = {sp}
            self._enqueue({"v": 1, "sp": sp, "go": 1})

            def _done(h, sp=sp):
                try:
                    if getattr(h, "interrupted", False):
                        self._enqueue({"v": 1, "sp": sp, "stop": 1})
                except Exception as exc:
                    _log_once("stop", "lip sync timeline: could not send stop.", exc=exc)

            handle.add_done_callback(_done)
        except Exception as exc:
            _log_once("state", "lip sync timeline: agent state handler failed.", exc=exc)
