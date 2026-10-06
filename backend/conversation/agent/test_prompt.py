"""Budget and must-have lines of the system prompt (prompt.py) and guidance files."""
import unittest
from pathlib import Path

from conversation.agent.prompt import (
    MAKER_LINE_AR, MAKER_LINE_EN, STATIC_PROMPT, STATIC_WORD_LIMIT, build_instructions,
)

GUIDANCE = Path(__file__).resolve().parent / "guidance"
GUIDANCE_NAMES = ("verse", "hadith", "disagreement", "fiqh", "creed", "afterlife", "story", "no_source", "comfort")


class PromptBudgetTests(unittest.TestCase):
    def test_static_prompt_within_budget(self):
        self.assertLessEqual(len(STATIC_PROMPT.split()), STATIC_WORD_LIMIT)

    def test_guidance_files_exist_and_are_short(self):
        for name in GUIDANCE_NAMES:
            words = len((GUIDANCE / f"{name}.md").read_text(encoding="utf-8").split())
            self.assertLessEqual(words, 80, name)

    def test_must_have_lines(self):
        for line in ("ذكاء اصطناعي ولست إنسانًا", MAKER_LINE_EN, MAKER_LINE_AR, "search_bank",
                     "{{card:ID}}", "flag_safety_concern", "at_home", "Never ask for details",
                     "never promise to"):
            self.assertIn(line, STATIC_PROMPT, line)

    def test_do_not_flag_fear_is_scoped_and_fear_of_someone_stays_flaggable(self):
        # The do-not-flag list names ordinary fear only (dark, tests, animals), so "I'm scared to go
        # home" or fear of an adult is not swallowed by it; fear of someone at home is 'sensitive'.
        do_not_flag = STATIC_PROMPT[STATIC_PROMPT.index("Do NOT flag normal childhood feelings"):]
        self.assertIn("ordinary sadness, fear (dark, tests, animals), worry", do_not_flag)
        self.assertNotIn("sadness, fear, worry", STATIC_PROMPT)
        self.assertIn("fear of someone at home", STATIC_PROMPT[:STATIC_PROMPT.index("Do NOT flag")])

    def test_dynamic_tail(self):
        text = build_instructions(language="ar", age_band="6-9", session_memory="cat Luna",
                                  active_quests_text="- quest")
        self.assertTrue(text.startswith(STATIC_PROMPT))
        for part in ("cat Luna", "- quest", "6-9", "Always reply in Arabic"):
            self.assertIn(part, text)
        self.assertIn("Always reply in English", build_instructions(language="en"))


class ValueNamesTailTests(unittest.TestCase):
    def test_value_names_go_in_the_dynamic_tail_only(self):
        text = build_instructions(language="en", value_names=["honesty", "kindness"])
        self.assertIn("VALUE NAMES for search_bank: honesty, kindness.", text)
        self.assertNotIn("VALUE NAMES", STATIC_PROMPT)
        self.assertNotIn("VALUE NAMES", build_instructions(language="en"))
