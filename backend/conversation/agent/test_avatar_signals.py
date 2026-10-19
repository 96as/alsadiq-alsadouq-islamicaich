"""Tests for the avatar signals (conversation/agent/avatar_signals.py).

No livekit is needed: a fake room records every set_attributes call. The module has no
Django or network dependency either. No Quran or hadith text appears here.

Run from backend/:  python manage.py test conversation.agent.test_avatar_signals \
    --settings=config.settings_sqlite_test
"""
from __future__ import annotations

import asyncio
import inspect
import time
import unittest
from types import SimpleNamespace

from conversation.agent import avatar_signals as sig_mod
from conversation.agent.avatar_signals import (
    AvatarSignals,
    classify_listen,
    classify_talk,
    normalize,
)

INITIAL = {
    "al.sig_v": "1", "al.activity": "idle", "al.search_kind": "web", "al.talk_style": "explain",
    "al.reply": "0", "al.listen_style": "neutral", "al.turn": "0",
}


class FakeRoom:
    """Records (time, attributes) for each set_attributes call and checks the key rules."""

    def __init__(self, fail=False):
        self.calls: list[tuple[float, dict]] = []
        self.fail = fail
        self.local_participant = SimpleNamespace(set_attributes=self._set)

    async def _set(self, attributes):
        if self.fail:
            raise RuntimeError("room is gone")
        for key, value in attributes.items():
            assert key.startswith("al.") and not key.startswith("lk."), key
            assert isinstance(value, str) and value != "", (key, value)
        self.calls.append((time.monotonic(), dict(attributes)))

    @property
    def batches(self) -> list[dict]:
        return [attrs for _t, attrs in self.calls]

    def merged(self) -> dict:
        out: dict = {}
        for attrs in self.batches:
            out.update(attrs)
        return out


def make(**kwargs):
    kwargs.setdefault("min_interval", 0.005)
    sig = AvatarSignals(**kwargs)
    room = FakeRoom()
    sig.bind(room)
    return sig, room


async def agen(*chunks):
    for chunk in chunks:
        yield chunk


async def collect(stream) -> list[str]:
    return [piece async for piece in stream]


class NormalizeTests(unittest.TestCase):
    def test_diacritics_and_tatweel_are_stripped(self):
        self.assertEqual(normalize("زَعْلان"), "زعلان")
        self.assertEqual(normalize("حـــزين"), "حزين")

    def test_letter_variants_are_folded(self):
        self.assertEqual(normalize("أإآٱ"), "اااا")
        self.assertEqual(normalize("مدرسة"), "مدرسه")
        self.assertEqual(normalize("على"), "علي")
        self.assertEqual(normalize("مؤمن"), "مومن")
        self.assertEqual(normalize("شيئ"), "شيي")

    def test_apostrophes_case_and_whitespace(self):
        self.assertEqual(normalize("  It’s   OKAY \n now "), "it's okay now")
        self.assertEqual(normalize("‘Yay’"), "'yay'")

    def test_empty_values(self):
        self.assertEqual(normalize(""), "")
        self.assertEqual(normalize(None), "")


class ListenClassifierTests(unittest.TestCase):
    def test_sad_words(self):
        for text in ("أنا حزين اليوم", "انا زعلان من صاحبي", "I feel sad", "I am so scared of tonight",
                     "they bullied me at school", "ضربني ولد في الصف", "ما عندي اصحاب"):
            self.assertEqual(classify_listen(text), "sad", text)

    def test_sad_phrases(self):
        for text in ("everyone hates me and nobody likes me", "ما أحد يحبني", "it was my fault today",
                     "i lied to my mom"):
            self.assertEqual(classify_listen(text), "sad", text)

    def test_excited_words(self):
        for text in ("أنا فرحان جدا", "فزت اليوم في المسابقة", "تخيل وش صار", "guess what happened",
                     "i got full marks", "tomorrow is my birthday", "yay we won"):
            self.assertEqual(classify_listen(text), "excited", text)

    def test_curious_words(self):
        for text in ("ليش السما زرقاء", "كيف تعمل الطائرة", "هل القمر بعيد", "عندي سؤال",
                     "why is the sky blue", "tell me about stars", "what is a volcano"):
            self.assertEqual(classify_listen(text), "curious", text)

    def test_curious_by_question_mark_alone(self):
        self.assertEqual(classify_listen("the moon is far away?"), "curious")
        self.assertEqual(classify_listen("القمر بعيد جدا؟"), "curious")

    def test_neutral(self):
        for text in ("the cat sat on the mat", "اليوم رحنا السوق", ""):
            self.assertEqual(classify_listen(text), "neutral", text)

    def test_priority_is_sad_then_excited_then_curious(self):
        self.assertEqual(classify_listen("why are you sad"), "sad")
        self.assertEqual(classify_listen("i won but i am sad"), "sad")
        self.assertEqual(classify_listen("guess what happened"), "excited")  # "what" is curious too
        self.assertEqual(classify_listen("why is it my birthday"), "excited")

    def test_negation_cancels_sad_and_excited(self):
        self.assertEqual(classify_listen("مو زعلان"), "neutral")
        self.assertEqual(classify_listen("مب خايف"), "neutral")
        self.assertEqual(classify_listen("ما كنت زعلان"), "neutral")  # negator two tokens before
        self.assertEqual(classify_listen("i am not sad at all"), "neutral")
        self.assertEqual(classify_listen("i'm not alone"), "neutral")
        self.assertEqual(classify_listen("مو فرحان"), "neutral")
        self.assertEqual(classify_listen("i am not excited"), "neutral")

    def test_negation_window_is_two_tokens(self):
        self.assertEqual(classify_listen("ما كنت ابدا زعلان"), "sad")
        self.assertEqual(classify_listen("not at all very sad"), "sad")

    def test_no_as_an_answer_does_not_cancel_the_feeling(self):
        # "لا" and "no" are also the answer "no"; they negate only the word right after them.
        for text in ("لا أنا زعلان", "لا، خايف من الظلام", "no i'm scared", "No, I'm sad today"):
            self.assertEqual(classify_listen(text), "sad", text)
        self.assertEqual(classify_listen("لا لا أنا فرحان مرة"), "excited")
        for text in ("لا أخاف", "لا أبكي", "no tears today", "لا مو زعلان", "لا ما أنا زعلان"):
            self.assertEqual(classify_listen(text), "neutral", text)

    def test_negation_does_not_cross_punctuation(self):
        self.assertEqual(classify_listen("Not really, sad."), "sad")
        self.assertEqual(classify_listen("مو مرة، زعلان شوي"), "sad")
        self.assertEqual(classify_listen("مو مرة زعلان"), "neutral")

    def test_negation_does_not_cancel_a_question(self):
        self.assertEqual(classify_listen("why do i not know this"), "curious")

    def test_a_remaining_hit_still_counts(self):
        self.assertEqual(classify_listen("i am not sad but i am scared"), "sad")

    def test_clitic_prefixes_match_when_three_letters_remain(self):
        self.assertEqual(classify_listen("والحزن صعب"), "sad")
        self.assertEqual(classify_listen("بالحزن"), "sad")
        self.assertEqual(classify_listen("وزعل كبير"), "sad")

    def test_clitic_prefix_needs_three_letters(self):
        # "وين" is a question word on its own, but "و" + "ين" must not create other hits.
        self.assertEqual(classify_listen("وين البيت"), "curious")
        self.assertEqual(classify_listen("ولد صغير"), "neutral")

    def test_diacritics_and_spelling_variants(self):
        self.assertEqual(classify_listen("أَنَا زَعْلَان"), "sad")
        self.assertEqual(classify_listen("هديه جميله"), "excited")  # ة typed as ه

    def test_ambiguous_words_stay_out(self):
        self.assertEqual(classify_listen("هذا خطير"), "neutral")
        self.assertEqual(classify_listen("من البيت ما راح"), "neutral")

    def test_two_word_question_forms_count(self):
        self.assertEqual(classify_listen("ما هو الذهب"), "curious")
        self.assertEqual(classify_listen("من هي ماما"), "curious")

    def test_it_is_fast_and_pure(self):
        text = "ليش السما زرقاء وأنا فرحان بس شوي زعلان لأن صاحبي ما لعب معي اليوم " * 3
        start = time.perf_counter()
        for _ in range(200):
            classify_listen(text)
        per_call_ms = (time.perf_counter() - start) * 1000 / 200
        self.assertLess(per_call_ms, 2.0)


class TalkClassifierTests(unittest.TestCase):
    def test_default_is_explain(self):
        self.assertEqual(classify_talk("The sky looks blue because of the air."), "explain")
        self.assertEqual(classify_talk(""), "explain")
        self.assertEqual(classify_talk(None), "explain")

    def test_safety_hint_wins_over_everything(self):
        self.assertEqual(classify_talk("Well done, you are great!", hint_praise=True, hint_safety=True), "gentle")

    def test_praise_by_hint_or_marker(self):
        self.assertEqual(classify_talk("Here is the answer.", hint_praise=True), "praise")
        self.assertEqual(classify_talk("Well done, that was honest."), "praise")
        self.assertEqual(classify_talk("ما شاء الله، أحسنت يا بطل"), "praise")
        self.assertEqual(classify_talk("أنت شاطرة"), "praise")

    def test_praise_outranks_a_sad_child(self):
        self.assertEqual(classify_talk("You were brave, I am proud of you.", listen_style="sad"), "praise")

    def test_gentle_by_marker_or_sad_listen(self):
        self.assertEqual(classify_talk("It's okay, take your time."), "gentle")
        self.assertEqual(classify_talk("لا تحزن، أنا معك"), "gentle")
        self.assertEqual(classify_talk("Let us look at it together.", listen_style="sad"), "gentle")

    def test_story(self):
        self.assertEqual(classify_talk("Once upon a time there was a kind farmer"), "story")
        self.assertEqual(classify_talk("كان يا ما كان في قرية صغيرة"), "story")
        self.assertEqual(classify_talk("في يوم من الأيام ضاع طفل"), "story")

    def test_question_by_mark_or_question_word(self):
        self.assertEqual(classify_talk("Do you like trees?"), "question")
        self.assertEqual(classify_talk("Why do you think he did that"), "question")
        self.assertEqual(classify_talk("هل جربت هذا"), "question")
        self.assertEqual(classify_talk("تحب النجوم؟"), "question")

    def test_good_question_and_exclamations_are_not_asking_back(self):
        # "سؤال حلو" is "good question" (then an explanation); "What a ...!" is an exclamation.
        self.assertEqual(classify_talk("سؤال حلو، الكذب يخلي القلب ثقيل لأن الناس ما يثقون فيك"), "explain")
        self.assertEqual(classify_talk("What a brave thing to do!"), "explain")
        self.assertEqual(classify_talk("كم أنت شجاع!"), "explain")
        self.assertEqual(classify_talk("What do you think happened next?"), "question")
        self.assertEqual(classify_talk("سؤال لك: وش تتوقع صار؟"), "question")  # a real question still counts

    def test_gentle_outranks_story_and_story_outranks_question(self):
        self.assertEqual(classify_talk("It's okay, once upon a time I was scared too"), "gentle")
        self.assertEqual(classify_talk("Once upon a time, who was there?"), "story")

    def test_a_sad_listen_does_not_beat_the_safety_or_praise_rules_order(self):
        self.assertEqual(classify_talk("Nice.", listen_style="sad", hint_safety=True), "gentle")
        self.assertEqual(classify_talk("Bravo!", listen_style="sad"), "praise")

    def test_the_vocabulary_is_closed(self):
        for opening in ("hello there", "Well done", "once upon a time", "why?", "it's okay"):
            self.assertIn(classify_talk(opening), sig_mod.TALK_STYLES)


class ContractTests(unittest.IsolatedAsyncioTestCase):
    async def test_the_initial_batch_is_the_spec_batch(self):
        sig, room = make()
        sig.start()
        await sig.flush()
        self.assertEqual(room.batches, [INITIAL])

    async def test_keys_and_values_follow_the_rules_in_a_full_turn(self):
        sig, room = make()
        sig.start()
        sig.on_child_text("ليش السما زرقاء")
        async with sig.search("library") as s:
            s.found = True
        await collect(sig.tap_reply(agen("Great question, little friend. ")))
        await sig.flush()
        for _t, attrs in room.calls:  # FakeRoom already asserted the rules per call
            self.assertTrue(attrs)
        seen = set().union(*room.batches)
        self.assertTrue(seen <= set(sig_mod._SHORT_TO_KEY.values()))

    async def test_a_turn_costs_at_most_five_calls(self):
        sig, room = make()
        sig.start()
        await sig.flush()
        before = len(room.calls)
        sig.on_child_text("why is the sky blue")  # listen_style + turn
        async with sig.search("library") as s:  # searching, then found
            s.found = True
        await collect(sig.tap_reply(agen("Because of the way light bends in the air. ")))  # talk_style + reply
        await sig.flush()
        self.assertLessEqual(len(room.calls) - before, 5)

    def test_the_module_has_no_scripture_and_no_new_imports(self):
        source = inspect.getsource(sig_mod)
        for char in ("﴿", "﴾", "ﷺ"):
            self.assertNotIn(char, source)
        imported = {line.split()[1].split(".")[0] for line in source.splitlines()
                    if line.startswith(("import ", "from ")) and not line.startswith("from __future__")}
        self.assertTrue(imported <= {"asyncio", "contextlib", "logging", "re", "time", "collections"}, imported)


class PublisherTests(unittest.IsolatedAsyncioTestCase):
    async def test_unchanged_values_are_not_resent_but_counters_are(self):
        sig, room = make()
        sig.update(talk_style="story", reply="1")
        await sig.flush()
        sig.update(talk_style="story", reply="2")
        await sig.flush()
        self.assertEqual(room.batches, [{"al.talk_style": "story", "al.reply": "1"}, {"al.reply": "2"}])

    async def test_bad_values_are_dropped(self):
        sig, room = make()
        sig.update(activity="bogus", talk_style="", listen_style=None, reply="abc", nonsense="x")
        await sig.flush()
        self.assertEqual(room.batches, [])

    async def test_an_unknown_search_kind_falls_back_to_web(self):
        sig, room = make()
        sig.update(search_kind="mars")
        await sig.flush()
        self.assertEqual(room.batches, [{"al.search_kind": "web"}])

    async def test_keys_queued_together_merge_into_one_call(self):
        sig, room = make()
        sig.update(talk_style="story", reply="1")
        sig.update(listen_style="sad", turn="1")
        await sig.flush()
        self.assertEqual(len(room.calls), 1)
        self.assertEqual(room.batches[0], {"al.talk_style": "story", "al.reply": "1",
                                           "al.listen_style": "sad", "al.turn": "1"})

    async def test_activity_changes_are_never_merged_away(self):
        sig, room = make()
        sig.update(activity="searching", search_kind="library")
        sig.update(activity="found")
        await sig.flush()
        self.assertEqual([b["al.activity"] for b in room.batches], ["searching", "found"])
        self.assertEqual(room.batches[0]["al.search_kind"], "library")

    async def test_calls_are_at_least_120ms_apart_by_default(self):
        sig, room = make(min_interval=sig_mod.PUBLISH_MIN_INTERVAL_S)
        sig.update(activity="searching", search_kind="folders")
        sig.update(activity="found")
        sig.update(activity="none")
        await sig.flush()
        self.assertEqual(len(room.calls), 3)
        times = [t for t, _ in room.calls]
        for earlier, later in zip(times, times[1:]):
            self.assertGreaterEqual(later - earlier, 0.115)
        self.assertEqual(sig_mod.PUBLISH_MIN_INTERVAL_S, 0.12)

    async def test_update_never_blocks(self):
        sig, _room = make(min_interval=1.0)
        start = time.perf_counter()
        for i in range(50):
            sig.update(reply=str(i))
        self.assertLess(time.perf_counter() - start, 0.05)
        sig._pump.cancel()  # do not wait a second for the test's sake

    async def test_without_a_room_everything_is_a_no_op(self):
        sig = AvatarSignals(min_interval=0.001)
        sig.start()
        sig.on_child_text("i am so sad today")
        async with sig.search("web") as s:
            s.found = True
        await collect(sig.tap_reply(agen("Hello my friend. ")))
        await sig.flush()  # nothing raised

    async def test_without_a_running_loop_update_is_a_no_op(self):
        sig = AvatarSignals()
        await asyncio.get_running_loop().run_in_executor(None, lambda: sig.update(reply="1"))

    async def test_a_failing_room_is_logged_once_and_never_raises(self):
        sig, room = make()
        room.fail = True
        with self.assertLogs(sig_mod.logger, level="WARNING") as logs:
            sig.update(reply="1")
            await sig.flush()
            sig.update(reply="2")
            await sig.flush()
        self.assertEqual(len(logs.records), 1)  # the second failure is debug level

    async def test_after_a_failure_the_same_value_is_sent_again(self):
        sig, room = make()
        room.fail = True
        with self.assertLogs(sig_mod.logger, level="WARNING"):
            sig.update(listen_style="sad")
            await sig.flush()
        room.fail = False
        sig.update(listen_style="sad")
        await sig.flush()
        self.assertEqual(room.batches, [{"al.listen_style": "sad"}])

    async def test_a_hanging_room_is_timed_out(self):
        sig, room = make()

        async def hang(_attrs):
            await asyncio.sleep(60)

        room.local_participant.set_attributes = hang
        original = sig_mod.PUBLISH_TIMEOUT_S
        sig_mod.PUBLISH_TIMEOUT_S = 0.05
        try:
            with self.assertLogs(sig_mod.logger, level="WARNING"):
                sig.update(reply="1")
                await asyncio.wait_for(sig.flush(), 2)
        finally:
            sig_mod.PUBLISH_TIMEOUT_S = original

    async def test_attach_survives_a_session_that_cannot_subscribe(self):
        sig, _room = make()

        class Bad:
            def on(self, *_a, **_k):
                raise RuntimeError("no events")

        with self.assertLogs(sig_mod.logger, level="WARNING"):
            sig.attach(Bad())


class SearchTests(unittest.IsolatedAsyncioTestCase):
    async def test_found(self):
        sig, room = make()
        async with sig.search("library") as s:
            self.assertEqual(sig._intent["al.activity"], "searching")
            s.found = True
        await sig.flush()
        self.assertEqual([b["al.activity"] for b in room.batches], ["searching", "found"])

    async def test_none_is_the_default_end(self):
        sig, room = make()
        async with sig.search("folders"):
            pass
        await sig.flush()
        self.assertEqual([b["al.activity"] for b in room.batches], ["searching", "none"])
        self.assertEqual(room.batches[0]["al.search_kind"], "folders")

    async def test_an_exception_ends_with_none_and_propagates(self):
        sig, room = make()
        with self.assertRaises(ValueError):
            async with sig.search("library") as s:
                s.found = True
                raise ValueError("boom")
        await sig.flush()
        self.assertEqual([b["al.activity"] for b in room.batches], ["searching", "none"])

    async def test_a_cancelled_search_still_ends(self):
        sig, room = make()

        async def work():
            async with sig.search("web"):
                await asyncio.sleep(60)

        task = asyncio.ensure_future(work())
        await asyncio.sleep(0.01)
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task
        await sig.flush()
        self.assertEqual([b["al.activity"] for b in room.batches], ["searching", "none"])

    async def test_two_searches_in_a_row_each_get_their_transitions(self):
        sig, room = make()
        async with sig.search("library") as s:
            s.found = False
        async with sig.search("library") as s:
            s.found = False
        await sig.flush()
        self.assertEqual([b["al.activity"] for b in room.batches],
                         ["searching", "none", "searching", "none"])

    async def test_overlapping_searches_share_one_signal(self):
        sig, room = make()
        a_done = asyncio.Event()
        b_in = asyncio.Event()

        async def first():
            async with sig.search("library") as s:
                await b_in.wait()
                s.found = False
            a_done.set()

        async def second():
            async with sig.search("folders") as s:
                b_in.set()
                await a_done.wait()
                s.found = True

        await asyncio.gather(first(), second())
        await sig.flush()
        self.assertEqual([b["al.activity"] for b in room.batches], ["searching", "found"])
        self.assertEqual(room.batches[0]["al.search_kind"], "library")
        self.assertEqual(sig._search_depth, 0)

    async def test_the_tools_signal_through_the_box(self):
        # The shape used in agent_class.py: the box is set inside the block.
        sig, room = make()
        rows = ["a quest"]
        async with sig.search("folders") as s:
            s.found = bool(rows)
        await sig.flush()
        self.assertEqual(room.merged()["al.activity"], "found")


class QuickFindTests(unittest.IsolatedAsyncioTestCase):
    def make_clocked(self):
        now = [1000.0]
        sig, room = make(clock=lambda: now[0])
        return sig, room, now

    async def test_it_signals_only_on_a_match(self):
        sig, room, _now = self.make_clocked()
        self.assertFalse(sig.quick_find("library", found=False))
        await sig.flush()
        self.assertEqual(room.batches, [])
        self.assertFalse(sig._last_quick)  # a miss does not start the cooldown

    async def test_a_match_goes_out_as_searching_then_found(self):
        sig, room, _now = self.make_clocked()
        self.assertTrue(sig.quick_find("library", found=True))
        await sig.flush()
        self.assertEqual([b["al.activity"] for b in room.batches], ["searching", "found"])
        self.assertEqual(room.batches[0]["al.search_kind"], "library")

    async def test_the_cooldown_is_45_seconds(self):
        sig, room, now = self.make_clocked()
        self.assertTrue(sig.quick_find("library", found=True))
        now[0] += 44.9
        self.assertFalse(sig.quick_find("library", found=True))
        now[0] += 0.2
        self.assertTrue(sig.quick_find("library", found=True))
        await sig.flush()
        self.assertEqual([b["al.activity"] for b in room.batches],
                         ["searching", "found", "searching", "found"])
        self.assertEqual(sig_mod.QUICK_FIND_COOLDOWN_S, 45.0)

    async def test_a_repeat_after_found_is_still_a_visible_change(self):
        sig, room, now = self.make_clocked()
        async with sig.search("library") as s:
            s.found = True
        await sig.flush()
        now[0] += 100
        self.assertTrue(sig.quick_find("library", found=True))
        await sig.flush()
        self.assertEqual([b["al.activity"] for b in room.batches],
                         ["searching", "found", "searching", "found"])

    async def test_it_stays_quiet_while_a_real_search_is_open(self):
        sig, room, _now = self.make_clocked()
        async with sig.search("web") as s:
            self.assertFalse(sig.quick_find("library", found=True))
            s.found = True
        await sig.flush()
        self.assertEqual([b["al.activity"] for b in room.batches], ["searching", "found"])


class TapReplyTests(unittest.IsolatedAsyncioTestCase):
    def tapped(self, **kwargs):
        sig, room = make(**kwargs)
        calls: list[dict] = []
        real_update = sig.update
        sig.update = lambda **kv: (calls.append(kv), real_update(**kv))[1]
        return sig, room, calls

    async def test_chunks_pass_through_unchanged_and_in_order(self):
        sig, _room, _calls = self.tapped()
        chunks = ["Well ", "done, ", "you ", "were ", "brave. ", "Next ", "part ", "here."]
        self.assertEqual(await collect(sig.tap_reply(agen(*chunks))), chunks)

    async def test_non_string_chunks_pass_through_too(self):
        sig, _room, _calls = self.tapped()
        marker = object()
        self.assertEqual(await collect(sig.tap_reply(agen("Hello there my friend. ", marker))),
                         ["Hello there my friend. ", marker])

    async def test_a_chunk_is_not_held_back(self):
        sig, _room, _calls = self.tapped()
        gate = asyncio.Event()

        async def source():
            yield "Hel"
            await gate.wait()
            yield "lo."

        stream = sig.tap_reply(source())
        first = await asyncio.wait_for(stream.__anext__(), 1)  # source is parked at the gate
        self.assertEqual(first, "Hel")
        gate.set()
        self.assertEqual(await collect(stream), ["lo."])

    async def test_the_style_is_published_at_the_first_sentence_end_after_12_chars(self):
        sig, _room, calls = self.tapped()
        stream = sig.tap_reply(agen("Well done, you were ", "brave. ", "And then there is more to say here."))
        await stream.__anext__()
        self.assertEqual(calls, [])  # no sentence end yet
        await stream.__anext__()  # "brave. " completes the sentence
        self.assertEqual(calls, [{"talk_style": "praise", "reply": "1"}])
        await collect(stream)
        self.assertEqual(len(calls), 1)  # once per reply

    async def test_an_early_period_does_not_cut_the_opening(self):
        sig, _room, calls = self.tapped()
        await collect(sig.tap_reply(agen("Hi. ", "Once upon a time there was a farmer. ")))
        self.assertEqual(calls, [{"talk_style": "story", "reply": "1"}])

    async def test_the_style_is_published_at_90_characters(self):
        sig, _room, calls = self.tapped()
        text = "once upon a time " + "x" * 100  # no sentence end at all
        stream = sig.tap_reply(agen(text[:40], text[40:80], text[80:], "tail"))
        await stream.__anext__()
        await stream.__anext__()
        self.assertEqual(calls, [])  # 80 characters so far
        await stream.__anext__()
        self.assertEqual(calls, [{"talk_style": "story", "reply": "1"}])
        await collect(stream)

    async def test_the_90_character_opening_ignores_text_after_the_cut(self):
        sig, _room, calls = self.tapped()
        text = "a" * 95 + " well done"  # the praise marker sits after the 90th character
        await collect(sig.tap_reply(agen(text)))
        self.assertEqual(calls, [{"talk_style": "explain", "reply": "1"}])

    async def test_the_style_is_published_after_350ms_if_nothing_else_decides(self):
        sig, _room, calls = self.tapped(opening_timeout=0.05)
        gate = asyncio.Event()

        async def source():
            yield "Well done"
            await gate.wait()
            yield " friend."

        stream = sig.tap_reply(source())
        await stream.__anext__()
        self.assertEqual(calls, [])
        await asyncio.sleep(0.12)  # the source is stalled; the timer decides
        self.assertEqual(calls, [{"talk_style": "praise", "reply": "1"}])
        gate.set()
        await collect(stream)
        self.assertEqual(len(calls), 1)
        self.assertEqual(sig_mod.OPENING_TIMEOUT_S, 0.35)

    async def test_a_short_reply_is_decided_at_the_end_of_the_stream(self):
        sig, _room, calls = self.tapped()
        await collect(sig.tap_reply(agen("Why not?")))
        self.assertEqual(calls, [{"talk_style": "question", "reply": "1"}])

    async def test_an_empty_reply_publishes_nothing_and_does_not_count(self):
        sig, _room, calls = self.tapped()
        await collect(sig.tap_reply(agen()))
        await collect(sig.tap_reply(agen("", "  ")))
        self.assertEqual(calls, [])
        await collect(sig.tap_reply(agen("Hello there my friend. ")))
        self.assertEqual(calls, [{"talk_style": "explain", "reply": "1"}])

    async def test_each_reply_bumps_the_counter(self):
        sig, room, _calls = self.tapped()
        await collect(sig.tap_reply(agen("The sea is deep. ")))
        await sig.flush()
        await collect(sig.tap_reply(agen("The sea is deep. ")))
        await sig.flush()
        self.assertEqual([b["al.reply"] for b in room.batches], ["1", "2"])

    async def test_two_replies_inside_one_publish_window_merge_to_the_latest(self):
        sig, room, _calls = self.tapped()
        await collect(sig.tap_reply(agen("The sea is deep. ")))
        await collect(sig.tap_reply(agen("The sea is deep. ")))
        await sig.flush()
        self.assertEqual([b["al.reply"] for b in room.batches], ["2"])

    async def test_an_abandoned_reply_decides_nothing(self):
        sig, _room, calls = self.tapped()
        sig.hint_praise()
        stream = sig.tap_reply(agen("Hello", " there"))
        await stream.__anext__()
        await stream.aclose()  # interrupted before the opening was known
        await asyncio.sleep(0.01)
        self.assertEqual(calls, [])
        await collect(sig.tap_reply(agen("Here is the answer. ")))
        self.assertEqual(calls, [{"talk_style": "praise", "reply": "1"}])  # the hint survived

    async def test_a_source_error_propagates(self):
        sig, _room, _calls = self.tapped()

        async def source():
            yield "Hello"
            raise ValueError("llm failed")

        with self.assertRaises(ValueError):
            await collect(sig.tap_reply(source()))

    async def test_hints_are_used_once(self):
        sig, _room, calls = self.tapped()
        sig.hint_praise()
        await collect(sig.tap_reply(agen("Here is the answer. ")))
        await collect(sig.tap_reply(agen("Here is the answer. ")))
        self.assertEqual([c["talk_style"] for c in calls], ["praise", "explain"])

    async def test_safety_outranks_praise_and_is_used_once(self):
        sig, _room, calls = self.tapped()
        sig.hint_praise()
        sig.hint_safety()
        await collect(sig.tap_reply(agen("Well done for telling me. ")))
        await collect(sig.tap_reply(agen("Well done for telling me. ")))
        self.assertEqual([c["talk_style"] for c in calls], ["gentle", "praise"])

    async def test_a_sad_turn_makes_the_reply_gentle(self):
        sig, _room, calls = self.tapped()
        sig.on_child_text("i am so sad today")
        await collect(sig.tap_reply(agen("Let us look at it together. ")))
        self.assertEqual(calls[-1], {"talk_style": "gentle", "reply": "1"})

    async def test_arabic_openings(self):
        sig, _room, calls = self.tapped()
        await collect(sig.tap_reply(agen("ما شاء الله، أحسنت يا بطل. ")))
        await collect(sig.tap_reply(agen("كان يا ما كان في قرية صغيرة. ")))
        await collect(sig.tap_reply(agen("هل تحب القصص الجميلة؟ ")))
        self.assertEqual([c["talk_style"] for c in calls], ["praise", "story", "question"])

    async def test_a_classifier_crash_does_not_touch_the_stream(self):
        sig, _room, _calls = self.tapped()
        original = sig_mod.classify_talk
        sig_mod.classify_talk = lambda *a, **k: 1 / 0
        try:
            with self.assertLogs(sig_mod.logger, level="WARNING"):
                out = await collect(sig.tap_reply(agen("Hello there my friend. ", "More.")))
        finally:
            sig_mod.classify_talk = original
        self.assertEqual(out, ["Hello there my friend. ", "More."])


class ListenFlowTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.sig, self.room = make()
        self.handlers: dict = {}
        self.sig.attach(SimpleNamespace(on=lambda event, cb: self.handlers.__setitem__(event, cb)))

    def transcript(self, text, final=False):
        self.handlers["user_input_transcribed"](SimpleNamespace(transcript=text, is_final=final))

    def agent_state(self, state):
        self.handlers["agent_state_changed"](SimpleNamespace(old_state="x", new_state=state))

    def user_state(self, state):
        self.handlers["user_state_changed"](SimpleNamespace(old_state="x", new_state=state))

    async def test_attach_subscribes_to_the_three_events(self):
        self.assertEqual(set(self.handlers),
                         {"user_input_transcribed", "agent_state_changed", "user_state_changed"})

    async def test_too_short_lines_are_not_classified(self):
        self.assertIsNone(self.sig.on_child_text("sad"))
        self.assertIsNone(self.sig.on_child_text(""))
        self.assertIsNone(self.sig.on_child_text(None))
        await self.sig.flush()
        self.assertEqual(self.room.batches, [])

    async def test_the_first_classification_publishes_listen_style_and_turn(self):
        self.transcript("ليش السما")
        await self.sig.flush()
        self.assertEqual(self.room.batches, [{"al.listen_style": "curious", "al.turn": "1"}])

    async def test_within_a_turn_only_upgrades_are_published(self):
        self.transcript("ليش السما")  # curious
        await self.sig.flush()
        self.transcript("ليش السما زرقاء")  # curious again: nothing
        await self.sig.flush()
        self.transcript("ليش السما زرقاء وانا فرحان")  # excited: upgrade
        await self.sig.flush()
        self.transcript("ليش السما زرقاء")  # a lower one later in the turn: nothing
        await self.sig.flush()
        self.transcript("ليش السما زرقاء وانا حزين")  # sad: upgrade
        await self.sig.flush()
        self.transcript("i won i won")  # excited after sad: nothing
        await self.sig.flush()
        self.assertEqual([b["al.listen_style"] for b in self.room.batches], ["curious", "excited", "sad"])
        self.assertEqual(self.room.merged()["al.listen_style"], "sad")
        self.assertEqual([b.get("al.turn") for b in self.room.batches if "al.turn" in b], ["1"])
        styles = [b["al.listen_style"] for b in self.room.batches]
        self.assertEqual(styles[0], "curious")
        self.assertEqual(styles[-1], "sad")
        self.assertNotIn("neutral", styles)

    async def test_a_neutral_first_line_still_opens_the_turn(self):
        self.transcript("the cat sat down")
        self.transcript("the cat sat down and i am sad")
        await self.sig.flush()
        self.assertEqual(self.room.merged(), {"al.listen_style": "sad", "al.turn": "1"})

    async def test_the_agent_speaking_ends_the_turn(self):
        self.transcript("ليش السما")
        await self.sig.flush()
        self.agent_state("thinking")  # a late final transcript still belongs to this turn
        self.transcript("ليش السما زرقاء وانا حزين")
        await self.sig.flush()
        self.agent_state("speaking")
        self.transcript("the cat sat down")  # the child's next turn
        await self.sig.flush()
        turns = [b["al.turn"] for b in self.room.batches if "al.turn" in b]
        self.assertEqual(turns, ["1", "2"])
        self.assertEqual(self.room.merged()["al.listen_style"], "neutral")  # reset, then re-published

    async def test_a_new_turn_with_the_same_class_still_bumps_the_turn(self):
        self.transcript("ليش السما")
        await self.sig.flush()
        self.agent_state("speaking")
        self.transcript("ليش القمر")
        await self.sig.flush()
        self.assertEqual(self.room.batches[-1], {"al.turn": "2"})  # listen_style unchanged, not resent

    async def test_the_child_starting_to_speak_opens_the_next_turn(self):
        self.transcript("ليش السما")
        self.agent_state("speaking")
        self.user_state("speaking")
        self.assertIsNone(self.sig._turn_class)
        self.agent_state("listening")
        self.user_state("listening")

    async def test_hints_reset_when_the_child_starts_a_new_turn(self):
        self.sig.hint_praise()
        self.sig.hint_safety()
        self.transcript("hello there friend")  # still the first turn, nothing was closed
        self.assertTrue(self.sig._hint_praise)
        self.agent_state("speaking")
        self.transcript("another question for you")
        self.assertFalse(self.sig._hint_praise or self.sig._hint_safety)

    async def test_typed_chat_is_a_turn_of_its_own(self):
        self.sig.on_child_text("why is the sky blue", new_turn=True)
        self.sig.on_child_text("i feel sad now", new_turn=True)
        await self.sig.flush()
        turns = [b["al.turn"] for b in self.room.batches if "al.turn" in b]
        self.assertEqual(turns[-1], "2")
        self.assertEqual(self.room.merged()["al.listen_style"], "sad")

    async def test_events_with_odd_shapes_do_not_raise(self):
        self.handlers["user_input_transcribed"](SimpleNamespace())
        self.handlers["agent_state_changed"](SimpleNamespace())
        self.handlers["user_state_changed"](object())
        self.handlers["user_input_transcribed"](SimpleNamespace(transcript=None))


if __name__ == "__main__":
    unittest.main()
