"""Shared helpers for the voice tools (standard library only, no LiveKit needed).

Keys are read from the environment, or else from a key file outside git. They are
never printed, logged or written to any output file.
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = REPO_ROOT / "backend"
# Default key file sits next to the worktrees, outside the repo: <worktrees>/eleven-key.txt
DEFAULT_KEY_FILE = REPO_ROOT.parent / "eleven-key.txt"
ELEVEN_BASE = "https://api.elevenlabs.io"
# Some CDNs reject the default Python-urllib agent, so identify ourselves.
USER_AGENT = "alsadiq-voice-tools/1.0"


def use_utf8_output() -> None:
    """Arabic text must print on Windows consoles that default to a legacy codepage."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass


def load_eleven_key() -> str | None:
    """ELEVEN_API_KEY from the environment, else from ELEVEN_KEY_FILE / the default key file."""
    key = (os.environ.get("ELEVEN_API_KEY") or "").strip()
    if key:
        return key
    path = Path(os.environ.get("ELEVEN_KEY_FILE") or DEFAULT_KEY_FILE)
    try:
        raw = path.read_bytes()
    except OSError:
        return None
    # Windows PowerShell writes UTF-16 (">") or UTF-8 with a BOM (Out-File/Set-Content);
    # a BOM left in the key would break the request header.
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        text = raw.decode("utf-16", "replace")
    else:
        text = raw.decode("utf-8-sig", "replace")
    lines = [ln.strip().strip("\"'") for ln in text.splitlines() if ln.strip()]
    key = lines[0] if lines else ""
    if key.upper().startswith("ELEVEN_API_KEY="):
        key = key.split("=", 1)[1].strip().strip("\"'")
    return key or None


def key_source() -> str:
    """Where the key would come from, for messages. Never includes the key itself."""
    if (os.environ.get("ELEVEN_API_KEY") or "").strip():
        return "environment ELEVEN_API_KEY"
    path = Path(os.environ.get("ELEVEN_KEY_FILE") or DEFAULT_KEY_FILE)
    return f"key file {path}" if path.is_file() else "none found"


def import_backend_module(name: str):
    """Import a backend module that has no framework imports at load time."""
    if str(BACKEND_DIR) not in sys.path:
        sys.path.insert(0, str(BACKEND_DIR))
    import importlib

    return importlib.import_module(name)


class ApiError(Exception):
    def __init__(self, status: int, detail: str):
        super().__init__(f"HTTP {status}: {detail}")
        self.status = status
        self.detail = detail


def _short_detail(raw: bytes) -> str:
    text = raw.decode("utf-8", "replace")
    try:
        data = json.loads(text)
        detail = data.get("detail", data)
        if isinstance(detail, dict):
            detail = detail.get("message") or detail.get("status") or detail
        text = str(detail)
    except (ValueError, AttributeError):
        pass
    return text[:300]


def request(method: str, url: str, *, headers: dict | None = None, body: bytes | None = None,
            timeout: float = 60.0, retries: int = 1):
    """Return (status, first_byte_seconds, total_seconds, payload_bytes). Raises ApiError on 4xx/5xx."""
    hdrs = {"User-Agent": USER_AGENT, **(headers or {})}
    for attempt in range(retries + 1):
        req = urllib.request.Request(url, data=body, method=method, headers=hdrs)
        start = time.perf_counter()
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                first = resp.read(1)
                ttfb = time.perf_counter() - start
                rest = resp.read()
                return resp.status, ttfb, time.perf_counter() - start, first + rest
        except urllib.error.HTTPError as err:
            detail = _short_detail(err.read())
            if err.code == 429 and attempt < retries:
                time.sleep(3)
                continue
            raise ApiError(err.code, detail) from None
        except urllib.error.URLError as err:
            raise ApiError(0, f"network error: {err.reason}") from None
    raise ApiError(0, "unreachable")


def get_json(path: str, key: str):
    _, _, _, data = request("GET", ELEVEN_BASE + path, headers={"xi-api-key": key})
    return json.loads(data)


def multipart(fields: list[tuple[str, str]], files: list[tuple[str, str, bytes, str]]):
    """Build a multipart/form-data body. files: (field, filename, content, content_type)."""
    boundary = uuid.uuid4().hex
    parts: list[bytes] = []
    for name, value in fields:
        parts.append(
            f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode()
        )
    for name, filename, content, ctype in files:
        parts.append(
            (f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'
             f"Content-Type: {ctype}\r\n\r\n").encode() + content + b"\r\n"
        )
    parts.append(f"--{boundary}--\r\n".encode())
    return b"".join(parts), f"multipart/form-data; boundary={boundary}"
