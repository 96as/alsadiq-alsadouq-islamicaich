"""Regression tests for the bugs found by the live text-mode check (docs/hackathon/review/live-check.md).

No scripture anywhere: bank texts are obvious placeholders.
"""
from django.test import SimpleTestCase

from conversation.agent import turn_guard as tg


class FiqhReferServesNoCardTests(SimpleTestCase):
    """B3: a REFER (personal ruling) turn must not carry a verse card the child reads as the ruling, and
    the model is told not to look anything up."""

    def test_every_level_d_rule_serves_no_items(self):
        for r in tg.load_rules().level_d:
            self.assertTrue(r.no_items, r.id)

    def test_refer_turns_publish_no_items(self):
        for text, lang in [
            ("can I pray if I missed wudu?", "en"),
            ("is my prayer valid if I laughed?", "en"),
            ("هل يجوز أصلي وأنا لابس جزمة؟", "ar"),
            ("هل تبطل الصلاة إذا ضحكت؟", "ar"),
        ]:
            hit = tg.check(text)
            self.assertEqual(hit and hit.kind, tg.REFER, text)
            self.assertIn("Do not call search_bank", hit.note, text)


class AttributionPhraseTests(SimpleTestCase):
    def test_the_guard_catches_the_arabic_screen_phrase(self):
        from conversation.agent import scripture_guard as sg
        for said in ("في الحديث الذي على الشاشة معنى بسيط", "الحديث اللي على بطاقتك يعني الصدق حلو"):
            self.assertIsNotNone(sg.find_attribution(said, frozenset({"quran"})), said)
            self.assertIsNone(sg.find_attribution(said, frozenset({"hadith"})), said)

    def test_guard_catches_the_hadith_on_your_screen_phrase_without_a_licensed_hadith(self):
        from conversation.agent import scripture_guard as sg
        said = "In simple words, the hadith on your screen means honesty is good."
        self.assertIsNotNone(sg.find_attribution(said, frozenset({"quran"})))
        self.assertIsNone(sg.find_attribution(said, frozenset({"hadith"})))


VENDORS = ("openai", "google", "xai", "x.ai", "anthropic", "claude", "gemini", "grok", "chatgpt", "gpt", "microsoft",
           "meta ai", "mistral")


class WhoMadeYouTests(SimpleTestCase):
    """B5: 'who made you' gets the fixed no-vendor answer, in the persona and as a turn injection."""

    def test_persona_carries_the_fixed_line_in_both_languages_and_no_vendor_name(self):
        from conversation.agent.agent_class import AlSadiqAgent
        for lang in ("ar", "en"):
            text = AlSadiqAgent(db_session_id=1, child_id=1, language=lang).instructions
            self.assertIn("أنا صديق ذكاء اصطناعي، صنعني فريق الصديق الصدوق.", text)
            self.assertIn("I'm an AI friend made by the Al-Sadiq Al-Sadouq team.", text)
            self.assertIn("أنا الصديق،", text)  # the existing disclosure line stays
            self.assertNotIn("كمبيوتر", text)
            low = text.lower()
            for name in VENDORS:
                self.assertNotIn(name, low, f"{name} in the {lang} persona")


    def test_the_english_language_block_asks_for_the_english_ai_line_not_the_arabic_one(self):
        # hk/12: the maker lines live in the static prompt (both languages, tested above); the English
        # language block only picks the English one.
        from conversation.agent.agent_class import AlSadiqAgent
        text = AlSadiqAgent(db_session_id=1, child_id=1, language="en").instructions
        block = text[text.index("LANGUAGE: This session is in English"):]
        self.assertIn("give the English AI line, never the Arabic one", block)
        self.assertNotIn("أنا صديق ذكاء اصطناعي، صنعني فريق الصديق الصدوق.", block)


class EnglishSessionLanguageTests(SimpleTestCase):
    """B6: an English session discloses in English and greets in Latin letters."""

    def prompt(self, lang):
        from conversation.agent.agent_class import AlSadiqAgent
        return AlSadiqAgent(db_session_id=1, child_id=1, language=lang).instructions

    def test_english_session_gets_a_language_block_with_the_english_disclosure(self):
        text = self.prompt("en")
        block = text[text.index("LANGUAGE: This session is in English"):]
        self.assertIn("I'm Al-Sadiq, an AI friend, not a person.", text)  # the English line is in the prompt...
        self.assertIn("give the English AI line, never the Arabic one", block)  # ...and the block picks it
        self.assertIn("Always reply in English, in Latin letters", block)
        self.assertIn("write the salam as 'Assalamu alaikum'", block)
        self.assertNotIn("This session is in Arabic", text)

    def test_arabic_session_keeps_its_arabic_language_block(self):
        text = self.prompt("ar")
        self.assertIn("LANGUAGE: This session is in Arabic", text)
        self.assertIn("Always reply in Arabic", text)
        self.assertNotIn("This session is in English", text)

    def test_english_greeting_has_no_arabic_script_and_arabic_greeting_is_unchanged(self):
        import re
        from conversation.agent import entrypoint
        arabic = re.compile("[؀-ۿ]")
        en = entrypoint._GREETING_INSTRUCTIONS["en"] + entrypoint._FIRST_MEETING_AI_LINE["en"]
        self.assertIn("Assalamu alaikum", en)
        self.assertFalse(arabic.search(en))
        self.assertIn("السلام عليكم", entrypoint._GREETING_INSTRUCTIONS["ar"])
