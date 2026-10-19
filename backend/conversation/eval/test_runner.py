"""Runner tests: tiny synthetic cases and bank (placeholder text only, no scripture)."""
import os
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from conversation.agent import turn_guard as tg
from conversation.agent.retrieval import ValueIndex
from conversation.eval import runner


def _item(pk, type_, **kw):
    d = dict(title_en='', title_ar='', keywords_en=[], keywords_ar=[], surah=None, ayah=None,
             content_level='', verification_status='reviewed', age_band='all')
    d.update(kw)
    return SimpleNamespace(pk=pk, type=type_, **d)


def _index():
    items = [_item(1, 'verse', surah=1, ayah=1), _item(2, 'hadith', title_en='placeholder topic')]
    vals = [SimpleNamespace(slug='v1', name_en='V1', name_ar='ق1', keywords_en=[], keywords_ar=[], order=0)]
    return ValueIndex.from_records(vals, items, [('v1', 1, 0)])


def _hit(kind='REFER', level='D', rule='r1', flag_type='', notify_parent=True):
    return tg.GuardHit(kind, rule, level, flag_type=flag_type, notify_parent=notify_parent)


def _case(cid, **expect):
    base = dict(mode='NONE', must_cite=False, must_not=['claims_human'], rubric='PASS if x; FAIL if y')
    base.update(expect)
    return dict(id=cid, category='grounding', lang='en', age=8, channels=['voice', 'text'],
                input='text in', input_voice='voice in', expect=base)


class RunnerTests(SimpleTestCase):
    def setUp(self):
        self.index = _index()
        self.item1 = self.index.items[1].obj

    def chk(self, table):
        """A stand-in guard: the hit (or None) for each input text."""
        return lambda text: table[text]

    def test_pass_fail_skipped_counts_and_pending(self):
        cases = [
            _case('ok-en', mode='REFER', level='D'),
            _case('bad-en', mode='REFER', level='D'),
            _case('model-en', mode='ANSWER', level='A', items=['verse:1:1'], must_cite=True),
            _case('safe-en', mode='SAFETY', flag_safety_concern=True, flag_type=['harmful']),
            _case('quiet-en', mode='NONE', items_must_be_empty=True),
            _case('creed-en', mode=['DISAGREE_AND_REFER', 'REFER'], level='C'),
        ]
        table = {}
        for c, hit in zip(cases, (_hit(), None, None, _hit('SAFETY', 'D', 'r2', 'harmful'), None, _hit('REFER', 'C'))):
            c['input'] = c['input_voice'] = c['id']
            table[c['id']] = hit
        res = runner.run_policy(cases, self.index, self.chk(table))
        by = {r.case_id: r.status for r in res if r.channel == 'text'}
        self.assertEqual(by, {'ok-en': 'pass', 'bad-en': 'fail', 'model-en': 'skipped', 'safe-en': 'pass',
                              'quiet-en': 'pass', 'creed-en': 'pass'})
        s = runner.summarize(res)['total']
        self.assertEqual((s['pass'], s['fail'], s['skipped']), (8, 2, 2))
        self.assertTrue(all(r.llm_pending for r in res))
        self.assertEqual(next(r for r in res if r.case_id == 'model-en').failures, [])

    def test_a_safety_alarm_on_a_turn_that_must_not_raise_one_fails_even_for_a_model_case(self):
        c = _case('over-en', mode='ANSWER', level='A')
        c['input'] = c['input_voice'] = 'x'
        res = runner.run_policy([c], self.index, self.chk({'x': _hit('SAFETY', 'D', 'r', 'harmful')}))
        self.assertEqual({r.status for r in res}, {'fail'})

    def test_a_plain_turn_that_gets_referred_fails(self):
        c = _case('refer-en', mode='NONE')
        c['input'] = c['input_voice'] = 'x'
        res = runner.run_policy([c], self.index, self.chk({'x': _hit('REFER', 'C')}))
        self.assertEqual({r.status for r in res}, {'fail'})

    def test_notify_parent(self):
        safe = dict(mode='SAFETY', flag_safety_concern=True, flag_type=['harmful'], notify_parent=False)
        c1, c2, c3 = _case('np-ok-en', **safe), _case('np-bad-en', **safe), _case('np-unset-en', **{**safe, 'notify_parent': None})
        for c, key in ((c1, 'a'), (c2, 'b'), (c3, 'b')):
            c['input'] = c['input_voice'] = key
        c3['expect'].pop('notify_parent')
        table = {'a': _hit('SAFETY', 'D', 'r', 'harmful', notify_parent=False),
                 'b': _hit('SAFETY', 'D', 'r', 'harmful', notify_parent=True)}
        res = runner.run_policy([c1, c2, c3], self.index, self.chk(table))
        by = {r.case_id: r for r in res if r.channel == 'text'}
        self.assertEqual(by['np-ok-en'].status, 'pass')
        self.assertEqual(by['np-bad-en'].failures[0][0], 'notify_parent')
        self.assertEqual(by['np-unset-en'].status, 'pass')

    def test_flag_type_is_checked(self):
        c = _case('ft-en', mode='SAFETY', flag_safety_concern=True, flag_type=['harmful'])
        c['input'] = c['input_voice'] = 'x'
        res = runner.run_policy([c], self.index, self.chk({'x': _hit('SAFETY', 'D', 'r', 'sensitive')}))
        self.assertEqual(res[0].failures[0][0], 'flag_type')

    def test_parity_failure(self):
        c = _case('par-en', mode='NONE')
        table = {'text in': None, 'voice in': _hit('REFER', 'D')}
        res = runner.run_policy([c], self.index, self.chk(table))
        self.assertEqual([r.status for r in res], ['fail', 'fail'])
        self.assertIn('parity', [f[0] for f in res[0].failures])

    def test_the_real_guard_agrees_with_every_dev_case_it_decides(self):
        from conversation.eval import load_cases
        cases = runner.filter_cases(load_cases(), exclude_tag='heldout')
        res = runner.run_policy(cases)
        bad = [(r.case_id, r.channel, r.failures) for r in res if r.status == 'fail']
        self.assertEqual(bad, [])
        s = runner.summarize(res)['total']
        self.assertGreater(s['pass'], 100)   # safety, REFER, creed and plain-chat cases are really decided here

    def test_filter_by_tag(self):
        a = dict(_case('a-en'), tags=['heldout'])
        b = dict(_case('b-en'), tags=['dialect'])
        c = _case('c-en')
        cases = [a, b, c]
        self.assertEqual([x['id'] for x in runner.filter_cases(cases, tag='heldout')], ['a-en'])
        self.assertEqual([x['id'] for x in runner.filter_cases(cases, exclude_tag='heldout')], ['b-en', 'c-en'])
        self.assertEqual(len(runner.filter_cases(cases)), 3)

    def test_pointer_resolution(self):
        self.assertEqual(runner.resolve_pointers(self.index, ['verse:1']), {1})
        self.assertEqual(runner.resolve_pointers(self.index, ['verse:1:1-3']), {1})
        self.assertEqual(runner.resolve_pointers(self.index, ['verse:2:1']), set())
        self.assertEqual(runner.resolve_pointers(self.index, ['hadith:placeholder-topic']), {2})

    def test_report_and_cli_exit_code(self):
        c = _case('bad-en', mode='REFER', level='D')
        res = runner.run_policy([c], self.index, self.chk({'text in': None, 'voice in': None}))
        with tempfile.TemporaryDirectory() as d:
            path = runner.write_report(res, directory=d)
            body = open(path, encoding='utf-8').read()
        self.assertIn('pass 0, fail 2, content gap 0', body)
        self.assertIn('bad-en', body)
        self.assertIn('fail 2', runner.console_summary(res))

    def test_command_exit_code(self):
        from django.core.management import call_command
        cases = [_case('bad-en', mode='REFER', level='D')]
        res = runner.run_policy(cases, self.index, self.chk({'text in': None, 'voice in': None}))
        with patch('conversation.management.commands.run_eval.load_cases', return_value=cases), \
                patch('conversation.management.commands.run_eval.Command._execute', return_value=('policy', res)), \
                patch('django.test.utils.setup_databases', return_value=None), \
                patch('django.test.utils.teardown_databases'), \
                patch('django.core.management.call_command'), \
                patch('conversation.management.commands.run_eval.call_command'):
            with self.assertRaises(SystemExit) as cm:
                call_command('run_eval', '--no-report')
            self.assertEqual(cm.exception.code, 1)
            call_command('run_eval', '--no-report', '--no-fail')

    def test_llm_needs_key(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop('OPENAI_API_KEY', None)
            with self.assertRaises(RuntimeError):
                runner.run_llm([], None, agent_model='placeholder-model', judge_models=['placeholder-judge'])

    def test_index_is_built_like_the_entrypoint(self):
        """run_eval reads the item links too, as entrypoint._get_value_index does (output-guard licence)."""
        from conversation.management.commands.run_eval import Command
        sentinel = object()
        with patch('conversation.agent.retrieval.build_value_index', return_value=sentinel), \
                patch('conversation.agent.turn_pipeline.annotate_linked_types') as annotate:
            self.assertIs(Command()._index(), sentinel)
        annotate.assert_called_once_with(sentinel)
