"""Thin OpenAI client for structured JSON responses (reporting pipeline)."""
from __future__ import annotations

import json
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


def call_llm(system_prompt: str, user_content: str, *, model: str | None = None) -> dict[str, Any]:
    """Call Chat Completions API and parse JSON object response.

    Requires OPENAI_API_KEY. Model defaults to REPORTING_LLM_MODEL env or ``gpt-5.4-mini``.
    """
    from openai import OpenAI

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set")

    resolved_model = model or os.getenv("REPORTING_LLM_MODEL", "gpt-5.4-mini")
    client = OpenAI(api_key=api_key)

    try:
        response = client.chat.completions.create(
            model=resolved_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            response_format={"type": "json_object"},
        )
    except Exception:
        logger.exception("OpenAI chat.completions failed model=%s", resolved_model)
        raise

    text = (response.choices[0].message.content or "").strip() or "{}"
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        logger.warning("LLM returned non-JSON; wrapping raw text")
        return {"raw_text": text, "parse_error": True}
