"""Tests for conversation.agent.tts_text (pure Python, no Django, no livekit).

Run from the backend folder with either:
    python -m unittest conversation.agent.test_tts_text -v
    python -m pytest conversation/agent/test_tts_text.py

No Quran text appears here. Placeholder words stand in for verses.
"""
import re
import unittest

from conversation.agent import tts_text
from conversation.agent.tts_text import (
    QURAN_PHRASE,
    TTSTextStream,
    clean_tts_stream,
    prepare_for_tts,
    tts_text_transform,
)

# Quran brackets, written as escapes so the source stays unambiguous.
OPEN = "\ufd3f"
CLOSE = "\ufd3e"
PBUH = "\ufdfa"
JALLA = "\ufdfb"
ALLAH_LIG = "\ufdf2"
BASMALA_LIG = "\ufdfd"

PLACEHOLDER = "PLACEHOLDER_VERSE"
PLACEHOLDER_AR = "نص_تجريبي"
AR_PHRASE = QURAN_PHRASE["ar"]
EN_PHRASE = QURAN_PHRASE["en"]


def norm(s: str) -> str:
    return " ".join(s.split())


def stream_chunks(chunks, lang):
    s = TTSTextStream(lang)
    out = [s.feed(c) for c in chunks]
    out.append(s.flush())
    return "".join(out)


def split_every(text: str, size: int):
    return [text[i:i + size] for i in range(0, len(text), size)]


async def agen(chunks):
    for c in chunks:
        yield c


async def collect(aiter):
    return [x async for x in aiter]


class MarkdownTests(unittest.TestCase):
    def test_bold_italic_asterisks(self):
        self.assertEqual(prepare_for_tts("This is **very** *nice*.", "en"),
                         "This is very nice.")

    def test_bold_arabic(self):
        self.assertEqual(prepare_for_tts("هذا **مهم** جدا", "ar"), "هذا مهم جدا")

    def test_headings_removed_only_at_line_start(self):
        self.assertEqual(prepare_for_tts("## Title\nbody", "en"), "Title\nbody")
        self.assertEqual(prepare_for_tts("C# is fine", "en"), "C# is fine")

    def test_bullets_and_numbered_lists(self):
        text = "- one\n* two\n+ three\n1. four\n2) five\n\u2022 six"
        self.assertEqual(prepare_for_tts(text, "en"),
                         "one\ntwo\nthree\nfour\nfive\nsix")

    def test_dash_inside_sentence_is_kept(self):
        self.assertEqual(prepare_for_tts("fun - really fun", "en"),
                         "fun - really fun")

    def test_links_keep_text(self):
        self.assertEqual(
            prepare_for_tts("See [the guide](https://example.com/x) now", "en"),
            "See the guide now")

    def test_images_keep_alt(self):
        self.assertEqual(prepare_for_tts("![a cat](http://x.y/c.png) here", "en"),
                         "a cat here")

    def test_inline_code_and_fences(self):
        out = prepare_for_tts("use `code` and\n```py\nx\n```", "en")
        self.assertNotIn("`", out)
        self.assertEqual(norm(out), "use code and x")

    def test_strikethrough_and_rules(self):
        out = prepare_for_tts("~~old~~ new\n---\nend", "en")
        self.assertNotIn("~", out)
        self.assertNotIn("---", out)
        self.assertIn("new", out)

    def test_table_pipes(self):
        self.assertNotIn("|", prepare_for_tts("a | b | c", "en"))

    def test_snake_case_underscores_survive(self):
        self.assertEqual(prepare_for_tts("my_var_name", "en"), "my_var_name")
        self.assertEqual(prepare_for_tts("_emphasis_ here", "en"), "emphasis here")

    def test_blockquote(self):
        self.assertEqual(prepare_for_tts("> quoted words", "en"), "quoted words")


class EmojiUrlTests(unittest.TestCase):
    def test_emoji_removed(self):
        out = prepare_for_tts("Great job \U0001f600\U0001f44d\u2728 friend", "en")
        self.assertEqual(norm(out), "Great job friend")

    def test_emoji_zwj_sequence_and_flags(self):
        family = "\U0001f468\u200d\U0001f469\u200d\U0001f467"
        flag = "\U0001f1f8\U0001f1e6"
        out = prepare_for_tts(f"hi {family} and {flag} bye", "en")
        self.assertEqual(norm(out), "hi and bye")

    def test_emoji_glued_to_word_does_not_merge_words(self):
        self.assertEqual(norm(prepare_for_tts("good\U0001f600next", "en")),
                         "good next")

    def test_keycap_keeps_digit(self):
        out = prepare_for_tts("1\ufe0f\u20e3 first", "en")
        self.assertEqual(norm(out), "one first")

    def test_arabic_with_emoji(self):
        self.assertEqual(norm(prepare_for_tts("أحسنت \U0001f31f يا بطل", "ar")),
                         "أحسنت يا بطل")

    def test_urls_removed(self):
        out = prepare_for_tts("Go to https://example.com/a?b=1 or www.test.org today", "en")
        self.assertEqual(norm(out), "Go to or today")

    def test_url_trailing_punctuation_kept(self):
        self.assertEqual(norm(prepare_for_tts("see https://example.com/x.", "en")),
                         "see .")

    def test_email_removed(self):
        self.assertEqual(norm(prepare_for_tts("mail me at a.b@example.com ok", "en")),
                         "mail me at ok")

    def test_tatweel_removed(self):
        self.assertEqual(prepare_for_tts("جمي\u0640\u0640ل", "ar"), "جميل")


class HonorificTests(unittest.TestCase):
    def test_pbuh_ligature_arabic(self):
        self.assertEqual(norm(prepare_for_tts(f"محمد {PBUH} رسول", "ar")),
                         "محمد صلى الله عليه وسلم رسول")

    def test_pbuh_ligature_english(self):
        self.assertEqual(norm(prepare_for_tts(f"Muhammad {PBUH} taught", "en")),
                         "Muhammad peace be upon him taught")

    def test_glued_ligature_is_spaced(self):
        self.assertEqual(norm(prepare_for_tts(f"محمد{PBUH}.", "ar")),
                         "محمد صلى الله عليه وسلم.")

    def test_other_ligatures(self):
        self.assertEqual(norm(prepare_for_tts(f"{JALLA} {ALLAH_LIG}", "ar")),
                         "جل جلاله الله")
        self.assertEqual(norm(prepare_for_tts(f"{JALLA} {ALLAH_LIG}", "en")),
                         "glorified and exalted is He Allah")

    def test_basmala_ligature_dropped_not_expanded(self):
        self.assertEqual(norm(prepare_for_tts(f"{BASMALA_LIG} hello", "en")),
                         "hello")

    def test_english_abbreviations(self):
        self.assertEqual(norm(prepare_for_tts("The Prophet (PBUH) said", "en")),
                         "The Prophet peace be upon him said")
        self.assertEqual(norm(prepare_for_tts("Prophet PBUH smiled", "en")),
                         "Prophet peace be upon him smiled")
        self.assertEqual(norm(prepare_for_tts("Allah (SWT) knows", "en")),
                         "Allah glorified and exalted is He knows")

    def test_plain_saw_word_untouched(self):
        self.assertEqual(prepare_for_tts("I saw it", "en"), "I saw it")
        self.assertEqual(prepare_for_tts("I SAW it", "en"), "I SAW it")

    def test_tashkeel_preserved_exactly(self):
        text = "الْوَلَدُ يَقْرَأُ الْكِتَابَ، وَالْبِنْتُ تَكْتُبُ"
        self.assertEqual(prepare_for_tts(text, "ar"), text)

    def test_tashkeel_preserved_next_to_other_rules(self):
        out = prepare_for_tts("**مُحَمَّدٌ** \U0001f600 \u0663", "ar")
        self.assertEqual(norm(out), "مُحَمَّدٌ ثلاثة")


class EnglishNumberTests(unittest.TestCase):
    def check(self, text, expected):
        self.assertEqual(prepare_for_tts(text, "en"), expected)

    def test_small(self):
        self.check("0", "zero")
        self.check("7", "seven")
        self.check("11", "eleven")
        self.check("19", "nineteen")
        self.check("21", "twenty-one")
        self.check("40", "forty")
        self.check("99", "ninety-nine")

    def test_hundreds_and_thousands(self):
        self.check("100", "one hundred")
        self.check("101", "one hundred one")
        self.check("999", "nine hundred ninety-nine")
        self.check("1000", "one thousand")
        self.check("12345", "twelve thousand three hundred forty-five")
        self.check("1,000,000", "one million")
        self.check("2,500", "two thousand five hundred")

    def test_years(self):
        self.check("1999", "nineteen ninety-nine")
        self.check("2026", "twenty twenty-six")
        self.check("2005", "two thousand five")
        self.check("2000", "two thousand")
        self.check("1900", "nineteen hundred")
        self.check("1805", "eighteen oh five")
        self.check("1447", "fourteen forty-seven")

    def test_year_in_sentence(self):
        self.check("It was in 2026.", "It was in twenty twenty-six.")

    def test_grouped_four_digits_is_cardinal(self):
        self.check("1,999", "one thousand nine hundred ninety-nine")

    def test_decimals_percent_ordinals(self):
        self.check("3.5", "three point five")
        self.check("0.25", "zero point two five")
        self.check("50%", "fifty percent")
        self.check("1st", "first")
        self.check("2nd", "second")
        self.check("3rd", "third")
        self.check("12th", "twelfth")
        self.check("21st", "twenty-first")
        self.check("30th", "thirtieth")

    def test_leading_zero_and_long_numbers_read_digit_by_digit(self):
        self.check("007", "zero zero seven")
        self.check("0123456789012", "zero one two three four five six seven eight nine zero one two")

    def test_digits_next_to_letters(self):
        self.check("H2O", "H two O")
        self.check("3D", "three D")

    def test_list_commas_not_treated_as_thousands(self):
        self.check("1,2,3", "one,two,three")

    def test_time(self):
        self.check("5:30", "five thirty")

    def test_arabic_indic_digits_in_english_text(self):
        self.check("I have \u0663 apples", "I have three apples")

    # Chapter:verse references (live finding 2026-10-05): "9:119" was spoken "nine one hundred nineteen".
    def test_verse_after_a_named_surah_says_only_the_verse(self):
        self.check("Surah At-Tawbah 9:119 teaches us", "Surah At-Tawbah verse one hundred nineteen teaches us")

    def test_verse_word_before_the_reference_is_not_doubled(self):
        self.check("Surah At-Tawbah, verse 9:119.", "Surah At-Tawbah, verse one hundred nineteen.")

    def test_reference_split_across_stream_chunks_reads_the_same(self):
        text = "Surah At-Tawbah, verse 9:119."
        for size in (1, 3, 7):
            self.assertEqual(stream_chunks(split_every(text, size), "en"),
                             "Surah At-Tawbah, verse one hundred nineteen.")

    def test_bare_reference_says_both_numbers_apart(self):
        self.check("See 2:255 today", "See two, two hundred fifty-five today")
        self.check("verse 9:119", "verse nine, one hundred nineteen")

    def test_clock_times_are_still_times(self):
        self.check("Come at 9:30", "Come at nine thirty")
        self.check("At 10:30 we read", "At ten thirty we read")


class ArabicNumberTests(unittest.TestCase):
    def check(self, text, expected):
        self.assertEqual(prepare_for_tts(text, "ar"), expected)

    def test_verse_reference_after_a_named_surah(self):
        # "surah Al-Ma'ida 5:119" is spoken "... the verse one hundred nineteen", not "five hundred nineteen".
        self.check("سورة المائدة 5:119.",
                   "سورة المائدة "
                   "الآية مائة وتسعة عشر.")

    def test_basic(self):
        self.check("0", "صفر")
        self.check("1", "واحد")
        self.check("2", "اثنان")
        self.check("10", "عشرة")
        self.check("11", "أحد عشر")
        self.check("12", "اثنا عشر")
        self.check("19", "تسعة عشر")
        self.check("20", "عشرون")
        self.check("21", "واحد وعشرون")
        self.check("99", "تسعة وتسعون")

    def test_hundreds(self):
        self.check("100", "مائة")
        self.check("101", "مائة وواحد")
        self.check("125", "مائة وخمسة وعشرون")
        self.check("200", "مائتان")
        self.check("300", "ثلاثمائة")
        self.check("999", "تسعمائة وتسعة وتسعون")

    def test_thousands_and_up(self):
        self.check("1000", "ألف")
        self.check("2000", "ألفان")
        self.check("3000", "ثلاثة آلاف")
        self.check("10000", "عشرة آلاف")
        self.check("11000", "أحد عشر ألفًا")
        self.check("100000", "مائة ألف")
        self.check("200000", "مائتا ألف")
        self.check("1,000,000", "مليون")
        self.check("2000000", "مليونان")
        self.check("1500", "ألف وخمسمائة")

    def test_years(self):
        self.check("2026", "ألفان وستة وعشرون")
        self.check("1447", "ألف وأربعمائة وسبعة وأربعون")

    def test_arabic_indic_digits(self):
        self.check("\u0662\u0660\u0662\u0666", "ألفان وستة وعشرون")
        self.check("\u0661\u0662", "اثنا عشر")

    def test_extended_arabic_indic_digits(self):
        self.check("\u06f1\u06f2", "اثنا عشر")

    def test_arabic_separators(self):
        self.check("\u0661\u066c\u0660\u0660\u0660", "ألف")
        self.check("\u0663\u066b\u0665", "ثلاثة فاصلة خمسة")

    def test_decimal_and_percent(self):
        self.check("3.5", "ثلاثة فاصلة خمسة")
        self.check("50%", "خمسون بالمئة")

    def test_number_in_sentence(self):
        self.check("عمري 8 سنوات", "عمري ثمانية سنوات")

    def test_leading_zero_digit_by_digit(self):
        self.check("007", "صفر صفر سبعة")

    def test_number_glued_to_letter(self):
        self.assertEqual(norm(prepare_for_tts("\u0662\u0660\u0662\u0666م", "ar")),
                         "ألفان وستة وعشرون م")


class LangTests(unittest.TestCase):
    def test_region_suffix(self):
        self.assertEqual(prepare_for_tts("5", "ar-SA"), "خمسة")
        self.assertEqual(prepare_for_tts("5", "en_US"), "five")

    def test_auto_detects_by_script(self):
        self.assertEqual(prepare_for_tts("I have 5", "auto"), "I have five")
        self.assertEqual(prepare_for_tts("عندي 5", "auto"), "عندي خمسة")

    def test_auto_digits_only_defaults_to_arabic(self):
        self.assertEqual(prepare_for_tts("5", "auto"), "خمسة")

    def test_callable_lang(self):
        holder = {"lang": "en"}
        s = TTSTextStream(lambda: holder["lang"])
        self.assertEqual(s.feed("5 "), "five ")
        holder["lang"] = "ar"
        self.assertEqual(s.feed("5 "), "خمسة ")

    def test_auto_follows_the_language_of_each_piece(self):
        chunks = ["Hello 2 ", "friends. ", "مرحبا 3 ", "أصدقاء "]
        self.assertEqual(norm(stream_chunks(chunks, "auto")),
                         "Hello two friends. مرحبا ثلاثة أصدقاء")

    def test_none_lang_is_auto(self):
        self.assertEqual(prepare_for_tts("hello 2", None), "hello two")


class EmptyInputTests(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(prepare_for_tts("", "ar"), "")
        self.assertEqual(prepare_for_tts("", "en"), "")
        self.assertEqual(prepare_for_tts(None, "en"), "")
        self.assertEqual(prepare_for_tts("   \n ", "en"), "")

    def test_stream_empty(self):
        s = TTSTextStream("en")
        self.assertEqual(s.feed(""), "")
        self.assertEqual(s.flush(), "")

    def test_only_stripped_content(self):
        self.assertEqual(prepare_for_tts("\U0001f600", "en"), "")
        self.assertEqual(prepare_for_tts("**", "en"), "")


class QuranGuardTests(unittest.TestCase):
    def test_bracketed_text_replaced_english(self):
        out = prepare_for_tts(f"Allah says {OPEN}{PLACEHOLDER}{CLOSE} and more", "en")
        self.assertEqual(norm(out), f"Allah says {EN_PHRASE} and more")
        self.assertNotIn(PLACEHOLDER, out)

    def test_bracketed_text_replaced_arabic(self):
        out = prepare_for_tts(f"قال تعالى {OPEN}{PLACEHOLDER_AR}{CLOSE} وهكذا", "ar")
        self.assertEqual(norm(out), f"قال تعالى {AR_PHRASE} وهكذا")
        self.assertNotIn(PLACEHOLDER_AR, out)

    def test_other_bracket_order_also_guarded(self):
        out = prepare_for_tts(f"x {CLOSE}{PLACEHOLDER}{OPEN} y", "en")
        self.assertNotIn(PLACEHOLDER, out)
        self.assertIn(EN_PHRASE, out)

    def test_brackets_glued_to_words(self):
        out = prepare_for_tts(f"says{OPEN}{PLACEHOLDER}{CLOSE}end", "en")
        self.assertEqual(norm(out), f"says {EN_PHRASE} end")

    def test_text_with_digits_inside_brackets_not_spoken(self):
        out = prepare_for_tts(f"{OPEN}{PLACEHOLDER} 12 34{CLOSE}", "en")
        self.assertEqual(out, EN_PHRASE)

    def test_two_verses_back_to_back_one_phrase(self):
        out = prepare_for_tts(f"{OPEN}a{CLOSE} {OPEN}b{CLOSE}", "en")
        self.assertEqual(out, EN_PHRASE)

    def test_two_verses_separated_by_words_two_phrases(self):
        out = prepare_for_tts(f"{OPEN}a{CLOSE} then {OPEN}b{CLOSE}", "en")
        self.assertEqual(norm(out), f"{EN_PHRASE} then {EN_PHRASE}")

    def test_unclosed_bracket_drops_rest(self):
        out = prepare_for_tts(f"before {OPEN}{PLACEHOLDER} never closed", "en")
        self.assertEqual(norm(out), f"before {EN_PHRASE}")

    def test_stray_closer_does_not_leak_following_text_as_verse_start(self):
        # Either bracket opens the guard, so this fails closed (text dropped).
        out = prepare_for_tts(f"abc {CLOSE} {PLACEHOLDER}", "en")
        self.assertNotIn(PLACEHOLDER, out)

    def test_brackets_never_in_output(self):
        out = prepare_for_tts(f"{OPEN}x{CLOSE}", "ar")
        self.assertNotIn(OPEN, out)
        self.assertNotIn(CLOSE, out)

    def test_logs_when_triggered(self):
        with self.assertLogs(tts_text.logger, level="INFO") as cm:
            prepare_for_tts(f"a {OPEN}{PLACEHOLDER}{CLOSE} b", "en")
        text = "\n".join(cm.output)
        self.assertIn("Quran", text)
        self.assertNotIn(PLACEHOLDER, text)

    def test_no_log_without_brackets(self):
        with self.assertNoLogs(tts_text.logger, level="DEBUG"):
            prepare_for_tts("plain text", "en")

    def test_auto_language_phrase(self):
        self.assertEqual(prepare_for_tts(f"Listen {OPEN}x{CLOSE}", "auto").split()[-4:],
                         EN_PHRASE.split())
        self.assertTrue(prepare_for_tts(f"استمع {OPEN}x{CLOSE}", "auto").endswith(AR_PHRASE))

    def test_unbalanced_for_very_long_unclosed_resumes(self):
        long_tail = "word " * 200  # more than the 400 char cap
        s = TTSTextStream("en")
        with self.assertLogs(tts_text.logger, level="WARNING"):
            out = s.feed(f"{OPEN}{long_tail}") + s.feed("tail end ") + s.flush()
        self.assertIn(EN_PHRASE, out)
        self.assertIn("tail end", out)


class StreamChunkBoundaryTests(unittest.TestCase):
    def test_opener_split_from_text_in_separate_chunks(self):
        out = stream_chunks(["Allah says ", OPEN, PLACEHOLDER, " more ", CLOSE, " ok"], "en")
        self.assertNotIn(PLACEHOLDER, out)
        self.assertEqual(norm(out), f"Allah says {EN_PHRASE} ok")

    def test_verse_open_and_close_in_distant_chunks(self):
        chunks = ["intro ", OPEN + "PLACE", "HOLD", "ER_VERSE a b c d", " e f", CLOSE + " outro"]
        out = stream_chunks(chunks, "en")
        self.assertNotIn("PLACE", out)
        self.assertNotIn("HOLD", out)
        self.assertEqual(norm(out), f"intro {EN_PHRASE} outro")

    def test_phrase_is_emitted_as_soon_as_bracket_opens(self):
        s = TTSTextStream("en")
        first = s.feed(f"hello {OPEN}")
        self.assertIn(EN_PHRASE, first)
        self.assertEqual(s.feed(PLACEHOLDER), "")  # nothing leaks while open
        self.assertEqual(s.feed(f"{CLOSE} done "), "done ")

    def test_verse_text_is_never_buffered_or_released_later(self):
        s = TTSTextStream("en")
        s.feed(f"a {OPEN}{PLACEHOLDER}")
        self.assertEqual(s._buf, "")
        self.assertNotIn(PLACEHOLDER, s.flush())

    def test_closer_then_text_in_same_chunk(self):
        out = stream_chunks([f"{OPEN}x", f"{CLOSE}after words here"], "en")
        self.assertEqual(norm(out), f"{EN_PHRASE} after words here")

    def test_number_split_across_chunks(self):
        self.assertEqual(norm(stream_chunks(["I have 1", "1 apples"], "en")),
                         "I have eleven apples")
        self.assertEqual(norm(stream_chunks(["عندي ", "\u0661", "\u0662", " كتابا"], "ar")),
                         "عندي اثنا عشر كتابا")

    def test_year_split_across_chunks(self):
        self.assertEqual(norm(stream_chunks(["in 20", "26 ok"], "en")),
                         "in twenty twenty-six ok")

    def test_decimal_split_across_chunks(self):
        self.assertEqual(norm(stream_chunks(["3", ".", "5 ", "cm"], "en")),
                         "three point five cm")

    def test_thousands_split_across_chunks(self):
        self.assertEqual(norm(stream_chunks(["1,", "000 ", "yes"], "en")),
                         "one thousand yes")

    def test_number_at_end_of_stream_is_flushed(self):
        self.assertEqual(norm(stream_chunks(["total ", "4", "2"], "en")),
                         "total forty-two")

    def test_symbol_across_chunks(self):
        self.assertEqual(
            norm(stream_chunks(["محمد ", PBUH, " قال"], "ar")),
            "محمد صلى الله عليه وسلم قال")
        self.assertEqual(
            norm(stream_chunks(["Muhammad", PBUH, "."], "en")),
            "Muhammad peace be upon him.")

    def test_word_split_before_symbol(self):
        self.assertEqual(
            norm(stream_chunks(["Muham", "mad ", PBUH], "en")),
            "Muhammad peace be upon him")

    def test_abbreviation_split_across_chunks(self):
        self.assertEqual(norm(stream_chunks(["Prophet (PB", "UH) smiled"], "en")),
                         "Prophet peace be upon him smiled")

    def test_markdown_bold_split(self):
        self.assertEqual(norm(stream_chunks(["a *", "*bold", "** b"], "en")),
                         "a bold b")

    def test_link_split_across_chunks(self):
        chunks = ["see [the gu", "ide](https://exa", "mple.com/x) now"]
        self.assertEqual(norm(stream_chunks(chunks, "en")), "see the guide now")

    def test_image_split_across_chunks(self):
        chunks = ["x !", "[alt text](http://a", ".b/c.png) y"]
        self.assertEqual(norm(stream_chunks(chunks, "en")), "x alt text y")

    def test_url_split_across_chunks(self):
        self.assertEqual(norm(stream_chunks(["go ht", "tps://exam", "ple.com/p now"], "en")),
                         "go now")

    def test_line_start_bullet_split_across_chunks(self):
        self.assertEqual(stream_chunks(["intro\n", "-", " item one\n", "- ", "item two"], "en"),
                         "intro\nitem one\nitem two")

    def test_heading_marker_split_across_chunks(self):
        self.assertEqual(stream_chunks(["##", " Title\nbody"], "en"), "Title\nbody")

    def test_dash_mid_line_after_chunk_split_is_kept(self):
        out = stream_chunks(["well ", "- fine ", "- ok"], "en")
        self.assertEqual(norm(out), "well - fine - ok")

    def test_emoji_zwj_split_across_chunks(self):
        chunks = ["hi \U0001f468", "\u200d", "\U0001f469 ", "bye"]
        self.assertEqual(norm(stream_chunks(chunks, "en")), "hi bye")

    def test_text_released_before_stream_ends(self):
        s = TTSTextStream("en")
        self.assertEqual(s.feed("Hello "), "Hello ")
        self.assertEqual(s.feed("wor"), "")
        self.assertEqual(s.feed("ld and "), "world and ")

    def test_long_unbroken_text_is_released(self):
        s = TTSTextStream("en")
        out = s.feed("x" * 600)
        self.assertEqual(len(out), 600)

    def test_stray_open_square_bracket_does_not_stall(self):
        s = TTSTextStream("en")
        out = s.feed("a [ " + "word " * 100) + s.flush()
        self.assertIn("word", out)

    def test_every_chunk_size_matches_one_shot(self):
        samples = [
            ("en", "## Heading\n- item **one** costs 25%\n- item two, in 2026.\n"
                   f"Muhammad {PBUH} taught [kindness](https://e.com/x) \U0001f600 "
                   f"{OPEN}{PLACEHOLDER} 1 2{CLOSE} then 1st, 3.5 and 1,000 at 5:30. "
                   "Visit https://example.com/a now (PBUH)."),
            ("ar", "# عنوان\n* بند **أول** بعمر \u0668 سنوات\n"
                   f"قال {PBUH} في 2026 {OPEN}{PLACEHOLDER_AR}{CLOSE} ثم 12 و\u0661\u0662\u066b\u0665 "
                   "[رابط](http://x.y/z) \U0001f31f ختام."),
            ("auto", "Hello 2 friends \U0001f600 and ![img](u.png) 3 more, end."),
            ("auto", "مرحبا 3 أصدقاء \U0001f600 [رابط](u.png) ثم \u0664 أيضا."),
        ]
        for lang, text in samples:
            expected = norm(prepare_for_tts(text, lang))
            self.assertNotIn(PLACEHOLDER, expected)
            for size in range(1, 14):
                with self.subTest(lang=lang, size=size):
                    got = norm(stream_chunks(split_every(text, size), lang))
                    self.assertEqual(got, expected)

    def test_chunk_sizes_never_leak_placeholder(self):
        text = f"say {OPEN}{PLACEHOLDER} {PLACEHOLDER}{CLOSE} done"
        for size in range(1, len(text) + 1):
            with self.subTest(size=size):
                s = TTSTextStream("en")
                outs = [s.feed(c) for c in split_every(text, size)] + [s.flush()]
                joined = "".join(outs)
                self.assertNotIn("PLACE", joined)
                self.assertNotIn("HOLDER", joined)
                self.assertNotIn("VERSE", joined)
                self.assertEqual(norm(joined), f"say {EN_PHRASE} done")


class AsyncAdapterTests(unittest.IsolatedAsyncioTestCase):
    async def test_clean_tts_stream(self):
        chunks = ["I am ", "1", "1 ", "**old**"]
        out = await collect(clean_tts_stream(agen(chunks), "en"))
        self.assertEqual(norm("".join(out)), "I am eleven old")

    async def test_yields_nothing_for_empty_stream(self):
        self.assertEqual(await collect(clean_tts_stream(agen([]), "en")), [])
        self.assertEqual(await collect(clean_tts_stream(agen(["", ""]), "ar")), [])

    async def test_transform_is_a_livekit_style_callable(self):
        transform = tts_text_transform("en")
        result = transform(agen(["a ", "b"]))
        self.assertTrue(hasattr(result, "__aiter__"))
        self.assertEqual("".join([x async for x in result]), "a b")

    async def test_transform_reusable_for_each_segment(self):
        transform = tts_text_transform("en")
        first = "".join(await collect(transform(agen(["one 1 "]))))
        second = "".join(await collect(transform(agen(["two 2 "]))))
        self.assertEqual(first, "one one ")
        self.assertEqual(second, "two two ")

    async def test_quran_across_async_chunks(self):
        transform = tts_text_transform("ar")
        out = "".join(await collect(transform(agen(
            ["قال ", OPEN, PLACEHOLDER_AR, " ", PLACEHOLDER_AR, CLOSE, " انتهى"]))))
        self.assertNotIn(PLACEHOLDER_AR, out)
        self.assertEqual(norm(out), f"قال {AR_PHRASE} انتهى")

    async def test_verse_spanning_two_segments_stays_suppressed(self):
        transform = tts_text_transform("en")
        seg1 = "".join(await collect(transform(agen([f"say {OPEN}{PLACEHOLDER} "]))))
        seg2 = "".join(await collect(transform(agen([f"{PLACEHOLDER}{CLOSE} done "]))))
        self.assertNotIn(PLACEHOLDER, seg1 + seg2)
        self.assertEqual(norm(seg1), f"say {EN_PHRASE}")
        self.assertEqual(norm(seg2), "done")

    async def test_state_not_shared_between_transform_instances(self):
        t1 = tts_text_transform("en")
        t2 = tts_text_transform("en")
        await collect(t1(agen([f"{OPEN}x "])))
        out = "".join(await collect(t2(agen(["plain words "]))))
        self.assertEqual(out, "plain words ")

    async def test_non_string_chunks_pass_through(self):
        marker = object()
        out = await collect(clean_tts_stream(agen(["hi ", marker, "there "]), "en"))
        self.assertIn(marker, out)
        self.assertEqual("".join(x for x in out if isinstance(x, str)), "hi there ")

    async def test_matches_livekit_apply_text_transforms_if_installed(self):
        try:
            from livekit.agents.voice.transcription.text_transforms import (
                _apply_text_transforms,
            )
        except Exception:
            self.skipTest("livekit-agents not installed")
        stream = _apply_text_transforms(agen(["I am 1", "1 \U0001f600"]),
                                        [tts_text_transform("en")])
        out = "".join([x async for x in stream])
        self.assertEqual(norm(out), "I am eleven")


class ConstantsTests(unittest.TestCase):
    def test_phrases_are_short_and_contain_no_brackets(self):
        for phrase in QURAN_PHRASE.values():
            self.assertLess(len(phrase), 40)
            self.assertNotIn(OPEN, phrase)
            self.assertNotIn(CLOSE, phrase)

    def test_ligature_codepoints_have_expected_names(self):
        import unicodedata
        self.assertIn("SALLALLAHOU", unicodedata.name(PBUH))
        self.assertIn("JALLAJALALOUHOU", unicodedata.name(JALLA))
        self.assertIn("ORNATE", unicodedata.name(OPEN))
        self.assertIn("ORNATE", unicodedata.name(CLOSE))


class ForeignScriptTests(unittest.TestCase):
    def test_cjk_kana_and_hangul_inside_an_arabic_word_are_removed(self):
        self.assertEqual(prepare_for_tts("أهلا يا صدي中ق", "ar"), "أهلا يا صديق")
        self.assertEqual(prepare_for_tts("مرحبا カタあ 한 بك", "ar"), "مرحبا بك")

    def test_arabic_english_digits_and_punctuation_are_untouched(self):
        for text in ["مرحبا يا صديقي، كيف حالك؟", "Hello there, friend! How are you?",
                     "It is a nice day: yes."]:
            self.assertEqual(prepare_for_tts(text, "auto"), text)
        self.assertEqual(prepare_for_tts("I have 3 cats", "en"), "I have three cats")

    def test_strip_function_edges(self):
        self.assertEqual(tts_text.strip_foreign_script(""), "")
        self.assertIsNone(tts_text.strip_foreign_script(None))
        self.assertEqual(tts_text.strip_foreign_script("a中b㐀c鿿d豈e가f"), "abcdef")

    def test_the_strip_before_the_guards_is_origins_exactly(self):
        # strip_foreign_script runs BEFORE the guards (in the speech cleaner, and in the chat's
        # transcription_node), so it is origin/hackathon's, unchanged: Kana, CJK ideographs and
        # extension A, compatibility ideographs and Hangul syllables removed, every other
        # character passed on as it was. So the speech cleaner's scripture filter, the attribution
        # guard and filter_scripture_stream read exactly origin's text (round-2 review B1 and B2:
        # the wider handling run here split a marked word and hid an attribution).
        removed = [chr(c) for c in (0x3041, 0x309B, 0x30FB, 0x30FC, 0x3400, 0x4DC0, 0x4E2D, 0x9FFF,
                                    0xF900, 0xFAFF, 0xAC00, 0xD7A3)]
        kept = ["д", "Ж", "а", "Р", "е", "ש", "ו", "ס", "ส", "क", "०", "α", "ο", "λ"] + [chr(c) for c in (
            0x1100, 0x3131, 0x314F, 0x3105, 0x3000, 0x3001, 0x3002, 0x3003, 0x300C, 0x3010, 0x2E80,
            0x2F00, 0xFE31, 0xFF01, 0xFF0C, 0xFF1A, 0xFF1B, 0xFF02, 0xFF07, 0xFF08, 0xFF1C, 0xFF5B,
            0xFF3B, 0xFF0A, 0xFF3F, 0xFF5E, 0xFF0F, 0xFF20, 0xFF40, 0xFF0E, 0xFF0D, 0xFF10, 0xFF21,
            0xFF53, 0xFF71, 0xFFA1, 0x3220, 0x3231, 0x20001, 0x2F800, 0xA960)]
        for ch in removed:
            with self.subTest(cp=hex(ord(ch))):
                self.assertEqual(tts_text.strip_foreign_script(f"a{ch}b"), "ab")
        for ch in kept:
            with self.subTest(cp=hex(ord(ch))):
                self.assertEqual(tts_text.strip_foreign_script(f"a{ch}b"), f"a{ch}b")
        # so the speech cleaner hands them to the guards as origin's did
        for text in ("Hello привет friend.", "Please tell a trusted аdult now.",
                     "The Prophet" + chr(0xFF01) + " of Allah said smile at the stars."):
            with self.subTest(text=text):
                self.assertEqual(prepare_for_tts(text, "en"), text)

    def test_every_off_script_block_goes_after_the_guards_and_nothing_else(self):
        # tidy_off_script runs AFTER the guards (TurnGuardMixin.guard_speech). Letters and digits
        # origin passed on (Bopomofo, Hangul Jamo, compat Jamo, half-width Kana and Hangul,
        # enclosed CJK numbers, extension B, compatibility supplement, Jamo extended A): one space
        # between two letters (a run: one space), so two words are never glued
        for ch in [chr(c) for c in (0x3105, 0x1100, 0x3131, 0xFF71, 0xFFA1, 0x3220, 0x20000,
                                    0x2F800, 0xA960)]:
            with self.subTest(cp=hex(ord(ch))):
                self.assertEqual(tts_text.tidy_off_script(f"a{ch}b"), "a b")
                self.assertEqual(tts_text.tidy_off_script(f"a{ch * 3}b"), "a b")   # a run: one space
        # punctuation and symbols (radicals, Kangxi radicals, CJK brackets, CJK compatibility forms)
        for ch in [chr(c) for c in (0x2E80, 0x2F00, 0x300C, 0xFE31)]:
            with self.subTest(cp=hex(ord(ch))):
                self.assertEqual(tts_text.tidy_off_script(f"a{ch}b"), "a b")
        # a CJK ideograph (origin removed it too) inside an Arabic word: the word stays one word
        self.assertEqual(tts_text.tidy_off_script("صد" + chr(0x4E2D) + "يقي"), "صديقي")
        # a run that mixes what origin removed with what it kept is one space
        self.assertEqual(tts_text.tidy_off_script("a" + chr(0x4E2D) + "д" + chr(0x4E2D) + "b"), "a b")
        # next to a space, at an end, after an opening mark or before a closing one: nothing
        self.assertEqual(tts_text.tidy_off_script("a д b"), "a  b")
        self.assertEqual(tts_text.tidy_off_script("дHello"), "Hello")
        self.assertEqual(tts_text.tidy_off_script("Helloд"), "Hello")
        self.assertEqual(tts_text.tidy_off_script("Helloд."), "Hello.")
        self.assertEqual(tts_text.tidy_off_script("(" + chr(0x300C) + "word" + chr(0x300D) + ")."), "(word).")

    def test_the_characters_origin_removed_are_removed_after_the_guards_too(self):
        # Kana, CJK ideographs and extension A, compatibility ideographs, Hangul syllables: what
        # origin/hackathon removed, removed the same way (a reply given to guard_speech without the
        # strip before it), punctuation-like or not (the Yijing hexagrams sit inside U+3400..U+9FFF)
        for ch in [chr(c) for c in (0x3041, 0x309B, 0x30FB, 0x30FC, 0x3400, 0x4DC0, 0x4E2D, 0xF900,
                                    0xAC00, 0xD7A3)]:
            with self.subTest(cp=hex(ord(ch))):
                self.assertEqual(tts_text.tidy_off_script(f"a{ch}b"), "ab")

    def test_off_script_punctuation_between_words_keeps_the_words_apart(self):
        # the said text keeps "said" a word of its own (the guards read the mark itself, as origin)
        for ch in [chr(c) for c in (0x3003, 0x300C, 0x300D, 0x3008, 0x3010, 0xFE41, 0xFF5B, 0xFF3B,
                                    0xFF08, 0xFF40, 0xFF20, 0xFF0F, 0xFF0A, 0xFF5E, 0xFF3F, 0xFF65,
                                    0xFFE5, 0x2F00, 0x0E31, 0x094D)]:
            with self.subTest(cp=hex(ord(ch))):
                got = tts_text.tidy_off_script(f"The Prophet said{ch}be tidy.")
                self.assertRegex(got, r"\bsaid\b")
                self.assertEqual(got.split(), ["The", "Prophet", "said", "be", "tidy."])
                got = tts_text.tidy_off_script(f"The Prophet said{ch * 2}be tidy.")
                self.assertEqual(got.split(), ["The", "Prophet", "said", "be", "tidy."])

    def test_cyrillic_hebrew_devanagari_and_thai_go_after_the_guards(self):
        for ch in ("Ж", "д", "א", "ש", "अ", "ह", "ก", "อ"):
            with self.subTest(cp=hex(ord(ch))):
                self.assertEqual(tts_text.tidy_off_script(f"a{ch}b"), "a b")
                self.assertEqual(tts_text.tidy_off_script(f"a{ch}{ch}b"), "a b")
        # a Cyrillic word with no Latin look-alike letter goes
        self.assertEqual(tts_text.tidy_off_script("Hello шлюз friend"), "Hello  friend")
        # look-alike letters are never taken out: a Cyrillic word keeps them as Latin letters and
        # its other letters go (context-free on purpose, see tts_text.HOMOGLYPHS)
        self.assertEqual(tts_text.tidy_off_script("Hello привет friend"), "Hello p bet friend")
        self.assertEqual(tts_text.tidy_off_script("مرحبا สวัส بك"), "مرحبا  بك")

    def test_a_letter_origin_kept_never_glues_two_arabic_words(self):
        # Origin passed these letters on and its attribution guard read them as a word gap (they
        # are not Arabic letters), so it declined these. The guards still read them as they are
        # (the strip before the guards is origin's); after the guards a letter between two words
        # becomes a space, never removed, so the said text never glues the two words.
        from conversation.agent.scripture_guard import find_attribution

        glued = {
            "النبي فعلдذلك.": "النبي فعل ذلك.",
            "النبي فعلשذلك اليوم.": "النبي فعل ذلك اليوم.",
            "كتبдالنبي كان يحب القمر.": "كتب النبي كان يحب القمر.",
            "لأنשالنبي كان يحب القمر.": "لأن النبي كان يحب القمر.",
            "قصةสالنبي كان يحب القمر.": "قصة النبي كان يحب القمر.",
        }
        for text, want in glued.items():
            with self.subTest(text=text):
                self.assertIsNotNone(find_attribution(text))                    # what the guard reads
                self.assertEqual(tts_text.strip_foreign_script(text), text)     # unchanged before it
                self.assertEqual(tts_text.tidy_off_script(text), want)
                for size in (1, 2, 3, 7):
                    self.assertEqual(_tidied_in_chunks(text, size), want)

    def test_hebrew_and_hangul_look_alikes_become_latin_letters(self):
        for ch, latin in (("ו", "l"), ("ן", "l"), ("ס", "o"), ("ㅇ", "o"), ("ㅣ", "l")):
            with self.subTest(cp=hex(ord(ch))):
                self.assertEqual(tts_text.HOMOGLYPHS[ch], latin)
                self.assertEqual(tts_text.tidy_off_script(f"x{ch}y"), f"x{latin}y")
        for text, want in (("Please tell a trusted aduןt now.", "Please tell a trusted adult now."),
                           ("Please tell a trusted aduוt now.", "Please tell a trusted adult now."),
                           ("Tell a teacher tㅇday, a trusted aduㅣt.", "Tell a teacher today, a trusted adult.")):
            with self.subTest(text=text):
                self.assertEqual(tts_text.tidy_off_script(text), want)
                self.assertEqual(tts_text.tidy_off_script(prepare_for_tts(text, "en")), want)
        # the Devanagari digit zero is a digit, not a letter: it becomes "0" (never "o")
        self.assertEqual(tts_text.tidy_off_script("tr०st"), "tr0st")

    def test_devanagari_and_thai_digits_become_ascii_digits(self):
        # after the guards, one to one: Devanagari and Thai "call 911" are said "call 911",
        # whole and in chunks of 1, 3 and 1000
        dev = "".join(chr(c) for c in (0x096F, 0x0967, 0x0967))
        thai = "".join(chr(c) for c in (0x0E59, 0x0E51, 0x0E51))
        for text in ("call " + dev, "call " + thai):
            with self.subTest(text=text):
                self.assertEqual(tts_text.tidy_off_script(text), "call 911")
                for size in (1, 3, 1000):
                    self.assertEqual(_tidied_in_chunks(text, size), "call 911")
                # before the guards nothing changed: the strip there keeps them, as origin's did
                self.assertEqual(tts_text.strip_foreign_script(text), text)
        # every digit of both scripts becomes the ASCII digit of its value, inside a word too
        for base in (0x0966, 0x0E50):
            for value in range(10):
                ch = chr(base + value)
                with self.subTest(cp=hex(base + value)):
                    self.assertEqual(tts_text.tidy_off_script(f"x{ch}y"), f"x{value}y")

    def test_cyrillic_and_greek_look_alikes_become_latin_letters(self):
        for ch, latin in tts_text.HOMOGLYPHS.items():
            with self.subTest(cp=hex(ord(ch))):
                self.assertEqual(tts_text.tidy_off_script(f"x{ch}y"), f"x{latin}y")
                self.assertEqual(tts_text.tidy_off_script(ch), latin)          # alone too
        # the letters the review named
        for cyr, latin in zip("аеорсхуіјѕкмнтв", "aeopcxyijskmhtb"):
            self.assertEqual(tts_text.tidy_off_script(cyr), latin)
        for grk, latin in zip("οαερ", "oaep"):
            self.assertEqual(tts_text.tidy_off_script(grk), latin)

    def test_a_safety_line_with_look_alike_letters_keeps_every_word(self):
        # "trusted аdult" (Cyrillic а): the speech cleaner and the guards read it as origin did,
        # and the TTS and the chat then get "trusted adult", never "trusted dult"
        cases = {
            "Please tell a trusted аdult right now.": "Please tell a trusted adult right now.",
            "Tell а trusted adult, a pаrent or a tеаcher.":
                "Tell a trusted adult, a parent or a teacher.",
            "Тell your раrеnt or cаll for help right nоw.":
                "Tell your parent or call for help right now.",
            "Please tell a trusted αdult or a tεacher tοday.":
                "Please tell a trusted adult or a teacher today.",
            "You are sаfе with mе. Plеаsе тell a тrusтed adulт.":
                "You are safe with me. Please tell a trusted adult.",
        }
        for text, want in cases.items():
            with self.subTest(text=text):
                self.assertEqual(tts_text.tidy_off_script(text), want)
                self.assertEqual(tts_text.tidy_off_script(prepare_for_tts(text, "en")), want)
                self.assertEqual(_tidied_in_chunks(text, 1), want)

    def test_an_attribution_written_with_look_alikes_is_said_in_latin_letters(self):
        # The guards read the look-alike letters as origin's guards did (the verdict is origin's:
        # test_off_script_parity checks it on the voice and the chat); what is said is
        # in Latin letters.
        for text in ("The Рrophet ѕaid to be kind.", "The Prοphet sаid to be kind.",
                     "Аllah ѕаys be kind."):
            with self.subTest(text=text):
                self.assertTrue(tts_text.tidy_off_script(text).isascii())
                self.assertEqual(tts_text.strip_foreign_script(text), text)

    def test_full_width_angle_brackets_go(self):
        lt, gt = chr(0xFF1C), chr(0xFF1E)
        self.assertEqual(tts_text.tidy_off_script(f"a{lt}b{gt}c"), "a b c")
        got = tts_text.tidy_off_script(f"{lt}Please tell a trusted adult{gt} now.")
        self.assertEqual(got, "Please tell a trusted adult now.")
        self.assertEqual(tts_text.tidy_off_script(prepare_for_tts(f"{lt}Please tell a trusted adult{gt} now.", "en")),
                         "Please tell a trusted adult now.")

    def test_full_width_forms_keep_their_meaning(self):
        text = ("Hi" + chr(0xFF01) + " " + chr(0xFF21) + chr(0xFF22) + chr(0xFF23) + " ok" + chr(0x3002)
                + " yes" + chr(0x3001) + " no")
        self.assertEqual(tts_text.tidy_off_script(text), "Hi! ABC ok. yes, no")
        self.assertEqual(tts_text.tidy_off_script("a" + chr(0x3000) + "b"), "a b")
        # (the attribution guard reads "Prophet！ of Allah said" as origin's did, and declines it;
        # only then is the mark said as "!": test_off_script_parity)

    def test_full_width_markup_forms_never_become_their_ascii_form(self):
        # after the guards and the cleaner, a plain "*", "_", "~", "`", "@", "/", "<...>" would be
        # read aloud or as markup, and "[...](...)", "{...}" shown raw in the chat: these go
        not_mapped = {0xFF5B: "{", 0xFF5D: "}", 0xFF3B: "[", 0xFF3D: "]", 0xFF08: "(", 0xFF09: ")",
                      0xFF40: "`", 0xFF20: "@", 0xFF0F: "/", 0xFF0A: "*", 0xFF5E: "~", 0xFF3F: "_",
                      0xFF1C: "<", 0xFF1E: ">"}
        for cp, ascii_form in not_mapped.items():
            ch = chr(cp)
            with self.subTest(cp=hex(cp)):
                self.assertEqual(tts_text.tidy_off_script(f"a{ch}b{ch}c"), "a b c")
                self.assertNotIn(ascii_form, tts_text.tidy_off_script(f"x {ch}{ch}y{ch}{ch} z"))
        lb, rb = chr(0xFF5B), chr(0xFF5D)
        for text, want in ((f"{lb}{lb}Please tell a trusted adult right now{rb}{rb}",
                            "Please tell a trusted adult right now"),
                           (f"Please tell a {lb}trusted adult{rb} today.", "Please tell a trusted adult today."),
                           (f"أرجوك {lb}أخبر شخصا بالغا{rb} الآن.", "أرجوك أخبر شخصا بالغا الآن.")):
            with self.subTest(text=text):
                self.assertEqual(tts_text.tidy_off_script(text), want)
                self.assertEqual(tts_text.tidy_off_script(prepare_for_tts(text, "en")), want)
        # the plain ASCII braces are left as they were (the brace rule is not this function's)
        self.assertEqual(tts_text.tidy_off_script("a{b}c"), "a{b}c")

    def test_arabic_latin_and_arabic_presentation_forms_are_never_touched(self):
        for text in ("مرحبا " + chr(0xFDFA) + " " + chr(0xFE8D) + chr(0xFE8E) + " ـ ، ؟",
                     "Café — 5€", "a" + chr(0x200D) + "b", "I love you 😀!", "1, 2, 3."):
            self.assertEqual(tts_text.tidy_off_script(text), text)

    def test_the_stream_gives_the_whole_texts_output_at_every_chunking(self):
        import random

        rnd = random.Random(5)
        alphabet = (list("ab حب.,!? ") + ["д", "а", "Р", "ש", "ו", "ส", "क", "०", "α", "λ"]
                    + [chr(c) for c in (0x4E2D, 0x3042, 0xAC00, 0x1100, 0x3131, 0x3000, 0x3001, 0x3002,
                                        0x3003, 0x300C, 0x300D, 0xFF01, 0xFF08, 0xFF09, 0xFF0E, 0xFF1A,
                                        0xFF5B, 0xFF71, 0x20001, 0x0E59, 0x096F)])
        bad = []
        for _ in range(600):
            text = "".join(rnd.choice(alphabet) for _ in range(rnd.randint(0, 40)))
            want = tts_text.tidy_off_script(text)
            for size in (1, 2, 3, 5, 1000, None):
                got = _tidied_in_chunks(text, size, rnd)
                if got != want:
                    bad.append((text, size, want, got))
        self.assertEqual(bad, [], bad[:3])

    def test_the_stream_passes_other_chunks_on_after_the_held_text(self):
        import asyncio

        marker = object()

        async def src():
            for chunk in ("Hello", "д", marker, "friend", "д"):
                yield chunk

        async def go():
            return [c async for c in tts_text.tidy_off_script_stream(src())]

        out = asyncio.run(go())
        self.assertEqual(out, ["Hello", marker, "friend"])       # a run at an end goes
        self.assertTrue(all(type(c) is str for c in out if c is not marker))


def _tidied_in_chunks(text, size, rnd=None):
    """tts_text.OffScriptTidier fed ``text`` in chunks of ``size`` (None: random chunks)."""
    tidier = tts_text.OffScriptTidier()
    chunks, i = [], 0
    while i < len(text):
        k = size if size is not None else rnd.randint(1, 6)
        chunks.append(text[i:i + k])
        i += k
    return "".join(tidier.feed(c) for c in chunks) + tidier.flush()


if __name__ == "__main__":
    unittest.main()
