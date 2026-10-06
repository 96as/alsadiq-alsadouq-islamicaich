"""Word-anchored gesture planning for the avatar (BEHAVIOUR-SPEC 3.1-3.3, work package W1).

What it does
- GesturePlanner.segment() is called once per tts_node call (one text segment of one speech).
- GestureSegment.tap_text(text) wraps the text stream that goes to the TTS. Every chunk is yielded
  FIRST and untouched; only afterwards is it appended to a buffer. When a clause boundary, 90
  characters without one, or the end of the stream is reached, the clause is planned with the T1
  model (gesture_runtime.py, pure standard library, about 0.5 ms per clause). Planning runs in the
  gap after a chunk has been handed on, never before it. No await, no lock, no I/O, no LLM call.
- The plan is, per segment word ordinal, the closed-inventory gesture events and the sentence
  events (talk style and expression). LipsyncTimeline.tap(frames, plan=segment) then asks
  GestureSegment.take(word_ix, word_norm) for every timed word the TTS reports and puts the events
  into the lk.lipsync packet that holds the word's first character (messages g and u, see
  lipsync_timeline.py).
- A clause that is planned only after its words were already published is sent as a late
  g-only message (never carries t) through the sink the timeline binds.

Safety rules kept here (spec 1.1, 1.7, 4.4)
- Only the closed inventory is ever emitted; anything else is dropped. Offering gestures never take
  the left hand.
- A clause that looks like scripture (a meta-word, or heavily vowelled Arabic) gets no gesture and no
  sentence event: the avatar stays neutral while it is read.
- A safety hint from the agent forces the gentle style.
- No scripture text lives in this module, its data or its tests.

Failure rule: nothing in here may break the voice. Every failure is logged once, the segment goes
quiet and the text and frames keep flowing.

Flag: GESTURE_EVENTS. On by default (lead decision); GESTURE_EVENTS=0 (or off/false/no) is the off
switch. The events can only travel on the timeline, so the caller still needs LIPSYNC_TIMELINE on as well.
"""
from __future__ import annotations

import logging
import os
import random
import re
import time
import unicodedata
import zlib
from collections import OrderedDict, deque

from conversation.agent import content_guard

logger = logging.getLogger(__name__)

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(HERE, "data", "gesture_model.json")

# The closed id inventory (spec appendix B). Anything else is dropped.
SEMANTIC_IDS = ("you", "me", "heart", "wide", "small", "list", "shrug", "wow", "idea", "beckon", "clap", "cheer",
                "think", "ask", "present", "calm", "round", "up", "hug")
INVENTORY = frozenset(SEMANTIC_IDS) | frozenset(("beat", "nod", "shake", "tilt", "greet", "wave", "bye"))
HEAD_IDS = {"H_Nod": "nod", "H_Shake": "shake", "H_Tilt": "tilt"}
GENTLE_IDS = frozenset(("heart", "calm", "me", "you", "hug"))   # the gentle style's set (spec 2.7)
TALK_STYLES = ("explain", "story", "praise", "question", "gentle")
EXPRESSIONS = ("neutral", "happy", "proud", "soft", "excited", "curious", "surprised")

MAX_CLAUSE_CHARS = 90
RECENT_SENTENCES = 2
_SPEECHES_KEPT = 8
_SEEN_KEPT = 12                 # ordinals remembered for a late plan
_ORDINAL_SEARCH = (0, -1, 1, -2, 2)
_TILT_GAP = 3                   # two tilts closer than this many words are one
_OFF_VALUES = ("0", "off", "false", "no")

_BOUNDARY = re.compile("[.!?؟,،;:—؛…][\"')\\]»”’]*(?=\\s)|\\n")
_SENT_END = re.compile("[.!?؟…]+[\"')\\]»”’]*\\s*$")
_WS = re.compile(r"\s")

_logged: set[str] = set()


def _log_once(key: str, message: str, *args, exc: BaseException | None = None) -> None:
    if key in _logged:
        return
    _logged.add(key)
    logger.warning(message, *args, exc_info=exc)


def enabled() -> bool:
    """GESTURE_EVENTS, default ON (0/off/false/no turns it off, see the module docstring)."""
    return os.environ.get("GESTURE_EVENTS", "").strip().lower() not in _OFF_VALUES


# ---------------------------------------------------------------------------
# Word text, the same on both sides of the join
# ---------------------------------------------------------------------------

def word_norm(text) -> str:
    """The key a planned token and a timed word must share: edge punctuation off, T1 normalisation."""
    try:
        from conversation.agent import gesture_runtime as rt
        return rt.normalize(rt._EDGE.sub("", str(text)))
    except Exception:
        return str(text).strip().lower()


def word_len(text, available: int | None = None) -> int:
    """Length of a timed word in items, without trailing spaces and punctuation (at least 1)."""
    s = str(text)
    end = len(s)
    while end > 1:
        ch = s[end - 1]
        if ch.isspace() or unicodedata.category(ch)[0] in ("P", "Z", "S"):
            end -= 1
        else:
            break
    if available is not None:
        end = min(end, available)
    return max(1, end)


def _clamp_k(k, default=2) -> int:
    try:
        return max(1, min(3, int(k)))
    except Exception:
        return default


# ---------------------------------------------------------------------------
# The plan of one segment
# ---------------------------------------------------------------------------

class _Entry:
    __slots__ = ("norm", "g", "u", "taken")

    def __init__(self, norm):
        self.norm = norm
        self.g = []        # [(id, k, h)]
        self.u = []        # [(talk_style, expression)]
        self.taken = False


class _SpeechState:
    """What survives across the segments of one speech."""
    __slots__ = ("rng", "recent", "last_hand", "hint", "praise", "safety", "last_style", "clauses")

    def __init__(self, rng, hint, praise, safety):
        self.rng = rng
        self.recent = deque(maxlen=RECENT_SENTENCES)   # ids used per sentence, newest last
        self.last_hand = ""
        self.hint = hint
        self.praise = praise
        self.safety = safety
        self.last_style = None
        self.clauses = 0

    def used_ids(self):
        return tuple(i for sentence in self.recent for i in sentence)


class GestureSegment:
    """One tts_node call. Created by GesturePlanner.segment(); never raises."""

    def __init__(self, planner, state: _SpeechState, lang_code: str):
        self._planner = planner
        self._state = state
        self._lang = lang_code
        self._buf = ""
        self._planned = 0                     # tokens planned so far (the next clause's ordinal offset)
        self._entries: dict[int, _Entry] = {}
        self._pending = deque()               # keys of untaken entries, ascending
        self._seen: dict[int, tuple] = {}     # ordinal -> (norm, ci, n) of words published before their plan
        self._sink = None
        self._sentence_start = True
        self._dead = False
        self.stats = {"clauses": 0, "events": 0, "delivered": 0, "late": 0, "dropped": 0, "skipped": 0}

    # -- the text path ----------------------------------------------------

    async def tap_text(self, text):
        """Yield every chunk of `text` unchanged, first; then buffer and plan. Adds no await of its own."""
        try:
            async for chunk in text:
                yield chunk
                self._feed(chunk)
            self._finish()
        finally:
            close = getattr(text, "aclose", None)
            if close is not None:
                await close()

    def _feed(self, chunk) -> None:
        if self._dead or not isinstance(chunk, str):
            return
        try:
            self._buf += chunk
            self._drain(final=False)
        except Exception as exc:
            self._fail("feed", exc)

    def _finish(self) -> None:
        if self._dead:
            return
        try:
            self._drain(final=True)
        except Exception as exc:
            self._fail("finish", exc)

    def _fail(self, key, exc) -> None:
        self._dead = True
        self._buf = ""
        _log_once("segment-" + key, "gesture planner: %s failed, this segment has no gesture events.", key, exc=exc)

    def _drain(self, final: bool) -> None:
        while True:
            m = _BOUNDARY.search(self._buf)
            if m is not None:
                clause, self._buf = self._buf[:m.end()], self._buf[m.end():]
            elif len(self._buf) >= MAX_CLAUSE_CHARS:
                cut = -1
                for i in range(len(self._buf) - 1, 0, -1):
                    if self._buf[i].isspace():
                        cut = i
                        break
                if cut <= 0:
                    break
                clause, self._buf = self._buf[:cut], self._buf[cut:]
            else:
                break
            self._plan_clause(clause)
        if final:
            rest, self._buf = self._buf, ""
            if rest.strip():
                self._plan_clause(rest)

    # -- planning ---------------------------------------------------------

    def _plan_clause(self, clause: str) -> None:
        toks = clause.split()
        if not toks:
            return
        offset = self._planned
        self._planned += len(toks)
        new_sentence = self._sentence_start
        self._sentence_start = bool(_SENT_END.search(clause))
        planner = self._planner
        if planner.model is None:
            return
        st = self._state
        if content_guard.looks_like_scripture(clause):
            self.stats["skipped"] += 1
            return
        started = time.perf_counter()
        try:
            produced = planner._events_for(clause, toks, st, self._lang, new_sentence)
        except Exception as exc:
            _log_once("plan", "gesture planner: planning a clause failed, it has no gesture events.", exc=exc)
            return
        finally:
            planner._note_ms((time.perf_counter() - started) * 1000.0)
        self.stats["clauses"] += 1
        fresh = []
        for ix, norm, g, u in produced:
            if not norm:
                continue
            e = self._entries.get(offset + ix)
            if e is None:
                e = _Entry(norm)
                self._entries[offset + ix] = e
                self._pending.append(offset + ix)
                fresh.append(offset + ix)
            e.g.extend(g)
            e.u.extend(u)
            self.stats["events"] += len(g) + len(u)
        if self._seen and self._sink is not None and fresh:
            self._send_late(fresh)
        for key in [k for k in self._seen if k < self._planned - _SEEN_KEPT]:
            del self._seen[key]

    def _send_late(self, keys) -> None:
        late_g, late_u = [], []
        for key in keys:
            e = self._entries[key]
            for d in _ORDINAL_SEARCH:
                seen = self._seen.get(key + d)
                if seen is not None and seen[0] == e.norm:
                    del self._seen[key + d]
                    e.taken = True
                    _, ci, n = seen
                    late_g.extend([ci, n, i, k, h] for i, k, h in e.g)
                    late_u.extend([ci, s, x] for s, x in e.u)
                    self.stats["late"] += len(e.g) + len(e.u)
                    break
        if late_g or late_u:
            try:
                self._sink(late_g, late_u)
            except Exception as exc:
                _log_once("late-sink", "gesture planner: could not send a late plan.", exc=exc)

    # -- the frame path (called by LipsyncTimeline.tap) --------------------

    def bind_sink(self, sink) -> None:
        """sink(g_events, u_events): the timeline's way to send a g-only message for this speech."""
        self._sink = sink

    def take(self, word_ix: int, norm: str):
        """The events planned for the timed word at segment ordinal `word_ix` whose normalised text is
        `norm`: ([(id, k, h)], [(talk_style, expression)]) or None. Search +-2 ordinals for the same text."""
        entries = self._entries
        if not entries:
            return None
        self._expire(word_ix)
        if not norm:
            return None
        for d in _ORDINAL_SEARCH:
            e = entries.get(word_ix + d)
            if e is not None and not e.taken and e.norm == norm:
                e.taken = True
                self.stats["delivered"] += len(e.g) + len(e.u)
                return e.g, e.u
        return None

    def note_word(self, word_ix: int, norm: str, ci: int, n: int) -> None:
        """A timed word went out without events. If its clause is not planned yet, remember it so a late
        plan can still reach it."""
        if word_ix >= self._planned and norm:
            self._seen[word_ix] = (norm, ci, n)

    def _expire(self, word_ix: int) -> None:
        pending = self._pending
        while pending and pending[0] < word_ix - 2:
            key = pending.popleft()
            e = self._entries.get(key)
            if e is not None and not e.taken:
                e.taken = True
                self.stats["dropped"] += len(e.g) + len(e.u)
                _log_once("mismatch", "gesture planner: a planned word did not match the spoken word, "
                                      "its events were dropped.")

    @property
    def planned_tokens(self) -> int:
        return self._planned


# ---------------------------------------------------------------------------
# The planner (one per agent)
# ---------------------------------------------------------------------------

class GesturePlanner:
    """Owns the model and the per-speech state. See the module docstring."""

    def __init__(self, model="auto", *, lang=None, speech_id=None, seed=None, mode=None):
        """model: a gesture_runtime.GestureModel, None (planner off) or "auto" (load data/gesture_model.json,
            lexicon fallback when it is missing).
        lang: optional callable returning the session language ("ar", "en", "en-US"...).
        speech_id: optional callable returning the id of the speech being generated.
        seed: optional int; with it the per-speech rng is the same on every run (tests).
        mode: None (the model's own mode), "model" or "lexicon"."""
        self._lang = lang
        self._speech_id = speech_id
        self._seed = seed
        self._mode = mode
        self._speeches: OrderedDict[str, _SpeechState] = OrderedDict()
        self._hint = {"talk_style": None, "praise": False, "safety": False}
        self.plan_ms: deque = deque(maxlen=512)
        self.model = self._load() if model == "auto" else model

    @staticmethod
    def _load():
        try:
            from conversation.agent import gesture_runtime as rt
            return rt.GestureModel.load(MODEL_PATH)
        except Exception as exc:
            _log_once("load", "gesture planner: the model could not be loaded, no gesture events.", exc=exc)
            return None

    @property
    def available(self) -> bool:
        return self.model is not None

    # -- hints from the agent / the signals branch --------------------------

    def set_hints(self, talk_style=None, praise=False, safety=False) -> None:
        """Hints for the NEXT speech (they are taken once, when its first segment starts): the reply's talk
        style (from AvatarSignals), and the praise and safety flags."""
        self._hint = {"talk_style": talk_style if talk_style in TALK_STYLES else None,
                      "praise": bool(praise), "safety": bool(safety)}

    # -- segments ----------------------------------------------------------

    def segment(self):
        """A GestureSegment for one tts_node call, or None when planning is off. Never raises."""
        try:
            if self.model is None:
                return None
            sp = self._current_speech_id()
            state = self._speeches.get(sp)
            if state is None:
                state = self._new_state(sp)
            else:
                self._speeches.move_to_end(sp)
            return GestureSegment(self, state, self._lang_code())
        except Exception as exc:
            _log_once("segment", "gesture planner: could not start a segment.", exc=exc)
            return None

    def _new_state(self, sp: str) -> _SpeechState:
        key = "%s|%s" % (self._seed, sp) if self._seed is not None else sp
        hint, self._hint = self._hint, {"talk_style": None, "praise": False, "safety": False}
        state = _SpeechState(random.Random(zlib.crc32(key.encode("utf-8"))),
                             hint["talk_style"], hint["praise"], hint["safety"])
        self._speeches[sp] = state
        while len(self._speeches) > _SPEECHES_KEPT:
            self._speeches.popitem(last=False)
        return state

    def _current_speech_id(self) -> str:
        try:
            if self._speech_id is not None:
                value = self._speech_id()
                if value:
                    return str(value)
            else:
                from livekit.agents.voice.agent_activity import _SpeechHandleContextVar

                handle = _SpeechHandleContextVar.get(None)
                if handle is not None:
                    return str(handle.id)
        except Exception:
            pass
        return "?"

    def _lang_code(self) -> str:
        try:
            value = self._lang() if self._lang else "ar"
        except Exception:
            value = "ar"
        return "en" if str(value or "").lower().startswith("en") else "ar"

    def _note_ms(self, ms: float) -> None:
        self.plan_ms.append(ms)

    def p99_ms(self) -> float:
        data = sorted(self.plan_ms)
        if not data:
            return 0.0
        return data[min(len(data) - 1, int(len(data) * 0.99))]

    # -- one clause -> events -----------------------------------------------

    def _events_for(self, clause, toks, st: _SpeechState, lang, new_sentence):
        """[(token index, norm, [(id, k, h)], [(talk_style, expression)])] for a clause."""
        if new_sentence:
            hint = "gentle" if st.safety else ("praise" if st.praise and st.clauses == 0 else st.hint)
        else:
            hint = st.last_style or st.hint
        plan = self.model.plan(clause, lang=lang, talk_style_hint=hint, used_ids=st.used_ids(), mode=self._mode)
        st.clauses += 1
        n = len(toks)
        by_ix: dict[int, list] = {}

        def slot(i):
            return by_ix.setdefault(i, [[], []])

        sentences = plan.get("sentences") or []
        starts = [(s["start"], s["talk_style"], s["expression"]) for s in sentences]

        def style_at(i):
            style = None
            for start, ts, _ex in starts:
                if start <= i:
                    style = ts
            return style or hint or "explain"

        used_here = []
        occupied = set()
        for a in plan.get("anchors") or []:
            i, gid = a.get("i"), a.get("id")
            if not isinstance(i, int) or not 0 <= i < n or gid not in INVENTORY or gid == "beat":
                continue
            if st.safety and gid in SEMANTIC_IDS and gid not in GENTLE_IDS:
                continue                     # a safety turn is gentle: only its gestures (spec 2.7)
            k = 1 if st.safety else _clamp_k(a.get("k"), 2)
            h = a.get("hand") or ""
            if h == "L":
                h = "R"                      # offering gestures never take the left hand (spec 1.1)
            slot(i)[0].append((gid, k, h if h in ("R", "B") else ""))
            occupied.add(i)
            if gid in SEMANTIC_IDS:
                used_here.append(gid)
        for b in plan.get("beats") or []:
            i = b.get("i")
            if st.safety or not isinstance(i, int) or not 0 <= i < n or i in occupied:
                continue                     # gentle has no beats (spec 2.7)
            slot(i)[0].append(("beat", _clamp_k(b.get("k"), 1), self._beat_hand(st, style_at(i))))
        last_tilt = -99
        for hd in plan.get("head") or []:
            i, gid = hd.get("i"), HEAD_IDS.get(hd.get("id"))
            if not isinstance(i, int) or not 0 <= i < n or gid is None:
                continue
            if gid == "tilt":
                if i - last_tilt < _TILT_GAP:
                    continue
                last_tilt = i
            slot(i)[0].append((gid, 2, ""))
        for k, (start, ts, ex) in enumerate(starts):
            if k == 0 and not new_sentence:
                st.last_style = ts if ts in TALK_STYLES else st.last_style
                continue
            if not isinstance(start, int) or not 0 <= start < n:
                continue
            if st.safety:
                ts, ex = "gentle", "soft"
            if ts not in TALK_STYLES or ex not in EXPRESSIONS:
                continue
            slot(start)[1].append((ts, ex))
            st.last_style = ts
        if new_sentence:
            st.recent.append(used_here)
        elif st.recent:
            st.recent[-1].extend(used_here)
        elif used_here:
            st.recent.append(used_here)
        out = []
        for i in sorted(by_ix):
            g, u = by_ix[i]
            out.append((i, word_norm(toks[i]), g, u))
        return out

    @staticmethod
    def _beat_hand(st: _SpeechState, style: str) -> str:
        """Beat hands R 0.45, L 0.35, Both 0.20 (story prefers Both); never the same variant twice in a
        row except R (spec 2.5.5)."""
        weights = (("R", 0.35), ("L", 0.25), ("B", 0.40)) if style == "story" else \
            (("R", 0.45), ("L", 0.35), ("B", 0.20))
        for _ in range(4):
            r = st.rng.random()
            acc = 0.0
            pick = weights[-1][0]
            for hand, w in weights:
                acc += w
                if r < acc:
                    pick = hand
                    break
            if pick == "R" or pick != st.last_hand:
                break
        else:
            pick = "R"  # four draws all repeated the last non-R variant: R keeps the "never twice" rule
        st.last_hand = pick
        return pick

    # -- a dry run for tools, docs and the dev panel -------------------------

    def preview(self, text: str, lang: str = "en") -> list:
        """The events a clause would get, as [{"w": word, "ix": i, "g": [...], "u": [...]}] (no state change
        beyond a throwaway speech). For the handoff, tests and the dev "say a line" box."""
        if self.model is None:
            return []
        st = _SpeechState(random.Random(zlib.crc32(b"preview")), None, False, False)
        toks = text.split()
        if content_guard.looks_like_scripture(text):
            return []
        out = []
        for i, norm, g, u in self._events_for(text, toks, st, lang, True):
            out.append({"ix": i, "w": toks[i], "g": list(g), "u": list(u)})
        return out
