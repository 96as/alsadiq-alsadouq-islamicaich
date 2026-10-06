"""Tests for the hybrid companion's tool side (hk/12): bank_search, the search_bank tool, the
{{card:ID}} marker filter, the licence, the reply audit, flag_safety_concern routing and the
_prepare paths (the guard's ``check`` is mocked: its own tests live with turn_guard).

Every Quran or hadith word here is a PLACEHOLDER; no scripture text appears in this file.

Run from backend/:  python manage.py test conversation.agent.test_bank_tool \
    --settings=config.settings_sqlite_test
"""
from __future__ import annotations

import asyncio
import contextlib
import unittest
from types import SimpleNamespace
from unittest import mock

from conversation.agent import bank_search, turn_pipeline
from conversation.agent.retrieval import ValueIndex
from conversation.agent.turn_guard import REFER, SAFETY, GuardHit
from conversation.test_turn_policy import drain_guard_tasks

ARABIC = "نص تجريبي"  # "placeholder text": stands in for the Arabic of a verse or an excerpt
GUIDE = {n: f"<{n}>" for n in
         ("verse", "hadith", "disagreement", "fiqh", "creed", "afterlife", "story", "no_source", "comfort")}

_DEFAULTS = dict(
    arabic_text="", english_text="", translation_name="", translation_source_url="",
    child_explanation_ar="", child_explanation_en="", child_explanation_older_ar="",
    child_explanation_older_en="", disagreement_note_ar="", disagreement_note_en="",
    title_ar="", title_en="", keywords_ar=[], keywords_en=[], surah=None, ayah=None,
    audio_url="", book="", number="", narrator="", grade="", grader="", source_site="",
    source_url="", verification_status="reviewed", age_band="all", content_level="",
)


def item(pk, type_="verse", **kw):
    return SimpleNamespace(pk=pk, type=type_, **{**_DEFAULTS, **kw})


def value(slug, kw_en=(), order=0):
    return SimpleNamespace(slug=slug, name_en=slug.title(), name_ar="قيمة " + slug,
                           keywords_en=list(kw_en), keywords_ar=[], order=order)


def bank():
    values = [value("honesty", ["lie", "lying", "truth"], 1), value("patience", ["patient"], 2)]
    items = [
        item(1, "verse", surah=49, ayah=12, arabic_text=ARABIC, english_text="PLACEHOLDER TRANSLATION 1",
             translation_name="Placeholder translation", child_explanation_en="Explain 1",
             verification_status="seeded"),
        item(2, "hadith", book="Placeholder book", number="7", grade="sahih", grader="G",
             arabic_text=ARABIC, english_text="PLACEHOLDER HADITH", translation_name="Placeholder",
             child_explanation_en="Explain 2", content_level="A"),
        item(3, "verse", surah=9, ayah=119, arabic_text=ARABIC, english_text="PLACEHOLDER TRANSLATION 3",
             translation_name="Placeholder translation", age_band="10-13", child_explanation_en="Explain 3"),
        item(4, "faq", title_en="Is the Kaaba a god", arabic_text=ARABIC + " excerpt",
             keywords_en=["kaaba"], child_explanation_en="Explain 4", content_level="B"),
        item(5, "fiqh", title_en="Do all pray the same", arabic_text=ARABIC + " excerpt",
             keywords_en=["pray the same"], disagreement_note_en="Everyone prays five times.",
             content_level="C"),
        item(6, "term", title_en="Tawhid", arabic_text=ARABIC, english_text="PLACEHOLDER 6",
             translation_name="Placeholder dictionary", keywords_en=["tawhid"]),
        item(7, "tafsir", title_en="Placeholder tafsir", arabic_text=ARABIC + " excerpt",
             keywords_en=["wasting"], child_explanation_en="Explain 7"),
        item(8, "hadith", book="Placeholder book", number="8", grade="sahih", grader="G",
             arabic_text=ARABIC, child_explanation_en="Explain 8", verification_status="seeded"),
    ]
    links = [("honesty", 1, 0), ("honesty", 2, 1), ("honesty", 3, 2), ("honesty", 8, 3), ("patience", 7, 0)]
    return ValueIndex.from_records(values, items, links)


def pks(items):
    return [i.pk for i in items]


class SearchTests(unittest.TestCase):
    def setUp(self):
        self.index = bank()

    def test_topic_keeps_only_its_types(self):
        got = bank_search.search(self.index, "lying", "hadith", ["honesty"], "en", None)
        self.assertEqual({i.type for i in got}, {"hadith"})
        got = bank_search.search(self.index, "lying", "quran", ["honesty", "patience"], "en", None)
        self.assertTrue(got and {i.type for i in got} <= {"verse", "tafsir"})
        got = bank_search.search(self.index, "tawhid", "word_meaning", [], "en", None)
        self.assertEqual(pks(got), [6])
        self.assertEqual(pks(bank_search.search(self.index, "do all pray the same", "worship", [], "en", None)), [5])

    def test_unknown_topic_is_values_and_unknown_values_are_ignored(self):
        got = bank_search.search(self.index, "x", "no-such-topic", ["nonsense", "HONESTY"], "en", None)
        self.assertTrue(got and {i.type for i in got} <= {"verse", "hadith"})
        self.assertEqual(bank_search.search(self.index, "x", "values", ["nonsense"], "en", None), [])

    def test_values_match_slug_english_and_arabic_name_case_insensitively(self):
        for name in ("honesty", "HoNeStY", "قيمة honesty"):
            got = bank_search.search(self.index, "x", "values", [name], "en", None)
            self.assertIn(1, pks(got), name)

    def test_question_keywords_add_candidates(self):
        got = bank_search.search(self.index, "why is the kaaba holy", "creed", [], "en", None)
        self.assertEqual(pks(got), [4])

    def test_younger_child_never_gets_older_material(self):
        young = bank_search.search(self.index, "x", "values", ["honesty"], "en", "6-9")
        older = bank_search.search(self.index, "x", "values", ["honesty"], "en", "10-13")
        self.assertNotIn(3, pks(young))
        self.assertIn(3, pks(older))

    def test_order_is_reviewed_first_then_type_and_at_most_three(self):
        got = bank_search.search(self.index, "x", "values", ["honesty"], "en", None)
        self.assertLessEqual(len(got), 3)
        # reviewed verse, reviewed hadith, then the seeded verse (the seeded hadith is cut at three)
        self.assertEqual(pks(got), [3, 2, 1])

    def test_empty_bank_or_nothing_found(self):
        self.assertEqual(bank_search.search(None, "x", "values", ["honesty"], "en", None), [])
        self.assertEqual(bank_search.search(self.index, "zzz", "creed", [], "en", None), [])


class FormatTests(unittest.TestCase):
    def setUp(self):
        self.index = bank()

    def fmt(self, items, topic="values", age=None):
        return bank_search.format_result(items, "en", age, topic, GUIDE)

    def test_found_result_shape(self):
        items = bank_search.search(self.index, "x", "values", ["honesty"], "en", None)
        text = self.fmt(items)
        self.assertTrue(text.startswith(
            f"FOUND {len(items)}. No card shown yet this session. Only these may be quoted or attributed this turn."))
        for it in items:
            self.assertIn("{{card:%d}} %s · " % (it.pk, it.type), text)
        self.assertIn("our simple explanation: Explain", text)
        self.assertIn("Show an item by writing its marker exactly as shown, where you mention it (at most 2).", text)
        self.assertIn("GUIDANCE:", text)

    def test_no_arabic_and_no_source_excerpt_ever_reaches_the_model(self):
        items = [self.index.items[pk].obj for pk in (1, 2, 4, 5, 6, 7)]
        text = self.fmt(items)
        self.assertNotIn(ARABIC, text)
        self.assertNotIn("excerpt", text)
        # a hadith's or verse's translation may be shown (it is ours to quote), the Arabic never
        self.assertIn("PLACEHOLDER HADITH", self.fmt([items[1]]))

    def test_not_found(self):
        text = self.fmt([], topic="creed")
        self.assertTrue(text.startswith("NOT FOUND. Nothing verified in the library for this."))
        self.assertIn("du'a wording or story", text)
        self.assertIn("<no_source>\n<creed>", text)
        self.assertNotIn("FOUND 0", text)

    def test_a_level_c_item_carries_what_all_agree_on(self):
        text = self.fmt([self.index.items[5].obj], topic="worship")
        self.assertIn("all agree: Everyone prays five times.", text)

    def test_stays_within_300_words_even_with_long_items(self):
        long_en = "word " * 400
        items = [item(i, "hadith", book="Placeholder book", number=str(i), grade="sahih", grader="G",
                      arabic_text=ARABIC, english_text=long_en, translation_name="Placeholder",
                      child_explanation_en=long_en) for i in (11, 12, 13)]
        index = ValueIndex.from_records([value("honesty")], items, [("honesty", i.pk, 0) for i in items])
        out = bank_search.format_result([index.items[i.pk].obj for i in items], "en", None, "afterlife",
                                        bank_search.load_guidance())
        self.assertLessEqual(len(out.split()), bank_search.MAX_RESULT_WORDS)
        self.assertIn("{{card:13}}", out)

    def test_guidance_precedence(self):
        v, h, c = (self.index.items[pk].obj for pk in (1, 2, 5))
        g = bank_search.guidance_names
        self.assertEqual(g([], "values"), ["no_source"])
        self.assertEqual(g([], "creed"), ["no_source", "creed"])
        self.assertEqual(g([], "worship"), ["no_source", "fiqh"])
        self.assertEqual(g([], "prophets_story"), ["no_source", "story"])
        self.assertEqual(g([v], "values"), ["verse"])
        self.assertEqual(g([h], "hadith"), ["hadith"])
        self.assertEqual(g([v, h], "values"), ["verse"])          # a verse beats a hadith
        self.assertEqual(g([v, c], "worship"), ["fiqh", "disagreement"])  # level C beats the verse
        self.assertEqual(g([v], "afterlife"), ["afterlife", "verse"])
        self.assertEqual(g([c], "creed"), ["creed", "disagreement"])

    def test_missing_guidance_files_are_skipped_silently(self):
        text = bank_search.format_result([self.index.items[1].obj], "en", None, "creed", {"creed": "<creed>"})
        self.assertIn("<creed>", text)
        self.assertNotIn("<verse>", text)
        self.assertNotIn("GUIDANCE:", bank_search.format_result([self.index.items[1].obj], "en", None, "values", {}))

    def test_real_guidance_files_load_and_are_short(self):
        guide = bank_search.load_guidance()
        self.assertEqual(set(guide), set(GUIDE))
        for name, text in guide.items():
            self.assertLessEqual(len(text.split()), 80, name)


async def _feed(chunks):
    for c in chunks:
        yield c


async def _strip(text, size=None):
    seen = []

    async def on_card(i):
        seen.append(i)

    chunks = [text] if size is None else [text[i:i + size] for i in range(0, len(text), size)]
    out = "".join([c async for c in turn_pipeline.strip_card_markers(_feed(chunks), on_card) if isinstance(c, str)])
    return out, seen


class MarkerFilterTests(unittest.IsolatedAsyncioTestCase):
    async def test_marker_is_stripped_however_the_text_is_split(self):
        text = "Kindness matters {{card:12}} so be kind {{card:7}}."
        for size in (None, 1, 2, 3, 5, 8, 24):
            out, seen = await _strip(text, size)
            self.assertEqual(out, "Kindness matters so be kind .", size)
            self.assertEqual(seen, [12, 7], size)

    async def test_text_without_a_marker_is_untouched(self):
        for size in (None, 1, 4):
            out, seen = await _strip("Hello { there } and {x} end", size)
            self.assertEqual((out, seen), ("Hello { there } and {x} end", []))

    async def test_a_brace_pair_that_is_not_a_card_marker_goes_on_as_plain_text(self):
        out, seen = await _strip("A {{verse:2:5}} B", 3)
        self.assertEqual((out, seen), ("A {{verse:2:5}} B", []))

    async def test_an_unclosed_marker_is_released_after_24_characters(self):
        text = "Hi {{card:12 and then a long tail of ordinary words {{card:5}}"
        for size in (None, 1, 6):
            out, seen = await _strip(text, size)
            self.assertEqual(seen, [5], size)
            self.assertEqual(out, "Hi {{card:12 and then a long tail of ordinary words ", size)

    async def test_a_half_closed_marker_is_still_a_marker(self):
        # "{{card:12}" with one closing brace must not leave an open "{{" for the scripture filter
        for text, want in (("Be kind {{card:12} every day.", "Be kind every day."),
                           ("Be kind {{card:12}", "Be kind ")):
            for size in (None, 1, 3, 7):
                out, seen = await _strip(text, size)
                self.assertEqual((out, seen), (want, [12]), (text, size))

    async def test_a_partial_marker_at_the_end_comes_out_as_text(self):
        out, seen = await _strip("Ends {{card:1", 4)
        self.assertEqual((out, seen), ("Ends {{card:1", []))

    async def test_flush_sentinels_pass_through(self):
        sentinel = object()
        got = []
        async for c in turn_pipeline.strip_card_markers(_feed(["a {{ca", sentinel, "rd:3}} b"]), mock.AsyncMock()):
            got.append(c)
        self.assertIn(sentinel, got)
        self.assertEqual("".join(c for c in got if isinstance(c, str)), "a b")


class BraceGuaranteeTests(unittest.IsolatedAsyncioTestCase):
    """The card-marker filter runs first in guard_speech; the old guarantee still holds behind it:
    no brace text is ever spoken or shown, whatever the chunking."""

    TEXTS = (
        "Be kind {{card:1}} and {{verse:49:12}} and {oops fine} {{card:99}} end",
        "a { b {{ card : 2 }} c }} d {{ unterminated and then a long tail of ordinary words after it",
        "{{card:12 and {{card:2}} {{{card:2}}} }}",
    )

    async def test_no_brace_ever_reaches_speech_or_transcript(self):
        agent = make_agent_class()()
        agent._turn_items = [agent._value_index.items[pk].obj for pk in (1, 2)]
        for text in self.TEXTS:
            for size in (1, 2, 3, 5, 7, 11, 40):
                chunks = [text[i:i + size] for i in range(0, len(text), size)]
                for out in ("".join([c async for c in agent.guard_speech(_feed(chunks))]),
                            "".join([c async for c in agent.guard_speech(_feed(chunks), count=False)])):
                    self.assertNotIn("{", out, (text, size))
                    self.assertNotIn("}", out, (text, size))
                    self.assertNotIn("card:", out, (text, size))


class FakeSignals:
    """Records search(kind) -> found/none, like the avatar's activity attribute."""

    def __init__(self):
        self.log = []

    @contextlib.asynccontextmanager
    async def search(self, kind):
        box = SimpleNamespace(found=False)
        self.log.append(("searching", kind))
        try:
            yield box
        finally:
            self.log.append(("found" if box.found else "none", kind))

    def hint_safety(self):
        pass


def make_agent_class():
    from conversation.agent.agent_class import AlSadiqAgent

    class TestAgent(AlSadiqAgent):
        """The real agent; database and room work is recorded, not done (as the eval agent does)."""

        def __init__(self, **kw):
            super().__init__(db_session_id=1, child_id=2, language="en", value_index=bank(), **kw)
            self.signals = FakeSignals()
            self.events = []
            self.spawned = []

        def _spawn(self, coro):
            self.spawned.append(coro)
            getattr(coro, "close", lambda: None)()

        async def _publish_event(self, topic, payload):
            self.events.append((topic, payload))

    return TestAgent


class ToolTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.agent = make_agent_class()()
        self.index = self.agent._value_index

    async def test_found_drives_the_library_animation_and_remembers_the_items(self):
        out = await self.agent.search_bank(question="why be honest", topic="values", values=["honesty"])
        self.assertTrue(out.startswith("FOUND"))
        self.assertEqual(self.agent.signals.log, [("searching", "library"), ("found", "library")])
        self.assertTrue(self.agent._tool_ran and self.agent._tool_found)
        self.assertEqual(pks(self.agent._turn_items), [3, 2, 1])

    async def test_not_found_ends_in_none(self):
        out = await self.agent.search_bank(question="zzz", topic="creed", values=None)
        self.assertTrue(out.startswith("NOT FOUND"))
        self.assertEqual(self.agent.signals.log, [("searching", "library"), ("none", "library")])
        self.assertTrue(self.agent._tool_ran and not self.agent._tool_found)

    async def test_a_refer_turn_gets_no_sources_and_ends_in_none(self):
        self.agent._refer_turn = True
        out = await self.agent.search_bank(question="is my prayer valid", topic="worship", values=[])
        self.assertIn("safety or a referral: no sources", out)
        self.assertNotIn("FOUND", out)
        self.assertEqual(self.agent.signals.log, [("searching", "library"), ("none", "library")])
        self.assertFalse(self.agent._tool_ran)
        self.assertEqual(self.agent._turn_items, [])

    async def test_a_safety_turn_gets_no_sources_and_ends_in_none(self):
        self.agent._safety_turn = True
        out = await self.agent.search_bank(question="does Allah still love me", topic="values", values=["honesty"])
        self.assertIn("safety or a referral: no sources", out)
        self.assertNotIn("FOUND", out)
        self.assertEqual(self.agent.signals.log, [("searching", "library"), ("none", "library")])
        self.assertEqual(self.agent._turn_items, [])
        self.assertFalse(self.agent._tool_ran)

    async def test_the_result_uses_the_session_language_not_the_childs_turn_language(self):
        self.agent._turn_language = "ar"  # the child wrote Arabic in an English session
        out = await self.agent.search_bank(question="why be honest", topic="values", values=["honesty"])
        self.assertIn("Explain 2", out)  # the English explanation of the hadith, not an Arabic fallback
        self.assertNotIn(ARABIC, out)

    async def test_the_tool_text_never_contains_arabic_scripture(self):
        out = await self.agent.search_bank(question="why be honest", topic="values", values=["honesty"])
        self.assertNotIn(ARABIC, out)

    async def test_a_failing_search_answers_not_found_instead_of_raising(self):
        with mock.patch.object(bank_search, "search", side_effect=RuntimeError("boom")):
            out = await self.agent.search_bank(question="x", topic="values", values=None)
        self.assertTrue(out.startswith("NOT FOUND"))

    async def test_the_tool_text_is_short_and_the_schema_is_strict_compatible(self):
        from livekit.agents import llm
        from livekit.agents.llm.utils import build_strict_openai_schema

        schemas = {t.info.name: build_strict_openai_schema(t)
                   for t in llm.ToolContext(self.agent.tools).function_tools.values()}
        fn = schemas["search_bank"]["function"]
        words = len(fn["description"].split()) + sum(
            len(p["description"].split()) for p in fn["parameters"]["properties"].values())
        self.assertLessEqual(words, 90)
        self.assertEqual(fn["parameters"]["required"], ["question", "topic", "values"])
        self.assertIn("at_home", schemas["flag_safety_concern"]["function"]["parameters"]["properties"])

    async def test_licence_follows_the_items_of_this_turn_only(self):
        self.assertEqual(self.agent._licence(), frozenset())
        await self.agent.search_bank(question="x", topic="hadith", values=["honesty"])
        self.assertEqual(self.agent._licence(), frozenset({"hadith"}))
        self.agent._prepare("why?")  # a follow-up with no new search: no licence (review M2) ...
        self.assertEqual(self.agent._turn_items, [])
        self.assertTrue(self.agent._prev_items)  # ... though last turn's items still validate a card id
        self.assertEqual(self.agent._licence(), frozenset())


async def _speak(agent, text, size=5, count=True):
    chunks = [text[i:i + size] for i in range(0, len(text), size)]
    return "".join([c async for c in agent.guard_speech(_feed(chunks), count=count)])


class CardMarkerTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.agent = make_agent_class()()
        self.agent._turn_items = [self.agent._value_index.items[pk].obj for pk in (1, 2, 8)]
        self.agent._turn_language = "en"

    def shown(self):
        return [p["id"] for topic, p in self.agent.events if topic == "reference"]

    async def test_a_cited_item_gets_its_card_and_the_marker_is_removed(self):
        out = await _speak(self.agent, "A verse {{card:1}} says to be honest.")
        self.assertEqual(out, "A verse says to be honest.")
        self.assertEqual(self.shown(), [1])
        card = self.agent.events[0][1]
        self.assertEqual(card["id"], 1)
        self.assertIn("arabic_text", card)  # the card is where the Arabic lives
        self.assertEqual(self.agent._cards, [1])
        self.assertEqual(len(self.agent.spawned), 1)  # the ServedReference write

    async def test_a_marker_after_a_model_flag_publishes_no_card(self):
        self.agent._flagged_turn = True  # flag_safety_concern ran earlier in this turn
        out = await _speak(self.agent, "You are brave {{card:1}} for telling me.")
        self.assertEqual(out, "You are brave for telling me.")
        self.assertEqual(self.shown(), [])
        self.assertEqual(self.agent._cards, [])

    async def test_a_safety_or_refer_turn_strips_the_marker_and_publishes_nothing(self):
        for flag in ("_safety_turn", "_refer_turn"):
            self.agent.events.clear()
            self.agent._prepare("hello")  # fresh turn; the items of the old turn become last turn's
            self.agent._prev_items = [self.agent._value_index.items[pk].obj for pk in (1, 2)]  # citable
            setattr(self.agent, flag, True)
            out = await _speak(self.agent, "Allah loves you {{card:1}} always {{card:2}}.")
            self.assertEqual(out, "Allah loves you always .", flag)
            self.assertEqual(self.shown(), [], flag)
            self.assertEqual(self.agent._cards, [], flag)

    async def test_a_failing_card_never_breaks_the_stream(self):
        async def boom(topic, payload):
            raise RuntimeError("room down")

        self.agent._publish_event = boom
        with self.assertLogs("conversation.agent.turn_pipeline", level="ERROR"):
            out = await _speak(self.agent, "Kind words {{card:1}} matter.")
        self.assertEqual(out, "Kind words matter.")

    async def test_cards_use_the_session_language(self):
        self.agent._turn_language = "ar"  # the child's words this turn; the card follows the session
        with mock.patch.object(turn_pipeline, "card_payload", wraps=turn_pipeline.card_payload) as cp:
            await _speak(self.agent, "See {{card:1}}.")
        self.assertEqual(cp.call_args.args[1], "en")

    async def test_a_stray_bracket_label_is_stripped_and_cited_like_a_marker(self):
        for size in (None, 1, 3, 7):
            self.agent.events.clear()
            self.agent._marker_seen, self.agent._cards, self.agent._shown_card_ids = set(), [], set()
            text = "Honesty matters [card:1] a lot."
            parts = [text] if size is None else [text[i:i + size] for i in range(0, len(text), size)]
            out = "".join([c async for c in self.agent.guard_speech(_feed(parts))])
            self.assertEqual(out, "Honesty matters a lot.", size)
            self.assertNotIn("card", out)
            self.assertEqual(self.shown(), [1], size)

    async def test_the_spoken_form_of_a_bracket_label_is_stripped_too(self):
        # the speech cleaner turns the digits into words before tts_node sees "[card:twelve]"
        out = await _speak(self.agent, "Honesty matters [card:twelve] a lot and [1] stays.")
        self.assertEqual(out, "Honesty matters a lot and [1] stays.")
        self.assertEqual(self.shown(), [])  # only the transcript path (digits) publishes

    async def test_an_id_that_search_bank_did_not_return_is_dropped_silently(self):
        with self.assertLogs("conversation.agent.turn_pipeline", level="INFO") as cm:
            out = await _speak(self.agent, "Look {{card:99}} here.")
        self.assertEqual(out, "Look here.")
        self.assertEqual(self.shown(), [])
        self.assertTrue(any("not an item search_bank returned" in line for line in cm.output))

    async def test_each_id_once_and_at_most_two_cards_a_turn(self):
        out = await _speak(self.agent, "A {{card:1}} B {{card:1}} C {{card:2}} D {{card:8}} E")
        self.assertNotIn("{{", out)
        self.assertEqual(self.shown(), [1, 2])

    async def test_an_item_is_published_once_per_session_however_often_it_is_cited(self):
        await _speak(self.agent, "A verse {{card:1}} says to be honest.")
        self.agent._prepare("why?")          # next turn: the model cites the same item again
        out = await _speak(self.agent, "Because {{card:1}} says so, and {{card:2}} too.")
        self.assertEqual(out, "Because says so, and too.")  # the marker is still stripped
        self.assertEqual(self.shown(), [1, 2])               # card 1 only the first time
        self.assertEqual(len(self.agent.spawned), 2)         # one ServedReference write per item
        self.assertEqual(self.agent._cards, [1, 2])          # both count as cited this turn...
        self.assertEqual(self.agent._licence(), frozenset())  # ...but a follow-up with no search licenses nothing
        self.agent._prepare("and?")
        await _speak(self.agent, "{{card:1}} {{card:2}}")
        self.assertEqual(self.shown(), [1, 2])               # nothing new in turn three
        self.assertEqual(len(self.agent.spawned), 2)

    async def test_a_recited_item_is_still_audited_as_cited(self):
        with mock.patch.object(turn_pipeline, "_write_reply_audit") as audit:
            await _speak(self.agent, "First {{card:1}}.")
            self.agent._prepare("why?")
            self.agent._tool_ran = self.agent._tool_found = True
            await _speak(self.agent, "Again {{card:1}}.")
            self.agent._audit_reply()
        self.assertEqual(audit.call_args.args[3], [1])

    async def test_speech_and_transcript_share_one_publication(self):
        await _speak(self.agent, "A {{card:2}} B", count=True)
        await _speak(self.agent, "A {{card:2}} B", count=False)
        self.assertEqual(self.shown(), [2])

    async def test_last_turns_items_can_still_be_cited(self):
        self.agent._prepare("why?")
        self.assertEqual(self.agent._turn_items, [])
        await _speak(self.agent, "Because {{card:1}}.")
        self.assertEqual(self.shown(), [1])

    async def test_the_transcript_path_removes_the_marker_too(self):
        out = "".join([c async for c in self.agent.transcription_node(
            _feed(["Be honest {{ca", "rd:1}} always."]), None)])
        self.assertEqual(out, "Be honest always.")
        self.assertEqual(self.shown(), [1])

    async def test_attribution_is_licensed_by_the_returned_items(self):
        out = await _speak(self.agent, "In a hadith, the Prophet said be kind.")
        self.assertIn("The Prophet said".lower(), out.lower())
        self.agent._turn_items = []
        out = await _speak(self.agent, "In a hadith, the Prophet said be kind.")
        self.assertNotIn("Prophet said", out)


class SafetyTurnShowsNoSourcesTests(unittest.IsolatedAsyncioTestCase):
    """End to end with the real guard: a disclosure turn gets no sources and no card, even if the model
    calls search_bank and cites an item."""

    async def test_a_safety_turn_never_shows_a_scripture_card(self):
        agent = make_agent_class()()
        agent._spawn = lambda coro: coro.close()
        note = agent._prepare("my dad hits me with a belt, does Allah still love me?")
        self.assertTrue(agent._safety_turn)
        self.assertTrue(note)
        out = await agent.search_bank(question="does Allah still love me", topic="values", values=["honesty"])
        self.assertIn("safety or a referral: no sources", out)
        self.assertEqual(agent._turn_items, [])
        agent._prev_items = [agent._value_index.items[1].obj]  # even last turn's items stay hidden
        text = "".join([c async for c in agent.guard_speech(_feed(["Allah loves you {{card:1}} so much."]))])
        self.assertEqual(text, "Allah loves you so much.")
        self.assertEqual([t for t, _ in agent.events if t == "reference"], [])


class ReplyAuditTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.agent = make_agent_class()()
        patcher = mock.patch.object(turn_pipeline, "_write_reply_audit")
        self.audit = patcher.start()
        self.addCleanup(patcher.stop)

    def last(self):
        return self.audit.call_args.args

    async def test_found_and_cited_is_an_answer_with_the_cited_ids(self):
        await self.agent.search_bank(question="x", topic="values", values=["honesty"])
        first = self.agent._turn_items[0]
        await _speak(self.agent, f"See {{{{card:{first.pk}}}}}.")
        self.agent._audit_reply()
        self.assertEqual(self.last(), (1, "ANSWER", "A", [first.pk]))
        self.agent._audit_reply()  # once per turn
        self.assertEqual(self.audit.call_count, 1)

    async def test_a_cited_level_c_item_is_disagree_and_refer(self):
        await self.agent.search_bank(question="do all pray the same", topic="worship", values=None)
        await _speak(self.agent, "It differs {{card:5}}.")
        self.agent._audit_reply()
        self.assertEqual(self.last(), (1, "DISAGREE_AND_REFER", "C", [5]))

    async def test_nothing_found_is_a_decline(self):
        await self.agent.search_bank(question="zzz", topic="creed", values=None)
        self.agent._audit_reply()
        self.assertEqual(self.last(), (1, "DECLINE_NO_SOURCE", "", []))

    async def test_no_tool_no_audit_and_a_refer_or_safety_turn_is_not_audited_here(self):
        self.agent._audit_reply()
        self.agent._refer_turn = True
        await self.agent.search_bank(question="x", topic="worship", values=None)
        self.agent._audit_reply()
        self.agent._tool_ran, self.agent._safety_turn = True, True
        self.agent._audit_reply()
        self.audit.assert_not_called()


class FlagRoutingTests(unittest.IsolatedAsyncioTestCase):
    """hk/12g (lead decision: parents are trusted): every model flag but off_topic alerts the parent,
    once per session, family cases included. There is no quiet / staff-only path."""

    def setUp(self):
        self.agent = make_agent_class()()
        self.agent._turn_ref = turn_pipeline.TurnRef(None)
        self.agent._turn_ref.id = 5
        patcher = mock.patch("conversation.agent.agent_class._create_safety_flag_and_alert",
                             new=mock.AsyncMock(return_value="ok"))
        self.flag = patcher.start()
        self.addCleanup(patcher.stop)

    async def call(self, flag_type="sensitive", at_home=False):
        return await self.agent.flag_safety_concern(flag_type=flag_type, description="d", at_home=at_home)

    async def test_every_model_flag_alerts_the_parent_once_per_session(self):
        await self.call("sensitive")
        await self.call("harmful")
        await self.call("inappropriate")
        notify = [c.kwargs["notify_parents"] for c in self.flag.await_args_list]
        self.assertEqual(notify, [True, False, False])
        for c in self.flag.await_args_list:
            self.assertEqual(c.kwargs["description"], "d")  # no staff-only prefix
            self.assertNotIn("mark_quiet", c.kwargs)

    async def test_a_family_case_alerts_the_parent(self):
        for text, flag_type, at_home in (
                ("my dad hits me", "harmful", True), ("my dad hits me", "harmful", False),
                ("my uncle touched me", "harmful", False), ("someone at home hurts me", "harmful", False),
                ("I'm scared of what my stepdad does when mum's out", "sensitive", False),
                ("my uncle showed me bad videos", "inappropriate", False),
                ("ابي العب برا بس بدي اروح البيت", "sensitive", False)):   # ابي/بدي ("I want"), not dad
            self.agent._alerted_rules.clear()
            self.agent._turn_text = text
            await self.call(flag_type, at_home=at_home)
            kw = self.flag.await_args.kwargs
            self.assertTrue(kw["notify_parents"], text)
            self.assertEqual(kw["description"], "d", text)

    async def test_a_flag_closes_sources_for_the_rest_of_the_turn(self):
        await self.call("harmful")
        self.assertTrue(self.agent._flagged_turn)
        self.assertEqual(self.agent._licence(), frozenset())

    async def test_an_off_topic_flag_is_recorded_as_before_but_never_alerts_a_parent(self):
        # hk/12b: off_topic is a record for review only (design lead: record, do not alert)
        for at_home in (False, True):
            self.agent._turn_text = "tell me about scary movies again"
            out = await self.call("off_topic", at_home=at_home)
            self.assertEqual(out, "Recorded.")
            kw = self.flag.await_args.kwargs
            self.assertEqual((kw["message_id"], kw["flag_type"], kw["description"]), (5, "off_topic", "d"))
            self.assertFalse(kw["notify_parents"])
            self.assertNotIn("tool", self.agent._alerted_rules)

    async def test_an_off_topic_flag_never_uses_up_the_sessions_alert(self):
        await self.call("off_topic")
        await self.call("OFF_TOPIC ")  # normalised like any flag type
        await self.call("sensitive")
        await self.call("harmful")
        self.assertEqual([c.kwargs["notify_parents"] for c in self.flag.await_args_list], [False, False, True, False])
        self.assertEqual([c.kwargs["flag_type"] for c in self.flag.await_args_list],
                         ["off_topic", "off_topic", "sensitive", "harmful"])

    async def test_an_off_topic_flag_after_the_alert_is_still_recorded(self):
        await self.call("harmful")
        await self.call("off_topic")
        self.assertEqual(self.flag.await_count, 2)
        self.assertEqual([c.kwargs["notify_parents"] for c in self.flag.await_args_list], [True, False])

    async def test_a_harm_flag_about_a_stranger_alerts_the_parent_once(self):
        self.agent._turn_text = "a man in my game wants photos"
        await self.call("harmful", at_home=False)
        await self.call("harmful", at_home=False)
        self.assertEqual([c.kwargs["notify_parents"] for c in self.flag.await_args_list], [True, False])

    async def test_a_coach_asking_for_secrecy_from_mom_still_alerts_the_parent(self):
        self.agent._turn_text = "my coach wants pics, dont tell my mom"
        await self.call("harmful", at_home=False)
        self.assertTrue(self.flag.await_args.kwargs["notify_parents"])

    async def test_the_tool_never_tells_the_model_whether_a_parent_was_notified(self):
        self.flag.return_value = "Flagged. 1 parent(s) notified."  # what the database helper says
        self.agent._turn_text = "a man in my game wants photos"
        self.assertEqual(await self.call("harmful"), "Recorded.")

    async def test_nothing_is_written_again_in_a_turn_the_guard_already_recorded(self):
        self.agent._safety_turn = True
        out = await self.call("harmful")
        self.assertIn("Already recorded", out)
        self.flag.assert_not_awaited()


class PrepareTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.agent = make_agent_class()()
        # the real _spawn runs the audit/flag tasks; only the database work is replaced
        self.agent._spawn = lambda coro: turn_pipeline.TurnGuardMixin._spawn(self.agent, coro)
        self.records = mock.AsyncMock()
        self.flag = mock.AsyncMock(return_value="ok")
        for target, new in (
            ("conversation.agent.turn_pipeline._write_turn_records", self.records),
            ("conversation.agent.agent_class._create_safety_flag_and_alert", self.flag),
            ("conversation.agent.turn_pipeline._FLAG_WAIT_SECONDS", 0.3),
        ):
            p = mock.patch(target, new=new)
            p.start()
            self.addCleanup(p.stop)

    def hit(self, kind=SAFETY, rule="bullying", notify=True, **kw):
        return GuardHit(kind=kind, rule_id=rule, level="D", flag_type="sensitive", notify_parent=notify,
                        note=f"NOTE {rule}", **kw)

    async def turn(self, hit, new_id=None, text="hello"):
        with mock.patch.object(turn_pipeline, "check", return_value=hit):
            note = self.agent._prepare(text)
        if new_id:
            self.agent._last_child_message_id = new_id
        await drain_guard_tasks(self.agent)
        return note

    async def test_nothing_to_say_injects_nothing_and_writes_nothing(self):
        self.assertEqual(await self.turn(None, new_id=2), "")
        self.records.assert_not_awaited()
        self.flag.assert_not_awaited()
        self.assertFalse(self.agent._safety_turn or self.agent._refer_turn)

    async def test_a_guard_error_fails_closed_with_a_note_and_an_audit_row(self):
        with mock.patch.object(turn_pipeline, "check", side_effect=RuntimeError("boom")), \
                mock.patch.object(turn_pipeline, "_write_reply_audit", mock.AsyncMock()) as audit, \
                self.assertLogs("conversation.agent.turn_pipeline", level="ERROR"):
            self.assertEqual(self.agent._prepare("hello"), turn_pipeline.GUARD_ERROR_NOTE)
            await drain_guard_tasks(self.agent)
        audit.assert_awaited_once_with(1, "GUARD_ERROR", "", [])
        self.assertFalse(self.agent._safety_turn)  # the model's own flag still has to go through

    async def test_a_safety_hit_injects_its_note_audits_and_flags(self):
        note = await self.turn(self.hit(), new_id=7)
        self.assertEqual(note, "NOTE bullying")
        self.assertTrue(self.agent._safety_turn)
        self.assertEqual(self.records.await_args.args[1].rule_id, "bullying")
        kw = self.flag.await_args.kwargs
        self.assertEqual((kw["message_id"], kw["flag_type"], kw["notify_parents"]), (7, "sensitive", True))
        self.assertIn("bullying", kw["description"])

    async def test_a_parent_is_alerted_once_per_rule_but_every_disclosure_is_flagged(self):
        await self.turn(self.hit(), new_id=2)
        await self.turn(self.hit(), new_id=3)
        self.assertEqual([c.kwargs["notify_parents"] for c in self.flag.await_args_list], [True, False])
        await self.turn(self.hit(rule="other_rule"), new_id=4)
        self.assertTrue(self.flag.await_args.kwargs["notify_parents"])

    async def test_a_family_rule_alerts_the_parent_and_never_silences_a_later_alert(self):
        # hk/12g: notify_parent=false only picks the rule (its home-harm reply); the parent is alerted
        await self.turn(self.hit(rule="hitting_at_home", notify=False), new_id=2)
        kw = self.flag.await_args.kwargs
        self.assertTrue(kw["notify_parents"])
        self.assertTrue(kw["description"].startswith("Automatic turn guard"))  # no staff-only prefix
        await self.turn(self.hit(rule="bullying", notify=True), new_id=3)  # a later rule alerts too
        self.assertTrue(self.flag.await_args.kwargs["notify_parents"])
        self.assertEqual([c.args[1].kind for c in self.records.await_args_list], [SAFETY, SAFETY])

    async def test_no_message_id_means_no_flag_on_the_previous_message(self):
        self.agent._last_child_message_id = 41
        await self.turn(self.hit(), new_id=None)
        self.flag.assert_not_awaited()

    async def test_a_refer_hit_injects_its_note_audits_and_flags_nothing(self):
        hit = GuardHit(kind=REFER, rule_id="personal_ruling", level="D", note="REFER NOTE")
        note = await self.turn(hit, new_id=2)
        self.assertEqual(note, "REFER NOTE")
        self.assertTrue(self.agent._refer_turn)
        self.assertFalse(self.agent._safety_turn)
        self.assertEqual(self.records.await_args.args[1], hit)
        self.flag.assert_not_awaited()
        out = await self.agent.search_bank(question="is it ok", topic="worship", values=None)
        self.assertIn("safety or a referral: no sources", out)
        await self.turn(None)  # the next turn is an ordinary one again
        self.assertFalse(self.agent._refer_turn)

    async def test_the_childs_words_are_kept_for_the_family_check(self):
        await self.turn(None, text="my uncle touched me")
        self.assertEqual(self.agent._turn_text, "my uncle touched me")

    async def test_the_turn_language_follows_the_childs_words(self):
        await self.turn(None, text="ما هي الصلاة")
        self.assertEqual(self.agent._turn_language, "ar")
        await self.turn(None, text="what is prayer")
        self.assertEqual(self.agent._turn_language, "en")


if __name__ == "__main__":
    unittest.main()
