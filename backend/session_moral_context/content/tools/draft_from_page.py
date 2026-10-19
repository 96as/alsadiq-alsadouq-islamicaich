#!/usr/bin/env python3
"""Turn a human-saved source page into a draft knowledge-bank item.

Pages are saved by the lead (or Cowork) in a normal browser; this tool never fetches
anything. A saved page is a text/markdown file whose first lines are
`Source URL: <url>` and `Retrieved: YYYY-MM-DD` (an .html file with
`<!-- Source URL: ... -->` / `<!-- Retrieved: ... -->` comments also works, best effort).
Saved pages are copyrighted source material: keep them in the gitignored tools/.cache/.

Supported pages (kind is detected from the URL):
  dorar.net/tafseer/<surah>/<n>          -> tafsir
  dorar.net/aqeeda/<id>                  -> aqidah
  dorar.net/feqhia/<id>                  -> fiqh
  dorar.net/history/event/<id>           -> sirah
  islamic-content.com/dictionary/word/<id>[/<lang>]  -> term (Al-Jamhara)

Usage:
  python3 draft_from_page.py show FILE [--max-chars N] [--sentences N]
      Print the page body (site chrome stripped) as numbered lines. Flags: H heading,
      S known section heading (e.g. المعنى الإجمالي), FN line carries a footnote marker
      [n], fn line looks like a footnote body (ends with " ."). The numbers are the ones
      `draft --lines` uses. --sentences N prints cleaned line N split into numbered
      sentences (see split_sentences for the rule), for `draft --sentences`.

  python3 draft_from_page.py draft FILE --type tafsir|aqidah|fiqh|sirah|term --value SLUG
        [--lines A-B] [--sentences A-B] [--en-lines C-D] [--verses S:A-B] [--title-ar T] [--title-en T]
        [--related verse:S:A ...] [--level A|B|C] [--disagreement-ar T]
        [--disagreement-en T] [--age-band all|6-9|10-13] [--keywords-ar a,b]
        [--keywords-en a,b] [--fragment F] [--strip-footnotes]
        [--allow-inline-verse] [--out FILE.json]
      Write a draft item (JSON list with one item) to stdout, or merge it into --out
      (a JSON list; an entry with the same type + source_url is replaced).
      arabic_text is exactly the selected contiguous lines joined by newlines. With a
      single --lines N, --sentences A-B takes sentences A..B of that line instead (a page
      whose whole event is one line can then be cut to its first sentences); the cut is
      asserted to be an exact substring of the saved page and goes through the same
      inline-verse and age-screen checks. Footnote
      markers stay unless --strip-footnotes (only the "[n]" marker goes; footnote text on
      the same line stays, so check it). verification_status is always "unverified".
      tafsir needs --verses (number "S:A-B"); term takes the title, the English
      equivalent and the definitions from the page (--lines / --en-lines override the
      automatic pick). Warnings (age screen incl. English, hadith quote marks, missing
      English title, bank verses) go to stderr. An excerpt that quotes Quran inline (﴿ ﴾, {...} around
      Arabic, or a [surah: ayah] reference) is refused unless every reference is given with
      --related verse:S:A and --allow-inline-verse is passed.

Nothing here contains scripture or source text; titles and excerpts come from the page.
"""
import argparse
import json
import re
import sys
import unicodedata
from html.parser import HTMLParser
from pathlib import Path

ITEMS_DIR = Path(__file__).resolve().parent.parent / 'items'

# kind -> (item type, canonical book name)
KINDS = {
    'tafsir': 'موسوعة التفسير - الدرر السنية',
    'aqidah': 'الموسوعة العقدية - الدرر السنية',
    'fiqh': 'الموسوعة الفقهية - الدرر السنية',
    'sirah': 'الموسوعة التاريخية - الدرر السنية',
    'term': 'Al-Jamhara Islamic Dictionary',
}
DEFAULT_LEVEL = {'tafsir': 'B', 'faq': 'B', 'fiqh': 'B', 'aqidah': 'A', 'sirah': 'A', 'term': 'A'}
TERM_TRANSLATION_NAME = 'Al-Jamhara (en)'

URL_PATTERNS = [
    ('tafsir', 'dorar.net', re.compile(r'^/tafseer/(?P<surah>\d+)(?:/(?P<n>\d+))?(?:/|$)')),
    ('aqidah', 'dorar.net', re.compile(r'^/aqeeda/(?P<id>\d+)(?:/|$)')),
    ('fiqh', 'dorar.net', re.compile(r'^/feqhia/(?P<id>\d+)(?:/|$)')),
    ('sirah', 'dorar.net', re.compile(r'^/history/event/(?P<id>\d+)(?:/|$)')),
    ('term', 'islamic-content.com',
     re.compile(r'^/(?:[a-z]{2}/)?dictionary/word/(?P<id>\d+)(?:/(?P<lang>[A-Za-z-]+))?/?$')),
]

# Deny-list screen (plan section 4.3 / 6): topics a child excerpt should not carry unchecked.
# Arabic stems are normalised with normalize_ar below. A token matches (after dropping one
# prefix letter, "ال" and a verb prefix) when it equals the stem, or starts with a stem of
# 4+ letters, or is a 3-letter stem plus a common suffix (قتل -> قتلوا, يقتل, قتلى).
# It only warns; the lead decides. TONE_CATS are not age topics: they only ask the drafter to
# explain hope-first for 6-9.
_DENY_RAW = {
    'jihad': ['جهاد', 'قتال', 'سيف', 'غزوه', 'غزوات', 'فتوحات'],
    'punishment': ['عقوبه', 'عقوبات', 'حدود', 'قصاص', 'رجم', 'جلد', 'قطع', 'تعزير', 'صلب'],
    'crime': ['زنا', 'سرقه', 'قتل', 'رده', 'مرتد', 'ارتداد', 'خمر', 'ربا', 'انتحار', 'ذبح',
              'ذبيحه'],
    'marriage_relations': ['نكاح', 'زواج', 'جماع', 'اختلاط', 'عوره', 'طلاق', 'حيض', 'نفاس',
                           'جنابه'],
    'slavery': ['رقيق', 'استرقاق', 'سبي', 'سبايا', 'عبيد', 'اماء', 'جواري'],
    # Hope first (الترغيب قبل الترهيب): simple afterlife words are a TONE flag only (no age
    # change); grave torment and punishment detail stay 10-13.
    'afterlife_mention': ['جنه', 'جهنم', 'جحيم', 'نار', 'عذاب', 'قيامه', 'اخره'],
    'afterlife_graphic': ['قبر', 'قبور', 'برزخ', 'سعير', 'زقوم', 'صديد', 'سقر', 'لظى', 'ضريع', 'غسلين', 'سلاسل',
                          'اغلال', 'نكير'],  # not منكر (= wrongdoing) or حميم (= close friend): common in values text
    'hour': ['دجال', 'ياجوج', 'ماجوج', 'اشراط', 'ساعه'],
    'sects_disbelief': ['كفر', 'كفار', 'مشركين', 'مشرك', 'خوارج', 'معتزله', 'شيعه',
                        'رافضه', 'تكفير', 'بدعه', 'زندقه'],
}
TONE_CATS = {'afterlife_mention'}
DENY_STEMS = {cat: [] for cat in _DENY_RAW}   # filled by _load_deny() once normalize_ar exists
DENY_EN = {
    'jihad': [r'jihad', r'swords?\b', r'conquest'],
    'punishment': [r'punish', r'whip', r'crucif', r'torment'],
    'crime': [r'kill', r'suicid', r'slaughter', r'adulter', r'fornicat', r'apostat'],
    'marriage_relations': [r'divorc', r'menstruat'],
    'slavery': [r'slave', r'slaver'],
    'afterlife_mention': [r'hell(?:fire)?\b', r'the fire\b', r'paradise', r'jannah',
                          r'the last day', r'day of judg', r'hereafter'],
    'afterlife_graphic': [r'grave', r'barzakh', r'zaqqum', r'scald', r'boiling', r'shackle',
                          r'chains\b', r'pus\b'],
    'sects_disbelief': [r'disbelie'],
}
STEM_SUFFIXES = {'', 'ه', 'ها', 'هم', 'وا', 'ون', 'ين', 'ان', 'ت', 'تم', 'نا', 'ا', 'ات', 'ى', 'ي'}

SECTION_HEADINGS = {
    'غريب الكلمات', 'مشكل الإعراب', 'المعنى الإجمالي', 'تفسير الآيات', 'الفوائد التربوية',
    'الفوائد العلمية واللطائف', 'بلاغة الآيات', 'الأدلة', 'وجه الدلالة',
    'المادة في سؤال وجواب', 'تفاصيل الحدث', 'الأدلة من الكتاب', 'الأدلة من السنة',
}

FOOTNOTE_MARK = re.compile(r'\[\d{1,3}\]')
VERSE_REF = re.compile(r'\[[^\]\d\s][^\]\d]*:\s*\d+(?:\s*[-–]\s*\d+)?\]')
HADITH_QUOTE = re.compile(r'\(\([^)]+\)\)')
# dorar history quotes Quran as {...} around Arabic letters
BRACE_VERSE = re.compile(r'\{[^{}]*[\u0621-\u064a][^{}]*\}')
# possible quoted prophetic speech, matched on normalize_ar(text): a speech verb then a quote
# mark within 15 chars, or the Prophet's name/salutation then a quote mark within 40 chars
SPEECH_QUOTE = re.compile(r'(?:قال|يقول)[^()"«]{0,15}[("«]'
                          r'|(?:رسول الله|النبي|صلي الله عليه وسلم)[^()"«]{0,40}[("«]')
# الإجماع (consensus) is not the deny-listed word جماع
IJMA = re.compile(r'(?:[وفبكل]|لل)?(?:ال)?اجماع')

# Page chrome (dorar). Everything before the encyclopedia title heading, and everything
# from the first end marker, is dropped; in between only the search form is dropped.
TITLE_HEADING = re.compile(r'^#\s+(?:موسوعة|الموسوعة)\s')
END_MARKERS = (
    '### انظر أيضا', '[Button: عرض الهوامش]', '[Button: غلق]', '[Input] [Input]',
    '##### انشر المادة', '##### روابط هامة', '#### لجنة الإشراف العلمي',
)
HEAD_EXACT = {
    'روابط مهمة', 'طريقة البحث', 'بحث', 'محتويات الصفحة', 'انظر أيضا', 'الرابط المختصر',
    'نــطاق البحــث:', 'نطاق البحث:', 'حفظ',
}
HEAD_PREFIX = (
    'المراجع المعتمدة', 'بحث في', 'بحث فى', 'عن الموسوعة', 'تنويه', 'ميلادي', 'التصنيف الموضوعي',
    'تصنيف رئيس', 'تصنيف فرعي', 'الحقبة الزمنية', 'ترتيب الأحداث', 'تصفح الكل', 'Image:',
    'iframe', 'طريقة البحث',
)
CONTROL_LINE = re.compile(r'^\[(?:Button|Input|Select)')

# Al-Jamhara
TERM_TITLE = re.compile(r'معنى\s*:\s*(?P<en>.+?)\s+-\s+(?P<ar>.+?)\s+-\s+الجمهرة')
TERM_FOOTER = re.compile(r'^\s*(حقوق النشر|(?:جميع )?الحقوق محفوظة|حقوق (?:الطبع|الاستفادة)|All rights reserved|©|Copyright|Privacy Policy|Terms of (?:Use|Service))', re.I)  # line start only: a definition line may contain "حقوق"
TERM_MENU = re.compile(r'^\s*[*•]\s')


def fail(msg):
    sys.exit(f'draft_from_page: {msg}')


def warn(msg):
    print(f'WARNING: {msg}', file=sys.stderr)


def normalize_ar(s):
    s = unicodedata.normalize('NFKC', s)
    s = re.sub('[\u064b-\u065f\u0670\u0640\u06d6-\u06ed]', '', s)
    for a, b in (('أ', 'ا'), ('إ', 'ا'), ('آ', 'ا'), ('ٱ', 'ا'), ('ى', 'ي'), ('ة', 'ه'),
                 ('ؤ', 'و'), ('ئ', 'ي')):
        s = s.replace(a, b)
    return s


SURAH_NAMES = [
    'الفاتحة', 'البقرة', 'آل عمران', 'النساء', 'المائدة', 'الأنعام', 'الأعراف', 'الأنفال',
    'التوبة', 'يونس', 'هود', 'يوسف', 'الرعد', 'إبراهيم', 'الحجر', 'النحل', 'الإسراء',
    'الكهف', 'مريم', 'طه', 'الأنبياء', 'الحج', 'المؤمنون', 'النور', 'الفرقان', 'الشعراء',
    'النمل', 'القصص', 'العنكبوت', 'الروم', 'لقمان', 'السجدة', 'الأحزاب', 'سبأ', 'فاطر',
    'يس', 'الصافات', 'ص', 'الزمر', 'غافر', 'فصلت', 'الشورى', 'الزخرف', 'الدخان', 'الجاثية',
    'الأحقاف', 'محمد', 'الفتح', 'الحجرات', 'ق', 'الذاريات', 'الطور', 'النجم', 'القمر',
    'الرحمن', 'الواقعة', 'الحديد', 'المجادلة', 'الحشر', 'الممتحنة', 'الصف', 'الجمعة',
    'المنافقون', 'التغابن', 'الطلاق', 'التحريم', 'الملك', 'القلم', 'الحاقة', 'المعارج',
    'نوح', 'الجن', 'المزمل', 'المدثر', 'القيامة', 'الإنسان', 'المرسلات', 'النبأ',
    'النازعات', 'عبس', 'التكوير', 'الانفطار', 'المطففين', 'الانشقاق', 'البروج', 'الطارق',
    'الأعلى', 'الغاشية', 'الفجر', 'البلد', 'الشمس', 'الليل', 'الضحى', 'الشرح', 'التين',
    'العلق', 'القدر', 'البينة', 'الزلزلة', 'العاديات', 'القارعة', 'التكاثر', 'العصر',
    'الهمزة', 'الفيل', 'قريش', 'الماعون', 'الكوثر', 'الكافرون', 'النصر', 'المسد',
    'الإخلاص', 'الفلق', 'الناس',
]
SURAH_ALIASES = {'المؤمن': 40, 'حم السجدة': 41, 'الدهر': 76, 'براءة': 9, 'بني إسرائيل': 17,
                 'الملائكة': 35, 'القتال': 47}

DIGITS_AR = str.maketrans('٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹', '01234567890123456789')


def norm(s):
    """Normalise Arabic for matching only (never for stored text)."""
    s = normalize_ar(s)
    return re.sub(r'\s+', ' ', re.sub(r'[:：،,.؟?!؛()\[\]\-–]', ' ', s)).strip()


def surah_number(name):
    n = norm(re.sub(r'^\s*سورة\s+', '', name))
    table = {norm(x): i + 1 for i, x in enumerate(SURAH_NAMES)}
    table.update({norm(k): v for k, v in SURAH_ALIASES.items()})
    return table.get(n)


def _load_deny():
    for cat, stems in _DENY_RAW.items():
        DENY_STEMS[cat] = [normalize_ar(s) for s in stems]


_load_deny()


def verse_refs(text):
    """[(surah, ayah)] for `[name: ayah]` / `[name: a-b]` references (either bracket side)."""
    found = []
    for m in re.finditer(r'[\[\]()]\s*([^\[\]():\d]+?)\s*[:：]\s*(\d+)(?:\s*[-–]\s*(\d+))?\s*[\[\]()]',
                         text.translate(DIGITS_AR)):
        s = surah_number(m.group(1))
        if not s:
            continue
        a = int(m.group(2))
        b = int(m.group(3) or a)
        if a <= b <= a + 30:
            found += [(s, k) for k in range(a, b + 1)]
    return found


# ---------------------------------------------------------------- page loading

class _HtmlText(HTMLParser):
    SKIP = {'script', 'style', 'noscript', 'svg', 'head', 'template'}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out, self.skip, self.buf, self.heading = [], 0, [], 0

    def flush(self):
        text = ' '.join(''.join(self.buf).split())
        self.buf = []
        if text:
            self.out.append(('#' * self.heading + ' ' if self.heading else '') + text)

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self.skip += 1
        elif re.fullmatch(r'h[1-6]', tag):
            self.flush()
            self.heading = int(tag[1])
        elif tag in ('p', 'div', 'br', 'li', 'tr', 'section', 'article', 'ul', 'ol'):
            self.flush()

    def handle_endtag(self, tag):
        if tag in self.SKIP:
            self.skip = max(0, self.skip - 1)
        elif re.fullmatch(r'h[1-6]', tag):
            self.flush()
            self.heading = 0
        elif tag in ('p', 'div', 'li', 'tr', 'section', 'article', 'ul', 'ol'):
            self.flush()

    def handle_data(self, data):
        if not self.skip:
            self.buf.append(data)


def html_to_lines(html):
    p = _HtmlText()
    p.feed(html)
    p.flush()
    return p.out


class Page:
    def __init__(self, url, retrieved, lines, path=None):
        self.url, self.retrieved, self.raw_lines, self.path = url, retrieved, lines, path


def load_page(path):
    path = Path(path)
    try:
        text = path.read_text(encoding='utf-8-sig')
    except OSError as e:
        fail(f'cannot read {path}: {e}')
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    url = retrieved = None
    m = re.search(r'Source URL:\s*(\S+?)\s*(?:-->|$)', text[:2000], re.M)
    if m:
        url = m.group(1)
    m = re.search(r'Retrieved:\s*(\S+?)\s*(?:-->|$)', text[:2000], re.M)
    if m:
        retrieved = m.group(1)
    if not url:
        fail(f'{path}: no "Source URL:" header in the first lines')
    if path.suffix.lower() in ('.html', '.htm') or text.lstrip().startswith(('<!', '<html', '<HTML')):
        lines = html_to_lines(text)
    else:
        lines = text.split('\n')
        # drop the two header lines (and the blank line after them) only when they lead
        i = 0
        while i < len(lines) and i < 4 and (
                lines[i].startswith(('Source URL:', 'Retrieved:')) or not lines[i].strip()):
            i += 1
        lines = lines[i:]
    return Page(url, retrieved, lines, path)


def detect_kind(url):
    """Return (kind, info dict) from the page URL, or fail."""
    from urllib.parse import urlparse
    u = urlparse(url.strip())
    host = (u.hostname or '').lower()
    if host.startswith('www.'):
        host = host[4:]
    for kind, site, rx in URL_PATTERNS:
        if host == site:
            m = rx.match(u.path)
            if m:
                return kind, {k: v for k, v in m.groupdict().items() if v is not None} | {'site': site}
    fail(f'unsupported page URL (expected dorar tafseer/aqeeda/feqhia/history or an '
         f'islamic-content.com dictionary word): {url}')


# ---------------------------------------------------------------- chrome stripping

class Line:
    def __init__(self, num, text, heading=False):
        self.num, self.text, self.heading = num, text, heading

    @property
    def flags(self):
        f = []
        if self.heading:
            f.append('H')
        if normalize_ar(self.text).strip(' :،.').strip() in {normalize_ar(s) for s in SECTION_HEADINGS}:
            f.append('S')
        if FOOTNOTE_MARK.search(self.text):
            f.append('FN')
        elif self.text.rstrip().endswith(' .'):
            f.append('fn')
        return f


def _is_head_chrome(s):
    return (not s or s == '* * *' or CONTROL_LINE.match(s) or s in HEAD_EXACT
            or s.startswith(HEAD_PREFIX) or re.fullmatch(r'#+', s))


def clean_dorar(raw):
    """Return the body of a dorar encyclopedia page as a list of Line (no blanks)."""
    lines = [l.strip() for l in raw]
    start = 0
    for i, s in enumerate(lines):
        if TITLE_HEADING.match(s):
            start = i + 1
            break
    end = len(lines)
    for i in range(start, len(lines)):
        if lines[i].startswith(END_MARKERS) or lines[i] in ('السابق', 'التالي'):
            end = i
            break
    out, in_head, seen_browse = [], True, False
    for s in lines[start:end]:
        if in_head:
            # history pages: the filter form ends at the separator after "تصفح الكل"
            if s.startswith('تصفح الكل'):
                seen_browse = True
            if seen_browse:
                if s == '* * *':
                    in_head = False
                continue
            m = re.match(r'^(#{1,6})\s+(\S.*)$', s)
            if m and not s.startswith('##### منهج'):
                in_head = False          # the first real heading starts the body
            elif _is_head_chrome(s):
                continue
            else:
                in_head = False
        if (not s or s == '* * *' or CONTROL_LINE.match(s) or re.fullmatch(r'#+', s)
                or s in HEAD_EXACT):
            continue
        m = re.match(r'^(#{1,6})\s+(\S.*)$', s)
        out.append(Line(len(out) + 1, m.group(2) if m else s, bool(m)))
    return out


def clean_term(raw):
    """Return (title dict or None, body Lines) for an Al-Jamhara dictionary page."""
    lines = [l.strip() for l in raw]
    title, start = None, 0
    for i, s in enumerate(lines):
        m = TERM_TITLE.search(s)
        if m:
            title = {k: v.strip(' *_#') for k, v in m.groupdict().items()}
            start = i + 1
            break
    out = []
    for s in lines[start:]:
        if TERM_FOOTER.search(s):
            break
        if (not s or s == '* * *' or CONTROL_LINE.match(s) or TERM_MENU.match(s)
                or s.startswith(('Image:', 'iframe')) or re.fullmatch(r'#+', s)):
            continue
        m = re.match(r'^(#{1,6})\s+(\S.*)$', s)
        out.append(Line(len(out) + 1, m.group(2) if m else s, bool(m)))
    return title, out


def clean_page(page):
    kind, info = detect_kind(page.url)
    if kind == 'term':
        title, body = clean_term(page.raw_lines)
        return kind, info, title, body
    return kind, info, None, clean_dorar(page.raw_lines)


# ---------------------------------------------------------------- helpers

def parse_range(spec, n, what='--lines'):
    m = re.fullmatch(r'\s*(\d+)\s*(?:-\s*(\d+))?\s*', spec or '')
    if not m:
        fail(f'{what} must look like 12 or 12-15, got {spec!r}')
    a = int(m.group(1))
    b = int(m.group(2) or a)
    if not 1 <= a <= b <= n:
        fail(f'{what} {spec}: out of range (the cleaned page has {n} lines; run `show` first)')
    return a, b


SENT_END = '.؟?!؛'
_OPENERS, _CLOSERS = '([{«', ')]}»'


def split_sentences(text):
    """Split one cleaned line into sentences; ''.join(result) == text, so any contiguous
    range of sentences is an exact substring of the page.

    A sentence ends at a terminator (. ؟ ? ! ؛; a run of them counts once) that is not inside
    parentheses/brackets/«» or straight double quotes, and that is followed by whitespace, the
    end of the line, or an Arabic letter (dorar often omits the space between sentences). The
    terminator and the whitespace after it stay with their sentence. Text after the last
    terminator is the last sentence."""
    sents, start, depth, in_quote, i, n = [], 0, 0, False, 0, len(text)
    while i < n:
        c = text[i]
        if c == '"':
            in_quote = not in_quote
        elif c in _OPENERS:
            depth += 1
        elif c in _CLOSERS:
            depth = max(0, depth - 1)
        elif c in SENT_END and depth == 0 and not in_quote:
            while i + 1 < n and text[i + 1] in SENT_END:
                i += 1
            nxt = text[i + 1] if i + 1 < n else ''
            if not nxt or nxt.isspace() or '؀' <= nxt <= 'ۿ':
                j = i + 1
                while j < n and text[j].isspace():
                    j += 1
                sents.append(text[start:j])
                start = j
                i = j
                continue
        i += 1
    if start < n:
        sents.append(text[start:])
    return sents


def _ar_candidates(tok):
    cands = {tok}
    for pre in ('و', 'ف', 'ب', 'ل', 'ك', 'س'):
        if tok.startswith(pre) and len(tok) > 3:
            cands.add(tok[1:])
    for c in list(cands):
        if c.startswith('ال') and len(c) > 4:
            cands.add(c[2:])
    for c in list(cands):
        if c[:1] in 'يتنا' and len(c) > 3:
            cands.add(c[1:])
    return cands


def age_screen(text):
    """Return a sorted list of (category, word) deny-list hits in text (Arabic and English)."""
    hits = set()
    for tok in re.findall(r'[\u0621-\u064a\u0671-\u06d3]+', normalize_ar(text)):
        if IJMA.match(tok):
            continue
        cands = _ar_candidates(tok)
        for cat, stems in DENY_STEMS.items():
            for c in cands:
                for s in stems:
                    if (c == s or (len(s) >= 4 and c.startswith(s))
                            or (len(s) == 3 and c.startswith(s) and c[3:] in STEM_SUFFIXES)):
                        hits.add((cat, tok))
    low = text.lower()
    for cat, pats in DENY_EN.items():
        for p in pats:
            for m in re.finditer(r'\b' + p, low):
                hits.add((cat, re.match(r'\w+', low[m.start():]).group(0)))
    return sorted(hits)


def bank_verses(items_dir=ITEMS_DIR):
    """Set of (surah, ayah) for verse items in items/*.json."""
    found = set()
    for f in sorted(Path(items_dir).glob('*.json')):
        try:
            data = json.loads(f.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            continue
        for it in data if isinstance(data, list) else []:
            if isinstance(it, dict) and it.get('type') == 'verse' and it.get('surah') and it.get('ayah'):
                found.add((int(it['surah']), int(it['ayah'])))
    return found


def check_related(labels, items_dir=ITEMS_DIR):
    have = bank_verses(items_dir)
    for lab in labels:
        m = re.fullmatch(r'verse:(\d+):(\d+)', lab)
        if not m:
            fail(f'--related must look like verse:S:A, got {lab!r}')
        if (int(m.group(1)), int(m.group(2))) not in have:
            warn(f'{lab} is not in the bank (items/*.json); the link will not resolve until the verse is seeded')


def check_inline_verse(text, related=(), allow=False):
    """Refuse an excerpt that quotes Quran inline (﴿ ﴾, {...} around Arabic, or a [surah: ayah]
    reference) unless every reference is also given with --related verse:S:A and
    --allow-inline-verse is set."""
    marks = '﴿' in text or '﴾' in text or bool(BRACE_VERSE.search(text))
    brackets = [m.group(0) for m in VERSE_REF.finditer(text)]
    if not marks and not brackets:
        return
    refs = [r for b in brackets for r in verse_refs(b)]
    unparsed = [b for b in brackets if not verse_refs(b)]
    have = set(related)
    missing = sorted({f'verse:{s}:{a}' for s, a in refs} - have)
    why = None
    if marks and not brackets:
        why = 'it contains verse marks (﴿ ﴾ or {...}) with no [surah: ayah] reference to map'
    elif unparsed:
        why = f'unreadable reference(s): {unparsed}'
    elif missing:
        why = 'references not given with --related: ' + ', '.join(missing)
    elif not allow:
        why = 'inline Quran text needs --allow-inline-verse (and the --related labels)'
    if why:
        fail('the excerpt quotes Quran inline, so it is refused (' + why + '). Pick lines '
             'without the verse, or give every reference with --related verse:S:A plus '
             '--allow-inline-verse')
    warn('inline Quran text allowed: check each quoted verse against the bank before review')


def screen_excerpt(text, related=(), allow_inline_verse=False):
    for cat, word in age_screen(text):
        if cat in TONE_CATS:
            warn(f'tone check [{cat}]: excerpt contains "{word}"; no age change, but explain '
                 'hope-first for 6-9 (mercy, reward, repentance; the Fire briefly and simply)')
            continue
        warn(f'age screen [{cat}]: excerpt contains "{word}"; check against the deny-list before use')
    check_inline_verse(text, related, allow_inline_verse)
    if HADITH_QUOTE.search(text):
        warn('excerpt contains a quoted hadith or source citation in (( )); it is not a hadith item '
             'and carries no grade here')
    if SPEECH_QUOTE.search(normalize_ar(text)):
        warn('possible quoted prophetic speech: not allowed in a sirah/aqidah excerpt without book, '
             'number and grade')
    if FOOTNOTE_MARK.search(text):
        warn('footnote markers [n] are kept (use --strip-footnotes to remove the markers only)')


def split_csv(s):
    return [x.strip() for x in (s or '').split(',') if x.strip()]


# ---------------------------------------------------------------- term parsing

def _letters(s):
    return [c for c in s if c.isalpha()]


def _arabic_share(s):
    ls = _letters(s)
    if not ls:
        return 0.0
    return sum('\u0600' <= c <= '\u06ff' for c in ls) / len(ls)


def parse_term(title, body):
    """Return dict(title_ar, title_en, ar_line, en_line) using line numbers (or None)."""
    ar = en = None
    for l in body:
        if len(l.text.split()) < 4 or l.heading:
            continue
        share = _arabic_share(l.text)
        if ar is None and share >= 0.6:
            ar = l.num
        elif en is None and share <= 0.1:
            en = l.num
        if ar and en:
            break
    return {'title_ar': (title or {}).get('ar', ''), 'title_en': (title or {}).get('en', ''),
            'ar_line': ar, 'en_line': en}


# ---------------------------------------------------------------- commands

def cmd_show(args):
    page = load_page(args.file)
    kind, info, title, body = clean_page(page)
    print(f'# kind={kind} url={page.url} retrieved={page.retrieved or "?"} lines={len(body)}')
    if kind == 'term':
        t = parse_term(title, body)
        print(f'# term title_ar={t["title_ar"]!r} title_en={t["title_en"]!r} '
              f'auto ar_line={t["ar_line"]} en_line={t["en_line"]}')
    if args.sentences:
        a, _ = parse_range(str(args.sentences), len(body), '--sentences')
        for k, s in enumerate(split_sentences(body[a - 1].text), 1):
            print(f'{a}.{k:<3} {s.strip()}')
        return
    for l in body:
        text = l.text
        if args.max_chars and len(text) > args.max_chars:
            text = text[:args.max_chars] + ' ...'
        print(f'{l.num:>4}  {",".join(l.flags):<6} {text}')


def build_draft(args):
    page = load_page(args.file)
    kind, info, title, body = clean_page(page)
    if args.type != kind:
        fail(f'--type {args.type} does not match the page ({page.url} is a {kind} page)')
    if not body:
        fail('the cleaned page is empty; run `show` and check the saved file')
    item = {'type': kind, 'values': [args.value]}
    if args.related:
        check_related(args.related)

    if kind == 'term':
        t = parse_term(title, body)
        if args.lines:
            a, b = parse_range(args.lines, len(body))
            ar_lines = body[a - 1:b]
        elif t['ar_line']:
            ar_lines = [body[t['ar_line'] - 1]]
            print(f'draft: Arabic definition = line {t["ar_line"]} (automatic)', file=sys.stderr)
        else:
            fail('no Arabic definition found; pass --lines A-B (see `show`)')
        if args.en_lines:
            a, b = parse_range(args.en_lines, len(body), '--en-lines')
            en_lines = body[a - 1:b]
        elif t['en_line']:
            en_lines = [body[t['en_line'] - 1]]
            print(f'draft: English definition = line {t["en_line"]} (automatic)', file=sys.stderr)
        else:
            en_lines = []
            warn('no English definition found on the page; english_text left blank')
        item['title_ar'] = args.title_ar or t['title_ar']
        item['title_en'] = args.title_en or t['title_en']
        if not item['title_en']:
            warn('title_en is empty: the page title was not found; pass --title-en with the '
                 'dictionary equivalent exactly as the page shows it')
        item['arabic_text'] = '\n'.join(l.text for l in ar_lines)
        if en_lines:
            item['english_text'] = '\n'.join(l.text for l in en_lines)
            item['translation_name'] = TERM_TRANSLATION_NAME
        item['number'] = info['id']
        screen_text = item['arabic_text'] + '\n' + item.get('english_text', '')
    else:
        if not args.lines:
            fail('--lines A-B is required (see `show` for the numbers)')
        a, b = parse_range(args.lines, len(body))
        sel = body[a - 1:b]
        text = '\n'.join(l.text for l in sel)
        if args.sentences:
            if a != b:
                fail('--sentences needs a single --lines N (one cleaned line)')
            sents = split_sentences(sel[0].text)
            sa, sb = parse_range(args.sentences, len(sents), '--sentences')
            text = ''.join(sents[sa - 1:sb]).strip()
            if text not in '\n'.join(page.raw_lines):
                fail('internal error: the sentence cut is not a substring of the saved page')
        if args.strip_footnotes:
            text = re.sub(r' ?' + FOOTNOTE_MARK.pattern, '', text)
            text = '\n'.join(s.strip() for s in text.split('\n'))
            if any('fn' in l.flags or 'FN' in l.flags for l in sel):
                warn('--strip-footnotes removed only the "[n]" markers; footnote text on the '
                     'same lines is still in arabic_text, check it')
        item['arabic_text'] = text
        if kind == 'tafsir':
            if not args.verses or not re.fullmatch(r'\d{1,3}:\d{1,3}(?:-\d{1,3})?', args.verses):
                fail('tafsir needs --verses S:A or S:A-B (the verse group the page covers)')
            item['number'] = args.verses
            item['title_en'] = args.title_en or f'Tafsir of {args.verses}'
            item['title_ar'] = args.title_ar or f'تفسير {args.verses}'
        else:
            item['number'] = info['id']
            heads = [l.text for l in body if l.heading]
            item['title_ar'] = args.title_ar or (heads[0] if heads else '')
            item['title_en'] = args.title_en or ''
            if not item['title_en']:
                warn('title_en is empty; pass --title-en (our own short English title)')
            if not item['title_ar']:
                warn('title_ar is empty; pass --title-ar')
        screen_text = text
    item['book'] = KINDS[kind]
    item['source_site'] = info['site']
    item['source_url'] = page.url.strip() + (('#' + args.fragment.lstrip('#')) if args.fragment else '')
    if len(item['number']) > 30:
        warn(f'number {item["number"]!r} is longer than 30 characters')
    if args.keywords_ar:
        item['keywords_ar'] = split_csv(args.keywords_ar)
    if args.keywords_en:
        item['keywords_en'] = split_csv(args.keywords_en)
    if args.related:
        item['related'] = list(args.related)
    level = args.level or DEFAULT_LEVEL[kind]
    if kind == 'fiqh' and (args.disagreement_ar or args.disagreement_en):
        level = 'C'
    if level == 'C' and not (args.disagreement_ar or args.disagreement_en):
        warn('level C needs --disagreement-ar/--disagreement-en (clean() will reject it otherwise)')
    item['content_level'] = level
    if args.disagreement_ar:
        item['disagreement_note_ar'] = args.disagreement_ar
    if args.disagreement_en:
        item['disagreement_note_en'] = args.disagreement_en
    item['age_band'] = args.age_band
    item['verification_status'] = 'unverified'
    screen_excerpt(screen_text, args.related, args.allow_inline_verse)
    return item


def merge_out(path, item):
    path = Path(path)
    data = []
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
        except ValueError as e:
            fail(f'{path} is not valid JSON: {e}')
        if not isinstance(data, list):
            fail(f'{path} must hold a JSON list')
    key = (item['type'], item['source_url'])
    replaced = False
    for i, old in enumerate(data):
        if isinstance(old, dict) and (old.get('type'), old.get('source_url')) == key:
            data[i], replaced = item, True
    if not replaced:
        data.append(item)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(f'{"replaced" if replaced else "added"} {item["type"]} {item["source_url"]} in {path}',
          file=sys.stderr)


def cmd_draft(args):
    item = build_draft(args)
    if args.out:
        merge_out(args.out, item)
    else:
        print(json.dumps([item], ensure_ascii=False, indent=1))


def make_parser():
    ap = argparse.ArgumentParser(prog='draft_from_page.py', description=__doc__.split('\n')[0])
    sub = ap.add_subparsers(dest='cmd', required=True)
    sp = sub.add_parser('show', help='print the cleaned page body as numbered lines')
    sp.add_argument('file')
    sp.add_argument('--max-chars', type=int, default=0)
    sp.add_argument('--sentences', type=int, metavar='N',
                    help='print cleaned line N split into numbered sentences (for draft --sentences)')
    sp.set_defaults(func=cmd_show)
    dp = sub.add_parser('draft', help='write a draft item from selected lines')
    dp.add_argument('file')
    dp.add_argument('--type', required=True, choices=list(KINDS))
    dp.add_argument('--value', required=True, help='value slug (see content/values.json)')
    dp.add_argument('--lines', help='A-B, contiguous cleaned lines (terms: the Arabic definition)')
    dp.add_argument('--sentences', help='A-B, contiguous sentences of the single --lines N '
                                        '(see `show --sentences N`)')
    dp.add_argument('--en-lines', help='terms only: lines of the English definition')
    dp.add_argument('--verses', help='tafsir only: S:A-B, the verse group the page covers')
    dp.add_argument('--title-ar')
    dp.add_argument('--title-en')
    dp.add_argument('--related', action='append', default=[], metavar='verse:S:A')
    dp.add_argument('--level', choices=['A', 'B', 'C'])
    dp.add_argument('--disagreement-ar')
    dp.add_argument('--disagreement-en')
    dp.add_argument('--age-band', choices=['all', '6-9', '10-13'], default='all')
    dp.add_argument('--keywords-ar', help='comma separated')
    dp.add_argument('--keywords-en', help='comma separated')
    dp.add_argument('--fragment', help='appended to source_url as #fragment (several items per page)')
    dp.add_argument('--strip-footnotes', action='store_true')
    dp.add_argument('--allow-inline-verse', action='store_true',
                    help='allow an excerpt that quotes Quran, if every reference is in --related')
    dp.add_argument('--out', help='JSON list file to add the item to (default: print)')
    dp.set_defaults(func=cmd_draft)
    return ap


def main(argv=None):
    args = make_parser().parse_args(argv)
    args.func(args)


if __name__ == '__main__':
    main()
