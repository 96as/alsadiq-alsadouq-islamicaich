"""Validate conversation/eval/cases.yaml (task 09). No database, no network, no LLM.

Run: cd backend && python3 manage.py test conversation.eval --settings=config.settings_sqlite_test
 or: cd backend && python3 -m unittest conversation.eval.test_cases_schema

PyYAML is needed to read cases.yaml. It is not in requirements.txt yet, so the tests
skip (with a message) when it is missing. Add `PyYAML` to requirements.txt to make them mandatory.
"""
import json
import re
import unittest
from collections import Counter
from pathlib import Path

from . import (
    ALWAYS_ON, CASES_PATH, CATEGORIES, CHANNELS, CITING_MODES, FLAG_TYPES, ITEM_TYPES,
    LEVELS, MODES, MUST_NOT, REFER_TO, load_cases,
)

try:
    import yaml  # noqa: F401
except ImportError:  # pragma: no cover
    yaml = None

CONTENT_DIR = Path(__file__).resolve().parents[2] / 'session_moral_context' / 'content'

CASE_REQUIRED = {'id', 'category', 'lang', 'age', 'channels', 'input', 'expect'}
CASE_OPTIONAL = {'origin', 'input_voice', 'notes', 'tags'}
EXPECT_REQUIRED = {'mode', 'must_cite', 'must_not', 'rubric'}
EXPECT_OPTIONAL = {
    'level', 'values', 'items', 'refer_to', 'flag_safety_concern', 'flag_type', 'must_state_ai',
    'items_must_be_empty', 'notify_parent',
}

ID_RE = re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*-(ar|en)$')
HELDOUT_ID_RE = re.compile(r'^heldout-\d{2}-(ar|en)$')
TAG_RE = re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
VERSE_RE = re.compile(r'^verse:(\d{1,3})(?::(\d{1,3})(?:-(\d{1,3}))?)?$')
OTHER_ITEM_RE = re.compile(r'^(%s):[a-z0-9]+(?:-[a-z0-9]+)*$' % '|'.join(t for t in ITEM_TYPES if t != 'verse'))

ARABIC_LETTER_RE = re.compile(r'[\u0621-\u064a\u066e-\u06d3\u06fa-\u06ff]')
TASHKEEL_RE = re.compile(r'[\u064b-\u065f\u0670]')
# Ornate Quran brackets and Quranic annotation / recitation marks. None belongs in a case.
QURAN_MARK_RE = re.compile(r'[\ufd3e\ufd3f\u06d6-\u06dc\u06df-\u06e8\u06ea-\u06ed\u08d3-\u08ff]')

REQUIRED_FIRST_USE_TAGS = (
    'fatwa', 'verdict', 'recite_verse_text', 'invented_hadith', 'insult', 'claims_human',
    'scripture_without_source',
)
# Grounding cases may target any of the 38 bank values (values.json); at least this many
# must be covered in both languages.
MIN_GROUNDING_VALUES = 10


def _as_list(x):
    return x if isinstance(x, list) else [x]


def _norm_ar(text):
    text = re.sub(r'[\u064b-\u065f\u0670\u0640\u06d6-\u06ed]', '', text)
    text = re.sub('[أإآٱ]', 'ا', text).replace('ى', 'ي')
    return re.findall(r'[\u0621-\u064a]+', text)


def _norm_en(text):
    return re.findall(r"[a-z0-9']+", text.lower())


def _shingles(words, n):
    return {tuple(words[i:i + n]) for i in range(len(words) - n + 1)}


def _bank_verses():
    """Yield (surah, ayah, item dict) for every verse in the committed bank files."""
    for path in sorted((CONTENT_DIR / 'items').glob('*.json')):
        data = json.loads(path.read_text(encoding='utf-8'))
        for item in (data if isinstance(data, list) else data.get('items', [data])):
            if item.get('type') == 'verse':
                yield item['surah'], item['ayah'], item


def _strings(case):
    """Every free-text string in a case (for the scripture scans)."""
    out = [case.get('input', ''), case.get('input_voice', ''), case.get('notes', '')]
    out.append(case.get('expect', {}).get('rubric', ''))
    return [s for s in out if isinstance(s, str) and s]


@unittest.skipIf(yaml is None, 'PyYAML is not installed (pip install pyyaml); cases.yaml was not checked')
class CasesSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = load_cases(CASES_PATH)
        cls.value_slugs = None
        values_path = CONTENT_DIR / 'values.json'
        if values_path.exists():
            cls.value_slugs = {v['slug'] for v in json.loads(values_path.read_text(encoding='utf-8'))}

    # ---- top level ------------------------------------------------------
    def test_is_a_list_of_enough_cases(self):
        self.assertIsInstance(self.cases, list)
        self.assertGreaterEqual(len(self.cases), 70, 'the set is meant to hold about 70-90 cases')
        for case in self.cases:
            self.assertIsInstance(case, dict)

    def test_ids_unique_and_well_formed(self):
        ids = [c['id'] for c in self.cases]
        dupes = [i for i, n in Counter(ids).items() if n > 1]
        self.assertEqual(dupes, [], 'duplicate ids')
        for case in self.cases:
            with self.subTest(id=case['id']):
                m = ID_RE.match(case['id'])
                self.assertIsNotNone(m, 'id must be lower-case words joined by hyphens and end with -ar or -en')
                self.assertEqual(m.group(1), case['lang'], 'id suffix must equal lang')

    # ---- per-case shape -------------------------------------------------
    def test_case_keys(self):
        for case in self.cases:
            with self.subTest(id=case.get('id')):
                keys = set(case)
                self.assertFalse(CASE_REQUIRED - keys, f'missing {CASE_REQUIRED - keys}')
                self.assertFalse(keys - CASE_REQUIRED - CASE_OPTIONAL, f'unknown {keys - CASE_REQUIRED - CASE_OPTIONAL}')

    def test_case_fields(self):
        for case in self.cases:
            with self.subTest(id=case['id']):
                self.assertIn(case['category'], CATEGORIES)
                self.assertIn(case['lang'], ('ar', 'en'))
                self.assertIs(type(case['age']), int)
                self.assertTrue(6 <= case['age'] <= 13, 'age must be 6-13')
                self.assertIsInstance(case['channels'], list)
                self.assertTrue(case['channels'] and set(case['channels']) <= set(CHANNELS))
                self.assertEqual(len(case['channels']), len(set(case['channels'])))
                for field in ('input', 'input_voice'):
                    if field in case:
                        self.assertIsInstance(case[field], str)
                        self.assertTrue(case[field].strip())
                if 'input_voice' in case:
                    self.assertIn('voice', case['channels'], 'input_voice needs the voice channel')
                    self.assertNotEqual(case['input_voice'], case['input'])
                if 'origin' in case:
                    self.assertTrue(TAG_RE.match(case['origin'].lower().replace('.', '-')), case['origin'])
                if 'tags' in case:
                    self.assertIsInstance(case['tags'], list)
                    for tag in case['tags']:
                        self.assertTrue(TAG_RE.match(tag), tag)
                if 'notes' in case:
                    self.assertIsInstance(case['notes'], str)

    def test_every_case_runs_on_both_channels(self):
        for case in self.cases:
            with self.subTest(id=case['id']):
                self.assertEqual(sorted(case['channels']), sorted(CHANNELS))

    def test_language_of_inputs(self):
        for case in self.cases:
            for field in ('input', 'input_voice'):
                if field not in case:
                    continue
                has_arabic = bool(ARABIC_LETTER_RE.search(case[field]))
                with self.subTest(id=case['id'], field=field):
                    if case['lang'] == 'ar':
                        self.assertTrue(has_arabic, 'Arabic case without Arabic letters')
                    else:
                        self.assertFalse(has_arabic, 'English case containing Arabic letters')
            with self.subTest(id=case['id'], field='rubric'):
                self.assertGreaterEqual(
                    len(re.findall('[A-Za-z]', case['expect']['rubric'])), 20,
                    'rubric is written in English (Arabic terms may appear inside it)')

    # ---- expect block ---------------------------------------------------
    def test_expect_keys_and_vocabulary(self):
        for case in self.cases:
            exp = case['expect']
            with self.subTest(id=case['id']):
                keys = set(exp)
                self.assertFalse(EXPECT_REQUIRED - keys, f'missing {EXPECT_REQUIRED - keys}')
                self.assertFalse(keys - EXPECT_REQUIRED - EXPECT_OPTIONAL, f'unknown {keys - EXPECT_REQUIRED - EXPECT_OPTIONAL}')
                modes = _as_list(exp['mode'])
                self.assertTrue(modes and set(modes) <= set(MODES), modes)
                self.assertEqual(len(modes), len(set(modes)))
                if 'level' in exp:
                    levels = _as_list(exp['level'])
                    self.assertTrue(levels and set(levels) <= set(LEVELS), levels)
                self.assertIsInstance(exp['must_cite'], bool)
                self.assertIsInstance(exp['must_not'], list)
                self.assertTrue(exp['must_not'], 'must_not is never empty')
                self.assertTrue(set(exp['must_not']) <= set(MUST_NOT), set(exp['must_not']) - set(MUST_NOT))
                self.assertEqual(len(exp['must_not']), len(set(exp['must_not'])))
                self.assertIsInstance(exp['rubric'], str)
                self.assertTrue(20 <= len(exp['rubric']) <= 450, 'rubric is one short line (20-450 chars)')
                self.assertNotIn('\n', exp['rubric'])
                if 'refer_to' in exp:
                    self.assertTrue(exp['refer_to'] and set(exp['refer_to']) <= set(REFER_TO), exp['refer_to'])
                if 'flag_safety_concern' in exp:
                    self.assertIsInstance(exp['flag_safety_concern'], bool)
                if 'flag_type' in exp:
                    self.assertTrue(exp['flag_type'] and set(exp['flag_type']) <= set(FLAG_TYPES), exp['flag_type'])
                if 'must_state_ai' in exp:
                    self.assertIs(exp['must_state_ai'], True)
                if 'items_must_be_empty' in exp:
                    self.assertIs(exp['items_must_be_empty'], True)
                if 'notify_parent' in exp:
                    self.assertIsInstance(exp['notify_parent'], bool)

    def test_values_are_known_slugs(self):
        if self.value_slugs is None:
            self.skipTest('values.json not found')
        for case in self.cases:
            vals = case['expect'].get('values', [])
            with self.subTest(id=case['id']):
                self.assertIsInstance(vals, list)
                self.assertTrue(set(vals) <= self.value_slugs, set(vals) - self.value_slugs)

    def test_item_pointers(self):
        for case in self.cases:
            items = case['expect'].get('items', [])
            with self.subTest(id=case['id']):
                self.assertIsInstance(items, list)
                self.assertEqual(len(items), len(set(items)))
                for ptr in items:
                    m = VERSE_RE.match(ptr)
                    if m:
                        surah = int(m.group(1))
                        self.assertTrue(1 <= surah <= 114, ptr)
                        if m.group(2):
                            start = int(m.group(2))
                            end = int(m.group(3) or start)
                            self.assertTrue(1 <= start <= end, ptr)
                    else:
                        self.assertIsNotNone(OTHER_ITEM_RE.match(ptr), f'bad item pointer {ptr!r}')

    # ---- consistency rules ----------------------------------------------
    def test_consistency_rules(self):
        for case in self.cases:
            exp = case['expect']
            modes = set(_as_list(exp['mode']))
            levels = set(_as_list(exp['level'])) if 'level' in exp else set()
            with self.subTest(id=case['id']):
                if not modes & {'NONE', 'SAFETY'}:
                    self.assertTrue(levels, 'a religious-content case needs a level')
                if modes & {'NONE', 'SAFETY'}:
                    self.assertEqual(len(modes), 1, 'NONE and SAFETY are never mixed with another mode')
                if levels == {'D'}:
                    self.assertEqual(modes, {'REFER'}, 'Level D always means REFER')
                if 'REFER' in modes or 'DISAGREE_AND_REFER' in modes:
                    self.assertTrue(exp.get('refer_to'), 'a referral mode needs refer_to')
                if modes == {'DECLINE_NO_SOURCE'}:
                    self.assertFalse(exp['must_cite'])
                if exp['must_cite']:
                    self.assertTrue(modes <= set(CITING_MODES), 'must_cite needs a citing mode')
                    self.assertTrue(exp.get('values') or exp.get('items'), 'must_cite needs values or items')
                if modes == {'NONE'}:
                    self.assertFalse(exp['must_cite'])
                if modes <= {'SAFETY', 'NONE'}:
                    self.assertIs(exp.get('items_must_be_empty'), True, 'SAFETY and NONE turns serve nothing')
                if exp.get('items_must_be_empty'):
                    self.assertFalse(exp.get('items'), 'items_must_be_empty contradicts items')
                    self.assertFalse(exp['must_cite'])
                    self.assertTrue(modes <= {'SAFETY', 'NONE', 'REFER', 'DECLINE_NO_SOURCE'}, modes)
                if 'notify_parent' in exp:
                    self.assertEqual(modes, {'SAFETY'}, 'notify_parent only applies to SAFETY')
                if modes == {'SAFETY'}:
                    self.assertIs(exp.get('flag_safety_concern'), True)
                    self.assertTrue(exp.get('flag_type'), 'SAFETY needs flag_type')
                    self.assertIn('trusted_adult', exp.get('refer_to', []))
                if exp.get('flag_type'):
                    self.assertIs(exp.get('flag_safety_concern'), True, 'flag_type only when flagging')
                if 'parent_route_for_safety' in exp['must_not']:
                    self.assertEqual(modes, {'SAFETY'})
                    self.assertNotIn('parent', exp.get('refer_to', []))
                    self.assertIs(exp.get('notify_parent'), False, 'family-sourced harm never alerts a parent')
                if case['category'] in ('safety-negative', 'everyday-chat'):
                    self.assertEqual(modes, {'NONE'})
                    self.assertIs(exp.get('flag_safety_concern'), False)
                if exp.get('must_state_ai'):
                    self.assertEqual(modes, {'NONE'})
                    self.assertIn('claims_human', exp['must_not'])
                if case['category'] == 'ai-disclosure':
                    self.assertTrue(exp.get('must_state_ai'))
                if case['category'] == 'personal-case':
                    self.assertEqual(levels, {'D'})
                if case['category'] == 'safety':
                    self.assertEqual(modes, {'SAFETY'})
                    self.assertIs(exp.get('flag_safety_concern'), True)

    # ---- no scripture anywhere ------------------------------------------
    def test_no_quranic_marks(self):
        for case in self.cases:
            for text in _strings(case):
                with self.subTest(id=case['id']):
                    self.assertIsNone(QURAN_MARK_RE.search(text), 'Quranic marks or ornate brackets found')

    def test_arabic_inputs_are_not_heavily_vowelled(self):
        for case in self.cases:
            for field in ('input', 'input_voice'):
                text = case.get(field)
                if not text:
                    continue
                letters = len(ARABIC_LETTER_RE.findall(text))
                marks = len(TASHKEEL_RE.findall(text))
                with self.subTest(id=case['id'], field=field):
                    self.assertLessEqual(marks, max(2, letters * 0.08), 'child chat is not fully vowelled; looks like scripture')

    def test_no_text_copied_from_bank_verses(self):
        verses = list(_bank_verses())
        if not verses:
            self.skipTest('bank item files not found')
        ar_shingles, en_shingles = set(), set()
        for _, _, item in verses:
            ar_shingles |= _shingles(_norm_ar(item.get('arabic_text', '')), 4)
            en_shingles |= _shingles(_norm_en(item.get('english_text', '')), 5)
        for case in self.cases:
            for text in _strings(case):
                with self.subTest(id=case['id']):
                    self.assertFalse(_shingles(_norm_ar(text), 4) & ar_shingles, 'four words of a bank verse (Arabic)')
                    self.assertFalse(_shingles(_norm_en(text), 5) & en_shingles, 'five words of a bank verse (English)')

    # ---- coverage -------------------------------------------------------
    def test_category_minimums(self):
        counts = Counter(c['category'] for c in self.cases)
        minimums = {
            'test-question': 24, 'grounding': 20, 'ai-disclosure': 6, 'story-request': 3,
            'invented-hadith': 3, 'personal-case': 4, 'safety': 8, 'safety-negative': 4,
            'everyday-chat': 4, 'hostile': 2, 'misquote': 2,
            'translation': 2, 'level-coverage': 6, 'out-of-bank': 2,
        }
        self.assertEqual(set(minimums), set(CATEGORIES))
        for category, minimum in minimums.items():
            with self.subTest(category=category):
                self.assertGreaterEqual(counts[category], minimum)

    def test_twelve_test_questions_in_both_languages(self):
        langs = {}
        for case in self.cases:
            origin = case.get('origin', '')
            if case['category'] == 'test-question':
                langs.setdefault(origin, set()).add(case['lang'])
        for n in range(1, 13):
            with self.subTest(question=n):
                self.assertEqual(langs.get(f'r5-Q{n}'), {'ar', 'en'}, f'r5-Q{n} needs an Arabic and an English case')

    def test_grounding_values_are_bank_values_in_both_languages(self):
        if self.value_slugs is None:
            self.skipTest('values.json not found')
        seen = {}
        for case in self.cases:
            if case['category'] == 'grounding':
                for slug in case['expect'].get('values', []):
                    seen.setdefault(slug, set()).add(case['lang'])
        self.assertTrue(set(seen) <= self.value_slugs, set(seen) - self.value_slugs)
        both = {slug for slug, langs in seen.items() if langs == {'ar', 'en'}}
        self.assertGreaterEqual(len(both), MIN_GROUNDING_VALUES, sorted(seen))

    def test_grounding_pointers_exist_in_the_bank(self):
        """Grounding cases target content the bank holds today, so every verse pointer must resolve."""
        index = {}
        for surah, ayah, item in _bank_verses():
            index[(surah, ayah)] = set(item.get('values', []))
        if not index:
            self.skipTest('bank item files not found')
        for case in self.cases:
            if case['category'] != 'grounding':
                continue
            exp = case['expect']
            with self.subTest(id=case['id']):
                for ptr in exp['items']:
                    m = VERSE_RE.match(ptr)
                    self.assertIsNotNone(m, f'grounding items must be verse pointers: {ptr}')
                    key = (int(m.group(1)), int(m.group(2)))
                    self.assertIn(key, index, f'{ptr} is not in the bank')
                    self.assertTrue(index[key] & set(exp['values']), f'{ptr} is not linked to {exp["values"]}')
                self.assertEqual(exp['mode'], 'ANSWER')
                self.assertTrue(exp['must_cite'])

    def test_all_levels_and_modes_used(self):
        levels, modes = set(), set()
        for case in self.cases:
            levels |= set(_as_list(case['expect'].get('level', [])))
            modes |= set(_as_list(case['expect']['mode']))
        self.assertEqual(levels, set(LEVELS))
        self.assertEqual(modes, set(MODES) - {'CLARIFY'})

    def test_must_not_vocabulary_is_exercised(self):
        used = Counter(t for c in self.cases for t in c['expect']['must_not'])
        for tag in REQUIRED_FIRST_USE_TAGS:
            with self.subTest(tag=tag):
                self.assertGreater(used[tag], 0)
        unused = set(MUST_NOT) - set(used)
        self.assertFalse(unused, f'vocabulary tags that no case uses: {sorted(unused)}')

    def test_always_on_tags_are_defined(self):
        self.assertTrue(set(ALWAYS_ON) <= set(MUST_NOT))

    def test_safety_sets_have_both_languages_and_negative_controls(self):
        safety = [c for c in self.cases if c['category'] == 'safety']
        self.assertEqual({c['lang'] for c in safety}, {'ar', 'en'})
        self.assertTrue(any('parent_route_for_safety' in c['expect']['must_not'] for c in safety))
        self.assertTrue(any(c['expect'].get('notify_parent') is None for c in safety),
                        'some safety cases (self-harm, grooming, bullying) leave the parent alert open')
        for category in ('safety-negative', 'everyday-chat'):
            group = [c for c in self.cases if c['category'] == category]
            self.assertEqual({c['lang'] for c in group}, {'ar', 'en'}, category)

    def test_inputs_are_unique(self):
        seen = Counter(c['input'] for c in self.cases)
        self.assertEqual([i for i, n in seen.items() if n > 1], [], 'identical input in two cases')

    def test_heldout_set(self):
        held = [c for c in self.cases if 'heldout' in c.get('tags', [])]
        self.assertGreaterEqual(len(held), 20)
        self.assertEqual({c['lang'] for c in held}, {'ar', 'en'})
        self.assertGreaterEqual(len({c['category'] for c in held}), 7)
        for case in held:
            with self.subTest(id=case['id']):
                self.assertRegex(case['id'], HELDOUT_ID_RE, 'held-out ids are opaque: heldout-NN-ar|en')
                self.assertNotIn('origin', case)
                self.assertNotIn('notes', case)
        self.assertEqual(sorted(c['id'] for c in self.cases if HELDOUT_ID_RE.match(c['id'])),
                         sorted(c['id'] for c in held), 'every heldout-NN id carries the heldout tag, and the reverse')

    def test_reviewer_probe_cases_present(self):
        probes = [c for c in self.cases if c.get('origin') in ('probe-1', 'probe-2')]
        self.assertEqual(len(probes), 50)

    def test_some_cases_have_spoken_variants(self):
        self.assertGreaterEqual(sum('input_voice' in c for c in self.cases), 5)


if __name__ == '__main__':
    unittest.main()
