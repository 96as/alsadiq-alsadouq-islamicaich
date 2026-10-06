"""
Notes Section for the file:
- The agent's half of the demo guards (the backend half is conversation/demo_guards.py).

- run_session_clock: the session time limit. It waits until `lead` seconds before the limit,
  tells the room (data topic "session_limit") and stops taking new turns (before_goodbye).
  A reply that is already playing finishes first (up to lead + grace seconds; only a reply
  longer than that is cut). Then it says a short warm goodbye in the session language (fixed
  words, no scripture) with its own playout budget (GOODBYE_MAX_SECONDS), then closes the
  room. Worst case the room closes at limit + grace + GOODBYE_MAX_SECONDS. It works the same
  in text-only mode, where the goodbye is just a chat line.

- UsageCountingTransform: counts the characters that are sent to ElevenLabs, per day, in
  Redis (demo_guards.add_eleven_chars). It wraps the session's speech cleaner, so it counts
  the cleaned text that really reaches the TTS (numbers as words, no markdown, no verses).
  That makes it one transform, so the session still has exactly one tts_text_transform. It
  never changes the text.
  The Redis write runs in a worker thread, in batches (every FLUSH_CHARS characters and at the
  end of each segment), so a slow or dead Redis never stalls the audio event loop.
  Past ELEVEN_DAILY_CHAR_CAP, the backend starts NEW sessions as text-only; a session that is
  already running finishes (it is capped by the time limit). Nothing switches to xAI.

- Injection (callables passed in) keeps both pieces testable without livekit.
"""
from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterable, Awaitable, Callable

from conversation import demo_guards

logger = logging.getLogger(__name__)

# Data-channel topic the child's app can listen on to show a countdown or "time is up".
SESSION_LIMIT_TOPIC = "session_limit"


# The goodbye's own playout budget, counted from when it is said (it is about 7 s of speech).
GOODBYE_MAX_SECONDS = 12.0


async def _until_quiet(current_speech: Callable[[], object | None], poll: float = 0.1) -> None:
    """Return once nothing is playing (the reply in progress and anything queued behind it)."""
    while True:
        speech = current_speech()
        if speech is None or (callable(getattr(speech, "done", None)) and speech.done()):
            return
        await speech.wait_for_playout()
        await asyncio.sleep(poll)  # always yield, and let a queued speech become current


async def run_session_clock(
    *,
    remaining_seconds: float,
    lead_seconds: float,
    grace_seconds: float,
    language: Callable[[], str | None],
    say: Callable[[str], object],
    publish: Callable[[dict], Awaitable[None]],
    close_room: Callable[[], Awaitable[None]],
    before_goodbye: Callable[[], None] | None = None,
    current_speech: Callable[[], object | None] | None = None,
    cut_speech: Callable[[], object] | None = None,
    goodbye_seconds: float = GOODBYE_MAX_SECONDS,
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
) -> None:
    """Wait, say goodbye, close the room. Cancel it to stop the clock (session ended early).

    remaining_seconds: time left until the limit, counted from the session's start.
    say: starts the goodbye and returns something with ``wait_for_playout()`` (a livekit
        SpeechHandle), or None.
    publish: sends a small JSON message to the room (errors are the caller's to swallow).
    close_room: deletes the room and ends the job.
    before_goodbye: called once right before the goodbye, to stop taking new turns so no
        reply is queued behind the goodbye (it would only be cut off by the close).
    current_speech: the speech playing now (a SpeechHandle) or None. A reply that is playing
        finishes before the goodbye, for up to lead + grace seconds; after that cut_speech()
        stops it so the goodbye can still be heard.
    goodbye_seconds: the goodbye's own playout budget, so a long reply never eats it. Worst
        case the room closes at limit + grace + goodbye_seconds.
    """
    await sleep(max(0.0, remaining_seconds - lead_seconds))
    seconds_left = int(min(lead_seconds, max(0.0, remaining_seconds)))
    logger.info("Demo session time limit reached: saying goodbye, closing in ~%ss", seconds_left)
    try:
        await publish({"type": "session_ending", "seconds_left": seconds_left})
    except Exception:  # noqa: BLE001 - the goodbye matters more than the notice
        logger.exception("Could not publish the session_ending notice")
    if before_goodbye is not None:
        try:
            before_goodbye()
        except Exception:  # noqa: BLE001 - never skip the goodbye over this
            logger.exception("Could not stop taking new turns before the goodbye")
    if current_speech is not None:
        # 1. Never cut the reply that is playing mid-sentence, unless it runs far too long.
        try:
            await asyncio.wait_for(_until_quiet(current_speech),
                                   timeout=max(1.0, lead_seconds + grace_seconds))
        except asyncio.CancelledError:
            raise
        except asyncio.TimeoutError:
            logger.warning("A reply was still playing %ss after the goodbye time; cutting it so "
                           "the goodbye is heard", int(lead_seconds + grace_seconds))
            if cut_speech is not None:
                try:
                    cut_speech()
                except Exception:  # noqa: BLE001
                    logger.exception("Could not cut the long reply")
        except Exception:  # noqa: BLE001
            logger.exception("Could not wait for the reply in progress")
    try:
        # 2. The goodbye, with its own budget.
        handle = say(demo_guards.goodbye_for(language()))
        waiter = getattr(handle, "wait_for_playout", None)
        if waiter is not None:
            await asyncio.wait_for(waiter(), timeout=max(1.0, goodbye_seconds))
    except asyncio.CancelledError:
        raise
    except Exception:  # noqa: BLE001 - a failed or slow goodbye must not keep the room open
        logger.exception("The goodbye did not finish; closing the room anyway")
    try:
        await publish({"type": "session_ended"})
    except Exception:  # noqa: BLE001
        logger.exception("Could not publish the session_ended notice")
    await close_room()


class UsageCountingTransform:
    """Wrap a tts_text_transform: pass text through unchanged and count its characters.

    Counts are handed to a worker thread in batches (FLUSH_CHARS, and the rest when the
    segment ends or is cut short), so the Redis call never blocks the audio event loop.
    """

    FLUSH_CHARS = 200

    def __init__(self, inner: Callable[[AsyncIterable[str]], AsyncIterable[str]],
                 add_chars: Callable[[int], None] | None = None):
        self._inner = inner
        # Looked up on each call so the module's counter is the one that runs (and tests can
        # replace it).
        self._add_chars = add_chars or (lambda n: demo_guards.add_eleven_chars(n))
        self.total = 0  # characters counted in this session
        self._pending: set[asyncio.Future] = set()

    def __call__(self, text: AsyncIterable[str]) -> AsyncIterable[str]:
        return self._counted(self._inner(text))

    async def _counted(self, cleaned: AsyncIterable[str]) -> AsyncIterable[str]:
        unflushed = 0
        try:
            async for chunk in cleaned:
                if isinstance(chunk, str) and chunk:
                    self.total += len(chunk)
                    unflushed += len(chunk)
                    if unflushed >= self.FLUSH_CHARS:
                        self._flush(unflushed)
                        unflushed = 0
                yield chunk
        finally:
            # Also runs when the reply is interrupted: what already went to the TTS counts.
            if unflushed:
                self._flush(unflushed)

    def _flush(self, count: int) -> None:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:  # no loop (plain sync use): count inline
            self._safe_add(count)
            return
        future = loop.run_in_executor(None, self._safe_add, count)
        self._pending.add(future)
        future.add_done_callback(self._pending.discard)

    def _safe_add(self, count: int) -> None:
        try:
            self._add_chars(count)
        except Exception:  # noqa: BLE001 - counting must never stop the voice
            logger.exception("Could not count ElevenLabs characters")

    async def drain(self) -> None:
        """Wait until the counts handed off so far have been written (tests, shutdown)."""
        pending = list(self._pending)
        if pending:
            await asyncio.gather(*pending, return_exceptions=True)
