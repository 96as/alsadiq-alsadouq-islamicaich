"""Offline checks for the multi-turn dev-conversation runner: no network, fake client."""
from django.test import SimpleTestCase

from conversation.eval.dev_conversations import runner
from conversation.eval.test_llm_eval import FakeClient, _bank_index

CONV = {'id': 'c1', 'lang': 'en', 'age': 8, 'theme': 't', 'memory': 'The child has a cat called Luna.',
        'expect': 'be a friend', 'turns': ['hello there my friend', 'we went to the park']}
VERDICT = {'scores': {k: 4 for k in runner.SCORE_KEYS}, 'reasons': {},
           'problems': [{'turn': 2, 'quote': 'Nice park', 'issue': 'x'},
                        {'turn': 2, 'quote': 'not in the reply', 'issue': 'y'}],
           'best_moment': {'turn': 1, 'why': 'warm'}}


class DevConversationRunnerTests(SimpleTestCase):
    def _run(self, channel='voice'):
        client = FakeClient('Nice park! What did you play?', VERDICT)
        run = runner.run_dev_convs([dict(CONV)], _bank_index(), client=client, agent_model='agent-x',
                                   judge_models=['judge-y'], channel=channel, max_calls=20)
        return run, client

    def test_history_carries_child_text_and_heard_reply_only(self):
        run, client = self._run()
        agent_calls = [c for c in client.calls if 'response_format' not in c]
        second = agent_calls[1]['messages']
        self.assertEqual(second[0]['role'], 'system')
        self.assertIn('Luna', second[0]['content'])          # session memory reaches the prompt
        roles = [m['role'] for m in second[1:3]]
        self.assertEqual(roles, ['user', 'assistant'])
        self.assertEqual(second[1]['content'], 'hello there my friend')
        self.assertEqual(second[2]['content'], run['conversations'][0]['turns'][0]['reply'])
        self.assertEqual(second[3], {'role': 'user', 'content': 'we went to the park'})

    def test_injection_is_per_turn_and_placed_by_channel(self):
        inj = 'TURN NOTE test'
        for channel, pos in (('voice', -1), ('text', -2)):
            client = FakeClient('Hi!', VERDICT)
            with self._patch_prepare(inj):
                runner.run_dev_convs([dict(CONV)], _bank_index(), client=client, agent_model='a',
                                     judge_models=['j'], channel=channel, max_calls=20, judge_on=False)
            msgs = client.calls[1]['messages']
            self.assertEqual(msgs[pos], {'role': 'system', 'content': inj})
            # the first turn's injection is not carried into the second turn's history
            self.assertEqual(sum(1 for m in msgs if m['content'] == inj), 1)

    def test_aggregate_and_quote_check(self):
        run, _ = self._run()
        conv = run['conversations'][0]
        self.assertEqual(conv['judge']['bad_quotes'], 1)
        self.assertEqual([p['quote'] for p in conv['judge']['problems']], ['Nice park'])
        agg = run['aggregate']
        self.assertEqual(agg['turns'], 2)
        self.assertEqual(agg['scores']['overall'], 4)
        self.assertEqual(agg['metrics']['repeated_openers'], 1)   # same opener twice
        for key in ('search_bank_turns', 'cards_shown', 'cards_on_unasked_turns'):
            self.assertEqual(agg['metrics'][key], 0)
        self.assertEqual(conv['turns'][0]['guard'], 'none')
        self.assertIn('c1', runner.render_transcript(run))

    def test_judge_transcript_has_guard_sources_and_cards(self):
        turn = {'n': 1, 'child': 'why do we pray?', 'reply': 'Because.', 'guard': 'none',
                'retrieved': [{'id': 1, 'type': 'faq', 'values': ['prayer']}],
                'items': [{'id': 1, 'type': 'faq', 'values': ['prayer']}], 'tool_calls': [{'name': 'search_bank'}]}
        text = runner.transcript_for_judge(dict(CONV), [turn])
        self.assertIn('guard: none; sources: faq/prayer; cards shown: faq/prayer; tool: search_bank', text)

    def test_search_bank_cards_and_unasked_metrics(self):
        def t(n, asked, **kw):
            base = dict(n=n, asked=asked, reply='ok', words=1, questions=0, guard='none', search_bank_called=False,
                        items=[], cards_invalid=[])
            return {**base, **kw}
        card = {'id': 1, 'type': 'faq', 'values': []}
        m = runner.metrics([t(1, True, search_bank_called=True, items=[card]),
                            t(2, False, search_bank_called=True, items=[card, card]),
                            t(3, False, reply='Ma sha Allah, well done!'),
                            t(4, False, guard='SAFETY', reply='Allah is with you')])
        self.assertEqual((m['search_bank_turns'], m['cards_shown'], m['cards_on_unasked_turns']), (2, 3, 2))
        self.assertEqual(m['religious_phrase_turns'], [3])         # turn 4 had a guard note: not a plain turn
        self.assertEqual(m['source_turns'], 2)

    def test_asked_flags(self):
        self.assertEqual(runner.asked_flags(['why do we pray?', 'why?', 'my cat is cute', 'what kind of pizza do you like?']),
                         [True, True, False, False])
        self.assertEqual(runner.asked_flags(['ليش لازم نقول الحمدلله؟', 'ليش؟', 'اليوم لعبت مع أخوي']), [True, True, False])
        self.assertEqual(runner.asked_flags(['is it honest to lie?', 'tell me a joke']), [True, False])

    def _patch_prepare(self, inj):
        from unittest import mock

        def fake(agent, text):
            return inj
        return mock.patch('conversation.eval.llm_driver.EvalAgent._prepare', fake)
