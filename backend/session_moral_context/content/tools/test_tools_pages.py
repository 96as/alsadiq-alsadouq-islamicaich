"""Tests for draft_from_page.py and extract_faq.py (plain unittest, offline).

Run:  cd backend/session_moral_context/content/tools && python3 -m unittest test_tools_pages -v

Every page and PDF here is synthetic: placeholder Arabic ("نص تجريبي") laid out like the
real dorar / Al-Jamhara pages and the Bayyinat PDF. No scripture or source text appears.
The PDF tests need PyMuPDF (pip install pymupdf) and a system font with Arabic letters;
they are skipped otherwise.
"""
import contextlib
import io
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import draft_from_page as dfp  # noqa: E402
import extract_faq as faq  # noqa: E402
import save_page  # noqa: E402

try:
    import pymupdf
except ImportError:  # pragma: no cover
    pymupdf = None

FONT = next((p for p in ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                         '/usr/share/fonts/dejavu/DejaVuSans.ttf',
                         '/Library/Fonts/Arial Unicode.ttf') if Path(p).exists()), None)
# a second font file for the verse-font test (the synthetic "verse" line is drawn in it)
BOLD_FONT = FONT.replace('Sans.ttf', 'Sans-Bold.ttf') if FONT else None
if BOLD_FONT == FONT or not (BOLD_FONT and Path(BOLD_FONT).exists()):
    BOLD_FONT = None

MENU = """  *   *   *     * قائمة تجريبية
    * رابط تجريبي أول
    * رابط تجريبي ثان
[Button: اختر نوع البحث]

[Input: البحث ..]
##### منهج العمل في الموسوعات

موسوعة تجريبية

منهج العمل في الموسوعة

راجع الموسوعة

الشيخ تجريبي
"""
FOOTER = """
السابق

التالي

[Input] [Input] [Input] [Input] [Input]

حفظ

[Button: غلق]
##### انشر المادة
##### روابط هامة

  * رابط ذيل تجريبي

##### تابعنا

#### لجنة الإشراف العلمي

  * الشيخ تجريبي

[Input: كلمة المرور]

تسجيل الدخول
"""


def header(url, retrieved='2026-10-05'):
    return f'Source URL: {url}\nRetrieved: {retrieved}\n\niframe†www.example.test\n\n'


def tafsir_page():
    return (header('https://dorar.net/tafseer/2/3') + MENU +
            """# موسوعة التفسير

روابط مهمة

المراجع المعتمدة منهج العمل في الموسوعة

[Button: بدون تشكيل]

[Input: بحث في الموسوعة ..]

طريقة البحث

[Select]

نــطاق البحــث:

[Input] الجميع

بحث في [Select]

بحث

##### عنوان تجريبي

###### غريب الكلمات

* * *
نص تجريبي أول [1] يُنظر: ((مصدر تجريبي)) (1/2). .
نص تجريبي ثان
##### المعنى الإجمالي
نص تجريبي ثالث
نص عن عذاب القبر تجريبي
""" + FOOTER)


def aqeeda_page():
    return (header('https://dorar.net/aqeeda/8') + MENU +
            """# الموسوعة العقدية

روابط مهمة

[Button: بدون تشكيل]

بحث
# فرع تجريبي

محتويات الصفحة

انظر أيضا

الرابط المختصر
نص عقدي تجريبي أول
نص عقدي تجريبي ثان
### انظر أيضا:

  * فرع آخر

[Button: عرض الهوامش]

* * *
""" + FOOTER)


def history_page():
    return (header('https://dorar.net/history/event/1') + MENU +
            """# الموسوعة التاريخية

عن الموسوعة

المراجع المعتمدة اعتماد منهجية الموسوعة

[Button: بدون تشكيل]

[Input: بحث في التاريخية ..]

تنويه نص تنويه تجريبي

[Input: العام]

ميلادي [Input] هجري

بحث فى :

[Input] عنوان الحدث

طريقة البحث : [Select]

تصنيف رئيس : [Select]

ترتيب الأحداث :

[Input] الأقدم

بحث
#####

Image: filter تصفح الكل

تصفح الكل عصر تجريبي أول عصر تجريبي ثان

* * *

حدث تجريبي .

العام الهجري : 1 العام الميلادي : 2
###### تفاصيل الحدث:
نص تاريخي تجريبي أول
نص تاريخي تجريبي ثان
[Input] [Input] [Input] [Input] [Input]

حفظ
""" + FOOTER)


def term_page(with_english=True):
    t = ('معنى : Placeholder Term - مصطلح تجريبي - الجمهرة\n\n'
         '  * قائمة الموقع\n  * لغات\n[Button: بحث]\nImage: logo\n\n'
         'تعريف مصطلح تجريبي يشرح المعنى بكلمات تجريبية فقط\n\n')
    if with_english:
        t += 'A placeholder definition that explains the term in plain words\n\n'
    t += 'جميع الحقوق محفوظة تجريبي\n  * رابط ذيل\n'
    return header('https://islamic-content.com/dictionary/word/1018/en') + 'x\n' + t


FIQH_FORM = """# الموسوعة الفقهية

[Button: بدون تشكيل]

بحث
# مبحث تجريبي

محتويات الصفحة

انظر أيضا

الرابط المختصر
مسألة تجريبية أولى
قول تجريبي أول
قول تجريبي ثان
### انظر أيضا:
"""


def write(tmp, name, text):
    p = Path(tmp) / name
    p.write_text(text, encoding='utf-8')
    return str(p)


def run(fn, *argv):
    """Run a CLI main with argv; return (stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        fn(list(argv))
    return out.getvalue(), err.getvalue()


class SavePage(unittest.TestCase):
    BODY = 'غريب الكلمات:\nحَوْلَيْنِ: مثنَّى'

    def result_file(self, body, sha=None):
        sha = sha or save_page.hashlib.sha256(body.encode()).hexdigest()
        obj = {'u': 'https://dorar.net/tafseer/2/40', 'x': sha, 'b': body, 'pad': 'x' * 10}
        wrapped = [{'type': 'text', 'text': '[navigate] ok'},
                   {'type': 'text', 'text': '[javascript_tool:javascript_exec] '
                    + json.dumps(obj, ensure_ascii=False, indent=2) + '\n\n(captured at origin https://dorar.net)'}]
        f = Path(tempfile.mkdtemp()) / 'r.txt'
        f.write_text(json.dumps(wrapped, ensure_ascii=False), encoding='utf-8')
        return f

    def test_saves_verified_page_with_header(self):
        out = Path(tempfile.mkdtemp()) / 'p.md'
        save_page.save(self.result_file(self.BODY), out)
        text = out.read_text(encoding='utf-8')
        self.assertTrue(text.startswith('Source URL: https://dorar.net/tafseer/2/40\nRetrieved: '))
        self.assertTrue(text.endswith(self.BODY + '\n'))

    def test_refuses_hash_mismatch(self):
        out = Path(tempfile.mkdtemp()) / 'p.md'
        with self.assertRaises(SystemExit):
            save_page.save(self.result_file(self.BODY, sha='0' * 64), out)
        self.assertFalse(out.exists())


class TermFooter(unittest.TestCase):
    def test_footer_only_at_line_start(self):
        self.assertTrue(dfp.TERM_FOOTER.search('جميع الحقوق محفوظة'))
        self.assertTrue(dfp.TERM_FOOTER.search('© 2026'))
        self.assertFalse(dfp.TERM_FOOTER.search('القيام بأداء الحقوق'))   # a definition line (word 363)


class PageHeaderAndKind(unittest.TestCase):
    def test_header_parsed_from_first_lines(self):
        with tempfile.TemporaryDirectory() as d:
            page = dfp.load_page(write(d, 'a.md', tafsir_page()))
        self.assertEqual(page.url, 'https://dorar.net/tafseer/2/3')
        self.assertEqual(page.retrieved, '2026-10-05')

    def test_html_comment_header_and_headings(self):
        html = ('<!-- Source URL: https://dorar.net/aqeeda/9 -->\n<!-- Retrieved: 2026-10-06 -->\n'
                '<html><body><script>var a=1;</script><h1>الموسوعة العقدية</h1>'
                '<h1>عنوان تجريبي</h1><p>نص تجريبي</p><p>سطر آخر</p></body></html>')
        with tempfile.TemporaryDirectory() as d:
            page = dfp.load_page(write(d, 'a.html', html))
            kind, _, _, body = dfp.clean_page(page)
        self.assertEqual((page.url, page.retrieved), ('https://dorar.net/aqeeda/9', '2026-10-06'))
        self.assertEqual([l.text for l in body], ['عنوان تجريبي', 'نص تجريبي', 'سطر آخر'])

    def test_missing_header_fails(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(SystemExit):
                dfp.load_page(write(d, 'a.md', 'نص تجريبي\n'))

    def test_kind_detection(self):
        cases = {
            'https://dorar.net/tafseer/4/18': ('tafsir', {'surah': '4', 'n': '18'}),
            'https://dorar.net/tafseer/1': ('tafsir', {'surah': '1'}),
            'https://dorar.net/aqeeda/8': ('aqidah', {'id': '8'}),
            'https://dorar.net/aqeeda/8/some-slug': ('aqidah', {'id': '8'}),
            'https://dorar.net/feqhia/669': ('fiqh', {'id': '669'}),
            'https://dorar.net/history/event/1': ('sirah', {'id': '1'}),
            'https://islamic-content.com/dictionary/word/3529/en': ('term', {'id': '3529', 'lang': 'en'}),
            'https://www.islamic-content.com/dictionary/word/5748': ('term', {'id': '5748'}),
        }
        for url, (kind, info) in cases.items():
            k, i = dfp.detect_kind(url)
            self.assertEqual(k, kind, url)
            for key, val in info.items():
                self.assertEqual(i[key], val, url)

    def test_unsupported_url_fails(self):
        for url in ('https://dorar.net/hadith/search?q=x', 'https://example.com/aqeeda/8',
                    'https://dorar.net/alakhlaq/3'):
            with self.assertRaises(SystemExit):
                dfp.detect_kind(url)


class ChromeStripping(unittest.TestCase):
    def body(self, text, name='p.md'):
        with tempfile.TemporaryDirectory() as d:
            page = dfp.load_page(write(d, name, text))
        return dfp.clean_page(page)[3]

    def assertNoChrome(self, texts):
        joined = '\n'.join(texts)
        for bad in ('قائمة تجريبية', 'منهج العمل', 'الشيخ تجريبي', 'بدون تشكيل', 'طريقة البحث',
                    'Button', 'Input', 'Select', 'انشر المادة', 'تسجيل الدخول', 'كلمة المرور',
                    'رابط ذيل', 'السابق', 'التالي', 'iframe', 'لجنة الإشراف', 'محتويات الصفحة',
                    'الرابط المختصر', 'انظر أيضا', 'تنويه', 'تصفح الكل', 'عن الموسوعة'):
            self.assertNotIn(bad, joined)

    def test_tafsir_body_only(self):
        body = self.body(tafsir_page())
        self.assertEqual([l.text for l in body], [
            'عنوان تجريبي', 'غريب الكلمات',
            'نص تجريبي أول [1] يُنظر: ((مصدر تجريبي)) (1/2). .', 'نص تجريبي ثان',
            'المعنى الإجمالي', 'نص تجريبي ثالث', 'نص عن عذاب القبر تجريبي'])
        self.assertEqual([l.num for l in body], list(range(1, 8)))
        self.assertNoChrome(l.text for l in body)

    def test_section_headings_and_footnote_flags(self):
        body = self.body(tafsir_page())
        self.assertEqual(body[1].flags, ['H', 'S'])
        self.assertEqual(body[2].flags, ['FN'])
        self.assertEqual(body[4].flags, ['H', 'S'])
        self.assertEqual(body[3].flags, [])

    def test_aqidah_page(self):
        body = self.body(aqeeda_page())
        self.assertEqual([l.text for l in body], ['فرع تجريبي', 'نص عقدي تجريبي أول',
                                                  'نص عقدي تجريبي ثان'])
        self.assertNoChrome(l.text for l in body)

    def test_fiqh_page(self):
        body = self.body(header('https://dorar.net/feqhia/6') + FIQH_FORM + FOOTER)
        self.assertEqual([l.text for l in body], ['مبحث تجريبي', 'مسألة تجريبية أولى',
                                                  'قول تجريبي أول', 'قول تجريبي ثان'])
        self.assertNoChrome(l.text for l in body)

    def test_history_page_filter_form_removed(self):
        body = self.body(history_page())
        self.assertEqual([l.text for l in body], [
            'حدث تجريبي .', 'العام الهجري : 1 العام الميلادي : 2', 'تفاصيل الحدث:',
            'نص تاريخي تجريبي أول', 'نص تاريخي تجريبي ثان'])
        self.assertNoChrome(l.text for l in body)

    def test_show_prints_numbered_lines(self):
        with tempfile.TemporaryDirectory() as d:
            out, _ = run(dfp.main, 'show', write(d, 'a.md', tafsir_page()))
        rows = out.strip().split('\n')
        self.assertTrue(rows[0].startswith('# kind=tafsir url=https://dorar.net/tafseer/2/3'))
        self.assertRegex(rows[3], r'^\s+3\s+FN\s+نص تجريبي أول \[1\]')
        self.assertEqual(len(rows), 8)


class DraftItems(unittest.TestCase):
    def draft(self, text, *argv, name='p.md', items_dir=None):
        with tempfile.TemporaryDirectory() as d:
            argv = ['draft', write(d, name, text), *argv]
            out, err = run(dfp.main, *argv)
        return json.loads(out)[0], err

    def test_selection_is_verbatim_and_contiguous(self):
        item, _ = self.draft(tafsir_page(), '--type', 'tafsir', '--verses', '2:5-6',
                             '--lines', '3-4', '--value', 'patience')
        self.assertEqual(item['arabic_text'],
                         'نص تجريبي أول [1] يُنظر: ((مصدر تجريبي)) (1/2). .\nنص تجريبي ثان')
        self.assertEqual(item['number'], '2:5-6')
        self.assertEqual(item['book'], 'موسوعة التفسير - الدرر السنية')
        self.assertEqual(item['source_site'], 'dorar.net')
        self.assertEqual(item['source_url'], 'https://dorar.net/tafseer/2/3')
        self.assertEqual(item['verification_status'], 'unverified')
        self.assertEqual(item['content_level'], 'B')
        self.assertEqual(item['values'], ['patience'])
        self.assertEqual(item['title_en'], 'Tafsir of 2:5-6')

    def test_strip_footnotes_only_removes_markers(self):
        item, err = self.draft(tafsir_page(), '--type', 'tafsir', '--verses', '2:5',
                               '--lines', '3', '--value', 'patience', '--strip-footnotes')
        self.assertEqual(item['arabic_text'], 'نص تجريبي أول يُنظر: ((مصدر تجريبي)) (1/2). .')
        self.assertIn('only the "[n]" markers', err)

    def test_lines_out_of_range_and_type_mismatch(self):
        with tempfile.TemporaryDirectory() as d:
            f = write(d, 'a.md', tafsir_page())
            with self.assertRaises(SystemExit):
                run(dfp.main, 'draft', f, '--type', 'tafsir', '--verses', '2:5', '--lines', '5-99',
                    '--value', 'x')
            with self.assertRaises(SystemExit):
                run(dfp.main, 'draft', f, '--type', 'fiqh', '--lines', '1-2', '--value', 'x')
            with self.assertRaises(SystemExit):  # tafsir needs --verses
                run(dfp.main, 'draft', f, '--type', 'tafsir', '--lines', '1-2', '--value', 'x')

    def test_levels_numbers_and_books_per_kind(self):
        item, _ = self.draft(aqeeda_page(), '--type', 'aqidah', '--lines', '2-3', '--value', 'x',
                             '--title-en', 'T')
        self.assertEqual((item['number'], item['content_level'], item['book']),
                         ('8', 'A', 'الموسوعة العقدية - الدرر السنية'))
        self.assertEqual(item['title_ar'], 'فرع تجريبي')
        item, _ = self.draft(history_page(), '--type', 'sirah', '--lines', '4-5', '--value', 'x')
        self.assertEqual((item['number'], item['content_level'], item['book']),
                         ('1', 'A', 'الموسوعة التاريخية - الدرر السنية'))
        fq = header('https://dorar.net/feqhia/6') + FIQH_FORM + FOOTER
        item, _ = self.draft(fq, '--type', 'fiqh', '--lines', '2-3', '--value', 'x')
        self.assertEqual((item['number'], item['content_level'], item['book']),
                         ('6', 'B', 'الموسوعة الفقهية - الدرر السنية'))
        self.assertNotIn('disagreement_note_ar', item)

    def test_fiqh_with_disagreement_is_level_c(self):
        fq = header('https://dorar.net/feqhia/6') + FIQH_FORM + FOOTER
        item, err = self.draft(fq, '--type', 'fiqh', '--lines', '2-4', '--value', 'x',
                               '--disagreement-ar', 'العلماء مختلفون', '--level', 'A')
        self.assertEqual(item['content_level'], 'C')
        self.assertEqual(item['disagreement_note_ar'], 'العلماء مختلفون')
        self.assertNotIn('level C needs', err)

    def test_fragment_and_keywords(self):
        item, _ = self.draft(aqeeda_page(), '--type', 'aqidah', '--lines', '2', '--value', 'x',
                             '--fragment', 'l2', '--keywords-ar', 'أ, ب')
        self.assertEqual(item['source_url'], 'https://dorar.net/aqeeda/8#l2')
        self.assertEqual(item['keywords_ar'], ['أ', 'ب'])

    def test_out_file_merges_and_replaces(self):
        with tempfile.TemporaryDirectory() as d:
            f = write(d, 'a.md', aqeeda_page())
            out = str(Path(d) / 'drafts.json')
            run(dfp.main, 'draft', f, '--type', 'aqidah', '--lines', '2', '--value', 'x', '--out', out)
            run(dfp.main, 'draft', f, '--type', 'aqidah', '--lines', '3', '--value', 'x', '--out', out)
            data = json.loads(Path(out).read_text(encoding='utf-8'))
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]['arabic_text'], 'نص عقدي تجريبي ثان')
            run(dfp.main, 'draft', f, '--type', 'aqidah', '--lines', '3', '--value', 'x',
                '--fragment', 'b', '--out', out)
            self.assertEqual(len(json.loads(Path(out).read_text(encoding='utf-8'))), 2)

    def test_related_checked_against_bank(self):
        with tempfile.TemporaryDirectory() as d:
            items = Path(d) / 'items'
            items.mkdir()
            (items / 'v.json').write_text(json.dumps([
                {'type': 'verse', 'surah': 2, 'ayah': 3}, {'type': 'hadith', 'number': '1'}]),
                encoding='utf-8')
            self.assertEqual(dfp.bank_verses(items), {(2, 3)})
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                dfp.check_related(['verse:2:3', 'verse:2:4'], items)
            self.assertIn('verse:2:4 is not in the bank', err.getvalue())
            self.assertNotIn('verse:2:3 is not', err.getvalue())
            with self.assertRaises(SystemExit):
                dfp.check_related(['2:3'], items)


class AgeScreen(unittest.TestCase):
    def test_deny_list_words_found(self):
        cats = {c for c, _ in dfp.age_screen('نص عن عذاب القبر تجريبي')}
        self.assertEqual(cats, {'afterlife_graphic', 'afterlife_mention'})  # عذاب mention + القبر graphic
        self.assertIn('jihad', {c for c, _ in dfp.age_screen('كتاب الجهاد والسيف')})
        self.assertIn('punishment', {c for c, _ in dfp.age_screen('وبالحدود والقصاص')})

    def test_clean_text_not_flagged(self):
        self.assertEqual(dfp.age_screen('نص تجريبي بسيط عن الأدب والصدق وحديث النبي'), [])

    def test_warning_goes_to_stderr_on_draft(self):
        with tempfile.TemporaryDirectory() as d:
            f = write(d, 'a.md', tafsir_page())
            _, err = run(dfp.main, 'draft', f, '--type', 'tafsir', '--verses', '2:5', '--lines', '7',
                         '--value', 'x')
            self.assertIn('WARNING: age screen [afterlife_graphic]', err)
            _, err = run(dfp.main, 'draft', f, '--type', 'tafsir', '--verses', '2:5', '--lines', '6',
                         '--value', 'x')
            self.assertNotIn('age screen', err)

    def test_quoted_markers_warn(self):
        w = io.StringIO()
        with contextlib.redirect_stderr(w):
            dfp.screen_excerpt('نص تجريبي و ((مصدر تجريبي)) [1]')
        self.assertIn('quoted hadith', w.getvalue())
        self.assertIn('footnote markers', w.getvalue())

    def test_deny_stems_are_normalised(self):
        for stems in dfp.DENY_STEMS.values():
            for s in stems:
                self.assertEqual(s, dfp.normalize_ar(s))
        self.assertIn('رده', dfp.DENY_STEMS['crime'])
        self.assertIn('مرتد', dfp.DENY_STEMS['crime'])

    def test_conjugations_and_new_topics(self):
        for text, cat in (('يقتل', 'crime'), ('قتلوا', 'crime'), ('القتلى', 'crime'),
                          ('الطلاق', 'marriage_relations'), ('الحيض', 'marriage_relations'),
                          ('النفاس', 'marriage_relations'), ('الجنابة', 'marriage_relations'),
                          ('الانتحار', 'crime'), ('الذبح', 'crime'), ('الصلب', 'punishment'),
                          ('الرقيق', 'slavery'), ('السبي', 'slavery'), ('المرتد', 'crime'),
                          ('الردة', 'crime')):
            self.assertIn(cat, {c for c, _ in dfp.age_screen(text)}, text)
        # no false positive on short everyday words
        self.assertEqual(dfp.age_screen('رقم قطة حديث صلاة سبب'), [])

    def test_afterlife_mention_is_a_tone_flag_not_an_age_hit(self):
        # hope first: simple words only ask for a gentle tone; plain fire is just a mention
        for text in ('الجنة والنار', 'جهنم', 'يوم القيامة والآخرة', 'أشعل أبي النار للشواء',
                     'Paradise, Hell, the Fire and the Last Day'):
            cats = {c for c, _ in dfp.age_screen(text)}
            self.assertEqual(cats, {'afterlife_mention'}, text)
        w = io.StringIO()
        with contextlib.redirect_stderr(w):
            dfp.screen_excerpt('الجنة لمن أطاع الله')
        self.assertIn('tone check [afterlife_mention]', w.getvalue())
        self.assertNotIn('age screen', w.getvalue())

    def test_afterlife_graphic_stays_an_age_10_13_hit(self):
        for text in ('عذاب القبر', 'القبر وعذابه', 'البرزخ', 'شجرة الزقوم', 'عذاب السعير',
                     'منكر ونكير', 'يشربون صديدا', 'السلاسل والأغلال',
                     'torment in the grave', 'boiling water', 'the Barzakh'):
            self.assertIn('afterlife_graphic', {c for c, _ in dfp.age_screen(text)}, text)
        w = io.StringIO()
        with contextlib.redirect_stderr(w):
            dfp.screen_excerpt('عذاب القبر')
        self.assertIn('age screen [afterlife_graphic]', w.getvalue())

    def test_values_words_sharing_graphic_stems_are_not_hits(self):
        for text in ('النهي عن المنكر', 'صديق حميم'):   # wrongdoing; a close friend
            self.assertEqual(dfp.age_screen(text), [], text)

    def test_english_screen(self):
        cats = {c for c, _ in dfp.age_screen('He was killed; a divorce; menstruation; slaves; '
                                              'suicide; slaughter; crucified; hell; grave; punished')}
        self.assertEqual(cats, {'crime', 'marriage_relations', 'slavery', 'punishment',
                                'afterlife_mention', 'afterlife_graphic'})
        self.assertEqual(dfp.age_screen('Hello, a shell and a gravy boat'), [])


class InlineVerse(unittest.TestCase):
    PAGE = (header('https://dorar.net/aqeeda/8') + '# الموسوعة العقدية\n# فرع تجريبي\n'
            'نص تجريبي قبل [يس: 40] وبعده\nنص نظيف تجريبي\nنص ﴿ تجريبي ﴾ بلا مرجع\n' + FOOTER)

    def go(self, *argv):
        with tempfile.TemporaryDirectory() as d:
            return run(dfp.main, 'draft', write(d, 'a.md', self.PAGE), '--type', 'aqidah',
                       '--value', 'x', *argv)

    def test_refused_by_default(self):
        with self.assertRaises(SystemExit) as cm:
            self.go('--lines', '2')
        self.assertIn('quotes Quran inline', str(cm.exception))

    def test_refused_with_flag_but_without_related(self):
        with self.assertRaises(SystemExit) as cm:
            self.go('--lines', '2', '--allow-inline-verse')
        self.assertIn('verse:36:40', str(cm.exception))

    def test_refused_with_related_but_without_flag(self):
        with self.assertRaises(SystemExit):
            self.go('--lines', '2', '--related', 'verse:36:40')

    def test_allowed_with_both_and_still_warns(self):
        out, err = self.go('--lines', '2', '--related', 'verse:36:40', '--allow-inline-verse')
        self.assertEqual(json.loads(out)[0]['related'], ['verse:36:40'])
        self.assertIn('inline Quran text allowed', err)

    def test_clean_lines_pass_and_verse_marks_without_reference_refused(self):
        out, _ = self.go('--lines', '3')
        self.assertEqual(json.loads(out)[0]['arabic_text'], 'نص نظيف تجريبي')
        with self.assertRaises(SystemExit):
            self.go('--lines', '4', '--allow-inline-verse')


class SentenceCuts(unittest.TestCase):
    """draft --sentences A-B on a page whose whole event is one cleaned line (synthetic text)."""
    LINE = ('جملة تجريبية أولى تنتهي هنا. جملة تجريبية ثانية (مع نقطة. داخل القوسين) تنتهي؟ '
            'قال شخص تجريبي: "اقتباس تجريبي. بنقطة" ثم تكملة!جملة بلا فاصلة قبلها... '
            'جملة أخيرة بلا علامة')

    def page(self, line):
        return history_page().replace('نص تاريخي تجريبي أول', line)

    def line_num(self, f, text):
        _, _, _, body = dfp.clean_page(dfp.load_page(f))
        return next(l.num for l in body if l.text == text)

    def test_split_keeps_terminators_and_rejoins(self):
        s = dfp.split_sentences(self.LINE)
        self.assertEqual(''.join(s), self.LINE)
        self.assertEqual([x.strip() for x in s], [
            'جملة تجريبية أولى تنتهي هنا.',
            'جملة تجريبية ثانية (مع نقطة. داخل القوسين) تنتهي؟',
            'قال شخص تجريبي: "اقتباس تجريبي. بنقطة" ثم تكملة!',
            'جملة بلا فاصلة قبلها...',
            'جملة أخيرة بلا علامة'])
        self.assertEqual(dfp.split_sentences('بلا علامة'), ['بلا علامة'])
        self.assertEqual(dfp.split_sentences(''), [])

    def test_range_cut_is_a_substring_and_shown(self):
        with tempfile.TemporaryDirectory() as d:
            f = write(d, 'h.md', self.page(self.LINE))
            n = self.line_num(f, self.LINE)
            out, _ = run(dfp.main, 'show', f, '--sentences', str(n))
            self.assertIn(f'{n}.2   جملة تجريبية ثانية', out)
            self.assertEqual(len([l for l in out.strip().split('\n') if not l.startswith('#')]), 5)
            out, _ = run(dfp.main, 'draft', f, '--type', 'sirah', '--value', 'honesty',
                         '--lines', str(n), '--sentences', '2-3')
            text = json.loads(out)[0]['arabic_text']
            self.assertEqual(text, 'جملة تجريبية ثانية (مع نقطة. داخل القوسين) تنتهي؟ '
                                   'قال شخص تجريبي: "اقتباس تجريبي. بنقطة" ثم تكملة!')
            self.assertIn(text, Path(f).read_text(encoding='utf-8'))
            out, _ = run(dfp.main, 'draft', f, '--type', 'sirah', '--value', 'honesty',
                         '--lines', str(n), '--sentences', '1')
            self.assertEqual(json.loads(out)[0]['arabic_text'], 'جملة تجريبية أولى تنتهي هنا.')

    def test_invalid_ranges_fail(self):
        with tempfile.TemporaryDirectory() as d:
            f = write(d, 'h.md', self.page(self.LINE))
            n = self.line_num(f, self.LINE)
            for lines, sents in ((str(n), '6'), (str(n), '3-2'), (str(n), 'x'),
                                 (f'{n}-{n + 1}', '1')):
                with self.assertRaises(SystemExit, msg=(lines, sents)):
                    run(dfp.main, 'draft', f, '--type', 'sirah', '--value', 'x',
                        '--lines', lines, '--sentences', sents)

    def test_inline_verse_and_age_screen_still_apply_to_the_cut(self):
        line = 'جملة نظيفة تجريبية. جملة فيها ﴿ علامات ﴾ [تجريبي: 3]. جملة فيها كلمة سيف تجريبية.'
        with tempfile.TemporaryDirectory() as d:
            f = write(d, 'h.md', self.page(line))
            n = self.line_num(f, line)
            out, err = run(dfp.main, 'draft', f, '--type', 'sirah', '--value', 'x',
                           '--lines', str(n), '--sentences', '1')
            self.assertEqual(json.loads(out)[0]['arabic_text'], 'جملة نظيفة تجريبية.')
            self.assertNotIn('age screen', err)
            with self.assertRaises(SystemExit):
                run(dfp.main, 'draft', f, '--type', 'sirah', '--value', 'x',
                    '--lines', str(n), '--sentences', '1-2')
            _, err = run(dfp.main, 'draft', f, '--type', 'sirah', '--value', 'x',
                         '--lines', str(n), '--sentences', '3')
            self.assertIn('age screen [jihad]', err)


class TermPages(unittest.TestCase):
    def test_title_and_definitions_parsed(self):
        with tempfile.TemporaryDirectory() as d:
            page = dfp.load_page(write(d, 'a.md', term_page()))
        kind, info, title, body = dfp.clean_page(page)
        self.assertEqual(kind, 'term')
        self.assertEqual(title, {'en': 'Placeholder Term', 'ar': 'مصطلح تجريبي'})
        self.assertEqual([l.text for l in body], [
            'تعريف مصطلح تجريبي يشرح المعنى بكلمات تجريبية فقط',
            'A placeholder definition that explains the term in plain words'])
        t = dfp.parse_term(title, body)
        self.assertEqual((t['ar_line'], t['en_line']), (1, 2))

    def test_term_draft(self):
        with tempfile.TemporaryDirectory() as d:
            out, _ = run(dfp.main, 'draft', write(d, 'a.md', term_page()), '--type', 'term',
                         '--value', 'x')
        item = json.loads(out)[0]
        self.assertEqual(item['title_en'], 'Placeholder Term')
        self.assertEqual(item['title_ar'], 'مصطلح تجريبي')
        self.assertEqual(item['arabic_text'], 'تعريف مصطلح تجريبي يشرح المعنى بكلمات تجريبية فقط')
        self.assertEqual(item['english_text'],
                         'A placeholder definition that explains the term in plain words')
        self.assertEqual(item['translation_name'], 'Al-Jamhara (en)')
        self.assertEqual((item['number'], item['book'], item['source_site']),
                         ('1018', 'Al-Jamhara Islamic Dictionary', 'islamic-content.com'))
        self.assertEqual(item['source_url'], 'https://islamic-content.com/dictionary/word/1018/en')
        self.assertEqual((item['content_level'], item['verification_status']), ('A', 'unverified'))

    def test_term_without_english(self):
        with tempfile.TemporaryDirectory() as d:
            out, err = run(dfp.main, 'draft', write(d, 'a.md', term_page(False)), '--type', 'term',
                           '--value', 'x')
        item = json.loads(out)[0]
        self.assertNotIn('english_text', item)
        self.assertNotIn('translation_name', item)
        self.assertIn('no English definition', err)


# ---------------------------------------------------------------------------- FAQ tool

def G(c, x0, x1, y=100.0, size=12.0, font='F', kind='text', y0=None, y1=None):
    return faq.Glyph(c, x0, y - size / 2 if y0 is None else y0, x1,
                     y + size / 2 if y1 is None else y1, size, font, kind)


class GlyphRebuild(unittest.TestCase):
    def test_right_to_left_order_from_positions(self):
        # logical text "ابج" drawn right to left; stream order deliberately scrambled
        gl = [G('ج', 10, 20), G('ا', 30, 40), G('ب', 20, 30)]
        self.assertEqual(faq.rebuild_lines(gl)[0].text, 'ابج')

    def test_marks_attach_to_their_base(self):
        gl = [G('ب', 20, 30), G('ا', 30, 40), G('َ', 21, 29, y0=84, y1=88),
              G('ّ', 31, 39, y0=84, y1=88)]
        self.assertEqual(faq.rebuild_lines(gl)[0].text, 'اّبَ')

    def test_space_over_a_letter_is_dropped(self):
        gl = [G('ب', 20, 40), G('ا', 40, 60), G(' ', 28, 33), G(' ', 60, 66), G('ج', 66, 80)]
        self.assertEqual(faq.rebuild_lines(gl)[0].text, 'ج اب')

    def test_visible_gap_becomes_space(self):
        gl = [G('ب', 60, 70), G('ا', 70, 80), G('ج', 20, 30)]   # gap of 30 > 0.25 * size
        self.assertEqual(faq.rebuild_lines(gl)[0].text, 'اب ج')

    def test_numbers_read_left_to_right(self):
        # "ص 312" : digits drawn 3,1,2 from left to right, the letter to their right
        gl = [G('3', 10, 16), G('1', 16, 22), G('2', 22, 28), G(' ', 28, 33), G('ص', 33, 45)]
        self.assertEqual(faq.rebuild_lines(gl)[0].text, 'ص 312')

    def test_lines_sorted_top_to_bottom(self):
        gl = [G('ب', 10, 20, y=150), G('ا', 10, 20, y=100)]
        self.assertEqual([l.text for l in faq.rebuild_lines(gl)], ['ا', 'ب'])

    def test_symbol_and_verse_glyphs_never_become_text(self):
        import re as _re
        v, s = _re.compile(faq.VERSE_FONT_RE, _re.I), _re.compile(faq.SYMBOL_FONT_RE, _re.I)
        self.assertEqual(faq.classify('x', 'HTEWUZ+QCF4_Hafs_20', v, _re.compile('zzz')), 'verse')
        self.assertEqual(faq.classify('\ue123', 'F', v, _re.compile('zzz')), 'sym')
        self.assertEqual(faq.classify('x', 'MySymbolFont', v, s), 'sym')
        # the King Fahd *symbol* font (honorific signs) is a symbol font, not a verse font
        self.assertEqual(faq.classify('n', 'GUMSLB+KFGQPCArabicSymbols01', v, s), 'sym')
        self.assertEqual(faq.classify('\uf068', 'GUMSLB+KFGQPCArabicSymbols01', v, s), 'sym')
        self.assertEqual(faq.classify('ﷺ', 'adwa-assalaf', v, s), 'text')   # folds to its words
        gl = [G('ب', 20, 30), G('\ue123', 30, 40, kind='sym'), G('\ue001', 40, 50, kind='verse')]
        line = faq.rebuild_lines(gl)[0]
        self.assertEqual((line.text, line.n_sym, line.n_verse), (faq.VERSE_HOLE + ' ب', 1, 1))

    def test_multi_char_ligature_glyph_is_reversed(self):
        self.assertEqual(faq.fix_glyph_text('إل'), 'لإ')
        self.assertEqual(faq.fix_glyph_text('ب'), 'ب')
        self.assertEqual(faq.fix_glyph_text('ﻻ'), 'لا')
        self.assertEqual(faq.fix_glyph_text('ﷺ'), 'صلى الله عليه وسلم')

    def test_zero_width_marks_attach_to_the_base_whose_left_edge_they_sit_on(self):
        # "هِ؛": the kasra is drawn with zero width at x = heh.x0, which is also the right
        # edge of the semicolon; the edge match must win over the containment tie
        gl = [G('ه', 333.33, 338.13), G('؛', 328.5, 333.33), G('ِ', 333.33, 333.33),
              G('ل', 338.13, 342.0)]
        self.assertEqual(faq.rebuild_lines(gl)[0].text, 'لهِ؛')
        gl = [G('ل', 229.17, 233.20), G('َ', 229.17, 229.17), G('َ', 220.32, 220.32),
              G('ق', 220.32, 229.17)]                          # mark before its base in stream
        self.assertEqual(faq.rebuild_lines(gl)[0].text, 'لَقَ')

    def test_header_split_reads_printed_page(self):
        small = faq.TextLine('٣١٢', 100, 130, 30.0, 8.0)
        body = [faq.TextLine('نص تجريبي', 100, 500, 120.0, 12.0),
                faq.TextLine('نص آخر', 100, 500, 140.0, 12.0)]
        rest, printed, header = faq.split_header([small] + body, 842)
        self.assertEqual((printed, header, len(rest)), (312, '٣١٢', 2))
        rest, printed, _ = faq.split_header(body, 842)
        self.assertIsNone(printed)

    def test_footer_numbers_dropped_and_years_not_page_numbers(self):
        body = [faq.TextLine('نص تجريبي', 100, 500, 120.0, 12.0),
                faq.TextLine('نص آخر', 100, 500, 140.0, 12.0)]
        footer = faq.TextLine('١٢٣', 280, 300, 800.0, 12.0)
        rest, printed, _ = faq.split_header(body + [footer], 842)
        self.assertEqual((len(rest), printed), (2, None))
        year = faq.TextLine('١٤٤٥', 100, 130, 30.0, 8.0)
        mixed = faq.TextLine('بينات 1445 ص 77', 100, 330, 32.0, 8.0)
        rest, printed, _ = faq.split_header([year] + body, 842)
        self.assertIsNone(printed)
        rest, printed, _ = faq.split_header([mixed] + body, 842)
        self.assertEqual(printed, 77)


class PageGlyphs(unittest.TestCase):
    """page_glyphs on a hand-made rawdict shaped like the real PDF's stream."""

    class Page:
        def __init__(self, spans):
            self.spans = spans

        def get_text(self, kind):
            return {'blocks': [{'lines': [{'spans': self.spans}]}]}

    @staticmethod
    def span(font, chars, color=0x231f20, size=15.0, y=(134.5, 163.8)):
        return {'font': font, 'size': size, 'color': color,
                'chars': [{'c': c, 'bbox': (x0, y[0], x1, y[1])} for c, x0, x1 in chars]}

    def glyphs(self, *spans):
        import re as _re
        return faq.page_glyphs(self.Page(list(spans)), _re.compile(faq.VERSE_FONT_RE, _re.I),
                               _re.compile(faq.SYMBOL_FONT_RE, _re.I))

    def test_ligature_halves_are_zero_width_letters_before_their_carrier(self):
        # "الله" as drawn: alef, then heh and lam with zero width at the carrier's right edge,
        # then the carrier lam that owns the whole ligature box
        gl = self.glyphs(self.span('adwa-assalaf', [
            ('ا', 387.72, 390.56), ('ه', 387.72, 387.72), ('ل', 387.72, 387.72),
            ('ل', 378.35, 387.72), ('،', 374.03, 378.35)]))
        self.assertEqual(faq.rebuild_lines(gl)[0].text, 'الله،')
        # "الإسلام": two lam-alef ligatures in one word, and a mark on a hidden letter
        gl = self.glyphs(self.span('(AH)-Manal-High', [
            ('ا', 88.64, 91.33), ('إ', 88.64, 88.64), ('ل', 80.45, 88.64), ('س', 73.07, 80.45),
            ('ا', 73.07, 73.07), ('ل', 64.48, 73.07), ('ِ', 64.48, 64.48), ('م', 58.59, 64.48)]))
        self.assertEqual(faq.rebuild_lines(gl)[0].text, 'الإسلاِم')
        # a whole-word ligature glyph (heading font): three hidden letters, carrier alef
        gl = self.glyphs(self.span('AbdoLine', [
            ('ه', 218.20, 218.20), ('ل', 218.20, 218.20), ('ل', 218.20, 218.20),
            ('ا', 201.32, 218.20), ('؟', 194.40, 201.32)], size=16.0))
        self.assertEqual(faq.rebuild_lines(gl)[0].text, 'الله؟')

    def test_coloured_digit_of_the_heading_font_is_a_bullet(self):
        gl = self.glyphs(
            self.span('fotograami-zkhref', [(' ', 426.47, 437.38)], color=0x8d2f45, size=16.0),
            self.span('(AH)-Manal-High', [('3', 419.39, 423.29)], color=0x8d2f45, size=16.0),
            self.span('adwa-assalaf', [('و', 413.10, 419.39), ('ج', 404.54, 413.10)]))
        self.assertEqual(faq.rebuild_lines(gl)[0].text, '•وج')
        self.assertTrue(faq.BULLET.match('•وج'))
        # the black page number in the same font stays a digit
        gl = self.glyphs(self.span('(AH)-Manal-High', [('3', 406.0, 411.0), ('0', 411.0, 416.0)],
                                   size=12.0))
        self.assertEqual(faq.rebuild_lines(gl)[0].text, '30')

    def test_honorific_symbol_glyph_is_dropped_and_counted(self):
        gl = self.glyphs(self.span('adwa-assalaf', [('م', 90.0, 96.0)]),
                         self.span('GUMSLB+KFGQPCArabicSymbols01', [('n', 68.4, 82.35)], size=14.0),
                         self.span('adwa-assalaf', [('و', 60.0, 66.0)]))
        line = faq.rebuild_lines(gl)[0]
        self.assertEqual((line.text, line.n_sym, line.n_verse), ('م و', 1, 0))

    class TracedPage(Page):
        """A page whose glyph trace (get_texttrace) can disagree with its rawdict."""
        def __init__(self, spans, trace):
            super().__init__(spans)
            self.trace = trace

        def get_texttrace(self):
            return [{'size': 15.0, 'chars': [(ord(c), 0, (x0, 163.0), (x0, 134.5, x1, 163.8))
                                             for c, x0, x1 in self.trace]}]

    def test_alef_dropped_as_a_duplicate_is_restored_from_the_trace(self):
        import re as _re
        # "الد" as the rawdict gives it: the real alef (203.18-205.88) is missing, only the
        # ligature's hidden zero-width alef at the carrier's right edge is left; the trace
        # still has the real alef glyph there
        raw = [(' ', 205.88, 209.63), ('ا', 203.18, 203.18), ('ل', 194.82, 203.18), ('د', 189.83, 194.82)]
        trace = [(' ', 205.88, 209.63), ('ا', 203.18, 205.88), ('ل', 194.82, 203.18), ('د', 189.83, 194.82)]
        pg = self.TracedPage([self.span('adwaassalaf-Bold', raw)], trace)
        gl = faq.page_glyphs(pg, _re.compile(faq.VERSE_FONT_RE, _re.I), _re.compile(faq.SYMBOL_FONT_RE, _re.I))
        line = faq.rebuild_lines(gl)[0]
        self.assertEqual((line.text, line.n_alef), ('الاد', 1))
        # the same word with both alefs in the rawdict (regular font) gains nothing
        raw2 = [(' ', 205.88, 209.63), ('ا', 203.18, 205.88), ('ا', 203.18, 203.18), ('ل', 194.82, 203.18), ('د', 189.83, 194.82)]
        gl = faq.page_glyphs(self.TracedPage([self.span('adwa-assalaf', raw2)], trace),
                             _re.compile(faq.VERSE_FONT_RE, _re.I), _re.compile(faq.SYMBOL_FONT_RE, _re.I))
        line = faq.rebuild_lines(gl)[0]
        self.assertEqual((line.text, line.n_alef), ('الاد', 0))
        # "لاخ" after a space (no alef on the page): the trace has the previous word's alef
        # elsewhere and no zero-width twin at the carrier's edge -> nothing restored
        raw3 = [('ا', 382.05, 384.88), (' ', 379.55, 382.05), ('ا', 379.55, 379.55), ('ل', 370.83, 379.55), ('خ', 362.27, 370.83)]
        trace3 = [('ا', 382.05, 384.88), (' ', 379.55, 382.05), ('ل', 370.83, 379.55), ('خ', 362.27, 370.83)]
        gl = faq.page_glyphs(self.TracedPage([self.span('adwa-assalaf', raw3)], trace3),
                             _re.compile(faq.VERSE_FONT_RE, _re.I), _re.compile(faq.SYMBOL_FONT_RE, _re.I))
        line = faq.rebuild_lines(gl)[0]
        self.assertEqual((line.text, line.n_alef), ('ا لاخ', 0))
        # a traced alef with a zero-width twin but no lam ending there (not the ligature
        # shape) is not restored either, and one trace entry is restored once
        pg = self.TracedPage([self.span('adwaassalaf-Bold', [('ا', 203.18, 203.18), ('د', 194.82, 203.18)])],
                             [('ا', 203.18, 205.88), ('ا', 203.18, 205.88), ('د', 194.82, 203.18)])
        gl = faq.page_glyphs(pg, _re.compile(faq.VERSE_FONT_RE, _re.I), _re.compile(faq.SYMBOL_FONT_RE, _re.I))
        self.assertEqual(sum(1 for g in gl if g.restored), 0)
        q = {'n': 9, 'question': 'سؤال', 'entries': [], 'toc': None,
             'blocks': {'short': [{'block': 'short', 'text': 'الد', 'page': 1, 'printed': 5, 'sym': 0,
                                   'verse': 0, 'alef': 1, 'span': {(1, 5)}}],
                        'similar': [], 'question': [], 'gist': [], 'detailed': []}}
        self.assertIn('[alef x1:', faq.render_text(q))

    def test_list_marker_glyph_labels_follow_the_trace(self):
        import re as _re
        # the rawdict labels the marker "1)" as space/1/) at the digit's, space's and
        # bracket's boxes; the trace shows which glyph is where (one line, three rawdict spans)
        pg = self.TracedPage(
            [self.span('adwaassalaf-Bold', [(' ', 438.39, 445.89)], color=0x00a886),
             self.span('adwaassalaf-Bold', [('1', 429.64, 433.39), (')', 433.39, 438.38)], color=0x00a886),
             self.span('adwa-assalaf', [('ع', 422.97, 429.66), ('ق', 418.01, 422.97)])],
            [('1', 438.39, 445.89), (' ', 429.64, 433.39), (')', 433.39, 438.38),
             ('ع', 422.97, 429.66), ('ق', 418.01, 422.97)])
        gl = faq.page_glyphs(pg, _re.compile(faq.VERSE_FONT_RE, _re.I), _re.compile(faq.SYMBOL_FONT_RE, _re.I))
        line = faq.rebuild_lines(gl)[0]
        self.assertEqual(line.text, '1) عق')
        self.assertTrue(faq.BULLET.match(line.text))
        # a trace that is not a permutation of the rawdict's characters changes nothing
        pg = self.TracedPage(
            [self.span('adwaassalaf-Bold', [(' ', 438.39, 445.89), ('1', 429.64, 433.39), (')', 433.39, 438.38)],
                       color=0x00a886)],
            [('7', 438.39, 445.89), (' ', 429.64, 433.39), (')', 433.39, 438.38)])
        gl = faq.page_glyphs(pg, _re.compile(faq.VERSE_FONT_RE, _re.I), _re.compile(faq.SYMBOL_FONT_RE, _re.I))
        self.assertEqual(faq.rebuild_lines(gl)[0].text, ')1')


class FaqBlocks(unittest.TestCase):
    def test_labels_detected(self):
        self.assertEqual(faq.match_label('السؤال'), 'question')
        self.assertEqual(faq.match_label('السُّؤَال :'), 'question')
        self.assertEqual(faq.match_label('السؤال (57)'), 'question')
        self.assertEqual(faq.match_label('عبارات مشابهة للسؤال'), 'similar')
        self.assertEqual(faq.match_label('مضمون السؤال'), 'gist')
        self.assertEqual(faq.match_label('مختصر الإجابة'), 'short')
        self.assertEqual(faq.match_label('مختصر الاجابة:'), 'short')
        self.assertEqual(faq.match_label('الجواب التفصيلي'), 'detailed')
        self.assertEqual(faq.match_label('الجواب'), 'heading')
        self.assertIsNone(faq.match_label('السؤال عن شيء تجريبي'))
        self.assertIsNone(faq.match_label('نص تجريبي'))
        self.assertEqual(faq.split_inline_label('السؤال: نص تجريبي'), ('question', 'نص تجريبي'))
        self.assertEqual(faq.split_inline_label('نص: تجريبي'), (None, 'نص: تجريبي'))
        self.assertTrue(faq.is_question_label('السؤال: نص'))
        self.assertFalse(faq.is_question_label('مضمون السؤال'))

    def test_toc_entries_including_wrapped_title(self):
        entries, sections = faq.parse_toc_lines([
            '4 بينات - عنوان الكتاب',                 # running header: not entry 4
            'المسألة الصفحة',
            'مدخل.........19',
            'أولًا: قسم تجريبي ..........21',
            '1- فرع مرقم ........21',
            '(1): عنوان تجريبي أول ........ 5',
            '- فرع تجريبي',
            '(2)- عنوان تجريبي طويل جدا',
            'يكمل في السطر التالي ..... ٦',
            '(3) عنوان ثالث …………… 12',
            '(4)- عنوان ينتهي بسؤال؟..12',
        ])
        self.assertEqual([(e['n'], e['page']) for e in entries], [(1, 5), (2, 6), (3, 12), (4, 12)])
        self.assertEqual(entries[0]['title'], 'عنوان تجريبي أول')
        self.assertEqual(entries[1]['title'], 'عنوان تجريبي طويل جدا يكمل في السطر التالي')
        self.assertEqual(entries[3]['title'], 'عنوان ينتهي بسؤال؟')
        self.assertEqual([s[1] for s in sections],
                         ['أولًا: قسم تجريبي', '1- فرع مرقم', '- فرع تجريبي'])

    def test_heading_closes_the_block_before_it(self):
        def L(text, y):
            t = faq.TextLine(text, 100, 560, y, 12.0)
            t.page, t.printed = 0, 5
            return t
        lines = [L('السؤال', 100), L('نص السؤال', 120), L('عبارات مشابهة للسؤال', 140),
                 L('•صيغة أولى', 160), L('الجواب', 180), L('مضمون السؤال', 200), L('مضمون', 220)]
        blocks, _ = faq.build_paragraphs(lines)
        self.assertEqual([p['text'] for p in blocks['similar']], ['صيغة أولى'])
        self.assertEqual([p['text'] for p in blocks['gist']], ['مضمون'])
        self.assertNotIn('heading', blocks)

    def test_bullet_item_keeps_its_hanging_indent_lines(self):
        def L(text, y, x1):
            t = faq.TextLine(text, 36, x1, y, 15.0)
            t.page, t.printed = 0, 5
            return t
        lines = [L('السؤال', 100, 434), L('نص السؤال', 120, 446), L('عبارات مشابهة للسؤال', 140, 437),
                 L('•صيغة أولى سطر أول', 160, 423), L('تكملة الصيغة', 183, 419),   # hangs by the bullet
                 L('•صيغة ثانية', 206, 423), L('مختصر الإجابة', 240, 437),
                 L('فقرة', 260, 446), L('سطر قصير مسنن', 283, 400)]                # indented: new paragraph
        blocks, _ = faq.build_paragraphs(lines)
        self.assertEqual([p['text'] for p in blocks['similar']],
                         ['صيغة أولى سطر أول تكملة الصيغة', 'صيغة ثانية'])
        self.assertEqual([p['text'] for p in blocks['short']], ['فقرة', 'سطر قصير مسنن'])

    def test_lost_alef_of_marked_lam_alef_restored_and_flagged(self):
        gl = [G('م', 56.13, 61.35), G('ب', 52.82, 56.13), G('ط', 45.38, 52.82), G('ِ', 45.38, 45.38),
              G('ل', 36.0, 45.38), G('ً', 36.0, 36.0), G(' ', 33.5, 36.0), G('ب', 28.0, 33.5)]
        self.assertEqual(faq.rebuild_lines(gl)[0].text, 'مبطِلًا ب')
        fix = lambda s: faq.LOST_ALEF.sub(r'\g<0>ا', s)
        self.assertEqual(fix('أولً: نصٌّ، مثلً. مُصلًّى'), 'أولًا: نصٌّ، مثلًا. مُصلًّى')
        self.assertEqual(fix('أَلَ تكفي؟ إِلَّ اللهَ، وَلَ قطيعةُ، بِلَ شكٍّ، لَ شفاءَ'),
                         'أَلَا تكفي؟ إِلَّا اللهَ، وَلَا قطيعةُ، بِلَا شكٍّ، لَا شفاءَ')
        # real words and unvocalised lam-alef (its alef is present) are left alone
        for s in ('يَسْألُ أهلَ', 'أَلَمْ أُخْبَرْ', 'لا يعبُدون إلا اللهَ', 'جَعَلَ كلَّ هلْ بَلْ أَلْ', 'العِلمِ',
                  'بَلَى'):
            self.assertEqual(fix(s), s, s)
        q = {'n': 9, 'question': 'سؤال', 'entries': [], 'toc': None,
             'blocks': {'short': [{'block': 'short', 'text': 'كان مبطِلًا أَلَا ترى', 'page': 1,
                                   'printed': 5, 'sym': 0, 'verse': 0, 'span': {(1, 5)}}],
                        'similar': [], 'question': [], 'gist': [], 'detailed': []}}
        self.assertIn('[alef x2: alef of a marked lam-alef restored', faq.render_text(q))

    def test_paragraphs_by_label_and_second_question_stops(self):
        def L(text, y, page=0, printed=5, x1=560):
            t = faq.TextLine(text, 100, x1, y, 12.0)
            t.page, t.printed = page, printed
            return t
        lines = [L('السؤال', 100), L('نص السؤال التجريبي', 120),
                 L('عبارات مشابهة للسؤال', 140), L('- صيغة أولى', 160), L('- صيغة ثانية', 180),
                 L('مختصر الإجابة', 200), L('فقرة أولى سطر 1', 220), L('فقرة أولى سطر 2', 240),
                 L('فقرة ثانية', 290), L('الجواب التفصيلي', 310), L('تفصيل', 330),
                 L('السؤال', 350), L('سؤال تال', 370)]
        blocks, _ = faq.build_paragraphs(lines)
        self.assertEqual([p['text'] for p in blocks['question']], ['نص السؤال التجريبي'])
        self.assertEqual([p['text'] for p in blocks['similar']], ['صيغة أولى', 'صيغة ثانية'])
        self.assertEqual([p['text'] for p in blocks['short']],
                         ['فقرة أولى سطر 1 فقرة أولى سطر 2', 'فقرة ثانية'])
        self.assertEqual([p['text'] for p in blocks['detailed']], ['تفصيل'])

    def test_paragraph_continues_across_page_without_terminal_punctuation(self):
        def L(text, y, page, printed):
            t = faq.TextLine(text, 100, 560, y, 12.0)
            t.page, t.printed = page, printed
            return t
        lines = [L('مختصر الإجابة', 100, 0, 5), L('بداية فقرة', 120, 0, 5),
                 L('تكملة الفقرة.', 100, 1, 6), L('سطر', 120, 1, 6), L('سطر آخر', 140, 1, 6),
                 L('فقرة جديدة', 180, 1, 6)]
        lines.insert(0, L('السؤال', 80, 0, 5))
        blocks, _ = faq.build_paragraphs(lines)
        self.assertEqual([p['text'] for p in blocks['short']],
                         ['بداية فقرة تكملة الفقرة. سطر سطر آخر', 'فقرة جديدة'])
        self.assertEqual(blocks['short'][0]['printed'], 5)

    def test_dash_colon_continues_the_sentence_and_is_no_list_marker(self):
        self.assertIsNone(faq.BULLET.match('-: تكملة'))
        self.assertTrue(faq.BULLET.match('- بند'))
        self.assertTrue(faq.BULLET.match('1) بند'))
        def L(text, y):
            t = faq.TextLine(text, 100, 560, y, 12.0)
            t.page, t.printed = 0, 5
            return t
        lines = [L('السؤال', 80), L('سؤال', 100), L('مختصر الإجابة', 120), L('بداية الجملة', 140),
                 L('-: تكملة الجملة.', 160), L('1) بند أول', 180), L('2) بند ثان', 200)]
        blocks, _ = faq.build_paragraphs(lines)
        self.assertEqual([p['text'] for p in blocks['short']],
                         ['بداية الجملة -: تكملة الجملة.', '1) بند أول', '2) بند ثان'])

    def test_surah_table_and_references(self):
        self.assertEqual(len(faq.SURAH_NAMES), 114)
        self.assertEqual(len({faq.norm(n) for n in faq.SURAH_NAMES}), 114)
        self.assertEqual(faq.surah_number('سورة يس'), 36)
        self.assertEqual(faq.surah_number('آل عمران'), 3)
        self.assertEqual(faq.surah_number('الأنفال'), 8)
        self.assertEqual(faq.verse_refs('قال [يس: 40] و]النحل: ٢[ ثم [البقرة: 1-3] و [غير: 5]'),
                         [(36, 40), (16, 2), (2, 1), (2, 2), (2, 3)])


# --- synthetic PDF ---------------------------------------------------------------------

PAGE_W, PAGE_H = 595, 842


def draw_line(page, font, text, y, size=12, right=560):
    """Draw logical Arabic text right to left, digit runs left to right, one glyph at a time,
    inserted left to right (the reverse of reading order) like a visual-order PDF."""
    placed, x = [], right
    for tok in re.findall(r'\d+|.', text, re.S):
        if tok.isdigit():
            x -= sum(font.text_length(d, fontsize=size) for d in tok)
            xx = x
            for d in tok:
                placed.append((d, xx))
                xx += font.text_length(d, fontsize=size)
        else:
            x -= font.text_length(tok, fontsize=size)
            placed.append((tok, x))
    for ch, xx in reversed(placed):
        page.insert_text((xx, y), ch, fontname='F0', fontsize=size)


def make_pdf(path, bold_lines=()):
    doc = pymupdf.open()
    font = pymupdf.Font(fontfile=FONT)

    def add(printed, lines):
        page = doc.new_page(width=PAGE_W, height=PAGE_H)
        page.insert_font(fontname='F0', fontfile=FONT)
        if printed:
            draw_line(page, font, printed, 30, size=8, right=300)
        for y, text in lines:
            if text in bold_lines:
                page.insert_font(fontname='F1', fontfile=FONT.replace('Sans.ttf', 'Sans-Bold.ttf'))
                x = 560
                for tok in text:
                    x -= font.text_length(tok, fontsize=12)
                    page.insert_text((x, y), tok, fontname='F1', fontsize=12)
            else:
                draw_line(page, font, text, y)

    add(None, [(100, 'فهرس تجريبي'),
               (130, '(1) عنوان تجريبي أول ........ 5'),
               (150, '(2) عنوان تجريبي ثان ........ 6'),
               (170, '(3) عنوان تجريبي ثالث ........ 6')])
    add('5', [(100, 'السؤال'), (120, 'ما هذا السؤال التجريبي الأول'),
              (160, 'عبارات مشابهة للسؤال'), (180, '- صيغة تجريبية أولى'), (200, '- صيغة تجريبية ثانية'),
              (240, 'مضمون السؤال'), (260, 'مضمون تجريبي'),
              (300, 'مختصر الإجابة'), (320, 'فقرة أولى تجريبية سطر أول'),
              (340, 'فقرة أولى تجريبية سطر ثان'), (376, 'فقرة ثانية تجريبية'),
              (416, 'الجواب التفصيلي'), (436, 'تفصيل تجريبي طويل')])
    add('٦', [(100, 'تكملة تفصيل تجريبي'),
              (140, 'السؤال'), (160, 'السؤال التجريبي الثاني'),
              (200, 'مختصر الإجابة'), (220, 'فقرة وحيدة تجريبية [يس: 40]'),
              (240, 'تتمة [البقرة: 255]'),
              (280, 'الجواب التفصيلي'), (300, 'تفصيل ثان'),
              (340, 'السؤال'), (360, 'السؤال التجريبي الثالث'),
              (400, 'مختصر الإجابة')])
    add('7', [(100, 'فقرة ثالثة تجريبية عن السيف'), (140, 'الجواب التفصيلي'), (160, 'تفصيل ثالث')])
    doc.save(str(path))
    doc.close()


@unittest.skipUnless(pymupdf and FONT, 'needs PyMuPDF and an Arabic-capable system font')
class SyntheticPdf(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.pdf = Path(cls.tmp.name) / 'faq.pdf'
        make_pdf(cls.pdf)
        cls.cache = str(Path(cls.tmp.name) / 'cache')
        cls.items = Path(cls.tmp.name) / 'items'
        cls.items.mkdir()
        (cls.items / 'v.json').write_text(json.dumps([
            {'type': 'verse', 'surah': 36, 'ayah': 40}]), encoding='utf-8')

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def cli(self, *argv):
        return run(faq.main, argv[0], str(self.pdf), *argv[1:], '--cache-dir', self.cache,
                   '--items-dir', str(self.items))

    def test_toc(self):
        out, _ = self.cli('toc')
        rows = [r.split('\t') for r in out.strip().split('\n')]
        self.assertEqual([(r[0], r[2]) for r in rows], [('1', '5'), ('2', '6'), ('3', '6')])
        self.assertEqual(rows[0][1], 'عنوان تجريبي أول')

    def test_toc_grep(self):
        out, _ = self.cli('toc', '--grep', 'ثالث')
        self.assertEqual(out.strip().split('\t')[0], '3')

    def test_printed_pages_read_from_header(self):
        r = faq.Reader(self.pdf, cache_dir=self.cache)
        self.assertEqual([r.page(i)[1] for i in range(4)], [None, 5, 6, 7])
        labels = r.question_labels()
        self.assertEqual([p for p, _ in labels], [1, 2, 2])      # Q2 and Q3 share a PDF page
        self.assertEqual(labels, faq.Reader(self.pdf, cache_dir=self.cache).question_labels())
        for l in r.page(1)[0]:
            self.assertNotIn('5', l.text.replace('الأول', ''))   # header line removed from body

    def test_question_blocks(self):
        out, _ = self.cli('question', '1')
        self.assertIn('Q1  pdf pages 2,3  printed 5,6', out)
        self.assertIn('== السؤال\n  [1] (p.5) ما هذا السؤال التجريبي الأول', out)
        self.assertIn('[1] (p.5) صيغة تجريبية أولى', out)
        self.assertIn('[2] (p.5) صيغة تجريبية ثانية', out)
        self.assertIn('[1] (p.5) فقرة أولى تجريبية سطر أول فقرة أولى تجريبية سطر ثان', out)
        self.assertIn('[2] (p.5) فقرة ثانية تجريبية', out)
        self.assertIn('== الجواب التفصيلي', out)

    def test_second_question_starts_at_its_label_on_a_shared_page(self):
        with contextlib.redirect_stderr(io.StringIO()):
            q = faq.get_question(faq.Reader(self.pdf, cache_dir=self.cache), 2)
            q3 = faq.get_question(faq.Reader(self.pdf, cache_dir=self.cache), 3)
        self.assertEqual(q['question'], 'السؤال التجريبي الثاني')
        self.assertEqual(q['blocks']['detailed'][0]['text'], 'تفصيل ثان')
        self.assertEqual(q['blocks']['short'][0]['printed'], 6)
        self.assertEqual(q3['question'], 'السؤال التجريبي الثالث')
        self.assertEqual(q3['blocks']['short'][0]['printed'], 7)   # continues on the next page

    def test_draft_item_fields(self):
        out, err = self.cli('draft', '2', '--value', 'honesty')
        item = json.loads(out)[0]
        self.assertEqual(item['type'], 'faq')
        self.assertEqual(item['title_ar'], 'السؤال التجريبي الثاني')
        self.assertEqual(item['arabic_text'], 'فقرة وحيدة تجريبية [يس: 40] تتمة [البقرة: 255]')
        self.assertEqual(item['number'], 'Q2 · p.6')
        # another question (3) also starts on printed page 6, so the fragment says which one
        self.assertEqual(item['source_url'], 'https://dawa.center/file/7937#p6-q2')
        self.assertEqual((item['source_site'], item['content_level'], item['age_band']),
                         ('dawa.center', 'B', 'all'))
        self.assertEqual(item['verification_status'], 'unverified')
        self.assertEqual(item['related'], ['verse:36:40'])     # 2:255 is not in the bank
        self.assertEqual(item['keywords_ar'], [])
        self.assertEqual(item['values'], ['honesty'])
        self.assertEqual(item['book'], faq.BOOK)

    def test_draft_keywords_and_paragraph_selection(self):
        out, _ = self.cli('draft', '1', '--value', 'x', '--paras', '2')
        item = json.loads(out)[0]
        self.assertEqual(item['arabic_text'], 'فقرة ثانية تجريبية')
        self.assertEqual(item['keywords_ar'], ['صيغة تجريبية أولى', 'صيغة تجريبية ثانية'])
        self.assertEqual(item['source_url'], 'https://dawa.center/file/7937#p5')
        self.assertNotIn('related', item)
        with self.assertRaises(SystemExit):
            self.cli('draft', '1', '--value', 'x', '--paras', '5')

    def test_draft_uses_page_of_selected_paragraph_and_age_screen(self):
        out, err = self.cli('draft', '3', '--value', 'x', '--paras', '1')
        item = json.loads(out)[0]
        self.assertEqual(item['number'], 'Q3 · p.7')
        self.assertEqual(item['source_url'], 'https://dawa.center/file/7937#p7')
        self.assertEqual(item['age_band'], '10-13')        # doubt-type (sword) defaults to 10-13
        self.assertIn('age screen [jihad]', err)

    def test_render_writes_text_and_png(self):
        d = Path(self.tmp.name) / 'render'
        self.cli('question', '1', '--render', str(d))
        names = sorted(p.name for p in d.iterdir())
        self.assertEqual(names, ['q001-pdf0002-p5.png', 'q001-pdf0003-p6.png', 'q001.txt'])
        self.assertTrue((d / 'q001-pdf0002-p5.png').read_bytes().startswith(b'\x89PNG'))

    @unittest.skipUnless(BOLD_FONT, 'needs DejaVuSans-Bold.ttf next to DejaVuSans.ttf to draw '
                                    'the synthetic verse line in a second font')
    def test_verse_font_glyphs_block_the_draft(self):
        bold = Path(self.tmp.name) / 'bold.pdf'
        make_pdf(bold, bold_lines=('فقرة ثانية تجريبية',))
        args = [str(bold), '--verse-font', 'Bold', '--cache-dir', str(Path(self.tmp.name) / 'c2'),
                '--items-dir', str(self.items)]
        out, _ = run(faq.main, 'question', args[0], '1', *args[1:])
        self.assertIn('1 verse hole(s)', out)
        self.assertIn(faq.VERSE_HOLE, out)
        d = ['draft', args[0], '1', '--value', 'x', *args[1:]]
        with self.assertRaises(SystemExit) as cm:                     # no --related: refused
            run(faq.main, *d)
        self.assertIn('1 verse hole(s)', str(cm.exception))
        with self.assertRaises(SystemExit):                           # wrong number of labels
            run(faq.main, *d, '--related', 'verse:36:40', '--related', 'verse:36:40')
        with self.assertRaises(SystemExit) as cm:                     # verse not in the bank
            run(faq.main, *d, '--related', 'verse:2:255')
        self.assertIn('not a verse:S:A label of a verse in the bank', str(cm.exception))
        out, _ = run(faq.main, *d, '--related', 'verse:36:40')       # filled by marker only
        item = json.loads(out)[0]
        self.assertIn('{{verse:36:40}}', item['arabic_text'])
        self.assertNotIn(faq.VERSE_HOLE, item['arabic_text'])
        self.assertEqual(item['related'], ['verse:36:40'])
        out, _ = run(faq.main, *d, '--paras', '1')                    # other paragraphs are fine
        self.assertIn('"فقرة أولى', out)
        self.assertNotIn('--allow-verse-holes', faq.__doc__)

    def test_dropped_symbols_refuse_the_draft(self):
        import argparse
        para = {'block': 'short', 'text': 'نص تجريبي', 'page': 1, 'printed': 5, 'sym': 2,
                'verse': 0, 'span': {(1, 5)}}
        q = {'n': 9, 'question': 'سؤال تجريبي', 'entries': [], 'toc': None,
             'blocks': {'short': [para], 'similar': [], 'question': [], 'gist': [], 'detailed': []}}
        ns = dict(paras=None, related=[], value='x', age_band=None, items_dir=str(self.items),
                  allow_dropped_symbols=False, keep_tashkeel=False)
        with self.assertRaises(SystemExit) as cm:
            faq.build_item(q, argparse.Namespace(**ns))
        self.assertIn('--allow-dropped-symbols', str(cm.exception))
        ns['allow_dropped_symbols'] = True
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            item = faq.build_item(q, argparse.Namespace(**ns))
        self.assertEqual(item['arabic_text'], 'نص تجريبي')
        self.assertIn('restored against the rendered page', err.getvalue())

    def test_verse_marks_in_text_are_refused(self):
        import argparse
        para = {'block': 'short', 'text': 'نص ﴿ تجريبي ﴾', 'page': 1, 'printed': 5, 'sym': 0,
                'verse': 0, 'span': {(1, 5)}}
        q = {'n': 9, 'question': 'سؤال', 'entries': [], 'toc': None,
             'blocks': {'short': [para], 'similar': [], 'question': [], 'gist': [], 'detailed': []}}
        ns = argparse.Namespace(paras=None, related=[], value='x', age_band=None,
                                items_dir=str(self.items), allow_dropped_symbols=False,
                                keep_tashkeel=False)
        with self.assertRaises(SystemExit):
            faq.build_item(q, ns)

    def test_tashkeel_stripped_from_the_draft_unless_kept(self):
        import argparse
        para = {'block': 'short', 'text': 'نصٌّ تجريبيٌ مُشكَّل', 'page': 1, 'printed': 5,
                'sym': 0, 'verse': 0, 'span': {(1, 5)}}
        sim = {'block': 'similar', 'text': 'صيغةٌ', 'page': 1, 'printed': 5, 'sym': 0,
               'verse': 0, 'span': {(1, 5)}}
        q = {'n': 9, 'question': 'سؤالٌ تجريبيٌّ', 'entries': [], 'toc': None,
             'blocks': {'short': [para], 'similar': [sim], 'question': [], 'gist': [],
                        'detailed': []}}
        ns = dict(paras=None, related=[], value='x', age_band=None, items_dir=str(self.items),
                  allow_dropped_symbols=False, keep_tashkeel=False)
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            item = faq.build_item(q, argparse.Namespace(**ns))
        self.assertEqual((item['arabic_text'], item['title_ar'], item['keywords_ar']),
                         ('نص تجريبي مشكل', 'سؤال تجريبي', ['صيغة']))
        self.assertNotIn('tashkeel kept', err.getvalue())
        ns['keep_tashkeel'] = True
        with contextlib.redirect_stderr(err):
            item = faq.build_item(q, argparse.Namespace(**ns))
        self.assertEqual(item['arabic_text'], 'نصٌّ تجريبيٌ مُشكَّل')
        self.assertIn('tashkeel kept', err.getvalue())

    def test_title_falls_back_to_the_toc_title_when_the_page_prints_no_question(self):
        import argparse
        para = {'block': 'short', 'text': 'نص', 'page': 1, 'printed': 5, 'sym': 0, 'verse': 0,
                'span': {(1, 5)}}
        q = {'n': 9, 'question': '', 'entries': [], 'toc': {'n': 9, 'title': 'عنوانٌ مِن الفهرس', 'page': 5},
             'blocks': {'short': [para], 'similar': [], 'question': [], 'gist': [], 'detailed': []}}
        ns = argparse.Namespace(paras=None, related=[], value='x', age_band=None,
                                items_dir=str(self.items), allow_dropped_symbols=False,
                                keep_tashkeel=False)
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            item = faq.build_item(q, ns)
        self.assertEqual(item['title_ar'], 'عنوان من الفهرس')
        self.assertIn('title_ar taken from the TOC title', err.getvalue())
        q['toc'] = None
        with self.assertRaises(SystemExit):
            faq.build_item(q, ns)

    def test_question_longer_than_title_limit_falls_back_to_the_toc_title(self):
        import argparse
        para = {'block': 'short', 'text': 'نص', 'page': 1, 'printed': 5, 'sym': 0, 'verse': 0,
                'span': {(1, 5)}}
        long_q = ' '.join(['سؤالٌ طويلٌ'] * 30)                      # > 200 characters
        q = {'n': 9, 'question': long_q, 'entries': [], 'toc': {'n': 9, 'title': 'عنوانٌ مِن الفهرس', 'page': 5},
             'blocks': {'short': [para], 'similar': [], 'question': [], 'gist': [], 'detailed': []}}
        ns = argparse.Namespace(paras=None, related=[], value='x', age_band=None,
                                items_dir=str(self.items), allow_dropped_symbols=False,
                                keep_tashkeel=False)
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            item = faq.build_item(q, ns)
        self.assertEqual(item['title_ar'], 'عنوان من الفهرس')
        self.assertIn(f'title_ar allows {faq.TITLE_MAX}', err.getvalue())
        q['toc'] = None
        with self.assertRaises(SystemExit) as cm:
            faq.build_item(q, ns)
        self.assertIn('cannot be drafted', str(cm.exception))
        q['question'] = 'سؤال قصير'                                   # within the limit: kept
        self.assertEqual(faq.build_item(q, ns)['title_ar'], 'سؤال قصير')

    def test_verse_hole_or_honorific_in_the_question_falls_back_to_the_toc_title(self):
        import argparse
        para = {'block': 'short', 'text': 'نص', 'page': 1, 'printed': 5, 'sym': 0, 'verse': 0,
                'span': {(1, 5)}}
        sim = [{'block': 'similar', 'text': 'صيغة', 'page': 1, 'printed': 5, 'sym': 0, 'verse': 0, 'span': {(1, 5)}},
               {'block': 'similar', 'text': 'صيغة ﴿ ' + faq.VERSE_HOLE + '﴾ [يس: 40]', 'page': 1,
                'printed': 5, 'sym': 0, 'verse': 1, 'span': {(1, 5)}}]
        qp = {'block': 'question', 'text': 'سؤال ﴿ ' + faq.VERSE_HOLE + '﴾', 'page': 1, 'printed': 5,
              'sym': 0, 'verse': 1, 'span': {(1, 5)}}
        q = {'n': 9, 'question': qp['text'], 'entries': [], 'toc': {'n': 9, 'title': 'عنوان الفهرس', 'page': 5},
             'blocks': {'short': [para], 'similar': sim, 'question': [qp], 'gist': [], 'detailed': []}}
        ns = argparse.Namespace(paras=None, related=[], value='x', age_band=None,
                                items_dir=str(self.items), allow_dropped_symbols=False,
                                keep_tashkeel=False)
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            item = faq.build_item(q, ns)
        self.assertEqual((item['title_ar'], item['keywords_ar']), ('عنوان الفهرس', ['صيغة']))
        self.assertIn('title_ar taken from the TOC title', err.getvalue())
        self.assertIn('1 similar wording(s) with a verse hole', err.getvalue())
        # a dropped honorific in the question or a similar wording is guarded like the answer
        qp['text'], qp['verse'], qp['sym'] = 'سؤال', 0, 1
        q['question'] = 'سؤال'
        with self.assertRaises(SystemExit) as cm:
            faq.build_item(q, ns)
        self.assertIn('--allow-dropped-symbols', str(cm.exception))
        self.assertEqual(faq.build_item(q, argparse.Namespace(**{**vars(ns), 'allow_dropped_symbols': True}))['title_ar'],
                         'عنوان الفهرس')
        qp['sym'], sim[0]['sym'] = 0, 1
        with self.assertRaises(SystemExit):
            faq.build_item(q, ns)
        q['toc'] = None
        sim[0]['sym'] = 0
        self.assertEqual(faq.build_item(q, ns)['title_ar'], 'سؤال')

    def test_glyphs_diagnostics_runs(self):
        out, _ = self.cli('glyphs', '2')
        self.assertIn('printed page: 5', out)
        self.assertIn(Path(FONT).stem.replace(' ', ''), out)   # DejaVuSans / ArialUnicode(MS)
        self.assertIn('digit glyphs', out)


class Hardening(unittest.TestCase):
    """Brace verses, quoted prophetic speech, and the الإجماع false positive (synthetic text)."""
    LINE = 'جملة تجريبية أولى بلا اقتباس. جملة ثانية فيها {كلمات تجريبية} وبعدها نص.'

    def test_brace_verse_refused_in_cut_but_clean_sentence_passes(self):
        with tempfile.TemporaryDirectory() as d:
            f = write(d, 'h.md', history_page().replace('نص تاريخي تجريبي أول', self.LINE))
            _, _, _, body = dfp.clean_page(dfp.load_page(f))
            n = next(l.num for l in body if l.text == self.LINE)
            out, _ = run(dfp.main, 'draft', f, '--type', 'sirah', '--value', 'x',
                         '--lines', str(n), '--sentences', '1')
            self.assertEqual(json.loads(out)[0]['arabic_text'], 'جملة تجريبية أولى بلا اقتباس.')
            for extra in ((), ('--allow-inline-verse',)):
                with self.assertRaises(SystemExit) as cm:
                    run(dfp.main, 'draft', f, '--type', 'sirah', '--value', 'x',
                        '--lines', str(n), '--sentences', '1-2', *extra)
                self.assertIn('quotes Quran inline', str(cm.exception))

    def test_braces_without_arabic_letters_are_not_a_verse(self):
        dfp.check_inline_verse('نص {1} و {} تجريبي')

    def warnings(self, text):
        w = io.StringIO()
        with contextlib.redirect_stderr(w):
            dfp.screen_excerpt(text)
        return w.getvalue()

    def test_prophetic_speech_warning(self):
        for text in ('فقال: "كلمات تجريبية"', 'يقول « كلمات تجريبية', 'قال (كلمات تجريبية)',
                     'عن رسول الله صلى الله عليه وسلم قال: «كلمات تجريبية»',
                     'قال الن\u064eّبي صلى الله عليه وسلم: "كلمات تجريبية"'):
            self.assertIn('possible quoted prophetic speech', self.warnings(text), text)
        for text in ('وصلى النبي صلى الله عليه وسلم بالناس في المسجد.', 'قال شخص تجريبي كلاما طويلا بلا اقتباس هنا'):
            self.assertNotIn('prophetic speech', self.warnings(text), text)

    def test_ijma_is_not_jima(self):
        for text in ('نقل الإجماع', 'نقل الاجماع', 'وفيه إجماع', 'اجماع', 'وبالإجماع', 'للإجماع'):
            self.assertNotIn('marriage_relations', {c for c, _ in dfp.age_screen(text)}, text)
        for text in ('جماع', 'الجماع', 'وجماع'):
            self.assertIn('marriage_relations', {c for c, _ in dfp.age_screen(text)}, text)


if __name__ == '__main__':
    unittest.main()
