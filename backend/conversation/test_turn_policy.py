"""Tests for the turn guard: safety, REFER and creed decisions, retrieval, scripture guard.

No scripture anywhere in here: every bank text is an obvious placeholder and the
Quranic marks used by the TTS filter tests sit on made-up words.
"""
import asyncio
from types import SimpleNamespace

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase

from conversation.agent import scripture_guard as sg
from conversation.agent import turn_guard as tg
from conversation.agent.retrieval import (
    ValueIndex, build_value_index, card_payload, format_sources_block, match_values,
)
from conversation.agent.surah_names import SURAH_AR, SURAH_EN
from conversation.agent.turn_pipeline import age_band_from_birth_year
from session_moral_context.models import ContentItem, Value, ValueItem

User = get_user_model()

_ITEM_DEFAULTS = dict(
    arabic_text="", english_text="", translation_name="", translation_source_url="",
    child_explanation_ar="", child_explanation_en="", child_explanation_older_ar="",
    child_explanation_older_en="", disagreement_note_ar="", disagreement_note_en="",
    title_ar="", title_en="", keywords_ar=[], keywords_en=[], surah=None, ayah=None,
    audio_url="", book="", number="", narrator="", grade="", grader="", source_site="",
    source_url="", verification_status="reviewed", age_band="all", content_level="",
)


def item(pk, type_="verse", **kw):
    d = dict(_ITEM_DEFAULTS)
    d.update(kw)
    return SimpleNamespace(pk=pk, type=type_, **d)


def value(slug, kw_en=(), kw_ar=(), order=0):
    return SimpleNamespace(slug=slug, name_en=slug.title(), name_ar="قيمة " + slug,
                           keywords_en=list(kw_en), keywords_ar=list(kw_ar), order=order)


async def drain_guard_tasks(agent, max_rounds: int = 50) -> None:
    """Wait for the agent's guard tasks, including the ones they spawn.

    ``await`` on an already finished task does not yield to the loop, so a finished task whose
    discard callback has not run yet would keep ``agent._guard_tasks`` non-empty forever: sleep
    once per round so the callbacks run (review of #87: intermittent hang)."""
    for _ in range(max_rounds):
        tasks = list(agent._guard_tasks)
        if not tasks:
            return
        await asyncio.gather(*tasks)
        await asyncio.sleep(0)
    raise AssertionError("guard tasks did not finish")


def synthetic_index():
    """A tiny bank of placeholders shaped like the 12 test questions' needs."""
    values = [
        value("honesty", ["lie", "lying", "honest", "truth"], ["كذب", "الكذب", "صدق"], 1),
        value("cleanliness", ["clean", "cleanliness"], ["نظافة", "النظافة"], 2),
    ]
    items = [
        item(1, "verse", surah=49, ayah=12, arabic_text="نص تجريبي 1", english_text="PLACEHOLDER TEXT 1",
             translation_name="Placeholder translation", child_explanation_en="Explain 1",
             child_explanation_ar="شرح 1", verification_status="seeded"),
        item(2, "hadith", book="Placeholder book", number="1", grade="صحيح", grader="مسلم",
             arabic_text="نص تجريبي 2", child_explanation_en="Explain 2", content_level="A"),
        item(3, "verse", surah=9, ayah=108, arabic_text="نص تجريبي 3", english_text="PLACEHOLDER TEXT 3",
             translation_name="Placeholder translation", verification_status="reviewed"),
        item(4, "faq", title_en="Is the Kaaba a god", arabic_text="نص تجريبي 4",
             keywords_en=["kaaba", "qiblah"], keywords_ar=["الكعبة", "القبلة"],
             child_explanation_en="Explain 4", child_explanation_ar="شرح 4", content_level="B"),
        item(5, "fiqh", title_en="Do all pray the same", arabic_text="نص تجريبي 5",
             keywords_en=["pray the same"], keywords_ar=["نفس الطريقة"],
             disagreement_note_en="Everyone prays five times; details differ.", content_level="C"),
        item(6, "faq", title_en="Older child only", arabic_text="نص تجريبي 6",
             keywords_en=["sword"], age_band="10-13", content_level="B"),
        item(7, "term", title_en="Tawhid", arabic_text="نص تجريبي 7", english_text="PLACEHOLDER 7",
             translation_name="Placeholder dictionary", keywords_en=["tawhid"], keywords_ar=["التوحيد"]),
    ]
    links = [("honesty", 1, 0), ("honesty", 2, 1), ("cleanliness", 3, 0)]
    return ValueIndex.from_records(values, items, links)


class ClassificationTests(SimpleTestCase):
    """What the guard catches before the model (safety, personal rulings, creed), Arabic and English.
    Everything else passes untouched: how the model answers it is judged in the LLM eval."""

    def refer(self, text):
        hit = tg.check(text)
        self.assertIsNotNone(hit, text)
        self.assertEqual(hit.kind, tg.REFER, text)
        return hit.level


    def test_q4_scholars_differ_is_level_c(self):
        for t in [
            "My mom asked two sheikhs and got two different answers. Why do scholars say different things?",
            "ماما سألت شيخين وجاوباها جوابين مختلفين، ليش العلماء يختلفون؟",
        ]:
            self.assertEqual(self.refer(t), "C", t)

    def test_q5_personal_case_is_level_d_on_both_languages(self):
        for t in [
            "I forgot and drank water while fasting. Does my fast still count?",
            "نسيت وشربت ماء وأنا صايم، صيامي صحيح؟",
            "My dad works at a bank. Is our family's money haram?",
            "بابا يشتغل في بنك، فلوسنا حرام؟",
        ]:
            self.assertEqual(self.refer(t), "D", t)


    def test_q10_do_all_muslims_agree_is_level_c(self):
        for t in [
            "Do all Muslims pray exactly the same way? My cousin prays a bit differently.",
            "كل المسلمين يصلون بنفس الطريقة بالضبط؟ ابن عمي يصلي بشكل مختلف.",
        ]:
            self.assertEqual(self.refer(t), "C", t)


    def test_dialect_haram_alaik_is_not_a_personal_ruling(self):
        self.assertIsNone(tg.check("ليش أمي قالت لي: حرام عليك؟"))

    def test_safety_beats_everything(self):
        for t, flag in [
            ("My parents are fighting all the time", "sensitive"),
            ("ماما وبابا يتخانقون وايد", "sensitive"),
            ("my dad hits me", "harmful"),
            ("I'm scared to go home", "sensitive"),
            ("I want to hurt myself", "harmful"),
            ("My parents are fighting about divorce, can Mom pray at home? Is that haram for us?", "sensitive"),
        ]:
            hit = tg.check(t)
            self.assertEqual((hit.kind, hit.level, hit.flag_type), (tg.SAFETY, "D", flag), t)

    def test_safety_instruction_never_routes_to_parents(self):
        for t in ("my dad hits me", "I want to hurt myself", "a man online asked me for photos"):
            self.assertIn("trusted adult or a teacher", tg.check(t).note, t)
        self.assertNotIn("parent", tg._SAFETY_NOTE.lower())

    def test_plain_chat_is_untouched(self):
        for t in ["I want to play football", "I can count to ten", "What is divorce?",
                  "why shouldn't I lie?", "ليش الكذب حرام؟", "tell me the story of Prophet Musa"]:
            self.assertIsNone(tg.check(t), t)

    def test_empty_text(self):
        self.assertIsNone(tg.check(""))


    def test_check_is_fast(self):
        import time
        t = time.perf_counter()
        for _ in range(50):
            tg.check("My mom asked two sheikhs and got two different answers, why do scholars differ "
                     "and is lying a sin for my family?")
        self.assertLess((time.perf_counter() - t) / 50, 0.010)


class RetrievalTests(SimpleTestCase):
    def test_arabic_with_and_without_diacritics_and_clitics(self):
        idx = synthetic_index()
        for text in ["الكذب", "ال\u0652ك\u064eذ\u0650ب\u064f", "بالكذب", "كذب"]:
            self.assertTrue(match_values(text, "ar", None, idx), text)

    def test_english_and_no_match(self):
        idx = synthetic_index()
        self.assertTrue(match_values("I told a lie", "en", None, idx))
        self.assertEqual(match_values("I like football", "en", None, idx), [])
        self.assertEqual(match_values("", "en", None, idx), [])
        self.assertEqual(match_values("lie", "en", None, None), [])

    def test_top_items_prefer_reviewed_then_verse_hadith_and_cap_at_three(self):
        values = [value("v", ["kind"])]
        items = [
            item(1, "faq", verification_status="reviewed", arabic_text="x"),
            item(2, "verse", verification_status="seeded", arabic_text="x"),
            item(3, "hadith", verification_status="reviewed", arabic_text="x"),
            item(4, "verse", verification_status="reviewed", arabic_text="x"),
        ]
        idx = ValueIndex.from_records(values, items, [("v", i.pk, 0) for i in items])
        got = [i.pk for i in match_values("be kind", "en", None, idx)]
        self.assertEqual(got, [4, 3, 1])  # reviewed first, then verse/hadith

    def test_age_band_preference_and_exclusion(self):
        values = [value("v", ["kind"])]
        items = [
            item(1, "verse", age_band="10-13", arabic_text="x"),
            item(2, "verse", age_band="6-9", arabic_text="x"),
            item(3, "verse", age_band="all", arabic_text="x"),
        ]
        idx = ValueIndex.from_records(values, items, [("v", i.pk, 0) for i in items])
        self.assertEqual([i.pk for i in match_values("kind", "en", "6-9", idx)], [2, 3])
        self.assertEqual([i.pk for i in match_values("kind", "en", "10-13", idx)][0], 1)

    def test_at_most_two_values(self):
        values = [value("a", ["alpha"]), value("b", ["beta"]), value("c", ["gamma"])]
        items = [item(i, "verse", arabic_text="x") for i in (1, 2, 3)]
        idx = ValueIndex.from_records(values, items, [("a", 1, 0), ("b", 2, 0), ("c", 3, 0)])
        got = {i.pk for i in match_values("alpha beta gamma", "en", None, idx)}
        self.assertEqual(len(got), 2)

    def test_fast_on_a_large_bank(self):
        import time
        values = [value(f"v{n}", [f"word{n}", f"phrase number {n}"]) for n in range(40)]
        items = [item(n, "verse", arabic_text="x", keywords_en=[f"kw{n}"]) for n in range(1, 600)]
        links = [(f"v{n % 40}", n, n) for n in range(1, 600)]
        idx = ValueIndex.from_records(values, items, links)
        t = time.perf_counter()
        for _ in range(20):
            match_values("please tell me about word3 and kw77 and phrase number 9 today", "en", None, idx)
        self.assertLess((time.perf_counter() - t) / 20, 0.010)

    def test_surah_name_tables_are_complete(self):
        self.assertEqual((len(SURAH_EN), len(SURAH_AR)), (114, 114))


class SourcesBlockTests(SimpleTestCase):
    def test_no_arabic_verse_text_in_llm_context(self):
        idx = synthetic_index()
        items = [i for i in idx.items.values()][:3]
        objs = [i.obj for i in items]
        for lang in ("en", "ar"):
            block = format_sources_block(objs, lang, None)
            self.assertIn("VERIFIED SOURCES", block)
            self.assertNotIn("نص تجريبي 1", block)  # verse arabic never goes to the LLM
            self.assertNotIn("نص تجريبي 3", block)
        self.assertIn("PLACEHOLDER TEXT 1", format_sources_block(objs, "en", None))
        self.assertIn("Surah Al-Hujurat (49:12)", format_sources_block(objs, "en", None))
        self.assertIn("سورة الحجرات (49:12)", format_sources_block(objs, "ar", None))

    def test_hadith_arabic_allowed_for_arabic_session_and_explanation_labelled(self):
        h = item(2, "hadith", book="B", number="1", grade="صحيح", grader="مسلم",
                 arabic_text="نص تجريبي 2", child_explanation_en="Explain 2")
        self.assertIn("نص تجريبي 2", format_sources_block([h], "ar", None))
        self.assertIn("ours, not the source's words", format_sources_block([h], "en", None))
        self.assertIn("graded sahih", format_sources_block([h], "en", None))

    def test_block_strips_quranic_marks_from_non_verse_text(self):
        f = item(9, "faq", arabic_text="نص\u06d6 تجريبي\u06d7 \ufd3f داخل القوس \ufd3e بعد", title_en="t")
        block = format_sources_block([f], "ar", None)
        self.assertNotIn("داخل القوس", block)

    def test_source_excerpts_stay_on_the_card_but_citation_and_explanation_reach_the_llm(self):
        for t in ("tafsir", "sirah", "aqidah", "fiqh", "faq"):
            it = item(20, t, arabic_text=f"مقتطف مصدر تجريبي {t}", english_text=f"SOURCE EXCERPT {t}",
                      translation_name="T", title_ar=f"عنوان {t}", title_en=f"Title {t}",
                      book=f"Book {t}", child_explanation_ar=f"شرح مبسط {t}",
                      child_explanation_en=f"Simple {t}")
            for lang, excerpt, cite, expl in (("ar", f"مقتطف مصدر تجريبي {t}", f"عنوان {t} (Book {t})", f"شرح مبسط {t}"),
                                              ("en", f"SOURCE EXCERPT {t}", f"Title {t} (Book {t})", f"Simple {t}")):
                block = format_sources_block([it], lang, None)
                self.assertNotIn(excerpt, block, (t, lang))
                self.assertIn(cite, block, (t, lang))
                self.assertIn(expl, block, (t, lang))
                self.assertIn("ours, not the source's words", block)
            self.assertEqual(card_payload(it, "ar")["arabic_text"], f"مقتطف مصدر تجريبي {t}")  # card keeps it

    def test_term_definition_still_reaches_the_llm(self):
        t = item(21, "term", arabic_text="تعريف مختصر تجريبي", english_text="SHORT DEFINITION",
                 translation_name="T", title_en="Term")
        self.assertIn("تعريف مختصر تجريبي", format_sources_block([t], "ar", None))
        self.assertIn("SHORT DEFINITION", format_sources_block([t], "en", None))

    def test_recitation_credit_names_reciter_and_links_everyayah(self):
        url = "https://everyayah.com/data/Husary_128kbps/049012.mp3"
        v = item(1, "verse", surah=49, ayah=12, arabic_text="x", audio_url=url)
        en, ar = card_payload(v, "en"), card_payload(v, "ar")
        self.assertEqual(en["audio_credit"], "Recitation: Mahmoud Khalil Al-Husary, everyayah.com")
        self.assertEqual(ar["audio_credit"], "التلاوة: محمود خليل الحصري، everyayah.com")
        self.assertEqual(en["audio_source_url"], "https://everyayah.com/")
        no_audio = card_payload(item(2, "hadith", arabic_text="x"), "en")
        self.assertEqual((no_audio["audio_credit"], no_audio["audio_source_url"]), ("", ""))

    def test_hadith_card_carries_both_source_links(self):
        h = item(2, "hadith", arabic_text="x", source_url="https://dorar.net/h/PLACEHOLDER",
                 english_text="PLACEHOLDER", translation_name="HadeethEnc.com",
                 translation_source_url="https://hadeethenc.com/en/browse/hadith/0")
        c = card_payload(h, "en")
        self.assertEqual(c["source_url"], "https://dorar.net/h/PLACEHOLDER")
        self.assertEqual(c["translation_source_url"], "https://hadeethenc.com/en/browse/hadith/0")

    def test_card_payload_contract(self):
        idx = synthetic_index()
        payload = card_payload(idx.items[1].obj, "en", "10-13", idx)
        self.assertEqual(set(payload), {
            "id", "type", "kind", "arabic_text", "english_text", "translation_name",
            "translation_source_url", "surah", "ayah", "surah_name", "audio_url",
            "audio_credit", "audio_source_url", "book", "number", "grade", "grader", "source_site", "source_url",
            "content_level", "value", "title", "explanation", "explanation_lang",
            "explanation_origin", "disagreement_note", "verification_status", "verse_refs", "segments"})
        self.assertEqual(payload["kind"], "scripture")
        self.assertEqual(payload["arabic_text"], "نص تجريبي 1")  # the card does carry it
        self.assertEqual(payload["value"], "Honesty")
        self.assertEqual(payload["explanation"], "Explain 1")
        self.assertEqual(payload["explanation_origin"], "generated")
        faq = card_payload(idx.items[5].obj, "en", None, idx)
        self.assertEqual(faq["kind"], "source_excerpt")
        self.assertEqual(faq["disagreement_note"], "Everyone prays five times; details differ.")
        self.assertEqual(faq["title"], "Do all pray the same")

    def test_english_text_needs_translation_name(self):
        i = item(1, "verse", english_text="E", translation_name="", arabic_text="x")
        self.assertEqual(card_payload(i, "en")["english_text"], "")


class BuildIndexDbTests(TestCase):
    def setUp(self):
        self.v = Value.objects.create(slug="honesty", name_en="Honesty", name_ar="الصدق",
                                      keywords_en=["lie"], keywords_ar=["كذب"])
        mk = lambda **kw: ContentItem.objects.create(**kw)  # noqa: E731
        self.seeded = mk(type="verse", surah=49, ayah=12, arabic_text="نص تجريبي",
                         english_text="PLACEHOLDER", translation_name="T", verification_status="seeded")
        self.unverified = mk(type="verse", surah=49, ayah=13, arabic_text="نص تجريبي",
                             verification_status="unverified")
        self.hadith_ok = mk(type="hadith", book="b", number="1", grade="صحيح", grader="g",
                            arabic_text="نص تجريبي", verification_status="reviewed")
        self.hadith_seeded = mk(type="hadith", book="b", number="2", grade="صحيح", grader="g",
                                arabic_text="نص تجريبي", verification_status="seeded")
        self.hadith_weak = mk(type="hadith", book="b", number="3", grade="ضعيف", grader="g",
                              arabic_text="نص تجريبي", verification_status="reviewed")
        for n, it in enumerate([self.seeded, self.unverified, self.hadith_ok,
                                self.hadith_seeded, self.hadith_weak]):
            ValueItem.objects.create(value=self.v, item=it, order=n)

    def test_only_servable_items_are_indexed_and_matched(self):
        idx = build_value_index()
        self.assertEqual(set(idx.items), {self.seeded.pk, self.hadith_ok.pk})
        got = {i.pk for i in match_values("why not lie", "en", None, idx)}
        self.assertEqual(got, {self.seeded.pk, self.hadith_ok.pk})
        self.assertEqual(idx.value_names("ar"), ["الصدق"])


def run(coro):
    return asyncio.run(coro)


async def agen(chunks):
    for c in chunks:
        yield c


async def collect(stream):
    return [c async for c in stream]


class ScriptureFilterTests(SimpleTestCase):
    SPAN = "\ufd3f" + "كلمة مصطنعة" + "\ufd3e"
    DENSE = "نص\u06d6 تجريبي\u06d7 آخر\u06d8"

    def test_ornate_span_removed(self):
        self.assertEqual(sg.strip_scripture(f"before {self.SPAN} after").split(), ["before", "after"])

    def test_dense_mark_run_removed_normal_arabic_kept(self):
        out = sg.strip_scripture(f"مرحبا يا صديقي {self.DENSE} كيف حالك")
        self.assertEqual(out.split(), ["مرحبا", "يا", "صديقي", "كيف", "حالك"])

    def test_single_marked_word_alone_is_kept(self):
        self.assertEqual(sg.strip_scripture("مرحبا نص\u0670 صديقي").split(), ["مرحبا", "نص\u0670", "صديقي"])

    def test_stream_across_chunk_boundaries(self):
        text = f"hello {self.SPAN} world {self.DENSE} bye"
        for size in (1, 3, 7, 100):
            chunks = [text[i:i + size] for i in range(0, len(text), size)]
            out = "".join(run(collect(sg.filter_scripture_stream(agen(chunks)))))
            self.assertEqual(out.split(), ["hello", "world", "bye"], size)

    def test_agent_tts_node_pipeline_is_wired(self):
        from conversation.agent.agent_class import AlSadiqAgent
        a = AlSadiqAgent(db_session_id=1, child_id=1)
        out = "".join(run(collect(a.guard_speech(agen([f"ok {self.SPAN} fine"])))))
        self.assertEqual(out.split(), ["ok", "fine"])


class AttributionGuardTests(SimpleTestCase):
    def guard(self, chunks, served=False, lang="en"):
        return "".join(run(collect(sg.guard_attribution_stream(agen(chunks), lambda: served, lang))))

    def split(self, text, size):
        return [text[i:i + size] for i in range(0, len(text), size)]

    def test_unsourced_attribution_is_replaced_by_decline(self):
        for text in [
            "Great question! The Prophet said PLACEHOLDER SAYING ONE.",
            "Remember, Allah says PLACEHOLDER SAYING TWO.",
            "The Prophet taught us PLACEHOLDER SAYING THREE.",
        ]:
            for size in (2, 5, 200):
                out = self.guard(self.split(text, size))
                self.assertIn(sg.DECLINE_TEXT["en"], out, (text, size))
                self.assertNotIn("PLACEHOLDER", out)

    def test_arabic_attribution_replaced_by_arabic_decline(self):
        for text in ["جميل! قال رسول الله كذا وكذا.", "قال النبي \ufdfa كذا", "ق\u064eال\u064e الله\u064f ت\u064eع\u064eال\u064eى كذا"]:
            for size in (2, 4, 200):
                out = self.guard(self.split(text, size), lang="ar")
                self.assertIn(sg.DECLINE_TEXT["ar"], out, (text, size))

    def test_sourced_turn_passes_through(self):
        text = "In simple words, the hadith on your screen means PLACEHOLDER. The Prophet said PLACEHOLDER."
        self.assertEqual(self.guard(self.split(text, 4), served=True), text)

    def test_normal_reply_is_unchanged_and_streams_early(self):
        text = "Oh nice, that sounds like a kind thing to do. Tell me more about it."
        self.assertEqual(self.guard(self.split(text, 3)), text)

        async def first_chunk():
            gen = sg.guard_attribution_stream(agen(self.split(text, 3)), lambda: False)
            return await gen.__anext__()
        self.assertTrue(run(first_chunk()))

    def test_counter_increments(self):
        before = sg.STATS["attribution_blocked"]
        self.guard(["The Prophet said hello"])
        self.assertEqual(sg.STATS["attribution_blocked"], before + 1)


class AgeBandTests(SimpleTestCase):
    def test_age_band_from_birth_year(self):
        from datetime import date
        d = date(2026, 10, 5)
        self.assertEqual(age_band_from_birth_year(2019, d), "6-9")
        self.assertEqual(age_band_from_birth_year(2016, d), "10-13")
        self.assertEqual(age_band_from_birth_year(2010, d), "10-13")
        self.assertIsNone(age_band_from_birth_year(None, d))
