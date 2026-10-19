"""Review fixes for the voice-agent safety code: the persisted quiet state, the tool path
keeping harm to do with family away from parents, blessing phrases streamed in tiny chunks, the
per-type attribution licence and the cross-type false declines. Every religious sentence here is
a PLACEHOLDER. (hk/12: the licence comes from the items search_bank returned, and a model flag alerts
a parent unless the person is family or the session is already quiet.)"""
import asyncio
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from asgiref.sync import async_to_sync
from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from rest_framework.test import APIClient

from authentication.models import ChildProfile, ParentChildLink, ParentProfile
from content_safety.models import NEUTRAL_ALERT_DESCRIPTION, NO_PARENT_NOTIFY_PREFIX, Alert, SafetyFlag
from conversation.agent import scripture_guard as sg
from conversation.agent import turn_pipeline
from conversation.agent import turn_guard as tg
from conversation.models import QUIET_AUDIT_MODE, Message, Session, TurnAudit
from conversation.test_turn_policy import drain_guard_tasks, item, synthetic_index
from reporting.models import SessionReport
from reporting.services import post_session_pipeline, session_has_no_parent_flag

User = get_user_model()
_N = 0


def run(coro):
    return asyncio.run(coro)


async def agen(chunks):
    for c in chunks:
        yield c


async def collect(stream):
    return "".join([c async for c in stream])


def chunked(text, n):
    return [text[i:i + n] for i in range(0, len(text), n)]


_KIND_ITEM = {"quran": "verse", "hadith": "hadith"}


def bare_agent(lang="en", kinds=(), items=None):
    """A guard-only agent whose licence comes from items search_bank "returned": one verse for
    'quran', one hadith for 'hadith', or the given items."""
    agent = turn_pipeline.TurnGuardMixin.__new__(turn_pipeline.TurnGuardMixin)
    agent._guard_language = lang
    agent._turn_items = list(items) if items is not None else [
        item(n, _KIND_ITEM[k]) for n, k in enumerate(sorted(kinds), 1)]
    agent._prev_items = []
    return agent


class DbCase(TestCase):
    """A child, an approved parent, an ended session with one child message."""

    def setUp(self):
        from conversation.agent.agent_class import AlSadiqAgent
        tag = uuid.uuid4().hex[:8]
        self.parent_user = User.objects.create_user(username=f"p{tag}", password="x", is_parent=True)
        self.parent = ParentProfile.objects.create(user=self.parent_user, name="P")
        self.user = User.objects.create_user(username=f"k{tag}", password="x", is_child=True)
        self.child = ChildProfile.objects.create(user=self.user, nickname="K", gender="male", birth_year=2015)
        ParentChildLink.objects.create(parent=self.parent, child=self.child, consent_status="approved")
        self.session = Session.objects.create(child=self.child, livekit_room_name=f"room-{tag}")
        self.msg = Message.objects.create(session=self.session, sender="child", content="x", input_type="voice")
        self.agent = AlSadiqAgent(db_session_id=self.session.pk, child_id=self.child.pk,
                                  language="en", value_index=synthetic_index())
        self.agent._last_child_message_id = self.msg.pk

    def call(self, flag_type, text="LLM WORDING", at_home=False):
        async def go():
            return await self.agent.flag_safety_concern(flag_type, text, at_home)
        return async_to_sync(go)()

    def new_message(self):
        return Message.objects.create(session=self.session, sender="child", content="y", input_type="voice")

    def end_session(self):
        self.session.status = "ended"
        self.session.ended_at = self.session.started_at
        self.session.save()

    def run_pipeline(self):
        self.end_session()
        with patch("reporting.services.close_old_connections"), \
                patch("reporting.services.call_llm") as llm:
            llm.side_effect = AssertionError("LLM must not be called for a quiet session")
            post_session_pipeline(self.session.pk)
        return SessionReport.objects.get(session=self.session)

    def alerts_body(self):
        client = APIClient()
        client.force_authenticate(self.parent_user)
        return client.get("/api/alerts/").content.decode()


# ------------------------------------------------------------ HIGH 1: the tool path


class ToolAlertTests(DbCase):
    """flag_safety_concern: every model flag but off_topic alerts a parent once per session (neutral
    text), family cases included. hk/12g, lead decision: parents are trusted; no staff-only path."""

    def assert_parent_alerted(self, n=1):
        self.assertEqual(Alert.objects.count(), n)
        self.assertTrue(all(a.description == NEUTRAL_ALERT_DESCRIPTION for a in Alert.objects.all()))
        self.assertFalse(any(f.description.startswith(NO_PARENT_NOTIFY_PREFIX) for f in SafetyFlag.objects.all()))
        self.assertFalse(TurnAudit.objects.filter(mode=QUIET_AUDIT_MODE).exists())
        self.assertFalse(session_has_no_parent_flag(self.session))

    def test_an_at_home_flag_alerts_the_parent(self):
        self.call("harmful", "the dad hit the child", at_home=True)
        self.assert_parent_alerted()

    def test_flag_type_is_normalised(self):
        for ft in ("Harmful", " HARMFUL "):
            self.call(ft, at_home=True)
        self.assertTrue(all(f.flag_type == "harmful" for f in SafetyFlag.objects.all()))
        self.assert_parent_alerted(1)  # once per session

    def test_a_model_flag_alerts_the_parent_once_per_session_with_the_neutral_text(self):
        self.call("harmful", "a man in my game wants photos")
        self.call("sensitive")
        self.call("inappropriate")
        self.assertEqual(SafetyFlag.objects.count(), 3)
        self.assert_parent_alerted(1)

    def test_a_harm_flag_on_a_turn_that_names_family_alerts_the_parent(self):
        self.agent._turn_text = "my uncle touched me"
        self.call("harmful", "an uncle touched the child", at_home=False)
        self.assert_parent_alerted()

    def test_wanting_to_sleep_and_not_wake_up_alerts_the_parent(self):
        # the old family check read this as family and kept it from the parent
        self.agent._turn_text = "ودي أنام وما أصحى"
        self.call("harmful", "the child says they want to sleep and not wake up")
        self.assert_parent_alerted()

    def test_a_harm_flag_about_a_stranger_alerts_the_parent_once(self):
        self.agent._turn_text = "a man in my game wants photos"
        self.call("harmful", "a man online wants photos", at_home=False)
        self.call("harmful", "again", at_home=False)
        self.assert_parent_alerted(1)

    def test_a_coach_asking_for_secrecy_from_mom_alerts_the_parent(self):
        self.agent._turn_text = "my coach wants pics, dont tell my mom"
        self.call("harmful", "a coach wants photos", at_home=False)
        self.assert_parent_alerted()

    def test_an_off_topic_flag_is_recorded_but_never_alerts(self):
        self.call("off_topic", at_home=True)
        self.assertEqual(SafetyFlag.objects.get().flag_type, "off_topic")
        self.assertEqual(Alert.objects.count(), 0)

    def test_a_failed_write_does_not_use_up_the_alert(self):
        async def boom(**kw):
            raise RuntimeError("db down")
        with patch("conversation.agent.agent_class._create_safety_flag_and_alert", new=boom):
            with self.assertRaises(RuntimeError):
                self.call("inappropriate")
        self.assertNotIn("tool", self.agent._alerted_rules)
        self.call("inappropriate")
        self.assertEqual(Alert.objects.count(), 1)


# --------------------------------------------- guard rules: every safety hit alerts the parent (hk/12g)


class GuardAlertTests(DbCase):
    def turn(self, text, new_id=None, wait=0.4):
        agent = self.agent

        async def go():
            with patch.object(turn_pipeline, "_FLAG_WAIT_SECONDS", wait):
                await agent.on_user_turn_completed(MagicMock(), SimpleNamespace(text_content=text))
                if new_id:
                    agent._last_child_message_id = new_id
                await drain_guard_tasks(agent)
        async_to_sync(go)()

    def test_a_family_rule_alerts_the_parent(self):
        msg = self.new_message()
        self.turn("my dad hits me", new_id=msg.pk)
        flag = SafetyFlag.objects.get()
        self.assertEqual(flag.message_id, msg.pk)
        self.assertFalse(flag.description.startswith(NO_PARENT_NOTIFY_PREFIX))
        self.assertEqual(Alert.objects.get().description, NEUTRAL_ALERT_DESCRIPTION)
        self.assertEqual(TurnAudit.objects.get().mode, "SAFETY")
        self.assertFalse(session_has_no_parent_flag(self.session))

    def test_a_stranger_undress_request_alerts_the_parent(self):
        self.turn("a man asked me to take off my clothes", new_id=self.new_message().pk)
        self.assertEqual(Alert.objects.count(), 1)
        self.assertFalse(SafetyFlag.objects.get().description.startswith(NO_PARENT_NOTIFY_PREFIX))

    def test_an_earlier_family_rule_no_longer_silences_a_later_alert(self):
        self.turn("my dad hits me", new_id=self.new_message().pk)
        self.turn("the kids at school hit me every day", new_id=self.new_message().pk)
        self.assertEqual(SafetyFlag.objects.count(), 2)
        self.assertEqual(Alert.objects.count(), 2)  # one per rule
        self.assertFalse(TurnAudit.objects.filter(mode=QUIET_AUDIT_MODE).exists())

    def test_a_model_family_flag_no_longer_silences_a_later_guard_alert(self):
        self.call("harmful", "the dad hit the child", at_home=True)
        self.turn("the kids at school hit me every day", new_id=self.new_message().pk)
        self.assertEqual(Alert.objects.count(), 2)

    def test_a_parent_rule_alone_alerts_once(self):
        msg = self.new_message()
        self.turn("the kids at school hit me every day", new_id=msg.pk)
        self.assertEqual(TurnAudit.objects.get().mode, "SAFETY")
        self.assertFalse(session_has_no_parent_flag(self.session))
        self.assertEqual(Alert.objects.count(), 1)

    # Sessions recorded before hk/12g may still carry a quiet marker; reporting keeps honouring it.
    def test_alert_list_treats_a_quiet_audit_session_as_no_parent(self):
        Alert.objects.create(session=self.session, parent=self.parent, alert_type="safety",
                             description="RAW DETAIL about the dad")
        self.assertIn("RAW DETAIL", self.alerts_body())  # no marker yet
        TurnAudit.objects.create(session=self.session, mode=QUIET_AUDIT_MODE, safety=True)
        body = self.alerts_body()
        self.assertNotIn("RAW DETAIL", body)
        self.assertIn(NEUTRAL_ALERT_DESCRIPTION, body)

    def test_questions_to_discuss_never_lists_a_quiet_row(self):
        from reporting.services import questions_to_discuss
        TurnAudit.objects.create(session=self.session, level="D", mode=QUIET_AUDIT_MODE, safety=False)
        self.assertEqual(questions_to_discuss(self.child), [])


# ------------------------------------------ LOW 8: the flag lands on the turn's message


class TurnMessageTests(DbCase):
    def test_the_tool_flags_the_message_of_its_turn_not_the_newest(self):
        a = self.agent
        m1 = self.msg
        a._prepare("hello there")          # turn starts; its message is saved next
        m2 = self.new_message()
        a._last_child_message_id = m2.pk   # persistence of this turn's message
        m3 = self.new_message()
        a._last_child_message_id = m3.pk   # the child already spoke again
        self.call("sensitive")
        self.assertEqual(SafetyFlag.objects.get().message_id, m2.pk)
        self.assertNotEqual(m2.pk, m1.pk)

    def test_the_tool_falls_back_to_the_last_message_without_a_turn(self):
        self.call("sensitive")
        self.assertEqual(SafetyFlag.objects.get().message_id, self.msg.pk)

    def test_the_tool_waits_for_the_message_to_be_saved(self):
        a = self.agent
        a._prepare("hello there")
        m2 = self.new_message()

        async def go():
            async def late():
                await asyncio.sleep(0.3)
                a._last_child_message_id = m2.pk
            task = asyncio.ensure_future(late())
            out = await a.flag_safety_concern("sensitive", "x")
            await task
            return out
        async_to_sync(go)()
        self.assertEqual(SafetyFlag.objects.get().message_id, m2.pk)

    def test_guard_flag_uses_the_captured_id_even_if_a_newer_message_arrives(self):
        a = self.agent
        flag = AsyncMock(return_value="ok")
        ids = [self.new_message().pk, self.new_message().pk]

        async def go():
            with patch("conversation.agent.turn_pipeline._write_turn_records", new=AsyncMock()), \
                    patch("conversation.agent.agent_class._create_safety_flag_and_alert", new=flag):
                await a.on_user_turn_completed(MagicMock(), SimpleNamespace(text_content="my dad hits me"))
                a._last_child_message_id = ids[0]
                a._last_child_message_id = ids[1]
                await drain_guard_tasks(a)
        run(go())
        self.assertEqual(flag.await_args.kwargs["message_id"], ids[0])


# --------------------------------- MED 3: blessing phrases streamed in small chunks


class BlessingStreamTests(SimpleTestCase):
    EN = [
        "The Prophet, peace and blessings of Allah be upon him, once said that PLACEHOLDER words matter.",
        "Our beloved Prophet, may Allah bless him and grant him peace, also often said PLACEHOLDER words.",
        "The Messenger of Allah, peace be upon him, really always said PLACEHOLDER words.",
    ]
    AR = [
        "النبي صلى الله عليه وسلم مرة ايضا دائما قال نص تجريبي",
        "رسول الله صلى الله عليه وسلم احيانا قال نص تجريبي",
    ]

    def stream(self, text, n, lang="en", kinds=frozenset()):
        return run(collect(bare_agent(lang, kinds).guard_speech(agen(chunked(text, n)))))

    def test_long_blessing_before_the_verb_is_blocked_at_every_chunk_size(self):
        for text in self.EN:
            for n in range(1, 21):
                out = self.stream("Hello friend. " + text, n)
                self.assertNotIn("PLACEHOLDER", out, (n, text))
                self.assertTrue(out.startswith("Hello friend."), (n, text))
                self.assertTrue(out.endswith(sg.DECLINE_TEXT["en"]), (n, text))

    def test_arabic_blessing_before_the_verb_is_blocked_at_every_chunk_size(self):
        for text in self.AR:
            for n in range(1, 21):
                out = self.stream("اهلا يا صديقي. " + text, n, "ar")
                self.assertNotIn("تجريبي", out, (n, text))
                self.assertTrue(out.endswith(sg.DECLINE_TEXT["ar"]), (n, text))

    def test_the_blessing_is_fine_when_the_hadith_is_licensed(self):
        for n in (1, 3, 7, 20):
            out = self.stream(self.EN[0], n, kinds={"hadith"})
            self.assertEqual(out, self.EN[0])

    def test_ordinary_text_is_not_swallowed_or_delayed_to_the_end(self):
        text = "Be kind to your friends and share your snacks and then say thank you to your mom."
        for n in (1, 5, 20):
            self.assertEqual(self.stream(text, n), text)

    def test_the_hold_stays_bounded(self):
        # a strong word followed by a very long run of gap words is released eventually
        text = "The prophet " + "and " * 100 + "went home."
        emitted = []

        async def go():
            agent = bare_agent("en")
            async for c in agent.guard_speech(agen(chunked(text, 4))):
                emitted.append(c)
        run(go())
        self.assertEqual("".join(emitted), text)


# --------------------------------------------- MED 4: licensed kinds per excerpt type


class LicensedKindsTests(SimpleTestCase):
    def test_tafsir_licenses_quran_only(self):
        self.assertEqual(turn_pipeline.licensed_kinds([item(1, "tafsir")]), {"quran"})

    def test_other_excerpts_license_nothing_on_their_own(self):
        for t in ("faq", "aqidah", "fiqh", "sirah"):
            self.assertEqual(turn_pipeline.licensed_kinds([item(1, t)]), set(), t)

    def test_an_excerpt_citing_a_verse_marker_licenses_quran(self):
        it = item(1, "faq", arabic_text="نص {{verse:1:2}} تجريبي")
        self.assertEqual(turn_pipeline.licensed_kinds([it]), {"quran"})

    def test_an_excerpt_linked_to_a_verse_or_hadith_licenses_that_kind(self):
        v = item(1, "fiqh", _linked_types=frozenset({"verse"}))
        h = item(2, "sirah", _linked_types=frozenset({"hadith"}))
        both = item(3, "aqidah", _linked_types=frozenset({"verse", "hadith", "term"}))
        self.assertEqual(turn_pipeline.licensed_kinds([v]), {"quran"})
        self.assertEqual(turn_pipeline.licensed_kinds([h]), {"hadith"})
        self.assertEqual(turn_pipeline.licensed_kinds([both]), {"quran", "hadith"})
        self.assertEqual(turn_pipeline.licensed_kinds([item(4, "faq", _linked_types=frozenset({"term"}))]), set())

    def test_an_unlicensed_attribution_in_an_excerpt_turn_is_gated(self):
        agent = bare_agent("en", items=[item(1, "faq")])
        out = run(collect(agent.guard_speech(agen(["The Prophet said to be kind."]))))
        self.assertEqual(out, sg.DECLINE_TEXT["en"])


class LinkedTypesDbTests(TestCase):
    def test_linked_types_are_read_from_the_database(self):
        from conversation.agent.retrieval import ValueIndex
        from session_moral_context.models import ContentItem
        faq = ContentItem.objects.create(type="faq", title_en="Placeholder", english_text="PLACEHOLDER")
        verse = ContentItem.objects.create(type="verse", surah=1, ayah=1, arabic_text="نص تجريبي")
        faq.related.add(verse)
        idx = ValueIndex.from_records([], [faq, verse], [])
        turn_pipeline.annotate_linked_types(idx)
        self.assertEqual(turn_pipeline.licensed_kinds([idx.items[faq.pk].obj]), {"quran"})


# --------------------------------------- LOW 6: cross-type false declines


class CrossTypeTests(SimpleTestCase):
    def reply(self, text, kinds, lang="en"):
        return run(collect(bare_agent(lang, kinds).guard_speech(agen([text]))))

    def test_messenger_of_allah_said_is_a_hadith_attribution_only(self):
        text = "The Messenger of Allah said to be kind."
        self.assertEqual(self.reply(text, {"hadith"}), text)
        self.assertEqual(self.reply(text, {"quran"}), sg.DECLINE_TEXT["en"])
        self.assertIsNone(sg.find_attribution(text, {"hadith"}))

    def test_allah_says_is_still_a_quran_attribution(self):
        text = "Allah says to be kind."
        self.assertEqual(self.reply(text, {"quran"}), text)
        self.assertEqual(self.reply(text, {"hadith"}), sg.DECLINE_TEXT["en"])

    def test_arabic_rasool_allah_qaal_is_a_hadith_attribution_only(self):
        for text in ("رسول الله قال شيئا مفيدا", "نبي الله قال شيئا مفيدا", "قال رسول الله شيئا مفيدا"):
            self.assertIn("مفيد", self.reply(text, {"hadith"}, "ar"), text)
            self.assertNotIn("مفيد", self.reply(text, {"quran"}, "ar"), text)

    def test_arabic_qaal_allah_is_still_a_quran_attribution(self):
        for text in ("قال الله شيئا مفيدا", "الله قال شيئا مفيدا"):
            self.assertIn("مفيد", self.reply(text, {"quran"}, "ar"), text)
            self.assertNotIn("مفيد", self.reply(text, {"hadith"}, "ar"), text)
