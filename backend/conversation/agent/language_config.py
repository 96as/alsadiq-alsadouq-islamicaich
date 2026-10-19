from __future__ import annotations

from typing import Tuple


def resolve_speech_languages(
    child_language_preference: str | None,
    *,
    default_stt_language: str,
    default_tts_language: str,
    arabic_tts_locale: str,
) -> Tuple[str, str]:
    pref = (child_language_preference or "").strip().lower()
    if pref == "ar":
        return "ar", arabic_tts_locale
    if pref == "en":
        return "en", "en"
    return default_stt_language, default_tts_language
