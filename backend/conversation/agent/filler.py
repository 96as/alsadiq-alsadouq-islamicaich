"""
Notes Section for the file:
- Soft thinking sounds (task 08, "soft fillers"). While the child waits for a slow answer the
  companion can make a quiet "hmm" so the pause feels like a friend thinking instead of a dead
  line. The sound is played through livekit's BackgroundAudioPlayer (a second, quiet audio
  track in the room) and is NOT part of the spoken reply: it is never sent to the TTS, never
  saved in the chat or the database, and never counted in the ElevenLabs character budget.

- Switches (environment):
    FILLER_MODE         off | hum   (default hum)
    FILLER_PROBABILITY  0.0 to 1.0  (default 0.5; the chance a slow turn gets a hum)
    FILLER_DELAY_S      seconds     (default 0.25; wait this long in "thinking" first, so a fast
                                     reply never gets a hum in front of it)
    FILLER_VOLUME       0.0 to 1.0  (default 0.8)
  An unknown FILLER_MODE is treated as off (quiet is the safe side for children).
  TODO (content team's call): a "spoken" mode ("let me think...") would be real words from the
  TTS. Words change what the child hears from the companion, so it is NOT built here. Until the
  content team decides, FILLER_MODE=spoken logs one warning and behaves as off.

- When it plays. Only for a turn the CHILD SPOKE (the user state went to "speaking" and the
  agent starts thinking within a few seconds of it). That one rule keeps it out of:
    * the greeting (nobody spoke yet),
    * typed messages (no speech),
    * the pause while a tool runs (agent state goes speaking to thinking: not a new turn).
  It only runs with the ElevenLabs voice (not xAI, not text-only) and never twice in a row with
  the same clip.

- When it stops. As soon as the reply starts (agent state "speaking"), when the child speaks
  again (an interruption), or when the agent goes back to listening or idle. The clips are
  shorter than 0.8 s and fade out.
  livekit's PlayHandle.stop() alone is NOT enough: the 1.5.1 BackgroundAudioPlayer keeps
  400 ms of mixed audio queued in its track (_AUDIO_SOURCE_BUFFER_MS) plus a mixer block or
  two, so a stopped clip would play on for most of its length, over the reply or the child.
  _HardStopHandle also drops that queue (now and twice more within 0.15 s, to catch the
  blocks the mixer hands on after the first drop). This player only ever plays hums, so
  dropping its queue never cuts anything else. A cut hum may click softly; it is quiet and
  is masked by the voice that caused the stop.

- KIDS RULE kept: nothing here changes the end-of-turn wait (Silero 0.55 s) or interruptions.

- Never fatal. Every handler swallows its own errors; if the player cannot start (missing
  clips, old livekit) the session simply has no hum.

- The clips live in agent/assets/fillers (see the README there for how they were made).
"""
from __future__ import annotations

import asyncio
import logging
import os
import random
import time
from pathlib import Path
from typing import Callable, NamedTuple

logger = logging.getLogger(__name__)

MODE_OFF = "off"
MODE_HUM = "hum"
_KNOWN_MODES = (MODE_OFF, MODE_HUM)

DEFAULT_MODE = MODE_HUM
DEFAULT_PROBABILITY = 0.5
DEFAULT_DELAY_S = 0.25
DEFAULT_VOLUME = 0.8

# The agent must start thinking within this long after the child's speech ends for the turn to
# count as a spoken one (guards against a stale "the child spoke" flag).
VOICE_TURN_WINDOW_S = 5.0

CLIPS_DIR = Path(__file__).resolve().parent / "assets" / "fillers"
CLIP_SUFFIXES = (".ogg", ".mp3")


class FillerSettings(NamedTuple):
    mode: str
    probability: float
    delay_s: float
    volume: float


def _float_env(name: str, default: float, low: float, high: float | None = None) -> float:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        value = float(raw)
    except ValueError:
        logger.warning("%s is not a number: using %s.", name, default)
        return default
    if value != value:  # NaN
        return default
    value = max(low, value)
    return min(high, value) if high is not None else value


def load_filler_settings() -> FillerSettings:
    raw = (os.getenv("FILLER_MODE") or DEFAULT_MODE).strip().lower() or DEFAULT_MODE
    if raw == "spoken":
        # TODO(content team): spoken fillers are real words in the companion's voice.
        logger.warning("FILLER_MODE=spoken is not built (content team's call): no filler.")
        mode = MODE_OFF
    elif raw not in _KNOWN_MODES:
        logger.warning("Unknown FILLER_MODE %r: no filler.", raw[:20])
        mode = MODE_OFF
    else:
        mode = raw
    return FillerSettings(
        mode=mode,
        probability=_float_env("FILLER_PROBABILITY", DEFAULT_PROBABILITY, 0.0, 1.0),
        delay_s=_float_env("FILLER_DELAY_S", DEFAULT_DELAY_S, 0.0, 5.0),
        volume=_float_env("FILLER_VOLUME", DEFAULT_VOLUME, 0.0, 1.0),
    )


def list_clips(directory: Path | str | None = None) -> list[str]:
    folder = Path(directory) if directory is not None else CLIPS_DIR
    if not folder.is_dir():
        return []
    return sorted(str(p) for p in folder.iterdir() if p.suffix.lower() in CLIP_SUFFIXES)


class FillerController:
    """Decides when to hum. `play(path)` must return a handle with stop()."""

    def __init__(
        self,
        play: Callable[[str], object],
        clips: list[str],
        *,
        probability: float = DEFAULT_PROBABILITY,
        delay_s: float = DEFAULT_DELAY_S,
        rng: random.Random | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._play = play
        self._clips = list(clips)
        self._probability = probability
        self._delay_s = delay_s
        self._rng = rng or random.Random()
        self._clock = clock
        self._child_speaking = False
        self._voice_turn = False
        self._voice_ended_at = 0.0
        self._thinking = False
        self._timer: asyncio.TimerHandle | None = None
        self._handle = None
        self._last_clip: str | None = None
        self.played = 0

    def attach(self, session) -> None:
        session.on("user_state_changed", self.on_user_state_changed)
        session.on("agent_state_changed", self.on_agent_state_changed)

    # -- events ------------------------------------------------------------------------

    def on_user_state_changed(self, event) -> None:
        try:
            new_state = getattr(event, "new_state", None)
            if new_state == "speaking":
                self._child_speaking = True
                self._voice_turn = True
                self._cancel()  # the child is talking: no hum over them
            else:
                if self._child_speaking:
                    self._voice_ended_at = self._clock()
                self._child_speaking = False
        except Exception:
            logger.debug("filler: user_state_changed failed", exc_info=True)

    def on_agent_state_changed(self, event) -> None:
        try:
            new_state = getattr(event, "new_state", None)
            old_state = getattr(event, "old_state", None)
            if new_state == "thinking":
                self._thinking = True
                if old_state == "speaking":
                    return  # tools running after a reply: not a new turn
                spoke = self._voice_turn and (
                    self._child_speaking or self._clock() - self._voice_ended_at <= VOICE_TURN_WINDOW_S
                )
                self._voice_turn = False
                if spoke:
                    self._schedule()
            else:
                self._thinking = False
                self._cancel()  # speaking, listening or idle: the wait is over
        except Exception:
            logger.debug("filler: agent_state_changed failed", exc_info=True)

    # -- playing -----------------------------------------------------------------------

    def _schedule(self) -> None:
        if not self._clips or self._rng.random() >= self._probability:
            return
        self._cancel()
        if self._delay_s <= 0:
            self._start()
            return
        self._timer = asyncio.get_running_loop().call_later(self._delay_s, self._start)

    def _start(self) -> None:
        self._timer = None
        if not self._thinking:
            return  # the reply already started
        try:
            choices = [c for c in self._clips if c != self._last_clip] or self._clips
            clip = self._rng.choice(choices)
            self._handle = self._play(clip)
            self._last_clip = clip
            self.played += 1
        except Exception:
            logger.debug("filler: could not play", exc_info=True)

    def _cancel(self) -> None:
        if self._timer is not None:
            self._timer.cancel()
            self._timer = None
        handle, self._handle = self._handle, None
        if handle is not None:
            try:
                handle.stop()
            except Exception:
                logger.debug("filler: could not stop", exc_info=True)

    def close(self) -> None:
        self._thinking = False
        self._cancel()


# After a stop the player's queue is dropped at once and again after these delays (seconds),
# to catch the mixer blocks that were already on their way to the track.
DROP_QUEUE_AGAIN_AFTER_S = (0.05, 0.15)


class _HumPlayer:
    """Plays hums on livekit's BackgroundAudioPlayer so that a stop is heard at once.

    See "When it stops" at the top. `audio_config` is livekit's AudioConfig.
    """

    def __init__(self, player, audio_config, volume: float) -> None:
        self._player = player
        self._audio_config = audio_config
        self._volume = volume
        self._plays = 0

    def play(self, path: str) -> "_HardStopHandle":
        handle = self._player.play(self._audio_config(path, volume=self._volume))
        self._plays += 1
        return _HardStopHandle(self, handle, self._plays)

    def drop_queue(self, play_number: int | None = None) -> None:
        """Drop the hum audio queued in the track. A late call never cuts a newer hum."""
        if play_number is not None and play_number != self._plays:
            return
        try:
            source = getattr(self._player, "_audio_source", None)
            clear = getattr(source, "clear_queue", None)
            if clear is not None:
                clear()
        except Exception:  # noqa: BLE001 - a hum that plays on is better than a broken session
            logger.debug("filler: could not drop the queued hum", exc_info=True)


class _HardStopHandle:
    def __init__(self, hums: _HumPlayer, handle, play_number: int) -> None:
        self._hums = hums
        self._handle = handle
        self._play_number = play_number

    def stop(self) -> None:
        try:
            self._handle.stop()
        finally:
            self._hums.drop_queue()
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None
            if loop is not None:
                for delay in DROP_QUEUE_AGAIN_AFTER_S:
                    loop.call_later(delay, self._hums.drop_queue, self._play_number)


async def start_filler(
    session,
    room,
    *,
    is_elevenlabs: bool,
    text_only: bool,
    settings: FillerSettings | None = None,
    clips_dir: Path | str | None = None,
):
    """Start the hum for this session. Returns an async closer, or None when it does not apply.

    The livekit import is inside the function so this module loads without livekit.
    """
    if text_only or not is_elevenlabs:
        return None
    settings = settings or load_filler_settings()
    if settings.mode != MODE_HUM or settings.probability <= 0:
        return None
    clips = list_clips(clips_dir)
    if not clips:
        logger.warning("FILLER_MODE=hum but there are no clips in %s: no filler.", CLIPS_DIR.name)
        return None
    try:
        from livekit.agents import AudioConfig, BackgroundAudioPlayer

        player = BackgroundAudioPlayer()
        await player.start(room=room)
    except Exception as exc:  # noqa: BLE001 - a missing hum must never break a session
        logger.warning("Filler sound not started (%s): the session carries on without it.",
                       type(exc).__name__)
        return None

    hums = _HumPlayer(player, AudioConfig, settings.volume)
    controller = FillerController(
        hums.play,
        clips,
        probability=settings.probability,
        delay_s=settings.delay_s,
    )
    controller.attach(session)

    async def close() -> None:
        controller.close()
        try:
            await player.aclose()
        except Exception:  # noqa: BLE001
            logger.debug("filler: player close failed", exc_info=True)

    return close


# The event loop keeps only a weak reference to a task: hold the running starters here.
_running: set[asyncio.Task] = set()


def start_filler_in_background(session, room, **kwargs) -> asyncio.Task | None:
    """Start the hum without holding up the greeting (publishing the track takes a moment).

    The hum never plays before the child has spoken, so starting a little late costs nothing.
    The player is closed when the session closes.
    """
    async def _run() -> None:
        close = await start_filler(session, room, **kwargs)
        if close is None:
            return
        session.on("close", lambda _event=None: asyncio.get_running_loop().create_task(close()))

    task = asyncio.get_running_loop().create_task(_run(), name="filler-start")
    _running.add(task)
    task.add_done_callback(_running.discard)
    return task


__all__ = [
    "FillerController",
    "FillerSettings",
    "load_filler_settings",
    "list_clips",
    "start_filler",
    "start_filler_in_background",
]
