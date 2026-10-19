"""
Notes Section for the file:
- Open the ElevenLabs websocket while the session is still starting (task 08, "TTS warm-up").
  The first reply used to pay the connection set-up (DNS, TLS, websocket upgrade, about 0.2 to
  0.5 s) on the child's clock. The plugin keeps ONE socket per TTS object and reuses it, so
  opening it at connect makes the greeting and every later reply start on a ready socket.

- Only for the ElevenLabs voice. xAI is a manual operator choice and gets nothing here. A
  session with no TTS (text-only) gets nothing either.

- Never fatal. A failed warm-up logs one warning (the error TYPE only, no message, no key) and
  the session carries on: the first real reply connects normally and the existing error path
  (the session "error" event in entrypoint.py) reports a rejected key or voice exactly once.

- Switch: TTS_WARMUP=0 turns it off (default on).

- It runs as a background task so it overlaps the rest of the start-up (agent session start,
  room audio set-up), with a timeout so a slow network never keeps a task around.
"""
from __future__ import annotations

import asyncio
import logging
import os

logger = logging.getLogger(__name__)

WARMUP_TIMEOUT_SECONDS = 8.0
_OFF_VALUES = {"0", "false", "no", "off"}
# The event loop keeps only a weak reference to a task: hold the running warm-ups here.
_running: set[asyncio.Task] = set()


def tts_warmup_enabled() -> bool:
    return (os.getenv("TTS_WARMUP") or "1").strip().lower() not in _OFF_VALUES


async def warm_up_tts(tts) -> bool:
    """Open the ElevenLabs websocket now. Returns True when it is open, False otherwise."""
    opener = getattr(tts, "current_connection", None)
    if opener is None:
        return False
    try:
        await asyncio.wait_for(opener(), timeout=WARMUP_TIMEOUT_SECONDS)
    except asyncio.CancelledError:
        raise
    except Exception as exc:  # noqa: BLE001 - warm-up must never break a session
        logger.warning(
            "TTS warm-up skipped (%s): the first reply will open the voice connection itself.",
            type(exc).__name__,
        )
        return False
    logger.info("TTS warm-up: ElevenLabs websocket is open")
    return True


def start_tts_warmup(tts, *, is_elevenlabs: bool) -> asyncio.Task | None:
    """Start the warm-up in the background; None when it does not apply."""
    if tts is None or not is_elevenlabs or not tts_warmup_enabled():
        return None
    task = asyncio.get_running_loop().create_task(warm_up_tts(tts), name="tts-warmup")
    _running.add(task)
    task.add_done_callback(_running.discard)
    return task
