"""
Notes Section for the file:
- Builds the speech-to-text engine behind STT_PROVIDER.

- STT_PROVIDER=openai (default, off-by-default for Scribe) -> the existing OpenAI STT,
  built by the callable the entrypoint passes in, so default behaviour is unchanged.
- STT_PROVIDER=scribe -> ElevenLabs Scribe via livekit-plugins-elevenlabs (ELEVEN_API_KEY).
  Model from STT_SCRIBE_MODEL (default scribe_v2_realtime).

- Keyterms bias recognition toward the value names (honesty, patience, ...). The plugin
  only sends keyterms on batch recognition (scribe_v1 / scribe_v2), not on the realtime
  stream, so with scribe_v2_realtime they are accepted but have no effect.

- No silent fallback. OpenAI is the default engine, and Scribe is only used when an operator
  sets STT_PROVIDER=scribe. If Scribe is chosen but cannot be used (missing or placeholder
  ELEVEN_API_KEY, plugin cannot be built) the factory logs ONE error naming the cause (never
  the key) and raises VoiceConfigurationError, the same as the TTS factory. It never
  quietly hears the child with a different engine.
"""
from __future__ import annotations

import logging
import os
from collections.abc import Callable, Iterable

from conversation.agent.tts_factory import (
    CODE_BUILD_FAILED,
    CODE_MISSING_KEY,
    CODE_PLUGIN_UNAVAILABLE,
    eleven_key_configured,
    fail_voice,
    redact,
)

logger = logging.getLogger(__name__)

PROVIDER_OPENAI = "openai"
PROVIDER_SCRIBE = "scribe"
DEFAULT_SCRIBE_MODEL = "scribe_v2_realtime"

# Everyday value words and greetings, no scripture. Arabic spellings of the knowledge-bank
# value themes (Honesty, Truthfulness, Courage, Kindness, Responsibility, Patience).
VALUE_KEYTERMS_AR = (
    "الصدق",
    "الأمانة",
    "الشجاعة",
    "اللطف",
    "الرحمة",
    "المسؤولية",
    "الصبر",
    "السلام عليكم",
    "إن شاء الله",
    "ما شاء الله",
    "جزاك الله خيرا",
    "الصديق الصدوق",
)

MAX_KEYTERMS = 50  # ElevenLabs allows more; keep the list short and relevant
_MAX_KEYTERM_CHARS = 49
_MAX_KEYTERM_WORDS = 5

_warned: set[str] = set()


def _reset_warnings_for_tests() -> None:
    _warned.clear()


def _env(name: str, default: str = "") -> str:
    return (os.getenv(name) or "").strip() or default


def selected_provider() -> str:
    provider = _env("STT_PROVIDER", PROVIDER_OPENAI).lower()
    if provider not in (PROVIDER_OPENAI, PROVIDER_SCRIBE):
        if f"bad-{provider}" not in _warned:
            _warned.add(f"bad-{provider}")
            logger.warning("Unknown STT_PROVIDER=%r; using %s", provider, PROVIDER_OPENAI)
        return PROVIDER_OPENAI
    return provider


def build_keyterms(lang: str, theme_names: Iterable[str] | None = None) -> list[str]:
    """Value names (from the knowledge bank) plus Arabic spellings for Arabic sessions."""
    terms: list[str] = []
    seen: set[str] = set()
    candidates = list(theme_names or [])
    if (lang or "").strip().lower() == "ar":
        candidates += list(VALUE_KEYTERMS_AR)
    for raw in candidates:
        term = " ".join((raw or "").split())
        if not term or term.lower() in seen:
            continue
        if len(term) > _MAX_KEYTERM_CHARS or len(term.split()) > _MAX_KEYTERM_WORDS:
            continue
        seen.add(term.lower())
        terms.append(term)
    return terms[:MAX_KEYTERMS]


def _load_elevenlabs_plugin():
    from livekit.plugins import elevenlabs

    return elevenlabs


def build_stt(
    lang: str,
    *,
    openai_factory: Callable[[], object],
    theme_names: Iterable[str] | None = None,
):
    """Build the session STT.

    lang: resolved STT language ("ar", "en", ...).
    openai_factory: builds the existing OpenAI STT; used by default (STT_PROVIDER unset or openai).
    theme_names: value names from the knowledge bank, used as Scribe keyterms.

    Raises VoiceConfigurationError if STT_PROVIDER=scribe is set but Scribe cannot be used.
    """
    if selected_provider() != PROVIDER_SCRIBE:
        return openai_factory()

    if not eleven_key_configured():
        fail_voice(
            CODE_MISSING_KEY,
            "STT_PROVIDER=scribe but ELEVEN_API_KEY is missing or still a placeholder.",
        )

    try:
        elevenlabs = _load_elevenlabs_plugin()
        kwargs = {"model_id": _env("STT_SCRIBE_MODEL", DEFAULT_SCRIBE_MODEL)}
        code = (lang or "").strip().lower()
        if code:
            kwargs["language_code"] = code
        keyterms = build_keyterms(code, theme_names)
        if keyterms:
            kwargs["keyterms"] = keyterms
        return elevenlabs.STT(**kwargs)
    except ImportError as exc:
        fail_voice(
            CODE_PLUGIN_UNAVAILABLE,
            "The ElevenLabs plugin (livekit-plugins-elevenlabs) could not be imported for "
            f"Scribe STT: {type(exc).__name__}.",
            cause=exc,
        )
    except Exception as exc:  # noqa: BLE001 - any build error becomes the one clear error
        detail = redact(f"{type(exc).__name__}: {exc}")
        fail_voice(CODE_BUILD_FAILED, f"ElevenLabs Scribe STT could not be built ({detail}).", cause=exc)
