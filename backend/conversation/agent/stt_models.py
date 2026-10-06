"""
Notes Section for the file:
- Which OpenAI transcription models STT_MODEL can switch to with the livekit-plugins-openai
  1.5.1 STT (task 08, step 8). Checked on the team key on 4 Oct 2026, with a real
  speech clip over the realtime transcription websocket and over the REST endpoint.

    gpt-4o-mini-transcribe   works (realtime and REST). The default.
    gpt-4o-transcribe        works (realtime and REST). More accurate, a bit slower.
    gpt-transcribe           works (realtime and REST). Same server-side stop-to-final time
                             as gpt-4o-mini-transcribe in a 3-run check (about 0.4 to 0.7 s),
                             so it is a fair A/B by STT_MODEL, not a speed win by itself.
    gpt-live-transcribe      DOES NOT WORK with the 1.5.1 plugin. Realtime only (REST is 404).
    gpt-realtime-whisper     DOES NOT WORK with the 1.5.1 plugin. Realtime only (REST is 404).

- Why the two live models fail: the plugin always sends turn_detection=server_vad in the
  session set-up and the API answers "Turn detection is not supported for this transcription
  model", which the plugin ignores. With turn_detection null the model does stream live text
  (the first words arrive while the child is still speaking), but it never sends a "final
  transcript" by itself: it only does after the client sends input_audio_buffer.commit, and
  the 1.5.1 plugin never sends a commit. So the child's turn would never get a transcript and
  the companion would stay silent. Same class of problem as the Scribe note in APPROACH.md.

- What this file does: a STT_MODEL of one of those two models is not used. ONE error is
  logged with the reason and the default model is used instead, so a typo in an env file never
  gives a session with a dead microphone. Other values pass through unchanged (a future
  model name just works).

- TODO (the way to use a live model later): a small subclass of the plugin's SpeechStream
  that sets turn_detection to null and sends input_audio_buffer.commit when livekit flushes
  the stream at the VAD end of speech (the _FlushSentinel in send_task). That also gives
  interim text while the child speaks. Needs a live check with children's speech first.
"""
from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

DEFAULT_STT_MODEL = "gpt-4o-mini-transcribe"

# Realtime-only models that need a client-side commit, which the 1.5.1 plugin never sends.
UNSUPPORTED_BY_PLUGIN = frozenset({"gpt-live-transcribe", "gpt-realtime-whisper"})


def resolve_stt_model(raw: str | None = None, *, default: str = DEFAULT_STT_MODEL) -> str:
    """The STT model to use: STT_MODEL if the plugin can run it, else the default."""
    value = (os.getenv("STT_MODEL") if raw is None else raw) or ""
    value = value.strip() or default
    if value.lower() in UNSUPPORTED_BY_PLUGIN:
        logger.error(
            "STT_MODEL=%s needs a client-side commit that livekit-plugins-openai 1.5.1 does not "
            "send, so the child's turns would never get a transcript. Using %s instead. "
            "See agent/stt_models.py.",
            value, default,
        )
        return default
    return value
