"""The reply language: the PARENT's language, unless REPLY_LANGUAGE_FOLLOWS_CHILD is on (hk/12 port).

The lead's design is the default: the parent chooses the companion's language; the prompt, the TTS,
the speech cleaner, the guards and the fixed lines keep to it. The CEO's rule (the reply follows
the child) is behind the flag, default off, and even then switches only between Arabic and English,
only on a clear message, and never because of another script (speech-to-text noise).

Covers the flag, the decider (turn_language.py), the per-turn TURN LANGUAGE line after hk/12's turn
note, the session prompt paragraphs (prompt.build_instructions), the TTS follow-up, the speech
cleaner, the attribution decline and the fixed fallback lines: with the flag off each one equals
hk/12-hybrid's (cfa101c) for every input. Ported from hk/03-output-guard-lang's test_turn_language.py
(the decider tests word for word); hk/12 has no turn_policy, so the turn note is turn_guard.check's.
Synthetic phrases only; no Quran or hadith text.

Run from backend/:  python manage.py test conversation.agent.test_turn_language \
    --settings=config.settings_sqlite_test
"""
import asyncio
import os
from contextlib import contextmanager
from types import SimpleNamespace
from unittest import mock

from django.test import SimpleTestCase

from conversation.agent.prompt import MAKER_LINE_EN, build_instructions
from conversation.agent.turn_language import (
    EN_EVIDENCE, FOLLOWS_CHILD_ENV, decide_reply_language as decide, language_line,
    reply_language_follows_child,
)
from conversation.agent.turn_pipeline import GUARD_ERROR_NOTE, _turn_lang

AR_SENTENCE = "أريد أن ألعب لعبة جديدة اليوم"
AR_WORD = "شكرا"
EN_SENTENCE = "please tell me a story about the moon"

# Every kind of input: noise, other scripts, one word, Arabizi, mixed, digits, safety, identity.
CORPUS = (
    "", "   ", "ok", "hmm", "uh hmm mm", "😀", "123", "???", AR_WORD, AR_SENTENCE, EN_SENTENCE,
    "hello", "hello there", "hello there friend", "yes please",
    "你好你好 谢谢", "你好 hello how are you", "こんにちは", "안녕하세요 친구", "привет как дела",
    "Γεια σου φίλε", "שלום", "marhaba habibi kifak", "7abibi kifak", "I'm Tayeb",
    "أريد أن ألعب minecraft", "can we talk about لعبة الليلة please", "شكرا thanks",
    "I am in grade5 and I like level5", "my dad hits me", "أبي يضربني كل يوم",
    "someone touches me at school and it hurts", "are you a robot", "who made you",
    "هل أنت إنسان", "tell me about honesty", "حدثني عن الصدق", "ok شكرا", "аре",
)

# hk/12's LANGUAGE paragraphs (prompt._LANGUAGE at ccf4330 and cfa101c), word for word.
_AL_ARABIYYA = "".join(chr(c) for c in (0x0627, 0x0644, 0x0639, 0x0631, 0x0628, 0x064A, 0x0629))
HK12_AR_PARAGRAPH = (
    "\n\nLANGUAGE: This session is in Arabic (" + _AL_ARABIYYA + "), chosen by the parent. Always reply in "
    "Arabic, whatever language the child writes in."
)
HK12_EN_PARAGRAPH = (
    "\n\nLANGUAGE: This session is in English, chosen by the parent. Always reply in English, in "
    "Latin letters, whatever language the child writes in; write the salam as 'Assalamu "
    "alaikum', and give the English AI line, never the Arabic one."
)


def hk12_turn_lang(text, session_lang):
    """hk/12's turn_pipeline._turn_lang, copied: the reference the flag-off path must equal."""
    from conversation.agent.text_match import has_arabic

    if has_arabic(text):
        return "ar"
    if any("a" <= ch.lower() <= "z" for ch in text):
        return "en"
    return session_lang if session_lang in ("ar", "en") else "en"


def hk12_note(text):
    """hk/12's turn note for ``text``: turn_guard.check's note, "" when the guard says nothing."""
    from conversation.agent.turn_guard import check

    hit = check(text)
    return hit.note if hit is not None else ""


@contextmanager
def follows_child(on: bool):
    """REPLY_LANGUAGE_FOLLOWS_CHILD set to "1" (on) or unset (off) inside the block."""
    with mock.patch.dict(os.environ, {}):
        if on:
            os.environ[FOLLOWS_CHILD_ENV] = "1"
        else:
            os.environ.pop(FOLLOWS_CHILD_ENV, None)
        yield


def make_agent(lang="en"):
    from conversation.agent.agent_class import AlSadiqAgent

    return AlSadiqAgent(db_session_id=1, child_id=1, language=lang)


class FakeTTS:
    def __init__(self, language):
        self._opts = SimpleNamespace(language=language)
        self.calls = []

    def update_options(self, **kw):
        self.calls.append(kw)
        self._opts.language = kw.get("language", self._opts.language)


def with_tts(agent, tts):
    # Agent.session is a read-only property that raises before the agent runs
    return mock.patch.object(type(agent), "session", new_callable=mock.PropertyMock,
                             return_value=SimpleNamespace(tts=tts))


def speak(agent, text):
    async def agen():
        yield text

    async def go():
        return "".join([c async for c in agent.guard_speech(agen())])

    return asyncio.run(go())


def spoken_numbers(language_reader):
    from conversation.agent.tts_text import speech_tts_text_transform

    async def gen():
        yield "I have 3 cats."

    async def collect(stream):
        return "".join([c async for c in stream if isinstance(c, str)])

    return asyncio.run(collect(speech_tts_text_transform(language_reader)(gen())))


def fallback_language(agent, last_text):
    from conversation.agent import agent_class

    seen = []
    with mock.patch.object(agent_class, "with_llm_fallback",
                           side_effect=lambda *args, **kw: seen.append(kw["language_for"]) or iter(())), \
            mock.patch.object(agent_class.Agent.default, "llm_node", return_value=iter(()), create=True):
        agent.llm_node(SimpleNamespace(items=[SimpleNamespace(role="user", content=[last_text],
                                                              text_content=last_text, type="message")]), [], None)
    return seen[0]("turn")


class FlagTests(SimpleTestCase):
    def test_off_unless_set_on(self):
        with follows_child(False):
            self.assertFalse(reply_language_follows_child())
        for value in ("1", "on", "true", "yes", " ON ", "True", "YES"):
            with self.subTest(value=value), mock.patch.dict(os.environ, {FOLLOWS_CHILD_ENV: value}):
                self.assertTrue(reply_language_follows_child())
        for value in ("0", "off", "false", "no", "", "2", "enabled"):
            with self.subTest(value=value), mock.patch.dict(os.environ, {FOLLOWS_CHILD_ENV: value}):
                self.assertFalse(reply_language_follows_child())

    def test_read_on_every_call(self):
        a = make_agent("ar")
        with follows_child(True):
            a._prepare(EN_SENTENCE, typed=True)
            self.assertEqual(a.reply_language, "en")
        with follows_child(False):
            self.assertEqual(a.reply_language, "ar")        # off again: the session language at once
            self.assertEqual(a._prepare(EN_SENTENCE, typed=True), "")


class FlagOffMatchesHk12Tests(SimpleTestCase):
    """REPLY_LANGUAGE_FOLLOWS_CHILD unset: hk/12's parent-pinned behaviour, for every input."""

    def setUp(self):
        patcher = follows_child(False)
        patcher.__enter__()
        self.addCleanup(patcher.__exit__, None, None, None)

    def test_the_prompt_is_hk12s_byte_for_byte(self):
        for language in ("ar", "en", "fr", "", "ar-SA", "EN"):
            for age_band in (None, "6-9", "10-13", "x"):
                for memory in (None, "", "Has a cat named Luna."):
                    for quests in (None, "- quest one"):
                        kw = dict(language=language, age_band=age_band, session_memory=memory,
                                  active_quests_text=quests)
                        with self.subTest(**kw):
                            text = build_instructions(**kw)
                            self.assertEqual(text, build_instructions(**kw, follows_child=False))
                            self.assertTrue(text.endswith(
                                HK12_AR_PARAGRAPH if language == "ar" else HK12_EN_PARAGRAPH))
                            self.assertNotIn("TURN LANGUAGE", text)
                            self.assertEqual(text.count("\n\nLANGUAGE:"), 1)
        ar, en = make_agent("ar").instructions, make_agent("en").instructions
        self.assertTrue(ar.endswith(HK12_AR_PARAGRAPH))
        self.assertTrue(en.endswith(HK12_EN_PARAGRAPH))

    def test_the_turn_language_and_fallback_are_hk12s_script_check(self):
        for lang in ("ar", "en", "xx"):
            for text in CORPUS:
                with self.subTest(lang=lang, text=text):
                    self.assertEqual(_turn_lang(text, lang), hk12_turn_lang(text, lang))

    def test_the_turn_note_is_hk12s_for_every_input(self):
        for lang in ("ar", "en"):
            for typed in (False, True):
                a = make_agent(lang)
                for text in CORPUS:
                    with self.subTest(lang=lang, typed=typed, text=text):
                        got = a._prepare(text, typed=typed)
                        self.assertEqual(got, hk12_note(text))
                        self.assertNotIn("TURN LANGUAGE", got)
                        self.assertEqual(a._turn_language, hk12_turn_lang(text, lang))

    def test_a_guard_error_gives_hk12s_note_alone(self):
        from conversation.agent import turn_pipeline

        a = make_agent("ar")
        with mock.patch.object(turn_pipeline, "check", side_effect=RuntimeError("boom")), \
                mock.patch.object(a, "_spawn", side_effect=lambda coro: coro.close()):
            self.assertEqual(a._prepare(EN_SENTENCE, typed=True), GUARD_ERROR_NOTE)

    def test_the_tts_is_never_touched_and_every_language_stays_the_sessions(self):
        for lang in ("ar", "en"):
            a, tts = make_agent(lang), FakeTTS(lang)
            with with_tts(a, tts):
                for text in CORPUS:
                    for typed in (False, True):
                        with self.subTest(lang=lang, text=text, typed=typed):
                            a._prepare(text, typed=typed)
                            self.assertEqual(a.reply_language, lang)
                            self.assertEqual(a.speech_language, a.language)    # hk/12 read agent.language
                            self.assertEqual(a._guard_reply_language(), a._guard_language)
            self.assertEqual(tts.calls, [])

    def test_the_speech_cleaner_reads_numbers_in_the_session_language(self):
        a = make_agent("ar")
        a._prepare(EN_SENTENCE, typed=True)
        self.assertNotIn("three", spoken_numbers(lambda: a.speech_language))
        b = make_agent("en")
        b._prepare(AR_SENTENCE, typed=True)
        self.assertIn("three", spoken_numbers(lambda: b.speech_language))

    def test_the_attribution_decline_is_in_the_session_language(self):
        from conversation.agent.scripture_guard import DECLINE_TEXT

        a = make_agent("ar")
        a._prepare(EN_SENTENCE, typed=True)
        out = speak(a, "Nice day. The Prophet said to always be kind.")
        self.assertIn(DECLINE_TEXT["ar"].split(".")[0], out)
        self.assertNotIn(DECLINE_TEXT["en"].split(".")[0], out)

    def test_the_fixed_fallback_line_is_hk12s(self):
        for lang in ("ar", "en"):
            for text in CORPUS:
                with self.subTest(lang=lang, text=text):
                    a = make_agent(lang)
                    a._prepare(text)
                    self.assertEqual(fallback_language(a, text), hk12_turn_lang(text, lang))


class DeciderTests(SimpleTestCase):
    """decide_reply_language: the rules of the flag-on path (the function itself reads no flag)."""

    def test_noise_and_other_scripts_keep_the_parents_language(self):
        for parent in ("ar", "en"):
            for text in ("", "   ", "😀", "123", "???", "uh hmm mm", "hmm", "brr shh", "你好你好 谢谢",
                         "こんにちは 元気", "안녕하세요 친구 오늘", "привет как дела сегодня",
                         "Γεια σου φίλε μου", "שלום חבר", "x y z", "你好 你好 你好 你好 hello"):
                for typed in (False, True):
                    with self.subTest(parent=parent, text=text, typed=typed):
                        self.assertEqual(decide(text, parent, typed=typed), parent)

    def test_one_word_never_switches(self):
        for typed in (False, True):
            for word in ("hello", "ok", "yes", "thanks", "minecraft", "Tayeb"):
                self.assertEqual(decide(word, "ar", typed=typed), "ar")
            self.assertEqual(decide(AR_WORD, "en", typed=typed), "en")
        self.assertEqual(decide(f"{AR_SENTENCE} hello", "ar", typed=True), "ar")   # one English word in Arabic

    def test_a_typed_message_switches_on_two_real_words(self):
        self.assertEqual(decide("hello there", "ar", typed=True), "en")
        self.assertEqual(decide(EN_SENTENCE, "ar", typed=True), "en")
        self.assertEqual(decide("أريد أن", "en", typed=True), "ar")
        self.assertEqual(decide(AR_SENTENCE, "en", typed=True), "ar")

    def test_a_spoken_turn_switches_only_on_several_real_words(self):
        self.assertEqual(decide("hello there", "ar"), "ar")                  # two words: a fragment
        self.assertEqual(decide("hello there friend", "ar"), "en")
        self.assertEqual(decide(EN_SENTENCE, "ar"), "en")
        self.assertEqual(decide("أريد أن", "en"), "en")
        self.assertEqual(decide("أريد أن ألعب", "en"), "ar")

    def test_a_mostly_noise_fragment_never_switches(self):
        # the real words must be three quarters of the message's words
        self.assertEqual(decide("你好 谢谢 再见 hello there friend", "ar"), "ar")
        self.assertEqual(decide("uh um hmm mm hello there friend", "ar"), "ar")
        self.assertEqual(decide("привет как дела hello there friend", "ar", typed=True), "ar")
        self.assertEqual(decide("你好 hello how are you", "ar", typed=True), "en")    # 4 of 5 words

    def test_mixed_messages_switch_only_with_a_clear_majority(self):
        self.assertEqual(decide("can we talk about لعبة الليلة please", "ar", typed=True), "ar")   # 5 of 7
        self.assertEqual(decide("I want to play لعبة today", "ar", typed=True), "en")            # 5 of 6
        self.assertEqual(decide("شكرا thanks", "en", typed=True), "en")
        self.assertEqual(decide("أريد أن ألعب minecraft", "en", typed=True), "ar")                 # 3 of 4

    def test_only_arabic_and_english(self):
        for text in ("Bonjour mon ami comment allez vous", "Hola amigo como estas hoy"):
            # never French or Spanish (there is no third answer)
            self.assertIn(decide(text, "ar", typed=True), ("ar", "en"))
        for text in CORPUS:
            for parent in ("ar", "en"):
                self.assertIn(decide(text, parent, "en", typed=True), ("ar", "en"))

    def test_another_latin_script_language_is_not_english(self):
        # round 1 review: every Latin-script word with a vowel counted as English, so these
        # switched an Arabic session to English. A move to English now needs an English word
        # (EN_EVIDENCE); without one the reply keeps the last reply language (rule 7).
        for text in ("je veux jouer avec toi", "hola como estas amigo", "ich möchte spielen bitte",
                     "merhaba nasilsin arkadas", "saya mau main game",
                     "Bonjour mon ami comment allez vous", "Hola amigo como estas hoy",
                     "voglio giocare con i bambini", "eu quero brincar do jogo"):
            for typed in (True, False):
                with self.subTest(text=text, typed=typed):
                    self.assertEqual(decide(text, "ar", typed=typed), "ar")
                    self.assertEqual(decide(text, "ar", "en", typed=typed), "en")   # last reply kept
                    self.assertEqual(decide(text, "en", typed=typed), "en")         # parent's language
        # none of the words left out of the evidence list is in it
        for word in ("a", "i", "in", "on", "to", "so", "no", "me", "do", "can", "come", "was", "will",
                     "die", "man", "an", "also", "kind", "name", "hand", "bad", "see", "red", "son",
                     "game", "question", "secret"):
            self.assertNotIn(word, EN_EVIDENCE)
        # a real English sentence still switches, typed (2+ words) and spoken (3+ words)
        for text in ("I want to play a game", "can you tell me a joke", "where is my cat",
                     "my dad hits me", "I'm sad today", "speak French to me", "talk to me now",
                     "someone hurt me"):
            with self.subTest(text=text):
                self.assertEqual(decide(text, "ar", typed=True), "en")
                self.assertEqual(decide(text, "ar"), "en")

    def test_a_known_speech_to_text_hallucination_never_switches_a_spoken_turn(self):
        # round 1 review: these are what the speech-to-text writes for silence or music
        for text in ("Thank you for watching", "Thank you for watching!", "thanks for watching guys",
                     "Please subscribe to my channel"):
            with self.subTest(text=text):
                self.assertEqual(decide(text, "ar"), "ar")
                self.assertEqual(decide(text, "ar", "en"), "en")            # the last reply kept
        for text in ("ترجمة نانسي قنقر", "اشتركوا في القناة", "شكراً للمشاهدة",
                     "ترجمه نانسي قنقر"):
            with self.subTest(text=text):
                self.assertEqual(decide(text, "en"), "en")
                self.assertEqual(decide(text, "ar", "en"), "en")            # never a way back either
        # a typed message is the child's own words: it is not checked
        self.assertEqual(decide("Thank you for watching", "ar", typed=True), "en")
        # a phrase matches whole words only
        self.assertEqual(decide("I like watching cartoons with you", "ar"), "en")

    def test_arabizi_never_switches_away_from_the_parents_language(self):
        for text in ("marhaba habibi kifak", "7abibi kifak", "ana 5ayef men el madrase", "wallah inta kwayyes"):
            with self.subTest(text=text):
                self.assertEqual(decide(text, "ar", typed=True), "ar")       # never "English"
                self.assertEqual(decide(text, "en", typed=True), "en")       # Latin letters: not Arabic script
                self.assertEqual(decide(text, "ar", "en", typed=True), "ar")  # back to the parent's Arabic

    def test_english_with_a_name_or_a_level_is_english(self):
        for text in ("my cat Habibi is asleep on the sofa", "I am in grade5 and I like level5",
                     "someone touches me at school and it hurts, I am in grade5 class"):
            with self.subTest(text=text):
                self.assertEqual(decide(text, "ar", typed=True), "en")
                self.assertEqual(decide(text, "en"), "en")

    def test_after_a_switch_an_unclear_message_keeps_the_last_reply_language(self):
        # sticky: the reply does not flip back on "ok" or on noise ...
        for text in ("ok", "hmm", "你好你好", "😀", "hello"):
            with self.subTest(text=text):
                self.assertEqual(decide(text, "ar", "en", typed=True), "en")
        # ... and comes back to the parent's language on a message in it (one word is enough)
        self.assertEqual(decide(AR_WORD, "ar", "en"), "ar")
        self.assertEqual(decide(AR_SENTENCE, "ar", "en"), "ar")
        self.assertEqual(decide("ok", "en", "ar", typed=True), "en")
        self.assertEqual(decide("ok شكرا", "ar", "en", typed=True), "en")     # half and half: unclear

    def test_a_turn_by_turn_conversation(self):
        prev, seen = None, []
        for text, typed in ((AR_SENTENCE, False), ("hello", True), (EN_SENTENCE, True), ("ok", True),
                            ("你好你好", False), (AR_WORD, False), ("hello there", False), (EN_SENTENCE, False)):
            prev = decide(text, "ar", prev, typed=typed)
            seen.append(prev)
        self.assertEqual(seen, ["ar", "ar", "en", "en", "en", "ar", "ar", "en"])

    def test_unknown_languages_fall_back_to_english(self):
        self.assertEqual(decide("hmm", None), "en")
        self.assertEqual(decide("hmm", "fr"), "en")
        self.assertEqual(decide("hmm", "ar-SA"), "ar")
        self.assertEqual(decide("hmm", "ar", "fr"), "ar")        # an unknown previous: the parent's
        self.assertEqual(decide("hmm", "ar", "en-US"), "en")

    def test_language_line_names_the_language_and_the_disclosure(self):
        self.assertIn("reply in Arabic", language_line("ar"))
        self.assertIn("reply in English", language_line("en"))
        self.assertIn("AI", language_line("ar"))
        self.assertIn("Never reply in a language other than Arabic or English", language_line("en"))


class FlagOnTests(SimpleTestCase):
    """REPLY_LANGUAGE_FOLLOWS_CHILD=1: the reply follows the child, under the decider's rules."""

    def setUp(self):
        patcher = follows_child(True)
        patcher.__enter__()
        self.addCleanup(patcher.__exit__, None, None, None)

    def test_noise_or_cjk_keeps_the_parents_language(self):
        noise = (chr(0x4F60) + chr(0x597D) + " " + chr(0x8C22) + chr(0x8C22), "uh hmm mm", chr(0x1F600),
                 "".join(chr(c) for c in (0x043F, 0x0440, 0x0438, 0x0432, 0x0435, 0x0442)) + " "
                 + "".join(chr(c) for c in (0x043A, 0x0430, 0x043A)) + " "
                 + "".join(chr(c) for c in (0x0434, 0x0435, 0x043B, 0x0430)),
                 "".join(chr(c) for c in (0x3053, 0x3093, 0x306B, 0x3061, 0x306F)))
        for lang in ("ar", "en"):
            for text in noise:
                for typed in (False, True):
                    with self.subTest(lang=lang, text=text, typed=typed):
                        a = make_agent(lang)
                        out = a._prepare(text, typed=typed)
                        self.assertEqual(a.reply_language, lang)
                        self.assertNotIn("TURN LANGUAGE", out)

    def test_one_english_word_in_an_arabic_session_keeps_arabic(self):
        for typed in (False, True):
            for word in ("hello", "minecraft", "ok"):
                with self.subTest(word=word, typed=typed):
                    a = make_agent("ar")
                    out = a._prepare(word, typed=typed)
                    self.assertEqual(a.reply_language, "ar")
                    self.assertEqual(out, hk12_note(word))

    def test_a_clear_english_sentence_typed_in_an_arabic_session_switches_only_with_the_flag(self):
        a = make_agent("ar")
        self.assertEqual(a._prepare(EN_SENTENCE, typed=True), language_line("en"))
        self.assertEqual(a.reply_language, "en")
        with follows_child(False):
            b = make_agent("ar")
            self.assertEqual(b._prepare(EN_SENTENCE, typed=True), "")
            self.assertEqual(b.reply_language, "ar")

    def test_reply_to_typed_counts_as_typed(self):
        a = make_agent("ar")
        session = mock.Mock()
        a.reply_to_typed(session, "hello there")                     # two typed words: a switch
        self.assertEqual(a.reply_language, "en")
        kwargs = session.generate_reply.call_args.kwargs
        self.assertIn("chat_ctx", kwargs)                            # the TURN LANGUAGE line rides in it
        b = make_agent("ar")
        b._prepare("hello there")                                    # the same two words spoken: no switch
        self.assertEqual(b.reply_language, "ar")

    def test_the_line_stays_while_switched_and_goes_when_back(self):
        a = make_agent("ar")
        self.assertEqual(a._prepare(AR_SENTENCE), "")
        self.assertEqual(a._prepare(EN_SENTENCE, typed=True), language_line("en"))
        self.assertEqual(a._prepare("ok", typed=True), language_line("en"))     # still English, off-session
        self.assertEqual(a._prepare(AR_SENTENCE), language_line("ar"))          # back: said once
        self.assertEqual(a._prepare(AR_SENTENCE), "")

    def test_a_turn_note_keeps_its_text_and_the_language_line_follows_it(self):
        text = "my dad hits me and it hurts"
        note = hk12_note(text)
        self.assertTrue(note)                                        # hk/12's guard speaks up here
        a = make_agent("ar")
        out = a._prepare(text, typed=True)
        self.assertEqual(out, note + "\n\n" + language_line("en"))
        self.assertEqual(out.count("TURN LANGUAGE"), 1)
        b = make_agent("en")
        self.assertEqual(b._prepare(text, typed=True), note)         # the session's language: no line

    def test_a_guard_error_keeps_its_note_and_the_language_line_follows_it(self):
        from conversation.agent import turn_pipeline

        a = make_agent("ar")
        with mock.patch.object(turn_pipeline, "check", side_effect=RuntimeError("boom")), \
                mock.patch.object(a, "_spawn", side_effect=lambda coro: coro.close()):
            self.assertEqual(a._prepare(EN_SENTENCE, typed=True),
                             GUARD_ERROR_NOTE + "\n\n" + language_line("en"))

    def test_the_childs_turn_language_is_still_hk12s_script_check(self):
        a = make_agent("ar")
        for text in CORPUS:
            with self.subTest(text=text):
                a._prepare(text, typed=True)
                self.assertEqual(a._turn_language, hk12_turn_lang(text, "ar"))

    def test_the_prompt_paragraphs_point_to_the_turn_language_line(self):
        ar, en = make_agent("ar").instructions, make_agent("en").instructions
        self.assertNotIn(HK12_AR_PARAGRAPH, ar)
        self.assertNotIn(HK12_EN_PARAGRAPH, en)
        for text in (ar, en):
            block = text[text.index("\n\nLANGUAGE:"):]
            self.assertIn("TURN LANGUAGE", block)
            self.assertIn("microphone noise", block)
            self.assertEqual(text.count("\n\nLANGUAGE:"), 1)
        en_block = en[en.index("\n\nLANGUAGE:"):]
        # the English paragraph no longer forbids the switch the TURN LANGUAGE line asks for
        self.assertNotIn("Always reply in English", en_block)
        self.assertNotIn("never the Arabic one", en_block)
        # the static prompt (identity and maker lines) is hk/12's: only the LANGUAGE paragraph moved
        with follows_child(False):
            off = make_agent("en").instructions
        self.assertEqual(off[:off.index("\n\nLANGUAGE:")], en[:en.index("\n\nLANGUAGE:")])
        self.assertIn(MAKER_LINE_EN, en)
        self.assertEqual(build_instructions(language="en", follows_child=True), en)

    def test_the_tts_hint_follows_the_reply_language(self):
        a, tts = make_agent("ar"), FakeTTS("ar")
        with with_tts(a, tts):
            a._prepare(AR_SENTENCE)
            a._prepare("hello")                                      # one word: no switch
            a._prepare(chr(0x4F60) + chr(0x597D) + " " + chr(0x8C22))    # noise: no switch
            self.assertEqual(tts.calls, [])
            a._prepare(EN_SENTENCE, typed=True)
            a._prepare("and the sun too please", typed=True)
            a._prepare(AR_SENTENCE)
        self.assertEqual(tts.calls, [{"language": "en"}, {"language": "ar"}])    # the voice id is never swapped

    def test_a_tts_hint_that_is_not_ar_or_en_is_left_alone(self):
        for current in ("", "auto", "fr"):
            a, tts = make_agent("ar"), FakeTTS(current)
            with with_tts(a, tts):
                a._prepare(EN_SENTENCE, typed=True)
            self.assertEqual(tts.calls, [], current)

    def test_a_tts_that_cannot_update_or_fails_never_breaks_the_turn(self):
        a = make_agent("ar")
        with with_tts(a, SimpleNamespace(_opts=SimpleNamespace(language="ar"))):
            self.assertEqual(a._prepare(EN_SENTENCE, typed=True), language_line("en"))
        broken = FakeTTS("ar")
        broken.update_options = mock.Mock(side_effect=RuntimeError("boom"))
        b = make_agent("ar")
        with with_tts(b, broken):
            self.assertEqual(b._prepare(EN_SENTENCE, typed=True), language_line("en"))

    def test_the_speech_cleaner_and_the_decline_follow_the_reply_language(self):
        from conversation.agent.scripture_guard import DECLINE_TEXT

        a = make_agent("ar")
        a._prepare(EN_SENTENCE, typed=True)
        self.assertIn("three", spoken_numbers(lambda: a.speech_language))
        out = speak(a, "Nice day. The Prophet said to always be kind.")
        self.assertIn(DECLINE_TEXT["en"].split(".")[0], out)
        self.assertNotIn(DECLINE_TEXT["ar"].split(".")[0], out)
        b = make_agent("en")
        b._prepare(AR_SENTENCE, typed=True)
        self.assertIn(DECLINE_TEXT["ar"].split(".")[0], speak(b, "Nice day. The Prophet said to always be kind."))

    def test_the_fixed_fallback_line_follows_the_reply_language(self):
        a = make_agent("en")
        a._prepare(AR_SENTENCE, typed=True)
        self.assertEqual(fallback_language(a, "ok"), "ar")         # "ok" keeps the Arabic reply
        b = make_agent("ar")
        b._prepare("hello")
        self.assertEqual(fallback_language(b, "hello"), "ar")      # one word did not switch

    def test_changing_the_session_language_restarts_the_reply_language(self):
        a = make_agent("en")
        a._prepare(AR_SENTENCE, typed=True)
        a.language = "en"
        self.assertEqual(a.reply_language, "en")
        a.language = "ar"
        self.assertEqual(a.reply_language, "ar")
        a.language = "en-US"                                         # region suffixes are fine
        self.assertEqual(a.reply_language, "en")
