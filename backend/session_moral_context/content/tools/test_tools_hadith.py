"""Tests for hadith_common, fetch_hadith and fetch_hadeethenc.

Run from this directory:  python3 -m unittest test_tools_hadith -v   (no Django, no network)

Every fixture is synthetic: placeholder Arabic such as "نص تجريبي" shaped like the real records.
No hadith text, no real dorar page, no real HadeethEnc record appears here.
"""
import contextlib
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path

import fetch_hadeethenc as he
import fetch_hadith as fh
import hadith_common as hc

# --- synthetic fixtures -----------------------------------------------------

NARR = 'راوٍ تجريبي'


def html_block(text, grade, narrator, grader, book, number, tag=None, cats=('تصنيف تجريبي',), prefix='1 - '):
    tag_a = f'<a tag="{tag}" href="https://dorar.net/h/{tag}" class="shareLink"><i></i></a>' if tag else ''
    cat_a = ''.join(f'<a class="badge" href="/hadith-category/cat/abc{i}">{c}</a>' for i, c in enumerate(cats))
    return f'''<div class="border-bottom py-4  ">
	<article class="overflow-hidden pt-7" >
		<h5 class="h5-responsive">
		 {prefix} {text} </h5>
	</article>
	<div class="d-block mb-2">
        <strong class="px-2">
            خلاصة حكم المحدث :
            <span class="primary-text-color">{grade}</span>
        </strong>
        <br>
		<strong class="px-2">
			الراوي :
			<span class="primary-text-color">{narrator}</span>
		</strong>
		<strong class="px-2">
			| المحدث :
			<a data-toggle="modal" view-card="mhd" card-link="/hadith/mhd/256"><span class="primary-text-color">{grader}</span></a>
		</strong>
		<strong class="px-2">
			| المصدر :
			<a data-toggle="modal" view-card="book" card-link="/hadith/book-card/6216"><span class="primary-text-color">{book}</span></a>
		</strong><br/>
		<strong class="px-2">
			   الصفحة أو الرقم :
			<span class="primary-text-color">{number}</span>
		</strong>
        <br>
        <span class="px-2">التصنيف الموضوعي : {cat_a}</span>
	</div>
	{tag_a}
	<script>var x = "نص لا يجب أن يظهر";</script>
</div>
'''


SEARCH_HTML = '<html><body><div class="tab-pane">' + ''.join([
    html_block('نَصٌّ <span class="search-keys">تجريبي</span> أول &amp; <a class="hist-link" data-content="شرح">كلمة</a> ثانية',
               '[صحيح]', '[راوٍ تجريبي]', 'البخاري', 'صحيح البخاري', '4321', tag='AbCd1234'),
    html_block('نص تجريبي ثان', '[صحيح]', NARR, 'مسلم', 'صحيح مسلم', '1234', tag='ZyXw9876', prefix='2 -'),
    html_block('نص تجريبي ثالث', 'حسن', NARR, 'الألباني', 'سنن الترمذي', '55', tag='Qq11Qq11', prefix='3 -'),
    html_block('نص تجريبي مقتطع . . .', '[صحيح]', NARR, 'البخاري', 'صحيح البخاري', '4322', tag='Pa111111', prefix='4 -'),
    html_block('نص تجريبي رابع', '[صحيح]', NARR, 'البخاري', 'صحيح البخاري', '4321', tag='Dup22222', prefix='5 -'),
    html_block('نص تجريبي خامس', '[صحيح]', NARR, 'البخاري', 'صحيح البخاري', '12/ص', tag='Bad33333', prefix='6 -'),
]) + '</div></body></html>'

COPY_TEXT = '''Source URL: https://dorar.net/hadith/search?q=test
Retrieved: 2026-10-05
نَصٌّ تجريبي نصي أول
خلاصة حكم المحدث : [صحيح]
الراوي : راوٍ تجريبي
| المحدث : البخاري
| المصدر : صحيح البخاري
الصفحة أو الرقم :
4321

أحاديث مشابهة
نص تجريبي نصي ثان
<ref>الراوي: راوٍ تجريبي | المحدث: مسلم<br>المصدر: صحيح مسلم | الصفحة أو الرقم: 1234<br>خلاصة حكم المحدث: [صحيح]<br>موقع الدرر السنية</ref>
'''

API_HTML = ('<div class="hadith" style="x">1 -  نص <span class="search-keys">تجريبي</span> أول</div>'
            '<div class="hadith-info"><span class="info-subtitle">الراوي:</span> راوٍ تجريبي</span> '
            '<span class="info-subtitle">المحدث:</span> البخاري '
            '<span class="info-subtitle">المصدر:</span> صحيح البخاري '
            '<span class="info-subtitle">الصفحة أو الرقم:</span> 4321 '
            '<span class="info-subtitle">خلاصة حكم المحدث:</span> <span>[صحيح]</span></div>\n--------------\n'
            '<div class="hadith">2 - نص تجريبي ثان ... الحديث</div>'
            '<div class="hadith-info"><span class="info-subtitle">الراوي:</span> راو '
            '<span class="info-subtitle">المحدث:</span> مسلم '
            '<span class="info-subtitle">المصدر:</span> صحيح مسلم '
            '<span class="info-subtitle">الصفحة أو الرقم:</span> 99 '
            '<span class="info-subtitle">خلاصة حكم المحدث:</span> <span>[صحيح]</span></div>')


def write(path, text):
    Path(path).write_text(text, encoding='utf-8')
    return path


class TmpDirCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)


def run_main(mod, argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = mod.main(argv)
        except SystemExit as e:
            code = e.code
    return code, out.getvalue(), err.getvalue()


# --- hadith_common ----------------------------------------------------------

class CommonTests(unittest.TestCase):
    def test_strip_marks_removes_tashkeel_tatweel_punctuation_whitespace(self):
        self.assertEqual(hc.strip_marks('نَـصٌّ، تَجْرِيبِيٌّ!'), 'نصتجريبي')

    def test_matn_equal_plain_and_unequal(self):
        self.assertEqual(hc.matn_equal('نَصٌّ تجريبي.', 'نص  تجريبي')[0], True)
        self.assertEqual(hc.matn_equal('نص تجريبي', 'نص آخر'), (False, ''))
        self.assertEqual(hc.matn_equal('', 'نص'), (False, ''))

    def test_matn_equal_narrator_stripped_on_both_sides_only(self):
        a = 'عن راوي تجريبي رضي الله عنه قال: نص تجريبي واحد'
        b = 'عن آخر تجريبي رضي الله عنه، أنه قال: نص تجريبي واحد'
        self.assertEqual(hc.matn_equal(a, b), (True, 'narrator-stripped'))
        # one side has a narrator clause, the other has none: NOT equal (stripped on one side only)
        self.assertEqual(hc.matn_equal(a, 'نص تجريبي واحد'), (False, ''))
        self.assertEqual(hc.matn_equal('نص تجريبي واحد', a), (False, ''))

    def test_strip_narrator_clause_leaves_ordinary_colon_alone(self):
        self.assertEqual(hc.strip_narrator_clause('نص تجريبي: بقية النص'), ('نص تجريبي: بقية النص', False))

    def test_strip_narrator_clause_only_first_colon_within_ten_words(self):
        near = 'عن راو تجريبي رضي الله عنه قال: بقية النص'
        self.assertEqual(hc.strip_narrator_clause(near), ('بقية النص', True))
        far = 'عن ' + ' '.join(['كلمة'] * 10) + ' قال: بقية النص'      # colon after the 10th word
        self.assertEqual(hc.strip_narrator_clause(far), (far, False))

    def test_label_matches_review_ledger_key(self):
        self.assertEqual(hc.label('Sahih al-Bukhari', '4321'), 'hadith:Sahih al-Bukhari:4321')

    def test_provenance_write_and_merge(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'provenance.json'
            hc.append_provenance('hadith:Sahih Muslim:1', {'a': 1}, p)
            hc.append_provenance('hadith:Sahih Muslim:1', {'b': 2}, p)
            hc.append_provenance('hadith:Sahih Muslim:2', {'c': 3}, p)
            data = json.loads(p.read_text(encoding='utf-8'))
            self.assertEqual(data['hadith:Sahih Muslim:1'], {'a': 1, 'b': 2})
            self.assertEqual(set(data), {'hadith:Sahih Muslim:1', 'hadith:Sahih Muslim:2'})

    def test_normalize_ar_for_keyword_tests(self):
        # tashkeel, tatweel and punctuation go; alef/ya/ta-marbuta fold; word breaks stay one space
        self.assertEqual(hc.normalize_ar('الإِسْرَافُ، والتَّـبْذِيرُ.'), 'الاسراف والتبذير')
        self.assertEqual(hc.normalize_ar('رَحْمَةٌ  أُخْرَى'), 'رحمه اخري')
        self.assertEqual(hc.normalize_ar(None), '')

    def test_pure_integer(self):
        self.assertEqual(hc.pure_integer(' 4321 '), '4321')
        self.assertEqual(hc.pure_integer('٤٣٢١'), '4321')
        self.assertIsNone(hc.pure_integer('12/3'))
        self.assertIsNone(hc.pure_integer('2788 و 2789'))


# --- fetch_hadith -----------------------------------------------------------

class DorarParserTests(TmpDirCase):
    def test_label_parsing(self):
        self.assertEqual(fh.parse_label_text('| المحدث : البخاري'), ('grader', 'البخاري'))
        self.assertEqual(fh.parse_label_text('  الصفحة أو الرقم :\n 4321'), ('number', '4321'))
        self.assertEqual(fh.parse_label_text('خلاصة حكم المحدث : [صحيح]'), ('grade', '[صحيح]'))
        self.assertIsNone(fh.parse_label_text('شيء آخر : قيمة'))

    def test_clean_hadith_keeps_diacritics_and_unwraps(self):
        s = 'نَصٌّ&nbsp; <span class="search-keys">تَجْرِيبِيٌّ</span> &amp; كلمة\n  أخرى'
        self.assertEqual(fh.clean_hadith(s), 'نَصٌّ تَجْرِيبِيٌّ & كلمة أخرى')
        self.assertEqual(fh.clean_hadith('12 - نص'), 'نص')

    def test_grade_bracket_strip(self):
        self.assertEqual(fh.strip_brackets('[صحيح]'), 'صحيح')
        self.assertEqual(fh.strip_brackets(' [ صحيح ] '), 'صحيح')
        self.assertEqual(fh.strip_brackets('حسن'), 'حسن')
        # only ONE surrounding pair is stripped; nested/multiple brackets are left alone
        self.assertEqual(fh.strip_brackets('[صحيح] وقال [حسن]'), '[صحيح] وقال [حسن]')
        self.assertEqual(fh.strip_brackets('[[صحيح]]'), '[[صحيح]]')

    def test_permalink_id_host_check(self):
        self.assertEqual(fh.permalink_id('https://www.dorar.net/h/AbCd1234'), 'AbCd1234')
        self.assertEqual(fh.permalink_id('http://dorar.net/h/AbCd1234/'), 'AbCd1234')
        for bad in ('https://dorar.net/hadith/search?q=t', 'https://dorar.net.evil.example/h/AbCd1234',
                    'https://evil.example/?u=dorar.net/h/AbCd1234', 'ftp://dorar.net/h/AbCd1234', ''):
            self.assertEqual(fh.permalink_id(bad), '', bad)

    def test_substring_url_is_not_a_source_url(self):
        f = write(self.tmp / 'x.txt', 'Source URL: https://evil.example/?u=dorar.net/h/AbCd1234\n' + COPY_TEXT.split('\n', 2)[2])
        self.assertEqual(fh.parse_file(f)[1][0]['source_url'], '')
        f = write(self.tmp / 'y.txt', 'Source URL: https://dorar.net/h/AbCd1234\n' + COPY_TEXT.split('\n', 2)[2])
        self.assertEqual(fh.parse_file(f)[1][0]['source_url'], 'https://dorar.net/h/AbCd1234')

    def test_text_parser_wrapped_takhrij_and_stray_book_heading(self):
        body = '\n'.join([
            'صحيح البخاري',                                   # stray heading before the first entry
            'نص تجريبي أول',
            'خلاصة حكم المحدث : [صحيح]',
            'الراوي : راو',
            '| المحدث : البخاري',
            '| المصدر : صحيح البخاري',
            'الصفحة أو الرقم : 4321',
            'التخريج : أخرجه فلان في كتاب تجريبي',
            'تتمة سطر التخريج الملتف',                        # wrapped continuation of التخريج
            '',
            'صحيح مسلم',                                      # stray heading between entries
            'نص تجريبي ثان',
            'خلاصة حكم المحدث : [صحيح]',
            'الراوي : راو',
            '| المحدث : مسلم',
            '| المصدر : صحيح مسلم',
            'الصفحة أو الرقم : 1234',
        ])
        a, b = fh.parse_file(write(self.tmp / 't.txt', body))[1]
        self.assertEqual(a['text'], 'نص تجريبي أول')
        self.assertEqual(b['text'], 'نص تجريبي ثان')     # not "تتمة ... صحيح مسلم نص تجريبي ثان"
        self.assertEqual((a['number'], b['number']), ('4321', '1234'))

    def test_text_parser_empty_label_value_does_not_swallow_next_hadith(self):
        body = '\n'.join([
            'نص تجريبي أول', 'خلاصة حكم المحدث : [صحيح]', 'الراوي : راو', '| المحدث : البخاري',
            '| المصدر : صحيح البخاري', 'الصفحة أو الرقم :',          # value missing
            'نص تجريبي ثان يمتد على عدة كلمات تجريبية فقط',
            'خلاصة حكم المحدث : [صحيح]', 'الراوي : راو', '| المحدث : مسلم', '| المصدر : صحيح مسلم',
            'الصفحة أو الرقم : 1234'])
        a, b = fh.parse_file(write(self.tmp / 't.txt', body))[1]
        self.assertIn('number', a['reject'])                      # first entry stays incomplete
        self.assertEqual(b['text'], 'نص تجريبي ثان يمتد على عدة كلمات تجريبية فقط')
        self.assertEqual(b['number'], '1234')

    def test_text_parser_lines_between_labels_do_not_leak_into_next_text(self):
        body = '\n'.join([
            'نص تجريبي أول', 'خلاصة حكم المحدث : [صحيح]', 'سطر شارد تجريبي', 'الراوي : راو',
            '| المحدث : البخاري', '| المصدر : صحيح البخاري', 'الصفحة أو الرقم : 4321',
            'نص تجريبي ثان', 'خلاصة حكم المحدث : [صحيح]', 'الراوي : راو', '| المحدث : مسلم',
            '| المصدر : صحيح مسلم', 'الصفحة أو الرقم : 1234'])
        a, b = fh.parse_file(write(self.tmp / 't.txt', body))[1]
        self.assertEqual(b['text'], 'نص تجريبي ثان')
        self.assertEqual(a['text'], 'نص تجريبي أول')

    def test_partial_detection(self):
        for bad in ('نص . . .', 'نص ...', 'نص… ثم', 'نص ... الحديث', '. . . نص'):
            self.assertTrue(fh.is_partial(bad), bad)
        self.assertFalse(fh.is_partial('نص تجريبي كامل.'))

    def test_html_entries_ids_and_fields(self):
        f = write(self.tmp / 'search.html', SEARCH_HTML)
        meta, entries = fh.parse_file(f)
        self.assertEqual(len(entries), 6)
        e = entries[0]
        self.assertEqual(e['text'], 'نَصٌّ تجريبي أول & كلمة ثانية')   # prefix gone, search-keys unwrapped
        self.assertEqual((e['book'], e['number'], e['grade'], e['grader']), ('صحيح البخاري', '4321', 'صحيح', 'البخاري'))
        self.assertEqual(e['narrator'], 'راوٍ تجريبي')               # editorial [ ] removed
        self.assertEqual(e['tag'], 'AbCd1234')
        self.assertEqual(e['source_url'], 'https://dorar.net/h/AbCd1234')
        self.assertEqual(e['categories'], ['تصنيف تجريبي'])
        self.assertNotIn('يظهر', e['text'])                           # <script> content ignored
        self.assertEqual(entries[1]['source_url'], 'https://dorar.net/h/ZyXw9876')

    def test_single_hadith_page_uses_canonical_link_and_bare_dash_prefix(self):
        page = ('<html><head><link rel="canonical" href="https://dorar.net/h/Sing1e99"></head><body>'
                + html_block('نص تجريبي مفرد', '[صحيح]', NARR, 'مسلم', 'صحيح مسلم', '1234', tag=None, prefix='-')
                + '<a tag="/site/search">بحث</a></body></html>')
        e = fh.parse_file(write(self.tmp / 'one.html', page))[1][0]
        self.assertEqual(e['text'], 'نص تجريبي مفرد')
        self.assertEqual(e['source_url'], 'https://dorar.net/h/Sing1e99')
        self.assertEqual(e['tag'], 'Sing1e99')

    def test_book_filter_partial_rejection_and_dedupe(self):
        f = write(self.tmp / 'search.html', SEARCH_HTML)
        entries = fh.parse_file(f)[1]
        usable, rejected = fh.candidates(entries, 'bukhari')
        # kept: 4321 (first copy) and 12/ص (usable but not pickable); dup 4321 folded; partial rejected
        self.assertEqual([e['number'] or e['number_raw'] for e in usable], ['4321', '12/ص'])
        self.assertEqual(usable[0]['dups'], 1)
        self.assertEqual([r['reject'] for r in rejected], ['partial quotation (ellipsis)'])
        usable_m, _ = fh.candidates(entries, 'muslim')
        self.assertEqual([e['number'] for e in usable_m], ['1234'])
        everything, _ = fh.candidates(entries, None)
        self.assertIn('سنن الترمذي', [e['book'] for e in everything])

    def test_pick_problems(self):
        entries = fh.parse_file(write(self.tmp / 's.html', SEARCH_HTML))[1]
        usable, _ = fh.candidates(entries, None)
        by_number = {e['number_raw']: e for e in usable}
        self.assertEqual(fh.pick_problems(by_number['4321']), [])
        self.assertTrue(any('pure integer' in p for p in fh.pick_problems(by_number['12/ص'])))
        tirmidhi = by_number['55']
        probs = ' '.join(fh.pick_problems(tirmidhi))
        self.assertIn('not Sahih al-Bukhari', probs)
        self.assertIn('not exactly', probs)

    def test_wrong_grader_is_rejected_for_pick(self):
        e = dict(fh.parse_file(write(self.tmp / 's.html', SEARCH_HTML))[1][0], grader='الألباني')
        self.assertTrue(any('compiler' in p for p in fh.pick_problems(e)))

    def test_text_format_labels_split_records_and_header(self):
        f = write(self.tmp / 'copy.txt', COPY_TEXT)
        meta, entries = fh.parse_file(f)
        self.assertEqual(meta['url'], 'https://dorar.net/hadith/search?q=test')
        self.assertEqual(meta['retrieved'], '2026-10-05')
        self.assertEqual(len(entries), 2)
        a, b = entries
        self.assertEqual(a['text'], 'نَصٌّ تجريبي نصي أول')
        self.assertEqual((a['book_key'], a['number'], a['grade']), ('bukhari', '4321', 'صحيح'))   # value on next line
        self.assertEqual(b['text'], 'نص تجريبي نصي ثان')                       # noise line "أحاديث مشابهة" dropped
        self.assertEqual((b['book_key'], b['number'], b['grader']), ('muslim', '1234', 'مسلم'))
        self.assertEqual(a['source_url'], '')       # a search URL is not a permalink: left empty
        self.assertEqual(a['reject'], '')

    def test_text_with_missing_label_is_rejected(self):
        f = write(self.tmp / 'x.txt', 'نص تجريبي\nالراوي : راو\nالمحدث : البخاري\nالمصدر : صحيح البخاري\n')
        e = fh.parse_file(f)[1][0]
        self.assertIn('missing', e['reject'])
        self.assertIn('number', e['reject'])
        self.assertIn('grade', e['reject'])

    def test_api_json_and_jsonp(self):
        payload = json.dumps({'ahadith': {'result': API_HTML}}, ensure_ascii=False)
        for name, body in (('a.json', payload), ('b.js', f'jQuery123({payload});')):
            entries = fh.parse_file(write(self.tmp / name, body))[1]
            self.assertEqual(len(entries), 2, name)
            self.assertEqual(entries[0]['text'], 'نص تجريبي أول')
            self.assertEqual((entries[0]['book_key'], entries[0]['number'], entries[0]['grade']),
                             ('bukhari', '4321', 'صحيح'))
            self.assertEqual(entries[0]['source_url'], '')                    # the API has no hadith id
            self.assertEqual(entries[1]['reject'], 'partial quotation (ellipsis)')

    def test_expand_paths_glob_and_dir(self):
        write(self.tmp / 'a.html', SEARCH_HTML)
        write(self.tmp / 'b.txt', COPY_TEXT)
        self.assertEqual(len(fh.expand_paths([str(self.tmp / '*.html')])), 1)
        self.assertEqual(len(fh.expand_paths([str(self.tmp)])), 2)
        with self.assertRaises(FileNotFoundError):
            fh.expand_paths([str(self.tmp / 'nope.html')])

    def test_cli_list_and_pick_with_provenance(self):
        f = write(self.tmp / 'search.html', '<!-- Source URL: https://www.dorar.net/hadith/search?q=t -->\n'
                  '<!-- Retrieved: 2026-10-05 -->\n' + SEARCH_HTML)
        code, out, err = run_main(fh, ['--from-file', str(f), '--book', 'bukhari', '--list'])
        self.assertEqual(code, 0)
        self.assertIn('4321', out)
        self.assertIn('rejected 1', err)
        prov, dest = self.tmp / 'prov.json', self.tmp / 'item.json'
        code, out, err = run_main(fh, ['--from-file', str(f), '--book', 'bukhari', '--pick', '1', '--value', 'honesty',
                                       '--out', str(dest), '--provenance', str(prov)])
        self.assertEqual(code, 0, err)
        item = json.loads(dest.read_text(encoding='utf-8'))[0]
        self.assertEqual((item['type'], item['book'], item['number'], item['grade'], item['grader']),
                         ('hadith', 'Sahih al-Bukhari', '4321', 'صحيح', 'البخاري'))
        self.assertEqual((item['source_site'], item['source_url'], item['verification_status']),
                         ('dorar.net', 'https://dorar.net/h/AbCd1234', 'unverified'))
        self.assertEqual(item['values'], ['honesty'])
        self.assertNotIn('english_text', item)
        data = json.loads(prov.read_text(encoding='utf-8'))
        rec = data['hadith:Sahih al-Bukhari:4321']
        self.assertEqual(rec['dorar_retrieved'], '2026-10-05')
        self.assertEqual(rec['dorar_sha256'], hc.sha256_file(f))

    def test_cli_pick_refuses_unpickable_and_unknown_value(self):
        f = write(self.tmp / 'search.html', SEARCH_HTML)
        code, _, err = run_main(fh, ['--from-file', str(f), '--book', 'bukhari', '--pick', '2', '--value', 'honesty',
                                     '--no-provenance'])
        self.assertIn('pure integer', str(code))
        code, _, _ = run_main(fh, ['--from-file', str(f), '--pick', '1', '--value', 'no-such-value', '--no-provenance'])
        self.assertIn('unknown value', str(code))

    def test_live_is_off_without_flag(self):
        code, _, _ = run_main(fh, [])
        self.assertIn('--from-file', str(code))


# --- fetch_hadeethenc -------------------------------------------------------

def ar_rec(hid, text='نص تجريبي عربي', title=None, cats=('282',), attribution='رواه البخاري', grade='صحيح',
           ref='صحيح البخاري (9/ 2) (4321)', translations=('ar', 'en')):
    return {'id': str(hid), 'title': title or f'عنوان تجريبي {hid}', 'hadeeth': text, 'attribution': attribution,
            'grade': grade, 'reference': ref, 'categories': list(cats), 'translations': list(translations),
            'explanation': 'شرح تجريبي', 'hints': [], 'words_meanings': []}


def en_rec(hid, title='A synthetic honest title', text='PLACEHOLDER ENGLISH TEXT 1'):
    return {'id': str(hid), 'title': title, 'hadeeth': text, 'attribution': 'Narrated by Bukhari',
            'grade': 'Authentic', 'categories': ['282'], 'hints': [], 'translations': ['ar', 'en']}


def put(cache, hid, lang, rec, retrieved='2026-10-05T10:00:00Z'):
    p = he.one_path(cache, hid, lang)
    p.parent.mkdir(parents=True, exist_ok=True)
    body = json.dumps(rec, ensure_ascii=False).encode('utf-8')
    p.write_bytes(body)
    hc.write_json(he.meta_path(p), {'url': f'x/{hid}/{lang}', 'retrieved_at': retrieved,
                                    'sha256': hc.sha256_bytes(body), 'bytes': len(body)})
    return body


def put_list(cache, cat, ids):
    p = he.list_path(cache, cat, 1)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({'data': [{'id': str(i), 'title': 't', 'translations': []} for i in ids],
                             'meta': {'current_page': '1', 'last_page': 1, 'total_items': len(ids), 'per_page': '100'}}),
                 encoding='utf-8')


class ReferenceAndAttributionTests(unittest.TestCase):
    def test_reference_regex_pure_integer_only(self):
        refs = he.extract_refs('صحيح البخاري (9/ 2) (4321)\nصحيح مسلم (3/ 7) (1234)\nصحيح مسلم (3/ 9) (2788 و 2789)\nكتاب آخر (1/ 2) (5)')
        self.assertEqual([(r['book'], r['number']) for r in refs],
                         [('bukhari', '4321'), ('muslim', '1234'), ('muslim', None)])
        self.assertEqual(he.extract_refs('بلا أرقام'), [])
        # left boundary: an abridgement or commentary title containing the book name is not the book
        self.assertEqual(he.extract_refs('مختصر صحيح مسلم (1/ 2) (55)'), [])
        self.assertEqual(he.extract_refs('كتاب صحيح البخاري (1/ 2) (55)'), [])
        self.assertEqual([r['number'] for r in he.extract_refs('كتاب (3) ؛ صحيح مسلم (1/ 2) (55)')], ['55'])
        self.assertEqual(he.pick_book_number(refs, {'bukhari', 'muslim'}), ('bukhari', '4321'))
        self.assertEqual(he.pick_book_number(refs, {'bukhari', 'muslim'}, 'muslim'), ('muslim', '1234'))
        self.assertEqual(he.pick_book_number(refs, {'muslim'}), ('muslim', '1234'))

    def test_attribution_mapping_spelling_variants(self):
        both = ({'bukhari', 'muslim'}, False)
        for s in ('متفق عليه', 'Agreed upon', 'Narrated by Bukhari & Muslim', 'رواه البخاري ومسلم', 'Narrated by Al-Bukhāri and Muslim'):
            self.assertEqual(he.sahihayn_books(s), both, s)
        self.assertEqual(he.sahihayn_books('رواه مسلم'), ({'muslim'}, False))
        self.assertEqual(he.sahihayn_books('Narrated by Bukhari'), ({'bukhari'}, False))
        self.assertEqual(he.sahihayn_books('Narrated by Al-Bukhāri'), ({'bukhari'}, False))
        # any other collector or prose: not a pure Sahihayn attribution
        self.assertTrue(he.sahihayn_books('رواه أبو داود')[1])
        self.assertTrue(he.sahihayn_books('Narrated by Bukhari - At-Tirmidhi')[1])
        self.assertTrue(he.sahihayn_books('رواه البخاري وأحمد في المسند')[1])


class CategoriesFileTests(unittest.TestCase):
    def test_mapping_covers_every_value_and_deny_list_is_complete(self):
        cfg = he.load_config()
        self.assertEqual(set(cfg['values']), set(hc.known_values()))
        for slug, v in cfg['values'].items():
            self.assertTrue(v['categories'] or v['keyword_only_categories'], slug)
            if v['keyword_only_categories'] and not v['categories']:
                self.assertTrue(v['keywords_en'] or v.get('keywords_ar'), slug)
            self.assertTrue(all(isinstance(c, int) for c in v['categories'] + v['keyword_only_categories']), slug)
        self.assertEqual(set(cfg['deny_list']),
                         {'139', '128', '127', '124', '191', '581', '205', '607', '63', '84', '323', '83', '65', '71'})
        mapped = {str(c) for v in cfg['values'].values() for c in v['categories'] + v['keyword_only_categories']}
        self.assertFalse(mapped & set(cfg['deny_list']))

    def test_paradise_and_hell_descriptions_unblocked_but_grave_barzakh_hour_stay_blocked(self):
        deny = he.load_config()['deny_list']
        self.assertNotIn('324', deny)
        self.assertTrue({'323', '83', '63', '84', '128', '127', '139', '124', '65'} <= set(deny))

    def test_values_without_own_category_are_found_by_arabic_keyword(self):
        # justice, orphans and waste have no HadeethEnc category of their own: broad categories + Arabic keywords
        v = he.load_config()['values']
        self.assertIn(282, v['justice']['keyword_only_categories'])      # Muslim 1827 sits in 282
        self.assertTrue({'المقسطين', 'العدل', 'عدل'} <= set(v['justice']['keywords_ar']))
        self.assertIn(511, v['caring-for-orphans']['keyword_only_categories'])    # Bukhari 6005 sits in 511
        self.assertTrue({'يتيم', 'اليتيم'} <= set(v['caring-for-orphans']['keywords_ar']))
        self.assertTrue({'إسراف', 'الإسراف', 'تبذير'} <= set(v['not-wasting']['keywords_ar']))
        for slug in ('justice', 'caring-for-orphans', 'not-wasting'):
            self.assertTrue(v[slug]['keyword_only_categories'], slug)


class CandidateTests(TmpDirCase):
    def setUp(self):
        super().setUp()
        self.cache = self.tmp / 'cache'
        # 1001: good, English, number; 1002: good, no English; 1003: weak grade; 1004: other collector
        # 1005: in a deny-list category (record field); 1006: deny-list by list membership only
        # 1007: too long; 1008: right category but no keyword; 1009: agreed, number only for Muslim
        recs = {
            1001: (ar_rec(1001), en_rec(1001)),
            1002: (ar_rec(1002, title='عنوان عن الصدق', ref='صحيح مسلم (1/ 2) (777)', attribution='رواه مسلم'), None),
            1003: (ar_rec(1003, grade='ضعيف'), en_rec(1003)),
            1004: (ar_rec(1004, attribution='رواه أبو داود'), en_rec(1004)),
            1005: (ar_rec(1005, cats=('282', '139')), en_rec(1005)),
            1006: (ar_rec(1006), en_rec(1006)),
            1007: (ar_rec(1007, text=' '.join(['كلمة'] * 81)), en_rec(1007)),
            1008: (ar_rec(1008), en_rec(1008, title='Something unrelated')),
            1009: (ar_rec(1009, attribution='متفق عليه', ref='صحيح مسلم (1/ 2) (888)'), en_rec(1009, title='honest again')),
        }
        for hid, (a, e) in recs.items():
            put(self.cache, hid, 'ar', a)
            if e:
                put(self.cache, hid, 'en', e)
        put_list(self.cache, 282, [1001, 1002, 1003, 1004, 1005, 1006, 1007, 1008, 1009])
        put_list(self.cache, 139, [1006])
        cats = [{'id': 282, 'title': 'Praiseworthy Morals', 'hadeeths_count': 9, 'parent_id': 266},
                {'id': 266, 'title': 'Ethics', 'hadeeths_count': 9, 'parent_id': None},
                {'id': 139, 'title': 'Jihad', 'hadeeths_count': 1, 'parent_id': 138}]
        for lang in ('ar', 'en'):
            he.cats_path(self.cache, lang).parent.mkdir(parents=True, exist_ok=True)
            he.cats_path(self.cache, lang).write_text(json.dumps(cats), encoding='utf-8')
        self.cfg = he.load_config()
        self.corpus = he.Corpus(self.cache)

    def test_gates_and_ranking(self):
        cands, rejects = he.list_candidates(self.corpus, self.cfg, 'honesty')
        ids = [c['id'] for c in cands]
        self.assertEqual(sorted(ids), ['1001', '1002', '1009'])
        # relevance first: 1002 matches by Arabic keyword (no English needed), 1001 and 1009 by English keyword
        self.assertEqual(ids, ['1002', '1001', '1009'])
        self.assertIn('grade is not exactly صحيح', rejects)
        self.assertIn('attribution is not Bukhari/Muslim/agreed', rejects)
        self.assertEqual(sum(v for k, v in rejects.items() if k.startswith('deny-list')), 2)
        self.assertIn('longer than 80 words', rejects)
        self.assertEqual(rejects['category matches but no keyword'], 1)

    def test_deny_list_by_record_field_by_list_membership_and_ancestor(self):
        self.assertIn('deny-list', he.evaluate(self.corpus, '1005', self.cfg)[1])
        self.assertIn('deny-list', he.evaluate(self.corpus, '1006', self.cfg)[1])
        put(self.cache, 1010, 'ar', ar_rec(1010, cats=('139',)))
        # a sub-category of a denied category is denied through the cached tree
        cats = json.loads(he.cats_path(self.cache, 'en').read_text(encoding='utf-8'))
        cats.append({'id': 900, 'title': 'sub', 'hadeeths_count': 1, 'parent_id': 139})
        he.cats_path(self.cache, 'en').write_text(json.dumps(cats), encoding='utf-8')
        put(self.cache, 1011, 'ar', ar_rec(1011, cats=('900',)))
        corpus = he.Corpus(self.cache)
        self.assertIn('deny-list', he.evaluate(corpus, '1011', self.cfg)[1])
        self.assertEqual(he.evaluate(corpus, '1001', self.cfg)[1], '')

    def test_flags_and_limit_and_table(self):
        cands, _ = he.list_candidates(self.corpus, self.cfg, 'honesty', require_en=True)
        self.assertEqual(sorted(c['id'] for c in cands), ['1001', '1009'])
        cands, _ = he.list_candidates(self.corpus, self.cfg, 'honesty', require_number=True)
        self.assertEqual(sorted(c['id'] for c in cands), ['1001', '1002', '1009'])
        code, out, err = run_main(he, ['candidates', '--value', 'honesty', '--cache', str(self.cache), '--limit', '2'])
        self.assertEqual(code, 0)
        lines = out.strip().splitlines()
        self.assertEqual(len(lines), 3)                       # header + 2 rows
        self.assertIn('Sahih Muslim', lines[1])
        self.assertIn('777', lines[1])
        self.assertIn('ar_keyword', lines[1])
        self.assertIn('rejected by gate', err)

    def test_all_values_counts_and_candidates_json(self):
        code, out, err = run_main(he, ['candidates', '--value', 'all', '--cache', str(self.cache)])
        self.assertEqual(code, 0, err)
        lines = {ln.split()[0]: ln.split() for ln in out.strip().splitlines()[1:]}
        self.assertEqual(lines['honesty'][1:4], ['3', '3', '0'])            # cand, numbered, needs_number
        self.assertEqual(lines['justice'], ['justice', '0', '0', '0', '<2'])
        self.assertEqual(len(lines), len(self.cfg['values']))
        rows = json.loads((self.cache / 'candidates.json').read_text(encoding='utf-8'))
        honesty = [r for r in rows if r['value'] == 'honesty']
        self.assertEqual([r['hadeethenc_id'] for r in honesty], ['1002', '1001', '1009'])     # rank order
        self.assertEqual(set(honesty[0]), {'value', 'hadeethenc_id', 'book', 'number', 'needs_number', 'grade',
                                           'attribution', 'words', 'first_8_words_ar', 'hadeethenc_url'})
        by_id = {r['hadeethenc_id']: r for r in honesty}
        self.assertEqual((by_id['1001']['book'], by_id['1001']['number'], by_id['1001']['needs_number']),
                         ('Sahih al-Bukhari', '4321', False))
        self.assertEqual((by_id['1001']['grade'], by_id['1001']['attribution'], by_id['1001']['words']),
                         ('صحيح', 'رواه البخاري', 3))
        self.assertTrue(by_id['1001']['hadeethenc_url'].endswith('/en/browse/hadith/1001'))
        self.assertTrue(by_id['1002']['hadeethenc_url'].endswith('/ar/browse/hadith/1002'))   # no English cached
        self.assertTrue(all(len(r['first_8_words_ar'].split()) <= 8 for r in rows))
        # --limit does not shorten `all`; --json-file redirects it
        dest = self.tmp / 'c.json'
        run_main(he, ['candidates', '--value', 'all', '--limit', '1', '--cache', str(self.cache), '--json-file', str(dest)])
        self.assertEqual(json.loads(dest.read_text(encoding='utf-8')), rows)
        # single value + --json-file writes the shown rows
        one = self.tmp / 'one.json'
        run_main(he, ['candidates', '--value', 'honesty', '--limit', '2', '--cache', str(self.cache), '--json-file', str(one)])
        self.assertEqual([r['hadeethenc_id'] for r in json.loads(one.read_text(encoding='utf-8'))], ['1002', '1001'])

    def test_candidate_without_cache_fails_clearly(self):
        code, _, _ = run_main(he, ['candidates', '--value', 'honesty', '--cache', str(self.tmp / 'empty')])
        self.assertIn('run `pull` first', str(code))

    def test_draft_without_dorar_file(self):
        prov, dest = self.tmp / 'prov.json', self.tmp / 'draft.json'
        code, _, err = run_main(he, ['draft', '--id', '1001', '--value', 'honesty', '--cache', str(self.cache),
                                     '--out', str(dest), '--provenance', str(prov)])
        self.assertEqual(code, 0, err)
        item = json.loads(dest.read_text(encoding='utf-8'))[0]
        self.assertEqual(item['arabic_text'], '')
        # the matn check cannot run without the dorar page: no English, no translation fields
        for k in ('english_text', 'translation_name', 'translation_source_url'):
            self.assertNotIn(k, item)
        # only the dorar page proves grade, grader and source_url
        self.assertEqual((item['book'], item['number'], item['grade'], item['grader'], item['source_url'],
                          item['source_site'], item['verification_status']),
                         ('Sahih al-Bukhari', '4321', '', '', '', 'dorar.net', 'unverified'))
        rec = json.loads(prov.read_text(encoding='utf-8'))['hadith:Sahih al-Bukhari:4321']
        self.assertEqual(rec['hadeethenc_id'], '1001')
        self.assertFalse(rec['english_included'])
        self.assertEqual(rec['sha256_en'], hc.sha256_file(he.one_path(self.cache, '1001', 'en')))
        self.assertEqual(rec['retrieved_at_ar'], '2026-10-05T10:00:00Z')
        self.assertIn('EMPTY', err)

    def test_draft_refuses_denied_weak_and_tampered(self):
        for hid, word in (('1005', 'deny-list'), ('1003', 'grade'), ('1004', 'attribution')):
            code, _, _ = run_main(he, ['draft', '--id', hid, '--value', 'honesty', '--cache', str(self.cache),
                                       '--no-provenance'])
            self.assertIn(word, str(code), hid)
        he.one_path(self.cache, '1001', 'ar').write_text('{"tampered": true}', encoding='utf-8')
        code, _, _ = run_main(he, ['draft', '--id', '1001', '--value', 'honesty', '--cache', str(self.cache),
                                   '--no-provenance'])
        self.assertIn('sha256', str(code))

    def test_draft_agreed_hadith_needs_or_takes_book(self):
        dest = self.tmp / 'd.json'
        code, _, err = run_main(he, ['draft', '--id', '1009', '--value', 'honesty', '--cache', str(self.cache),
                                     '--out', str(dest), '--no-provenance'])
        item = json.loads(dest.read_text(encoding='utf-8'))[0]
        self.assertEqual((item['book'], item['number'], item['grader']), ('Sahih Muslim', '888', ''))
        code, _, err = run_main(he, ['draft', '--id', '1009', '--value', 'honesty', '--cache', str(self.cache),
                                     '--book', 'bukhari', '--out', str(dest), '--no-provenance'])
        item = json.loads(dest.read_text(encoding='utf-8'))[0]
        self.assertEqual((item['book'], item['number']), ('Sahih al-Bukhari', ''))
        self.assertIn('number is empty', err)

    def _dorar_file(self, text):
        return write(self.tmp / 'dorar.txt',
                     'Source URL: https://dorar.net/h/AbCd1234\nRetrieved: 2026-10-05\n'
                     f'{text}\nخلاصة حكم المحدث : [صحيح]\nالراوي : {NARR}\n| المحدث : البخاري\n'
                     '| المصدر : صحيح البخاري\nالصفحة أو الرقم : 4321\n')

    def test_draft_with_dorar_file_matn_equal_keeps_english(self):
        # HadeethEnc ar matn "نص تجريبي عربي"; dorar copy differs only by tashkeel and punctuation
        f = self._dorar_file('نَصٌّ تجريبي عربي.')
        prov, dest = self.tmp / 'prov.json', self.tmp / 'draft.json'
        code, _, err = run_main(he, ['draft', '--id', '1001', '--value', 'honesty', '--cache', str(self.cache),
                                     '--dorar-file', str(f), '--out', str(dest), '--provenance', str(prov)])
        self.assertEqual(code, 0, err)
        item = json.loads(dest.read_text(encoding='utf-8'))[0]
        self.assertEqual(item['arabic_text'], 'نَصٌّ تجريبي عربي.')       # from dorar, not HadeethEnc
        self.assertEqual(item['english_text'], 'PLACEHOLDER ENGLISH TEXT 1')
        self.assertEqual(item['source_url'], 'https://dorar.net/h/AbCd1234')
        self.assertEqual((item['narrator'], item['grade'], item['grader']), (NARR, 'صحيح', 'البخاري'))
        self.assertEqual(item['verification_status'], 'unverified')
        rec = json.loads(prov.read_text(encoding='utf-8'))['hadith:Sahih al-Bukhari:4321']
        self.assertTrue(rec['english_included'])
        self.assertEqual(rec['dorar_sha256'], hc.sha256_file(f))
        self.assertIn('matn check passed', err)

    def test_draft_with_dorar_file_mismatch_drops_english(self):
        f = self._dorar_file('نص مختلف تماما')
        dest = self.tmp / 'draft.json'
        code, _, err = run_main(he, ['draft', '--id', '1001', '--value', 'honesty', '--cache', str(self.cache),
                                     '--dorar-file', str(f), '--out', str(dest), '--no-provenance'])
        self.assertEqual(code, 0, err)
        item = json.loads(dest.read_text(encoding='utf-8'))[0]
        self.assertEqual(item['arabic_text'], 'نص مختلف تماما')
        for k in ('english_text', 'translation_name', 'translation_source_url'):
            self.assertNotIn(k, item)
        self.assertIn('english_text DROPPED', err)

    def test_draft_with_dorar_file_narrator_clause_both_sides(self):
        put(self.cache, 1020, 'ar', ar_rec(1020, text='عن راو تجريبي رضي الله عنه قال: نص تجريبي واحد'))
        put(self.cache, 1020, 'en', en_rec(1020))
        f = self._dorar_file('عن آخر رضي الله عنه أنه قال: نص تجريبي واحد')
        dest = self.tmp / 'draft.json'
        code, _, err = run_main(he, ['draft', '--id', '1020', '--value', 'honesty', '--cache', str(self.cache),
                                     '--dorar-file', str(f), '--out', str(dest), '--no-provenance'])
        self.assertEqual(code, 0, err)
        self.assertIn('english_text', json.loads(dest.read_text(encoding='utf-8'))[0])
        self.assertIn('narrator-stripped', err)


class Rules2Tests(TmpDirCase):
    """Relevance ranking, Arabic keywords without English, 80-word default, needs_number.
    Synthetic config and records only (keywords such as رحمة are search terms, not hadith text)."""

    CFG = {'deny_list': {'9': 'denied'}, 'category_titles': {},
           'values': {'v': {'categories': [1], 'keyword_only_categories': [2],
                            'keywords_en': ['merc'], 'keywords_ar': ['رحمة', 'إسراف']}}}

    def corpus(self, recs):
        cache = self.tmp / 'cache'
        for hid, (a, e) in recs.items():
            put(cache, hid, 'ar', a)
            if e:
                put(cache, hid, 'en', e)
        return he.Corpus(cache)

    def ids(self, recs, **kw):
        cands, rejects = he.list_candidates(self.corpus(recs), self.CFG, 'v', **kw)
        return [c['id'] for c in cands], cands, rejects

    def test_rank_category_then_arabic_keyword_then_english_keyword(self):
        recs = {
            3001: (ar_rec(3001, cats=('1',)), None),                                    # category, no English
            3002: (ar_rec(3002, cats=('2',), title='عنوان عن الرَّحْمَةِ'), None),          # Arabic keyword, no English
            3003: (ar_rec(3003, cats=('2',)), en_rec(3003, title='A merciful title')),  # English keyword only
            3004: (ar_rec(3004, cats=('2',)), en_rec(3004)),                            # right category, no keyword
            3005: (ar_rec(3005, cats=('2',), title='عنوان عن رحمة'), en_rec(3005, title='Mercy')),   # both languages
        }
        ids, cands, rejects = self.ids(recs)
        # relevance beats "has English": 3002 (no English) is still above 3003 (English)
        self.assertEqual(ids, ['3001', '3005', '3002', '3003'])
        self.assertEqual([c['match'] for c in cands], ['category', 'ar_keyword', 'ar_keyword', 'en_keyword'])
        self.assertEqual(rejects, {'category matches but no keyword': 1})

    def test_arabic_keyword_is_normalised_and_keeps_word_breaks(self):
        recs = {
            3101: (ar_rec(3101, cats=('2',), text='نص عن الاِسْرَافِ تجريبي'), None),       # hamza and tashkeel differ
            3102: (ar_rec(3102, cats=('2',), text='نص عن الرحمه تجريبي'), None),           # ta marbuta vs ha
            3103: (ar_rec(3103, cats=('2',), text='نص عن الإس راف تجريبي'), None),         # keyword split by a space: no
        }
        self.assertEqual(self.ids(recs)[0], ['3101', '3102'])
        # a keyword must not be assembled from the ends of two words
        put(self.tmp / 'cache', 3104, 'ar', ar_rec(3104, text='تقل قلت'))
        corpus = he.Corpus(self.tmp / 'cache')
        self.assertEqual(he.keyword_hits(corpus, '3104', [], ['قلق']), (set(), set()))
        self.assertEqual(he.keyword_hits(corpus, '3104', [], ['قلت']), (set(), {'قلت'}))

    def test_english_keywords_match_word_starts_only(self):
        put(self.tmp / 'cache', 3201, 'ar', ar_rec(3201))
        put(self.tmp / 'cache', 3201, 'en', en_rec(3201, title='None of you believes, surely', text='x'))
        corpus = he.Corpus(self.tmp / 'cache')
        self.assertEqual(he.keyword_hits(corpus, '3201', ['lie', 'rely', 'sure'], []), ({'sure'}, set()))
        put(self.tmp / 'cache', 3201, 'en', en_rec(3201, title='Whoever Lies', text='x'))
        self.assertEqual(he.keyword_hits(he.Corpus(self.tmp / 'cache'), '3201', ['lie'], []), ({'lie'}, set()))

    def test_arabic_keywords_fall_back_to_values_json(self):
        cfg = {'values': {'honesty': {'keywords_ar': ['خاص']}, 'justice': {}}}
        self.assertEqual(he.value_keywords_ar('honesty', cfg), ['خاص'])
        self.assertIn('الصدق', he.value_keywords_ar('honesty'))               # no config: values.json
        self.assertIn('صدق', he.value_keywords_ar('honesty', {'values': {'honesty': {}}}))
        self.assertEqual(he.value_keywords_ar('no-such-value'), [])

    def test_default_max_words_is_80(self):
        self.assertEqual(he.DEFAULT_MAX_WORDS, 80)
        recs = {n: (ar_rec(n, cats=('1',), text=' '.join(['كلمة'] * n)), None) for n in (62, 80, 81)}
        recs = {4000 + n: v for n, v in recs.items()}
        ids, _, rejects = self.ids(recs)
        self.assertEqual(sorted(ids), ['4062', '4080'])
        self.assertEqual(rejects, {'longer than 80 words': 1})
        self.assertEqual(self.ids(recs, max_words=60)[0], [])                  # --max-words still works
        self.assertEqual(sorted(self.ids(recs, max_words=81)[0]), ['4062', '4080', '4081'])
        self.assertEqual(he.build_parser().parse_args(['candidates', '--value', 'x']).max_words, 80)

    def test_reference_without_book_number_is_kept_and_flagged(self):
        recs = {
            4101: (ar_rec(4101, cats=('1',), ref='صحيح البخاري، دار طوق النجاة، 1422هـ.'), None),
            4102: (ar_rec(4102, cats=('1',), attribution='متفق عليه', ref='صحيح البخاري، دار طوق النجاة.'), None),
            4103: (ar_rec(4103, cats=('1',), attribution='رواه مسلم', ref='صحيح مسلم (3/ 9) (2788 و 2789)'), None),
            4104: (ar_rec(4104, cats=('1',)), None),
            4105: (ar_rec(4105, cats=('1',), attribution='متفق عليه', ref='صحيح مسلم (1/ 2) (888)'), None),
        }
        ids, cands, _ = self.ids(recs)
        by = {c['id']: c for c in cands}
        self.assertEqual(sorted(ids), ['4101', '4102', '4103', '4104', '4105'])        # none dropped
        self.assertEqual([(by[i]['book'], by[i]['number'], by[i]['needs_number']) for i in
                          ('4101', '4102', '4103', '4104', '4105')],
                         [('bukhari', None, True), (None, None, True), ('muslim', None, True),
                          ('bukhari', '4321', False), ('muslim', '888', False)])
        self.assertEqual(ids[:2], ['4104', '4105'])                                    # numbered rank first
        self.assertEqual(sorted(self.ids(recs, require_number=True)[0]), ['4104', '4105'])   # --require-number still filters

    def test_candidates_json_row_for_an_unnumbered_agreed_hadith(self):
        text = 'عن راو تجريبي رضي الله عنه قال: قال النبي: «' + ' '.join(f'ك{i}' for i in range(1, 30)) + '»'
        corpus = self.corpus({4201: (ar_rec(4201, cats=('1',), attribution='متفق عليه', ref='لا رقم', text=text), None)})
        c, _ = he.evaluate(corpus, '4201', self.CFG, 'v')
        row = he.json_row(corpus, 'v', c)
        self.assertEqual((row['book'], row['number'], row['needs_number']), (None, None, True))
        self.assertEqual(row['first_8_words_ar'], 'ك1 ك2 ك3 ك4 ك5 ك6 ك7 ك8')          # the saying, not the narrator
        self.assertEqual(row['attribution'], 'متفق عليه')

    def test_first_words_of_the_saying(self):
        self.assertEqual(he.first_words('عن أبي رضي الله عنه قال: قال النبي: «واحد اثنان ثلاثة» وبعد', 2), 'واحد اثنان')
        self.assertEqual(he.first_words('عن أبي رضي الله عنه قال: واحد اثنان ثلاثة', 2), 'واحد اثنان')   # narrator clause
        self.assertEqual(he.first_words('واحد اثنان ثلاثة', 2), 'واحد اثنان')
        self.assertEqual(he.first_words('', 8), '')

    def test_real_mapping_finds_orphans_justice_waste_without_english(self):
        cfg = he.load_config()
        recs = {
            5001: (ar_rec(5001, cats=('511',), title='عنوان عن اليتيم'), None),
            5002: (ar_rec(5002, cats=('282',), text='نص تجريبي عن المقسطين'), None),
            5003: (ar_rec(5003, cats=('290',), title='عنوان عن الإسراف'), None),
            5004: (ar_rec(5004, cats=('290',), title='عنوان بلا كلمة مفتاحية'), None),
        }
        corpus = self.corpus(recs)
        for slug, hid in (('caring-for-orphans', '5001'), ('justice', '5002'), ('not-wasting', '5003')):
            cands, _ = he.list_candidates(corpus, cfg, slug)
            self.assertEqual([(c['id'], c['match']) for c in cands], [(hid, 'ar_keyword')], slug)
        self.assertEqual(he.list_candidates(corpus, cfg, 'caring-for-orphans')[0][0]['category'], '511')


class Seq(list):
    """A route that answers with successive responses."""


class FetcherAndPullTests(TmpDirCase):
    class Fake(he.Fetcher):
        def __init__(self, routes, **kw):
            super().__init__(gap=0, sleep=self.record, **kw)
            self.routes, self.sleeps, self.calls = routes, [], []

        def record(self, s):
            self.sleeps.append(s)

        def _request(self, url):
            self.calls.append(url)
            r = self.routes[url]
            r = r.pop(0) if isinstance(r, Seq) else r
            if isinstance(r, tuple):
                return r
            return 200, {}, json.dumps(r, ensure_ascii=False).encode('utf-8')

    def test_backs_off_on_429_then_succeeds(self):
        f = self.Fake({'u': Seq([(429, {'Retry-After': '3'}, b''), (429, {}, b''), (200, {}, b'{"ok": 1}')])})
        self.assertEqual(json.loads(f.get('u')), {'ok': 1})
        self.assertIn(3.0, f.sleeps)
        self.assertIn(4.0, f.sleeps)          # exponential fallback 2 * 2**1

    def test_403_stops_immediately(self):
        f = self.Fake({'u': (403, {}, b'')})
        with self.assertRaises(he.Blocked):
            f.get('u')
        self.assertEqual(len(f.calls), 1)

    def test_404_raises_not_found(self):
        with self.assertRaises(he.NotFound):
            self.Fake({'u': (404, {}, b'')}).get('u')

    def test_gives_up_after_max_retries(self):
        f = self.Fake({'u': (429, {}, b'')}, max_retries=2)
        with self.assertRaises(RuntimeError):
            f.get('u')
        self.assertEqual(len(f.calls), 2)

    def routes(self):
        B = he.BASE
        cfg_cats = [{'id': 282, 'title': 'x', 'hadeeths_count': 3, 'parent_id': None}]
        r = {f'{B}/categories/list/?language={l}': cfg_cats for l in ('ar', 'en')}
        r[f'{B}/hadeeths/list/?language=ar&category_id=282&page=1&per_page=100'] = {
            'data': [{'id': '1'}, {'id': '2'}, {'id': '3'}], 'meta': {'last_page': 2}}
        r[f'{B}/hadeeths/list/?language=ar&category_id=282&page=2&per_page=100'] = {'data': [{'id': '4'}], 'meta': {'last_page': 2}}
        r[f'{B}/hadeeths/list/?language=ar&category_id=139&page=1&per_page=100'] = {'data': [{'id': '3'}], 'meta': {'last_page': 1}}
        r[f'{B}/hadeeths/one/?language=ar&id=1'] = ar_rec(1)
        r[f'{B}/hadeeths/one/?language=en&id=1'] = en_rec(1)
        r[f'{B}/hadeeths/one/?language=ar&id=2'] = ar_rec(2, grade='ضعيف')
        r[f'{B}/hadeeths/one/?language=ar&id=4'] = ar_rec(4, translations=('ar',))
        return r

    def test_pull_with_fake_network_prefilter_deny_and_cache(self):
        cfg = {'deny_list': {'139': 'Jihad'},
               'values': {'honesty': {'categories': [], 'keyword_only_categories': [282], 'keywords_en': ['honest']}}}
        cache = self.tmp / 'c'
        f = self.Fake(self.routes())
        out = io.StringIO()
        he.pull(cache, cfg, ['honesty'], f, out=out)
        self.assertTrue(he.one_path(cache, '1', 'ar').exists())
        self.assertTrue(he.one_path(cache, '1', 'en').exists())
        self.assertTrue(he.one_path(cache, '2', 'ar').exists())
        self.assertFalse(he.one_path(cache, '2', 'en').exists())      # weak grade: English not fetched
        self.assertFalse(he.one_path(cache, '3', 'ar').exists())      # listed under the deny-list: never fetched
        self.assertTrue(he.one_path(cache, '4', 'ar').exists())
        self.assertFalse(he.one_path(cache, '4', 'en').exists())      # no English translation advertised
        meta = json.loads(he.meta_path(he.one_path(cache, '1', 'en')).read_text(encoding='utf-8'))
        self.assertEqual(meta['sha256'], hc.sha256_file(he.one_path(cache, '1', 'en')))
        self.assertTrue(meta['retrieved_at'].endswith('Z'))
        self.assertTrue(meta['url'].endswith('language=en&id=1'))
        n = len(f.calls)
        he.pull(cache, cfg, ['honesty'], f, out=io.StringIO())        # second run: everything from the cache
        self.assertEqual(len(f.calls), n)
        corpus = he.Corpus(cache)
        self.assertEqual(corpus.members['282'], {'1', '2', '3', '4'})
        self.assertTrue(corpus.raw_ok('1', 'en'))


if __name__ == '__main__':
    unittest.main()
