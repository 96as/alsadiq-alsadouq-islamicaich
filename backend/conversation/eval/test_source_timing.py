"""Offline checks for the source-timing harness (hk/13): the pure metric functions, the loader, the shipped set.
No network, no LLM. Children's messages only, no scripture."""
import re
import tempfile
from pathlib import Path

from django.test import SimpleTestCase

from conversation.eval import source_timing as st


def rec(label='due', *, conv='c1', rep=1, n=1, lang='en', band='6-9', cards=(), mention=False, ref=False,
        found=False, unlicensed=False, called=False, reply='ok'):
    return {'conv': conv, 'rep': rep, 'n': n, 'label': label, 'lang': lang, 'age_band': band, 'child': 'hi',
            'guard': 'none', 'search_bank_called': called, 'search_args': [], 'cards_shown': list(cards),
            'source_mentioned': mention, 'referral': ref, 'not_found': found, 'unlicensed': unlicensed, 'reply': reply}


class TextCheckTests(SimpleTestCase):
    def test_source_mentioned_en_and_ar(self):
        for text in ('Want to hear a hadith about that?', 'There is a verse about it.', 'It is in a surah we know.',
                     'The Quran talks about this.', 'في حديث حلو عن هالشي', 'تحب أقرأ لك الحديث؟',
                     'في آية عن الصبر', 'هذي سورة قصيرة', 'يقول القرآن إن الله مع الصابرين', 'تحب الحديث الشريف؟', 'في حديث عن الصدق', 'في الحديث دا معنى حلو'):
            self.assertTrue(st.source_mentioned(text), text)
        for text in ('That sounds like a great day!', 'حديثك حلو يا صديق', 'إيه صح، فزتم!', 'العالم كبير', 'أحب الحديث عن البيتزا!', 'نكمل الحديث معك',
                     'Let us play a guessing game', 'I would love to hear your story'):
            self.assertFalse(st.source_mentioned(text), text)

    def test_referral_en_and_ar(self):
        for text in ('Ask your mom or dad.', 'Maybe ask a teacher about it.', 'A scholar can tell you.',
                     'Your parents will know.', 'اسأل ماما', 'اسألي أهلك', 'هذا سؤال للشيخ', 'اسأل المعلمة',
                     'روح لبابا وقول له'):
            self.assertTrue(st.referral(text), text)
        for text in ('I could not find that in my library.', 'Good question! I am not sure.', 'اسألك سؤال؟',
                     'ما لقيت هذا في مكتبتي', 'عالم الملائكة كبير', 'This is a moment for comfort',
                     'سأقول لك شي حلو'):
            self.assertFalse(st.referral(text), text)

    def test_says_not_found_en_and_ar(self):
        for text in ("I couldn't find that in my library.", 'I could not find it.', "That's not in my library.",
                     "I don't have that one.", "I couldn’t find anything about it.", 'ما لقيت شي عن هالموضوع',
                     'لم أجد هذا', 'ما عندي هالمعلومة', 'مو في مكتبتي', 'ما لقيته في مكتبتي', 'ما لاقيت شي',
                     'ما قدرت ألاقي دعاء السفر', 'ما أقدر ألاقيها', 'لا أعرف رقما محددا', 'I do not know how many there are.'):
            self.assertTrue(st.says_not_found(text), text)
        for text in ('Great question, the whale story is long!', 'هذا سؤال حلو', 'Here is what I know about it.'):
            self.assertFalse(st.says_not_found(text), text)


class MetricTests(SimpleTestCase):
    def test_offered_card_or_mention(self):
        self.assertTrue(st.offered(rec(cards=[3])))
        self.assertTrue(st.offered(rec(mention=True)))
        self.assertFalse(st.offered(rec()))

    def test_rates_per_label(self):
        rs = [rec('due', cards=[1]), rec('due', mention=True), rec('due'), rec('due'),            # 2 of 4
              rec('not_due'), rec('not_due'), rec('not_due', cards=[2]), rec('not_due', mention=True),   # 2 of 4
              rec('ask', cards=[3]), rec('ask'),                                                   # 1 of 2
              rec('not_in_bank', ref=True, found=True), rec('not_in_bank', found=True),
              rec('not_in_bank'), rec('not_in_bank', ref=True),                                    # wrong referral 2/4, found 2/4
              ]
        m = st.compute_metrics(rs)
        self.assertEqual((m['offered_when_due']['hits'], m['offered_when_due']['n'], m['offered_when_due']['rate']), (2, 4, 0.5))
        self.assertEqual(m['offered_when_due_card_only']['hits'], 1)
        self.assertEqual((m['creep']['hits'], m['creep']['n']), (2, 4))
        self.assertEqual(m['creep_card_only']['hits'], 1)
        self.assertEqual((m['ask_served']['hits'], m['ask_served']['n']), (1, 2))
        self.assertEqual((m['not_in_bank_wrong_referral']['hits'], m['not_in_bank_wrong_referral']['n']), (2, 4))
        self.assertEqual((m['not_in_bank_says_not_found']['hits'], m['not_in_bank_says_not_found']['n']), (2, 4))

    def test_invented_counts_only_checkable_turns(self):
        rs = [rec(unlicensed=True), rec(unlicensed=False), rec(unlicensed=None), rec('ask', unlicensed=True)]
        m = st.compute_metrics(rs)['invented_content']
        self.assertEqual((m['hits'], m['n']), (2, 3))

    def test_empty_label_has_no_rate(self):
        self.assertIsNone(st.compute_metrics([rec('due')])['creep']['rate'])

    def test_failing_reasons(self):
        self.assertEqual(st.failing_reasons(rec('due', cards=[1])), [])
        self.assertTrue(st.failing_reasons(rec('due')))
        self.assertTrue(st.failing_reasons(rec('not_due', mention=True)))
        self.assertEqual(st.failing_reasons(rec('not_due')), [])
        self.assertTrue(st.failing_reasons(rec('ask', mention=True)))             # a mention is not a card
        self.assertEqual(st.failing_reasons(rec('not_in_bank', found=True)), [])
        self.assertEqual(len(st.failing_reasons(rec('not_in_bank', ref=True))), 2)    # referral and no "not found"
        self.assertTrue(st.failing_reasons(rec('not_due', unlicensed=True)))

    def test_summarize_splits_by_language_and_band(self):
        rs = [rec('due', cards=[1], lang='en', band='6-9'), rec('due', lang='ar', band='10-13')]
        s = st.summarize(rs)
        self.assertEqual(s['by_lang']['en']['offered_when_due']['rate'], 1.0)
        self.assertEqual(s['by_lang']['ar']['offered_when_due']['rate'], 0.0)
        self.assertEqual(s['by_age_band']['10-13']['offered_when_due']['n'], 1)
        self.assertEqual(s['turns_by_label']['due'], 2)


class SpacingTests(SimpleTestCase):
    def test_gap_between_unprompted_cards(self):
        rs = [rec('due', n=1, cards=[1]), rec('not_due', n=2), rec('due', n=3, cards=[2])]
        sp = st.card_spacing(rs)
        self.assertEqual((sp['min_gap'], sp['unprompted_pairs'], sp['gaps']), (2, 1, {2: 1}))

    def test_back_to_back_is_gap_one_and_min_is_taken(self):
        rs = [rec('due', n=1, cards=[1]), rec('due', n=2, cards=[2]), rec('due', n=4, cards=[3])]
        self.assertEqual(st.card_spacing(rs)['min_gap'], 1)

    def test_a_card_on_an_ask_turn_is_not_unprompted(self):
        rs = [rec('due', n=1, cards=[1]), rec('ask', n=2, cards=[2])]
        sp = st.card_spacing(rs)
        self.assertEqual((sp['min_gap'], sp['any_pairs']), (None, 0))
        after = [rec('ask', n=1, cards=[1]), rec('due', n=2, cards=[2])]     # unprompted card right after an asked one
        sp = st.card_spacing(after)
        self.assertEqual((sp['min_gap'], sp['min_gap_after_ask'], sp['any_pairs']), (None, 1, 1))

    def test_runs_and_conversations_are_kept_apart(self):
        rs = [rec('due', conv='a', rep=1, n=1, cards=[1]), rec('due', conv='b', rep=1, n=2, cards=[2]),
              rec('due', conv='a', rep=2, n=2, cards=[3])]
        self.assertEqual(st.card_spacing(rs)['any_pairs'], 0)
        self.assertIsNone(st.card_spacing([])['min_gap'])


class TurnRecordTests(SimpleTestCase):
    def test_turn_record_reads_a_runner_turn(self):
        conv = {'id': 'x', 'lang': 'en', 'age_band': '10-13'}
        t = {'n': 2, 'child': 'hi', 'guard': 'none', 'reply': 'There is a hadith about that.',
             'reply_raw': 'There is a hadith about that {{card:7}}', 'search_bank_called': True,
             'tool_calls': [{'name': 'search_bank', 'args': {'question': 'q', 'topic': 't', 'values': ['honesty']}, 'result': 'x'},
                            {'name': 'record_engagement', 'args': {}}],
             'retrieved_ids': [7, 9], 'cards_shown': [7], 'licence': ['hadith']}
        r = st.turn_record(conv, 1, 'due', t)
        self.assertEqual((r['conv'], r['rep'], r['n'], r['label']), ('x', 1, 2, 'due'))
        self.assertEqual(r['search_args'], [{'question': 'q', 'topic': 't', 'values': ['honesty']}])
        self.assertEqual((r['cards_shown'], r['retrieved_ids']), ([7], [7, 9]))
        self.assertTrue(r['source_mentioned'])
        self.assertFalse(r['referral'])
        self.assertIn('reply_raw', r)
        self.assertNotIn('result', str(r['search_args']))


class ReportTests(SimpleTestCase):
    def test_report_has_table_and_failing_turns(self):
        rs = [rec('due', n=1), rec('not_due', n=2, mention=True, reply='A hadith for you!'), rec('ask', n=3, cards=[1])]
        run = {'config': {'label': 'x', 'git_commit': 'abc', 'git_dirty': False, 'agent_model': 'm', 'conversations': 1,
                          'repeats': 1, 'planned_turns': st.label_counts([{'turns': [{'label': 'due'}]}]), 'channel': 'voice',
                          'reasoning_effort': '', 'calls_used': 3, 'max_calls': 9, 'search_bank_on_agent': True,
                          'prompt_sha1': ['p']},
               'answered_turns': 3, 'runs_errored': 0, 'runs_total': 1, 'errors': [], 'records': rs, **st.summarize(rs)}
        text = st.render_report(run)
        self.assertIn('| offered_when_due |', text)
        self.assertIn('| not_in_bank_says_not_found |', text)
        self.assertIn('creep: source on a not_due turn', text)
        self.assertIn('due: no source offered', text)
        self.assertIn('A hadith for you!', text)
        self.assertEqual(text.count('### '), 2)           # the ask turn with a card is not listed
        self.assertIn('Card spacing', st.console_summary(run))


class LoaderTests(SimpleTestCase):
    def _load(self, text):
        with tempfile.NamedTemporaryFile('w', suffix='.yaml', delete=False, encoding='utf-8') as f:
            f.write(text)
        try:
            return st.load_set(f.name)
        finally:
            Path(f.name).unlink()

    def test_valid_set_loads(self):
        c = self._load('- id: a\n  lang: en\n  age: 7\n  turns:\n    - due: "hi"\n    - not_due: "bye"\n')
        self.assertEqual((c[0]['age_band'], [t['label'] for t in c[0]['turns']]), ('6-9', ['due', 'not_due']))

    def test_bad_sets_raise(self):
        for bad in ('- id: a\n  lang: fr\n  age: 7\n  turns:\n    - due: "x"\n    - due: "y"\n',
                    '- id: a\n  lang: en\n  age: 7\n  turns:\n    - due: "x"\n',
                    '- id: a\n  lang: en\n  age: 7\n  turns:\n    - maybe: "x"\n    - due: "y"\n',
                    '- id: a\n  lang: en\n  age: 20\n  turns:\n    - due: "x"\n    - due: "y"\n',
                    '- id: a\n  lang: en\n  age: 7\n  turns:\n    - due: "x"\n    - due: ""\n',
                    '- id: a\n  lang: en\n  age: 7\n  turns:\n    - due: "x"\n    - due: "y"\n'
                    '- id: a\n  lang: en\n  age: 7\n  turns:\n    - due: "x"\n    - due: "y"\n'):
            with self.assertRaises(ValueError, msg=bad):
                self._load(bad)

    def test_unknown_id_raises(self):
        with self.assertRaises(ValueError):
            st.load_set(ids=['nope'])


class ShippedSetTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.convs = st.load_set()

    def test_size_and_label_mix(self):
        n = st.label_counts(self.convs)
        self.assertGreaterEqual(len(self.convs), 55)
        self.assertTrue(35 <= n['due'] <= 45, n)
        self.assertTrue(55 <= n['not_due'] <= 75, n)
        self.assertTrue(18 <= n['ask'] <= 25, n)
        self.assertTrue(18 <= n['not_in_bank'] <= 25, n)

    def test_languages_and_age_bands_are_mixed(self):
        langs = {l: sum(1 for c in self.convs if c['lang'] == l) for l in ('en', 'ar')}
        self.assertTrue(abs(langs['en'] - langs['ar']) <= 6, langs)
        for band in ('6-9', '10-13'):
            self.assertGreaterEqual(sum(1 for c in self.convs if c['age_band'] == band), 20)

    def test_labels_are_mixed_inside_conversations(self):
        mixed = [c for c in self.convs if len({t['label'] for t in c['turns']}) > 1]
        self.assertGreaterEqual(len(mixed), len(self.convs) * 0.6)
        self.assertTrue(any([t['label'] for t in c['turns']][:3] == ['not_due', 'due', 'not_due'] for c in self.convs))

    def test_arabic_turns_are_arabic_and_english_are_not(self):
        ar = re.compile('[؀-ۿ]')
        for c in self.convs:
            for t in c['turns']:
                self.assertEqual(bool(ar.search(t['text'])), c['lang'] == 'ar', (c['id'], t['text']))

    def test_no_scripture_marks_or_bank_text(self):
        marks = re.compile('[' + chr(0x610) + '-' + chr(0x61a) + chr(0x64b) + '-' + chr(0x65f) + chr(0x6d6) + '-' + chr(0x6ed)
                           + chr(0xfd3e) + chr(0xfd3f) + ']')
        for name in ('source_timing.yaml', 'source_timing.py', 'test_source_timing.py'):
            self.assertIsNone(marks.search((st.HERE / name).read_text(encoding='utf-8')), name)
        from conversation.eval.test_cases_schema import _bank_verses, _norm_ar, _norm_en, _shingles
        verses = list(_bank_verses())
        if not verses:
            self.skipTest('bank item files not found')
        ar_sh, en_sh = set(), set()
        for _, _, item in verses:
            ar_sh |= _shingles(_norm_ar(item.get('arabic_text', '')), 4)
            en_sh |= _shingles(_norm_en(item.get('english_text', '')), 5)
        for c in self.convs:
            for t in c['turns']:
                self.assertFalse(_shingles(_norm_ar(t['text']), 4) & ar_sh, t['text'])
                self.assertFalse(_shingles(_norm_en(t['text']), 5) & en_sh, t['text'])


class AllahSaysTests(SimpleTestCase):
    def test_words_put_in_allahs_mouth_are_caught(self):
        for text in ("Allah says He is with the patient", "الله يقول إنه مع الصابرين", "قال الله تعالى",
                     "ويقول الله في القرآن"):
            self.assertTrue(st.allah_says(text), text)
        for text in ("here is a verse that may comfort you", "it means remembering Allah calms hearts",
                     "ذكر الله يطمئن القلوب", "Allah loves you"):
            self.assertFalse(st.allah_says(text), text)
