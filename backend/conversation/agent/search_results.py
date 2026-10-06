"""The `al.search` publisher: what Al-Sadiq's web page shows in his hand (BEHAVIOUR-SPEC 6.2, work package W1).

The browser draws a small window with a page of result cards while the avatar searches. This module
sends the CONTENT of that page on the LiveKit data topic `al.search` (agent to browser, reliable).
The state machine (searching, found, none) is NOT here: it is driven by the `al.activity` attributes
(avatar_signals.py in the signals branch, `signals.search("web")`). `al.search` only carries text.

Messages (all `v` 1; `id` ties the three together, e.g. "S3"):

    {"v":1,"id":"S3","st":"searching","kind":"web","q":"how do bees make honey","lang":"en"}
    {"v":1,"id":"S3","st":"results","r":[{"t":"How bees make honey","d":"example.org","s":"Bees collect..."}],"hl":0}
    {"v":1,"id":"S3","st":"none"}

Two optional fields on top of the spec, both ignorable by a consumer that does not know them:

    "gu":1   the neutral grown-up card: the query tripped the scripture check, or a safety concern was
             flagged this turn. The page shows "Let's read this with a grown-up" / "نقرأها مع أحد الكبار"
             and NO text. `q` is "" in that case and there are no results. (st is "searching" then "none".)
    "fx":1   the content is a dev fixture (the simulated source below), never a real search. The page may
             show a small "fixture" badge.

Rules enforced here (spec 6.2, 4.4)
- At most 5 results; title 70 characters, snippet 140 (cut with an ellipsis, never rewritten); the
  domain only, never a full URL; nothing clickable (there is no link field at all).
- A result is dropped when its title, snippet or domain contains a scripture meta-word or more than 20%
  of its Arabic letters carry diacritics (content_guard). If the query trips the check, or
  `safety_flagged()` says a concern was flagged this turn, only the neutral grown-up card is sent.
- Strict safe search only: `search()` refuses a provider that does not declare `safe_search = True`.
- Text is cleaned: markup tags, control characters and bidi-override characters are removed and
  whitespace is collapsed. The browser must draw it as plain text (canvas / textContent), never innerHTML.
- `hl` is the index (in the SHOWN list) of the result the agent used; 0 when unknown or when that
  result was dropped.

Hook for the agent team (the one line): when a web tool exists, write it as
    results = await my_web_search(query)          # strict safe search, a list of dicts
    await self._search.results(sid, results, used=0)
or simply hand the provider to `AlSadiqAgent.web_search(query)` (agent_class.py), which wraps the
`signals.search("web")` activity and calls `SearchPublisher.search()`.

Dev source: `DevSearchProvider` serves kid-safe FIXTURES (see DEV_FIXTURES). It is on only when the
env flag SEARCH_DEV_SIM=1 is set (entrypoint.py), and its messages carry "fx":1. No real web access,
no key, no network.

Failure rule: nothing here raises into the voice path. A failed publish is logged once.
"""
from __future__ import annotations

import asyncio
import html
import json
import logging
import os
import re
from typing import Awaitable, Callable, Iterable
from urllib.parse import urlsplit

from conversation.agent import content_guard

logger = logging.getLogger(__name__)

TOPIC = "al.search"
VERSION = 1
MAX_RESULTS = 5
TITLE_MAX = 70
SNIPPET_MAX = 140
QUERY_MAX = 80
DOMAIN_MAX = 40
DEFAULT_TIMEOUT_S = 8.0
DEV_ENV = "SEARCH_DEV_SIM"

GROWNUP_TEXT = {"en": "Let's read this with a grown-up", "ar": "نقرأها مع أحد الكبار"}

_TAG = re.compile(r"<[^>]*>")
_CONTROL = re.compile("[\x00-\x08\x0b-\x1f\x7f-\x9f‎‏‪-‮⁦-⁩]")
_SPACES = re.compile(r"\s+")
_HOST = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+$")

_logged: set[str] = set()


def _log_once(key: str, message: str, *args, exc: BaseException | None = None) -> None:
    if key in _logged:
        return
    _logged.add(key)
    logger.warning(message, *args, exc_info=exc)


def dev_enabled() -> bool:
    """SEARCH_DEV_SIM=1: serve the fixtures. Off unless asked for."""
    return os.environ.get(DEV_ENV, "").strip().lower() in ("1", "on", "true", "yes")


# ---------------------------------------------------------------------------
# Cleaning and filtering (pure functions)
# ---------------------------------------------------------------------------

def clean_text(value) -> str:
    """Plain text: tags and control characters out, entities decoded once, whitespace collapsed."""
    if value is None:
        return ""
    s = html.unescape(_TAG.sub(" ", str(value)))
    s = _TAG.sub(" ", s)           # entities that decoded into tags
    s = _CONTROL.sub("", s)
    return _SPACES.sub(" ", s).strip()


def truncate(text: str, limit: int) -> str:
    """At most `limit` characters; a longer text is cut at a word end where possible and ends with an ellipsis."""
    if len(text) <= limit:
        return text
    cut = text[:limit - 1].rstrip()
    space = cut.rfind(" ")
    if space >= limit // 2:
        cut = cut[:space].rstrip(" ,.;:-،؛")
    return cut + "…"


def domain_of(value) -> str:
    """The bare host of a URL or domain ("https://www.Example.org/a?b" -> "example.org"), or "" when it
    does not look like a host. Never a path, query, port or credentials."""
    if not value:
        return ""
    raw = str(value).strip()
    try:
        parts = urlsplit(raw if "//" in raw else "//" + raw)
        host = (parts.hostname or "").lower().rstrip(".")
    except ValueError:
        return ""
    if host.startswith("www."):
        host = host[4:]
    if not host or len(host) > DOMAIN_MAX or not _HOST.match(host):
        return ""
    return host


def query_is_blocked(query) -> bool:
    return content_guard.looks_like_scripture(clean_text(query))


def _pick(raw: dict, *names):
    for n in names:
        if n in raw and raw[n] not in (None, ""):
            return raw[n]
    return None


def clean_result(raw) -> dict | None:
    """One provider result -> {"t","d","s"}, or None when it must not be shown (no title, no real domain,
    or it trips the scripture check)."""
    if not isinstance(raw, dict):
        return None
    title = clean_text(_pick(raw, "t", "title", "name"))
    snippet = clean_text(_pick(raw, "s", "snippet", "description", "content", "body"))
    domain = domain_of(_pick(raw, "d", "domain", "url", "link", "href", "displayed_url"))
    if not title or not domain:
        return None
    if content_guard.looks_like_scripture(title) or content_guard.looks_like_scripture(snippet) \
            or content_guard.looks_like_scripture(domain):
        return None
    return {"t": truncate(title, TITLE_MAX), "d": domain, "s": truncate(snippet, SNIPPET_MAX)}


def filter_results(raw_results, used=None):
    """(shown results, hl): at most MAX_RESULTS cleaned results in provider order, and the index in the shown
    list of the provider's `used` result (0 when unknown or dropped)."""
    shown, hl = [], 0
    if not isinstance(raw_results, Iterable) or isinstance(raw_results, (str, bytes, dict)):
        return shown, hl
    for ix, raw in enumerate(raw_results):
        if len(shown) >= MAX_RESULTS:
            break
        cleaned = clean_result(raw)
        if cleaned is None:
            continue
        if used is not None and ix == used:
            hl = len(shown)
        shown.append(cleaned)
    return shown, hl


def _lang_code(value) -> str:
    return "en" if str(value or "").lower().startswith("en") else "ar"


def build_searching(sid: str, query, lang, kind="web", grownup=False, fixture=False) -> dict:
    msg = {"v": VERSION, "id": sid, "st": "searching", "kind": kind,
           "q": "" if grownup else truncate(clean_text(query), QUERY_MAX), "lang": _lang_code(lang)}
    if grownup:
        msg["gu"] = 1
    if fixture:
        msg["fx"] = 1
    return msg


def build_results(sid: str, shown: list, hl: int, fixture=False) -> dict:
    msg = {"v": VERSION, "id": sid, "st": "results", "r": shown, "hl": hl}
    if fixture:
        msg["fx"] = 1
    return msg


def build_none(sid: str, grownup=False, fixture=False) -> dict:
    msg = {"v": VERSION, "id": sid, "st": "none"}
    if grownup:
        msg["gu"] = 1
    if fixture:
        msg["fx"] = 1
    return msg


# ---------------------------------------------------------------------------
# The publisher
# ---------------------------------------------------------------------------

class SearchPublisher:
    """Publishes `al.search` into a LiveKit room. One per session. Never raises."""

    def __init__(self, room, lang: Callable[[], str] | None = None, safety_flagged: Callable[[], bool] | None = None):
        """room: the livekit room (local_participant.publish_data).
        lang: callable returning the session language ("ar", "en", ...).
        safety_flagged: callable, True when a safety concern was flagged in this turn."""
        self._room = room
        self._lang = lang
        self._safety = safety_flagged
        self._n = 0
        self._grownup: dict[str, bool] = {}
        self._fixture: dict[str, bool] = {}

    # -- pieces ---------------------------------------------------------------

    def _language(self) -> str:
        try:
            return _lang_code(self._lang() if self._lang else "ar")
        except Exception:
            return "ar"

    def _flagged(self) -> bool:
        try:
            return bool(self._safety()) if self._safety else False
        except Exception:
            return True  # when in doubt, show nothing

    async def _send(self, message: dict) -> bool:
        try:
            payload = json.dumps(message, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            await self._room.local_participant.publish_data(payload, reliable=True, topic=TOPIC)
            return True
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            _log_once("publish", "al.search: publish_data failed.", exc=exc)
            return False

    async def start(self, query, kind="web", *, fixture=False) -> str:
        """Send "searching" and return the search id. Sends the neutral grown-up card's first half (no query
        text) when the query trips the check or a safety concern was flagged this turn."""
        self._n += 1
        sid = "S%d" % self._n
        grownup = query_is_blocked(query) or self._flagged()
        self._grownup[sid] = grownup
        self._fixture[sid] = bool(fixture)
        for stale in list(self._grownup)[:-8]:
            self._grownup.pop(stale, None)
            self._fixture.pop(stale, None)
        await self._send(build_searching(sid, query, self._language(), kind, grownup=grownup, fixture=fixture))
        return sid

    async def results(self, sid: str, raw_results, used=None) -> int:
        """Send the results of search `sid` (filtered) or "none". Returns how many cards were shown."""
        fixture = self._fixture.get(sid, False)
        if self._grownup.get(sid) or self._flagged():
            await self._send(build_none(sid, grownup=True, fixture=fixture))
            return 0
        try:
            shown, hl = filter_results(raw_results, used)
        except Exception as exc:
            _log_once("filter", "al.search: could not read the results.", exc=exc)
            shown, hl = [], 0
        if not shown:
            await self._send(build_none(sid, fixture=fixture))
            return 0
        await self._send(build_results(sid, shown, hl, fixture=fixture))
        return len(shown)

    async def none(self, sid: str) -> None:
        await self._send(build_none(sid, grownup=self._grownup.get(sid, False), fixture=self._fixture.get(sid, False)))

    async def search(self, query, provider, kind="web", used=None, timeout: float = DEFAULT_TIMEOUT_S) -> int:
        """The whole flow: searching, the provider call, results or none. `provider` is an async callable
        (query, lang) -> list of result dicts and must declare `safe_search = True` (strict safe search).
        Returns the number of cards shown (0 for none or the grown-up card)."""
        fixture = bool(getattr(provider, "is_fixture", False))
        sid = await self.start(query, kind, fixture=fixture)
        if self._grownup.get(sid):
            await self._send(build_none(sid, grownup=True, fixture=fixture))
            return 0
        if getattr(provider, "safe_search", False) is not True:
            _log_once("safe-search", "al.search: the provider does not declare strict safe search, not used.")
            await self.none(sid)
            return 0
        try:
            raw = await asyncio.wait_for(provider(clean_text(query), self._language()), timeout)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            _log_once("provider", "al.search: the search provider failed.", exc=exc)
            await self.none(sid)
            return 0
        if isinstance(raw, tuple) and len(raw) == 2 and isinstance(raw[1], int):
            raw, used = raw
        return await self.results(sid, raw, used)


# ---------------------------------------------------------------------------
# The dev / simulated source: FIXTURES, not a search
# ---------------------------------------------------------------------------

# Kid-safe fixtures for the demo and the tests. They are written here, they are not the result of any
# search, and every message built from them carries "fx":1. No religious text, no names, no links.
# The domains end in .example (reserved, can never resolve).
DEV_FIXTURES = {
    "bees": {
        "keys": ("bee", "honey", "نحل", "عسل"),
        "en": [
            ("How bees make honey", "kids-nature.example", "Bees collect nectar from flowers and carry it back to the hive, where it slowly turns into honey."),
            ("Why bees dance", "science-for-kids.example", "A bee can tell its friends where the flowers are by moving in a little figure of eight."),
            ("Bees and flowers", "garden-club.example", "When a bee visits a flower it carries pollen, and that helps new flowers and fruit to grow."),
            ("A day in the hive", "kids-nature.example", "Some bees clean, some build, some feed the babies and some fly out to find nectar."),
        ],
        "ar": [
            ("كيف تصنع النحلة العسل", "kids-nature.example", "تجمع النحلة رحيق الزهور وتحمله إلى الخلية وهناك يتحول إلى عسل."),
            ("لماذا ترقص النحلة", "science-for-kids.example", "تخبر النحلة صديقاتها أين توجد الزهور برقصة صغيرة على شكل رقم ثمانية."),
            ("النحل والزهور", "garden-club.example", "حين تزور النحلة زهرة تنقل اللقاح فتنبت زهور وثمار جديدة."),
        ],
    },
    "moon": {
        "keys": ("moon", "night sky", "قمر", "القمر"),
        "en": [
            ("Why the moon changes shape", "space-for-kids.example", "The moon does not make its own light. We see the part that the sun is shining on."),
            ("How far away is the moon", "science-for-kids.example", "The moon is about as far as thirty earths side by side."),
            ("Moon facts for children", "kids-nature.example", "The moon takes about a month to travel once around the earth."),
        ],
        "ar": [
            ("لماذا يتغير شكل القمر", "space-for-kids.example", "القمر لا يصنع ضوئه بنفسه ونحن نرى الجزء الذي تضيئه الشمس."),
            ("كم يبعد القمر عنا", "science-for-kids.example", "يبعد القمر مثل ثلاثين كرة أرضية موضوعة بجانب بعض."),
            ("معلومات عن القمر للأطفال", "kids-nature.example", "يدور القمر حول الأرض مرة كل شهر تقريبا."),
        ],
    },
    "rain": {
        "keys": ("rain", "cloud", "weather", "مطر", "سحاب"),
        "en": [
            ("How rain is made", "weather-for-kids.example", "The sun warms the sea, the water rises as vapour, turns into clouds and falls again as rain."),
            ("Why clouds float", "science-for-kids.example", "A cloud is made of tiny drops that are so light the air can hold them up."),
            ("Rainbows after the rain", "weather-for-kids.example", "A rainbow appears when sunlight passes through tiny drops of water."),
        ],
        "ar": [
            ("كيف ينزل المطر", "weather-for-kids.example", "تسخن الشمس البحر فيصعد الماء بخارا ثم يصير سحابا ثم ينزل مطرا."),
            ("لماذا تطفو السحاب", "science-for-kids.example", "السحابة قطرات صغيرة خفيفة يحملها الهواء."),
            ("قوس قزح بعد المطر", "weather-for-kids.example", "يظهر قوس القزح حين تمر أشعة الشمس في قطرات الماء."),
        ],
    },
    "generic": {
        "keys": (),
        "en": [
            ("Amazing facts about nature", "kids-nature.example", "Plants, animals and weather are full of surprises that are fun to discover."),
            ("Fun science for children", "science-for-kids.example", "Easy experiments and clear answers to the questions children ask most."),
            ("Questions kids ask", "learn-together.example", "Short, friendly answers you can read together with a grown-up."),
        ],
        "ar": [
            ("حقائق ممتعة عن الطبيعة", "kids-nature.example", "النباتات والحيوانات والطقس مليئة بمفاجآت ممتعة."),
            ("علوم ممتعة للأطفال", "science-for-kids.example", "تجارب سهلة وإجابات واضحة عن أكثر أسئلة الأطفال."),
            ("أسئلة يسألها الأطفال", "learn-together.example", "إجابات قصيرة ولطيفة تقرأها مع أحد الكبار."),
        ],
    },
}


def _fixture_for(query: str) -> dict:
    q = clean_text(query).lower()
    for name, entry in DEV_FIXTURES.items():
        if any(k in q for k in entry["keys"]):
            return entry
    return DEV_FIXTURES["generic"]


class DevSearchProvider:
    """The simulated source: returns the fixture page for a query. `is_fixture` makes every message carry
    "fx":1. Declares safe_search because it serves only the kid-safe fixtures above."""

    safe_search = True
    is_fixture = True

    def __init__(self, delay_s: float = 0.0):
        self._delay = delay_s

    async def __call__(self, query, lang="en"):
        if self._delay:
            await asyncio.sleep(self._delay)
        rows = _fixture_for(query)["en" if _lang_code(lang) == "en" else "ar"]
        return [{"title": t, "url": "https://" + d + "/", "snippet": s} for t, d, s in rows]


ProviderType = Callable[[str, str], Awaitable[list]]
