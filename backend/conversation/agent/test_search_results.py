"""Tests for search_results.py: the `al.search` publisher, its content filters and the dev fixtures
(BEHAVIOUR-SPEC 6.2). No network, no livekit. No scripture anywhere: the guard tests use only the
meta-words that name such a text, and the heavily vowelled sample is an everyday word.

Run from backend/:  python manage.py test conversation.agent.test_search_results \
    --settings=config.settings_sqlite_test
"""
from __future__ import annotations

import asyncio
import json
import os
import unittest
from types import SimpleNamespace
from unittest import mock

from conversation.agent import content_guard
from conversation.agent import search_results as sr
from conversation.agent.test_voice_wiring import _WiringBase

VOWELLED = "كَتَبَ الوَلَدُ الدَرْسَ"


class _Room:
    def __init__(self, fail=False):
        self.publish_data = mock.AsyncMock(side_effect=RuntimeError("down") if fail else None)
        self.local_participant = SimpleNamespace(publish_data=self.publish_data)

    def messages(self):
        out = []
        for call in self.publish_data.await_args_list:
            assert call.kwargs["topic"] == "al.search" and call.kwargs["reliable"] is True
            out.append(json.loads(call.args[0].decode("utf-8")))
        return out


def _raw(i, **kw):
    row = {"title": "Title %d" % i, "url": "https://site%d.example/page?x=1" % i, "snippet": "Snippet %d" % i}
    row.update(kw)
    return row


class _Provider:
    safe_search = True

    def __init__(self, rows=None, error=None, delay=0):
        self.rows, self.error, self.delay = rows, error, delay
        self.calls = []

    async def __call__(self, query, lang):
        self.calls.append((query, lang))
        if self.delay:
            await asyncio.sleep(self.delay)
        if self.error:
            raise self.error
        return self.rows


class CleaningTests(unittest.TestCase):
    def test_tags_controls_and_bidi_overrides_are_removed(self):
        self.assertEqual(sr.clean_text("<b>Hello</b>‮  wor\x00ld <script>x()</script>"), "Hello world x()")
        self.assertEqual(sr.clean_text("a\n\t b"), "a b")
        self.assertEqual(sr.clean_text(None), "")
        self.assertEqual(sr.clean_text("Tom &amp; Jerry"), "Tom & Jerry")
        self.assertNotIn("<", sr.clean_text("&lt;img src=x&gt;hi"))

    def test_truncate_keeps_the_limit_and_ends_with_an_ellipsis(self):
        self.assertEqual(sr.truncate("short", 70), "short")
        long = "word " * 40
        for limit in (70, 140):
            cut = sr.truncate(long.strip(), limit)
            self.assertLessEqual(len(cut), limit)
            self.assertTrue(cut.endswith("…"))
            self.assertFalse(cut[-2].isspace())
        self.assertEqual(len(sr.truncate("x" * 500, 70)), 70)
        self.assertEqual(sr.truncate("a" * 70, 70), "a" * 70)
        self.assertEqual(len(sr.truncate("a" * 71, 70)), 70)

    def test_domain_only_never_a_full_url(self):
        cases = {
            "https://www.Example.org/a/b?c=d#e": "example.org",
            "http://user:pw@kids.example:8080/x": "kids.example",
            "kids.example/path": "kids.example",
            "https://a.b.example.org": "a.b.example.org",
            "": "",
            "not a host": "",
            "javascript:alert(1)": "",
            "https://localhost/": "",
            "https://" + "a" * 50 + ".example/": "",
            "https://exa mple.org/": "",
        }
        for raw, want in cases.items():
            self.assertEqual(sr.domain_of(raw), want, raw)


class FilterTests(unittest.TestCase):
    def test_a_result_has_exactly_t_d_s_and_no_url(self):
        shown, hl = sr.filter_results([_raw(1)])
        self.assertEqual(shown, [{"t": "Title 1", "d": "site1.example", "s": "Snippet 1"}])
        self.assertEqual(hl, 0)
        self.assertNotIn("/", shown[0]["d"])
        self.assertNotIn("http", json.dumps(shown))

    def test_at_most_five_results(self):
        shown, _ = sr.filter_results([_raw(i) for i in range(12)])
        self.assertEqual(len(shown), 5)
        self.assertEqual([r["t"] for r in shown], ["Title %d" % i for i in range(5)])

    def test_title_and_snippet_are_truncated_to_70_and_140(self):
        shown, _ = sr.filter_results([_raw(1, title="T" * 200, snippet="word " * 100)])
        self.assertLessEqual(len(shown[0]["t"]), 70)
        self.assertLessEqual(len(shown[0]["s"]), 140)

    def test_the_provider_key_names_are_accepted(self):
        shown, _ = sr.filter_results([{"t": "A", "d": "a.example", "s": "x"},
                                      {"name": "B", "link": "https://b.example/z", "description": "y"},
                                      {"title": "C", "domain": "c.example", "content": "z"}])
        self.assertEqual([(r["t"], r["d"], r["s"]) for r in shown],
                         [("A", "a.example", "x"), ("B", "b.example", "y"), ("C", "c.example", "z")])

    def test_results_without_a_title_or_a_real_domain_are_dropped(self):
        shown, _ = sr.filter_results([_raw(1, title=""), _raw(2, url="nope"), "text", None, 5, _raw(3)])
        self.assertEqual([r["d"] for r in shown], ["site3.example"])

    def test_a_result_with_a_meta_word_is_dropped_from_any_field(self):
        rows = [_raw(1, title="A surah for kids"), _raw(2, snippet="read the hadith of the day"),
                _raw(3, title="الحديث اليوم"),
                _raw(4, snippet="a verse"), _raw(5, url="https://quran.example/"), _raw(6), _raw(7)]
        shown, _ = sr.filter_results(rows)
        self.assertEqual([r["d"] for r in shown], ["site6.example", "site7.example"])

    def test_a_result_with_heavily_vowelled_arabic_is_dropped(self):
        self.assertGreater(content_guard.diacritic_ratio(VOWELLED), 0.2)
        shown, _ = sr.filter_results([_raw(1, snippet=VOWELLED), _raw(2, title=VOWELLED), _raw(3)])
        self.assertEqual([r["d"] for r in shown], ["site3.example"])

    def test_plain_arabic_text_is_kept(self):
        shown, _ = sr.filter_results([_raw(1, title="كيف تصنع النحلة العسل")])
        self.assertEqual(len(shown), 1)

    def test_hl_is_the_index_in_the_shown_list(self):
        rows = [_raw(1, title="a surah"), _raw(2), _raw(3), _raw(4)]
        self.assertEqual(sr.filter_results(rows, used=2)[1], 1)   # raw 2 is shown as index 1
        self.assertEqual(sr.filter_results(rows, used=0)[1], 0)   # dropped: 0
        self.assertEqual(sr.filter_results(rows, used=None)[1], 0)
        self.assertEqual(sr.filter_results(rows, used=9)[1], 0)

    def test_garbage_input_never_raises(self):
        for bad in (None, 5, "abc", b"abc", {"a": 1}, [[]], iter([1, None])):
            shown, hl = sr.filter_results(bad)
            self.assertEqual((shown, hl), ([], 0))


class MessageTests(unittest.TestCase):
    def test_the_message_shapes_match_the_spec(self):
        self.assertEqual(sr.build_searching("S1", "how do bees make honey", "en"),
                         {"v": 1, "id": "S1", "st": "searching", "kind": "web", "q": "how do bees make honey", "lang": "en"})
        self.assertEqual(sr.build_none("S1"), {"v": 1, "id": "S1", "st": "none"})
        self.assertEqual(sr.build_results("S1", [{"t": "a", "d": "b.example", "s": "c"}], 0),
                         {"v": 1, "id": "S1", "st": "results", "r": [{"t": "a", "d": "b.example", "s": "c"}], "hl": 0})

    def test_the_language_is_en_or_ar(self):
        self.assertEqual(sr.build_searching("S", "q", "en-US")["lang"], "en")
        self.assertEqual(sr.build_searching("S", "q", "ar")["lang"], "ar")
        self.assertEqual(sr.build_searching("S", "q", None)["lang"], "ar")

    def test_the_query_is_cleaned_and_cut(self):
        msg = sr.build_searching("S", "<i>" + "q" * 300, "en")
        self.assertEqual(len(msg["q"]), sr.QUERY_MAX)
        self.assertNotIn("<", msg["q"])

    def test_the_grownup_card_carries_no_query_text(self):
        msg = sr.build_searching("S", "a secret query", "en", grownup=True)
        self.assertEqual(msg["q"], "")
        self.assertEqual(msg["gu"], 1)
        self.assertEqual(sr.build_none("S", grownup=True)["gu"], 1)

    def test_the_grownup_texts_are_the_spec_wording(self):
        self.assertEqual(sr.GROWNUP_TEXT["en"], "Let's read this with a grown-up")
        self.assertEqual(sr.GROWNUP_TEXT["ar"], "نقرأها مع أحد الكبار")


class PublisherTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        sr._logged.clear()

    def publisher(self, room=None, lang="en", flagged=False):
        room = room or _Room()
        return room, sr.SearchPublisher(room, lang=lambda: lang, safety_flagged=lambda: flagged)

    async def test_the_whole_flow_is_searching_then_results(self):
        room, pub = self.publisher()
        provider = _Provider([_raw(i) for i in range(7)])
        shown = await pub.search("how do bees make honey", provider, used=1)
        self.assertEqual(shown, 5)
        a, b = room.messages()
        self.assertEqual(a["st"], "searching")
        self.assertEqual(a["id"], b["id"])
        self.assertEqual((a["q"], a["lang"], a["kind"]), ("how do bees make honey", "en", "web"))
        self.assertEqual(b["st"], "results")
        self.assertEqual(len(b["r"]), 5)
        self.assertEqual(b["hl"], 1)
        self.assertNotIn("gu", a)
        self.assertNotIn("fx", a)
        self.assertEqual(provider.calls, [("how do bees make honey", "en")])

    async def test_ids_are_unique_per_search(self):
        room, pub = self.publisher()
        for _ in range(3):
            await pub.search("bees", _Provider([_raw(1)]))
        ids = [m["id"] for m in room.messages() if m["st"] == "searching"]
        self.assertEqual(ids, ["S1", "S2", "S3"])

    async def test_no_usable_results_is_none(self):
        room, pub = self.publisher()
        shown = await pub.search("bees", _Provider([_raw(1, title="a surah"), _raw(2, url="x")]))
        self.assertEqual(shown, 0)
        self.assertEqual([m["st"] for m in room.messages()], ["searching", "none"])

    async def test_a_scripture_query_gets_the_grownup_card_and_the_provider_is_never_called(self):
        room, pub = self.publisher()
        provider = _Provider([_raw(1)])
        shown = await pub.search("tell me the hadith about bees", provider)
        self.assertEqual(shown, 0)
        self.assertEqual(provider.calls, [])
        a, b = room.messages()
        self.assertEqual((a["st"], a["q"], a["gu"]), ("searching", "", 1))
        self.assertEqual((b["st"], b["gu"]), ("none", 1))
        self.assertNotIn("hadith", json.dumps(room.messages()))

    async def test_a_safety_concern_this_turn_gets_the_grownup_card(self):
        room, pub = self.publisher(flagged=True)
        provider = _Provider([_raw(1)])
        self.assertEqual(await pub.search("bees", provider), 0)
        self.assertEqual(provider.calls, [])
        self.assertTrue(all(m.get("gu") == 1 for m in room.messages()))
        self.assertTrue(all("r" not in m for m in room.messages()))

    async def test_a_concern_flagged_while_the_search_runs_hides_the_results(self):
        flag = {"on": False}
        room = _Room()
        pub = sr.SearchPublisher(room, lang=lambda: "en", safety_flagged=lambda: flag["on"])
        sid = await pub.start("bees")
        flag["on"] = True
        self.assertEqual(await pub.results(sid, [_raw(1)]), 0)
        last = room.messages()[-1]
        self.assertEqual((last["st"], last.get("gu")), ("none", 1))
        self.assertNotIn("r", last)

    async def test_a_broken_safety_callback_means_the_grownup_card(self):
        room = _Room()
        pub = sr.SearchPublisher(room, safety_flagged=mock.Mock(side_effect=RuntimeError("x")))
        self.assertEqual(await pub.search("bees", _Provider([_raw(1)])), 0)

    async def test_a_provider_without_strict_safe_search_is_refused(self):
        room, pub = self.publisher()
        provider = _Provider([_raw(1)])
        provider.safe_search = False
        self.assertEqual(await pub.search("bees", provider), 0)
        self.assertEqual(provider.calls, [])
        self.assertEqual([m["st"] for m in room.messages()], ["searching", "none"])

        async def bare(query, lang):
            return [_raw(1)]

        self.assertEqual(await pub.search("bees", bare), 0)

    async def test_a_failing_or_slow_provider_is_none(self):
        room, pub = self.publisher()
        self.assertEqual(await pub.search("bees", _Provider(error=RuntimeError("boom"))), 0)
        self.assertEqual(await pub.search("bees", _Provider([_raw(1)], delay=1), timeout=0.05), 0)
        self.assertEqual([m["st"] for m in room.messages()], ["searching", "none", "searching", "none"])

    async def test_a_failed_publish_never_raises(self):
        room, pub = self.publisher(_Room(fail=True))
        self.assertEqual(await pub.search("bees", _Provider([_raw(1)])), 1)

    async def test_the_payload_is_compact_utf8_json_on_the_topic_reliably(self):
        room, pub = self.publisher(lang="ar")
        await pub.search("النحل", _Provider([_raw(1, title="عسل")]))
        raw = room.publish_data.await_args_list[1].args[0]
        self.assertIsInstance(raw, bytes)
        self.assertIn("عسل", raw.decode("utf-8"))   # not \\u-escaped: smaller on the wire
        self.assertNotIn(b'":"'.replace(b":", b": "), raw)
        self.assertNotIn(b", ", raw)

    async def test_text_in_results_is_cleaned_before_it_is_sent(self):
        room, pub = self.publisher()
        await pub.search("bees", _Provider([_raw(1, title="<b>Bold</b> title", snippet="a‮b\x00c <img src=x onerror=1>")]))
        r = room.messages()[1]["r"][0]
        self.assertEqual(r["t"], "Bold title")
        self.assertNotIn("<", r["s"])
        self.assertNotIn("‮", r["s"])

    async def test_nothing_clickable_no_url_in_any_message(self):
        room, pub = self.publisher()
        await pub.search("bees", _Provider([_raw(i) for i in range(4)]))
        blob = json.dumps(room.messages())
        self.assertNotIn("http", blob)
        self.assertNotIn("?x=1", blob)
        for r in room.messages()[1]["r"]:
            self.assertEqual(set(r), {"t", "d", "s"})


class DevFixtureTests(unittest.IsolatedAsyncioTestCase):
    def test_the_flag(self):
        for env, want in (({}, False), ({"SEARCH_DEV_SIM": "1"}, True), ({"SEARCH_DEV_SIM": "0"}, False),
                          ({"SEARCH_DEV_SIM": "yes"}, True), ({"SEARCH_DEV_SIM": ""}, False)):
            with self.subTest(env=env), mock.patch.dict(os.environ, env, clear=True):
                self.assertIs(sr.dev_enabled(), want)

    def test_every_fixture_passes_the_filters_it_will_meet(self):
        for name, entry in sr.DEV_FIXTURES.items():
            for lang in ("en", "ar"):
                rows = entry[lang]
                self.assertGreaterEqual(len(rows), 3, (name, lang))
                for title, domain, snippet in rows:
                    self.assertFalse(content_guard.looks_like_scripture(title + " " + snippet), (name, title))
                    self.assertTrue(domain.endswith(".example"), "reserved TLD: can never be a real site")
                    self.assertLessEqual(len(title), sr.TITLE_MAX)
                    self.assertLessEqual(len(snippet), sr.SNIPPET_MAX, (name, snippet))
                shown, _ = sr.filter_results([{"title": t, "url": "https://" + d + "/", "snippet": s} for t, d, s in rows])
                self.assertEqual(len(shown), len(rows), (name, lang))

    def test_fixture_queries_are_not_scripture(self):
        for entry in sr.DEV_FIXTURES.values():
            for key in entry["keys"]:
                self.assertFalse(sr.query_is_blocked(key), key)

    async def test_the_dev_provider_picks_a_fixture_by_topic_and_language(self):
        provider = sr.DevSearchProvider()
        en = await provider("how do bees make honey", "en")
        self.assertEqual(en[0]["title"], "How bees make honey")
        ar = await provider("كيف تصنع النحلة العسل", "ar")
        self.assertEqual(ar[0]["title"], sr.DEV_FIXTURES["bees"]["ar"][0][0])
        self.assertEqual((await provider("why is the moon round", "en"))[0]["title"], "Why the moon changes shape")
        self.assertEqual((await provider("something odd", "en"))[0]["title"], "Amazing facts about nature")

    async def test_dev_messages_are_marked_as_fixtures(self):
        room = _Room()
        pub = sr.SearchPublisher(room, lang=lambda: "en")
        shown = await pub.search("how do bees make honey", sr.DevSearchProvider())
        self.assertEqual(shown, 4)
        msgs = room.messages()
        self.assertTrue(all(m.get("fx") == 1 for m in msgs))
        self.assertEqual([m["st"] for m in msgs], ["searching", "results"])
        self.assertTrue(all(r["d"].endswith(".example") for r in msgs[1]["r"]))

    async def test_a_real_provider_is_never_marked_as_a_fixture(self):
        room = _Room()
        await sr.SearchPublisher(room, lang=lambda: "en").search("bees", _Provider([_raw(1)]))
        self.assertTrue(all("fx" not in m for m in room.messages()))

    async def test_the_dev_provider_is_not_on_by_default(self):
        self.assertFalse(sr.dev_enabled())


class _FakeSignals:
    """Stands in for avatar_signals.AvatarSignals.search(kind): an async context manager with a `found` flag."""

    def __init__(self):
        self.events = []

    def search(self, kind):
        outer = self

        class _Ctx:
            found = False

            async def __aenter__(self):
                outer.events.append(("enter", kind))
                return self

            async def __aexit__(self, *exc):
                outer.events.append(("exit", kind, self.found))
                return False

        return _Ctx()


class AgentSearchHookTests(_WiringBase):
    def _agent(self):
        return self.agent_class.AlSadiqAgent(db_session_id=1, child_id=2, language="en")

    async def test_the_hook_does_nothing_until_a_provider_is_set(self):
        agent = self._agent()
        self.assertEqual(await agent.web_search("bees"), 0)

    async def test_web_search_publishes_through_the_hook(self):
        agent, room = self._agent(), _Room()
        agent.set_search(sr.SearchPublisher(room, lang=lambda: agent.language), _Provider([_raw(1), _raw(2)]))
        self.assertEqual(await agent.web_search("bees"), 2)
        self.assertEqual([m["st"] for m in room.messages()], ["searching", "results"])

    async def test_web_search_drives_the_signals_activity_when_the_signals_branch_is_merged(self):
        agent, room = self._agent(), _Room()
        agent.signals = _FakeSignals()
        agent.set_search(sr.SearchPublisher(room), _Provider([_raw(1)]))
        await agent.web_search("bees")
        self.assertEqual(agent.signals.events, [("enter", "web"), ("exit", "web", True)])
        agent.set_search(sr.SearchPublisher(room), _Provider([]))
        await agent.web_search("bees")
        self.assertEqual(agent.signals.events[-1], ("exit", "web", False))

    async def test_a_safety_flag_on_this_childs_message_means_the_grownup_card_this_turn_only(self):
        agent, room = self._agent(), _Room()
        agent._last_child_message_id = 7
        self.assertFalse(agent.safety_flagged_this_turn())
        with mock.patch.object(self.agent_class, "_create_safety_flag_and_alert", mock.AsyncMock(return_value="ok")):
            await agent.flag_safety_concern("harmful", "x")
        self.assertTrue(agent.safety_flagged_this_turn())
        agent.set_search(sr.SearchPublisher(room, safety_flagged=agent.safety_flagged_this_turn), _Provider([_raw(1)]))
        self.assertEqual(await agent.web_search("bees"), 0)
        self.assertTrue(all(m.get("gu") == 1 for m in room.messages()))
        agent._last_child_message_id = 8     # the next child message: a new turn
        self.assertFalse(agent.safety_flagged_this_turn())

    async def test_the_dev_fixtures_are_off_unless_the_flag_is_set(self):
        await self.run_entrypoint()
        self.assertIsNone(self.agent._search)

    async def test_the_flag_without_a_room_that_can_listen_never_stops_the_session(self):
        with mock.patch.dict(os.environ, {"SEARCH_DEV_SIM": "1"}):
            await self.run_entrypoint()
        self.assertIsNotNone(self.session)

    async def test_the_dev_request_runs_the_fixture_search_and_other_topics_are_ignored(self):
        agent = self._agent()
        room = _Room()
        listeners = {}
        room.on = lambda event, cb: listeners.setdefault(event, cb)
        room.name = "r"
        self.entrypoint._wire_dev_search(room, agent)
        on_data = listeners["data_received"]
        mk = lambda topic, body: SimpleNamespace(topic=topic, data=body if isinstance(body, bytes) else json.dumps(body).encode())
        on_data(mk("something.else", {"q": "bees"}))
        on_data(mk("al.dev.search", b"not json"))
        on_data(mk("al.dev.search", {"q": "   "}))
        await asyncio.sleep(0)
        self.assertEqual(room.messages(), [])
        on_data(mk("al.dev.search", {"q": "how do bees make honey"}))
        for _ in range(40):
            await asyncio.sleep(0.05)
            if len(room.messages()) >= 2:
                break
        msgs = room.messages()
        self.assertEqual([m["st"] for m in msgs], ["searching", "results"])
        self.assertTrue(all(m["fx"] == 1 for m in msgs))
        self.assertEqual(msgs[1]["r"][0]["t"], "How bees make honey")


if __name__ == "__main__":
    unittest.main()
