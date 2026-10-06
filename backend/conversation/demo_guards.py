"""
Notes Section for the file:
- Credit and safety guards for the public demo. No migrations: everything lives in Redis
  (plus the existing Session rows as a fallback), so the Django backend and the LiveKit
  agent share one source of truth.

- What it guards (all env-configurable, see CONFIG below):
    * a time limit per voice session (the agent says goodbye and closes the room),
    * a daily session cap per child (checked when a session starts),
    * a daily ElevenLabs character budget: past it, NEW sessions are text-only,
    * a kill switch, the Redis key VOICE_MODE (eleven | xai | text | off),
    * a start throttle per user (see SessionStartThrottle).
  Judge accounts (demo.accounts.is_judge_user) get their own, higher daily cap and start
  throttle (JUDGE_DAILY_SESSIONS, JUDGE_SESSION_START_PER_HOUR) instead of the demo ones.

- NO AUTOMATIC FALLBACK TO xAI (lead's rule, 2026-10-04). Nothing in this file ever picks
  xai on its own. "xai" is only returned when an operator chose it by hand: the Redis key
  VOICE_MODE=xai, or the TTS_PROVIDER=xai environment variable. When ElevenLabs is out of
  budget the answer is "text", never another voice.

- When the guards are active: DEMO_GUARDS=1, or DEMO_GUARDS unset and DEBUG is off.
  DEMO_GUARDS=0 forces them off. While they are off, no limit applies (the kill switch
  still works, because it only exists when an operator sets it on purpose).

- Redis trouble never takes the product down: every Redis call fails open (the guard is
  skipped) after one logged error, and a short circuit breaker avoids hammering a dead
  Redis from the audio path. The session time limit needs no Redis at all.

- Keys (Redis):
    VOICE_MODE                          operator's kill switch value (no expiry)
    demo:sessions:<child_id>:<day>      sessions started by a child today (2 day expiry)
    demo:eleven_chars:<day>             characters sent to ElevenLabs today (2 day expiry)
    demo:session:<session_id>           JSON: the mode decided at start (6 hour expiry)
  <day> is the date in DEMO_DAY_UTC_OFFSET_HOURS (default +3, Riyadh; no DST).

- No Quran text here. The goodbye lines are plain friendly words.
"""
from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Modes
# ---------------------------------------------------------------------------

MODE_ELEVEN = "eleven"
MODE_XAI = "xai"
MODE_TEXT = "text"
MODE_OFF = "off"
VOICE_MODES = (MODE_ELEVEN, MODE_XAI, MODE_TEXT, MODE_OFF)

KEY_VOICE_MODE = "VOICE_MODE"

REASON_ENV = "env"  # no Redis value: followed TTS_PROVIDER
REASON_OPERATOR = "operator"  # Redis VOICE_MODE
REASON_ELEVEN_CAP = "eleven_daily_cap"  # budget used up: text only, never another voice

# ---------------------------------------------------------------------------
# Friendly messages. Arabic first. Shown to a child, so: warm, short, no codes, no scripture.
# ---------------------------------------------------------------------------

MESSAGES = {
    "daily_limit": {
        "ar": "لقد استمتعنا اليوم كثيرًا يا صديقي! عُد غدًا ونكمل حديثنا.",
        "en": "We had lots of fun today, my friend! Come back tomorrow and we will chat again.",
    },
    "rate_limited": {
        "ar": "مهلًا يا صديقي، بدأنا محادثات كثيرة في وقت قصير. انتظر قليلًا ثم حاول مرة أخرى.",
        "en": "Slow down, my friend, we started lots of chats in a short time. "
              "Wait a little and try again.",
    },
    "voice_resting": {
        "ar": "صوت الصديق يستريح الآن، فلنتحدّث كتابةً!",
        "en": "Al-Sadiq's voice is resting, so let's chat by text!",
    },
    "voice_off": {
        "ar": "الصديق يستريح الآن. عُد بعد قليل وسنتحدّث معًا.",
        "en": "Al-Sadiq is resting right now. Please come back a little later.",
    },
}

GOODBYE = {
    "ar": "حان وقت الوداع يا صديقي، كان حديثنا جميلًا جدًا. أراك قريبًا، مع السلامة!",
    "en": "It is almost time to say goodbye, my friend. I really enjoyed our chat. "
          "See you soon, bye bye!",
}


def message_for(code: str) -> dict:
    return dict(MESSAGES[code])


def goodbye_for(language: str | None) -> str:
    return GOODBYE["ar" if (language or "").strip().lower().startswith("ar") else "en"]


# ---------------------------------------------------------------------------
# Configuration (read from the environment at call time)
# ---------------------------------------------------------------------------

_warned: set[str] = set()


def _warn_once(key: str, message: str, *args) -> None:
    if key not in _warned:
        _warned.add(key)
        logger.warning(message, *args)


def _env(name: str) -> str:
    return (os.getenv(name) or "").strip()


def _env_int(name: str, default: int) -> int:
    raw = _env(name)
    if not raw:
        return default
    try:
        return max(0, int(raw))
    except ValueError:
        _warn_once(f"bad-int-{name}", "%s=%r is not a whole number; using %s", name, raw, default)
        return default


def guards_active() -> bool:
    """DEMO_GUARDS=1 turns the limits on, 0 turns them off. Unset: on unless DEBUG is on."""
    flag = _env("DEMO_GUARDS").lower()
    if flag in ("1", "true", "on", "yes"):
        return True
    if flag in ("0", "false", "off", "no"):
        return False
    # Same rule as settings.py: DEBUG unset counts as off (production).
    return (os.getenv("DEBUG", "0") or "").strip() != "1"


@dataclass(frozen=True)
class GuardConfig:
    active: bool
    session_max_seconds: int  # 0 = no limit
    daily_sessions: int  # 0 = no limit
    eleven_daily_chars: int  # 0 = no cap
    session_start_per_hour: int  # 0 = no throttle
    judge_daily_sessions: int  # same, for judge accounts
    judge_session_start_per_hour: int
    goodbye_lead_seconds: int
    hard_grace_seconds: int


def config() -> GuardConfig:
    active = guards_active()

    def limit(name: str, default: int) -> int:
        return _env_int(name, default) if active else 0

    return GuardConfig(
        active=active,
        session_max_seconds=limit("DEMO_SESSION_MAX_SECONDS", 300),
        daily_sessions=limit("DEMO_DAILY_SESSIONS", 3),
        eleven_daily_chars=limit("ELEVEN_DAILY_CHAR_CAP", 20000),
        session_start_per_hour=limit("DEMO_SESSION_START_PER_HOUR", 6),
        judge_daily_sessions=limit("JUDGE_DAILY_SESSIONS", 30),
        judge_session_start_per_hour=limit("JUDGE_SESSION_START_PER_HOUR", 20),
        goodbye_lead_seconds=_env_int("DEMO_GOODBYE_LEAD_SECONDS", 20),
        hard_grace_seconds=_env_int("DEMO_SESSION_GRACE_SECONDS", 10),
    )


def _day_offset_hours() -> int:
    raw = _env("DEMO_DAY_UTC_OFFSET_HOURS")
    try:
        return int(raw) if raw else 3
    except ValueError:
        _warn_once("bad-offset", "DEMO_DAY_UTC_OFFSET_HOURS=%r is not a whole number; using 3", raw)
        return 3


def today() -> str:
    """The guard day (a date string) in DEMO_DAY_UTC_OFFSET_HOURS, default Riyadh (+3)."""
    return (datetime.now(timezone.utc) + timedelta(hours=_day_offset_hours())).date().isoformat()


# ---------------------------------------------------------------------------
# Redis access. Every call fails open.
# ---------------------------------------------------------------------------

_client = None
_client_url: str | None = None
_down_until = 0.0
_BREAKER_SECONDS = 30.0
_DAY_TTL = 2 * 24 * 3600
_SESSION_TTL = 6 * 3600


def _redis_url() -> str:
    url = _env("REDIS_URL")
    if url:
        return url
    host = _env("REDIS_HOST")
    if not host:
        return ""
    return f"redis://{host}:{_env('REDIS_PORT') or '6379'}/{_env('REDIS_GUARDS_DB') or '0'}"


def redis_client():
    """The shared Redis client, or None when Redis is not configured or recently failed."""
    global _client, _client_url
    if time.monotonic() < _down_until:
        return None
    url = _redis_url()
    if not url:
        if guards_active() and "no-redis" not in _warned:
            _warned.add("no-redis")
            logger.error(
                "Demo guards are on but Redis is not configured (REDIS_HOST / REDIS_URL): the "
                "kill switch, the daily caps and the ElevenLabs budget are skipped in this "
                "process.")
        return None
    if _client is None or _client_url != url:
        try:
            import redis

            _client = redis.Redis.from_url(
                url, socket_timeout=0.5, socket_connect_timeout=0.5, decode_responses=True)
            _client_url = url
        except Exception:  # noqa: BLE001 - never break a session over the guards
            _trip("could not create the Redis client")
            return None
    return _client


def _trip(why: str) -> None:
    global _down_until
    _down_until = time.monotonic() + _BREAKER_SECONDS
    logger.error("Demo guards: Redis unavailable (%s). Guards that need it are skipped for "
                 "%ds.", why, int(_BREAKER_SECONDS))


def _redis_call(fn, *, default=None):
    """Run fn(client). On any Redis error log once, open the breaker and return default."""
    client = redis_client()
    if client is None:
        return default
    try:
        return fn(client)
    except Exception as exc:  # noqa: BLE001
        _trip(type(exc).__name__)
        return default


def _reset_for_tests() -> None:
    global _client, _client_url, _down_until
    _client = None
    _client_url = None
    _down_until = 0.0
    _warned.clear()


# ---------------------------------------------------------------------------
# Kill switch and voice decision
# ---------------------------------------------------------------------------


def env_voice_mode() -> str:
    """What the environment says when nobody set the kill switch. xai only by hand."""
    provider = _env("TTS_PROVIDER").lower()
    return MODE_XAI if provider == "xai" else MODE_ELEVEN


def stored_voice_mode() -> str | None:
    """The operator's VOICE_MODE value from Redis, or None when unset or unreadable."""
    raw = _redis_call(lambda r: r.get(KEY_VOICE_MODE))
    if raw is None:
        return None
    value = str(raw).strip().lower()
    if value in VOICE_MODES:
        return value
    _warn_once(f"bad-voice-mode-{value}",
               "Redis VOICE_MODE=%r is not one of %s; ignoring it", value, "/".join(VOICE_MODES))
    return None


def set_stored_voice_mode(mode: str | None) -> bool:
    """Set (or with None clear) the kill switch. Returns False when Redis is unavailable."""
    if mode is not None and mode not in VOICE_MODES:
        raise ValueError(f"mode must be one of {VOICE_MODES}")

    def _apply(r):
        if mode is None:
            r.delete(KEY_VOICE_MODE)
        else:
            r.set(KEY_VOICE_MODE, mode)
        return True

    return bool(_redis_call(_apply, default=False))


@dataclass(frozen=True)
class VoiceDecision:
    mode: str  # eleven | xai | text | off
    reason: str  # env | operator | eleven_daily_cap
    notice: str | None = None  # a MESSAGES code to show the child, if any

    def as_dict(self) -> dict:
        return {"mode": self.mode, "reason": self.reason, "notice": self.notice}


_UNAVAILABLE = object()


def eleven_chars_today() -> int | None:
    """Characters sent to ElevenLabs today, or None when Redis is unavailable."""
    value = _redis_call(lambda r: r.get(f"demo:eleven_chars:{today()}") or 0,
                        default=_UNAVAILABLE)
    if value is _UNAVAILABLE:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def add_eleven_chars(count: int) -> None:
    """Count characters sent to ElevenLabs today. Fails open."""
    if count <= 0:
        return

    def _add(r):
        key = f"demo:eleven_chars:{today()}"
        r.incrby(key, count)
        r.expire(key, _DAY_TTL)

    _redis_call(_add)


def resolve_voice(*, cfg: GuardConfig | None = None) -> VoiceDecision:
    """Decide how a NEW session talks. Read at each session start.

    Order: Redis VOICE_MODE, else TTS_PROVIDER from the environment. When the answer is
    ElevenLabs and today's character budget is used up, the session is text-only. This
    function never returns xai unless an operator chose it.
    """
    cfg = cfg or config()
    stored = stored_voice_mode()
    if stored is not None:
        base, reason = stored, REASON_OPERATOR
    else:
        base, reason = env_voice_mode(), REASON_ENV

    if base == MODE_OFF:
        return VoiceDecision(MODE_OFF, reason, "voice_off")
    if base == MODE_TEXT:
        return VoiceDecision(MODE_TEXT, reason, "voice_resting")
    if base == MODE_ELEVEN and cfg.eleven_daily_chars > 0:
        used = eleven_chars_today()
        if used is not None and used >= cfg.eleven_daily_chars:
            logger.warning(
                "ElevenLabs daily character budget used up (%s of %s): new sessions are "
                "text-only. No other voice is used.", used, cfg.eleven_daily_chars)
            return VoiceDecision(MODE_TEXT, REASON_ELEVEN_CAP, "voice_resting")
    return VoiceDecision(base, reason)


# ---------------------------------------------------------------------------
# Daily session cap per child
# ---------------------------------------------------------------------------


class GuardDenied(Exception):
    """A guard refused to start the session. Carries what the API should answer."""

    def __init__(self, code: str, http_status: int):
        super().__init__(code)
        self.code = code
        self.http_status = http_status
        self.message = message_for(code)


def _db_sessions_today(child_id: int) -> int:
    from conversation.models import Session

    offset = _day_offset_hours()
    local_now = datetime.now(timezone.utc) + timedelta(hours=offset)
    start_local = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
    return Session.objects.filter(
        child_id=child_id, started_at__gte=start_local - timedelta(hours=offset)).count()


def _daily_cap(cfg: GuardConfig, judge: bool) -> int:
    return cfg.judge_daily_sessions if judge else cfg.daily_sessions


def reserve_daily_session(child_id: int, *, cfg: GuardConfig | None = None,
                          judge: bool = False) -> bool:
    """Count one more session for the child today. False when the daily cap is reached.

    Uses Redis (so a wiped demo family keeps its count). If Redis is unavailable it falls
    back to counting Session rows. A refused attempt is not counted.
    """
    cfg = cfg or config()
    cap = _daily_cap(cfg, judge)
    if cap <= 0:
        return True
    key = f"demo:sessions:{child_id}:{today()}"

    def _reserve(r):
        used = r.incr(key)
        r.expire(key, _DAY_TTL)
        if used > cap:
            r.decr(key)
            return False
        return True

    result = _redis_call(_reserve)
    if result is not None:
        return result
    try:
        return _db_sessions_today(child_id) < cap
    except Exception:  # noqa: BLE001
        logger.exception("Daily session cap: database fallback failed; allowing the session")
        return True


def release_daily_session(child_id: int, *, cfg: GuardConfig | None = None,
                          judge: bool = False) -> None:
    """Undo reserve_daily_session when the session could not be created."""
    cfg = cfg or config()
    if _daily_cap(cfg, judge) <= 0:
        return
    _redis_call(lambda r: r.decr(f"demo:sessions:{child_id}:{today()}"))


# ---------------------------------------------------------------------------
# One entry point for the session start view
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SessionGrant:
    decision: VoiceDecision
    max_seconds: int  # 0 = no limit
    reserved: bool  # a daily slot was counted (release it if creating the session fails)


REASON_CHILD_CHOICE = "child_choice"  # the child's app asked for a text-only chat


def check_session_start(
    child_id: int, *, cfg: GuardConfig | None = None, text_only: bool = False,
    judge: bool = False,
) -> SessionGrant:
    """Run the start-time guards in order. Raises GuardDenied, or returns the grant.

    1. kill switch "off"  -> 503 voice_off (no session, no room)
    2. daily cap          -> 429 daily_limit
    A budget-exhausted ElevenLabs answer is not a denial: the grant says text mode.
    text_only: the child asked for a text chat (the app offers it when the voice is resting).
    It never turns a voice on, only off, so it cannot cost credits or reach xAI. The kill
    switch and the daily cap still apply.
    judge: a judge account, counted against JUDGE_DAILY_SESSIONS instead.
    """
    cfg = cfg or config()
    decision = resolve_voice(cfg=cfg)
    if decision.mode == MODE_OFF:
        raise GuardDenied("voice_off", 503)
    if text_only and decision.mode != MODE_TEXT:
        decision = VoiceDecision(MODE_TEXT, REASON_CHILD_CHOICE)
    reserved = False
    if _daily_cap(cfg, judge) > 0:
        if not reserve_daily_session(child_id, cfg=cfg, judge=judge):
            raise GuardDenied("daily_limit", 429)
        reserved = True
    return SessionGrant(decision=decision, max_seconds=cfg.session_max_seconds, reserved=reserved)


# ---------------------------------------------------------------------------
# Per-session state shared with the agent
# ---------------------------------------------------------------------------


def save_session_state(session_id: int, grant: SessionGrant) -> None:
    payload = {
        "mode": grant.decision.mode,
        "reason": grant.decision.reason,
        "max_seconds": grant.max_seconds,
    }

    def _save(r):
        r.set(f"demo:session:{session_id}", json.dumps(payload), ex=_SESSION_TTL)

    _redis_call(_save)


def load_session_state(session_id: int) -> dict | None:
    raw = _redis_call(lambda r: r.get(f"demo:session:{session_id}"))
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except (TypeError, ValueError):
        return None
    if not isinstance(data, dict) or data.get("mode") not in VOICE_MODES:
        return None
    return data


# ---------------------------------------------------------------------------
# Usage report (manage.py voice_mode)
# ---------------------------------------------------------------------------


def usage_report() -> dict:
    cfg = config()
    day = today()

    def _sessions(r):
        total, children = 0, 0
        for key in r.scan_iter(match=f"demo:sessions:*:{day}", count=200):
            children += 1
            total += int(r.get(key) or 0)
        return total, children

    sessions = _redis_call(_sessions)
    return {
        "day": day,
        "redis": redis_client() is not None and sessions is not None,
        "guards_active": cfg.active,
        "stored_voice_mode": stored_voice_mode(),
        "env_voice_mode": env_voice_mode(),
        "decision": resolve_voice(cfg=cfg).as_dict(),
        "eleven_chars": eleven_chars_today(),
        "eleven_char_cap": cfg.eleven_daily_chars,
        "sessions_today": sessions[0] if sessions else None,
        "children_today": sessions[1] if sessions else None,
        "daily_sessions_per_child": cfg.daily_sessions,
        "session_max_seconds": cfg.session_max_seconds,
        "session_start_per_hour": cfg.session_start_per_hour,
        "judge_daily_sessions_per_child": cfg.judge_daily_sessions,
        "judge_session_start_per_hour": cfg.judge_session_start_per_hour,
    }
