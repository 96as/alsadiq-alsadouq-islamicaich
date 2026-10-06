"""Tests for word-anchored gestures: gesture_planner.py, the g/u events and the g-only late message in
lipsync_timeline.py, the tts_node wiring and the GESTURE_EVENTS flag (BEHAVIOUR-SPEC 3.1-3.6, W1).

Everything runs without livekit or a network: a fake ElevenLabs alignment feeds the real LipsyncTimeline.
No scripture appears here. The placeholder sentences are ordinary vocabulary; the few meta-words in the
content-guard test are the words the guard looks for, not any text.

Run from backend/:  python manage.py test conversation.agent.test_gesture_planner \
    --settings=config.settings_sqlite_test
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import unittest
from types import SimpleNamespace
from unittest import mock

from conversation.agent import content_guard
from conversation.agent import gesture_planner as gp
from conversation.agent import lipsync_timeline as lt
from conversation.agent.test_lipsync_timeline import (
    _Frame, _Room, _TimedString, _agen, _fresh_logs, _fake_default_tts_node,
)
from conversation.agent.test_voice_wiring import _ELEVEN_ENV, _FakeAgent, _WiringBase

# ---------------------------------------------------------------------------
# Fixtures: ordinary sentences, never scripture
# ---------------------------------------------------------------------------

EN_LINES = [
    "Well done! I am so proud of you. Do you want to hear a story about a big whale?",
    "Hello my friend. Let me think for a moment, maybe the moon is round like a ball.",
    "First we mix the colours, then we paint the sky, and last we say thank you.",
]
AR_LINES = [
    "أحسنت يا بطل! أنا فخور فيك وايد.",
    "السلام عليكم يا صديقي. "
    "هل تحب أن نتعلم عن الشمس والقمر اليوم؟",
    "لا، هذا غير صحيح. نعم، أنت على حق.",
]
FIXTURES = EN_LINES + AR_LINES


def _norm(w):
    return gp.word_norm(w)


def _timed_words(text, *, step=60, start=0, skip_chars=()):
    """What the patched ElevenLabs plugin produces for `text`: one word per whitespace token, the text of each
    running up to the next word (so with its trailing space), every word carrying its characters. Times count
    from 0 for the call (one tts_node call is one ElevenLabs context). Words in `skip_chars` (ordinals) get
    no `char_ms`."""
    words = []
    pos = 0
    t = start
    ix = 0
    for m in re.finditer(r"\S+\s*", text):
        w = _TimedString(m.group(0))
        if ix not in skip_chars:
            w.char_ms = [(c, t + i * step, step) for i, c in enumerate(m.group(0))]
        t += len(m.group(0)) * step
        words.append(w)
        ix += 1
    return words


def _frames_for(text, per_frame=3, **kw):
    words = _timed_words(text, **kw)
    out = []
    for i in range(0, len(words), per_frame):
        group = words[i:i + per_frame]
        ms = sum(len(w) for w in group) * 0.06
        out.append(_Frame(ms, group))
    return out


async def _chunks(*parts):
    for p in parts:
        yield p


def _split_stream(text, size=7):
    return [text[i:i + size] for i in range(0, len(text), size)]


class _Stub:
    """A model double: plan() returns what `fn(text, kw)` says, in the gesture_runtime result shape."""

    mode = "stub"

    def __init__(self, fn):
        self.fn = fn
        self.calls = []

    def plan(self, text, **kw):
        self.calls.append((text, kw))
        return self.fn(text, kw)


def _plan(text, anchors=(), sentences=((0, "explain", "neutral"),), beats=(), head=()):
    """A gesture_runtime-shaped plan. Indices are clause-relative and out-of-range ones are ignored."""
    toks = text.split()
    n = len(toks)
    anchors = [a for a in anchors if a[0] < n]
    beats = [b for b in beats if b[0] < n]
    head = [h for h in head if h[0] < n]
    sentences = [x for x in sentences if x[0] < n]
    return {
        "tokens": toks,
        "sentences": [{"start": s, "talk_style": st, "expression": ex, "conf": 1.0} for s, st, ex in sentences],
        "anchors": [{"i": i, "w": toks[i], "id": gid, "k": k, "conf": 1.0, "combo": None, "hand": h}
                    for i, gid, k, h in anchors],
        "beats": [{"i": i, "w": toks[i], "k": k} for i, k in beats],
        "head": [{"i": i, "id": hid} for i, hid in head],
        "mode": "stub", "reason": None,
    }


def _by_word(wanted, beats=(), head=(), sentences=None):
    """A stub plan function that anchors by WORD (so it does not depend on where the planner cuts clauses).
    wanted: {normalised word: (id, k, hand)}; beats/head: sets of normalised words; sentences: callable(clause)
    -> [(start, talk_style, expression)] or None for one neutral explain sentence."""
    def fn(text, kw):
        toks = text.split()
        norms = [gp.word_norm(t) for t in toks]
        anchors = [(i, *wanted[w][:1], wanted[w][1], wanted[w][2]) for i, w in enumerate(norms) if w in wanted]
        sent = sentences(text) if sentences else [(0, "explain", "neutral")]
        return _plan(text, anchors=anchors, sentences=sent,
                     beats=[(i, 1) for i, w in enumerate(norms) if w in beats],
                     head=[(i, "H_Tilt") for i, w in enumerate(norms) if w in head])
    return fn


def _planner(model="auto", sp="speech_1", **kw):
    kw.setdefault("seed", 7)
    return gp.GesturePlanner(model, speech_id=lambda: sp, **kw)


class _Run:
    """One speech through the real LipsyncTimeline with a fake alignment."""

    def __init__(self, planner, sp="speech_1", lang="en"):
        self.planner = planner
        self.sp = sp
        self.room = _Room()
        self.tl = lt.LipsyncTimeline(self.room, lang=lambda: lang, speech_id=lambda: sp)

    async def segment(self, text, *, text_chunks=None, frame_kw=None, frames=None):
        seg = self.planner.segment()
        spoken = []
        async for chunk in seg.tap_text(_chunks(*(text_chunks or _split_stream(text)))):
            spoken.append(chunk)
        frames = frames if frames is not None else _frames_for(text, **(frame_kw or {}))
        out = [f async for f in self.tl.tap(_agen(*frames), plan=seg)]
        await self.tl.flush()
        return seg, "".join(spoken), out

    def messages(self):
        return self.room.messages()


def reconstruct(messages, sp="speech_1"):
    """items of one speech (every `t` in seq order) and each g/u event with the packet that carried it."""
    items = []
    events_g, events_u = [], []
    for m in messages:
        if m.get("sp") != sp or "t" not in m:
            continue
        first = len(items)
        items.extend(m["t"])
        for e in m.get("g", []):
            events_g.append((e, first, first + len(m["t"])))
        for e in m.get("u", []):
            events_u.append((e, first, first + len(m["t"])))
    return items, events_g, events_u


def spoken_word(items, ci, n):
    return "".join(x[0] for x in items[ci:ci + n])


# ---------------------------------------------------------------------------
# The text path
# ---------------------------------------------------------------------------

class TextTapTests(unittest.IsolatedAsyncioTestCase):
    async def test_chunks_pass_through_unchanged_and_in_order(self):
        planner = _planner()
        text = EN_LINES[0]
        chunks = _split_stream(text, 5)
        got = [c async for c in planner.segment().tap_text(_chunks(*chunks))]
        self.assertEqual(got, chunks)

    async def test_the_tap_adds_no_await_of_its_own(self):
        """Driven by hand: a source that never suspends makes every step of tap_text finish in one send()."""
        planner = _planner()
        seg = planner.segment()
        chunks = _split_stream(EN_LINES[0] + " ", 6)
        gen = seg.tap_text(_chunks(*chunks))
        got = []
        for _ in range(len(chunks)):
            coro = gen.__anext__()
            try:
                coro.send(None)
            except StopIteration as stop:
                got.append(stop.value)
            else:
                self.fail("tap_text suspended: it added an await")
        self.assertEqual(got, chunks)
        coro = gen.__anext__()
        with self.assertRaises(StopAsyncIteration):
            try:
                coro.send(None)
            except StopIteration:
                self.fail("the end of the stream did not raise StopAsyncIteration")
        self.assertGreater(seg.stats["clauses"], 0)

    async def test_a_chunk_is_handed_on_before_it_is_planned(self):
        log = []

        def fn(text, kw):
            log.append(("plan", text))
            return _plan(text)

        planner = _planner(_Stub(fn))
        seg = planner.segment()
        chunks = ["Well ", "done! ", "I am ", "proud. ", "Bye."]
        async for chunk in seg.tap_text(_chunks(*chunks)):
            log.append(("recv", chunk))
        # "done! " completes the first clause only once the following whitespace is seen, and the plan call comes
        # after the consumer already holds the chunk that ended it.
        self.assertLess(log.index(("recv", "done! ")), log.index(("plan", "Well done!")))
        self.assertLess(log.index(("recv", "proud. ")), log.index(("plan", " I am proud.")))
        self.assertEqual([x for x in log if x[0] == "plan"][-1], ("plan", " Bye."))

    async def test_clauses_are_cut_at_punctuation_at_90_chars_and_at_the_end(self):
        clauses = []
        planner = _planner(_Stub(lambda t, kw: clauses.append(t) or _plan(t)))
        long_run = " ".join(["word"] * 40)  # 199 characters, no punctuation
        text = "Hello, my friend. " + long_run
        seg = planner.segment()
        async for _ in seg.tap_text(_chunks(*_split_stream(text, 9))):
            pass
        self.assertEqual(clauses[0].strip(), "Hello,")
        self.assertEqual(clauses[1].strip(), "my friend.")
        for c in clauses[2:-1]:
            self.assertLessEqual(len(c), 100)  # cut at the last space once 90 characters are buffered
        self.assertEqual("".join(clauses).split(), text.split())  # nothing lost, nothing doubled, no cut word

    async def test_a_decimal_point_does_not_split_a_word(self):
        clauses = []
        planner = _planner(_Stub(lambda t, kw: clauses.append(t) or _plan(t)))
        seg = planner.segment()
        async for _ in seg.tap_text(_chunks("It is 3.5 metres high.")):
            pass
        self.assertEqual(clauses, ["It is 3.5 metres high."])

    async def test_planner_exceptions_never_break_the_text(self):
        def boom(text, kw):
            raise RuntimeError("model blew up")

        _fresh_logs()
        gp._logged.clear()
        planner = _planner(_Stub(boom))
        chunks = _split_stream(EN_LINES[0], 8)
        got = [c async for c in planner.segment().tap_text(_chunks(*chunks))]
        self.assertEqual(got, chunks)

    async def test_a_failing_buffer_step_silences_the_segment_but_not_the_text(self):
        planner = _planner()
        seg = planner.segment()
        with mock.patch.object(gp.GestureSegment, "_drain", side_effect=RuntimeError("x")):
            got = [c async for c in seg.tap_text(_chunks("a ", "b. ", "c "))]
        self.assertEqual(got, ["a ", "b. ", "c "])

    async def test_closing_the_tapped_text_closes_the_source(self):
        closed = []

        async def source():
            try:
                yield "Hello "
                yield "there "
            finally:
                closed.append(True)

        gen = _planner().segment().tap_text(source())
        await gen.__anext__()
        await gen.aclose()
        self.assertEqual(closed, [True])

    async def test_non_text_chunks_are_passed_on(self):
        planner = _planner()
        got = [c async for c in planner.segment().tap_text(_chunks("a ", 5, "b. "))]
        self.assertEqual(got, ["a ", 5, "b. "])


# ---------------------------------------------------------------------------
# g and u on the packets
# ---------------------------------------------------------------------------

class PacketEventTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        _fresh_logs()
        gp._logged.clear()

    async def test_g_lands_on_the_first_character_of_its_word_english(self):
        text = "Well done I am proud of you."
        fn = _by_word({"done": ("clap", 3, "B"), "of": ("heart", 2, "R")}, beats={"am"},
                      sentences=lambda c: [(0, "praise", "proud")])
        run = _Run(_planner(_Stub(fn)))
        await run.segment(text)
        items, gs, us = reconstruct(run.messages())
        self.assertEqual("".join(x[0] for x in items), text)
        by_id = {e[2]: e for e, _a, _b in gs}
        self.assertEqual(set(by_id), {"clap", "heart", "beat"})
        for gid, word in (("clap", "done"), ("heart", "of"), ("beat", "am")):
            e = by_id[gid]
            self.assertEqual(spoken_word(items, e[0], e[1]), word)
        self.assertEqual((by_id["clap"][3], by_id["clap"][4]), (3, "B"))
        self.assertEqual(us[0][0], [0, "praise", "proud"])

    async def test_ci_is_the_item_index_in_arabic_and_english_across_two_segments(self):
        for lang, lines in (("en", EN_LINES), ("ar", AR_LINES)):
            with self.subTest(lang=lang):
                seg_texts = [lines[0], lines[1]]

                def fn(t, kw):
                    toks = t.split()
                    return _plan(t, anchors=[(i, "you", 2, "R") for i in range(0, len(toks), 2)])

                run = _Run(_planner(_Stub(fn), sp="sp_" + lang), sp="sp_" + lang, lang=lang)
                for text in seg_texts:
                    await run.segment(text)
                items, gs, us = reconstruct(run.messages(), "sp_" + lang)
                self.assertGreater(len(gs), 6)
                joined = "".join(x[0] for x in items)
                self.assertEqual(joined, seg_texts[0] + seg_texts[1])
                first_len = len(seg_texts[0])
                second_norms = {gp.word_norm(x) for x in seg_texts[1].split()}
                for e, lo, hi in gs:
                    ci, n = e[0], e[1]
                    self.assertTrue(lo <= ci < hi, "the event rides in the packet that holds its anchor")
                    word = spoken_word(items, ci, n)
                    self.assertTrue(word.strip() and not word[-1].isspace(), repr(word))
                    # ci is the word's FIRST item: the item before it is a space or the start of a segment
                    self.assertTrue(ci == 0 or ci == first_len or joined[ci - 1].isspace(), (ci, word))
                    if ci >= first_len:  # the index kept counting across the two segments
                        self.assertIn(gp.word_norm(word), second_norms)
                self.assertTrue(any(e[0] >= first_len for e, _a, _b in gs))

    async def test_events_go_in_the_packet_of_their_anchor_when_packets_split(self):
        words = ["word%d" % i for i in range(60)]  # 60 words of 6-7 chars: well over 120 items
        text = " ".join(words) + "."
        wanted = {w: ("present", 2, "R") for w in ("word0", "word17", "word18", "word19", "word20", "word38", "word59")}
        run = _Run(_planner(_Stub(_by_word(wanted))))
        await run.segment(text, frame_kw={"per_frame": 7})
        msgs = [m for m in run.messages() if "t" in m]
        self.assertGreater(len(msgs), 3)
        self.assertEqual([m["seq"] for m in msgs], list(range(len(msgs))))
        items, gs, _ = reconstruct(run.messages())
        self.assertEqual(len(gs), 7)
        for e, lo, hi in gs:
            self.assertTrue(lo <= e[0] < hi)
        self.assertEqual([spoken_word(items, e[0], e[1]) for e, _a, _b in gs], list(wanted))
        self.assertGreater(len({(lo, hi) for _e, lo, hi in gs}), 3, "the events spread over several packets")

    async def test_the_u_event_rides_on_the_first_word_of_the_sentence(self):
        text = "Hello my friend. How are you today?"

        def sentences(clause):
            return [(0, "explain", "happy")] if clause.strip().startswith("Hello") else [(0, "question", "curious")]

        run = _Run(_planner(_Stub(_by_word({}, sentences=sentences))))
        await run.segment(text)
        items, _g, us = reconstruct(run.messages())
        events = [e for e, _a, _b in us]
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0][1:], ["explain", "happy"])
        self.assertEqual(spoken_word(items, events[0][0], 5), "Hello")
        self.assertEqual(events[1][1:], ["question", "curious"])
        self.assertEqual(spoken_word(items, events[1][0], 3), "How")

    async def test_a_word_without_characters_still_counts_in_word_ix(self):
        text = "one two three four five"

        def fn(t, kw):
            return _plan(t, anchors=[(3, "wide", 2, "B")])

        run = _Run(_planner(_Stub(fn)))
        await run.segment(text, frames=_frames_for(text, skip_chars=(1,)))
        items, gs, _ = reconstruct(run.messages())
        self.assertEqual(len(gs), 1)
        e = gs[0][0]
        self.assertEqual(spoken_word(items, e[0], e[1]), "four")

    async def test_one_word_can_carry_a_semantic_gesture_and_a_head_gesture(self):
        text = "What do you think?"

        def fn(t, kw):
            return _plan(t, anchors=[(3, "ask", 2, "R")], head=[(3, "H_Tilt")], sentences=[(0, "question", "curious")])

        run = _Run(_planner(_Stub(fn)))
        await run.segment(text)
        _items, gs, _ = reconstruct(run.messages())
        self.assertEqual([e[2] for e, _a, _b in gs], ["ask", "tilt"])
        self.assertEqual(gs[0][0][0], gs[1][0][0])

    async def test_word_text_off_by_one_ordinal_is_found_by_the_plus_minus_two_search(self):
        text = "alpha beta gamma delta epsilon"
        spoken = "alpha extra beta gamma delta epsilon"  # the TTS reports one more word than the plan saw

        def fn(t, kw):
            return _plan(t, anchors=[(2, "up", 2, "R")])

        run = _Run(_planner(_Stub(fn)))
        await run.segment(text, frames=_frames_for(spoken))
        items, gs, _ = reconstruct(run.messages())
        self.assertEqual(len(gs), 1)
        e = gs[0][0]
        self.assertEqual(spoken_word(items, e[0], e[1]), "gamma")

    async def test_a_word_that_does_not_match_anywhere_is_dropped_and_logged_once(self):
        text = "alpha beta gamma delta epsilon zeta eta"
        spoken = "alpha beta other things in the way here"

        def fn(t, kw):
            return _plan(t, anchors=[(2, "up", 2, "R"), (3, "wide", 2, "B")])

        gp._logged.clear()
        run = _Run(_planner(_Stub(fn)))
        with self.assertLogs(gp.logger, level="WARNING") as logs:
            seg, _t, _o = await run.segment(text, frames=_frames_for(spoken))
        _items, gs, _ = reconstruct(run.messages())
        self.assertEqual(gs, [])
        self.assertEqual(seg.stats["dropped"], 2)
        self.assertEqual(len([r for r in logs.records if "did not match" in r.getMessage()]), 1)

    async def test_old_packets_are_unchanged_without_a_plan(self):
        run = _Run(_planner())
        await run.tl.flush()
        out = [f async for f in run.tl.tap(_agen(*_frames_for("hello there")))]
        await run.tl.flush()
        for m in run.messages():
            self.assertEqual(set(m), {"v", "sp", "seq", "lang", "t"})
        self.assertEqual(len(out), 1)

    async def test_the_events_do_not_change_the_t_items(self):
        text = EN_LINES[0]
        with_plan = _Run(_planner())
        await with_plan.segment(text)
        plain = _Run(_planner())
        plain_out = [f async for f in plain.tl.tap(_agen(*_frames_for(text)))]
        await plain.tl.flush()
        self.assertEqual([m["t"] for m in with_plan.messages() if "t" in m],
                         [m["t"] for m in plain.messages() if "t" in m])
        self.assertEqual(len(plain_out), len(_frames_for(text)))

    async def test_frames_are_yielded_unchanged_with_a_plan(self):
        frames = _frames_for(EN_LINES[1])
        run = _Run(_planner())
        seg = run.planner.segment()
        async for _ in seg.tap_text(_chunks(*_split_stream(EN_LINES[1]))):
            pass
        out = [f async for f in run.tl.tap(_agen(*frames), plan=seg)]
        self.assertEqual(len(out), len(frames))
        for a, b in zip(out, frames):
            self.assertIs(a, b)

    async def test_a_plan_that_raises_in_take_never_breaks_the_frames(self):
        frames = _frames_for(EN_LINES[1])
        run = _Run(_planner())
        seg = run.planner.segment()
        async for _ in seg.tap_text(_chunks(*_split_stream(EN_LINES[1]))):
            pass
        with mock.patch.object(gp.GestureSegment, "take", side_effect=RuntimeError("boom")):
            out = [f async for f in run.tl.tap(_agen(*frames), plan=seg)]
        await run.tl.flush()
        self.assertEqual(len(out), len(frames))
        items, gs, _ = reconstruct(run.messages())
        self.assertEqual(gs, [])
        self.assertTrue(items)  # the lip sync itself still went out


# ---------------------------------------------------------------------------
# The late plan
# ---------------------------------------------------------------------------

class LatePlanTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        _fresh_logs()
        gp._logged.clear()

    async def test_a_clause_planned_after_its_words_went_out_is_a_g_only_message(self):
        text = "Well done I am proud of you."
        fn = _by_word({"done": ("clap", 3, "B")}, sentences=lambda c: [(0, "praise", "proud")])
        run = _Run(_planner(_Stub(fn)))
        seg = run.planner.segment()
        out = [f async for f in run.tl.tap(_agen(*_frames_for(text)), plan=seg)]  # frames FIRST: nothing planned yet
        await run.tl.flush()
        before = len(run.messages())
        async for _ in seg.tap_text(_chunks(text)):
            pass
        await run.tl.flush()
        late = run.messages()[before:]
        self.assertTrue(late)
        for m in late:
            self.assertNotIn("t", m)
            self.assertNotIn("seq", m)
            self.assertEqual(m["sp"], "speech_1")
            self.assertEqual(m["v"], 1)
        items, _g, _u = reconstruct(run.messages())
        events = [e for m in late for e in m.get("g", [])]
        self.assertEqual(len(events), 1)
        self.assertEqual(spoken_word(items, events[0][0], events[0][1]), "done")
        self.assertEqual(events[0][2:], ["clap", 3, "B"])
        sentences = [e for m in late for e in m.get("u", [])]
        self.assertEqual(sentences, [[0, "praise", "proud"]])
        self.assertEqual(seg.stats["late"], 2)

    async def test_the_late_message_never_replaces_a_timeline_in_the_browser_logic(self):
        """TimelineSync.push treats a message with t and no seq as a new timeline: a late message has neither."""
        text = "Look at this big tree."
        run = _Run(_planner(_Stub(_by_word({"tree": ("up", 2, "R")}))))
        seg = run.planner.segment()
        _ = [f async for f in run.tl.tap(_agen(*_frames_for(text)), plan=seg)]
        async for _ in seg.tap_text(_chunks(text)):
            pass
        await run.tl.flush()
        for m in run.messages():
            self.assertFalse("t" in m and "seq" not in m)

    async def test_a_partly_late_plan_sends_only_the_late_part(self):
        text1, text2 = "Well done! ", "I am proud of you."

        run = _Run(_planner(_Stub(_by_word({"done": ("heart", 2, "R"), "you": ("heart", 2, "R")}))))
        seg = run.planner.segment()
        feeder = seg.tap_text(_chunks(text1, text2))
        await feeder.__anext__()                       # "Well done! " handed on, planning pending
        await feeder.__anext__()                       # now the first clause is planned (on time for frames later)
        frames = _frames_for(text1 + text2)
        _ = [f async for f in run.tl.tap(_agen(*frames), plan=seg)]
        with self.assertRaises(StopAsyncIteration):
            await feeder.__anext__()                   # end of stream: the last clause is planned LATE
        await run.tl.flush()
        msgs = run.messages()
        in_packet = [e for m in msgs if "t" in m for e in m.get("g", [])]
        late = [e for m in msgs if "t" not in m for e in m.get("g", [])]
        items, _g, _u = reconstruct(msgs)
        self.assertEqual([spoken_word(items, e[0], e[1]) for e in in_packet], ["done"])
        self.assertEqual([spoken_word(items, e[0], e[1]) for e in late], ["you"])

    async def test_a_failing_late_sink_is_logged_and_the_text_continues(self):
        seg = _planner().segment()
        seg.bind_sink(mock.Mock(side_effect=RuntimeError("down")))
        seg._seen[0] = ("done", 4, 4)
        got = [c async for c in seg.tap_text(_chunks("done "))]
        self.assertEqual(got, ["done "])


# ---------------------------------------------------------------------------
# The model, the policy and the guards
# ---------------------------------------------------------------------------

class PlanningTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        gp._logged.clear()

    def test_the_t1_model_loads_from_data_and_is_the_model_not_the_fallback(self):
        planner = gp.GesturePlanner()
        self.assertTrue(planner.available)
        self.assertEqual(planner.model.mode, "model")
        self.assertTrue(os.path.exists(gp.MODEL_PATH))

    def test_a_missing_model_file_falls_back_to_the_lexicon(self):
        with mock.patch.object(gp, "MODEL_PATH", os.path.join(gp.HERE, "data", "nope.json")):
            planner = gp.GesturePlanner()
        self.assertTrue(planner.available)
        self.assertEqual(planner.model.mode, "lexicon")
        self.assertTrue(planner.preview("Well done! I am proud of you.", "en"))

    def test_a_planner_without_a_model_makes_no_segments(self):
        self.assertIsNone(gp.GesturePlanner(None).segment())

    def test_only_inventory_ids_are_emitted_and_forbidden_ones_never_fire(self):
        def fn(t, kw):
            return _plan(t, anchors=[(0, "point_at_child", 2, "R"), (1, "thumbs_up", 2, "R"), (2, "ok_circle", 2, "R"),
                                     (3, "temple_tap", 2, "R"), (4, "beckon_palm_up", 2, "R"), (5, "clap", 2, "B")],
                         head=[(0, "H_Dip"), (1, "H_Bad")])

        planner = _planner(_Stub(fn))
        events = planner.preview("a b c d e f", "en")
        ids = [g[0] for e in events for g in e["g"]]
        self.assertEqual(ids, ["clap"])
        self.assertTrue(set(ids) <= gp.INVENTORY)

    def test_every_id_the_t1_model_can_emit_is_in_the_inventory(self):
        from conversation.agent import gesture_runtime as rt
        self.assertTrue(set(rt.SEMANTIC) <= gp.INVENTORY)
        self.assertTrue(set(rt.ONESHOT) <= gp.INVENTORY)
        self.assertEqual({gp.HEAD_IDS[h] for h in rt.HEAD}, {"nod", "shake"})

    def test_the_left_hand_never_offers(self):
        def fn(t, kw):
            return _plan(t, anchors=[(0, "present", 2, "L"), (1, "you", 2, "L"), (2, "heart", 2, "L")])

        events = _planner(_Stub(fn)).preview("a b c", "en")
        self.assertEqual([g[2] for e in events for g in e["g"]], ["R", "R", "R"])

    def test_beat_hands_follow_the_policy_and_the_left_hand_is_only_for_beats(self):
        planner = _planner(_Stub(lambda t, kw: _plan(t, beats=[(i, 1) for i in range(40)])))
        events = planner.preview(" ".join("w%d" % i for i in range(40)), "en")
        hands = [e["g"][0][2] for e in events]
        self.assertEqual(set(hands), {"R", "L", "B"})
        for a, b in zip(hands, hands[1:]):
            self.assertFalse(a == b and a != "R")

    def test_a_non_r_beat_never_repeats_even_when_every_redraw_repeats_it(self):
        class _Stuck:
            def random(self):
                return 0.6  # always "L" with the explain weights (R .45, L .35, B .20)

        st = gp._SpeechState(_Stuck(), None, False, False)
        hands = [gp.GesturePlanner._beat_hand(st, "explain") for _ in range(6)]
        self.assertEqual(hands, ["L", "R", "L", "R", "L", "R"])

    def test_a_beat_is_never_on_a_word_that_has_a_gesture(self):
        planner = _planner(_Stub(lambda t, kw: _plan(t, anchors=[(1, "clap", 2, "B")], beats=[(1, 1), (2, 1)])))
        events = [e for e in planner.preview("a b c", "en") if e["g"]]
        self.assertEqual([(e["ix"], [g[0] for g in e["g"]]) for e in events], [(1, ["clap"]), (2, ["beat"])])

    def test_two_tilts_close_together_are_one(self):
        planner = _planner(_Stub(lambda t, kw: _plan(t, head=[(3, "H_Tilt"), (4, "H_Tilt"), (9, "H_Tilt")])))
        events = planner.preview("a b c d e f g h i j", "en")
        self.assertEqual([e["ix"] for e in events if e["g"]], [3, 9])

    async def test_a_clause_that_looks_like_scripture_gets_no_events(self):
        """Meta-words only (the guard looks for the words that name such a text); no such text is here."""
        planner = _planner()
        for text, first_clause_words in (("This is about a surah. Listen carefully.", 5),
                                         ("The hadith says something. Well done!", 4)):
            seg = planner.segment()
            async for _ in seg.tap_text(_chunks(text)):
                pass
            self.assertEqual(seg.stats["skipped"], 1, text)
            self.assertFalse([k for k in seg._entries if k < first_clause_words], text)
            self.assertTrue(seg._entries, "the clause after it is still planned")

    def test_a_heavily_vowelled_clause_gets_no_events(self):
        word = "كَتَبَ"
        text = " ".join([word] * 6) + "."
        self.assertEqual(_planner().preview(text, "ar"), [])

    async def test_a_safety_hint_forces_the_gentle_style(self):
        planner = _planner(_Stub(lambda t, kw: _plan(t, sentences=[(0, "praise", "excited")])))
        planner.set_hints(safety=True)
        seg = planner.segment()
        async for _ in seg.tap_text(_chunks("Well done! ")):
            pass
        self.assertEqual(seg._entries[0].u, [("gentle", "soft")])
        self.assertEqual(planner.model.calls[0][1]["talk_style_hint"], "gentle")

    async def test_a_safety_turn_keeps_only_gentle_gestures_at_k1_and_no_beats(self):
        def fn(t, kw):
            return _plan(t, sentences=[(0, "praise", "excited")], beats=[(3, 2)], head=[(4, "H_Nod")],
                         anchors=[(0, "clap", 3, "B"), (1, "heart", 3, "R"), (2, "wow", 2, "B")])

        planner = _planner(_Stub(fn))
        planner.set_hints(safety=True)
        seg = planner.segment()
        async for _ in seg.tap_text(_chunks("a b c d e. ")):
            pass
        got = {k: e.g for k, e in seg._entries.items() if e.g}
        self.assertEqual(got, {1: [("heart", 1, "R")], 4: [("nod", 2, "")]})
        # without the safety hint the same plan keeps everything
        planner = _planner(_Stub(fn))
        seg = planner.segment()
        async for _ in seg.tap_text(_chunks("a b c d e. ")):
            pass
        self.assertEqual(sorted(g[0] for e in seg._entries.values() for g in e.g),
                         ["beat", "clap", "heart", "nod", "wow"])

    async def test_the_reply_talk_style_is_the_hint_and_is_taken_once(self):
        stub = _Stub(lambda t, kw: _plan(t))
        planner = _planner(stub, sp="speech_a")
        planner.set_hints(talk_style="story")
        seg = planner.segment()
        async for _ in seg.tap_text(_chunks("Once upon a time there was a fox. It was clever. ")):
            pass
        self.assertEqual(stub.calls[0][1]["talk_style_hint"], "story")
        # the next speech does not inherit it
        planner._speech_id = lambda: "speech_b"
        seg = planner.segment()
        async for _ in seg.tap_text(_chunks("Hello. ")):
            pass
        self.assertIsNone(stub.calls[-1][1]["talk_style_hint"])

    async def test_ids_of_the_last_two_sentences_are_passed_for_novelty(self):
        stub = _Stub(lambda t, kw: _plan(t, anchors=[(0, "wide", 2, "B")]) if t.strip().startswith("Big")
                     else _plan(t, anchors=[(0, "round", 2, "B")]))
        planner = _planner(stub)
        seg = planner.segment()
        async for _ in seg.tap_text(_chunks("Big sky. Round moon. Big sea. Round sun. Last one.")):
            pass
        used = [kw["used_ids"] for _t, kw in stub.calls]
        self.assertEqual(used[0], ())
        self.assertEqual(used[1], ("wide",))
        self.assertEqual(used[2], ("wide", "round"))
        self.assertEqual(used[3], ("round", "wide"))  # only the last two sentences
        self.assertEqual(used[4], ("wide", "round"))

    async def test_a_continuation_clause_inherits_the_sentence_style_and_sends_no_new_u(self):
        stub = _Stub(lambda t, kw: _plan(t, sentences=[(0, "story", "happy")]))
        planner = _planner(stub)
        seg = planner.segment()
        async for _ in seg.tap_text(_chunks("Long ago, in a far away land, there lived a fox. ")):
            pass
        us = [(k, e.u) for k, e in sorted(seg._entries.items()) if e.u]
        self.assertEqual(len(us), 1)           # only the first clause of the sentence announces its style
        self.assertEqual(us[0][0], 0)
        self.assertEqual(stub.calls[1][1]["talk_style_hint"], "story")


class DeterminismAndBudgetTests(unittest.IsolatedAsyncioTestCase):
    async def _events(self, seed, sp="speech_x"):
        run = _Run(_planner(sp=sp, seed=seed), sp=sp)
        for text in (EN_LINES[0], EN_LINES[2]):
            await run.segment(text)
        return [m for m in run.messages()]

    async def test_same_seed_same_speech_same_messages(self):
        a = await self._events(5)
        b = await self._events(5)
        self.assertEqual(a, b)

    async def test_a_different_seed_changes_the_beat_hands(self):
        words = ["w%d" % i for i in range(30)]
        fn = _by_word({}, beats=set(words))
        outs = []
        for seed in (1, 2, 3, 4):
            planner = gp.GesturePlanner(_Stub(fn), speech_id=lambda: "s", seed=seed)
            seg = planner.segment()
            async for _ in seg.tap_text(_chunks(" ".join(words) + ".")):
                pass
            outs.append(tuple(seg._entries[i].g[0][2] for i in sorted(seg._entries)))
        self.assertEqual(len(outs[0]), 30)
        self.assertEqual(len(set(outs)), 4)
        self.assertEqual(await self._events(1), await self._events(1))

    async def test_the_p99_budget_is_2_ms_per_clause(self):
        planner = _planner()
        lines = [t for t in FIXTURES for _ in range(40)]
        seg_planner = planner
        for text in lines:  # warm
            seg_planner.preview(text, "en")
        seg_planner.plan_ms.clear()
        for k, text in enumerate(lines):
            planner._speech_id = lambda k=k: "sp%d" % (k % 6)
            seg = planner.segment()
            async for _ in seg.tap_text(_chunks(text)):
                pass
        self.assertGreater(len(planner.plan_ms), 300)
        self.assertLessEqual(planner.p99_ms(), 2.0, "p99 %.2f ms" % planner.p99_ms())


# ---------------------------------------------------------------------------
# A recorded fake session with the REAL T1 model
# ---------------------------------------------------------------------------

class RealModelSessionTests(unittest.IsolatedAsyncioTestCase):
    """Whole speeches (several text segments each) through the real model and the real timeline: every g/u
    event must sit on the first item of a word of the spoken text, in the packet that holds it."""

    async def _speech(self, lang, segments, sp):
        planner = _planner(sp=sp, seed=11, lang=lambda: lang)
        run = _Run(planner, sp=sp, lang=lang)
        for text in segments:
            await run.segment(text)
        return run

    async def test_every_event_lands_on_a_real_word_of_the_speech_en_and_ar(self):
        speeches = {"en": [EN_LINES[0] + " ", EN_LINES[1] + " ", EN_LINES[2]],
                    "ar": [AR_LINES[0] + " ", AR_LINES[1] + " ", AR_LINES[2]]}
        for lang, segments in speeches.items():
            with self.subTest(lang=lang):
                run = await self._speech(lang, segments, "real_" + lang)
                items, gs, us = reconstruct(run.messages(), "real_" + lang)
                joined = "".join(x[0] for x in items)
                self.assertEqual(joined, "".join(segments))
                self.assertGreater(len(gs), 5)
                self.assertGreater(len(us), 2)
                word_starts = {m.start() for m in re.finditer(r"\S+", joined)}
                for e, lo, hi in gs + us:
                    self.assertIn(e[0], word_starts, e)
                    self.assertTrue(lo <= e[0] < hi)
                for e, _lo, _hi in gs:
                    ci, n, gid, k, h = e
                    self.assertIn(gid, gp.INVENTORY)
                    self.assertIn(k, (1, 2, 3))
                    self.assertIn(h, ("R", "L", "B", ""))
                    if gid in gp.SEMANTIC_IDS:
                        self.assertNotEqual(h, "L", e)
                    self.assertTrue(spoken_word(items, ci, n).strip(), e)
                for e, _lo, _hi in us:
                    self.assertIn(e[1], gp.TALK_STYLES)
                    self.assertIn(e[2], gp.EXPRESSIONS)
                # the message stream itself is well formed
                for m in run.messages():
                    self.assertEqual(m["v"], 1)
                    if "t" in m:
                        self.assertIn("seq", m)

    async def test_the_known_cases_of_the_t1_model(self):
        run = await self._speech("en", ["Well done! ", "Hello my friend."], "known_en")
        items, gs, us = reconstruct(run.messages(), "known_en")
        by = {(spoken_word(items, e[0], e[1]), e[2]) for e, _a, _b in gs}
        self.assertIn(("done", "clap"), by)
        self.assertTrue(("Hello", "wave") in by or ("Hello", "greet") in by, by)
        self.assertEqual(us[0][0][1], "praise")
        self.assertIn(us[0][0][2], ("proud", "excited", "happy"))
        run = await self._speech("ar", ["السلام عليكم يا صديقي."], "known_ar")
        _items, gs, _us = reconstruct(run.messages(), "known_ar")
        self.assertIn("greet", [e[2] for e, _a, _b in gs])


# ---------------------------------------------------------------------------
# Fixtures, flag, content guard
# ---------------------------------------------------------------------------

class FixtureAndGuardTests(unittest.TestCase):
    def test_no_scripture_in_any_fixture(self):
        for text in FIXTURES:
            self.assertFalse(content_guard.looks_like_scripture(text), text)

    def test_no_scripture_in_the_planner_data(self):
        fallback = json.load(open(os.path.join(gp.HERE, "lexicon_fallback.json"), encoding="utf-8"))
        fallback.pop("note", None)  # prose that says "no scripture or verse anywhere"
        self.assertFalse(content_guard.has_meta_word(json.dumps(fallback, ensure_ascii=False)))
        self.assertFalse(content_guard.heavily_vowelled(json.dumps(fallback, ensure_ascii=False)))
        data = json.load(open(gp.MODEL_PATH, encoding="utf-8"))
        lexicon_data = dict(data["lexicon"])
        lexicon_data.pop("note", None)
        lexicon = json.dumps(lexicon_data, ensure_ascii=False)
        self.assertFalse(content_guard.has_meta_word(lexicon))
        self.assertFalse(content_guard.heavily_vowelled(lexicon))

    def test_the_guard_flags_meta_words_and_vowelled_text_and_spares_ordinary_words(self):
        for bad in ("a surah", "the hadith", "two verses", "Qur'an time", "tafsir", "سورة قصيرة",
                    "الحديث الشريف", "قال رسول الله",
                    "بالآيات", "كَتَبَ الوَلَدُ"):
            self.assertTrue(content_guard.looks_like_scripture(bad), bad)
        for ok in ("universe", "reverse the song", "the sun is round", "بداية جميلة",
                   "إيه هذا حلو", "نهاية القصة", ""):
            self.assertFalse(content_guard.looks_like_scripture(ok), ok)

    def test_the_flag(self):
        # Unset is ON; 0/off/false/no is the off switch. (The timeline requirement is the entrypoint's.)
        cases = [({}, True), ({"LIPSYNC_TIMELINE": "1"}, True), ({"GESTURE_EVENTS": "1"}, True),
                 ({"GESTURE_EVENTS": "0"}, False), ({"GESTURE_EVENTS": "off"}, False),
                 ({"GESTURE_EVENTS": "false"}, False), ({"GESTURE_EVENTS": "no"}, False)]
        for env, want in cases:
            with self.subTest(env=env), mock.patch.dict(os.environ, env, clear=True):
                self.assertIs(gp.enabled(), want)

    def test_word_helpers(self):
        self.assertEqual(gp.word_norm("done! "), "done")
        self.assertEqual(gp.word_norm("«Hello,» "), "hello")
        self.assertEqual(gp.word_len("done! "), 4)
        self.assertEqual(gp.word_len("اليوم؟ "), 5)
        self.assertEqual(gp.word_len("..."), 1)
        self.assertEqual(gp.word_len("abc", 2), 2)


# ---------------------------------------------------------------------------
# The agent wiring
# ---------------------------------------------------------------------------

class WiringTests(_WiringBase):
    def setUp(self):
        super().setUp()
        p = mock.patch.object(_FakeAgent.default, "tts_node", staticmethod(_fake_default_tts_node), create=True)
        p.start()
        self.addCleanup(p.stop)

    async def run_with_env(self, **env):
        env = {k: v for k, v in env.items() if v is not None}
        with mock.patch.dict(os.environ, env):
            with mock.patch.object(lt, "install_char_timing_patch", return_value=True):
                return await self.run_entrypoint()

    async def test_gestures_are_on_by_default_with_the_timeline(self):
        await self.run_with_env(LIPSYNC_TIMELINE="1")
        self.assertIsInstance(self.agent._gestures, gp.GesturePlanner)
        self.assertIsInstance(self.agent._lipsync, lt.LipsyncTimeline)

    async def test_gesture_events_one_with_the_timeline_turns_gestures_on(self):
        await self.run_with_env(LIPSYNC_TIMELINE="1", GESTURE_EVENTS="1")
        self.assertIsInstance(self.agent._gestures, gp.GesturePlanner)
        self.assertEqual(self.agent._gestures.model.mode, "model")

    async def test_gesture_events_zero_turns_only_the_gestures_off(self):
        await self.run_with_env(LIPSYNC_TIMELINE="1", GESTURE_EVENTS="0")
        self.assertIsNone(self.agent._gestures)
        self.assertIsInstance(self.agent._lipsync, lt.LipsyncTimeline)

    async def test_no_timeline_no_gestures(self):
        await self.run_with_env(LIPSYNC_TIMELINE="0")
        self.assertIsNone(self.agent._gestures)
        self.assertIsNone(self.agent._lipsync)

    async def test_a_planner_that_cannot_start_never_stops_the_session(self):
        with mock.patch.object(gp, "GesturePlanner", side_effect=RuntimeError("no model")):
            await self.run_with_env(LIPSYNC_TIMELINE="1")
        self.assertIsNone(self.agent._gestures)
        self.assertIsInstance(self.agent._lipsync, lt.LipsyncTimeline)

    async def test_tts_node_end_to_end_a_fake_session(self):
        """The whole chain: text -> planner -> fake TTS that reports timed words -> timeline -> data packets."""
        await self.run_with_env(LIPSYNC_TIMELINE="1", GESTURE_EVENTS="1")
        agent = self.agent
        room = _Room()
        tl = lt.LipsyncTimeline(room, lang=lambda: "en", speech_id=lambda: "sp_e2e")
        agent.set_lipsync(tl)
        agent.set_gestures(gp.GesturePlanner(speech_id=lambda: "sp_e2e", seed=3))
        spoken_text = EN_LINES[0]

        async def default(a, text, model_settings):
            collected = []
            async for chunk in text:
                collected.append(chunk)
            for frame in _frames_for("".join(collected)):
                yield frame

        with mock.patch.object(_FakeAgent.default, "tts_node", staticmethod(default)):
            out = [f async for f in agent.tts_node(_chunks(*_split_stream(spoken_text)), None)]
        await tl.flush()
        self.assertEqual(len(out), len(_frames_for(spoken_text)))
        items, gs, us = reconstruct(room.messages(), "sp_e2e")
        self.assertEqual("".join(x[0] for x in items), spoken_text)
        self.assertTrue(gs)
        for e, lo, hi in gs:
            self.assertTrue(lo <= e[0] < hi)
            self.assertIn(e[2], gp.INVENTORY)
            self.assertIn(e[3], (1, 2, 3))
            self.assertIn(e[4], ("R", "L", "B", ""))
            self.assertTrue(spoken_word(items, e[0], e[1]).strip())
        self.assertTrue(us)

    async def test_without_a_timeline_the_text_is_not_even_wrapped(self):
        await self.run_with_env()
        self.agent.set_gestures(gp.GesturePlanner(seed=1))
        seen = []

        async def default(a, text, model_settings):
            async for chunk in text:
                seen.append(chunk)
            yield "frame"

        source = _chunks("Hello ")
        with mock.patch.object(_FakeAgent.default, "tts_node", staticmethod(default)):
            out = [f async for f in self.agent.tts_node(source, None)]
        self.assertEqual(out, ["frame"])
        # avatar-integ: the avatar-signals tap wraps the stream, so compare the chunks, not the object
        self.assertEqual(seen, ["Hello "])

    async def test_a_planner_that_cannot_segment_leaves_the_text_untouched(self):
        await self.run_with_env(LIPSYNC_TIMELINE="1")
        planner = gp.GesturePlanner(None)
        self.agent.set_gestures(planner)
        seen = []

        async def default(a, text, model_settings):
            async for chunk in text:
                seen.append(chunk)
            yield "frame"

        source = _chunks("Hello ")
        with mock.patch.object(_FakeAgent.default, "tts_node", staticmethod(default)):
            out = [f async for f in self.agent.tts_node(source, None)]
        self.assertEqual(out, ["frame"])
        # avatar-integ: the avatar-signals tap wraps the stream, so compare the chunks, not the object
        self.assertEqual(seen, ["Hello "])


if __name__ == "__main__":
    unittest.main()
