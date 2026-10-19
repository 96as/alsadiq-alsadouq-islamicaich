"""Round 3 tests for the turn guard: the LLM safety tool, the distress veto, level D
verbs, fabrication requests, the companion rule, retrieval synonyms and the attribution
gate per item type. Every religious sentence here is a PLACEHOLDER."""
import asyncio
import re
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from types import SimpleNamespace

from asgiref.sync import async_to_sync
from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase

from authentication.models import ChildProfile, ParentChildLink, ParentProfile
from content_safety.models import NEUTRAL_ALERT_DESCRIPTION, NO_PARENT_NOTIFY_PREFIX, Alert, SafetyFlag
from conversation.agent import scripture_guard as sg
from conversation.agent import turn_guard as tg
from conversation.agent import turn_pipeline
from conversation.agent.text_match import forms
from conversation.models import Message, Session
from conversation.test_turn_policy import drain_guard_tasks, item, synthetic_index

User = get_user_model()


def run(coro):
    return asyncio.run(coro)


async def agen(chunks):
    for c in chunks:
        yield c


async def collect(stream):
    return "".join([c async for c in stream])


def prep(text, lang="en"):
    """The guard's decision for one turn: a GuardHit or None."""
    return tg.check(text)


def is_safety(text):
    h = tg.check(text)
    return bool(h and h.kind == tg.SAFETY)


# ----------------------------------------------------------------- 1. the LLM tool


class LlmFlagToolTests(TestCase):
    """flag_safety_concern: the LLM's words never reach a parent (neutral alert text only). Every model flag
    but off_topic alerts a parent once a session, family cases included (hk/12g, lead decision)."""

    def setUp(self):
        from conversation.agent.agent_class import AlSadiqAgent
        self.parent_user = User.objects.create_user(username="par3", password="x")
        self.parent = ParentProfile.objects.create(user=self.parent_user, name="P")
        self.user = User.objects.create_user(username="kid3", password="x", is_child=True)
        self.child = ChildProfile.objects.create(user=self.user, nickname="K", gender="male", birth_year=2015)
        ParentChildLink.objects.create(parent=self.parent, child=self.child, consent_status="approved")
        self.session = Session.objects.create(child=self.child, livekit_room_name="room-tool")
        self.msg = Message.objects.create(session=self.session, sender="child", content="x", input_type="voice")
        self.agent = AlSadiqAgent(db_session_id=self.session.pk, child_id=self.child.pk,
                                  language="en", value_index=synthetic_index())
        self.agent._last_child_message_id = self.msg.pk

    def call(self, flag_type, text="LLM WORDING about the dad", at_home=False):
        async def go():
            return await self.agent.flag_safety_concern(flag_type, text, at_home)
        return async_to_sync(go)()

    def test_flags_about_someone_at_home_alert_the_parent_once(self):
        for ft in ("harmful", "sensitive", "off_topic", "something_unknown"):
            self.call(ft, at_home=True)
        self.assertEqual(Alert.objects.get().description, NEUTRAL_ALERT_DESCRIPTION)
        self.assertEqual(SafetyFlag.objects.filter(message=self.msg).count(), 4)
        self.assertFalse(any(f.description.startswith(NO_PARENT_NOTIFY_PREFIX) for f in SafetyFlag.objects.all()))

    def test_other_model_flags_alert_once_with_the_neutral_text_never_the_llm_text(self):
        self.call("harmful", "LLM WORDING: a man online wants photos")
        self.call("sensitive", "LLM WORDING: again")
        alert = Alert.objects.get()
        self.assertEqual(alert.description, NEUTRAL_ALERT_DESCRIPTION)
        self.assertNotIn("LLM WORDING", alert.description)
        self.assertEqual(SafetyFlag.objects.filter(message=self.msg).count(), 2)

    def test_inappropriate_alerts_with_the_neutral_text_never_the_llm_text(self):
        self.call("inappropriate", "LLM WORDING: the child said a secret thing")
        alert = Alert.objects.get()
        self.assertEqual(alert.description, NEUTRAL_ALERT_DESCRIPTION)
        self.assertNotIn("LLM WORDING", alert.description)
        flag = SafetyFlag.objects.get()
        self.assertFalse(flag.description.startswith(NO_PARENT_NOTIFY_PREFIX))

    def test_prompt_tells_the_model_to_set_at_home(self):
        # (hk/12 reversed the old "no family abuse example in the prompt" rule: the lead's flag text names
        # family harm so the model flags it. Since hk/12g at_home no longer changes who is alerted.)
        text = self.agent.instructions.lower()
        self.assertIn("flag_safety_concern", text)
        self.assertIn("set at_home to true", text)


class ParentAlertSessionTests(SimpleTestCase):
    """hk/12g: a family rule alerts the parent and never silences later rules in the session."""

    def run_turns(self, texts):
        from conversation.agent.agent_class import AlSadiqAgent
        agent = AlSadiqAgent(db_session_id=1, child_id=1, language="en", value_index=synthetic_index())
        agent._last_child_message_id = 1
        flag = AsyncMock(return_value="ok")

        async def go():
            with patch("conversation.agent.turn_pipeline._write_turn_records", new=AsyncMock()), \
                    patch.object(turn_pipeline, "_FLAG_WAIT_SECONDS", 0.5), \
                    patch("conversation.agent.agent_class._create_safety_flag_and_alert", new=flag):
                for i, text in enumerate(texts, start=2):
                    await agent.on_user_turn_completed(MagicMock(), SimpleNamespace(text_content=text))
                    agent._last_child_message_id = i
                    await drain_guard_tasks(agent)
        run(go())
        return flag.await_args_list

    def test_a_family_rule_then_bullying_then_self_harm_each_alert_the_parent(self):
        calls = self.run_turns(["my dad hits me", "the kids at school hit me every day", "i want to hurt myself"])
        self.assertEqual(len(calls), 3)
        for c in calls:
            self.assertTrue(c.kwargs["notify_parents"])
            self.assertFalse(c.kwargs["description"].startswith(NO_PARENT_NOTIFY_PREFIX))
            self.assertEqual(c.kwargs["alert_description"], NEUTRAL_ALERT_DESCRIPTION)

    def test_before_any_family_rule_a_parent_rule_still_alerts_once(self):
        calls = self.run_turns(["the kids at school hit me every day", "the kids at school hit me again"])
        self.assertEqual([c.kwargs["notify_parents"] for c in calls], [True, False])
        self.assertFalse(calls[0].kwargs["description"].startswith(NO_PARENT_NOTIFY_PREFIX))


# ------------------------------------------------------------- 2. safety rule coverage


class SafetyRuleCoverageTests(SimpleTestCase):


    def test_self_harm_phrases_all_dialects(self):
        for text, lang in [
            ("موت حالي", "ar"), ("ودي اموت", "ar"), ("بدي اموت", "ar"), ("ابغى اموت", "ar"),
            ("ابغى اختفي من الدنيا", "ar"), ("ما ابي اعيش بعد اليوم", "ar"), ("بدي اقتل حالي", "ar"),
            ("مش عايز اعيش", "ar"), ("تعبت من حياتي", "ar"),
            ("i want to disappear forever", "en"), ("i dont want to be alive anymore", "en"),
            ("i keep thinking about hurting myself", "en"), ("i think everyone would be better off if i was gone", "en"),
        ]:
            p = prep(text)
            self.assertEqual((p.kind, p.flag_type, p.notify_parent), (tg.SAFETY, "harmful", True), text)

    def test_self_harm_false_positives(self):
        for text in ("my mom will kill me if i break the vase", "i cut myself on a piece of paper",
                     "i hurt myself playing football today"):
            self.assertFalse(is_safety(text), text)

    def test_grooming_photos_secret_and_meeting(self):
        for text, lang, rule in [
            ("a boy online asked me to send him photos and keep it secret", "en", None),
            ("a stranger online said send me your photo and dont tell your mom", "en", None),
            ("someone i met in a game wants me to meet him and not tell my parents", "en", "grooming_meet"),
            ("someone online wants me to come to his house and said its our secret", "en", None),
            ("واحد في اللعبة قال لي ارسل صورتك ولا تقول لاحد", "ar", None),
            ("شخص غريب في اللعبة طلب مني صور وقال لا تقول لامك", "ar", None),
        ]:
            p = prep(text)
            self.assertEqual((p.kind, p.flag_type), (tg.SAFETY, "harmful"), text)
            self.assertTrue(p.notify_parent, text)
            if rule:
                self.assertEqual(p.rule_id, rule)

    def test_family_grooming_and_neglect_use_the_family_rules(self):
        # notify_parent=false now only picks the rule (its home-harm reply); the parent is alerted (hk/12g)
        for text, lang in [
            ("my uncle makes me sit on his lap and tells me not to tell anyone", "en"),
            ("my uncle told me to keep a secret and i dont like it", "en"),
            ("my older cousin touches me and says its our secret", "en"),
            ("my uncle kisses me on the lips and tells me not to tell", "en"),
            ("nobody feeds me at home my parents leave me alone for days", "en"),
            ("عمي يقلي اقلع ملابسي ويقول لا تخبر احد", "ar"),
            ("عمي بيقلي ما تحكي لحدا وبيلمسني", "ar"),
            ("امي وابوي بيتطلقوا وانا حزين وخايف", "ar"),
        ]:
            p = prep(text)
            self.assertEqual(p.kind, tg.SAFETY, text)
            self.assertFalse(p.notify_parent, text)

    def test_a_no_parent_rule_wins_when_several_rules_fire(self):
        # hitting_at_home (notify_parent=false) and bullying both match: the family rule wins (its reply)
        p = prep("my dad hits me and the kids at school hit me too")
        self.assertEqual(p.kind, tg.SAFETY)
        self.assertFalse(p.notify_parent)
        # self harm plus violence at home
        p = prep("i want to die and my dad hits my mom")
        self.assertFalse(p.notify_parent)

    def test_bullying_and_the_school_boy_phrasing(self):
        for text, lang in [
            ("في ولد بالمدرسة يضربني", "ar"), ("في ولد بالمدرسة كل يوم يضربني وياخذ مصروفي", "ar"),
            ("يضربني ولد كبير في الباص كل يوم", "ar"), ("في بنت بالمدرسة تضربني كل يوم", "ar"),
            ("the older kids at school keep hitting me and taking my snacks", "en"),
            ("boys at school keep calling me names and pushing me", "en"),
            ("a boy in my class bullies me every day", "en"),
        ]:
            p = prep(text)
            self.assertEqual((p.kind, p.rule_id, p.notify_parent), (tg.SAFETY, "bullying", True), text)

    def test_harmless_sentences_are_not_safety(self):
        for text, lang in [
            ("my cousin showed me a secret handshake and said dont tell anyone", "en"),
            ("my uncle bought me a gift and said dont tell mom its a surprise", "en"),
            ("my teacher took photos of our class trip", "en"),
            ("my dad filmed a video of me playing football", "en"),
            ("the ball hit me on the leg", "en"),
            ("my mom locked the car with me inside by accident lol", "en"),
            ("my mom told me to keep it secret that we bought dad a birthday present", "en"),
            ("ابوي يغلبني بالشطرنج كل مرة", "ar"),
            ("صورت قطتنا بالجوال", "ar"),
            ("ابوي وامي راحوا السوق", "ar"),
        ]:
            self.assertFalse(is_safety(text), text)


# --------------------------------------------------------------- 3. level D and C


class LevelDVerbTests(SimpleTestCase):
    def test_break_and_validity_verbs_with_worship_objects(self):
        for text, lang in [
            ("اذا نسيت وشربت مي وانا صايم بيخرب صيامي", "ar"),
            ("هل بيخرب صيامي اذا بلعت ريقي", "ar"),
            ("لو ضحكت بالصلاة بتبطل صلاتي", "ar"),
            ("اذا اكلت ناسي وانا صايم ينفع صيامي", "ar"),
            ("وضوئي صحيح اذا لمست القطة", "ar"),
            ("صيامي يبطل اذا شميت ريحة اكل", "ar"),
            ("هل يصح اصلي وانا جالس", "ar"),
            ("لازم اتوضى من جديد اذا لمست كلبنا", "ar"),
            ("does it break my fast if i swallow water while brushing my teeth", "en"),
            ("if i laugh in prayer do i have to pray again", "en"),
            ("can i skip fajr if i am very tired", "en"),
            ("is it a sin if i forgot to pray isha", "en"),
        ]:
            p = prep(text)
            self.assertEqual((p.kind, p.level), (tg.REFER, "D"), text)

    def test_judging_a_persons_fate_is_d(self):
        for text, lang in [
            ("my auntie doesnt wear hijab is she going to hell", "en"),
            ("is my dad going to hell because he doesnt pray", "en"),
            ("will my grandma go to heaven even though she skips prayers", "en"),
            ("is my uncle a kafir because he drinks", "en"),
            ("is my teacher going to hell", "en"),
            ("هل جدي بيدخل النار لانه ما يصلي", "ar"),
            ("عمتي ما تلبس الحجاب هل راح تدخل جهنم", "ar"),
            ("جارنا ما يصلي هل هو كافر", "ar"),
        ]:
            p = prep(text)
            self.assertEqual((p.kind, p.level), (tg.REFER, "D"), text)


    def test_music_dispute_is_level_c(self):
        for text, lang in [
            ("my friend says music is haram but my cousin says its fine who is right", "en"),
            ("my brother says music is haram but my mom listens to it", "en"),
            ("my dad says watching tv is haram and my mom says its fine", "en"),
            ("is listening to music haram in islam", "en"),
            ("امي تقول الموسيقى حرام وابوي يقول لا مين الصح", "ar"),
            ("ابوي يقول الرسم حرام وامي تقول عادي", "ar"),
            ("هل الاغاني حرام", "ar"),
        ]:
            p = prep(text)
            self.assertEqual((p.kind, p.level), (tg.REFER, "C"), text)

    def test_two_scholars_two_answers_is_level_c(self):
        for text, lang in [
            ("my sheikh told me one thing and another sheikh said the opposite", "en"),
            ("my mom asked two sheikhs and got two different answers", "en"),
            ("ليش الشيخ فلان قال شي والشيخ الثاني قال شي ثاني", "ar"),
        ]:
            p = prep(text)
            self.assertEqual((p.kind, p.level), (tg.REFER, "C"), text)

    def test_a_plain_halal_or_haram_question_is_not_a_conflict(self):
        h = prep("is pork haram or halal")
        self.assertNotEqual(h and h.rule_id, "conflicting_claims")


# ------------------------------------------------------------ 7. attribution gate


class AttributionGateTests(SimpleTestCase):
    def reply(self, text, items, lang="en", count=True):
        agent = turn_pipeline.TurnGuardMixin.__new__(turn_pipeline.TurnGuardMixin)
        agent._guard_language = lang
        agent._turn_items = list(items)  # what search_bank returned this turn
        agent._prev_items = []
        return run(collect(agent.guard_speech(agen([text]), count=count)))

    def test_licensed_kinds_by_item_type(self):
        k = turn_pipeline.licensed_kinds
        self.assertEqual(k([item(1, "verse")]), {"quran"})
        self.assertEqual(k([item(2, "hadith")]), {"hadith"})
        self.assertEqual(k([item(3, "verse"), item(4, "hadith")]), {"quran", "hadith"})
        self.assertEqual(k([item(5, "tafsir")]), {"quran"})
        self.assertEqual(k([item(5, "faq")]), set())  # excerpts license only what they link to
        self.assertEqual(k([item(6, "term")]), set())
        self.assertEqual(k([item(7, "story")]), set())
        self.assertEqual(k([]), set())

    def test_hadith_attribution_without_a_hadith_item_is_blocked(self):
        for text in ("The Prophet said that kindness is good.", "A hadith says to be kind.",
                     "It is narrated that he smiled."):
            self.assertEqual(self.reply(text, []), sg.DECLINE_TEXT["en"], text)
        for text in ("قال رسول الله شيئا مفيدا", "في الحديث ان اللطف مفيد"):
            self.assertEqual(self.reply(text, [], "ar"), sg.DECLINE_TEXT["ar"], text)

    def test_a_verse_does_not_license_hadith_attribution(self):
        verse = [item(1, "verse")]
        out = self.reply("The Prophet said that kindness is good.", verse)
        self.assertNotIn("kindness", out)
        self.assertEqual(self.reply("Allah says to be kind to people.", verse), "Allah says to be kind to people.")
        self.assertNotIn("مفيد", self.reply("قال رسول الله شيئا مفيدا", verse, "ar"))
        self.assertIn("مفيد", self.reply("قال الله شيئا مفيدا", verse, "ar"))

    def test_a_hadith_does_not_license_allah_says(self):
        hadith = [item(2, "hadith")]
        self.assertEqual(self.reply("The Prophet said to be kind.", hadith), "The Prophet said to be kind.")
        out = self.reply("In the Quran, Allah says to be kind.", hadith)
        self.assertNotIn("be kind", out)
        self.assertNotIn("مفيد", self.reply("قال الله شيئا مفيدا", hadith, "ar"))
        self.assertIn("مفيد", self.reply("قال النبي شيئا مفيدا", hadith, "ar"))

    def test_linked_excerpts_license_what_they_link_to_and_terms_license_neither(self):
        both = frozenset({"verse", "hadith"})
        for t in ("faq", "aqidah", "fiqh", "sirah"):
            self.assertEqual(
                self.reply("Allah says be kind and the Prophet said so.", [item(1, t, _linked_types=both)]),
                "Allah says be kind and the Prophet said so.", t)
            self.assertNotIn("be kind", self.reply("Allah says be kind.", [item(1, t)]), t)
        self.assertEqual(self.reply("Allah says be kind.", [item(1, "tafsir")]), "Allah says be kind.")
        self.assertEqual(self.reply("The Prophet said so.", [item(1, "tafsir")]), sg.DECLINE_TEXT["en"])
        self.assertNotIn("be kind", self.reply("Allah says be kind.", [item(1, "term")]))

    def test_counters_record_one_event_per_reply(self):
        before = dict(sg.STATS)
        self.reply("The Prophet said that kindness is good.", [])
        self.assertEqual(sg.STATS["attribution_blocked"], before.get("attribution_blocked", 0) + 1)
        self.reply("The Prophet said that kindness is good.", [], count=False)
        self.assertEqual(sg.STATS["attribution_blocked"], before.get("attribution_blocked", 0) + 1)

    def test_scripture_marks_are_counted_once_per_reply(self):
        before = sg.STATS["scripture_stripped"]
        marked = "ok " + sg.ORNATE_OPEN + "نص تجريبي" + sg.ORNATE_CLOSE + " done"
        self.reply(marked, [item(1, "verse")])
        counted = sg.STATS["scripture_stripped"] - before
        self.assertGreaterEqual(counted, 1)
        self.reply(marked, [item(1, "verse")], count=False)
        self.assertEqual(sg.STATS["scripture_stripped"] - before, counted)


# ---------------------------------------------------------------------- 8. low items


class LowItemTests(SimpleTestCase):
    def test_arabic_ranges_are_escaped_in_the_sources(self):
        base = Path(sg.__file__).parent
        for name in ("scripture_guard.py", "text_match.py"):
            src = (base / name).read_text(encoding="utf-8")
            # a range written with literal Arabic characters (or compared with <=) would be
            # invisible in review; the sources must spell the bounds as backslash-u escapes
            self.assertIsNone(re.search("[\u0600-\u06ff\u08a0-\u08ff]-[\u0600-\u06ff\u08a0-\u08ff]", src), name)
            self.assertIsNone(re.search("<=\\s*[\"'][\u0600-\u06ff]", src), name)
            self.assertIn("\\u0600-\\u06ff", src, name)
        self.assertTrue(sg._ARABIC.search("ب"))
        self.assertFalse(sg._ARABIC.search("b"))

    def test_dialect_plural_and_double_clitic_forms(self):
        self.assertIn("يتطلقوا", forms("يتطلقون"))
        self.assertIn("يلمسني", forms("وبيلمسني"))
        self.assertIn("كذب", forms("بالكذب"))

    def test_rule_matching_is_fast(self):
        import time
        text = "My mom asked two sheikhs and got two different answers, why do scholars differ and is lying a sin for my family?"
        tg.check(text)
        t = time.perf_counter()
        for _ in range(50):
            tg.check(text)
        self.assertLess((time.perf_counter() - t) / 50, 0.005)


# ------------------------------------------------- 9. definition + person; prophet event questions


class JudgingNamedPersonTests(SimpleTestCase):
    """A "what is jannah" definition must not cancel a refer when a relative's fate is asked."""

    REFER_ALL = [
        ("what is heaven for my grandma", "en"),
        ("what's paradise like for my grandma who died", "en"),
        ("what is heaven like for grandpa now", "en"),
        ("is grandpa in heaven? what is heaven", "en"),
        ("what's hell? is my uncle going there?", "en"),
        ("what is heaven? is she there", "en"),
        ("is my uncle going to hell?", "en"),
        ("شو الجنة وهل عمي بيروح النار", "ar"),
        ("وش هي الجنة؟ وهل جدي بيدخلها؟", "ar"),
        ("جدتي ماتت، وش هي الجنة اللي راحت لها؟", "ar"),
        ("ما الجنة التي دخلها جدي", "ar"),
        ("عمي بيدخل النار؟", "ar"),
        ("هي بتدخل النار؟", "ar"),
        ("امي بتروح الجنة؟", "ar"),
    ]
    DEFINITIONS = [("وش هي الجنة؟", "ar"), ("شو هي النار", "ar"), ("what is heaven?", "en")]

    def test_fate_of_a_person_refers(self):
        for text, lang in self.REFER_ALL:
            h = prep(text)
            self.assertEqual(h and h.kind, tg.REFER, text)

    def test_bare_definitions_do_not_refer(self):
        for text, lang in self.DEFINITIONS:
            self.assertIsNone(prep(text), text)


