"""Persona wording after the 5 Oct lead decisions: the name is الصديق الصدوق,
'the truthful friend'; the Arabic nickname is الصديق (never صادق); honesty is
one value among many in the prompt and the points directives. Ported in hk/12 to the
single prompt (conversation/agent/prompt.py); the old HOPE AND ACCOUNTABILITY paragraph
is now one prompt rule plus guidance/afterlife.md."""
from django.test import SimpleTestCase

from conversation.agent import bank_search, entrypoint
from conversation.agent.agent_class import AlSadiqAgent


def instructions(language="en"):
    return AlSadiqAgent(db_session_id=1, child_id=1, language=language).instructions


class PersonaNameTests(SimpleTestCase):
    def test_name_means_the_truthful_friend(self):
        text = instructions()
        self.assertIn("truthful friend", text)
        self.assertIn("الصديق الصدوق", text)
        self.assertNotIn("The Truthful'", text)
        self.assertNotIn("Honesty is the trait you value most", text)

    def test_arabic_nickname_is_al_sadiq_in_both_languages(self):
        for lang in ("en", "ar"):
            text = instructions(lang)
            self.assertIn("أنا الصديق،", text)
            self.assertNotIn("صادق", text, f"old nickname in {lang} prompt")

    def test_first_meeting_line_uses_al_sadiq(self):
        ar = entrypoint._FIRST_MEETING_AI_LINE["ar"]
        self.assertIn("الصديق", ar)
        self.assertNotIn("صادق", ar)
        self.assertIn("Sadiq", entrypoint._FIRST_MEETING_AI_LINE["en"])
        self.assertIn("ذكاء اصطناعي ولست", ar)
        self.assertNotIn("كمبيوتر", ar)
        self.assertIn("an AI friend", entrypoint._FIRST_MEETING_AI_LINE["en"])

    def test_persona_rules_survive_the_rewrite(self):
        text = instructions()
        self.assertIn("an AI, not a person", text)
        self.assertIn("AI friend", text)
        self.assertNotIn("computer friend", text)
        self.assertNotIn("كمبيوتر", text)
        self.assertIn("ذكاء اصطناعي ولست", text)
        self.assertIn("No source, no answer", text)


class ValuesNotHonestyFirstTests(SimpleTestCase):
    def test_purpose_and_points_cover_all_values(self):
        text = instructions()
        self.assertNotIn("develop honesty", text)
        self.assertNotIn("brave honesty moment", text)
        self.assertIn("honesty, kindness, patience, gratitude, mercy", text)  # honesty is one value among many
        self.assertIn("practising a value", text)
        self.assertIn("forgiving", text)
        # amounts unchanged
        for amount in ("(+10)", "(+5)", "(-3)", "(-8)"):
            self.assertIn(amount, text)

    def test_record_engagement_description_is_value_neutral(self):
        agent = AlSadiqAgent(db_session_id=1, child_id=1)
        tool = next(t for t in agent.tools if t.id == "record_engagement")
        self.assertNotIn("brave honesty", tool.info.description)
        self.assertIn("practising", tool.info.description)


class HopeAndAccountabilityTests(SimpleTestCase):
    """5 Oct lead decision: hope first, gentle accountability (scholar-consulted)."""

    def test_hope_first_is_in_the_prompt_in_both_languages(self):
        for lang in ("en", "ar"):
            text = instructions(lang)
            self.assertIn("Hope first, gentle accountability", text)
            self.assertIn("lead with Allah's love, mercy and forgiveness", text)
            self.assertIn("never use the Fire as a threat", text)

    def test_the_afterlife_guidance_keeps_the_age_bands_and_the_comfort(self):
        guide = " ".join(bank_search.load_guidance()["afterlife"].split())
        for phrase in ("Jannah", "the Fire", "the Last Day", "Hope first", "For ages 6 to 9", "10 to 13",
                       "never graphic", "Never use it as a threat", "never say where any person is going",
                       "comfort first", "Most Merciful"):
            self.assertIn(phrase, guide)
        self.assertEqual(bank_search.guidance_names([], "afterlife"), ["no_source", "afterlife"])

    def test_no_escalation_rule_stays_and_never_judges_a_person(self):
        text = instructions()
        self.assertIn("Never intensify fear, conflict or distress", text)
        self.assertIn("never use fear to make a child behave", text)
        self.assertIn("judge a person or group", text)

    def test_unchanged_guards_remain(self):
        text = instructions()
        self.assertIn("No source, no answer", text)
        self.assertIn("judge a person or group", text)
        self.assertIn("an AI, not a person", text)
