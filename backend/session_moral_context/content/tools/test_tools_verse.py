"""Tests for the verse-text tools. Pure python unittest, no network, no Django.

Run from this directory:  python3 -m unittest -v test_tools_verse
All Arabic below is obviously synthetic placeholder text, never scripture.
"""
import contextlib
import hashlib
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import cut_ayah_clips  # noqa: E402
import fetch_verse  # noqa: E402
import kfgqpc  # noqa: E402
import refresh_arabic  # noqa: E402
import verify_arabic  # noqa: E402

NBSP = '\xa0'
REAL_V2 = HERE / '.cache' / 'quran-complex' / 'UthmanicHafs_v2-0 data' / 'hafsData_v2-0.json'
# Placeholder "KFGQPC" rows. Distinctive code points (U+0671 alef wasla, U+06E1, U+0657) are
# included only so byte-for-byte handling is exercised; the words are made up.
ROWS = [
    {'sura_no': 1, 'aya_no': 1, 'aya_text': 'ٱلنص 1 التجريبيۡ' + NBSP + '١',
     'aya_text_emlaey': 'نص تجريبي واحد'},
    {'sura_no': 1, 'aya_no': 2, 'aya_text': 'كلمة٣ تجريبيةٗ ثانية' + NBSP + '۝٢',
     'aya_text_emlaey': 'كلمة تجريبية ثانية'},
    {'sura_no': 2, 'aya_no': 5, 'aya_text': 'نص PLACEHOLDER ثالث' + NBSP + '٥',
     'aya_text_emlaey': 'نص ثالث'},
]


def write_json(path, data, bom=False):
    text = json.dumps(data, ensure_ascii=False, indent=2) + '\n'
    Path(path).write_text(text, encoding='utf-8-sig' if bom else 'utf-8')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def stripped(i):
    return kfgqpc.strip_ayah_number(ROWS[i]['aya_text'])


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.data = self.tmp / 'hafsData_v99.json'
        write_json(self.data, ROWS)
        self.items = self.tmp / 'items'
        self.items.mkdir()

    def kf(self):
        return kfgqpc.Kfgqpc(self.data, sha(self.data))

    def verse_item(self, s, a, text, **extra):
        it = {'type': 'verse', 'surah': s, 'ayah': a, 'arabic_text': text,
              'english_text': f'English {s}:{a}', 'translation_name': 'Saheeh International',
              'source_site': 'quranpedia.net', 'source_url': 'https://example.invalid/x',
              'audio_url': 'https://example.invalid/a.mp3', 'values': ['v'], 'age_band': 'all',
              'verification_status': 'reviewed', 'reviewed_by': 'Tester', 'reviewed_at': '2026-10-04'}
        it.update(extra)
        return it

    def write_items(self, name, items):
        write_json(self.items / name, items)


class TestKfgqpc(Base):
    def test_strip_only_trailing_number(self):
        self.assertEqual(stripped(0), 'ٱلنص 1 التجريبيۡ')  # internal digit kept
        self.assertEqual(stripped(1), 'كلمة٣ تجريبيةٗ ثانية')  # internal digit kept, U+06DD dropped with number
        self.assertEqual(kfgqpc.strip_ayah_number('نص'), 'نص')  # nothing to strip: unchanged

    def test_strip_presentation_form_glyph(self):
        # KFGQPC v2-0: NBSP (or a plain space, e.g. 2:286) + ONE number glyph in U+FC00..U+FDFF
        self.assertEqual(kfgqpc.strip_ayah_number('نص' + NBSP + '\ufc0b'), 'نص')
        self.assertEqual(kfgqpc.strip_ayah_number('نص' + ' ' + '\ufd1d'), 'نص')  # ﴝ
        # A bare trailing glyph (no separator) is not an ayah number: keep it.
        self.assertEqual(kfgqpc.strip_ayah_number('نص' + '\ufc00'), 'نص' + '\ufc00')
        self.assertEqual(kfgqpc.strip_ayah_number('نص' + NBSP + '\ufc0b\n'), 'نص')
        # only the TRAILING glyph goes; a glyph elsewhere and real letters stay
        self.assertEqual(kfgqpc.strip_ayah_number('نص' + '\ufc0b' + ' كلمة' + NBSP + '\ufc0b'), 'نص\ufc0b كلمة')
        self.assertEqual(kfgqpc.strip_ayah_number('ﻻ' + NBSP + '\ufc0b'), 'ﻻ')  # U+FEFB is outside the range: kept
        self.assertEqual(kfgqpc.strip_ayah_number('نص\ufeff'), 'نص\ufeff')

    def test_glyph_rows_load_stripped(self):
        f = self.tmp / 'hafsData_v2-0.json'
        write_json(f, [{'sura_no': 49, 'aya_no': 12, 'aya_text': 'نص' + NBSP + '\ufc0b'},
                       {'sura_no': 2, 'aya_no': 286, 'aya_text': 'نص' + ' ' + '\ufd1d'}])
        kf = kfgqpc.Kfgqpc(f)
        self.assertEqual((kf.get(49, 12), kf.get(2, 286)), ('نص', 'نص'))

    @unittest.skipUnless(REAL_V2.is_file(), 'pinned KFGQPC v2-0 JSON not in tools/.cache')
    def test_real_v2_file_fully_stripped(self):
        kf = kfgqpc.Kfgqpc(REAL_V2)
        raw = json.loads(REAL_V2.read_text(encoding='utf-8-sig'))
        self.assertEqual(len(kf.text), 6236)
        for row in raw:
            key, t = (row['sura_no'], row['aya_no']), row['aya_text']
            s = kf.text[key]
            self.assertTrue(t.startswith(s), key)
            # exactly NBSP (or one space) + one glyph was removed, nothing else
            self.assertRegex(t[len(s):], '^[\xa0 ][\ufc00-\ufdff]$', key)
            for text in (s, kf.search.get(key, '')):
                self.assertNotRegex(text, '[\ufc00-\ufdff]', key)  # no glyph anywhere (so no letter lost to it)
                self.assertNotRegex(text, '[\xa0 \\s]$', key)

    def test_strip_number_with_trailing_whitespace(self):
        self.assertEqual(kfgqpc.strip_ayah_number('نص' + NBSP + '\u0663\n'), 'نص')
        self.assertEqual(kfgqpc.strip_ayah_number('نص' + NBSP + '\u06dd\u0663 '), 'نص')

    def test_text_is_byte_for_byte_except_number(self):
        kf = self.kf()
        self.assertEqual(kf.get(1, 1), ROWS[0]['aya_text'][:-2])  # NBSP + one digit removed
        self.assertTrue(kf.get(1, 1).startswith('ٱ'))
        self.assertNotIn(NBSP, kf.get(2, 5))

    def test_search_text(self):
        kf = self.kf()
        self.assertEqual(kf.get_search(1, 1), 'نص تجريبي واحد')
        self.assertIsNone(kf.get_search(9, 9))

    def test_edition_string(self):
        kf = self.kf()
        self.assertEqual(kf.release, 'v99')
        self.assertEqual(kf.edition(), f'KFGQPC Hafs v99 sha256:{sha(self.data)[:12]}')
        self.assertEqual(kfgqpc.Kfgqpc(self.data, release='v2-0').release, 'v2-0')

    def test_sha_mismatch_fails(self):
        with self.assertRaises(kfgqpc.KfgqpcError):
            kfgqpc.Kfgqpc(self.data, '0' * 64)

    def test_sha_pin_case_and_space_insensitive(self):
        self.assertTrue(kfgqpc.Kfgqpc(self.data, ' ' + sha(self.data).upper() + ' ').pinned)

    def test_variants_sora_bom_wrapped_strings(self):
        rows = [{'sora': '3', 'aya_no': '7', 'aya_text': 'نص' + NBSP + '٧'}]
        for name, payload, bom in (('a.json', rows, True), ('b.json', {'verses': rows}, False)):
            f = self.tmp / name
            write_json(f, payload, bom=bom)
            self.assertEqual(kfgqpc.Kfgqpc(f).get(3, 7), 'نص', name)

    def test_missing_verse_and_duplicates(self):
        with self.assertRaises(kfgqpc.KfgqpcError):
            self.kf().get(114, 6)
        f = self.tmp / 'dup.json'
        write_json(f, ROWS + [ROWS[0]])
        with self.assertRaises(kfgqpc.KfgqpcError):
            kfgqpc.Kfgqpc(f)

    def test_encoding_report(self):
        rep = self.kf().encoding_report()
        self.assertEqual(rep['U+0671'], 1)
        self.assertEqual(rep['U+0657'], 1)
        self.assertEqual(rep['U+08F0'], 0)


class TestVerify(Base):
    def run_verify(self, *extra):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = verify_arabic.main(['--kfgqpc', str(self.data), '--sha256', sha(self.data),
                                       '--items', str(self.items), *extra])
        return code, out.getvalue()

    def test_all_match(self):
        self.write_items('a.json', [self.verse_item(1, 1, stripped(0)), self.verse_item(1, 2, stripped(1))])
        code, out = self.run_verify()
        self.assertEqual(code, 0)
        self.assertIn('0 mismatching verse(s)', out)
        self.assertIn('1:1 OK', out)

    def test_mismatch_exit_1_and_ignores_non_verse(self):
        self.write_items('a.json', [
            self.verse_item(1, 1, stripped(0)),
            self.verse_item(1, 2, 'نص مختلف'),
            {'type': 'hadith', 'arabic_text': 'x'},
        ])
        code, out = self.run_verify()
        self.assertEqual(code, 1)
        self.assertIn('1:2 MISMATCH', out)
        self.assertIn('1 mismatching verse(s)', out)

    def test_nfc_equal_is_still_a_mismatch(self):
        import unicodedata
        text = 'á'  # decomposed; NFC-equal to the composed form below
        f = self.tmp / 'nfc.json'
        write_json(f, [{'sura_no': 1, 'aya_no': 1, 'aya_text': unicodedata.normalize('NFC', text)}])
        self.write_items('a.json', [self.verse_item(1, 1, text)])
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = verify_arabic.main(['--kfgqpc', str(f), '--items', str(self.items)])
        self.assertEqual(code, 1)
        self.assertIn('NFC-equal', out.getvalue())

    def test_verse_missing_from_file(self):
        self.write_items('a.json', [self.verse_item(50, 1, 'x')])
        code, out = self.run_verify()
        self.assertEqual(code, 1)
        self.assertIn('not in the KFGQPC file', out)

    def test_strict_requires_new_fields(self):
        self.write_items('a.json', [self.verse_item(1, 1, stripped(0))])
        self.assertEqual(self.run_verify()[0], 0)
        self.assertEqual(self.run_verify('--strict')[0], 1)

    def test_strict_rejects_trailing_junk(self):
        # The v2-0 bug: stripper left the number behind on BOTH sides, so file == item.
        class Stub:
            def __init__(self, want):
                self.text = {(1, 1): want}

            get = lambda self, s, a: self.text[(s, a)]  # noqa: E731
            get_search = lambda self, s, a: None  # noqa: E731
            edition = lambda self: 'ed'  # noqa: E731
        for junk in (NBSP, ' ', '\n', '1', '\u0663', '\ufc0b', '\ufd1d'):
            with self.subTest(junk=junk):
                text = 'نص' + junk
                item = self.verse_item(1, 1, text, text_edition='ed')
                self.assertEqual(verify_arabic.check_item(item, Stub(text)), [])  # lenient mode: equal, passes
                problems = verify_arabic.check_item(item, Stub(text), strict=True)
                self.assertEqual(len(problems), 1, problems)
                self.assertIn('ends with', problems[0])
        clean = self.verse_item(1, 1, 'نص', text_edition='ed')
        self.assertEqual(verify_arabic.check_item(clean, Stub('نص'), strict=True), [])

    def test_strict_cli_fails_on_unstripped_number(self):
        f = self.tmp / 'hafsData_v97.json'
        write_json(f, [{'sura_no': 1, 'aya_no': 1, 'aya_text': 'نص' + NBSP}])  # no number: stays unstripped
        kf = kfgqpc.Kfgqpc(f, sha(f))
        self.write_items('a.json', [self.verse_item(1, 1, 'نص' + NBSP, text_edition=kf.edition())])
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = verify_arabic.main(['--kfgqpc', str(f), '--sha256', sha(f), '--items', str(self.items), '--strict'])
        self.assertEqual(code, 1)
        self.assertIn('ends with NBSP/space/digit/ayah-number glyph (U+00A0)', out.getvalue())

    def test_stale_search_and_edition_detected(self):
        kf = self.kf()
        good = self.verse_item(1, 1, stripped(0), arabic_text_search=kf.get_search(1, 1), text_edition=kf.edition())
        bad = self.verse_item(1, 2, stripped(1), arabic_text_search='غير', text_edition='old')
        self.write_items('a.json', [good, bad])
        code, out = self.run_verify('--strict')
        self.assertEqual(code, 1)
        self.assertIn('1:1 OK', out)
        self.assertIn('arabic_text_search differs', out)
        self.assertIn('text_edition', out)

    def test_strict_without_sha_exit_2(self):
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            self.assertEqual(verify_arabic.main(['--kfgqpc', str(self.data), '--items', str(self.items),
                                                 '--strict']), 2)
        self.assertIn('--sha256', err.getvalue())
        with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(verify_arabic.main(['--kfgqpc', str(self.data), '--items', str(self.items)]), 0)

    def test_pin_mismatch_exit_2(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(verify_arabic.main(['--kfgqpc', str(self.data), '--sha256', '0' * 64,
                                                 '--items', str(self.items)]), 2)

    def test_legacy_positional_form(self):
        self.write_items('a.json', [self.verse_item(1, 1, stripped(0))])
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(verify_arabic.main([str(self.data), str(self.items)]), 0)


class TestRefresh(Base):
    def setUp(self):
        super().setUp()
        self.hadith = {'type': 'hadith', 'collection': 'x', 'arabic_text': 'نص حديث تجريبي', 'verification_status': 'seeded'}
        self.write_items('a.json', [
            self.verse_item(1, 1, 'old one'), self.hadith, self.verse_item(1, 2, 'old two')])
        self.write_items('b.json', [self.verse_item(2, 5, stripped(2))])  # will need new fields only
        self.read = lambda n: json.loads((self.items / n).read_text(encoding='utf-8'))
        self.args = ['--kfgqpc', str(self.data), '--sha256', sha(self.data), '--items', str(self.items)]

    def run_refresh(self, *extra):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            refresh_arabic.main([*self.args, *extra])
        return out.getvalue()

    def test_dry_run_writes_nothing(self):
        before = {p.name: p.read_bytes() for p in self.items.glob('*.json')}
        out = self.run_refresh('--dry-run')
        self.assertIn('would change 3 of 3 verse(s) in 2 file(s)', out)
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.items.glob('*.json')})

    def test_refresh_replaces_and_preserves(self):
        self.run_refresh()
        a = self.read('a.json')
        kf = self.kf()
        self.assertEqual(a[0]['arabic_text'], stripped(0))
        self.assertEqual(a[0]['arabic_text_search'], 'نص تجريبي واحد')
        self.assertEqual(a[0]['text_edition'], kf.edition())
        # key order: new keys directly after arabic_text, rest unchanged
        self.assertEqual(list(a[0])[:6], ['type', 'surah', 'ayah', 'arabic_text', 'arabic_text_search', 'text_edition'])
        self.assertEqual(list(a[0])[6:], ['english_text', 'translation_name', 'source_site', 'source_url',
                                          'audio_url', 'values', 'age_band', 'verification_status',
                                          'reviewed_by', 'reviewed_at'])
        # status/review keys untouched on purpose
        self.assertEqual((a[0]['verification_status'], a[0]['reviewed_by'], a[0]['reviewed_at']),
                         ('reviewed', 'Tester', '2026-10-04'))
        # non-verse untouched
        self.assertEqual(a[1], self.hadith)
        # english untouched without --fix-english
        self.assertEqual(a[0]['english_text'], 'English 1:1')

    def test_style_and_idempotent(self):
        self.run_refresh()
        raw = (self.items / 'a.json').read_text(encoding='utf-8')
        self.assertEqual(raw, json.dumps(json.loads(raw), ensure_ascii=False, indent=2) + '\n')
        snapshot = {p.name: p.read_bytes() for p in self.items.glob('*.json')}
        out = self.run_refresh()
        self.assertIn('changed 0 of 3 verse(s) in 0 file(s)', out)
        self.assertEqual(snapshot, {p.name: p.read_bytes() for p in self.items.glob('*.json')})

    def test_missing_verse_aborts_before_writing(self):
        self.write_items('c.json', [self.verse_item(99, 1, 'x')])
        before = {p.name: p.read_bytes() for p in self.items.glob('*.json')}
        with self.assertRaises(SystemExit), contextlib.redirect_stderr(io.StringIO()):
            self.run_refresh()
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.items.glob('*.json')})

    def test_verify_passes_after_refresh(self):
        self.run_refresh()
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(verify_arabic.main(['--kfgqpc', str(self.data), '--sha256', sha(self.data),
                                                 '--items', str(self.items), '--strict']), 0)

    def test_stale_search_dropped_when_file_has_none(self):
        rows = [dict(r) for r in ROWS]
        del rows[0]['aya_text_emlaey']
        f = self.tmp / 'hafsData_v98.json'
        write_json(f, rows)
        self.write_items('a.json', [self.verse_item(1, 1, 'old', arabic_text_search='stale')])
        err = io.StringIO()
        out = io.StringIO()
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(out):
            refresh_arabic.main(['--kfgqpc', str(f), '--sha256', sha(f), '--items', str(self.items)])
        it = self.read('a.json')[0]
        self.assertNotIn('arabic_text_search', it)
        self.assertEqual(it['text_edition'], kfgqpc.Kfgqpc(f).edition())
        self.assertIn('arabic_text_search', out.getvalue())
        self.assertIn('warning', err.getvalue())
        # a second run is a no-op
        with contextlib.redirect_stdout(io.StringIO()) as o2:
            refresh_arabic.main(['--kfgqpc', str(f), '--sha256', sha(f), '--items', str(self.items)])
        self.assertIn('changed 0 of 2', o2.getvalue())

    def test_requires_pin(self):
        with self.assertRaises(SystemExit), contextlib.redirect_stderr(io.StringIO()):
            refresh_arabic.main(['--kfgqpc', str(self.data), '--items', str(self.items)])

    def test_fix_english_shapes(self):
        shapes = {
            'risan': {'1': [{'chapter': 1, 'verse': 1, 'text': '(1) Fixed one.[2]', 'footnotes': 'n'}]},
            'quranenc': {'result': [{'sura': '1', 'aya': '1', 'translation': '(1) Fixed one.'}]},
            'map': {'1:1': 'Fixed one.'},
        }
        for name, payload in shapes.items():
            with self.subTest(name):
                self.write_items('a.json', [self.verse_item(1, 1, 'old')])
                src = self.tmp / f'{name}.json'
                write_json(src, payload)
                self.run_refresh('--fix-english', str(src))
                self.assertEqual(self.read('a.json')[0]['english_text'], 'Fixed one.')


class TestFetchVerse(Base):
    def fake_checked(self, url, ok):
        if '/translation/' in url:
            return {'ayah_number': 1, 'translation_text': '(1) Placeholder English one[3]<br /><div class="foot-notes">n</div>'}
        return {'surah': 1, 'number': 1, 'text': '﻿نص تجريبي' + NBSP + '١'}

    def build(self, kf=None, **kw):
        with mock.patch.object(fetch_verse, 'checked', self.fake_checked), \
                mock.patch.object(fetch_verse, 'cached', lambda url, method='GET': 'https://example.invalid/canon'):
            return fetch_verse.verse(1, 1, kf, **kw)

    def test_default_mushaf_is_2(self):
        self.assertEqual(fetch_verse.MUSHAF_ID, 2)
        urls = []

        def spy(url, ok):
            urls.append(url)
            return self.fake_checked(url, ok)
        with mock.patch.object(fetch_verse, 'checked', spy), \
                mock.patch.object(fetch_verse, 'cached', lambda url, method='GET': 'u'):
            fetch_verse.verse(1, 1)
        self.assertTrue(any('/mushafs/2/1/1' in u for u in urls), urls)
        self.assertFalse(any('/mushafs/1/' in u for u in urls))

    def test_quranpedia_mode(self):
        it = self.build(edition_date='2026-10-04')
        self.assertEqual(it['arabic_text'], 'نص تجريبي')  # BOM and trailing number removed
        self.assertEqual(it['text_edition'], 'Quranpedia mushaf 2 2026-10-04')
        self.assertNotIn('arabic_text_search', it)
        self.assertEqual(it['english_text'], 'Placeholder English one')  # no full stop added
        self.assertEqual(it['verification_status'], 'seeded')
        self.assertIn('audio_url', it)

    def test_kfgqpc_mode(self):
        kf = self.kf()
        it = self.build(kf)
        self.assertEqual(it['arabic_text'], kf.get(1, 1))
        self.assertEqual(it['arabic_text_search'], 'نص تجريبي واحد')
        self.assertEqual(it['text_edition'], kf.edition())
        self.assertEqual(list(it)[:6], ['type', 'surah', 'ayah', 'arabic_text', 'arabic_text_search', 'text_edition'])

    def test_audio_source_none(self):
        self.assertNotIn('audio_url', self.build(audio_source='none'))

    def test_english_never_adds_punctuation(self):
        self.assertEqual(fetch_verse.english('(4) And your clothing purify'), 'And your clothing purify')
        self.assertEqual(fetch_verse.english('(5) Text with note[12].'), 'Text with note.')

    def test_cli_requires_pin_with_kfgqpc(self):
        with self.assertRaises(SystemExit), contextlib.redirect_stderr(io.StringIO()):
            fetch_verse.main(['--kfgqpc', str(self.data), '1:1'])


@unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'), 'ffmpeg/ffprobe not installed')
class TestCutClips(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.src = self.tmp / 'surah.mp3'
        subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'sine=frequency=440:duration=6',
                        '-c:a', 'libmp3lame', str(self.src)], check=True)
        self.timing = [
            {'ayah': 0, 'start_time': 0, 'end_time': 500},  # intro, ignored
            {'ayah': 1, 'start_time': 500, 'end_time': 2500},
            {'ayah': 2, 'start_time': 2500, 'end_time': 5000},
        ]
        self.tfile = self.tmp / 't.json'
        self.tfile.write_text(json.dumps(self.timing), encoding='utf-8')

    def test_timing_map_and_window(self):
        self.assertEqual(cut_ayah_clips.timing_map(self.timing), {1: (0.5, 2.5), 2: (2.5, 5.0)})
        s, e = cut_ayah_clips.clip_window(0.01, 1.0)
        self.assertEqual(s, 0.0)
        self.assertAlmostEqual(e, 1.15)

    def test_parse_refs(self):
        self.assertEqual(cut_ayah_clips.parse_refs(['49:12', '49:10', '2:1']), {49: [12, 10], 2: [1]})
        with self.assertRaises(ValueError):
            cut_ayah_clips.parse_refs(['115:1'])

    def test_cut_offline_cli(self):
        out = self.tmp / 'out'
        with contextlib.redirect_stdout(io.StringIO()) as buf:
            cut_ayah_clips.main(['--timing-json', str(self.tfile), '--surah-mp3', str(self.src),
                                 '--out', str(out), '49:1', '49:2'])
        self.assertEqual(sorted(p.name for p in out.glob('*.mp3')), ['049001.mp3', '049002.mp3'])
        self.assertIn('ok 049001.mp3', buf.getvalue())
        res = cut_ayah_clips.cut_surah(49, [1], self.timing, self.src, out)
        name, dur, expected = res[0]
        self.assertAlmostEqual(dur, expected, delta=0.1)  # 2.0 s + 0.2 s padding

    def test_missing_timing(self):
        with self.assertRaises(ValueError):
            cut_ayah_clips.cut_surah(49, [9], self.timing, self.src, self.tmp)


if __name__ == '__main__':
    unittest.main()
