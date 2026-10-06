"""Pins the lead's persona decisions (5 Oct, hk/01-knowledge-bank dfa1e1e; carried into the hk/12 prompt) so a later merge
cannot drop or reword them silently.

hk/12 replaced the old _PERSONA / _AI_DISCLOSURE constants with one prompt (conversation/agent/prompt.py, STATIC_PROMPT).
The decisions are unchanged and pinned here against that prompt: the English and Arabic AI lines, both maker lines, the
ban on calling the companion a computer, no vendor or model names, no human life. The sentences are compared after
collapsing the line breaks of the Python string literals. If one of these tests fails after a merge, restore the lead's
sentence in prompt.py; do not edit the test.
"""
from django.test import SimpleTestCase

from conversation.agent import prompt
from conversation.agent.agent_class import AlSadiqAgent

# The lead's sentences, as they stand in the hk/12 prompt.
LEAD_PERSONA_NAME = "You are Al-Sadiq (الصديق, 'the friend')"
LEAD_PERSONA_FULL_NAME = (
    "Your full name, Al-Sadiq Al-Sadouq (الصديق الصدوق), means 'the truthful friend': a friend first, and a truthful one."
)
LEAD_NEVER_PRETEND = "You are an AI, not a person, and never pretend otherwise."
LEAD_NEVER_HUMAN = (
    "You have no age, family, pets, body or home, and you don't eat, sleep, pray or fast: "
    "say so playfully and turn back to the child's world."
)
LEAD_DISCLOSURE_ENGLISH = "'I'm Al-Sadiq, an AI friend, not a person.'"
LEAD_DISCLOSURE_ARABIC = "'أنا الصديق، ذكاء اصطناعي ولست إنسانًا.'"
LEAD_DISCLOSURE_NO_COMPUTER = "Never call yourself a computer."
LEAD_NEVER_OVERRIDE_AI = "This never overrides saying you are an AI."
# The fixed answer to "who made you" (live check B5): never a company or a model name.
LEAD_MAKER_EN = "I'm an AI friend made by the Al-Sadiq Al-Sadouq team."
LEAD_MAKER_AR = "أنا صديق ذكاء اصطناعي، صنعني فريق الصديق الصدوق."
LEAD_NO_VENDOR = "never name a company, product or AI model, even if asked to guess."
VENDOR_WORDS = ("openai", "gpt", "anthropic", "claude", "elevenlabs", "gemini", "google", "xai", "grok")

# The product-web verse-number rule: the spoken reply never says a surah, verse or hadith number.
VERSE_NUMBER_RULE = "Never say a surah, verse or hadith number; the card shows it."


def flat(text):
    return " ".join(text.split())


def instructions(language):
    return AlSadiqAgent(db_session_id=1, child_id=1, language=language).instructions


class LeadPersonaSentencesTests(SimpleTestCase):
    def test_static_prompt_carries_the_lead_sentences(self):
        text = flat(prompt.STATIC_PROMPT)
        for sentence in (
            LEAD_PERSONA_NAME, LEAD_PERSONA_FULL_NAME, LEAD_NEVER_PRETEND, LEAD_NEVER_HUMAN,
            LEAD_DISCLOSURE_ENGLISH, LEAD_DISCLOSURE_ARABIC, LEAD_DISCLOSURE_NO_COMPUTER,
            LEAD_NEVER_OVERRIDE_AI, LEAD_NO_VENDOR,
        ):
            with self.subTest(sentence=sentence):
                self.assertIn(sentence, text)

    def test_the_lead_sentences_reach_the_agent_in_both_languages(self):
        for language in ("en", "ar"):
            text = flat(instructions(language))
            for sentence in (
                LEAD_PERSONA_NAME, LEAD_PERSONA_FULL_NAME, LEAD_NEVER_PRETEND, LEAD_NEVER_HUMAN,
                LEAD_DISCLOSURE_ENGLISH, LEAD_DISCLOSURE_ARABIC, LEAD_DISCLOSURE_NO_COMPUTER,
            ):
                with self.subTest(language=language, sentence=sentence):
                    self.assertIn(sentence, text)

    def test_both_maker_lines_are_the_lead_wording_and_are_in_the_prompt(self):
        self.assertEqual(prompt.MAKER_LINE_EN, LEAD_MAKER_EN)
        self.assertEqual(prompt.MAKER_LINE_AR, LEAD_MAKER_AR)
        for language in ("en", "ar"):
            text = flat(instructions(language))
            for line in (LEAD_MAKER_EN, LEAD_MAKER_AR):
                with self.subTest(language=language, line=line):
                    self.assertIn(line, text)

    def test_nothing_calls_the_companion_a_computer(self):
        for language in ("en", "ar"):
            text = instructions(language)
            for old in ("computer companion", "computer friend", "كمبيوتر", "friendly computer"):
                with self.subTest(language=language, old=old):
                    self.assertNotIn(old, text)
        # "computer" appears once, in the ban on using the word
        self.assertEqual(flat(prompt.STATIC_PROMPT).count("computer"), 1)

    def test_no_vendor_or_model_name_anywhere_in_the_prompt(self):
        for language in ("en", "ar"):
            text = instructions(language).lower()
            for word in VENDOR_WORDS:
                with self.subTest(language=language, word=word):
                    self.assertNotIn(word, text)

    def test_the_session_language_block_keeps_the_right_ai_line(self):
        self.assertIn("give the English AI line, never the Arabic one", flat(instructions("en")))
        self.assertIn("Always reply in Arabic", flat(instructions("ar")))


class VerseNumberRuleKeptTests(SimpleTestCase):
    def test_the_prompt_keeps_the_never_say_numbers_rule(self):
        self.assertIn(VERSE_NUMBER_RULE, flat(instructions("en")))
        self.assertIn(VERSE_NUMBER_RULE, flat(instructions("ar")))
