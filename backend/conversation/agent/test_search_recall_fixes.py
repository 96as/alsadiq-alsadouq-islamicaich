"""Tests for task 13's search fixes: loose value-name matching, the topic filter before the top-3 cut, the
related-item fallback, the "last card shown" hint, and the child words added as value keywords.

Every Quran or hadith word here is a PLACEHOLDER; no scripture text appears in this file.

Run from backend/:  python manage.py test conversation.agent.test_search_recall_fixes \
    --settings=config.settings_sqlite_test
"""
from __future__ import annotations

import json
import os
import unittest
from collections import Counter
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from conversation.agent import bank_search, turn_pipeline
from conversation.agent.retrieval import ValueIndex, load_synonyms, load_weak_keywords
from conversation.agent.test_bank_tool import ARABIC, GUIDE, _speak, item, make_agent_class, pks

CONTENT = Path(__file__).resolve().parents[2] / "session_moral_context" / "content"
PHRASINGS = Path(__file__).resolve().parents[1] / "eval" / "search_recall_phrasings.yaml"


def val(slug, name_en, name_ar, kw_en=(), kw_ar=(), order=0):
    return SimpleNamespace(slug=slug, name_en=name_en, name_ar=name_ar, keywords_en=list(kw_en),
                           keywords_ar=list(kw_ar), order=order)


def small_bank():
    values = [
        val("honesty", "Honesty", "الصدق", ["honest", "truth"], ["الصدق"], 1),
        val("keeping-promises", "Keeping Promises", "الوفاء بالوعد", ["promise"], ["وعد"], 2),
        val("seeking-knowledge", "Seeking Knowledge", "طلب العلم", ["study"], ["علم"], 3),
    ]
    items = [
        item(1, "verse", surah=1, ayah=1, arabic_text=ARABIC, keywords_en=["lying"], child_explanation_en="E1"),
        item(2, "verse", surah=1, ayah=2, arabic_text=ARABIC, keywords_en=["lying"], child_explanation_en="E2"),
        item(3, "verse", surah=1, ayah=3, arabic_text=ARABIC, keywords_en=["lying"], child_explanation_en="E3"),
        item(4, "hadith", book="B", number="4", grade="sahih", grader="G", arabic_text=ARABIC,
             keywords_en=["lying"], child_explanation_en="E4"),
        item(5, "hadith", book="B", number="5", grade="sahih", grader="G", arabic_text=ARABIC,
             child_explanation_en="E5"),
        item(6, "hadith", book="B", number="6", grade="sahih", grader="G", arabic_text=ARABIC,
             child_explanation_en="E6"),
        item(7, "hadith", book="B", number="7", grade="sahih", grader="G", arabic_text=ARABIC,
             child_explanation_en="E7"),
    ]
    links = [("honesty", 1, 0), ("honesty", 2, 1), ("honesty", 3, 2), ("honesty", 4, 3),
             ("keeping-promises", 5, 0), ("seeking-knowledge", 6, 0), ("seeking-knowledge", 7, 1)]
    return ValueIndex.from_records(values, items, links)


class LooseValueNameTests(unittest.TestCase):
    def setUp(self):
        self.index = small_bank()

    def slugs(self, *names):
        return bank_search._value_slugs(self.index, list(names))

    def test_name_keyword_case_and_singular_plural_all_find_the_value(self):
        self.assertEqual(self.slugs("honest"), ["honesty"])          # a keyword, not the name
        self.assertEqual(self.slugs("HoNeSt"), ["honesty"])
        self.assertEqual(self.slugs("keeping promise"), ["keeping-promises"])   # singular of the name
        self.assertEqual(self.slugs("promises"), ["keeping-promises"])          # plural of a keyword
        self.assertEqual(self.slugs("keeping-promises"), ["keeping-promises"])  # the slug

    def test_arabic_clitics_and_the_arabic_name_match(self):
        self.assertEqual(self.slugs("بالصدق"), ["honesty"])
        self.assertEqual(self.slugs("الصدق"), ["honesty"])
        self.assertEqual(self.slugs("طلب العلم"), ["seeking-knowledge"])

    def test_one_value_per_name_in_the_models_order_at_most_two_unknown_ignored(self):
        self.assertEqual(self.slugs("study", "nonsense", "honest"), ["seeking-knowledge", "honesty"])
        self.assertEqual(self.slugs("honest", "promise", "study"), ["honesty", "keeping-promises"])
        self.assertEqual(self.slugs("nonsense", "", "  "), [])

    def test_the_name_beats_a_keyword_hit_of_another_value(self):
        index = ValueIndex.from_records(
            [val("a", "Alpha", "ألف", ["beta"], [], 1), val("b", "Beta", "باء", [], [], 2)], [], [])
        self.assertEqual(bank_search._value_slugs(index, ["beta"]), ["b"])


class TopicFilterTests(unittest.TestCase):
    def test_hadith_search_is_not_emptied_by_three_better_matching_verses(self):
        index = small_bank()
        got = bank_search.search(index, "why is lying bad", "hadith", [], "en", None)
        self.assertEqual(pks(got), [4])
        self.assertFalse(got.related)


class RelatedFallbackTests(unittest.TestCase):
    def setUp(self):
        self.index = small_bank()

    def test_no_verse_for_the_value_returns_its_hadith_marked_related(self):
        got = bank_search.search(self.index, "x", "quran", ["seeking knowledge"], "en", None)
        self.assertEqual(pks(got), [6, 7])
        self.assertTrue(got.related)

    def test_at_most_two_related_items(self):
        index = small_bank()
        got = bank_search.search(index, "x", "hadith", ["honesty"], "en", None)    # honesty has a hadith: normal
        self.assertFalse(got.related)
        got = bank_search.search(index, "x", "quran", ["keeping promises"], "en", None)
        self.assertEqual((pks(got), got.related), ([5], True))

    def test_nothing_at_all_stays_empty_and_unrelated(self):
        got = bank_search.search(self.index, "zzz", "quran", [], "en", None)
        self.assertEqual((list(got), got.related), ([], False))

    def test_a_normal_hit_is_never_marked_related(self):
        got = bank_search.search(self.index, "x", "quran", ["honesty"], "en", None)
        self.assertTrue(got and not got.related)

    def test_values_topic_has_nothing_to_fall_back_to(self):
        index = ValueIndex.from_records([val("a", "Alpha", "ألف")], [item(1, "tafsir", keywords_en=["alpha"])],
                                        [("a", 1, 0)])
        self.assertEqual(list(bank_search.search(index, "x", "values", ["alpha"], "en", None)), [])

    def test_the_header_says_what_was_not_found(self):
        got = bank_search.search(self.index, "x", "quran", ["seeking knowledge"], "en", None)
        text = bank_search.format_result(got, "en", None, "quran", GUIDE)
        self.assertTrue(text.startswith("NO verse FOUND for this; RELATED items from the same value:"), text)
        self.assertIn("{{card:6}}", text)
        got = bank_search.search(self.index, "x", "hadith", ["honesty"], "en", None)
        text = bank_search.format_result(got, "en", None, "hadith", GUIDE)
        self.assertTrue(text.startswith("FOUND 1."), text)


class CardHintTests(unittest.TestCase):
    def setUp(self):
        self.items = bank_search.search(small_bank(), "x", "values", ["honesty"], "en", None)

    def head(self, n):
        return bank_search.format_result(self.items, "en", None, "values", GUIDE, turns_since_card=n).split("\n")[0]

    def test_the_header_says_how_long_ago_a_card_was_shown(self):
        self.assertIn(" Last card shown: 3 turns ago. ", self.head(3))
        self.assertIn(" Last card shown: this turn. ", self.head(0))
        self.assertIn(" Last card shown: 1 turn ago. ", self.head(1))
        self.assertIn(" No card shown yet this session. ", self.head(None))
        self.assertTrue(self.head(3).startswith(f"FOUND {len(self.items)}. Last card shown: 3 turns ago. Only these"))

    def test_not_found_has_no_hint(self):
        self.assertNotIn("card shown", bank_search.format_result([], "en", None, "creed", GUIDE, turns_since_card=2))


class TurnCounterTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.agent = make_agent_class()()
        self.agent._turn_language = "en"
        p = mock.patch.object(turn_pipeline, "check", return_value=None)
        p.start()
        self.addCleanup(p.stop)

    async def ask(self):
        return await self.agent.search_bank(question="why be honest", topic="values", values=["honesty"])

    async def test_none_until_a_card_is_shown_then_counts_turns(self):
        self.assertIsNone(self.agent._turns_since_card)
        self.agent._prepare("hi")                                   # turn 1
        self.assertIn("No card shown yet this session.", await self.ask())
        await _speak(self.agent, "Honesty matters {{card:1}}.")     # card published in turn 1
        self.assertEqual(self.agent._turns_since_card, 0)
        self.agent._prepare("and?")                                 # turn 2
        self.assertIn("Last card shown: 1 turn ago.", await self.ask())
        self.agent._prepare("why?")                                 # turn 3
        self.assertEqual(self.agent._turns_since_card, 2)
        self.assertIn("Last card shown: 2 turns ago.", await self.ask())

    async def test_a_recited_card_is_not_a_new_card(self):
        self.agent._prepare("hi")
        await self.ask()
        await _speak(self.agent, "A {{card:1}}.")
        self.agent._prepare("again")
        self.agent._prepare("again")
        await self.ask()
        await _speak(self.agent, "A {{card:1}}.")                   # already shown this session: stripped, no card
        self.assertEqual(self.agent._turns_since_card, 2)

    async def test_a_turn_with_no_card_does_not_reset_it(self):
        self.agent._prepare("hi")
        await self.ask()
        await _speak(self.agent, "A {{card:1}}.")
        self.agent._prepare("thanks")
        self.assertEqual(self.agent._turns_since_card, 1)


class ChildWordsTests(unittest.TestCase):
    """The shipped keywords and retrieval_synonyms, over one placeholder verse and hadith per value."""

    @classmethod
    def setUpClass(cls):
        values = json.loads((CONTENT / "values.json").read_text(encoding="utf-8"))
        vals = [SimpleNamespace(slug=v["slug"], name_en=v["name_en"], name_ar=v["name_ar"],
                                keywords_en=v["keywords_en"], keywords_ar=v["keywords_ar"], order=v["order"])
                for v in values]
        items, links, pk = [], [], 0
        for v in vals:
            for type_ in ("verse", "hadith"):
                if v.slug == "visiting-the-sick" and type_ == "verse":
                    continue    # the real bank has no verse for this value
                pk += 1
                items.append(item(pk, type_, surah=1 if type_ == "verse" else None, ayah=pk if type_ == "verse" else None,
                                  arabic_text=ARABIC, child_explanation_en="E", child_explanation_ar="ش",
                                  book="B", number=str(pk), grade="sahih", grader="G"))
                links.append((v.slug, pk, 0))
        cls.records = (vals, items, links)
        cls.index = ValueIndex.from_records(vals, items, links, load_synonyms(), load_weak_keywords())

    def right_value(self, text, topic, slug, lang="en", values=()):
        got = bank_search.search(self.index, text, topic, list(values), lang, None)
        return any(slug in self.index.items[i.pk].value_slugs for i in got), got

    def test_phrasings_that_used_to_miss_now_find_their_value(self):
        cases = [
            ("my friend cheated on the test and I did not tell the teacher, what should I do?", "values", "honesty", "en"),
            ("is there a hadith about breaking your word?", "hadith", "keeping-promises", "en"),
            ("what does Islam say about showing off?", "values", "humility", "en"),
            ("is there a verse about forgiving people?", "quran", "forgiveness", "en"),
            ("شو يقول الإسلام عن التفاخر؟", "values", "humility", "ar"),
            ("في حديث عن إفشاء السلام؟", "hadith", "spreading-salam", "ar"),
            ("ولد سلم علي وما رديت عليه، هذا غلط؟", "values", "spreading-salam", "ar"),
            ("is there a hadith about how to eat?", "hadith", "table-manners", "en"),
            ("I left half my food on the plate and threw it away, is that bad?", "values", "not-wasting", "en"),
            ("my friend is sick at home and I want to cheer him up, what can I do?", "values", "visiting-the-sick", "en"),
        ]
        for text, topic, slug, lang in cases:
            ok, got = self.right_value(text, topic, slug, lang)
            self.assertTrue(ok, f"{slug}: {text} -> {[self.index.items[i.pk].value_slugs for i in got]}")

    def test_grief_and_disclosure_turns_find_nothing(self):
        # review of hk/13: these child words must never pull a value card (orphan verses on "my dad died",
        # modesty verses on a disclosure, courage verses on bullying)
        for text, lang in (("my dad died", "en"), ("I have no dad", "en"), ("مات أبوي", "ar"),
                           ("my dad died last week", "en"), ("a man asked me to change in front of him", "en"),
                           ("I'm being bullied at school", "en"), ("my parents are not talking", "en"),
                           ("someone is watching me", "en"),
                           # review of #76 (26fb0028), and the sweep of the same kind of word
                           ("he said don't tell anyone, it's a secret", "en"), ("سر بيني وبينه", "ar"),
                           ("my dad shouted at my mom and hit her", "en"), ("my cat died", "en"),
                           ("أخاف من الظلام", "ar"), ("أنا زعلان", "ar"),
                           ("my friends are mean to me every day", "en"), ("أمي مريضة وتعبانة", "ar"),
                           ("ظلمني المعلم وضربني", "ar"), ("ضربت", "ar"), ("I failed my exam", "en"),
                           ("رسبت في الاختبار", "ar"), ("I got angry and screamed", "en"),
                           ("تخانقت مع صاحبي", "ar"), ("we are visiting my cousins", "en"),
                           # round 2 of the #76 review: an ask cue must not re-open a death, fear or
                           # secret turn (the veto list)
                           ("my grandma died, what can I do", "en"), ("جدي مات، شو أعمل", "ar"),
                           ("ماتت جدتي وش اسوي", "ar"), ("is it wrong to be sad when my grandpa died?", "en"),
                           ("I'm scared, what do I do", "en"), ("أخاف أنام لحالي وش اسوي", "ar"),
                           ("أنا خايف، شو أعمل", "ar"), ("عمي قال لي سر وما أقول لأحد، غلط؟", "ar"),
                           ("my uncle told me to keep a secret, is it bad?", "en"),
                           ("my cat died, what can I do", "en"), ("my dog died what do I do", "en"),
                           ("they laugh about me behind my back", "en"),
                           # round 3: hitting, mocking, more spellings of death, and serious illness
                           ("يضربوني بالمدرسة وش اسوي", "ar"), ("يتمسخرون علي بالمدرسة شو أسوي", "ar"),
                           ("تضربني أختي شو اسوي", "ar"), ("يضربونا بالمدرسة وش اسوي", "ar"),
                           ("ضربني ولد وش اسوي", "ar"), ("they keep hitting me, what can I do", "en"),
                           ("my brother hits me, what should I do", "en"),
                           ("they make fun of me at school, what can I do", "en"),
                           ("kids are calling me names, what do I do", "en"), ("توفت جدتي وش اسوي", "ar"),
                           ("جدي متوفي وش اسوي", "ar"), ("my grandma is very ill", "en"),
                           ("my grandma is very ill, what can I do", "en"), ("جدتي مريضة كثير", "ar"),
                           ("جدتي مريضة كثير شو أسوي", "ar"), ("ستي مريضة كتير شو بعمل", "ar")):
            got = bank_search.search(self.index, text, "values", [], lang, None)
            self.assertEqual([self.index.items[i.pk].value_slugs for i in got], [], text)

    def test_the_weak_keywords_flag_never_switches_the_veto_off(self):
        with mock.patch.dict(os.environ, {"RETRIEVAL_WEAK_KEYWORDS": "0"}):
            weak = load_weak_keywords()
        self.assertFalse(weak.words)
        index = ValueIndex.from_records(*self.records, load_synonyms(), weak)
        for text in ("my grandma died, what can I do", "يضربوني بالمدرسة وش اسوي"):
            self.assertEqual(bank_search.search(index, text, "values", [], "en", None), [], text)
        self.assertTrue(bank_search.search(index, "is there a verse about visiting sick people?", "quran", [], "en", None))

    def test_a_value_name_the_model_makes_up_still_finds_the_value(self):
        for name, slug in (("truthfulness", "honesty"), ("kindness", "mercy"), ("tawakkul", "trust-in-allah"),
                           ("fairness", "justice"), ("remembrance", "remembering-allah"), ("التسامح", "forgiveness")):
            self.assertEqual(bank_search._value_slugs(self.index, [name]), [slug], name)

    def test_the_lead_example_a_verse_for_a_value_with_no_verse_offers_the_hadith(self):
        ok, got = self.right_value("is there a verse about visiting sick people?", "quran", "visiting-the-sick")
        self.assertTrue(ok and got.related and all(i.type == "hadith" for i in got))


class PhrasingFileTests(unittest.TestCase):
    def test_five_english_and_five_arabic_phrasings_for_every_value(self):
        from conversation.eval_support import search_recall as sr
        slugs = {v["slug"] for v in json.loads((CONTENT / "values.json").read_text(encoding="utf-8"))}
        cases = sr.load_phrasings(PHRASINGS)
        self.assertEqual(len(cases), 380)
        per = Counter((c["value"], c["lang"]) for c in cases)
        self.assertEqual({k[0] for k in per}, slugs)
        self.assertEqual(set(per.values()), {5})
        self.assertEqual({c["shape"] for c in cases}, {"verse", "hadith", "say", "sit"})
        self.assertEqual(len({sr.case_key(c) for c in cases}), 380)
        self.assertEqual({c["topic"] for c in cases if c["shape"] == "verse"}, {"quran"})
        self.assertTrue(all(any("؀" <= ch <= "ۿ" for ch in c["text"]) == (c["lang"] == "ar") for c in cases))


class RecallReportTests(unittest.TestCase):
    def test_a_miss_is_classified_and_the_summary_counts_it(self):
        from conversation.eval_support import search_recall as sr
        index = small_bank()
        ask = {"value": "seeking-knowledge", "lang": "en", "shape": "sit", "text": "x", "topic": "values"}
        hit = sr.run_one(index, ask, "I want to study", "values", [])
        self.assertTrue(hit["found"] and hit["right"])
        miss = sr.run_one(index, ask, "zzz", "values", ["nonsense"])
        self.assertEqual((miss["found"], miss["right"], miss["miss"]), (False, False, "value_name_unmatched"))
        self.assertEqual(sr.run_one(index, ask, "zzz", "values", [])["miss"], "no_keyword")
        self.assertEqual(sr.run_one(index, ask, "why is lying bad", "values", ["honesty"])["miss"], "other_value")
        gap = {"value": "keeping-promises", "lang": "en", "shape": "verse", "text": "x", "topic": "quran"}
        self.assertEqual(sr.classify_miss(index, gap, "x", "quran", ["keeping promises"]), "bank_gap")   # no verse
        rows = [{**ask, "a": hit, "b": miss}]
        s = sr.summarise(rows, ["seeking-knowledge"])
        self.assertEqual((s["a"]["right_value"], s["b"]["not_found"], s["b"]["miss_classes"]),
                         (1.0, 1.0, {"value_name_unmatched": 1}))


if __name__ == "__main__":
    unittest.main()
