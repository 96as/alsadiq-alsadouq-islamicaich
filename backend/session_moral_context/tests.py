import json
import shutil
import subprocess
import sys
import tempfile
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import RequestFactory, SimpleTestCase, TestCase
from django.urls import reverse

from .models import ContentItem, IslamicReference, MoralContext, MoralTheme, Value
from .utils.arabic import normalize_ar
from .utils.review import item_hash


class NormalizeArTests(SimpleTestCase):
    def test_cases(self):
        self.assertEqual(normalize_ar('الصِّدْقُ'), 'الصدق')
        self.assertEqual(normalize_ar('كـــذب'), 'كذب')
        self.assertEqual(normalize_ar('أإآ'), 'ااا')
        self.assertEqual(normalize_ar('هدى'), 'هدي')
        self.assertEqual(normalize_ar('رحمة'), 'رحمه')
        self.assertEqual(normalize_ar('  a \n  b  '), 'a b')
        self.assertEqual(normalize_ar(None), '')
        self.assertEqual(normalize_ar(''), '')

    def test_extended_marks_and_alef_wasla(self):
        s = '\u0671' + '\u0644\u0635' + '\u06e1' + '\u0653' + '\u06d6'
        self.assertEqual(normalize_ar(s), '\u0627\u0644\u0635')


class CleanTests(TestCase):
    def test_hadith_seeded_without_grade(self):
        item = ContentItem(type='hadith', book='TEST-BOOK', number='1', grader='x',
                           source_url='https://dorar.net/x', source_site='dorar.net',
                           verification_status='seeded')
        with self.assertRaises(ValidationError) as cm:
            item.full_clean()
        self.assertIn('grade', cm.exception.message_dict)

    def test_verse_seeded_with_dorar(self):
        item = ContentItem(type='verse', surah=1, ayah=1, arabic_text='TEST-AR نص',
                           source_site='dorar.net', verification_status='seeded')
        with self.assertRaises(ValidationError) as cm:
            item.full_clean()
        self.assertIn('source_site', cm.exception.message_dict)

    def test_blank_hadith_unverified_do_not_collide(self):
        for t in ('A', 'B'):
            item = ContentItem(type='hadith', english_text=t)
            item.full_clean()
            item.validate_constraints()
            item.save()
        self.assertEqual(ContentItem.objects.count(), 2)

    def test_hadith_wrong_site(self):
        item = ContentItem(type='hadith', book='B', number='1', grade='g', grader='x',
                           source_url='https://dawa.center/x', source_site='dawa.center',
                           verification_status='seeded')
        with self.assertRaises(ValidationError) as cm:
            item.full_clean()
        self.assertIn('source_site', cm.exception.message_dict)

    def test_source_url_host_and_required(self):
        base = dict(type='faq', source_site='dawa.center', arabic_text='نص تجريبي',
                    verification_status='seeded')
        ContentItem(**base, source_url='https://www.dawa.center/x').full_clean()
        for url in ('https://evil.com/x', ''):
            with self.assertRaises(ValidationError) as cm:
                ContentItem(**base, source_url=url).full_clean()
            self.assertIn('source_url', cm.exception.message_dict)

    def test_surah_range_and_keywords_type(self):
        with self.assertRaises(ValidationError) as cm:
            ContentItem(type='verse', surah=115, ayah=0).full_clean()
        self.assertIn('surah', cm.exception.message_dict)
        self.assertIn('ayah', cm.exception.message_dict)
        with self.assertRaises(ValidationError):
            Value(slug='x', name_ar='a', name_en='a', keywords_en='oops').full_clean()

    def test_verse_unverified_ok(self):
        ContentItem(type='verse').full_clean()

    def test_seeded_without_source_site(self):
        with self.assertRaises(ValidationError) as cm:
            ContentItem(type='faq', verification_status='seeded').full_clean()
        self.assertIn('source_site', cm.exception.message_dict)

    def test_search_text_norm(self):
        item = ContentItem.objects.create(
            type='faq', arabic_text='TEST-AR نَصٌّ', english_text='Test English')
        self.assertEqual(item.search_text_norm, 'test-ar نص test english')
        v = Value.objects.create(slug='t', name_ar='ت', name_en='T', keywords_en=['KW'])
        item.values.add(v, through_defaults={'order': 0})
        item.save()
        self.assertIn('kw', item.search_text_norm)


class SeedContentTests(TestCase):
    VALUE = {'slug': 'test-value', 'name_ar': 'TEST-AR', 'name_en': 'Test',
             'keywords_en': ['testkw'], 'order': 1}
    GOOD = {'type': 'hadith', 'values': ['test-value'], 'arabic_text': 'TEST-AR نص',
            'english_text': 'test english', 'book': 'TEST-BOOK', 'number': '1',
            'translation_name': 'TEST-TRANSLATION', 'grade': 'صحيح', 'grader': 'TEST-GRADER', 'source_site': 'dorar.net',
            'source_url': 'https://dorar.net/test/1', 'verification_status': 'seeded'}
    BAD = {**GOOD, 'number': '2', 'grade': ''}

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)
        (self.dir / 'items').mkdir()
        (self.dir / 'values.json').write_text(json.dumps([self.VALUE]))
        self.write([self.GOOD, self.BAD])

    def write(self, items):
        (self.dir / 'items' / 'a.json').write_text(json.dumps(items))

    def run_seed(self, *args):
        out = StringIO()
        call_command('seed_content', '--dir', str(self.dir), *args, stdout=out)
        return out.getvalue()

    def test_seed_rejects_bad_keeps_good_and_is_idempotent(self):
        out = self.run_seed()
        self.assertIn('rejected 1', out)
        self.assertIn('a.json:1', out)
        self.assertEqual(ContentItem.objects.count(), 1)
        item = ContentItem.objects.get()
        self.assertEqual(item.values.get().slug, 'test-value')
        self.assertIn('testkw', item.search_text_norm)
        out = self.run_seed()
        self.assertIn('created 0', out)
        self.assertIn('updated 0', out)
        self.assertEqual(ContentItem.objects.count(), 1)

    def test_non_object_and_duplicates_rejected(self):
        self.write(['junk', self.GOOD, self.GOOD, {**self.GOOD, 'number': '3', 'values': ['test-value'] * 2}])
        out = self.run_seed()
        self.assertIn('rejected 3', out)
        self.assertIn('duplicate natural key, first at a.json:1', out)
        self.assertEqual(ContentItem.objects.count(), 1)

    def test_dry_run(self):
        self.run_seed('--dry-run')
        self.assertEqual(ContentItem.objects.count(), 0)
        self.assertEqual(Value.objects.count(), 0)

    def test_unknown_key_and_slug_rejected(self):
        self.write([{**self.GOOD, 'typo': 1}, {**self.GOOD, 'values': ['nope']}])
        self.assertIn('rejected 2', self.run_seed())

    def test_extractor_placeholder_rejected(self):
        self.write([{**self.GOOD, 'title_ar': 'سؤال ⟦VERSE_HOLE⟧'}])
        out = self.run_seed()
        self.assertIn('rejected 1', out)
        self.assertIn('placeholder', out)
        self.assertEqual(ContentItem.objects.count(), 0)

    def test_existing_reviewed_kept_if_unchanged_else_downgraded(self):
        self.write([self.GOOD])
        self.run_seed()
        ContentItem.objects.update(verification_status='reviewed')
        self.assertIn('skipped (reviewed) 1', self.run_seed())
        self.assertEqual(ContentItem.objects.get().verification_status, 'reviewed')
        self.write([{**self.GOOD, 'english_text': 'changed'}])
        out = self.run_seed()
        self.assertIn('skipped (reviewed) 0', out)
        item = ContentItem.objects.get()
        self.assertEqual(item.english_text, 'changed')
        self.assertEqual(item.verification_status, 'seeded')

    def test_new_explanation_fields_in_search_text(self):
        self.write([{**self.GOOD, 'child_explanation_older_ar': 'TESTOLDAR',
                     'child_explanation_older_en': 'OlderEn', 'girls_note_ar': 'TESTGIRLAR',
                     'girls_note_en': 'GirlsEn'}])
        self.run_seed()
        t = ContentItem.objects.get().search_text_norm
        for w in ('olderen', 'girlsen', normalize_ar('TESTOLDAR').lower(),
                  normalize_ar('TESTGIRLAR').lower()):
            self.assertIn(w, t)

    def ledger(self, entries):
        (self.dir / 'reviewed.json').write_text(json.dumps(entries))

    def entry(self, item, **kw):
        return {'key': 'hadith:TEST-BOOK:1', 'sha256': item_hash(item),
                'by': 'Nobody', 'at': '2026-10-04', **kw}

    def reviewed(self, item, by='Nobody'):
        return {**item, 'verification_status': 'reviewed', 'reviewed_by': by,
                'reviewed_at': '2026-10-04'}

    def test_file_reviewed_and_ledger_match_marks_reviewed(self):
        item = self.reviewed(self.GOOD)
        self.write([item])
        self.ledger([self.entry(item)])
        out = self.run_seed()
        self.assertIn('reviewed 1', out)
        self.assertNotIn('STALE', out)
        row = ContentItem.objects.get()
        self.assertEqual(row.verification_status, 'reviewed')
        self.assertEqual(row.reviewed_at.date().isoformat(), '2026-10-04')
        self.assertIsNone(row.reviewed_by)  # no such user
        user = get_user_model().objects.create(username='Nobody')
        self.run_seed()
        self.assertEqual(ContentItem.objects.get().reviewed_by, user)

    def test_file_reviewed_but_content_edited_is_seeded_and_stale(self):
        self.ledger([self.entry(self.GOOD)])
        self.write([self.reviewed({**self.GOOD, 'english_text': 'edited'})])
        out = self.run_seed()
        self.assertIn('STALE REVIEW hadith:TEST-BOOK:1 - file says reviewed but content changed', out)
        row = ContentItem.objects.get()
        self.assertEqual(row.verification_status, 'seeded')
        self.assertIsNone(row.reviewed_at)

    def test_file_reviewed_without_ledger_is_seeded(self):
        self.write([self.reviewed(self.GOOD)])
        self.assertIn('STALE REVIEW', self.run_seed())
        self.assertEqual(ContentItem.objects.get().verification_status, 'seeded')

    def test_ledger_match_file_seeded_promotes_with_note(self):
        self.write([self.GOOD])
        self.ledger([self.entry(self.GOOD)])
        out = self.run_seed()
        self.assertIn('NOTE hadith:TEST-BOOK:1 reviewed in ledger; run mark_reviewed', out)
        self.assertEqual(ContentItem.objects.get().verification_status, 'reviewed')

    def test_bad_reviewed_at_rejected(self):
        self.write([{**self.GOOD, 'reviewed_at': 'yesterday'}])
        self.assertIn('rejected 1', self.run_seed())

    def test_hash_ignores_status_fields(self):
        self.assertEqual(item_hash(self.GOOD), item_hash(self.reviewed(self.GOOD)))
        self.assertEqual(item_hash(self.GOOD),
                         item_hash({k: v for k, v in self.GOOD.items() if k != 'verification_status'}))
        self.assertNotEqual(item_hash(self.GOOD), item_hash({**self.GOOD, 'english_text': 'x'}))

    def test_mark_reviewed_writes_file_and_check(self):
        root = self.dir / 'pkg'
        (root / 'content' / 'tools').mkdir(parents=True)
        (root / 'utils').mkdir()
        here = Path(__file__).resolve().parent
        shutil.copy(here / 'content' / 'tools' / 'mark_reviewed.py', root / 'content' / 'tools')
        shutil.copy(here / 'utils' / 'review.py', root / 'utils')
        (root / 'content' / 'items').mkdir()
        (root / 'content' / 'reviewed.json').write_text('[]')
        itemfile = root / 'content' / 'items' / 'a.json'
        itemfile.write_text(json.dumps([self.GOOD]))
        tool = str(root / 'content' / 'tools' / 'mark_reviewed.py')

        def run(*args):
            return subprocess.run([sys.executable, tool, *args], capture_output=True, text=True)

        self.assertEqual(run('--check').returncode, 0)
        r = run('--by', 'Tester', '--at', '2026-10-04', 'test-value')
        self.assertEqual(r.returncode, 0, r.stderr)
        item = json.loads(itemfile.read_text())[0]
        self.assertEqual(
            (item['verification_status'], item['reviewed_by'], item['reviewed_at']),
            ('reviewed', 'Tester', '2026-10-04'))
        keys = list(item)
        self.assertEqual(keys[keys.index('verification_status') + 1:], ['reviewed_by', 'reviewed_at'])
        ledger = json.loads((root / 'content' / 'reviewed.json').read_text())
        self.assertEqual(ledger[0]['sha256'], item_hash(self.GOOD))
        self.assertEqual(run('--check').returncode, 0)
        item['english_text'] = 'edited'
        itemfile.write_text(json.dumps([item]))
        r = run('--check')
        self.assertEqual(r.returncode, 1)
        self.assertIn('hadith:TEST-BOOK:1', r.stdout)
        self.assertEqual(run('--list-stale').returncode, 1)

    def test_ledger_unknown_key_reported(self):
        self.write([self.GOOD])
        self.ledger([self.entry(self.GOOD, key='hadith:NOPE:9')])
        self.assertIn('UNKNOWN REVIEW KEY hadith:NOPE:9', self.run_seed())

    def items(self):
        a = {'type': 'verse', 'surah': 1, 'ayah': 1, 'arabic_text': 'نص تجريبي',
             'source_site': 'quranpedia.net', 'source_url': 'https://quranpedia.net/1/1',
             'verification_status': 'seeded', 'values': ['test-value']}
        t = {'type': 'tafsir', 'arabic_text': 'نص تجريبي', 'source_site': 'dorar.net',
             'source_url': 'https://dorar.net/t', 'verification_status': 'seeded',
             'values': ['test-value'], 'related': ['verse:1:1', 'hadith:TEST-BOOK:1']}
        return a, t

    def test_related_and_level_defaults(self):
        a, t = self.items()
        self.write([a, t, self.GOOD])
        out = self.run_seed()
        self.assertIn('rejected 0', out)
        tafsir = ContentItem.objects.get(type='tafsir')
        self.assertEqual(tafsir.content_level, 'B')
        self.assertEqual(ContentItem.objects.get(type='verse').content_level, 'A')
        self.assertEqual({i.type for i in tafsir.related.all()}, {'verse', 'hadith'})
        self.assertEqual(ContentItem.objects.get(type='verse').cited_by.get(), tafsir)

    def test_rejected_item_does_not_rewrite_related(self):
        a, t = self.items()
        self.write([a, t, self.GOOD])
        self.run_seed()
        bad = {**t, 'related': ['verse:1:1'], 'arabic_text': ''}
        self.write([a, bad, self.GOOD])
        self.assertIn('rejected 1', self.run_seed())
        self.assertEqual(ContentItem.objects.get(type='tafsir').related.count(), 2)

    def test_related_edit_downgrades_reviewed_row(self):
        a, t = self.items()
        self.write([a, t, self.GOOD])
        self.run_seed()
        ContentItem.objects.filter(type='tafsir').update(verification_status='reviewed')
        self.write([a, {**t, 'related': ['verse:1:1']}, self.GOOD])
        out = self.run_seed()
        self.assertIn('skipped (reviewed) 0', out)
        self.assertEqual(ContentItem.objects.get(type='tafsir').verification_status, 'seeded')

    def test_related_unknown_label_rejected(self):
        a, t = self.items()
        t['related'] = ['verse:9:9']
        self.write([a, t])
        out = self.run_seed()
        self.assertIn('rejected 1', out)
        self.assertIn('unknown label', out)
        self.assertEqual(ContentItem.objects.get(type='tafsir').related.count(), 0)


def seeded(**kw):
    base = dict(type='faq', arabic_text='نص تجريبي', source_site='dawa.center',
                source_url='https://dawa.center/x', verification_status='seeded')
    return ContentItem(**{**base, **kw})


def errors_of(item):
    try:
        item.full_clean()
    except ValidationError as e:
        return e.message_dict
    return {}


class SchemaRuleTests(TestCase):
    def test_site_matrix(self):
        ok = {'verse': 'quranpedia.net', 'tafsir': 'shamela.ws', 'aqidah': 'dorar.net',
              'fiqh': 'dorar.net', 'sirah': 'shamela.ws', 'faq': 'dawa.center',
              'term': 'islamic-content.com'}
        for t, site in ok.items():
            extra = {'surah': 1, 'ayah': 1} if t == 'verse' else {}
            item = seeded(type=t, source_site=site, source_url=f'https://{site}/x', **extra)
            self.assertEqual(errors_of(item), {}, t)
        self.assertEqual(errors_of(seeded(
            type='story', arabic_text='', source_site='quranpedia.net',
            source_url='https://quranpedia.net/s')), {})
        self.assertIn('source_site', errors_of(seeded(
            type='term', source_site='dawa.center')))
        self.assertIn('source_site', errors_of(seeded(
            type='tafsir', source_site='dawa.center')))

    def test_pending_sites_rejected_for_every_type(self):
        for site in ('hadeethenc.com', 'quranenc.com', 'islamenc.com', 'terminologyenc.com'):
            for t in ('verse', 'hadith', 'tafsir', 'faq', 'term', 'story', 'fiqh'):
                item = seeded(type=t, source_site=site, source_url=f'https://{site}/x')
                self.assertIn('source_site', errors_of(item), (site, t))

    def test_mp3quran_is_a_choice_but_not_a_text_source(self):
        self.assertIn('source_site', errors_of(seeded(
            source_site='mp3quran.net', source_url='https://mp3quran.net/x')))

    def hadith(self, **kw):
        base = dict(type='hadith', book='B', number='1', grade='صحيح', grader='x',
                    source_site='dorar.net', source_url='https://dorar.net/x')
        return seeded(**{**base, **kw})

    def test_hadith_grade_and_text(self):
        self.assertEqual(errors_of(self.hadith()), {})
        self.assertEqual(errors_of(self.hadith(grade='[ صحيح ]')), {})
        self.assertIn('grade', errors_of(self.hadith(grade='حسن')))
        self.assertIn('arabic_text', errors_of(self.hadith(arabic_text='')))

    def test_english_requires_translation_name(self):
        self.assertIn('translation_name', errors_of(seeded(english_text='x')))
        self.assertEqual(errors_of(seeded(english_text='x', translation_name='T')), {})

    def test_arabic_text_rules(self):
        self.assertIn('arabic_text', errors_of(seeded(arabic_text='')))
        self.assertIn('arabic_text', errors_of(seeded(
            type='story', source_site='quranpedia.net', source_url='https://quranpedia.net/s')))

    def test_level_c_needs_note(self):
        self.assertIn('disagreement_note_ar', errors_of(seeded(content_level='C')))
        self.assertEqual(errors_of(seeded(content_level='C', disagreement_note_en='n')), {})

    def test_unverified_is_unconstrained(self):
        self.assertEqual(errors_of(ContentItem(type='hadith', content_level='A')), {})

    def test_bracketed_grade_normalised_and_servable(self):
        h = self.hadith(grade='[صحيح]', verification_status='reviewed')
        h.full_clean()
        h.save()
        h.refresh_from_db()
        self.assertEqual(h.grade, 'صحيح')
        self.assertIn(h, ContentItem.objects.servable())

    def test_servable(self):
        def mk(t, status, **kw):
            return ContentItem.objects.create(
                type=t, verification_status=status, english_text=f'{t}{status}{kw}', **kw)
        v1 = mk('verse', 'seeded', surah=1, ayah=1)
        v2 = mk('verse', 'unverified', surah=1, ayah=2)
        f1 = mk('faq', 'seeded')
        f2 = mk('faq', 'reviewed')
        h1 = mk('hadith', 'reviewed', grade='صحيح')
        h2 = mk('hadith', 'reviewed', grade='حسن')
        h3 = mk('hadith', 'seeded', grade='صحيح')
        got = set(ContentItem.objects.servable())
        self.assertEqual(got, {v1, f2, h1})
        self.assertFalse({v2, f1, h2, h3} & got)

    def test_search_uses_arabic_text_search_for_verses(self):
        v = ContentItem.objects.create(
            type='verse', surah=1, ayah=1, arabic_text='ٱلْكلمة', arabic_text_search='بحثية',
            title_en='TitleX', keywords_ar=['مفتاح'], keywords_en=['kwx'])
        self.assertIn('بحثيه', v.search_text_norm)
        self.assertNotIn('الكلمه', v.search_text_norm)
        for w in ('titlex', 'مفتاح', 'kwx'):
            self.assertIn(w, v.search_text_norm)
        h = ContentItem.objects.create(type='hadith', arabic_text='نصحديث', arabic_text_search='ignored')
        self.assertIn('نصحديث', h.search_text_norm)

    def test_normalize_08f0_08f2(self):
        self.assertEqual(normalize_ar('ب\u08f0\u08f1\u08f2ت'), 'بت')

    def test_legacy_references_unverified_by_default(self):
        r = IslamicReference.objects.create(reference_type='hadith', text='x')
        self.assertFalse(r.is_verified)


class RealContentTests(TestCase):
    def test_dry_run_on_real_content_has_no_rejections(self):
        out = StringIO()
        call_command('seed_content', '--dry-run', stdout=out)
        self.assertIn('rejected 0', out.getvalue())


class LegacyImportTests(TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.fixture = Path(directory.name) / 'synthetic.json'
        self.fixture.write_text(json.dumps([{
            'theme': 'Synthetic theme',
            'references': [
                {'type': kind, 'text': f'SYNTHETIC legacy {kind}',
                 'source': 'Synthetic source', 'is_verified': True}
                for kind in ('hadith', 'quran')
            ],
        }]))

    def run_legacy(self):
        err = StringIO()
        call_command('seed_islamic_knowledge', '--legacy-i-know',
                     '--fixture', str(self.fixture), stdout=StringIO(), stderr=err)
        return err.getvalue()

    def test_default_refuses_before_fixture_access_or_database_queries(self):
        from .management.commands.seed_islamic_knowledge import Command

        with patch('session_moral_context.management.commands.seed_islamic_knowledge.open', create=True) as opened, \
                patch('session_moral_context.management.commands.seed_islamic_knowledge.os.path.exists') as exists:
            with self.assertNumQueries(0), self.assertRaisesMessage(CommandError, 'Use seed_content'):
                Command().handle(fixture=str(self.fixture), legacy_i_know=False)
        opened.assert_not_called()
        exists.assert_not_called()
        self.assertFalse(MoralTheme.objects.exists())
        self.assertFalse(IslamicReference.objects.exists())

    def test_explicit_override_is_idempotent_and_never_verifies_fixture(self):
        self.assertIn('remain unverified', self.run_legacy())
        self.run_legacy()
        self.assertEqual(MoralTheme.objects.count(), 1)
        self.assertEqual(IslamicReference.objects.count(), 2)
        self.assertFalse(IslamicReference.objects.filter(is_verified=True).exists())
        self.assertEqual(MoralTheme.objects.get().references.count(), 2)

    def test_override_downgrades_existing_verified_match_with_warning(self):
        reference = IslamicReference.objects.create(
            reference_type='hadith', text='SYNTHETIC legacy hadith', is_verified=True)
        self.assertIn(f'Legacy reference {reference.pk} downgraded to unverified', self.run_legacy())
        reference.refresh_from_db()
        self.assertFalse(reference.is_verified)
        self.assertEqual(reference.source, 'Synthetic source')
        self.run_legacy()
        self.assertEqual(IslamicReference.objects.count(), 2)

    def test_help_marks_legacy_and_directs_to_current_bank(self):
        from .management.commands.seed_islamic_knowledge import Command
        parser = Command().create_parser('manage.py', 'seed_islamic_knowledge')
        self.assertFalse(parser.parse_args([]).legacy_i_know)
        help_text = parser.format_help()
        self.assertIn('Legacy', help_text)
        self.assertIn('--legacy-i-know', help_text)
        self.assertIn('seed_content', help_text)


class LegacyAdminTests(TestCase):
    def setUp(self):
        from authentication.models import ChildProfile
        from conversation.models import Message, Session

        self.user = get_user_model().objects.create_superuser(
            username='legacy_admin', password='x', email='legacy@example.com')
        child_user = get_user_model().objects.create_user(username='legacy_child', is_child=True)
        child = ChildProfile.objects.create(
            user=child_user, nickname='Synthetic', gender='male', birth_year=2015)
        session = Session.objects.create(child=child, livekit_room_name='legacy_admin_test')
        message = Message.objects.create(session=session, sender='child', content='SYNTHETIC text')
        self.objects = [
            MoralTheme.objects.create(name='Synthetic theme'),
            IslamicReference.objects.create(reference_type='hadith', text='SYNTHETIC legacy reference'),
            MoralContext.objects.create(message=message),
        ]

    def test_all_three_admins_allow_view_only_even_for_superuser(self):
        request = RequestFactory().get('/')
        request.user = self.user
        for obj in self.objects:
            with self.subTest(model=obj._meta.model_name):
                model_admin = admin.site._registry[type(obj)]
                self.assertFalse(model_admin.has_add_permission(request))
                for instance in (None, obj):
                    self.assertTrue(model_admin.has_view_permission(request, instance))
                    self.assertFalse(model_admin.has_change_permission(request, instance))
                    self.assertFalse(model_admin.has_delete_permission(request, instance))

    def test_admin_pages_are_viewable_but_all_write_routes_are_denied(self):
        self.client.force_login(self.user)
        for obj in self.objects:
            with self.subTest(model=obj._meta.model_name):
                prefix = f'admin:session_moral_context_{obj._meta.model_name}'
                change = reverse(f'{prefix}_change', args=[obj.pk])
                self.assertEqual(self.client.get(change).status_code, 200)
                self.assertEqual(self.client.post(change, {}).status_code, 403)
                self.assertEqual(self.client.get(reverse(f'{prefix}_add')).status_code, 403)
                self.assertEqual(self.client.post(reverse(f'{prefix}_delete', args=[obj.pk])).status_code, 403)
                self.assertTrue(type(obj).objects.filter(pk=obj.pk).exists())
