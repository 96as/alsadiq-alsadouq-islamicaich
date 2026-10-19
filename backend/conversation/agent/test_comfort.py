"""Comfort verses (hk/13b): ``search_bank(topic="comfort")`` serves only the fixed COMFORT set, never keyword
matches, and never on a safety, referral, flagged or disclosure turn. Placeholder text only: no scripture."""
from __future__ import annotations

import unittest
from unittest import mock

from conversation.agent import bank_search, turn_pipeline
from conversation.agent.retrieval import ValueIndex
from conversation.agent.test_bank_tool import ARABIC, GUIDE, _speak, item, make_agent_class, value

COMFORT_REFS = {ref for _f, _w, refs in bank_search.COMFORT for ref in refs}


def comfort_bank():
    refs = sorted(COMFORT_REFS)
    items = [item(pk, "verse", surah=s, ayah=a, arabic_text=ARABIC, child_explanation_en=f"Comfort {pk}",
                  verification_status="seeded" if (s, a) == (39, 10) else "reviewed")
             for pk, (s, a) in enumerate(refs, 1)]
    # a value verse whose keywords are distress words: comfort must never pull it in
    items.append(item(99, "verse", surah=49, ayah=12, arabic_text=ARABIC, child_explanation_en="Lesson",
                      keywords_en=["sad", "scared", "died", "exam", "dark"]))
    links = [("honesty", 99, 0)] + [("patience", pk, 0) for pk in range(1, len(refs) + 1)]
    return ValueIndex.from_records([value("honesty", ["lie"], 1), value("patience", ["patient"], 2)], items, links)


def refs(items):
    return [(i.surah, i.ayah) for i in items]


class ComfortSearchTests(unittest.TestCase):
    def setUp(self):
        self.index = comfort_bank()

    def test_comfort_returns_only_the_reviewed_comfort_set(self):
        for q in ("I'm sad", "I'm scared of the dark", "my cat died", "exam tomorrow, I'm nervous",
                  "I lie and I am sad", "is there a verse about honesty", "", "مات جدي", "أخاف من الظلام"):
            for values in ([], ["honesty"]):
                got = bank_search.search(self.index, q, "comfort", values, "en", None)
                self.assertTrue(got, q)
                self.assertTrue(set(refs(got)) <= COMFORT_REFS, (q, refs(got)))
                self.assertNotIn((39, 10), refs(got))   # seeded, not reviewed
                self.assertLessEqual(len(got), 2)

    def test_the_feeling_picks_the_first_verse(self):
        for q, first in (("I'm scared of the dark", (20, 46)), ("my grandma died", (2, 153)),
                         ("I'm nervous about my exam", (65, 3)), ("I feel sad today", (13, 28)),
                         ("ماتت قطتي", (2, 153)), ("خايف من الامتحان", (20, 46))):
            self.assertEqual(refs(bank_search.search(self.index, q, "comfort", [], "en", None))[0], first, q)

    def test_values_topic_on_distress_words_still_finds_no_lesson_card_from_comfort(self):
        # comfort goes through its topic only: the comfort set is not keyword-matched on other topics
        got = bank_search.search(self.index, "I'm sad", "values", [], "en", None)
        self.assertFalse(set(refs(got)) & COMFORT_REFS)

    def test_one_verse_at_most_and_the_comfort_guidance(self):
        got = bank_search.search(self.index, "I'm sad", "comfort", [], "en", None)
        out = bank_search.format_result(got, "en", None, "comfort", GUIDE)
        self.assertIn("(at most 1)", out)
        self.assertIn("<comfort>", out)

    def test_disclosures_block_comfort(self):
        for text in ("he said it's our secret", "my uncle touched me and I'm scared", "my dad hits me",
                     "I want to hurt myself", "a man asked me to change in front of him", "عمي قال سر بيننا",
                     "أبوي يضربني", "أبي أموت"):
            self.assertTrue(bank_search.comfort_blocked(text), text)
        # review of #83: photos, hurt, smacked, kiss, clothes, "between us", "nobody can know", and Arabic forms
        for text in ("he wants photos", "send pictures of me", "he hurt me", "my brother hurts me", "he smacked me",
                     "he tried to kiss me", "he said take off my clothes", "keep it between us",
                     "no one must know", "nobody can know", "لا تخبر أحد", "ما تقول لماما", "ما تقول لبابا",
                     "عندي أسرار مع عمي", "هذا سري", "يأذيني", "يبي صوري", "صورني", "أذيت نفسي", "آذي نفسي"):
            self.assertTrue(bank_search.comfort_blocked(text), text)
        for text in ("my cat died", "I'm scared of the dark", "kids teased me at school", "I'm nervous about my exam",
                     "أنا حزين على سريري", "عيد سعيد وسرور", "أسرتي تحبني", "خايف من الامتحان"):
            self.assertFalse(bank_search.comfort_blocked(text), text)


class ComfortToolTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.agent = make_agent_class()()
        self.agent._value_index = comfort_bank()
        self.agent._turn_text = "my cat died"

    async def test_a_sad_turn_gets_a_comfort_verse(self):
        out = await self.agent.search_bank(question="my cat died", topic="comfort", values=[])
        self.assertTrue(out.startswith("FOUND"))
        self.assertTrue(set(refs(self.agent._turn_items)) <= COMFORT_REFS)

    async def test_no_comfort_on_a_safety_refer_flagged_or_disclosure_turn(self):
        for flag, text in (("_safety_turn", "my cat died"), ("_refer_turn", "my cat died"),
                           ("_flagged_turn", "my cat died"), (None, "he said it's our secret, I'm scared")):
            agent = make_agent_class()()
            agent._value_index, agent._turn_text = comfort_bank(), text
            if flag:
                setattr(agent, flag, True)
            out = await agent.search_bank(question="the child is scared", topic="comfort", values=[])
            self.assertIn("no sources", out, (flag, text))
            self.assertEqual(agent._turn_items, [], (flag, text))

    async def test_after_a_disclosure_or_a_flag_no_comfort_for_the_rest_of_the_session(self):
        await self.agent.search_bank(question="x", topic="comfort", values=[])   # a fresh turn: allowed
        self.agent._turn_text = "he said it's our secret"
        self.assertIn("no sources", await self.agent.search_bank(question="x", topic="comfort", values=[]))
        self.agent._prepare("I don't want anyone to know")   # next turn, no disclosure words in it
        self.assertIn("no sources", await self.agent.search_bank(question="sad", topic="comfort", values=[]))
        self.assertTrue((await self.agent.search_bank(question="lie", topic="values", values=["honesty"])))
        flagged = make_agent_class()()
        flagged._value_index, flagged._turn_text = comfort_bank(), "my cat died"
        await flagged.flag_safety_concern(flag_type="sensitive", description="d")
        flagged._prepare("my cat died")
        self.assertIn("no sources", await flagged.search_bank(question="sad", topic="comfort", values=[]))

    async def test_a_disclosure_turn_with_no_search_and_no_flag_still_blocks_later_comfort(self):
        with mock.patch.object(turn_pipeline, "check", return_value=None):   # a guard miss: no SAFETY turn
            self.agent._prepare("my uncle said it's our secret")   # and the model neither searched nor flagged
            self.assertFalse(self.agent._safety_turn)
            self.agent._prepare("I'm sad")
        self.assertIn("no sources", await self.agent.search_bank(question="sad", topic="comfort", values=[]))

    async def test_one_comfort_verse_per_session(self):
        self.assertTrue((await self.agent.search_bank(question="my cat died", topic="comfort", values=[])).startswith("FOUND"))
        self.agent._prepare("she was fluffy")
        out = await self.agent.search_bank(question="sad", topic="comfort", values=[])
        self.assertIn("already shared", out)
        self.assertEqual(self.agent._turn_items, [])

    async def test_a_comfort_marker_after_a_flag_publishes_no_card(self):
        await self.agent.search_bank(question="my cat died", topic="comfort", values=[])
        pk = self.agent._turn_items[0].pk
        self.agent._flagged_turn = True
        out = await _speak(self.agent, "I'm here {{card:%d}} with you." % pk)
        self.assertEqual(out, "I'm here with you.")
        self.assertEqual([p for t, p in self.agent.events if t == "reference"], [])


if __name__ == "__main__":
    unittest.main()
