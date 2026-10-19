"""Child-echo filter: detection and removal must tokenise text the same way.

A parent never sees the child's own words. These cases split or break an echo so that the
detector and the remover disagree (or the text only looks different, not different to a human).
"""
from django.test import SimpleTestCase

from reporting.services import (
    _echo_keys,
    _parent_view,
    echoes_child_text,
    filter_child_echo_topics,
    strip_child_echo,
)

CHILD = ["I was very sad because my dog died last week"]
CHILD_AR = ["كنت حزينا جدا لأن كلبي مات الاسبوع الماضي"]


class InvisibleCharacterTests(SimpleTestCase):
    def test_format_characters_inside_words_do_not_hide_an_echo(self):
        keys = _echo_keys(CHILD)
        for ch in ("​", "‌", "‍", "﻿", "‎", "‏", "‮", "⁦", "­", "⁠"):
            with self.subTest(char=hex(ord(ch))):
                text = f"He said I was ve{ch}ry sa{ch}d because my d{ch}og died last week."
                self.assertTrue(echoes_child_text(text, keys))

    def test_format_characters_also_apply_to_the_child_side(self):
        keys = _echo_keys(["I was ve​ry sad because my dog died last week"])
        self.assertTrue(echoes_child_text("I was very sad because my dog died last week", keys))

    def test_strip_removes_an_echo_hidden_by_zero_width_characters(self):
        text = "He was fine. I was ve​ry sad because my dog died last week. Allah is kind."
        out = strip_child_echo(text, CHILD)
        self.assertFalse(echoes_child_text(out, _echo_keys(CHILD)))
        self.assertIn("Allah is kind", out)


class SentenceSplitTests(SimpleTestCase):
    def test_echo_spanning_two_sentences_does_not_survive(self):
        """Detected on the whole text, but each half alone is below the 6-word run."""
        text = "He felt low. I was very sad because. My dog died last week. Allah is kind."
        out = strip_child_echo(text, CHILD)
        self.assertFalse(echoes_child_text(out, _echo_keys(CHILD)), out)
        self.assertIn("Allah is kind", out)
        self.assertIn("He felt low", out)

    def test_echo_split_by_every_kind_of_break(self):
        keys = _echo_keys(CHILD)
        for sep in (". ", "؟ ", "، ", "؛ ", "\n", "\r\n", "... ", "… ", "\n- ", "\n• ", " • ", "。", "؟", "،", "!"):
            with self.subTest(sep=repr(sep)):
                text = f"Ok{sep}I was very sad because{sep}my dog died last week{sep}Fine thanks"
                out = strip_child_echo(text, CHILD)
                self.assertFalse(echoes_child_text(out, keys), out)
                self.assertIn("Fine thanks", out)

    def test_arabic_echo_split_by_arabic_punctuation(self):
        keys = _echo_keys(CHILD_AR)
        for sep in ("؟ ", "، ", "؛ ", "\n", "…", "،"):
            with self.subTest(sep=repr(sep)):
                text = f"ذكر الطفل شيئا{sep}كنت حزينا جدا لأن{sep}كلبي مات الاسبوع الماضي{sep}وهذا مفهوم"
                out = strip_child_echo(text, CHILD_AR)
                self.assertFalse(echoes_child_text(out, keys), out)
                self.assertIn("وهذا مفهوم", out)

    def test_unrelated_sentences_are_kept(self):
        text = "Talk about kindness. Ask about school."
        self.assertEqual(strip_child_echo(text, CHILD), text)

    def test_short_child_message_echo_is_removed_per_sentence(self):
        out = strip_child_echo("Fine. Yes I did it. Great.", ["yes I did it"])
        self.assertNotIn("did it", out)
        self.assertIn("Great", out)


class ListItemTests(SimpleTestCase):
    def test_topics_use_the_same_normalisation(self):
        topics = ["school", "I was ve​ry sad because my dog died last week", "kindness"]
        self.assertEqual(filter_child_echo_topics(topics, CHILD), ["school", "kindness"])

    def test_non_string_topics_are_dropped_not_passed_through(self):
        topics = ["school", {"t": "I was very sad because my dog died last week"}, ["x"], None, 5]
        self.assertEqual(filter_child_echo_topics(topics, CHILD), ["school"])

    def test_parent_view_applies_the_same_checks_to_every_field(self):
        echo = "I was ve​ry sad because my dog died last week"
        raw = {
            "emotional_progression": f"Calm. {echo}، then fine",
            "themes_discussed": ["pets", echo],
            "key_moments": ["a fine moment", echo, "I was very sad because… my dog died last week"],
        }
        view = _parent_view(raw, CHILD)
        keys = _echo_keys(CHILD)
        self.assertEqual(view["themes_discussed"], ["pets"])
        self.assertEqual(view["key_moments"], ["a fine moment"])
        self.assertFalse(echoes_child_text(view["emotional_progression"], keys))
        self.assertIn("then fine", view["emotional_progression"])


class DecimalAndPersianTests(SimpleTestCase):
    def test_decimals_and_numbered_text_are_not_split(self):
        text = "My dog weighs 3.5 kg and 10.25 lb. Version 2.0 is out. I was very sad because my dog died last week."
        out = strip_child_echo(text, CHILD)
        self.assertIn("3.5 kg", out)
        self.assertIn("10.25 lb", out)
        self.assertIn("Version 2.0 is out", out)
        self.assertFalse(echoes_child_text(out, _echo_keys(CHILD)))

    def test_period_before_a_letter_or_end_still_splits(self):
        out = strip_child_echo("Fine.I was very sad because my dog died last week.Kind", CHILD)
        self.assertEqual(out, "Fine. Kind")

    def test_echo_split_after_a_decimal_is_still_caught(self):
        keys = _echo_keys(["I weigh 3.5 kilos and I was very sad today"])
        out = strip_child_echo("Ok. I weigh 3.5 kilos and I was very sad today. Fine.", ["I weigh 3.5 kilos and I was very sad today"])
        self.assertFalse(echoes_child_text(out, keys))
        self.assertIn("Fine", out)

    def test_persian_yeh_and_kaf_fold_to_the_arabic_letters(self):
        persian = "\u06a9نت حزینا جدا لأن \u06a9لبی مات الاسبوع الماضی"
        self.assertTrue(echoes_child_text(persian, _echo_keys(CHILD_AR)))
        self.assertTrue(echoes_child_text(CHILD_AR[0], _echo_keys([persian])))
        out = strip_child_echo(f"ذكر الطفل شيئا. {persian}. وهذا مفهوم", CHILD_AR)
        self.assertNotIn("حزینا", out)
        self.assertIn("وهذا مفهوم", out)
