"""Second-round tests for the turn guard: safety routing, level D coverage, the
transcript guard, the typed path after a tool call, attribution forms and
{{verse:S:A}} markers. Every religious sentence here is a PLACEHOLDER."""
import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase

from authentication.models import ChildProfile, ParentChildLink, ParentProfile
from conversation.agent import scripture_guard as sg
from conversation.agent import turn_pipeline
from conversation.agent import turn_guard as tg
from conversation.agent.retrieval import (
    ValueIndex, card_payload, format_sources_block, match_values, replace_verse_markers, text_segments,
    verse_refs,
)
from conversation.models import Message, Session
from conversation.test_turn_policy import drain_guard_tasks, item, synthetic_index
from content_safety.models import Alert, SafetyFlag

User = get_user_model()


def run(coro):
    return asyncio.run(coro)


async def agen(chunks):
    for c in chunks:
        yield c


async def collect(stream):
    return [c async for c in stream]


def pol(text, lang="en"):
    return tg.check(text)


class SafetyRulesTests(SimpleTestCase):
    def test_false_positives_are_not_safety(self):
        for t in [
            "my dad and I had a pillow fight",
            "I'm scared of the dark at home",
            "someone at football hit me with the ball by accident",
            "ابي اعرف عن الطلاق",
            "What is divorce?",
            "My brother hit me with a pillow while we were playing",
            "I fight with the dragon in my video game with my dad",
        ]:
            h = pol(t)
            self.assertFalse(h and h.kind == tg.SAFETY, t)

    def test_true_positives_and_flag_types(self):
        cases = [
            ("My parents are fighting all the time", "family_fighting", "sensitive", False),
            ("my parents fight every night", "family_fighting", "sensitive", False),
            ("بابا وماما يتضاربون", "family_fighting", "sensitive", False),
            ("بابا يضرب ماما لما يزعل وأنا خايف", "violence_witnessed_at_home", "harmful", False),
            ("My dad hits my mom when he gets angry. I'm really scared.", "violence_witnessed_at_home", "harmful", False),
            ("My dad hit me with a belt because I forgot", "hitting_at_home", "harmful", False),
            ("I'm scared to go home", "fear_at_home", "sensitive", False),
            ("My uncle touches me in places I don't like", "unsafe_touch", "harmful", False),
            ("Sometimes I wish I could just disappear. Nobody would even notice.", "self_harm", "harmful", True),
            ("The kids at school hit me every day", "bullying", "sensitive", True),
            ("الأولاد في المدرسة يضربونني كل يوم", "bullying", "sensitive", True),
            ("Can you tell me about drugs? My friend said they feel fun.", "drugs_or_adult_content", "inappropriate", True),
        ]
        for text, rule, flag, notify in cases:
            p = pol(text)
            self.assertEqual((p.kind, p.rule_id, p.flag_type, p.notify_parent),
                             (tg.SAFETY, rule, flag, notify), text)

    def test_safety_wins_over_value_keywords(self):
        self.assertEqual(pol("My dad hits my mom when she lies about money").kind, tg.SAFETY)

    def test_safety_instruction_wording(self):
        text = pol("my dad hits me").note.lower()
        self.assertIn("trusted adult or a teacher", text)
        self.assertIn("already recorded; do not call flag_safety_concern", text)
        self.assertIn("never say that anyone has been told", text)
        self.assertIn("never promise to keep it secret", text)
        self.assertNotIn("responsible adults", text)

    def test_base_prompt_does_not_promise_parent_notification(self):
        from conversation.agent.agent_class import AlSadiqAgent
        ins = AlSadiqAgent(db_session_id=1, child_id=1).instructions
        self.assertNotIn("so their parent can be informed", ins)


class SafetyFlagFlowTests(TestCase):
    """The real flag function writes only what the rule allows."""

    def setUp(self):
        self.parent_user = User.objects.create_user(username="par", password="x")
        self.parent = ParentProfile.objects.create(user=self.parent_user, name="P")
        self.user = User.objects.create_user(username="kidx", password="x", is_child=True)
        self.child = ChildProfile.objects.create(user=self.user, nickname="K", gender="male", birth_year=2015)
        ParentChildLink.objects.create(parent=self.parent, child=self.child, consent_status="approved")
        self.session = Session.objects.create(child=self.child, livekit_room_name="room-flag")
        self.msg = Message.objects.create(session=self.session, sender="child", content="x", input_type="voice")

    def flag(self, **kw):
        from conversation.agent.agent_class import _create_safety_flag_and_alert
        return _create_safety_flag_and_alert.func(
            message_id=self.msg.pk, session_id=self.session.pk, child_id=self.child.pk,
            flag_type="harmful", description="STAFF NOTE hitting_at_home", **kw)

    def test_staff_only_flag_never_alerts_a_parent(self):
        self.flag(notify_parents=False, alert_description="neutral")
        self.assertEqual(SafetyFlag.objects.filter(message=self.msg).count(), 1)
        self.assertEqual(Alert.objects.count(), 0)

    def test_notifying_flag_alerts_with_neutral_text(self):
        self.flag(notify_parents=True, alert_description="Sadiq noticed something that may need a check-in.")
        alert = Alert.objects.get()
        self.assertNotIn("hitting_at_home", alert.description)
        self.assertNotIn("STAFF", alert.description)

    def test_default_behaviour_unchanged_for_the_llm_tool(self):
        self.flag()
        self.assertEqual(Alert.objects.count(), 1)

    def test_the_tools_off_topic_flag_is_recorded_without_an_alert_and_leaves_the_alert(self):
        # hk/12b: the real tool and database helper, end to end
        from asgiref.sync import async_to_sync

        from conversation.agent.agent_class import AlSadiqAgent
        agent = AlSadiqAgent(db_session_id=self.session.pk, child_id=self.child.pk, language="en",
                             value_index=synthetic_index())
        agent._turn_ref = turn_pipeline.TurnRef(None)
        agent._turn_ref.id = self.msg.pk

        async def flag(flag_type, text):
            agent._turn_text = text
            return await agent.flag_safety_concern(flag_type=flag_type, description="model note")

        self.assertEqual(async_to_sync(flag)("off_topic", "tell me about scary movies again"), "Recorded.")
        row = SafetyFlag.objects.get(message=self.msg)
        self.assertEqual((row.flag_type, row.description), ("off_topic", "model note"))
        self.assertEqual(Alert.objects.count(), 0)
        async_to_sync(flag)("sensitive", "everyone hates me and nobody would care if I disappeared")
        self.assertEqual(SafetyFlag.objects.filter(message=self.msg).count(), 2)
        self.assertEqual(Alert.objects.filter(parent=self.parent, session=self.session).count(), 1)


class SafetyPipelineTests(SimpleTestCase):
    def make_agent(self):
        from conversation.agent.agent_class import AlSadiqAgent
        return AlSadiqAgent(db_session_id=1, child_id=1, language="en", value_index=synthetic_index())

    def turn(self, agent, text, flag_mock, new_id=None, wait=0.5):
        async def go():
            with patch("conversation.agent.turn_pipeline._write_turn_records", new=AsyncMock()), \
                    patch.object(turn_pipeline, "_FLAG_WAIT_SECONDS", wait), \
                    patch("conversation.agent.agent_class._create_safety_flag_and_alert", new=flag_mock):
                await agent.on_user_turn_completed(MagicMock(), SimpleNamespace(text_content=text))
                if new_id:
                    agent._last_child_message_id = new_id
                await drain_guard_tasks(agent)
        run(go())

    def test_hitting_at_home_alerts_the_parent(self):
        a = self.make_agent()
        a._last_child_message_id = 1
        flag = AsyncMock(return_value="ok")
        self.turn(a, "my dad hits me", flag, new_id=2)
        kw = flag.await_args.kwargs
        self.assertEqual((kw["message_id"], kw["flag_type"], kw["notify_parents"]), (2, "harmful", True))
        self.assertNotIn("my dad", kw["description"])

    def test_self_harm_rule_does_notify(self):
        a = self.make_agent()
        flag = AsyncMock(return_value="ok")
        self.turn(a, "I want to hurt myself", flag, new_id=7)
        self.assertTrue(flag.await_args.kwargs["notify_parents"])
        self.assertNotIn("self_harm", flag.await_args.kwargs["alert_description"])

    def test_every_disclosure_is_flagged_but_a_parent_is_alerted_once_per_rule(self):
        a = self.make_agent()
        flag = AsyncMock(return_value="ok")
        self.turn(a, "the kids at school hit me every day", flag, new_id=2)
        self.turn(a, "the kids at school hit me again", flag, new_id=3)
        self.assertEqual(flag.await_count, 2)
        self.assertEqual([c.kwargs["message_id"] for c in flag.await_args_list], [2, 3])
        self.assertEqual([c.kwargs["notify_parents"] for c in flag.await_args_list], [True, False])
        self.turn(a, "my parents are fighting", flag, new_id=4)
        self.assertEqual(flag.await_count, 3)

    def test_family_rules_alert_the_parent_once_per_rule_with_no_prefix(self):
        # hk/12g (lead decision): parents are trusted; there is no staff-only path
        from content_safety.models import NEUTRAL_ALERT_DESCRIPTION, NO_PARENT_NOTIFY_PREFIX
        a = self.make_agent()
        flag = AsyncMock(return_value="ok")
        self.turn(a, "my dad hits me", flag, new_id=2)
        self.turn(a, "my dad hits me again", flag, new_id=3)
        self.assertEqual([c.kwargs["notify_parents"] for c in flag.await_args_list], [True, False])
        for c in flag.await_args_list:
            self.assertFalse(c.kwargs["description"].startswith(NO_PARENT_NOTIFY_PREFIX))
            self.assertEqual(c.kwargs["alert_description"], NEUTRAL_ALERT_DESCRIPTION)

    def test_no_new_message_id_means_no_flag_on_the_previous_message(self):
        a = self.make_agent()
        a._last_child_message_id = 41
        flag = AsyncMock(return_value="ok")
        self.turn(a, "my dad hits me", flag, new_id=None, wait=0.3)
        flag.assert_not_awaited()

    def test_llm_tool_defers_in_a_safety_turn(self):
        a = self.make_agent()
        a._last_child_message_id = 5
        flag = AsyncMock(return_value="ok")
        self.turn(a, "my dad hits me", flag, new_id=6)
        with patch("conversation.agent.agent_class._create_safety_flag_and_alert", new=flag):
            before = flag.await_count
            out = run(a.flag_safety_concern.__wrapped__(a, "harmful", "x")) if hasattr(
                a.flag_safety_concern, "__wrapped__") else None
        if out is not None:
            self.assertIn("Already recorded", out)
            self.assertEqual(flag.await_count, before)
        self.assertTrue(a._safety_turn)


class LevelDTests(SimpleTestCase):
    def test_worship_questions_are_level_d(self):
        for t, lang in [
            ("is it ok to skip prayer if I'm tired?", "en"),
            ("should I pray if I am sick", "en"),
            ("do I have to fast if I'm 8?", "en"),
            ("هل لازم أصلي إذا كنت مريض؟", "ar"),
            ("اقدر اصلي بالبيجامة؟", "ar"),
            ("ممكن ما أصلي الفجر لو سهرت وأنا تعبان؟", "ar"),
            ("Does my mom's prayer count if she stood up halfway to pick up my baby brother?", "en"),
            ("هل صلاة ماما تصح لو وقفت في نصها؟", "ar"),
            ("صلاة أمي تصح؟", "ar"),
            ("does my dad's fast still count", "en"),
        ]:
            p = pol(t)
            self.assertEqual((p.kind, p.level), (tg.REFER, "D"), t)

    def test_everyday_questions_stay_untouched(self):
        for t in ["should I tell my friend the truth", "can I have a snack", "do I have to do homework",
                  "why do we pray", "how long do we fast", "ليش نصلي", "do you pray?", "هل تصلي؟"]:
            self.assertIsNone(pol(t), t)


class TranscriptGuardTests(SimpleTestCase):
    def agent(self):
        from conversation.agent.agent_class import AlSadiqAgent
        return AlSadiqAgent(db_session_id=1, child_id=1)

    def test_transcript_gets_the_same_attribution_guard_as_the_audio(self):
        a = self.agent()
        chunks = ["Nice! ", "The Prophet ", "said PLACEHOLDER ", "SAYING."]
        spoken = "".join(run(collect(a.guard_speech(agen(chunks)))))
        shown = "".join(run(collect(a.transcription_node(agen(chunks), None))))
        self.assertEqual(spoken.split(), shown.split())
        self.assertIn(sg.DECLINE_TEXT["en"].split(".")[0], shown)
        self.assertNotIn("PLACEHOLDER", shown)

    def test_transcript_strips_ornate_spans_and_markdown(self):
        a = self.agent()
        text = "**bold** \ufd3f placeholder span \ufd3e end"
        shown = "".join(run(collect(a.transcription_node(agen([text]), None))))
        self.assertNotIn("placeholder span", shown)
        self.assertNotIn("**", shown)

    def test_served_turn_transcript_passes_through(self):
        a = self.agent()
        a._turn_items = [SimpleNamespace(type="hadith")]  # search_bank returned a hadith: the licence
        shown = "".join(run(collect(a.transcription_node(agen(["The Prophet said PLACEHOLDER."]), None))))
        self.assertIn("The Prophet said PLACEHOLDER.", shown)

    def test_timed_chunks_pass_through_untouched(self):
        from livekit.agents.types import TimedString
        a = self.agent()
        chunks = [TimedString("Hello ", start_time=0.0), TimedString("there", start_time=0.5)]
        out = run(collect(a.guard_transcript(agen(chunks))))
        self.assertTrue(all(isinstance(c, TimedString) for c in out))
        self.assertEqual("".join(out), "Hello there")


class TypedPathAfterToolCallTests(SimpleTestCase):

    def test_instructions_path_would_have_lost_it(self):
        """Documents why chat_ctx is used: update_instructions replaces the system text."""
        from livekit.agents import llm
        from livekit.agents.voice.generation import update_instructions

        ctx = llm.ChatContext.empty()
        update_instructions(ctx, instructions="BASE\nTURN POLICY extra", add_if_missing=True)
        update_instructions(ctx, instructions="BASE", add_if_missing=False)
        self.assertNotIn("TURN POLICY", " ".join(m.text_content or "" for m in ctx.messages()))


# Exact token streams of o200k_base (the OpenAI tokenizer the agent LLM streams in), one entry per phrase, as
# decoded text deltas. Produced with tiktoken 0.14.0 (not installed in the image, so they are hard-coded; a test
# re-checks them whenever tiktoken is importable). Arabic words are split BELOW word level, e.g. the word
# for "orphan" arrives as " ي" + "تي" + "ما" and the title "النبي" can arrive as "الن" + "بي".
_O200K_SPLITS = {
    "كان النبي يتيما في صغره": ["كان", " النبي", " ي", "تي", "ما", " في", " ص", "غ", "ره"],
    "النبي ﷺ كان يتيما": ["الن", "بي", " ﷺ", " كان", " ي", "تي", "ما"],
    "كان النبي ﷺ يتيما في صغره": ["كان", " النبي", " ﷺ", " ي", "تي", "ما", " في", " ص", "غ", "ره"],
    "ان النبي كان يتيما في صغره": ["ان", " النبي", " كان", " ي", "تي", "ما", " في", " ص", "غ", "ره"],
    "ان النبي ﷺ كان يتيما في صغره": ["ان", " النبي", " ﷺ", " كان", " ي", "تي", "ما", " في", " ص", "غ", "ره"],
    "كان النبي يقينا": ["كان", " النبي", " يق", "ينا"],
    "النبي كان يهوديا": ["الن", "بي", " كان", " ي", "هود", "يا"],
    "كان النبي يمنيا": ["كان", " النبي", " يمن", "يا"],
    "النبي ﷺ كان يتيما فقيرا": ["الن", "بي", " ﷺ", " كان", " ي", "تي", "ما", " فق", "يرا"],
    "كان النبي يوسف عليه السلام يحب اباه": ["كان", " النبي", " يوسف", " عليه", " السلام", " يحب", " اب", "اه"],
    "كان النبي يعقوب حزينا": ["كان", " النبي", " يع", "ق", "وب", " حز", "ينا"],
    "كان النبي يونس صابرا": ["كان", " النبي", " ي", "ونس", " ص", "اب", "را"],
    "كان النبي يوشع قائدا": ["كان", " النبي", " ي", "وش", "ع", " قائ", "دا"],
    "كان النبي يحيى عليه السلام بارا كذا": ["كان", " النبي", " ي", "حي", "ى", " عليه", " السلام", " بار", "ا", " ك", "ذا"],
    "كان النبي يحيى بن زكريا بارا كذا": ["كان", " النبي", " ي", "حي", "ى", " بن", " ز", "ك", "ريا", " بار", "ا", " ك", "ذا"],
    "كان النبي يحيى ابن زكريا بارا كذا": ["كان", " النبي", " ي", "حي", "ى", " ابن", " ز", "ك", "ريا", " بار", "ا", " ك", "ذا"],
    "النبي يعقوب كان حزينا": ["الن", "بي", " يع", "ق", "وب", " كان", " حز", "ينا"],
    "مرحبا يا صديقي، كان النبي يتيما في صغره وكان جده يرعاه.": ["مرح", "با", " يا", " ص", "دي", "قي", "،", " كان", " النبي", " ي", "تي", "ما", " في", " ص", "غ", "ره", " وكان", " ج", "ده", " ير", "ع", "اه", "."],
    "كان النبي يحب كذا": ["كان", " النبي", " يحب", " ك", "ذا"],
    "النبي ﷺ كان يحب كذا": ["الن", "بي", " ﷺ", " كان", " يحب", " ك", "ذا"],
    "كان النبي يحيي كذا": ["كان", " النبي", " ي", "حي", "ي", " ك", "ذا"],
    "ان النبي كان يحب كذا": ["ان", " النبي", " كان", " يحب", " ك", "ذا"],
    "النبي ﷺ كان يبتسم دائما": ["الن", "بي", " ﷺ", " كان", " ي", "بت", "سم", " دائما"],
    "كان النبي ﷺ يتيمم كذا": ["كان", " النبي", " ﷺ", " يت", "يم", "م", " ك", "ذا"],
    "كان النبي لا يحب كذا": ["كان", " النبي", " لا", " يحب", " ك", "ذا"],
    "كان النبي اذا غضب كذا": ["كان", " النبي", " اذا", " غض", "ب", " ك", "ذا"],
    "كان رسول الله ﷺ يحب كذا": ["كان", " رسول", " الله", " ﷺ", " يحب", " ك", "ذا"],
    "رسول الله ﷺ كان يحب كذا": ["رس", "ول", " الله", " ﷺ", " كان", " يحب", " ك", "ذا"],
    "ان رسول الله كان يحب كذا": ["ان", " رسول", " الله", " كان", " يحب", " ك", "ذا"],
    "كان النبي يحيى كذا": ["كان", " النبي", " ي", "حي", "ى", " ك", "ذا"],
    "النبي -صلى الله عليه وسلم- قال كذا": ["الن", "بي", " -", "ص", "لى", " الله", " عليه", " وسلم", "-", " قال", " ك", "ذا"],
    "النبي ﷺ فعل كذا": ["الن", "بي", " ﷺ", " فعل", " ك", "ذا"],
    "ان النبي ﷺ فعل كذا": ["ان", " النبي", " ﷺ", " فعل", " ك", "ذا"],
    # review round 2: the Yahya-greets family, glued dashes, Quran/qal gaps (tiktoken 0.14.0, o200k_base)
    "كان رسول الله صلى الله عليه وآله وسلم يحيي ابنته كذا": ["كان", " رسول", " الله", " صلى", " الله", " عليه", " وآ", "له", " وسلم", " ي", "حي", "ي", " ابن", "ته", " ك", "ذا"],
    "النبي، صلى الله عليه وآله وسلم، كان يحيي ابنته كذا": ["الن", "بي", "،", " صلى", " الله", " عليه", " وآ", "له", " وسلم", "،", " كان", " ي", "حي", "ي", " ابن", "ته", " ك", "ذا"],
    "كان رسول الله صلى الله عليه وآله وسلم يحيي بناته كذا": ["كان", " رسول", " الله", " صلى", " الله", " عليه", " وآ", "له", " وسلم", " ي", "حي", "ي", " بن", "اته", " ك", "ذا"],
    "رسول الله ، صلى الله عليه وسلم، كان يحيي ابنه كذا": ["رس", "ول", " الله", " ،", " صلى", " الله", " عليه", " وسلم", "،", " كان", " ي", "حي", "ي", " اب", "نه", " ك", "ذا"],
    "كان رسول الله صلى الله عليه وسلم يحيي ابناءه كذا": ["كان", " رسول", " الله", " صلى", " الله", " عليه", " وسلم", " ي", "حي", "ي", " اب", "ناء", "ه", " ك", "ذا"],
    "كان النبي يحيي ابن عمه كذا": ["كان", " النبي", " ي", "حي", "ي", " ابن", " ع", "مه", " ك", "ذا"],
    "كان النبي يحيي ابن آدم كذا": ["كان", " النبي", " ي", "حي", "ي", " ابن", " آدم", " ك", "ذا"],
    "كان النبي يحيي -ابن- كذا": ["كان", " النبي", " ي", "حي", "ي", " -", "اب", "ن", "-", " ك", "ذا"],
    "كان النبي يحيي عليه السلامة كذا": ["كان", " النبي", " ي", "حي", "ي", " عليه", " السلام", "ة", " ك", "ذا"],
    "كان النبي يحيي بن عمه كذا": ["كان", " النبي", " ي", "حي", "ي", " بن", " ع", "مه", " ك", "ذا"],
    "The Prophet—peace be upon him—said PLACEHOLDER.": ["The", " Prophet", "—", "peace", " be", " upon", " him", "—", "said", " PLACE", "H", "OLDER", "."],
    "The Prophet-peace be upon him-said PLACEHOLDER.": ["The", " Prophet", "-pe", "ace", " be", " upon", " him", "-s", "aid", " PLACE", "H", "OLDER", "."],
    "Our Prophet—peace be upon him—taught PLACEHOLDER.": ["Our", " Prophet", "—", "peace", " be", " upon", " him", "—", "t", "aught", " PLACE", "H", "OLDER", "."],
    "النبي-صلى الله عليه وسلم-قال كذا": ["الن", "بي", "-", "ص", "لى", " الله", " عليه", " وسلم", "-", "قال", " ك", "ذا"],
    "كان النبي-صلى الله عليه وسلم-يحب كذا": ["كان", " النبي", "-", "ص", "لى", " الله", " عليه", " وسلم", "-", "ي", "حب", " ك", "ذا"],
    "ان النبي-صلى الله عليه وسلم-نهى عن كذا": ["ان", " النبي", "-", "ص", "لى", " الله", " عليه", " وسلم", "-", "نه", "ى", " عن", " ك", "ذا"],
    "النبي-صلى الله عليه وسلم- قال كذا": ["الن", "بي", "-", "ص", "لى", " الله", " عليه", " وسلم", "-", " قال", " ك", "ذا"],
    "النبي—ﷺ—كان يحب كذا": ["الن", "بي", "—", "", "ﷺ", "—", "كان", " يحب", " ك", "ذا"],
    "ونبي الله ﷺ كان يحب كذا": ["ون", "بي", " الله", " ﷺ", " كان", " يحب", " ك", "ذا"],
    "فنبي الله ﷺ كان يحب كذا": ["فن", "بي", " الله", " ﷺ", " كان", " يحب", " ك", "ذا"],
    "الله -عز وجل- يقول كذا": ["الله", " -", "ع", "ز", " وجل", "-", " يقول", " ك", "ذا"],
    "الله - عز وجل - يقول كذا": ["الله", " -", " عز", " وجل", " -", " يقول", " ك", "ذا"],
    "الله (عز وجل) يقول كذا": ["الله", " (", "ع", "ز", " وجل", ")", " يقول", " ك", "ذا"],
    "الله، عز وجل، يقول كذا": ["الله", "،", " عز", " وجل", "،", " يقول", " ك", "ذا"],
    "الله —سبحانه وتعالى— يأمرنا بكذا": ["الله", " —", "سب", "ح", "انه", " وتع", "الى", "—", " يأ", "مر", "نا", " بك", "ذا"],
    "Allah - the Almighty - says PLACEHOLDER.": ["Allah", " -", " the", " Almighty", " -", " says", " PLACE", "H", "OLDER", "."],
    "قال -صلى الله عليه وسلم-: كذا": ["قال", " -", "ص", "لى", " الله", " عليه", " وسلم", "-", ":", " ك", "ذا"],
    "قال (صلى الله عليه وسلم): كذا": ["قال", " (", "ص", "لى", " الله", " عليه", " وسلم", "):", " ك", "ذا"],
    "وقال -عليه الصلاة والسلام-: كذا": ["وقال", " -", "ع", "ليه", " الصلاة", " والسلام", "-", ":", " ك", "ذا"],
    "كان النبي -ﷺ- كريما - وكان رحيما": ["كان", " النبي", " -", "", "ﷺ", "-", " ك", "ري", "ما", " -", " وكان", " ر", "حي", "ما"],
    "The well-known prophets were kind - very kind.": ["The", " well", "-known", " prophets", " were", " kind", " -", " very", " kind", "."],
}


class AttributionFormsTests(SimpleTestCase):
    """Placeholders only: the guard works on the phrasing around the sentence."""

    def blocked(self, text, lang="en"):
        """Blocked at every chunk size, and no word of the attribution leaks before the decline."""
        results = set()
        decline = sg.DECLINE_TEXT["ar" if lang == "ar" else "en"].split(".")[0]
        for n in (1, 2, 3, 5, 8, 100):
            out = "".join(run(collect(sg.guard_attribution_stream(agen(self.split(text, n)), lambda: False, lang))))
            results.add(decline in out)
            if decline in out:
                spoken = out.split(decline)[0]
                for lead in (
                    "prophet", "quran", "hadith", "allah", "النبي", "رسول", "القرآن", "الحديث", "قال",
                    "أن", "ان", "لأن", "لان",
                ):
                    self.assertNotIn(lead, spoken.lower(), (text, n, out))
        return results == {True}

    def stream_out(self, tokens, lang="ar"):
        return "".join(run(collect(sg.guard_attribution_stream(agen(tokens), lambda: False, lang))))

    def blocked_tokens(self, tokens, lang="ar"):
        """The stream for these exact tokens ends in the decline and says nothing of the claim before it."""
        out = self.stream_out(tokens, lang)
        decline = sg.DECLINE_TEXT["ar" if lang == "ar" else "en"].split(".")[0]
        if decline not in out:
            return False
        for lead in ("النبي", "رسول", "كان", "ان ", "ان", "أن", "لأن", "لان"):
            self.assertNotIn(lead, out.split(decline)[0], (tokens, out))
        return True

    def split(self, text, n):
        return [text[i:i + n] for i in range(0, len(text), n)]

    def test_english_forms_are_caught(self):
        for t in [
            "The Prophet, peace be upon him, said PLACEHOLDER.",
            "Our Prophet said PLACEHOLDER.",
            "The Prophet \ufdfa once said PLACEHOLDER.",
            "The Prophet used to say PLACEHOLDER.",
            "In the Quran it says PLACEHOLDER.",
            "The Quran teaches us PLACEHOLDER.",
            "There is a hadith that says PLACEHOLDER.",
            "Allah, the Almighty, says PLACEHOLDER.",
            "According to a hadith, PLACEHOLDER.",
            "Prophet Muhammad (peace be upon him) taught PLACEHOLDER.",
        ]:
            self.assertTrue(self.blocked(t), t)

    def test_arabic_forms_are_caught(self):
        for t in [
            "النبي عليه السلام قال كذا",
            "قال صلى الله عليه وسلم كذا",
            "في الحديث كذا",
            "الله سبحانه وتعالى يقول كذا",
            "قال عليه الصلاة والسلام كذا",
            "القرآن الكريم يقول كذا",
        ]:
            self.assertTrue(self.blocked(t, "ar"), t)

    # lead review: "ان النبي كان <imperfect verb>" and "ان النبي فعل" claim what the Prophet did
    def test_lead_phrase_prophet_loved_sweets_needs_a_source(self):
        t = "ان النبي كان يحب الحلواء"
        self.assertIsNotNone(sg.find_attribution(t))
        self.assertTrue(self.blocked(t, "ar"), t)

    def test_lead_phrase_prophet_smiled_with_blessing_sign_and_adverb_needs_a_source(self):
        t = "ان النبي ﷺ كان يبتسم دائما"
        self.assertIsNotNone(sg.find_attribution(t))
        self.assertTrue(self.blocked(t, "ar"), t)

    def test_lead_phrase_prophet_did_such_needs_a_source(self):
        t = "ان النبي فعل كذا"
        self.assertIsNotNone(sg.find_attribution(t))
        self.assertTrue(self.blocked(t, "ar"), t)

    def test_messenger_of_allah_kana_imperfect_needs_a_source(self):
        for t in ("ان رسول الله كان يحب كذا", "أن رسول الله كان يأكل كذا", "ان رسول الله فعل كذا"):
            self.assertIsNotNone(sg.find_attribution(t), t)
            self.assertTrue(self.blocked(t, "ar"), t)

    def test_blessing_gaps_before_and_after_kana_and_faala(self):
        for t in (
            "ان النبي ﷺ كان يحب كذا",
            "ان النبي صلى الله عليه وسلم كان يحب كذا",
            "ان النبي كان صلى الله عليه وسلم يحب كذا",
            "ان النبي ﷺ كان دائما يحب كذا",
            "ان النبي صلى الله عليه وسلم فعل كذا",
            "ان النبي ﷺ فعل كذا",
            "ان رسول الله (صلى الله عليه وسلم) فعل كذا",
        ):
            self.assertIsNotNone(sg.find_attribution(t), t)
            self.assertTrue(self.blocked(t, "ar"), t)

    def test_kana_with_an_adjective_stays_allowed(self):
        # the served-verse description the earlier loosening was for
        for t in (
            "ان النبي كان رحيما",
            "ان النبي ﷺ كان رحيما بالناس",
            "ان رسول الله صلى الله عليه وسلم كان لطيفا",
        ):
            self.assertIsNone(sg.find_attribution(t), t)
            self.assertIsNone(sg.find_attribution(t, frozenset({"quran"})), t)

    def test_kana_with_a_y_initial_noun_or_adjective_stays_allowed(self):
        # deliberate: ي-initial nouns/adjectives are not imperfect verbs ("يتيما" orphan)
        for t in ("ان النبي كان يتيما", "ان النبي ﷺ كان يتيما في صغره", "ان النبي كان يقينا"):
            self.assertIsNone(sg.find_attribution(t), t)
        # deliberate: "يسير" (walks / easy) is ambiguous and is cut, a false cut only declines
        self.assertIsNotNone(sg.find_attribution("ان النبي كان يسير كذا"))

    def test_faala_as_a_noun_or_adverb_is_not_a_claim(self):
        for t in (
            "ان النبي فعلا رحيم",             # "indeed" (adverb)
            "ان فعل النبي كان رحمة",          # "the Prophet's act" is a noun, the subject is the act
            "ان النبي كان فعله رحمة",         # "his act" (noun with a suffix)
        ):
            self.assertIsNone(sg.find_attribution(t), t)

    def test_long_blessing_before_kana_is_held_back_while_streaming(self):
        # 8+ words before the verb: the weak lead-in "ان" must not be emitted ahead of the claim
        for t in (
            "ان رسول الله صلى الله عليه وسلم كان يحب كذا",
            "ان النبي صلى الله عليه وسلم كان دائما يحب كذا",
            "ان رسول الله صلى الله عليه وسلم فعل كذا",
        ):
            self.assertIsNotNone(sg.find_attribution(t), t)
            self.assertTrue(self.blocked(t, "ar"), t)
            # realistic subword tokens, the verb itself split across two of them
            words = t.split(" ")
            verb_at = words.index("يحب") if "يحب" in words else len(words) - 2
            tokens = [w + " " for w in words[:verb_at]] + [words[verb_at][:2], words[verb_at][2:] + " "]
            tokens += [w + " " for w in words[verb_at + 1:]]
            self.assertTrue(self.blocked_tokens(tokens), tokens)
            # and one word per token, with and without the trailing space
            self.assertTrue(self.blocked_tokens([w + " " for w in words]), t)
            self.assertTrue(self.blocked_tokens([" " + w for w in words]), t)

    def test_arabic_comma_separates_the_blessing_like_a_space(self):
        for t in (
            "النبي، صلى الله عليه وسلم، قال كذا",
            "النبي ﷺ، قال كذا",
            "ان النبي، عليه السلام، نهى عن كذا",
            "ان النبي، صلى الله عليه وسلم، كان يحب كذا",
            "ان النبي ﷺ كان، يحب كذا",
            "ان النبي ، صلى الله عليه وسلم ، كان يحب كذا",   # spaced commas, 8+ words before the verb
        ):
            self.assertIsNotNone(sg.find_attribution(t), t)
            self.assertTrue(self.blocked(t, "ar"), t)
        # a comma after an ordinary sentence still passes
        self.assertIsNone(sg.find_attribution("ان النبي، كان رحيما"))

    def test_partial_words_are_held_while_streaming_and_whole_words_pass(self):
        # The allows for "يتيما" and "فعلا" are decided on a COMPLETE word while a reply streams.
        # The guard reads raw model tokens, and o200k_base splits an Arabic word below word level
        # (" ي" + "تي" + "ما"), so word tokens are NOT what it sees: a chunk that ends inside the
        # word ("يتي", "فعل" before "ا") is undecided and held, never cut. Every chunking, down
        # to single characters, speaks these texts whole (see the o200k tests below for the
        # real token splits).
        for t, tokens in (
            ("ان النبي كان يتيما في صغره", ["ان ", "النبي ", "كان ", "يتيما ", "في ", "صغره"]),
            ("ان النبي فعلا قدوة لنا", ["ان ", "النبي ", "فعلا ", "قدوة ", "لنا"]),
            ("كان النبي ﷺ يتيما في صغره", ["كان ", "النبي ", "ﷺ ", "يتيما ", "في ", "صغره"]),
            ("النبي ﷺ كان يتيما", ["النبي ", "ﷺ ", "كان ", "يتيما"]),
            ("كان النبي يوسف عليه السلام يحب اباه", ["كان ", "النبي ", "يوسف ", "عليه ", "السلام ", "يحب ", "اباه"]),
        ):
            self.assertIsNone(sg.find_attribution(t), t)
            self.assertEqual(self.stream_out(tokens), t)
            for n in (1, 2, 3, 5, 8, 100):
                self.assertEqual(self.stream_out(self.split(t, n)), t, (t, n))

    def test_new_claims_are_licensed_by_a_served_hadith_only(self):
        t = "ان النبي كان يحب كذا"
        self.assertIsNone(sg.find_attribution(t, frozenset({"hadith"})))
        self.assertIsNotNone(sg.find_attribution(t, frozenset({"quran"})))

    # lead decision: verb-first "كان النبي ﷺ يحب كذا" and subject-first "النبي ﷺ كان يحب كذا" claim
    # what the Prophet did, so they need a source like "ان النبي كان يحب كذا". Placeholders only.
    def assert_nothing_spoken_before_decline(self, t):
        decline = sg.DECLINE_TEXT["ar"].split(".")[0]
        words = t.split(" ")
        streams = [(n, self.split(t, n)) for n in (1, 2, 3, 5, 8, 100)]
        streams += [("words", [w + " " for w in words]), ("words-lead-space", [" " + w for w in words])]
        # realistic subword tokens: every word split in two
        sub = []
        for w in words:
            sub += [w[:len(w) // 2 or 1], w[len(w) // 2 or 1:] + " "]
        streams.append(("subword", sub))
        for label, tokens in streams:
            out = self.stream_out(tokens, "ar")
            self.assertIn(decline, out, (t, label, out))
            # a lone proclitic «و» in front of «وقال ...» is the one letter the final rule starts after
            self.assertIn(out.split(decline)[0].strip(), ("", "و"), (t, label, out))

    FIRST_ORDERS = (
        "كان النبي ﷺ يحب كذا",
        "النبي ﷺ كان يحب كذا",
        "كان رسول الله ﷺ يحب كذا",
        "رسول الله ﷺ كان يحب كذا",
        "كان الرسول ﷺ يحب كذا",
        "الرسول ﷺ كان يحب كذا",
        "كان نبينا ﷺ يحب كذا",
        "نبينا ﷺ كان يحب كذا",
        "كان نبي الله ﷺ يحب كذا",
        "نبي الله ﷺ كان يحب كذا",
    )

    def test_verb_first_and_subject_first_kana_claims_need_a_source(self):
        for t in self.FIRST_ORDERS + ("كان النبي يحب كذا", "النبي كان يحب كذا"):
            self.assertIsNotNone(sg.find_attribution(t), t)
            self.assertTrue(self.blocked(t, "ar"), t)
            self.assert_nothing_spoken_before_decline(t)

    def test_blessing_gaps_in_both_orders(self):
        for subj in ("النبي", "رسول الله"):
            for blessing in (
                "", "ﷺ", "(ﷺ)", "صلى الله عليه وسلم", "(صلى الله عليه وسلم)",
                "عليه الصلاة والسلام", "عليه السلام", "صلى الله عليه وآله وسلم", "الكريم",
                "محمد ﷺ" if subj == "النبي" else "ﷺ",
            ):
                for t in (
                    f"كان {subj} {blessing} يحب كذا",
                    f"{subj} {blessing} كان يحب كذا",
                    f"{subj}، {blessing}، كان يحب كذا",
                    f"{subj} {blessing} كان دائما يحب كذا",
                    f"كان {subj} {blessing} دائما يحب كذا",
                    f"{subj} {blessing} فعل كذا",
                ):
                    self.assertIsNotNone(sg.find_attribution(t), t)
                    self.assertTrue(self.blocked(t, "ar"), t)
                    self.assert_nothing_spoken_before_decline(t)

    def test_faala_subject_first_needs_a_source_verb_first_is_the_noun(self):
        for t in (
            "النبي ﷺ فعل كذا", "رسول الله ﷺ فعل كذا", "النبي صلى الله عليه وسلم فعل كذا",
            "والنبي ﷺ فعل كذا", "الرسول عليه الصلاة والسلام فعل كذا", "نبينا (ﷺ) فعل كذا",
        ):
            self.assertIsNotNone(sg.find_attribution(t), t)
            self.assertTrue(self.blocked(t, "ar"), t)
            self.assert_nothing_spoken_before_decline(t)
        # verb-first "فعل النبي" is also the noun "the Prophet's act": deliberately not a claim
        for t in ("فعل النبي ﷺ رحمة", "ان فعل النبي كان رحمة", "كان فعل النبي ﷺ رحمة", "فعل رسول الله كذا"):
            self.assertIsNone(sg.find_attribution(t), t)

    def test_proclitic_on_the_subject_or_kana_needs_a_source(self):
        for t in (
            "وكان النبي ﷺ يحب كذا", "فكان النبي ﷺ يحب كذا", "وكان رسول الله ﷺ يحب كذا",
            "والنبي ﷺ كان يحب كذا", "فالنبي ﷺ كان يحب كذا", "ورسول الله ﷺ كان يحب كذا",
            "ونبينا ﷺ كان يحب كذا", "ان النبي ﷺ كان لا يحب كذا", "لأن النبي ﷺ كان لا يحب كذا",
        ):
            self.assertIsNotNone(sg.find_attribution(t), t)
            self.assertTrue(self.blocked(t, "ar"), t)
            self.assert_nothing_spoken_before_decline(t)

    def test_negated_and_conditional_kana_claims_need_a_source(self):
        for t in (
            "كان النبي ﷺ لا يحب كذا", "النبي ﷺ كان لا يحب كذا", "كان النبي ﷺ لم يفعل كذا",
            "ما كان النبي ﷺ يفعل كذا", "كان النبي ﷺ اذا غضب كذا", "النبي ﷺ كان اذا غضب كذا",
        ):
            self.assertIsNotNone(sg.find_attribution(t), t)
        for t in ("كان النبي ﷺ لا يحب كذا", "النبي ﷺ كان لا يحب كذا", "كان النبي ﷺ اذا غضب كذا"):
            self.assertTrue(self.blocked(t, "ar"), t)
            self.assert_nothing_spoken_before_decline(t)

    def test_long_blessing_in_both_orders_is_held_while_streaming(self):
        for t in (
            "كان رسول الله صلى الله عليه وسلم يحب كذا",
            "رسول الله صلى الله عليه وسلم كان يحب كذا",
            "كان النبي صلى الله عليه وسلم دائما يحب كذا",
            "النبي صلى الله عليه وسلم كان دائما يحب كذا",
            "كان النبي عليه الصلاة والسلام يحب كذا",
            "النبي، صلى الله عليه وسلم، كان يحب كذا",
        ):
            self.assertIsNotNone(sg.find_attribution(t), t)
            self.assert_nothing_spoken_before_decline(t)

    def test_new_forms_are_licensed_by_a_served_hadith_only(self):
        every = ("كان النبي ﷺ يحب كذا", "النبي ﷺ كان يحب كذا", "كان رسول الله ﷺ يحب كذا",
                 "رسول الله ﷺ كان يحب كذا", "النبي ﷺ فعل كذا", "رسول الله ﷺ فعل كذا",
                 "كان النبي ﷺ لا يحب كذا", "وكان النبي ﷺ يحب كذا") + self.FIRST_ORDERS
        for t in every:
            self.assertIsNone(sg.find_attribution(t, frozenset({"hadith"})), t)
            self.assertIsNone(sg.find_attribution(t, sg.KINDS), t)
            self.assertIsNotNone(sg.find_attribution(t, frozenset({"quran"})), t)
            self.assertIsNotNone(sg.find_attribution(t), t)
            # streamed with a hadith served this turn: spoken whole
            for n in (1, 3, 100):
                out = "".join(run(collect(sg.guard_attribution_stream(
                    agen(self.split(t, n)), lambda: {"hadith"}, "ar"))))
                self.assertEqual(out, t, (t, n))
            # a verse served instead does not license it
            out = "".join(run(collect(sg.guard_attribution_stream(
                agen(self.split(t, 3)), lambda: {"quran"}, "ar"))))
            self.assertIn(sg.DECLINE_TEXT["ar"].split(".")[0], out, t)

    def test_kana_with_an_adjective_or_noun_stays_allowed_in_both_orders(self):
        for t in (
            "كان النبي رحيما", "النبي ﷺ كان رحيما", "كان النبي ﷺ رحيما بالاطفال",
            "كان رسول الله لطيفا", "رسول الله صلى الله عليه وسلم كان لطيفا",
            "كان النبي صلى الله عليه وسلم كريما", "النبي عليه الصلاة والسلام كان كريما",
            "كان الرسول رحمة للناس", "نبينا ﷺ كان قدوة لنا",
            "كان النبي يتيما", "النبي ﷺ كان يتيما في صغره", "كان رسول الله يتيما",
            "كان النبي يقينا", "النبي كان يهوديا", "كان النبي يمنيا", "كان النبي ﷺ يتيما فقيرا",
        ):
            self.assertIsNone(sg.find_attribution(t), t)
            self.assertIsNone(sg.find_attribution(t, frozenset({"quran"})), t)
            self.assertEqual(self.stream_out([t], "ar"), t)

    def test_y_initial_verbs_sharing_the_exclusion_prefix_are_caught_in_both_orders(self):
        for t in ("كان النبي ﷺ يتيمم كذا", "النبي ﷺ كان يتيمم كذا", "كان النبي يمنيهم كذا", "النبي كان يمنيه كذا"):
            self.assertIsNotNone(sg.find_attribution(t), t)

    # review fix round: prophets' names that start with ي are names, not imperfect verbs
    def test_y_initial_prophet_names_stay_allowed_after_the_title(self):
        for t in (
            "كان النبي يوسف عليه السلام يحب اباه",
            "كان نبي الله يونس في بطن الحوت",
            "كان النبي يعقوب حزينا",
            "كان نبي الله يوسف جميلا",
            "كان النبي يحيى عليه السلام بارا كذا",
            "كان النبي يحيى بن زكريا بارا كذا",
            "كان النبي يحيى ابن زكريا بارا كذا",
            "كان النبي يحيى (عليه السلام) بارا كذا",
            "كان النبي يوشع قائدا",
            "كان رسول الله يونس صابرا",
            "وكان النبي يوسف ﷺ صبورا",
            "كان النبي يوسف (عليه السلام) يحب اباه",
        ):
            self.assertIsNone(sg.find_attribution(t), t)
            self.assertIsNone(sg.find_attribution(t, frozenset({"quran"})), t)
            self.assertEqual(self.stream_out([t], "ar"), t)
            # one word per token: nothing is cut and nothing is lost
            self.assertEqual(self.stream_out([w + " " for w in t.split(" ")], "ar").strip(), t, t)

    def test_names_are_excluded_only_as_whole_words_and_yahya_only_as_a_name(self):
        # "يحيي" is also the verb "he revives": «كان النبي ﷺ يحيي كذا» is a real claim
        for t in (
            "كان النبي ﷺ يحيي كذا",
            "كان النبي يحيى كذا",
            "النبي ﷺ كان يحيي كذا",
            "كان النبي يحيي كذا عليه السلام",       # «عليه السلام» does not directly follow
            "كان النبي يحيي ابنه كذا",                # «ابنه» ("his son") is not the marker «ابن»
            "كان النبي يونسه كذا",                    # not the whole word
            "كان النبي يوسفهم كذا",
            "كان النبي يعقوبهم كذا",
        ):
            self.assertIsNotNone(sg.find_attribution(t), t)
            self.assertIsNone(sg.find_attribution(t, frozenset({"hadith"})), t)
        for t in ("كان النبي ﷺ يحيي كذا", "كان النبي يحيى كذا"):
            self.assertTrue(self.blocked(t, "ar"), t)
            self.assert_nothing_spoken_before_decline(t)

    def test_yahya_undecided_mid_stream_is_settled_by_the_next_words_or_the_end(self):
        decline = sg.DECLINE_TEXT["ar"].split(".")[0]
        # the name arrives first and "عليه السلام" later, in several tokens: spoken whole
        for tokens in (
            ["كان ", "النبي ", "يحيى ", "عليه ", "السلام ", "بارا ", "كذا"],
            ["كان ", "النبي ", "يحيى", " عليه", " السلام", " بارا"],
            ["كان ", "النبي ", "يحيى ", "ب", "ن ", "زكريا ", "بارا"],
        ):
            self.assertEqual(self.stream_out(tokens, "ar"), "".join(tokens), tokens)
        # the verb "يحيي" settled by the next word, or by the end of the reply: still the decline
        for tokens in (
            ["كان ", "النبي ", "يحيي ", "كذا"],
            ["كان ", "النبي ", "ﷺ ", "يحيي"],
            ["كان ", "النبي ", "ﷺ ", "يحيي ", "عليه ", "كذا"],
        ):
            self.assertTrue(self.blocked_tokens(tokens), tokens)
        # the same with the marker «ابن» ("son of"), also split across tokens
        for tokens in (
            ["كان ", "النبي ", "يحيى ", "ابن ", "زكريا ", "بارا ", "كذا"],
            ["كان ", "النبي ", "يحيى ", "ا", "بن ", "زكريا ", "بارا"],
            ["كان ", "النبي ", "يحيى", " ابن", " زكريا", " بارا"],
        ):
            self.assertEqual(self.stream_out(tokens, "ar"), "".join(tokens), tokens)
        # a character-level stream speaks the name whole (the marker may still be on its way)
        for t in ("كان النبي يحيى عليه السلام بارا كذا", "كان النبي يحيى بن زكريا بارا",
                  "كان النبي يحيى ابن زكريا بارا كذا"):
            for n in (1, 2, 3, 5, 8, 100):
                self.assertEqual(self.stream_out(self.split(t, n), "ar"), t, (t, n))

    def test_a_served_story_about_a_y_named_prophet_is_not_cut_mid_retelling(self):
        t = "كان النبي يوسف عليه السلام يحب اباه كثيرا وكان نبي الله يعقوب حزينا"
        self.assertIsNone(sg.find_attribution(t))
        out = self.stream_out([w + " " for w in t.split(" ")], "ar")
        self.assertEqual(out.strip(), t)
        self.assertNotIn(sg.DECLINE_TEXT["ar"].split(".")[0], out)

    def test_lead_in_before_the_other_subjects_is_held_until_the_decline(self):
        for t in (
            "ان الرسول ﷺ كان يحب كذا",
            "لأن نبينا ﷺ كان يحب كذا",
            "بأن الرسول ﷺ كان يحب كذا",
            "وأن نبينا ﷺ كان يحب كذا",
            "فإن نبي الله ﷺ كان يحب كذا",
        ):
            self.assertIsNotNone(sg.find_attribution(t), t)
            words = t.split(" ")
            self.assertTrue(self.blocked_tokens([w + " " for w in words]), t)
            self.assertTrue(self.blocked_tokens([" " + w for w in words]), t)
            self.assert_nothing_spoken_before_decline(t)
        # ordinary "ان" text is still held for one word only
        self.assertEqual(self.stream_out(["ان ", "الجو ", "جميل ", "اليوم "], "ar"), "ان الجو جميل اليوم ")

    def test_mentions_that_describe_no_act_pass(self):
        for t in (
            "النبي ﷺ هو خاتم الانبياء",
            "احب النبي ﷺ كثيرا",
            "صلى على النبي",
            "اللهم صل على النبي",
            "نحن نحب رسول الله",
            "محمد هو رسول الله",
            "النبي ﷺ رحيم بالاطفال",
            "الانبياء كانوا يحبون كذا",
            "نبي الله موسى كان يحب كذا",
            "كان نبي الله موسى يحب كذا",
            "كان النبيل يحب كذا",
            "النبيل كان يحب كذا",
            "النبي ﷺ فعلا رحيم",
            "فعل الخير جميل",
            "كان فعل النبي ﷺ رحمة",
            "فعل النبي ﷺ رحمة",
        ):
            self.assertIsNone(sg.find_attribution(t), t)
            self.assertEqual(self.stream_out([w + " " for w in t.split(" ")], "ar").strip(), t, t)
            for n in (1, 3, 100):
                # a chunk ending inside "فعل" is undecided and held (see the partial-words test
                # above), so every chunking speaks the text whole
                self.assertEqual(self.stream_out(self.split(t, n), "ar"), t, (t, n))

    def test_everyday_kana_sentences_pass_and_are_not_held(self):
        for t in (
            "كان احمد يحب اللعب",
            "كان ابي يحب القهوة",
            "كان الاستاذ يقول كلاما جميلا",
            "كان يا ما كان في قديم الزمان",
            "كان الجو جميلا اليوم",
            "وكان صديقي سعيدا",
            "فعل الولد خيرا",
            "كان محمد يلعب في الحديقة",
            "هل كان",
        ):
            self.assertIsNone(sg.find_attribution(t), t)
            words = t.split(" ")
            for tokens in (
                self.split(t, 1), self.split(t, 2), self.split(t, 3), self.split(t, 5), self.split(t, 8),
                self.split(t, 100), [w + " " for w in words], [" " + w for w in words],
            ):
                self.assertEqual(self.stream_out(tokens, "ar"), "".join(tokens), (t, tokens))
        # "كان" is held for one word only: the word before it, and the word after the next one, are out
        async def spoken_after(tokens):
            g = sg.guard_attribution_stream(agen(tokens), lambda: False, "ar")
            return await g.__anext__()
        self.assertIn("يا", run(spoken_after(["كان ", "يا ", "ما ", "كان ", "هناك ", "ولد "])))

    def test_ordinary_sentences_pass(self):
        for t in [
            "I think the teacher said hello to the class.",
            "That is a kind thing to do, well done.",
            "The prophets are mentioned by many people.",
            "في المدرسة قال المعلم مرحبا",
        ]:
            self.assertFalse(self.blocked(t, "ar" if "المدرسة" in t else "en"), t)

    def test_first_chunks_are_not_held_for_ordinary_text(self):
        async def first():
            g = sg.guard_attribution_stream(agen(["Oh nice, ", "that sounds fun. ", "Tell me more"]), lambda: False)
            return await g.__anext__()
        self.assertTrue(run(first()).startswith("Oh nice"))

    def test_regex_ranges_are_written_as_escapes(self):
        import inspect
        src = inspect.getsource(sg)
        for ch in ("\ufd3e", "\ufd3f", "\u06d6", "\u0615", "\ufdfa", "\u064b"):
            self.assertNotIn(ch, src)

    # review follow-up #1: the \u064a-noun exclusion had no end anchor, so it matched a prefix
    # of a longer word and let real imperfect verbs through ("\u064a\u062a\u064a\u0645\u0645" tayammum, "\u064a\u062a\u064a\u0645\u0646",
    # "\u064a\u0645\u0646\u064a\u0647\u0645" / "\u064a\u0645\u0646\u064a\u0647" he-gives-false-hope-to-them/him).
    def test_y_initial_exclusion_stays_allowed_only_for_the_whole_word(self):
        for t in (
            "\u0627\u0646 \u0627\u0644\u0646\u0628\u064a \u0643\u0627\u0646 \u064a\u062a\u064a\u0645\u0627",
            "\u0627\u0646 \u0627\u0644\u0646\u0628\u064a \ufdfa \u0643\u0627\u0646 \u064a\u062a\u064a\u0645\u0627 \u0641\u064a \u0635\u063a\u0631\u0647",
            "\u0627\u0646 \u0627\u0644\u0646\u0628\u064a \u0643\u0627\u0646 \u064a\u0642\u064a\u0646\u0627",
            "\u0627\u0646 \u0627\u0644\u0646\u0628\u064a \u0643\u0627\u0646 \u064a\u0647\u0648\u062f\u064a\u0627",
            "\u0627\u0646 \u0627\u0644\u0646\u0628\u064a \u0643\u0627\u0646 \u064a\u0645\u0646\u064a\u0627",
        ):
            self.assertIsNone(sg.find_attribution(t), t)

    def test_y_initial_words_sharing_the_exclusion_prefix_are_still_caught(self):
        for t in (
            "\u0627\u0646 \u0627\u0644\u0646\u0628\u064a \u0643\u0627\u0646 \u064a\u062a\u064a\u0645\u0645 \u0643\u0630\u0627",     # tayammum, a real imperfect verb, not "\u064a\u062a\u064a\u0645" (orphan)
            "\u0627\u0646 \u0627\u0644\u0646\u0628\u064a \ufdfa \u0643\u0627\u0646 \u064a\u062a\u064a\u0645\u0646 \u0643\u0630\u0627",
            "\u0627\u0646 \u0627\u0644\u0646\u0628\u064a \u0643\u0627\u0646 \u064a\u0645\u0646\u064a\u0647\u0645 \u0643\u0630\u0627",    # "\u064a\u064f\u0645\u064e\u0646\u0651\u064a" + them, not "\u064a\u0645\u0646\u064a" (Yemeni)
            "\u0627\u0646 \u0627\u0644\u0646\u0628\u064a \u0643\u0627\u0646 \u064a\u0645\u0646\u064a\u0647 \u0643\u0630\u0627",     # "\u064a\u064f\u0645\u064e\u0646\u0651\u064a" + him
        ):
            self.assertIsNotNone(sg.find_attribution(t), t)
            self.assertTrue(self.blocked(t, "ar"), t)

    # review follow-up #2: "\u0644\u0623\u0646/\u0628\u0623\u0646/\u0648\u0623\u0646/\u0641\u0625\u0646 \u0627\u0644\u0646\u0628\u064a|\u0631\u0633\u0648\u0644 \u0627\u0644\u0644\u0647 ..." leak on the live
    # (streaming) path. The whole-string regex already matches ("\u0644\u0623\u0646" normalises to
    # "\u0644\u0627\u0646", which contains "\u0627\u0646" as a literal substring right before "\u0627\u0644\u0646\u0628\u064a"), but
    # token-by-token the proclitic word "\u0644\u0627\u0646" was neither a strong word nor a known
    # _LEADS prefix, so it used to be spoken immediately, and the remaining tail
    # ("\u0627\u0644\u0646\u0628\u064a \u0643\u0627\u0646 \u064a\u062d\u0628 \u0643\u0630\u0627") no longer matched the "\u0627\u0646 \u0627\u0644\u0646\u0628\u064a ..." patterns on its own.
    def test_proclitic_lead_ins_need_a_source(self):
        cases = [
            "\u0644\u0623\u0646 \u0627\u0644\u0646\u0628\u064a \ufdfa \u0643\u0627\u0646 \u064a\u062d\u0628 \u0643\u0630\u0627",
            "\u0628\u0623\u0646 \u0627\u0644\u0646\u0628\u064a \u0643\u0627\u0646 \u064a\u062d\u0628 \u0643\u0630\u0627",
            "\u0648\u0623\u0646 \u0627\u0644\u0646\u0628\u064a \u0643\u0627\u0646 \u064a\u062d\u0628 \u0643\u0630\u0627",
            "\u0641\u0625\u0646 \u0627\u0644\u0646\u0628\u064a \u0643\u0627\u0646 \u064a\u062d\u0628 \u0643\u0630\u0627",
            "\u0644\u0623\u0646 \u0631\u0633\u0648\u0644 \u0627\u0644\u0644\u0647 \u0643\u0627\u0646 \u064a\u062d\u0628 \u0643\u0630\u0627",
            "\u0644\u0627\u0646 \u0627\u0644\u0646\u0628\u064a \u0646\u0647\u0649 \u0639\u0646 \u0643\u0630\u0627",       # the older "\u0627\u0646 \u0627\u0644\u0646\u0628\u064a + teaching verb" rule
            "\u0628\u0623\u0646 \u0627\u0644\u0646\u0628\u064a \u0641\u0639\u0644 \u0643\u0630\u0627",
        ]
        for t in cases:
            self.assertIsNotNone(sg.find_attribution(t), t)
            self.assertTrue(self.blocked(t, "ar"), t)
            decline = sg.DECLINE_TEXT["ar"].split(".")[0]
            # nothing at all is spoken before the decline, not even the bare proclitic letter
            for n in (1, 2, 3, 5, 8, 100):
                out = self.stream_out(self.split(t, n), "ar")
                self.assertIn(decline, out, (t, n, out))
                self.assertEqual(out.split(decline)[0].strip(), "", (t, n, out))
            words = t.split(" ")
            for tokens in (
                [w + " " for w in words],
                [" " + w for w in words],
            ):
                self.assertTrue(self.blocked_tokens(tokens), (t, tokens))
                out = self.stream_out(tokens, "ar")
                self.assertEqual(out.split(decline)[0].strip(), "", (t, tokens, out))

    def test_ordinary_text_starting_with_the_proclitic_is_not_held_or_cut(self):
        # "\u0644\u0627\u0646" ("because") is a very ordinary word; it must only be held while the next
        # word could still complete a lead phrase, not indefinitely.
        for tokens in (
            ["\u0644\u0627\u0646 ", "\u0627\u0644\u062c\u0648 ", "\u062d\u0627\u0631 ", "\u0627\u0644\u064a\u0648\u0645 ", "\u0641\u0644\u0646\u0628\u0642 ", "\u0641\u064a ", "\u0627\u0644\u0628\u064a\u062a"],
            ["\u0644\u0627\u0646 ", "\u0627\u0644\u0627\u0643\u0644 ", "\u0644\u0630\u064a\u0630 "],
        ):
            out = self.stream_out(tokens, "ar")
            self.assertEqual(out, "".join(tokens), tokens)
            self.assertNotIn(sg.DECLINE_TEXT["ar"].split(".")[0], out, tokens)

    # ---- review round: the guard reads RAW model tokens, not words. o200k_base splits an Arabic
    # word below word level (" ي" + "تي" + "ما" for «يتيما»), so a ي-word is decided only once it is
    # whole; until then it is held. These tests stream the real o200k splits (hard-coded in
    # _O200K_SPLITS, checked against tiktoken when it is installed), characters and words.
    Y_ALLOWED = (
        "كان النبي يتيما في صغره",
        "النبي ﷺ كان يتيما",
        "كان النبي ﷺ يتيما في صغره",
        "ان النبي كان يتيما في صغره",
        "ان النبي ﷺ كان يتيما في صغره",
        "كان النبي يقينا",
        "النبي كان يهوديا",
        "كان النبي يمنيا",
        "النبي ﷺ كان يتيما فقيرا",
        "كان النبي يوسف عليه السلام يحب اباه",
        "كان النبي يعقوب حزينا",
        "كان النبي يونس صابرا",
        "كان النبي يوشع قائدا",
        "كان النبي يحيى عليه السلام بارا كذا",
        "كان النبي يحيى بن زكريا بارا كذا",
        "كان النبي يحيى ابن زكريا بارا كذا",
        "النبي يعقوب كان حزينا",
        "مرحبا يا صديقي، كان النبي يتيما في صغره وكان جده يرعاه.",
    )
    Y_CLAIMS = (
        "كان النبي يحب كذا",
        "النبي ﷺ كان يحب كذا",
        "كان النبي يحيي كذا",
        "ان النبي كان يحب كذا",
        "النبي ﷺ كان يبتسم دائما",
        "كان النبي ﷺ يتيمم كذا",
        "كان النبي لا يحب كذا",
        "كان النبي اذا غضب كذا",
        "كان رسول الله ﷺ يحب كذا",
        "رسول الله ﷺ كان يحب كذا",
        "ان رسول الله كان يحب كذا",
        "كان النبي يحيى كذا",
        "النبي -صلى الله عليه وسلم- قال كذا",
        "النبي ﷺ فعل كذا",
        "ان النبي ﷺ فعل كذا",
        # review round 2: «يحيي» + «ابن/بن» that is NOT «ابن زكريا» is the verb "greets" (his daughter, his
        # cousin ...). The real o200k split is ' ي','حي','ي',' ابن','ته': the subject must not leave
        # the hold while «ابن» is only partial
        "كان رسول الله صلى الله عليه وآله وسلم يحيي ابنته كذا",
        "النبي، صلى الله عليه وآله وسلم، كان يحيي ابنته كذا",
        "كان رسول الله صلى الله عليه وآله وسلم يحيي بناته كذا",
        "رسول الله ، صلى الله عليه وسلم، كان يحيي ابنه كذا",
        "كان رسول الله صلى الله عليه وسلم يحيي ابناءه كذا",
        "كان النبي يحيي ابن عمه كذا",
        "كان النبي يحيي ابن آدم كذا",
        "كان النبي يحيي -ابن- كذا",
        "كان النبي يحيي عليه السلامة كذا",
        "كان النبي يحيي بن عمه كذا",
        # the glued dashes (no space around the blessing) and the glued «ونبي/فنبي»
        "النبي-صلى الله عليه وسلم-قال كذا",
        "كان النبي-صلى الله عليه وسلم-يحب كذا",
        "ان النبي-صلى الله عليه وسلم-نهى عن كذا",
        "النبي-صلى الله عليه وسلم- قال كذا",
        "النبي—ﷺ—كان يحب كذا",
        "ونبي الله ﷺ كان يحب كذا",
        "فنبي الله ﷺ كان يحب كذا",
        # the Quran and «قال» rules take the same separators between their words
        "الله -عز وجل- يقول كذا",
        "الله - عز وجل - يقول كذا",
        "الله (عز وجل) يقول كذا",
        "الله، عز وجل، يقول كذا",
        "الله —سبحانه وتعالى— يأمرنا بكذا",
        "قال -صلى الله عليه وسلم-: كذا",
        "قال (صلى الله عليه وسلم): كذا",
        "وقال -عليه الصلاة والسلام-: كذا",
    )
    # the same, English: decided by the English rules and declined with the English text
    EN_CLAIMS = (
        "The Prophet—peace be upon him—said PLACEHOLDER.",
        "The Prophet-peace be upon him-said PLACEHOLDER.",
        "Our Prophet—peace be upon him—taught PLACEHOLDER.",
        "Allah - the Almighty - says PLACEHOLDER.",
    )
    # more allowed texts that must come out whole: the dash separators and the new strong starts must
    # not turn ordinary sentences into claims, nor hold them back
    MORE_ALLOWED = (
        "كان النبي -ﷺ- كريما - وكان رحيما",
        "The well-known prophets were kind - very kind.",
    )

    def streams_of(self, t):
        """Every way the tests feed one text: real o200k tokens, characters, words, sub-word pieces."""
        words = t.split(" ")
        streams = []
        if t in _O200K_SPLITS:
            streams.append(("o200k", _O200K_SPLITS[t]))
        streams += [("chars%d" % n, self.split(t, n)) for n in (1, 2, 3, 5, 8, 100)]
        streams += [("words", [w + " " for w in words]), ("words-lead-space", [" " + w for w in words])]
        # a made-up sub-word split in the shape of o200k: 1 letter, 2 letters, the rest of each word
        sub = []
        for k, w in enumerate(words):
            lead = " " if k else ""
            sub += [lead + w[:1], w[1:3], w[3:]]
        streams.append(("subword", [x for x in sub if x]))
        return streams

    def test_o200k_splits_are_the_ones_the_reviewer_saw(self):
        # guards the fixture itself: the ي-word really does arrive in pieces
        self.assertEqual(_O200K_SPLITS["كان النبي يتيما في صغره"][:5], ["كان", " النبي", " ي", "تي", "ما"])
        self.assertEqual(_O200K_SPLITS["ان النبي كان يتيما في صغره"][:6], ["ان", " النبي", " كان", " ي", "تي", "ما"])
        # the reviewer's repro, token for token: «ابن» arrives before «ته»
        self.assertEqual(
            _O200K_SPLITS["كان رسول الله صلى الله عليه وآله وسلم يحيي ابنته كذا"][9:15],
            [" ي", "حي", "ي", " ابن", "ته", " ك"])
        for t in self.Y_ALLOWED[:-1] + self.Y_CLAIMS + self.EN_CLAIMS + self.MORE_ALLOWED:
            self.assertIn(t, _O200K_SPLITS, t)
            self.assertEqual("".join(_O200K_SPLITS[t]), t)

    def test_o200k_splits_match_tiktoken_when_it_is_installed(self):
        try:
            import tiktoken
            enc = tiktoken.get_encoding("o200k_base")
        except Exception as exc:  # not installed in the image, or no network for the vocabulary
            self.skipTest(
                "tiktoken / o200k_base unavailable (%r): the o200k splits stay hard-coded in "
                "_O200K_SPLITS (produced with tiktoken 0.14.0) and the stream tests still use them" % (exc,))
        import codecs
        for t, expected in _O200K_SPLITS.items():
            dec = codecs.getincrementaldecoder("utf-8")()
            got = [dec.decode(enc.decode_single_token_bytes(i)) for i in enc.encode(t)]
            self.assertEqual(got, expected, t)

    def test_y_words_split_by_o200k_are_never_cut_mid_word(self):
        for t in self.Y_ALLOWED + self.MORE_ALLOWED:
            self.assertIsNone(sg.find_attribution(t), t)
            self.assertIsNone(sg.find_attribution(t, frozenset({"quran"})), t)
            for label, tokens in self.streams_of(t):
                out = self.stream_out(tokens)
                self.assertEqual(out, "".join(tokens), (t, label, tokens, out))

    def test_claims_split_by_o200k_decline_and_nothing_of_the_claim_is_spoken(self):
        for claims, lang in ((self.Y_CLAIMS, "ar"), (self.EN_CLAIMS, "en")):
            decline = sg.DECLINE_TEXT[lang].split(".")[0]
            for t in claims:
                self.assertIsNotNone(sg.find_attribution(t), t)
                self.assertIsNone(sg.find_attribution(t, frozenset({"hadith", "quran"})), t)
                for label, tokens in self.streams_of(t):
                    out = self.stream_out(tokens, lang)
                    self.assertIn(decline, out, (t, label, tokens, out))
                    self.assertIn(out.split(decline)[0].strip(), ("", "و"), (t, label, tokens, out))  # a lone proclitic «و» may precede

    def test_a_partial_y_word_is_undecided_and_the_whole_word_decides(self):
        decline = sg.DECLINE_TEXT["ar"].split(".")[0]
        # live: a ي-word touching the end of the text is not a claim yet, the final rule says it is
        for t in ("كان النبي يتي", "النبي ﷺ كان ي", "ان النبي كان يتيم", "كان النبي يحب", "النبي كان يتيمم",
                  "كان النبي اذا", "النبي فعل", "ان النبي فعل", "ان النبي كان يتيما"):
            self.assertIsNone(sg.find_attribution(t, final=False), t)
        for t in ("كان النبي يتي", "النبي ﷺ كان ي", "كان النبي يحب", "النبي كان يتيمم", "النبي فعل"):
            if t.endswith(" ي"):
                continue  # one letter is not a verb yet, in either mode
            self.assertIsNotNone(sg.find_attribution(t), t)
        # once the word completes (a non-letter follows) the live rule decides like the final rule
        for t, claim in (
            ("كان النبي يتيما ", False), ("كان النبي يتيمم ", True), ("كان النبي يحب ", True),
            ("ان النبي كان يتيما ", False), ("ان النبي كان يحب ", True), ("النبي فعلا ", False),
            ("النبي فعل ", True), ("كان النبي اذا ", True), ("كان النبي يوسف ", False),
        ):
            live = sg.find_attribution(t, final=False)
            self.assertEqual(live is not None, claim, t)
            self.assertEqual((sg.find_attribution(t) is not None), claim, t)
        # the old failure, token for token (d32f31e declined this one mid-word)
        tokens = ["ان", " النبي", " كان", " ي", "تي", "ما", " في", " ص", "غ", "ره"]
        self.assertEqual(self.stream_out(tokens), "".join(tokens))
        # a verb that is only a verb once it is whole: «يتيم» + «م»
        self.assertTrue(self.blocked_tokens(["كان", " النبي", " ي", "تي", "م", "م", " كذا"]))
        self.assertTrue(self.blocked_tokens(["كان", " النبي", " ي", "حب", " كذا"]))
        # a claim that ends the reply on a partial-looking word is still caught at the end
        self.assertTrue(self.blocked_tokens(["كان", " النبي", " ي", "حب"]))
        self.assertIn(decline, self.stream_out(["النبي", " ﷺ", " كان", " ي", "بتسم"]))

    def test_stream_decision_equals_the_final_decision_for_every_chunking(self):
        # differential: for a complete text, the streamed outcome is the final outcome whatever the
        # chunking. Allowed texts come out whole, claims come out as the text before the claim
        # followed by the decline; only the timing of the decision depends on the chunking.
        decline = sg.DECLINE_TEXT["ar"].split(".")[0]
        texts = list(self.Y_ALLOWED[:-1]) + list(self.Y_CLAIMS) + list(self.FIRST_ORDERS)
        subjects = ("النبي", "رسول الله")
        # blessings long enough to push the subject out of a 7-word hold window, with commas, dashes
        blessings = ("", "ﷺ", "صلى الله عليه وسلم", "صلى الله عليه وآله وسلم", "، صلى الله عليه وسلم،",
                     "عليه الصلاة والسلام", "-صلى الله عليه وسلم-", "-صلى الله عليه وآله وسلم-")
        verbs = ("يحب", "يتيما", "يتيمم", "يقينا", "يهوديا", "يمنيهم", "يوسف", "يعقوب عليه السلام",
                 "يحيى عليه السلام", "يحيى ابن زكريا", "يحيى بن زكريا", "يحيى كذا", "فعل", "فعلا", "رحيما",
                 "اذا غضب", "لا يحب", "ي",
                 # «يحيي» + a partial or a wrong marker is the verb "greets": the subject stays held
                 "يحيي ابنته", "يحيي بناته", "يحيي ابنه", "يحيي ابناءه", "يحيي ابن عمه", "يحيي ابن آدم",
                 "يحيي ابن", "يحيي بن", "يحيي ابن زكريا", "يحيي عليه السلامة")
        for s in subjects:
            for b in blessings:
                for v in verbs:
                    texts += [f"كان {s} {b} {v} كذا", f"{s} {b} كان {v} كذا", f"ان {s} {b} كان {v} كذا"]
        texts += ["ان النبي فعلا قدوة لنا", "كان الجو جميلا اليوم", "كان محمد يلعب في الحديقة",
                  "ان النبي كان رحيما بالناس", "هل كان", "كان النبيل يحب كذا"]
        for t in texts:
            pos = sg.find_attribution(t)
            for label, tokens in self.streams_of(t):
                out = self.stream_out(tokens)
                if pos is None:
                    self.assertEqual(out, "".join(tokens), (t, label, out))
                else:
                    self.assertIn(decline, out, (t, label, out))
                    self.assertEqual(out.split(decline)[0].strip(), t[:pos].strip(), (t, label, out))

    # review: a blessing between dashes is a gap like a comma or a bracket was ("النبي -صلى الله عليه
    # وسلم- قال كذا" used to pass untouched). Hyphen, en dash and em dash, in every rule that has a gap.
    DASHES = ("-", chr(0x2013), chr(0x2014))

    def test_dash_wrapped_blessing_is_a_gap_in_every_rule_shape(self):
        for d in self.DASHES:
            for t in (
                f"النبي {d}صلى الله عليه وسلم{d} قال كذا",
                f"النبي {d} صلى الله عليه وسلم {d} قال كذا",
                f"النبي {d}ﷺ{d} قال كذا",
                f"النبي {d} قال كذا",
                f"رسول الله {d}صلى الله عليه وسلم{d} يقول كذا",
                f"ان النبي {d}صلى الله عليه وسلم{d} نهى عن كذا",
                f"ان النبي {d}صلى الله عليه وسلم{d} كان يحب كذا",
                f"ان النبي كان {d}صلى الله عليه وسلم{d} يحب كذا",
                f"ان النبي {d}صلى الله عليه وسلم{d} فعل كذا",
                f"لأن النبي {d}صلى الله عليه وسلم{d} كان يحب كذا",
                f"كان النبي {d}صلى الله عليه وسلم{d} يحب كذا",
                f"كان النبي {d}صلى الله عليه وسلم{d} اذا غضب كذا",
                f"وكان رسول الله {d}ﷺ{d} لا يحب كذا",
                f"النبي {d}صلى الله عليه وسلم{d} كان يحب كذا",
                f"النبي {d}صلى الله عليه وسلم{d} كان اذا غضب كذا",
                f"النبي {d}صلى الله عليه وسلم{d} فعل كذا",
                f"والنبي {d}ﷺ{d} كان يحب كذا",
                # the dash touching the subject and the next word: one whitespace-free "word" for the
                # old splitter, so the subject left the hold before the gap was complete
                f"النبي{d}صلى الله عليه وسلم{d}قال كذا",
                f"النبي{d}صلى الله عليه وسلم{d} قال كذا",
                f"كان النبي{d}صلى الله عليه وسلم{d}يحب كذا",
                f"ان النبي{d}صلى الله عليه وسلم{d}نهى عن كذا",
                f"النبي{d}ﷺ{d}كان يحب كذا",
                f"رسول الله{d}ﷺ{d}يقول كذا",
                f"ونبي الله {d}ﷺ{d} كان يحب كذا",
                f"فنبي الله {d}ﷺ{d} كان يحب كذا",
                # the Quran and «قال» rules, which do not use the blessing gap, take the separators too
                f"الله {d}عز وجل{d} يقول كذا",
                f"الله {d} عز وجل {d} يقول كذا",
                f"الله{d}سبحانه وتعالى{d}يأمرنا بكذا",
                f"قال {d}صلى الله عليه وسلم{d}: كذا",
                f"وقال {d}عليه الصلاة والسلام{d}: كذا",
            ):
                self.assertIsNotNone(sg.find_attribution(t), t)
                self.assertIsNone(sg.find_attribution(t, frozenset({"hadith", "quran"})), t)
                self.assertTrue(self.blocked(t, "ar"), t)
                self.assert_nothing_spoken_before_decline(t)
                for label, tokens in self.streams_of(t):
                    out = self.stream_out(tokens)
                    decline = sg.DECLINE_TEXT["ar"].split(".")[0]
                    self.assertIn(decline, out, (t, label, out))
                    self.assertIn(out.split(decline)[0].strip(), ("", "و"), (t, label, out))
            for t in (
                f"The Prophet {d}peace be upon him{d} said PLACEHOLDER.",
                f"The Prophet {d} peace be upon him {d} said PLACEHOLDER.",
                f"Prophet Muhammad {d}peace be upon him{d} taught PLACEHOLDER.",
                f"Our Prophet {d} said PLACEHOLDER.",
                f"The Prophet{d}peace be upon him{d}said PLACEHOLDER.",
                f"Our Prophet{d}peace be upon him{d}taught PLACEHOLDER.",
                f"Allah {d} the Almighty {d} says PLACEHOLDER.",
                f"Allah{d}the Almighty{d}says PLACEHOLDER.",
            ):
                self.assertIsNotNone(sg.find_attribution(t), t)
                self.assertTrue(self.blocked(t, "en"), t)
                decline = sg.DECLINE_TEXT["en"].split(".")[0]
                for label, tokens in self.streams_of(t):
                    out = self.stream_out(tokens, "en")
                    self.assertIn(decline, out, (t, label, out))
                    self.assertEqual(out.split(decline)[0].strip(), "", (t, label, out))

    def test_dash_gap_does_not_turn_ordinary_text_into_a_claim(self):
        for t in (
            "النبي - رحيم بالاطفال",
            "كان النبي - رحيما",
            f"النبي {chr(0x2013)}ﷺ{chr(0x2013)} كان رحيما",
            "ان النبي -ﷺ- كان يتيما في صغره",
            "كان النبي -صلى الله عليه وسلم- يتيما",
            "النبي -ﷺ- هو خاتم الانبياء",
            "كان النبي -ﷺ- كريما - وكان رحيما",
            "The prophets are well-known - great people.",
        ):
            self.assertIsNone(sg.find_attribution(t), t)
            for label, tokens in self.streams_of(t):
                self.assertEqual(self.stream_out(tokens, "ar"), "".join(tokens), (t, label))

    # punctuation between the subject and the say-verb is a gap like a comma or a dash
    PUNCT_EN = [
        "The Prophet: of Allah said PLACEHOLDER.",
        "The Prophet! of Allah said PLACEHOLDER.",
        "The Prophet\uff01 of Allah said PLACEHOLDER.",
        "The Prophet\uff1a of Allah said PLACEHOLDER.",
        "The Prophet? of Allah said PLACEHOLDER.",
        "The Prophet\uff1f of Allah said PLACEHOLDER.",
        "The Prophet; of Allah said PLACEHOLDER.",
        "The Prophet\uff1b of Allah said PLACEHOLDER.",
        "The Prophet. of Allah said PLACEHOLDER.",
        "The Prophet\uff0e of Allah said PLACEHOLDER.",
        "The Prophet\uff0c of Allah said PLACEHOLDER.",
        "The Prophet\u2026 of Allah said PLACEHOLDER.",
        "The Prophet: said PLACEHOLDER.",
        "Allah: says PLACEHOLDER.",
    ]
    PUNCT_AR = [
        "النبي: قال كذا",
        "النبي، صلى الله عليه وسلم، قال كذا",
        "النبي\u061b قال كذا",
        "النبي\u061f قال كذا",
        "النبي\uff1a قال كذا",
        "النبي\uff01 قال كذا",
        "النبي\u2026 قال كذا",
        "الله: يقول كذا",
    ]

    def test_punctuation_between_the_subject_and_the_verb_is_declined(self):
        for t in self.PUNCT_EN:
            self.assertIsNotNone(sg.find_attribution(t), t)
            self.assertIsNone(sg.find_attribution(t, frozenset({"hadith", "quran"})), t)
            self.assertTrue(self.blocked(t, "en"), t)   # every chunking, nothing of the claim spoken
        for t in self.PUNCT_AR:
            self.assertIsNotNone(sg.find_attribution(t), t)
            self.assertTrue(self.blocked(t, "ar"), t)
        # the plain forms stay declined, as before
        for t in ("The Prophet of Allah said PLACEHOLDER.", "the Prophet said PLACEHOLDER.",
                  "النبي قال كذا"):
            self.assertIsNotNone(sg.find_attribution(t), t)

    def test_a_colon_in_a_plain_sentence_passes_untouched(self):
        for t, lang in (
            ("Here is my list: honesty, kindness and patience!", "en"),
            ("The prophets are great: they were kind. Right?", "en"),
            ("Note: Allah loves kind children. Why? Because kindness matters.", "en"),
            ("عندي سؤال: هل تحب الكرة؟ نعم، احبها", "ar"),
        ):
            self.assertIsNone(sg.find_attribution(t), t)
            for label, tokens in self.streams_of(t):
                self.assertEqual(self.stream_out(tokens, lang), "".join(tokens), (t, label))

    def test_yahya_marker_ibn_as_well_as_bn(self):
        for t in ("كان النبي يحيى ابن زكريا بارا كذا", "كان النبي يحيى بن زكريا بارا كذا",
                  "النبي يحيى ابن زكريا كان بارا", "كان النبي يحيى (ابن زكريا) بارا"):
            self.assertIsNone(sg.find_attribution(t), t)
        # only «ابن/بن زكريا» (Yahya's one father) is the marker: «يحيي ابن عمه» greets his cousin
        for t in ("كان النبي يحيي ابنه كذا", "كان النبي يحيي كذا", "كان النبي يحيى ابنا كذا",
                  "كان النبي يحيي ابن عمه كذا", "كان النبي يحيي ابن آدم كذا", "كان النبي يحيي -ابن- كذا",
                  "كان النبي يحيي بن عمه كذا", "كان النبي يحيي ابنته كذا", "كان النبي يحيي بناته كذا",
                  "كان النبي يحيي ابناءه كذا", "كان النبي يحيي ابن", "كان النبي يحيي بن ",
                  "كان النبي يحيي ابن زكر كذا"):
            self.assertIsNotNone(sg.find_attribution(t), t)
            self.assertIsNone(sg.find_attribution(t, frozenset({"hadith"})), t)

    def test_yahya_marker_that_is_still_partial_holds_the_subject_back(self):
        # the partial marker is undecided while it grows: «يحيي» + «ابن» + «ته» must not release the
        # subject (review round 2: the c6b87fa wrapper spoke these whole, only the false cut at the
        # partial «يحي» had caught them before)
        for t in ("كان رسول الله صلى الله عليه وآله وسلم يحيي ابنته كذا",
                  "كان رسول الله صلى الله عليه وآله وسلم يحيي بناته كذا",
                  "النبي، صلى الله عليه وآله وسلم، كان يحيي ابنته كذا"):
            start = t.index("يحيي")
            # every split point of the two-token stream, through «يحيي» + «ابن» + «ته»
            for cut in range(start, start + 20):
                self.assertTrue(self.blocked_tokens([t[:cut], t[cut:]]), (t, cut))
        # live: the partial marker is undecided, the complete name is not a claim, a wrong marker is one
        for t in ("كان النبي يحيي ابن", "كان النبي يحيي ابن ز", "كان النبي يحيي ابن زكري", "كان النبي يحيي بن ",
                  "كان النبي يحيي عليه السلا", "كان النبي يحيي "):
            self.assertIsNone(sg.find_attribution(t, final=False), t)
            self.assertIsNotNone(sg.find_attribution(t), t)
        for t in ("كان النبي يحيي ابنته", "كان النبي يحيي ابن عمه", "كان النبي يحيي بناته "):
            self.assertIsNotNone(sg.find_attribution(t, final=False), t)
        # the name itself, in every spelling, is spoken whole at every chunking
        for t in ("كان النبي يحيى بن زكريا بارا كذا", "كان النبي يحيى ابن زكريا بارا كذا",
                  "كان النبي يحيى -ابن زكريا- بارا", "كان النبي يحيى (بن زكريا) بارا",
                  "كان النبي يحيى عليه السلام بارا"):
            self.assertIsNone(sg.find_attribution(t), t)
            for label, tokens in self.streams_of(t):
                self.assertEqual(self.stream_out(tokens), "".join(tokens), (t, label))

    def test_long_blessing_then_negation_is_held_until_the_decline(self):
        # found by the differential test: "رسول الله صلى الله عليه وسلم كان لا يحب كذا" has 8 words
        # before the verb; the negation broke the run of held gap words, the subject left the hold
        # window and a character-level stream spoke the whole claim
        for t in (
            "رسول الله صلى الله عليه وسلم كان لا يحب كذا",
            "كان رسول الله صلى الله عليه وسلم لم يفعل كذا",
            "رسول الله صلى الله عليه وسلم كان قد يغضب كذا",
            "ان رسول الله صلى الله عليه وسلم كان ما يفعل كذا",
        ):
            self.assertIsNotNone(sg.find_attribution(t), t)
            self.assert_nothing_spoken_before_decline(t)

    # final review, pre-existing fail-open: a long English blessing followed by "used to say" / "would say"
    # pushed the subject out of the 7-word hold window ("used", "to", "would" were not hold gap words), so
    # a streamed reply spoke "The Prophet, peace and blessings be upon him," before the verb arrived.
    EN_LONG_BLESSING_CLAIMS = (
        "The Prophet, peace and blessings be upon him, used to say PLACEHOLDER.",
        "The Prophet, peace and blessings be upon him, would say PLACEHOLDER.",
        "Our Prophet, peace and blessings of Allah be upon him, used to say PLACEHOLDER.",
        "Our Prophet, may Allah bless him and grant him peace, would say PLACEHOLDER.",
        "The Prophet, peace and blessings be upon him, used to tell PLACEHOLDER.",
        "The Prophet, peace and blessings be upon him, used to teach PLACEHOLDER.",
        "The Prophet, peace and blessings be upon him, would often say PLACEHOLDER.",
        "The Prophet, peace and blessings be upon him, would usually say PLACEHOLDER.",
        "The Messenger, peace and blessings be upon him, used to also say PLACEHOLDER.",
        "The Prophet used to always tell PLACEHOLDER.",
        "The Prophet sometimes said PLACEHOLDER.",
        "The Prophet, peace and blessings be upon him, always used to say PLACEHOLDER.",
        "The Prophet, peace and blessings be upon him, once would say PLACEHOLDER.",
    )

    def test_english_long_blessing_then_used_to_or_would_is_held_until_the_decline(self):
        decline = sg.DECLINE_TEXT["en"].split(".")[0]
        for t in self.EN_LONG_BLESSING_CLAIMS:
            self.assertIsNotNone(sg.find_attribution(t), t)
            self.assertIsNone(sg.find_attribution(t, frozenset({"hadith"})), t)
            self.assertTrue(self.blocked(t, "en"), t)  # chunk sizes 1, 2, 3, 5, 8, 100
            words = t.split(" ")
            streams = [("words", [w + " " for w in words]), ("words-lead-space", [" " + w for w in words])]
            sub = []
            for k, w in enumerate(words):
                sub += [(" " if k else "") + w[:2], w[2:]]
            streams.append(("subword", [x for x in sub if x]))
            for label, tokens in streams:
                out = self.stream_out(tokens, "en")
                self.assertIn(decline, out, (t, label, out))
                self.assertEqual(out.split(decline)[0].strip(), "", (t, label, out))

    def test_english_hold_words_do_not_hold_ordinary_text(self):
        # "used", "to" and "would" are hold gap words only behind a subject; everywhere else they pass at once
        for t in (
            "I used to play outside and I would go to the park to run.",
            "We want to be kind to everyone and we would like to help.",
            "The prophets are in the stories we read, and we used to talk about them.",
            "The Prophet is a role model, and we try to be like him.",
        ):
            self.assertIsNone(sg.find_attribution(t), t)
            for n in (1, 2, 3, 5, 8, 100):
                tokens = self.split(t, n)
                self.assertEqual(self.stream_out(tokens, "en"), t, (t, n))
        # the hold is short: the first chunks of ordinary text are not held back
        async def first():
            g = sg.guard_attribution_stream(
                agen(["I used to ", "like to swim, ", "and I would go to the pool"]), lambda: False)
            return await g.__anext__()
        self.assertTrue(run(first()).startswith("I used to"))

    # final review, pre-existing fail-open: «قال» + a divine name written between dashes or brackets
    # ("قال -تعالى-: ...") was not the Quran rule, which wanted plain whitespace after «قال»
    QAL_QURAN_CLAIMS = (
        "قال -تعالى-: كذا",
        "قال (تعالى): كذا",
        "قال —تعالى—: كذا",
        "قال –تعالى–: كذا",
        "وقال -تعالى-: كذا",
        "وقال (تعالى): كذا",
        "قال -سبحانه-: كذا",
        "قال (سبحانه): كذا",
        "قال —سبحانه—: كذا",
        "قال -عز وجل-: كذا",
        "قال (عز وجل): كذا",
        "قال —عز وجل—: كذا",
        "وقال -عز وجل-: كذا",
        "قال -جل وعلا-: كذا",
        "قال -جل جلاله-: كذا",
        "قال -تبارك وتعالى-: كذا",
        "قال - تعالى - : كذا",
        "قال -الله تعالى-: كذا",
        "قال، تعالى، كذا",
        "قال (الله): كذا",
        "قال -ربنا-: كذا",
        "قال -عز - وجل-: كذا",
    )

    def test_qal_quran_rule_takes_the_separators_between_qal_and_the_divine_name(self):
        for t in self.QAL_QURAN_CLAIMS:
            self.assertIsNotNone(sg.find_attribution(t), t)
            self.assertIsNone(sg.find_attribution(t, frozenset({"quran"})), t)  # a served verse licenses it
            self.assertIsNotNone(sg.find_attribution(t, frozenset({"hadith"})), t)  # a hadith does not
            self.assertTrue(self.blocked(t, "ar"), t)
            self.assert_nothing_spoken_before_decline(t)
            for label, tokens in self.streams_of(t):
                out = self.stream_out(tokens)
                decline = sg.DECLINE_TEXT["ar"].split(".")[0]
                self.assertIn(decline, out, (t, label, out))
                self.assertIn(out.split(decline)[0].strip(), ("", "و"), (t, label, out))

    def test_qal_quran_rule_still_leaves_an_ordinary_qal_alone(self):
        for t in (
            "قال لي صديقي كذا",
            "قال -صديقي- كذا",
            "قال (احمد): كذا",
            "قال - كذا",
            "قال الولد كذا",
            "قال عز الدين كذا",
            "قال جلال كذا",
            "قال تعلم كذا",
        ):
            self.assertIsNone(sg.find_attribution(t), t)
            for label, tokens in self.streams_of(t):
                self.assertEqual(self.stream_out(tokens), "".join(tokens), (t, label))

    # final review nit: «بنبينا» (glued ب) is a subject the final rule takes but was not a strong start
    def test_glued_b_on_our_prophet_is_held_and_declined_while_streaming(self):
        for t in (
            "بنبينا ﷺ كان يحب كذا",
            "بنبينا صلى الله عليه وسلم كان يحب كذا",
            "بنبينا ﷺ فعل كذا",
        ):
            self.assertIsNotNone(sg.find_attribution(t), t)
            self.assertTrue(self.blocked(t, "ar"), t)
            self.assert_nothing_spoken_before_decline(t)
            for label, tokens in self.streams_of(t):
                out = self.stream_out(tokens)
                decline = sg.DECLINE_TEXT["ar"].split(".")[0]
                self.assertIn(decline, out, (t, label, out))
                self.assertIn(out.split(decline)[0].strip(), ("", "ب"), (t, label, out))
        # the word alone, whole, ends the hold only once a non-claim word follows
        t = "اقتدينا بنبينا ﷺ في الرحمة"
        self.assertIsNone(sg.find_attribution(t), t)
        for label, tokens in self.streams_of(t):
            self.assertEqual(self.stream_out(tokens), "".join(tokens), (t, label))


class VerseMarkerTests(SimpleTestCase):
    def faq(self):
        return item(9, "faq", arabic_text="نص تجريبي {{verse:49:12}} ثم نص {{verse:9:108}} و {{verse:49:12}}",
                    english_text="PLACEHOLDER {{verse:2:256}}", translation_name="T",
                    title_en="t", child_explanation_en="e")

    def test_refs_extracted_in_order_without_duplicates(self):
        self.assertEqual(verse_refs(self.faq().arabic_text), ["49:12", "9:108"])
        self.assertEqual(verse_refs(""), [])

    def test_marker_replaced_by_a_citation_for_llm_context(self):
        self.assertEqual(replace_verse_markers("a {{verse:49:12}} b", "en"), "a (Surah Al-Hujurat 49:12) b")
        self.assertIn("(سورة الحجرات 49:12)", replace_verse_markers("{{verse:49:12}}", "ar"))

    def test_raw_marker_never_reaches_the_llm_block(self):
        for lang in ("en", "ar"):
            block = format_sources_block([self.faq()], lang)
            self.assertNotIn("{{", block)
            self.assertNotIn("verse:", block.replace("type=verse", ""))
        # the faq excerpt (and so its markers) is card-only now; markers elsewhere still become citations
        self.assertNotIn("تجريبي", format_sources_block([self.faq()], "ar"))
        self.assertNotIn("PLACEHOLDER", format_sources_block([self.faq()], "en"))

    def bank(self, *extra):
        """The faq plus the three bank verses its markers point at (placeholder audio)."""
        verses = [
            item(1, "verse", surah=49, ayah=12, arabic_text="نص تجريبي 1", audio_url="https://a.example/49012.mp3"),
            item(3, "verse", surah=9, ayah=108, arabic_text="نص تجريبي 3", audio_url="https://a.example/09108.mp3"),
            item(4, "verse", surah=2, ayah=256, arabic_text="نص تجريبي 4"),
        ]
        return ValueIndex.from_records([], [self.faq(), *verses, *extra], [])

    @staticmethod
    def strings(obj):
        if isinstance(obj, str):
            yield obj
        elif isinstance(obj, dict):
            for v in obj.values():
                yield from VerseMarkerTests.strings(v)
        elif isinstance(obj, (list, tuple)):
            for v in obj:
                yield from VerseMarkerTests.strings(v)

    def test_card_lists_refs_and_turns_markers_into_segments(self):
        idx = self.bank()
        card = card_payload(idx.items[9].obj, "en", None, idx)
        self.assertEqual(card["verse_refs"], ["49:12", "9:108"])
        segs = card["segments"]
        self.assertEqual([s["type"] for s in segs], ["text", "verse", "text", "verse", "text", "verse"])
        self.assertEqual(segs[0], {"type": "text", "text": "نص تجريبي "})
        self.assertEqual(segs[1], {
            "type": "verse", "surah": 49, "ayah": 12, "ref": "49:12", "item_key": "verse:49:12", "id": 1,
            "surah_name": "الحجرات", "audio_url": "https://a.example/49012.mp3"})
        self.assertEqual(segs[3]["audio_url"], "https://a.example/09108.mp3")
        self.assertEqual(segs[5]["ref"], "49:12")  # a repeated marker is a second segment
        # a bank verse is a reference and a recording, never text typed by us
        self.assertNotIn("arabic_text", segs[1])

    def test_faq_card_with_verse_segments_carries_the_recitation_credit(self):
        f = item(9, "faq", arabic_text="x {{verse:49:12}}")
        v = item(1, "verse", surah=49, ayah=12, arabic_text="نص",
                 audio_url="https://everyayah.com/data/Husary_128kbps/049012.mp3")
        idx = ValueIndex.from_records([], [f, v], [])
        card = card_payload(idx.items[9].obj, "en", None, idx)
        self.assertIn("everyayah.com", card["audio_credit"])
        self.assertEqual(card["audio_source_url"], "https://everyayah.com/")
        self.assertEqual(card["audio_url"], "")

    def test_card_without_markers_has_no_segments(self):
        idx = synthetic_index()
        self.assertEqual(card_payload(idx.items[4].obj, "en", None, idx)["segments"], [])
        self.assertEqual(card_payload(idx.items[1].obj, "en", None, idx)["segments"], [])

    def test_card_plain_text_fallback_is_the_reference_only(self):
        idx = self.bank()
        card = card_payload(idx.items[9].obj, "en", None, idx)
        self.assertEqual(card["arabic_text"],
                         "نص تجريبي (سورة الحجرات 49:12) ثم نص (سورة التوبة 9:108) و (سورة الحجرات 49:12)")
        self.assertEqual(card["english_text"], "PLACEHOLDER (Surah Al-Baqarah 2:256)")
        for text in self.strings({k: v for k, v in card.items() if k != "segments"}):
            self.assertNotIn("{", text)
            self.assertNotIn("}", text)

    def test_no_marker_is_left_in_the_card_text_fields(self):
        f = item(9, "faq", arabic_text="x {{verse:49:12}}", english_text="e {{verse:49:12}}", translation_name="T",
                 title_en="t {{verse:49:12}}", child_explanation_en="x {{verse:49:12}}",
                 disagreement_note_en="n {{verse:49:12}}", content_level="C")
        v = item(1, "verse", surah=49, ayah=12, arabic_text="نص")
        idx = ValueIndex.from_records([], [f, v], [])
        card = card_payload(idx.items[9].obj, "en", None, idx)
        for key in ("english_text", "title", "explanation", "disagreement_note"):
            self.assertTrue(card[key].endswith(" (Surah Al-Hujurat 49:12)"), (key, card[key]))
        self.assertNotIn("{{", "".join(self.strings({k: v for k, v in card.items() if k != "segments"})))

    def test_card_without_an_index_still_shows_no_braces(self):
        card = card_payload(self.faq(), "en", None, None)
        self.assertTrue(all(s["type"] == "text" for s in card["segments"]))
        self.assertIn("(سورة الحجرات 49:12)", "".join(s["text"] for s in card["segments"]))
        self.assertNotIn("{{", "".join(self.strings(card)))

    def test_a_marker_to_a_verse_outside_the_bank_excludes_the_item(self):
        gap = item(7, "faq", arabic_text="نص {{verse:1:2}} تجريبي", keywords_en=["zebra"], title_en="t")
        idx = ValueIndex.from_records([], [gap, item(1, "verse", surah=49, ayah=12, arabic_text="نص")], [])
        self.assertNotIn(7, idx.items)
        self.assertEqual(match_values("zebra", "en", None, idx), [])

    def test_the_exclusion_is_logged_without_text(self):
        gap = item(7, "faq", arabic_text="نص {{verse:1:2}} تجريبي", title_en="t")
        with self.assertLogs("conversation.agent.retrieval", "WARNING") as cm:
            ValueIndex.from_records([], [gap], [])
        self.assertIn("item=7", cm.output[0])
        self.assertIn("1:2", cm.output[0])
        self.assertNotIn("تجريبي", cm.output[0])

    def test_a_malformed_marker_excludes_the_item(self):
        bad = item(7, "faq", arabic_text="نص {{verse:abc}} تجريبي", keywords_en=["zebra"])
        idx = ValueIndex.from_records([], [bad], [])
        self.assertNotIn(7, idx.items)

    def test_markers_outside_the_arabic_and_english_text_are_still_cleaned_for_the_llm(self):
        f = item(9, "faq", arabic_text="نص", title_en="t {{verse:49:12}}", child_explanation_en="x {{verse:49:12}} y",
                 disagreement_note_en="n {{verse:49:12}}", content_level="C")
        block = format_sources_block([f], "en")
        self.assertNotIn("{", block)
        self.assertIn("(Surah Al-Hujurat 49:12)", block)

    def test_fallback_drops_malformed_markers_and_stray_braces(self):
        self.assertEqual(replace_verse_markers("a {{bad}} b } c { d", "en"), "a  b  c  d")

    def test_stray_braces_never_survive_into_text_segments(self):
        idx = self.bank()
        segs = text_segments("a { b {{verse:49:12}}} c", "en", idx)
        self.assertEqual([s["type"] for s in segs], ["text", "verse", "text"])
        self.assertEqual((segs[0]["text"], segs[2]["text"]), ("a  b ", " c"))
        for s in segs:
            self.assertNotIn("{", s.get("text", ""))
            self.assertNotIn("}", s.get("text", ""))
        self.assertEqual(text_segments("{ {{verse:49:12}} }", "en", idx)[0]["type"], "text")

    def test_verse_translation_stays_verbatim_on_the_card(self):
        v = item(1, "verse", surah=49, ayah=12, arabic_text="x {{verse:2:256}}",
                 english_text="PLACEHOLDER {{verse:2:256}} } {", translation_name="T")
        card = card_payload(v, "en")
        self.assertEqual(card["arabic_text"], "x {{verse:2:256}}")
        self.assertEqual(card["english_text"], "PLACEHOLDER {{verse:2:256}} } {")

    def test_verse_english_only_with_translation_name(self):
        v = item(1, "verse", surah=49, ayah=12, arabic_text="x", english_text="PLACEHOLDER TEXT", translation_name="")
        self.assertNotIn("PLACEHOLDER TEXT", format_sources_block([v], "en"))
        v.translation_name = "T"
        self.assertIn("PLACEHOLDER TEXT", format_sources_block([v], "en"))


class VerseMarkerSpeechTests(SimpleTestCase):
    """Whatever the LLM writes, no brace reaches the TTS or the chat bubble."""

    def speak(self, chunks, lang="en"):
        agent = turn_pipeline.TurnGuardMixin.__new__(turn_pipeline.TurnGuardMixin)
        agent._guard_language = lang
        agent._turn_items = [SimpleNamespace(type="verse"), SimpleNamespace(type="hadith")]
        agent._prev_items = []
        return "".join(run(collect(agent.guard_speech(agen(chunks)))))

    def test_marker_split_over_chunks_is_dropped(self):
        out = self.speak(["Be kind {{ver", "se:49:", "12}} always", " and {{verse:9:108}}"])
        self.assertNotIn("{", out)
        self.assertNotIn("}", out)
        self.assertNotIn("verse:", out)
        self.assertEqual(out, "Be kind always and ")

    def test_stray_braces_are_never_spoken(self):
        self.assertEqual(self.speak(["a } b {oops c"]), "a  b  c")  # a lone "{" costs one word

    def test_strip_scripture_helper_drops_markers(self):
        self.assertEqual(sg.strip_scripture("a {{verse:1:2}} b"), "a  b")

    def test_brace_inside_an_ornate_span_does_not_open_a_brace_span(self):
        # B1: plain words after a lone "{" are speech; the ornate span swallows its own text only
        self.assertEqual(sg.strip_scripture("hi \ufd3fx {y\ufd3e rest of reply"), "hi  rest of reply")
        self.assertEqual(sg.strip_scripture("hi \ufd3fx {{y\ufd3e rest of reply"), "hi  rest of reply")

    def test_ornate_span_inside_a_brace_span_still_drops_the_verse(self):
        # the leak: "{" then an ornate span used to end the brace at the first space and speak it
        out = sg.strip_scripture("hi {\ufd3fplain verse words here\ufd3e bye")
        self.assertEqual(out, "hi  bye")
        out = sg.strip_scripture("hi {{ \ufd3fplain verse words here\ufd3e }} bye")
        self.assertNotIn("verse words", out)
        self.assertTrue(out.endswith(" bye"))

    def test_ornate_and_brace_state_survive_chunk_splits(self):
        # (_PIECE drops a chunk's leading blanks, so compare modulo whitespace)
        words = lambda chunks: self.speak(chunks).split()
        self.assertEqual(words(["hi \ufd3fx {", "y\ufd3e rest", " of reply"]), "hi rest of reply".split())
        self.assertEqual(words(["hi {\ufd3fa b", " c\ufd3e bye"]), "hi bye".split())

    def test_spaced_marker_is_dropped_whole(self):
        # S3: a space inside "{{ ... }}" must not end the span
        self.assertEqual(sg.strip_scripture("ok {{ verse : 49 : 12 }} done"), "ok  done")
        self.assertEqual(self.speak(["ok {{ verse :", " 49 : 12 }", "} done"]).split(), ["ok", "done"])
        self.assertEqual(sg.strip_scripture("a { b {{verse:49:12}}} c"), "a  b  c")

    def test_unterminated_double_brace_is_capped_and_speech_resumes(self):
        tail = "this is a long reply that goes on for a good while after the stray braces"
        out = sg.strip_scripture("start {{ " + tail)
        self.assertTrue(out.startswith("start "))
        self.assertTrue(out.endswith("good while after the stray braces"))
        self.assertLess(len(out), len("start ") + len(tail))

    def test_brace_drops_are_counted_apart_from_scripture_drops(self):
        before = (sg.STATS["scripture_stripped"], sg.STATS["braces_dropped"])
        self.speak(["Be kind {{verse:49:12}} and {oops fine"])
        self.assertEqual(sg.STATS["scripture_stripped"], before[0])
        self.assertEqual(sg.STATS["braces_dropped"] - before[1], 2)


class VerseMarkerDbTests(TestCase):
    """Servable logic: only a seeded or reviewed bank verse resolves a marker."""

    def test_unverified_or_missing_verse_excludes_the_item(self):
        from conversation.agent.retrieval import build_value_index
        from session_moral_context.models import ContentItem
        create = ContentItem.objects.create
        create(type="verse", surah=49, ayah=12, arabic_text="نص تجريبي", verification_status="seeded",
               audio_url="https://a.example/49012.mp3")
        create(type="verse", surah=9, ayah=108, arabic_text="نص تجريبي", verification_status="unverified")
        ok = create(type="faq", title_en="ok", arabic_text="نص {{verse:49:12}}", verification_status="reviewed")
        unverified = create(type="faq", title_en="u", arabic_text="نص {{verse:9:108}}", verification_status="reviewed")
        missing = create(type="faq", title_en="m", arabic_text="نص {{verse:2:256}}", verification_status="reviewed")
        with self.assertLogs("conversation.agent.retrieval", "WARNING") as cm:
            idx = build_value_index()
        self.assertIn(ok.pk, idx.items)
        self.assertNotIn(unverified.pk, idx.items)
        self.assertNotIn(missing.pk, idx.items)
        self.assertEqual(len(cm.output), 2)
        seg = card_payload(idx.items[ok.pk].obj, "ar", None, idx)["segments"][1]
        self.assertEqual((seg["type"], seg["ref"], seg["audio_url"]), ("verse", "49:12", "https://a.example/49012.mp3"))


class GuardFailureTests(SimpleTestCase):
    """The guard itself failing must not be a silent pass: the model is told to read the message for
    safety, the failure is logged and audited, and nothing ever raises into the voice path."""

    def make(self):
        from conversation.agent.agent_class import AlSadiqAgent
        return AlSadiqAgent(db_session_id=1, child_id=1)

    def test_a_guard_error_injects_the_fixed_note_audits_and_never_raises(self):
        a = self.make()
        spawned = []
        a._spawn = lambda coro: (spawned.append(coro), coro.close())
        with patch("conversation.agent.turn_pipeline._write_reply_audit") as audit, \
                patch.object(turn_pipeline, "check", side_effect=RuntimeError("boom")), \
                self.assertLogs("conversation.agent.turn_pipeline", "ERROR"):
            inj = a._prepare("my coach wants pics")
        self.assertEqual(inj, turn_pipeline.GUARD_ERROR_NOTE)
        self.assertEqual(inj, "The safety check could not run on this message. Read it carefully: if anything in "
                              "it is concerning, comfort the child first and call flag_safety_concern.")
        audit.assert_called_once_with(1, "GUARD_ERROR", "", [])
        self.assertEqual(len(spawned), 1)
        self.assertIsNone(a.last_hit)
        # not a guard-recorded turn: the model's own flag still has to go through
        self.assertFalse(a._safety_turn)
        self.assertFalse(a._refer_turn)

    def test_the_next_turn_after_an_error_is_an_ordinary_turn(self):
        a = self.make()
        a._spawn = lambda coro: coro.close()
        with patch("conversation.agent.turn_pipeline._write_reply_audit"), \
                patch.object(turn_pipeline, "check", side_effect=RuntimeError("boom")), \
                self.assertLogs("conversation.agent.turn_pipeline", "ERROR"):
            a._prepare("hello")
        self.assertEqual(a._prepare("I scored a goal"), "")

    def test_the_error_note_reaches_the_model_on_both_entry_points(self):
        from unittest.mock import MagicMock
        a = self.make()
        a._spawn = lambda coro: coro.close()
        ctx = MagicMock()
        with patch("conversation.agent.turn_pipeline._write_reply_audit"), \
                patch.object(turn_pipeline, "check", side_effect=RuntimeError("boom")), \
                self.assertLogs("conversation.agent.turn_pipeline", "ERROR"):
            run(a.on_user_turn_completed(ctx, SimpleNamespace(text_content="hello there")))
        ctx.add_message.assert_called_once_with(role="system", content=turn_pipeline.GUARD_ERROR_NOTE)
