#!/usr/bin/env python3
"""Offline-first parser for dorar.net hadith pages saved by a human (plan route D, r3 section 7.1).

Hadith text is NEVER typed here or in the tests. It is copied from the saved dorar page.
Agents do not fetch dorar by script: the lead (or Cowork) saves pages from a normal browser
into content/tools/.cache/dorar/ (gitignored). Do not commit saved pages.

Accepted inputs (--from-file takes files, directories or globs; repeat the option freely):
  1. Site-search HTML (https://www.dorar.net/hadith/search?q=..&s[]=6216&s[]=3088 saved as
     "Webpage, HTML only"), or a single https://dorar.net/h/<id> page. Blocks are
     div.border-bottom: text in h5, labelled <strong> values, id in <a tag="<id>">.
  2. Text pages / copy-button text with the labels  الراوي | المحدث | المصدر |
     الصفحة أو الرقم | خلاصة حكم المحدث  (hadith text on the lines before the labels).
  3. API JSON or JSONP  {"ahadith":{"result":"<html>"}}  (no hadith id in this shape).
Saved-file convention: the first lines may say  `Source URL: <url>`  and  `Retrieved: YYYY-MM-DD`
(or `# url: <url>`; in HTML put them in an <!-- ... --> comment). source_url is only ever a
https://dorar.net/h/<id> permalink: from the share link / canonical link in the HTML, or a header URL
of that form. Search-result URLs are not accepted (they do not identify one hadith).

Usage (run from this directory, or give the path):
  python3 fetch_hadith.py --from-file '.cache/dorar/*.html' --book bukhari --list
  python3 fetch_hadith.py --from-file .cache/dorar/honesty.html --book bukhari --pick 3 \\
      --value honesty [--out /tmp/honesty-draft.json]
  python3 fetch_hadith.py --live --url https://dorar.net/h/<id>      (off by default, see below)

  --book bukhari|muslim  keep entries whose المصدر is صحيح البخاري / صحيح مسلم
  --list                 numbered candidates (default action); --all also shows rejected ones
  --pick N --value SLUG  write item N (numbering of --list) as a JSON list with one item to
                         stdout or --out. Status is always `unverified`: the lead checks it
                         against the cited dorar page, then mark_reviewed.py promotes it.
  --no-provenance        do not touch content/provenance.json (pick appends dorar file
                         name, sha256 and retrieved date under hadith:<book>:<number>)

Rules enforced: every entry needs all five labels and a non-empty text; partial quotations
(". . .", "...", "…", "... الحديث") are rejected; the grade loses its [ ] brackets; for a pick the
grade must be exactly صحيح, the number a pure integer, the book Bukhari or Muslim and the grader
the compiler. Diacritics are never touched; stdlib only.

--live (needs --url, one page every 5 s, cached in .cache/dorar/) stops on HTTP 403 with
"save the page from a browser": dorar sits behind Cloudflare, we do not try to get round it.
"""
import argparse
import glob
import html
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

import hadith_common as hc

DORAR_CACHE = hc.CACHE / 'dorar'
LIVE_DELAY = 5.0
CREDIT = 'موقع الدرر السنية'

LABELS = {
    'الراوي': 'narrator',
    'المحدث': 'grader',
    'المصدر': 'book',
    'الصفحة أو الرقم': 'number',
    'خلاصة حكم المحدث': 'grade',
    'التخريج': 'takhrij',
}
REQUIRED = ('narrator', 'grader', 'book', 'number', 'grade')
_LABEL_ALT = '|'.join(sorted(LABELS, key=len, reverse=True) + ['الصفحة'])
LABEL_RE = re.compile(r'(' + _LABEL_ALT + r')\s*[:：]')
# Navigation text the site prints between entries; never part of a hadith.
NOISE = ('أحاديث مشابهة', 'أصول الحديث', 'الصحيح البديل', 'شرح الحديث', 'التصنيف الموضوعي', CREDIT)
PARTIAL_RE = re.compile(r'(?:\.\s*){3,}|…')
PREFIX_RE = re.compile(r'^\s*(?:\d+\s*)?[-–—]\s+')
BRACKETS_RE = re.compile(r'^\s*\[([^\[\]]*)\]\s*$')  # one surrounding pair only
PERMALINK_PATH_RE = re.compile(r'^/h/([A-Za-z0-9]{4,16})/?$')
DORAR_HOSTS = ('dorar.net', 'www.dorar.net')
BOOK_HEADINGS = {hc.strip_marks(b['ar']) for b in hc.BOOKS.values()}


# --- cleaning ---------------------------------------------------------------

def clean_hadith(s):
    """Unwrap tags (keeping their content), decode entities, collapse whitespace, drop the
    "N -" list prefix. Never touches diacritics or any letter."""
    s = re.sub(r'<br\s*/?>', ' ', s or '', flags=re.I)
    s = re.sub(r'<[^>]+>', '', s)
    s = html.unescape(s)
    s = re.sub(r'\s+', ' ', s).strip()
    return PREFIX_RE.sub('', s).strip()


def permalink_id(url):
    """'https://www.dorar.net/h/AbCd1234' -> 'AbCd1234'; anything else (search URLs, other
    hosts, look-alike hosts such as dorar.net.evil.example) -> ''."""
    try:
        u = urllib.parse.urlparse(url or '')
    except ValueError:
        return ''
    m = PERMALINK_PATH_RE.match(u.path)
    return m.group(1) if u.scheme in ('http', 'https') and u.hostname in DORAR_HOSTS and m else ''


def strip_brackets(s):
    """`[صحيح]` -> `صحيح` (dorar brackets paraphrased grades and editorial narrator names)."""
    s = (s or '').strip()
    m = BRACKETS_RE.match(s)
    return m.group(1).strip() if m else s


def is_partial(text):
    """True for fragments: any ". . ." / "..." / "…" run, or "... الحديث" (covered by the first)."""
    return bool(PARTIAL_RE.search(text))


def book_key(book_name):
    """'صحيح البخاري' -> 'bukhari', 'صحيح مسلم' -> 'muslim', else None (marks ignored)."""
    plain = hc.strip_marks(book_name or '')
    for key, b in hc.BOOKS.items():
        if plain == hc.strip_marks(b['ar']):
            return key
    return None


# --- entries ----------------------------------------------------------------

def make_entry(raw, meta, source_file, fmt):
    """Normalise a raw dict (text, narrator, grader, book, number, grade, tag, ...) into an
    entry with a `reject` reason ('' when usable)."""
    e = {
        'text': clean_hadith(raw.get('text', '')),
        'narrator': strip_brackets(clean_hadith(raw.get('narrator', ''))),
        'grader': clean_hadith(raw.get('grader', '')),
        'book': clean_hadith(raw.get('book', '')),
        'number_raw': clean_hadith(raw.get('number', '')),
        'grade_raw': clean_hadith(raw.get('grade', '')),
        'tag': raw.get('tag', '') or '',
        'categories': raw.get('categories', []),
        'file': str(source_file), 'format': fmt,
        'retrieved': meta.get('retrieved', ''), 'header_url': meta.get('url', ''),
        'file_sha256': meta.get('sha256', ''),
    }
    e['grade'] = strip_brackets(e['grade_raw'])
    e['number'] = hc.pure_integer(e['number_raw']) or ''
    e['book_key'] = book_key(e['book'])
    e['words'] = hc.word_count(e['text'])
    # source_url must be a /h/<id> permalink: from the share link, the canonical link or the
    # header URL. A search URL proves nothing about one hadith, so it is left empty.
    tag = e['tag'] or permalink_id(meta.get('page_url', '')) or permalink_id(meta.get('url', ''))
    e['tag'] = tag
    e['source_url'] = f'https://dorar.net/h/{tag}' if tag else ''
    missing = [k for k in REQUIRED if not (e['number_raw'] if k == 'number' else e[k])]
    if not e['text']:
        missing.insert(0, 'text')
    if missing:
        e['reject'] = 'missing ' + ','.join(missing)
    elif is_partial(e['text']):
        e['reject'] = 'partial quotation (ellipsis)'
    else:
        e['reject'] = ''
    return e


def read_header(text):
    """Source URL / Retrieved / # url: lines or an HTML comment in the first 4 KB."""
    head = text[:4096]
    meta = {}
    m = re.search(r'Source URL:\s*(\S+?)(?:\s*-->|\s|$)', head)
    if not m:
        m = re.search(r'^#\s*url:\s*(\S+)', head, re.M)
    if m:
        meta['url'] = m.group(1)
    m = re.search(r'Retrieved:\s*(\d{4}-\d{2}-\d{2})', head)
    if m:
        meta['retrieved'] = m.group(1)
    return meta


# --- format 1: site HTML ----------------------------------------------------

class _BlockParser(HTMLParser):
    """Parses ONE div.border-bottom chunk of a site page."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.h5_done = False
        self.in_h5 = False
        self.h5 = []
        self.in_strong = False
        self.strong = []
        self.strongs = []
        self.skip = 0
        self.tag = ''
        self.sharh = ''
        self.cat_href = False
        self.cat = []
        self.categories = []
        self.copy = ''

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ('script', 'style'):
            self.skip += 1
        elif tag == 'h5' and not self.h5_done:
            self.in_h5 = True
        elif tag == 'br' and self.in_h5:
            self.h5.append(' ')
        elif tag == 'strong' and not self.in_h5:
            self.in_strong = True
            self.strong = []
        elif tag == 'a':
            if re.fullmatch(r'[A-Za-z0-9]{4,16}', a.get('tag') or '') and not self.tag:
                self.tag = a['tag']
            if a.get('xplain') and a['xplain'] != '0':
                self.sharh = a['xplain']
            if (a.get('href') or '').startswith('/hadith-category/cat/'):
                self.cat_href = True
                self.cat = []
            if a.get('data-clipboard-text') and not self.copy:
                self.copy = a['data-clipboard-text']

    def handle_endtag(self, tag):
        if tag in ('script', 'style') and self.skip:
            self.skip -= 1
        elif tag == 'h5' and self.in_h5:
            self.in_h5 = False
            self.h5_done = True
        elif tag == 'strong' and self.in_strong:
            self.in_strong = False
            self.strongs.append(''.join(self.strong))
        elif tag == 'a' and self.cat_href:
            self.cat_href = False
            c = clean_hadith(''.join(self.cat))
            if c:
                self.categories.append(c)

    def handle_data(self, data):
        if self.skip:
            return
        if self.in_h5:
            self.h5.append(data)
        if self.in_strong:
            self.strong.append(data)
        if self.cat_href:
            self.cat.append(data)


_BLOCK_SPLIT = re.compile(r'(?=<div[^>]*\bclass="[^"]*\bborder-bottom\b)')


def parse_label_text(s):
    """'| المحدث : البخاري' -> ('grader', 'البخاري'); None when there is no known label."""
    s = re.sub(r'\s+', ' ', s).strip().lstrip('|').strip()
    m = LABEL_RE.match(s)
    if not m:
        return None
    key = LABELS.get(m.group(1), 'number' if m.group(1) == 'الصفحة' else None)
    return key, s[m.end():].strip()


def parse_html(text, meta, source_file):
    entries = []
    page_url = ''
    m = re.search(r'<link[^>]+rel="canonical"[^>]+href="([^"]+)"', text) or \
        re.search(r'<meta[^>]+property="og:url"[^>]+content="([^"]+)"', text)
    if m:
        page_url = m.group(1)
    meta = dict(meta, page_url=page_url)
    chunks = [c for c in _BLOCK_SPLIT.split(text) if '<h5' in c]
    single = len(chunks) == 1
    for chunk in chunks:
        p = _BlockParser()
        p.feed(chunk)
        raw = {'text': ''.join(p.h5), 'tag': p.tag, 'categories': p.categories}
        for s in p.strongs:
            kv = parse_label_text(s)
            if kv and kv[0] and kv[0] not in raw:
                raw[kv[0]] = kv[1]
        if not any(k in raw for k in ('narrator', 'grader', 'book')) and p.copy:
            raw.update(_fields_from_copy(p.copy))
        e = make_entry(raw, meta if single else dict(meta, page_url=''), source_file, 'html')
        entries.append(e)
    return entries


def _fields_from_copy(s):
    out = {}
    s = re.sub(r'<br\s*/?>', '\n', s)
    s = re.sub(r'</?ref>', '', s).replace(CREDIT, '')
    pos = [(m.start(), m.end(), m.group(1)) for m in LABEL_RE.finditer(s)]
    for i, (st, en, lab) in enumerate(pos):
        end = pos[i + 1][0] if i + 1 < len(pos) else len(s)
        key = LABELS.get(lab, 'number' if lab == 'الصفحة' else None)
        if key and key not in out:
            out[key] = re.sub(r'\s*\|\s*$', '', s[en:end].strip()).strip()
    return out


# --- format 2: text ---------------------------------------------------------

def parse_text(text, meta, source_file):
    body = re.sub(r'<br\s*/?>', '\n', text, flags=re.I)
    body = re.sub(r'</?ref>', '\n', body)
    lines = []
    for ln in body.splitlines():
        if re.match(r'\s*(Source URL:|Retrieved:|#\s*url:)', ln):
            continue
        ln = re.sub(r'\s+', ' ', ln).strip()
        lines.append(ln)
    entries = []
    cur = {'fields': {}, 'text': ''}
    pending = []
    open_key = None

    def flush():
        nonlocal cur
        if cur['fields']:
            raw = dict(cur['fields'], text=cur['text'])
            entries.append(make_entry(raw, dict(meta, page_url=''), source_file, 'text'))
        cur = {'fields': {}, 'text': ''}

    cont = None  # a التخريج value that wraps onto following lines

    def is_noise(bare):
        return bare in NOISE or hc.strip_marks(bare) in BOOK_HEADINGS

    def value_like(key, line):
        """Could `line` be the value of a label whose value sat on the next line?"""
        if len(line.split()) > 12:
            return False
        return bool(re.fullmatch(r'[\d٠-٩/\-–.،, ]+', line)) if key == 'number' else True

    for line in lines:
        if not line:
            open_key = cont = None      # a blank line ends a dangling label or a wrapped value
            continue
        found = list(LABEL_RE.finditer(line))
        if not found:
            bare = line.replace('|', '').strip()
            if is_noise(bare):
                open_key = cont = None
                continue
            if open_key and value_like(open_key, line):
                cur['fields'][open_key] = line
                open_key = None
                continue
            open_key = None             # an empty label value never swallows the next hadith's text
            if cont:
                cur['fields'][cont] = (cur['fields'][cont] + ' ' + line).strip()
            elif bare:
                pending.append(line)
            continue
        open_key = cont = None
        prefix = line[:found[0].start()].replace('|', ' ').strip()
        if prefix:
            pending.append(prefix)
        for i, mt in enumerate(found):
            key = LABELS.get(mt.group(1), 'number' if mt.group(1) == 'الصفحة' else None)
            end = found[i + 1].start() if i + 1 < len(found) else len(line)
            val = line[mt.end():end].strip().rstrip('|').strip()
            val = val.replace(CREDIT, '').strip()
            if key is None:
                continue
            if key in cur['fields']:
                flush()
            if not cur['fields'] and not cur['text']:
                cur['text'] = ' '.join(pending)
                pending = []
            cur['fields'][key] = val
            open_key = key if not val else None
            cont = key if key == 'takhrij' else None
        pending = []        # only lines after the LAST label line can start the next entry
    flush()
    return entries


# --- format 3: API JSON / JSONP --------------------------------------------

def parse_api(text, meta, source_file):
    s = text.strip()
    m = re.match(r'^[\w$.]*\(\s*(.*)\)\s*;?\s*$', s, re.S)
    if m:
        s = m.group(1)
    data = json.loads(s)
    res = (data.get('ahadith') or {}).get('result') if isinstance(data, dict) else None
    if not isinstance(res, str):
        raise ValueError('JSON has no {"ahadith":{"result":"<html>"}} (the legacy array shape is not supported)')
    entries = []
    pat = re.compile(r'<div class="hadith"[^>]*>(.*?)</div>\s*<div class="hadith-info">(.*?)</div>', re.S)
    for hm in pat.finditer(res):
        raw = {'text': hm.group(1)}
        parts = re.split(r'<span class="info-subtitle">\s*([^<]*?)\s*</span>', hm.group(2))
        # parts: [pre, label1, value1, label2, value2, ...]
        for i in range(1, len(parts) - 1, 2):
            lab = re.sub(r'\s*[:：]\s*$', '', clean_hadith(parts[i]))
            key = LABELS.get(lab)
            if key:
                raw[key] = parts[i + 1]
        entries.append(make_entry(raw, dict(meta, page_url=''), source_file, 'api'))
    return entries


# --- loading ----------------------------------------------------------------

def detect_format(text):
    s = text.lstrip()
    if re.match(r'^[\w$.]*\(?\s*\{\s*"ahadith"', s) or ('"ahadith"' in s[:200] and '{' in s[:50]):
        return 'api'
    if '<h5' in text and 'border-bottom' in text:
        return 'html'
    return 'text'


def parse_file(path):
    path = Path(path)
    raw_bytes = path.read_bytes()
    text = raw_bytes.decode('utf-8-sig')
    meta = read_header(text)
    meta['sha256'] = hc.sha256_bytes(raw_bytes)
    fmt = detect_format(text)
    parser = {'html': parse_html, 'text': parse_text, 'api': parse_api}[fmt]
    return meta, parser(text, meta, path.name)


def expand_paths(specs):
    out = []
    for spec in specs:
        p = Path(spec).expanduser()
        if p.is_dir():
            out += sorted(x for x in p.iterdir() if x.is_file() and not x.name.startswith('.'))
        elif any(ch in spec for ch in '*?['):
            out += [Path(x) for x in sorted(glob.glob(str(p)))]
        elif p.exists():
            out.append(p)
        else:
            raise FileNotFoundError(spec)
    return out


def load_entries(specs):
    entries = []
    for p in expand_paths(specs):
        entries += parse_file(p)[1]
    return entries


def candidates(entries, book=None):
    """(usable, rejected). Usable = no reject reason, book filter applied, deduped by
    (book, number); the first copy wins and `dups` counts the others."""
    usable, rejected, seen = [], [], {}
    for e in entries:
        if book and e['book_key'] != book:
            continue
        if e['reject']:
            rejected.append(e)
            continue
        key = (e['book_key'] or e['book'], e['number'] or e['number_raw'])
        if key in seen and e['number']:
            seen[key]['dups'] = seen[key].get('dups', 0) + 1
            continue
        seen[key] = e
        usable.append(e)
    return usable, rejected


def pick_problems(e):
    """Reasons an entry cannot become a hadith item (empty list = fine)."""
    p = []
    if e['book_key'] not in hc.BOOKS:
        p.append('book is not Sahih al-Bukhari / Sahih Muslim')
    if not e['number']:
        p.append(f"number {e['number_raw']!r} is not a pure integer (set it by hand after checking dorar)")
    if e['grade'] != 'صحيح':
        p.append(f"grade {e['grade']!r} is not exactly صحيح")
    elif e['book_key'] in hc.BOOKS and e['grader'] != hc.BOOKS[e['book_key']]['grader']:
        p.append(f"grader {e['grader']!r} is not the compiler {hc.BOOKS[e['book_key']]['grader']!r}")
    return p


def to_item(e, values, with_status=True):
    b = hc.BOOKS[e['book_key']]
    item = {
        'type': 'hadith',
        'values': list(values),
        'arabic_text': e['text'],
        'book': b['name'],
        'number': e['number'],
    }
    if e['narrator']:
        item['narrator'] = e['narrator']
    item.update(grade=e['grade'], grader=e['grader'], source_site='dorar.net', source_url=e['source_url'])
    if with_status:
        item['verification_status'] = 'unverified'  # a human confirms it against the dorar page
    return item


# --- output -----------------------------------------------------------------

def print_list(usable, rejected, show_all, out=None):
    out = out or sys.stdout
    print(f"{'#':>3}  {'book':<9} {'number':>7} {'grade':<8} {'grader':<9} {'words':>5}  {'id':<9} text", file=out)
    for i, e in enumerate(usable, 1):
        flag = ''
        probs = pick_problems(e)
        if probs:
            flag = '  !' + probs[0]
        prev = ' '.join(e['text'].split()[:8])
        dup = f" (+{e['dups']} dup)" if e.get('dups') else ''
        print(f"{i:>3}  {(e['book_key'] or e['book'])[:9]:<9} {e['number'] or '?':>7} {e['grade']:<8} {e['grader']:<9} "
              f"{e['words']:>5}  {e['tag'] or '-':<9} {prev}{dup}{flag}", file=out)
    print(f'{len(usable)} usable, {len(rejected)} rejected', file=sys.stderr)
    if rejected:
        from collections import Counter
        for reason, n in Counter(r['reject'] for r in rejected).items():
            print(f'  rejected {n}: {reason}', file=sys.stderr)
        if show_all:
            for r in rejected:
                print(f"  - {r['file']}: {r['reject']}: {' '.join(r['text'].split()[:6])}", file=sys.stderr)


# --- live (optional, off by default) ---------------------------------------

def live_fetch(urls):
    DORAR_CACHE.mkdir(parents=True, exist_ok=True)
    out = []
    for i, url in enumerate(urls):
        f = DORAR_CACHE / ('live_' + hc.sha256_bytes(url.encode())[:16] + '.html')
        if not f.exists():
            if i:
                time.sleep(LIVE_DELAY)
            req = urllib.request.Request(url, headers={'User-Agent': hc.UA})
            try:
                with urllib.request.urlopen(req, timeout=30) as r:
                    body = r.read().decode('utf-8')
            except urllib.error.HTTPError as ex:
                if ex.code == 403:
                    sys.exit('fetch_hadith: HTTP 403 from dorar.net (Cloudflare). Stopping: save the page from a '
                             'browser into .cache/dorar/ and use --from-file.')
                sys.exit(f'fetch_hadith: {url}: HTTP {ex.code}')
            except (urllib.error.URLError, OSError) as ex:
                sys.exit(f'fetch_hadith: {url}: {ex}')
            f.write_text(f'<!-- Source URL: {url} -->\n<!-- Retrieved: {time.strftime("%Y-%m-%d")} -->\n{body}',
                         encoding='utf-8')
        out.append(f)
    return out


# --- CLI --------------------------------------------------------------------

def build_parser():
    ap = argparse.ArgumentParser(description='Parse saved dorar.net hadith pages (offline-first).')
    ap.add_argument('--from-file', action='append', metavar='PATH_OR_GLOB', help='saved page(s); repeatable')
    ap.add_argument('--book', choices=sorted(hc.BOOKS), help='keep only this compiler')
    ap.add_argument('--list', action='store_true', help='print numbered candidates (default)')
    ap.add_argument('--all', action='store_true', help='with --list, also show rejected entries')
    ap.add_argument('--pick', type=int, metavar='N', help='write item N of --list')
    ap.add_argument('--value', help='value slug(s), comma separated (required with --pick)')
    ap.add_argument('--out', help='write the item JSON here instead of stdout')
    ap.add_argument('--no-provenance', action='store_true')
    ap.add_argument('--provenance', help=argparse.SUPPRESS)
    ap.add_argument('--live', action='store_true', help='fetch --url pages (off by default; stops on 403)')
    ap.add_argument('--url', action='append', help='with --live')
    return ap


def main(argv=None):
    args = build_parser().parse_args(argv)
    specs = list(args.from_file or [])
    if args.live:
        if not args.url:
            sys.exit('fetch_hadith: --live needs --url')
        specs += [str(f) for f in live_fetch(args.url)]
    if not specs:
        sys.exit('fetch_hadith: give --from-file PATH_OR_GLOB (or --live --url URL)')
    try:
        entries = load_entries(specs)
    except FileNotFoundError as ex:
        sys.exit(f'fetch_hadith: no such file: {ex}')
    except ValueError as ex:
        sys.exit(f'fetch_hadith: {ex}')
    usable, rejected = candidates(entries, args.book)
    if args.pick is None or args.list:
        print_list(usable, rejected, args.all)
    if args.pick is None:
        return 0
    if not args.value:
        sys.exit('fetch_hadith: --pick needs --value SLUG')
    values = [v.strip() for v in args.value.split(',') if v.strip()]
    known = hc.known_values()
    bad = [v for v in values if known and v not in known]
    if bad:
        sys.exit(f'fetch_hadith: unknown value slug(s): {", ".join(bad)}')
    if not 1 <= args.pick <= len(usable):
        sys.exit(f'fetch_hadith: --pick {args.pick} is out of range (1..{len(usable)})')
    e = usable[args.pick - 1]
    problems = pick_problems(e)
    if problems:
        sys.exit('fetch_hadith: cannot pick this entry: ' + '; '.join(problems))
    item = to_item(e, values)
    blob = json.dumps([item], ensure_ascii=False, indent=2) + '\n'
    if args.out:
        Path(args.out).write_text(blob, encoding='utf-8')
        print(f'wrote {args.out}', file=sys.stderr)
    else:
        sys.stdout.write(blob)
    if not item['source_url']:
        print('note: no https://dorar.net/h/<id> permalink known, so source_url is EMPTY (a search URL does not '
              'identify one hadith). Save the /h/<id> page, or put `Source URL: https://dorar.net/h/<id>` on '
              'the first line of the saved file.', file=sys.stderr)
    if not args.no_provenance:
        rec = {'dorar_file': e['file'], 'dorar_sha256': e['file_sha256'], 'dorar_retrieved': e['retrieved'],
               'dorar_source_url': e['source_url']}
        path = hc.append_provenance(hc.label(item['book'], item['number']), rec, args.provenance)
        print(f'provenance: {hc.label(item["book"], item["number"])} -> {path}', file=sys.stderr)
    return 0


if __name__ == '__main__':
    sys.exit(main())
