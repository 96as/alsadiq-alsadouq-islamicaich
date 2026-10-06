"""
Notes Section for the file:
- Builds the TTS engine for a voice session. ElevenLabs is THE voice.

- TTS_PROVIDER=elevenlabs (default) -> livekit-plugins-elevenlabs, auth ELEVEN_API_KEY.
- TTS_PROVIDER=xai                  -> the existing xAI streaming client, unchanged. This is an
  explicit rollback that only an operator turns on by setting the variable. Nothing in the
  code ever selects it by itself.

- NO AUTOMATIC FALLBACK (lead's rule, 2026-10-04). If ElevenLabs cannot be used (missing or
  placeholder key, plugin cannot be imported or built) build_tts logs ONE error line that
  names the cause (never the key) and raises VoiceConfigurationError. The entrypoint turns
  that into a clear failure for the session instead of speaking with another voice. A key,
  voice or plan that the API rejects after the session started is reported by the session
  error handler (explain_tts_failure below), also with no other voice taking over.

- Transcripts: the entrypoint runs the speech cleaner (tts_text.py: digits to words,
  Quran-bracket guard) as a session tts_text_transform and keeps the chat/DB transcript
  on the LLM's ORIGINAL text, so it does NOT use aligned transcripts. build_tts() is
  therefore called with aligned_transcript=False (the default), which turns off
  ElevenLabs word timings (sync_alignment=false). With aligned_transcript=True the
  plugin reports word timings and, under use_tts_aligned_transcript=True, the chat and
  DB text would come from the TTS text; ELEVEN_ALIGNMENT=original (default) then keeps
  the exact text sent to TTS, "normalized" ElevenLabs' rewritten text.

- Streaming only: the session uses the plugin's stream() (WebSocket multi-stream-input),
  because only that path honours language, normalisation and pronunciation dictionaries
  (the HTTP synthesize() path sends just text, model and voice settings). The plugin
  reports streaming=True, so livekit's default tts_node always picks stream().

- Models: eleven_v4_turbo is rejected (plugin 1.5.1 does not know it and it is not usable
  through the streaming socket). It falls back to the default model with one warning.

- Islamic content rule: Quran verses are never synthesised. They are played as
  recitation audio elsewhere. Nothing in this module handles scripture text.

- Env (all optional except the key):
    ELEVEN_API_KEY, ELEVEN_VOICE_ID_AR, ELEVEN_VOICE_ID_EN, ELEVEN_MODEL,
    ELEVEN_STABILITY, ELEVEN_SIMILARITY, ELEVEN_SPEED, ELEVEN_STYLE, ELEVEN_SPEAKER_BOOST,
    ELEVEN_TEXT_NORMALIZATION, ELEVEN_ALIGNMENT, ELEVEN_LANGUAGE_HINT,
    XAI_API_KEY, XAI_TTS_VOICE, XAI_TTS_LANGUAGE, ARABIC_TTS_LOCALE.
"""
from __future__ import annotations

import logging
import os
import threading
import time

from conversation.agent.language_config import resolve_speech_languages

logger = logging.getLogger(__name__)

PROVIDER_ELEVENLABS = "elevenlabs"
PROVIDER_XAI = "xai"

# Candidate Arabic (MSA) voices from the task-07 audition list. The defaults are
# placeholders until the team picks one; confirm with scripts/voice/audition.py.
DEFAULT_VOICE_ID_AR = "w4LX7bK479eHGM1k15Em"  # Habibah (warm, storytelling)
DEFAULT_VOICE_ID_EN = "w4LX7bK479eHGM1k15Em"  # multilingual voice reads English too
DEFAULT_MODEL = "eleven_flash_v2_5"

# Calm storyteller for children, from the source-checked fact sheet
# (docs/hackathon/handoffs/07-elevenlabs-facts.md, "Recommended settings"): steadier and a
# little slower than normal, no style exaggeration. Tune by ear after the audition.
DEFAULT_STABILITY = 0.65
DEFAULT_SIMILARITY = 0.75
DEFAULT_STYLE = 0.0
DEFAULT_SPEAKER_BOOST = True
DEFAULT_SPEED = 0.92
SPEED_MIN, SPEED_MAX = 0.7, 1.2  # ElevenLabs accepted range (the plugin comment says 0.8)

# Models that accept a language_code hint. Others (multilingual_v2, v3) reject it.
_LANGUAGE_HINT_MODELS = {"eleven_flash_v2_5", "eleven_turbo_v2_5"}

# Not usable with plugin 1.5.1's streaming socket (see the fact sheet): never offered.
_UNSUPPORTED_MODELS = {"eleven_v4_turbo"}

_TEXT_NORMALIZATION_VALUES = ("auto", "on", "off")
_ALIGNMENT_VALUES = ("original", "normalized")
DEFAULT_ALIGNMENT = "original"
_OFF_VALUES = ("0", "off", "false", "no")

_warned: set[str] = set()


class VoiceConfigurationError(RuntimeError):
    """The configured voice provider cannot be used. There is no fallback voice.

    code is a short stable word for the UI and the logs (see the CODE_* constants).
    The message names the cause and never contains a key.
    """

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


CODE_MISSING_KEY = "missing_key"
CODE_PLUGIN_UNAVAILABLE = "plugin_unavailable"
CODE_BUILD_FAILED = "build_failed"
CODE_KEY_REJECTED = "key_rejected"
CODE_VOICE_REJECTED = "voice_rejected"
CODE_QUOTA = "quota_or_plan"
CODE_UNREACHABLE = "unreachable"
CODE_FAILED = "failed"


def _warn_once(key: str, message: str, *args) -> None:
    if key in _warned:
        return
    _warned.add(key)
    logger.warning(message, *args)


def _reset_warnings_for_tests() -> None:
    _warned.clear()
    _last_api_error.clear()


def _env(name: str, default: str = "") -> str:
    return (os.getenv(name) or "").strip() or default


def _env_float(name: str, default: float, lo: float, hi: float) -> float:
    raw = _env(name)
    if not raw:
        return default
    try:
        value = float(raw)
    except ValueError:
        _warn_once(f"bad-float-{name}", "%s=%r is not a number; using %s", name, raw, default)
        return default
    return max(lo, min(hi, value))


def _env_choice(name: str, default: str, allowed: tuple[str, ...]) -> str:
    value = _env(name, default).lower()
    if value not in allowed:
        _warn_once(f"bad-choice-{name}", "%s=%r is not one of %s; using %s",
                   name, value, "/".join(allowed), default)
        return default
    return value


def eleven_key_configured() -> bool:
    """True when ELEVEN_API_KEY holds something that could be a real key.

    Blank values and the .env example placeholders ("your-...", "<...>") count as
    missing, so a copied example file fails clearly at session start (VoiceConfigurationError)
    instead of mid-call.
    """
    key = _env("ELEVEN_API_KEY")
    if not key:
        return False
    lowered = key.lower()
    return not (lowered.startswith(("your-", "<", "changeme", "change-me")) or " " in key)


def selected_provider() -> str:
    """Return the TTS provider named by TTS_PROVIDER (default elevenlabs)."""
    provider = _env("TTS_PROVIDER", PROVIDER_ELEVENLABS).lower()
    if provider not in (PROVIDER_ELEVENLABS, PROVIDER_XAI):
        _warn_once(
            f"bad-provider-{provider}",
            "Unknown TTS_PROVIDER=%r; using %s", provider, PROVIDER_ELEVENLABS,
        )
        return PROVIDER_ELEVENLABS
    return provider


def voice_id_for(lang: str) -> str:
    """Pick the ElevenLabs voice id for the session language (ar or en)."""
    if (lang or "").strip().lower() == "ar":
        return _env("ELEVEN_VOICE_ID_AR", DEFAULT_VOICE_ID_AR)
    return _env("ELEVEN_VOICE_ID_EN", DEFAULT_VOICE_ID_EN)


def _load_elevenlabs_plugin():
    # Lazy so the module imports (and tests run) without the plugin installed.
    from livekit.plugins import elevenlabs

    return elevenlabs


def _load_xai_tts_class():
    from conversation.agent.xai_tts_streaming import TTS as XaiStreamingTTS

    return XaiStreamingTTS


def _build_xai(lang: str, xai_language: str | None):
    if xai_language is None:
        _, xai_language = resolve_speech_languages(
            lang,
            default_stt_language=_env("STT_LANGUAGE", "en"),
            default_tts_language=_env("XAI_TTS_LANGUAGE", "auto"),
            arabic_tts_locale=_env("ARABIC_TTS_LOCALE", "ar-SA"),
        )
    return _load_xai_tts_class()(
        voice=_env("XAI_TTS_VOICE", "leo"),
        language=xai_language,
    )


def selected_model() -> str:
    """ELEVEN_MODEL, with models that cannot work on the streaming socket rejected."""
    model = _env("ELEVEN_MODEL", DEFAULT_MODEL)
    if model.lower() in _UNSUPPORTED_MODELS:
        _warn_once(
            f"unsupported-model-{model.lower()}",
            "ELEVEN_MODEL=%r is not usable with the streaming plugin (livekit-plugins-"
            "elevenlabs 1.5.1); using %s", model, DEFAULT_MODEL,
        )
        return DEFAULT_MODEL
    return model


def _build_elevenlabs(lang: str, aligned_transcript: bool, lipsync_alignment: bool = False):
    elevenlabs = _load_elevenlabs_plugin()
    model = selected_model()

    settings_kwargs = {
        "stability": _env_float("ELEVEN_STABILITY", DEFAULT_STABILITY, 0.0, 1.0),
        "similarity_boost": _env_float("ELEVEN_SIMILARITY", DEFAULT_SIMILARITY, 0.0, 1.0),
        "style": _env_float("ELEVEN_STYLE", DEFAULT_STYLE, 0.0, 1.0),
        "use_speaker_boost": _env(
            "ELEVEN_SPEAKER_BOOST", "on" if DEFAULT_SPEAKER_BOOST else "off"
        ).lower() not in _OFF_VALUES,
        "speed": _env_float("ELEVEN_SPEED", DEFAULT_SPEED, SPEED_MIN, SPEED_MAX),
    }

    kwargs = {
        "voice_id": voice_id_for(lang),
        "model": model,
        "voice_settings": elevenlabs.VoiceSettings(**settings_kwargs),
        "apply_text_normalization": _env_choice(
            "ELEVEN_TEXT_NORMALIZATION", "auto", _TEXT_NORMALIZATION_VALUES),
        # Word timings are only useful (and only sent) when the chat transcript is built
        # from TTS text. Our transcript is the LLM's original text, so they stay off.
        "sync_alignment": aligned_transcript,
    }
    # The avatar's lip sync (LIPSYNC_TIMELINE=1) needs the character timings too, without making
    # them the chat transcript (the session keeps use_tts_aligned_transcript=False).
    if lipsync_alignment:
        kwargs["sync_alignment"] = True
    if aligned_transcript or lipsync_alignment:
        kwargs["preferred_alignment"] = _env_choice(
            "ELEVEN_ALIGNMENT", DEFAULT_ALIGNMENT, _ALIGNMENT_VALUES)
    # language_code enforces one language for the whole session. The prompt lets the
    # agent answer in English inside an Arabic session, so ELEVEN_LANGUAGE_HINT=off
    # lets ElevenLabs detect the language per sentence instead.
    hint_on = _env("ELEVEN_LANGUAGE_HINT", "on").lower() not in _OFF_VALUES
    if hint_on and model in _LANGUAGE_HINT_MODELS and (lang or "").strip().lower() in ("ar", "en"):
        kwargs["language"] = lang.strip().lower()
    return elevenlabs.TTS(**kwargs)


_SECRET_ENV_NAMES = ("ELEVEN_API_KEY", "XAI_API_KEY", "OPENAI_API_KEY")


def redact(text: str) -> str:
    """Remove the values of the provider keys from text that is about to be logged."""
    for name in _SECRET_ENV_NAMES:
        value = _env(name)
        if len(value) >= 8:
            text = text.replace(value, "[redacted]")
    return text


def fail_voice(code: str, message: str, *, cause: BaseException | None = None):
    """Log ONE error line naming the cause, then raise. Never includes a key."""
    logger.error("Voice unavailable (%s): %s No fallback voice is used.", code, message)
    raise VoiceConfigurationError(code, message) from cause


def build_tts(lang: str, *, xai_language: str | None = None, aligned_transcript: bool = False,
              provider: str | None = None, lipsync_alignment: bool = False):
    """Build the session TTS.

    lang: resolved session language ("ar" or "en"; anything else gets the English voice).
    xai_language: language query param for the xAI client, used only when the operator set
        TTS_PROVIDER=xai (entrypoint passes the value from resolve_speech_languages). When
        omitted it is derived from env.
    aligned_transcript: True only if the session builds its transcript from TTS word
        timings (use_tts_aligned_transcript=True). Default False: no timings are requested.
    lipsync_alignment: True when LIPSYNC_TIMELINE is on: ElevenLabs also returns character timings
        (sync_alignment) for the avatar's lip sync, which the agent forwards. The transcript is
        unaffected. Default False leaves the arguments given to ElevenLabs exactly as before.
    provider: the voice the operator chose for THIS session through the VOICE_MODE kill switch
        (conversation/demo_guards.py): "elevenlabs" or "xai". None means follow TTS_PROVIDER.
        It is only ever passed from an explicit operator choice, never from a failure.

    Raises VoiceConfigurationError when ElevenLabs is selected but cannot be used. It never
    returns an xAI engine unless TTS_PROVIDER=xai was set explicitly.
    """
    chosen = provider if provider in (PROVIDER_ELEVENLABS, PROVIDER_XAI) else selected_provider()
    if chosen == PROVIDER_XAI:
        _warn_once(
            "xai-explicit",
            "xAI voice selected by the operator (TTS_PROVIDER=xai or VOICE_MODE=xai): speaking "
            "with the xAI voice because the operator chose this rollback. ElevenLabs is not used.",
        )
        return _build_xai(lang, xai_language)

    if not eleven_key_configured():
        fail_voice(
            CODE_MISSING_KEY,
            "TTS_PROVIDER=elevenlabs but ELEVEN_API_KEY is missing or still a placeholder.",
        )

    try:
        install_api_error_capture()
        return _build_elevenlabs(lang, aligned_transcript, lipsync_alignment)
    except ImportError as exc:
        fail_voice(
            CODE_PLUGIN_UNAVAILABLE,
            "The ElevenLabs plugin (livekit-plugins-elevenlabs) could not be imported: "
            f"{type(exc).__name__}.",
            cause=exc,
        )
    except Exception as exc:  # noqa: BLE001 - any build error becomes the one clear error
        detail = redact(f"{type(exc).__name__}: {exc}")
        fail_voice(CODE_BUILD_FAILED, f"The ElevenLabs TTS could not be built ({detail}).", cause=exc)


# A key, voice or plan that the API rejects after the session started.
#
# The plugin (1.5.1) only logs ElevenLabs' own reason ("invalid_api_key",
# "voice_id_does_not_exist", ...) as extra fields of a log record named "elevenlabs tts
# returned error", then closes the socket. The exception the session finally sees is a
# generic "connection closed", so the real cause would be lost. A small log handler keeps the
# last reason (never any key: the API message holds none) for explain_tts_failure.

_PLUGIN_LOGGER = "livekit.plugins.elevenlabs"
_API_ERROR_MAX_AGE_S = 120.0
_last_api_error: dict = {}
_api_error_lock = threading.Lock()


class _ApiErrorCapture(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        if "returned error" not in record.getMessage():
            return
        data = getattr(record, "data", None)
        message = data.get("message") if isinstance(data, dict) else ""
        text = f"{getattr(record, 'error', '')} {message or ''}".strip()
        with _api_error_lock:
            _last_api_error.update(text=text, at=time.monotonic())


_capture_handler: _ApiErrorCapture | None = None


def install_api_error_capture() -> None:
    """Idempotent. Called when ElevenLabs is built so mid-session rejections stay explainable."""
    global _capture_handler
    if _capture_handler is None:
        _capture_handler = _ApiErrorCapture()
        logging.getLogger(_PLUGIN_LOGGER).addHandler(_capture_handler)


def _recent_api_error() -> str:
    with _api_error_lock:
        if _last_api_error and time.monotonic() - _last_api_error["at"] < _API_ERROR_MAX_AGE_S:
            return str(_last_api_error["text"])
    return ""


def _exception_chain(exc: BaseException | None):
    seen: set[int] = set()
    while exc is not None and id(exc) not in seen:
        seen.add(id(exc))
        yield exc
        exc = exc.__cause__ or exc.__context__


def explain_tts_failure(exc: BaseException | None) -> tuple[str, str]:
    """Turn a TTS error from the session into (code, plain cause). Never includes a key.

    Walks the exception chain: the plugin wraps a rejected WebSocket handshake (HTTP 401)
    in a generic connection error. ElevenLabs' own reason for an API-level rejection (bad key,
    unknown voice, quota) reaches us only through the plugin's log, captured above.
    """
    texts: list[str] = []
    statuses: list[int] = []
    for item in _exception_chain(exc):
        texts.append(f"{type(item).__name__} {item}".lower())
        for attr in ("status_code", "status"):
            value = getattr(item, attr, None)
            if isinstance(value, int) and value > 0:
                statuses.append(value)
        body = getattr(item, "body", None)
        if body:
            texts.append(str(body).lower())
    api_reason = _recent_api_error()
    if api_reason:
        texts.append(api_reason.lower())
    blob = " ".join(texts)

    if 401 in statuses or any(w in blob for w in ("invalid_api_key", "invalid api key", "unauthorized")):
        return CODE_KEY_REJECTED, "ElevenLabs rejected the API key (check ELEVEN_API_KEY)."
    if "voice" in blob and any(
        w in blob for w in ("not found", "not_found", "does not exist", "not_exist", "invalid", "unknown")
    ):
        return CODE_VOICE_REJECTED, (
            "ElevenLabs rejected the voice id (check ELEVEN_VOICE_ID_AR and ELEVEN_VOICE_ID_EN)."
        )
    if 402 in statuses or 429 in statuses or any(
        w in blob for w in ("quota", "credits", "payment", "plan", "subscription")
    ):
        return CODE_QUOTA, "ElevenLabs refused the request: quota, credits or plan limit."
    if 403 in statuses:
        return CODE_KEY_REJECTED, "ElevenLabs denied access (HTTP 403): check the key, its permissions and the plan."
    if any(w in blob for w in ("could not connect", "timeout", "timed out", "connection")):
        return CODE_UNREACHABLE, "ElevenLabs could not be reached (network or timeout)."
    name = type(exc).__name__ if exc is not None else "unknown error"
    return CODE_FAILED, f"ElevenLabs TTS failed ({redact(name)})."
