#!/usr/bin/env python3
"""HadeethEnc discovery for hadith items (plan section 4, route H: "find on HadeethEnc, prove on dorar").

HadeethEnc is used to FIND child-suitable Bukhari/Muslim hadith graded صحيح and to read the
book + number out of its Arabic `reference`. The cited Arabic text must come from the dorar.net
page (see fetch_hadith.py); HadeethEnc's English is attached only if the two matns are equal
(plan 4.2 step 4). No hadith text lives in this repo's code or fixtures.

All commands run from this directory. Cache (gitignored): .cache/hadeethenc/ (raw JSON per id and
language, plus a .meta.json with url, retrieved_at and sha256 of the raw bytes).

  python3 fetch_hadeethenc.py pull [--values all|slug,slug] [--cache DIR] [--refresh] [--gap 0.15]
      Needs network (hadeethenc.com). For the mapped categories (hadeethenc_categories.json):
      categories list, hadeeths/list (language=ar, per_page=100, all pages), then hadeeths/one for
      ar and en. Sequential, 150 ms apart, honest User-Agent, backs off on HTTP 429, STOPS on 403
      (no retry, no workaround). Records whose Arabic grade is not exactly صحيح or whose attribution
      is not Bukhari/Muslim/agreed are not fetched in English (--no-prefilter to fetch all).
  python3 fetch_hadeethenc.py candidates --value SLUG|all [--limit 20] [--max-words 80]
          [--require-en] [--require-number] [--json] [--json-file PATH] [--cache DIR]
      Offline, from the cache. Ranked table: id, book, number or ? (= needs_number: the reference gave
      no book number, read it off the dorar page), words, relevance, category, English title.
      Relevance order: category match, then Arabic keyword hit (checked on the Arabic title and matn,
      normalised, so records without English still match), then English keyword hit.
      `--value all` prints one count line per value (cand / numbered / needs_number, flags values
      with fewer than 2; --limit does not apply) and writes DIR/candidates.json (or --json-file):
      every candidate of every value in rank order, [{value, hadeethenc_id, book, number|null,
      needs_number, grade, attribution, words, first_8_words_ar, hadeethenc_url}], with only 8
      words of the Arabic (the first words of the saying, after the narrator clause): enough to
      search dorar.net, not a copy of the hadith.
      `--limit 0` means no limit; `--json-file` also writes the rows shown for a single value.
  python3 fetch_hadeethenc.py draft --id ID --value SLUG [--dorar-file PATH] [--dorar-pick N]
          [--book bukhari|muslim] [--number N] [--out FILE] [--no-provenance] [--cache DIR]
      Draft item (a JSON list with one item, status unverified) to stdout or --out, and provenance
      appended to content/provenance.json under hadith:<book>:<number>. Without --dorar-file,
      arabic_text, grade, grader and source_url are EMPTY and no English/translation fields are
      attached (the matn check cannot run); provenance holds only the HadeethEnc id, sha256 and
      retrieved_at. With it, those fields come from the dorar page and the matn-equality rule
      decides whether HadeethEnc's English is attached (english_text, translation_name and
      translation_source_url appear only when the matns are equal; otherwise the reason is printed). For an "agreed upon" hadith run draft twice
      with --book bukhari and --book muslim: dorar prints one entry per book.

Terms (r1 2.7): do not alter the text; cite HadeethEnc.com; keep retrieval date + sha256.
"""
import argparse
import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fetch_hadith  # noqa: E402
import hadith_common as hc  # noqa: E402

BASE = 'https://hadeethenc.com/api/v1'
PAGE = 'https://hadeethenc.com/{lang}/browse/hadith/{id}'
CATS_JSON = hc.TOOLS / 'hadeethenc_categories.json'
DEFAULT_CACHE = hc.CACHE / 'hadeethenc'
GRADE_OK = 'صحيح'
DEFAULT_MAX_WORDS = 80    # 60 dropped the best honesty hadith (62 words); 80 keeps it
TRANSLATION_NAME = 'HadeethEnc.com (English)'
# The (?<!\w[ \t])(?<!\w) pair is a left boundary: "مختصر صحيح مسلم (..)" (an abridgement) must not match.
REF_PAT = re.compile(r'(?<!\w[ \t])(?<!\w)(صحيح البخاري|صحيح مسلم)\s*\(\s*(\d+)\s*/\s*[^)]*\)\s*\(([^)]*)\)')
BOOK_BY_AR = {b['ar']: k for k, b in hc.BOOKS.items()}


class Blocked(Exception):
    pass


class NotFound(Exception):
    pass


def now_iso():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


# --- HTTP -------------------------------------------------------------------

class Fetcher:
    """Sequential, polite GET client. `_request` is the only network call (tests override it)."""

    def __init__(self, gap=0.15, sleep=time.sleep, max_retries=5):
        self.gap = gap
        self.sleep = sleep
        self.max_retries = max_retries
        self._last = 0.0
        self.requests = 0

    def _request(self, url):
        req = urllib.request.Request(url, headers={'User-Agent': hc.UA, 'Accept': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.status, dict(r.headers), r.read()
        except urllib.error.HTTPError as e:
            return e.code, dict(e.headers or {}), b''

    def get(self, url):
        for attempt in range(self.max_retries):
            wait = self.gap - (time.monotonic() - self._last)
            if wait > 0:
                self.sleep(wait)
            try:
                status, headers, body = self._request(url)
            except (urllib.error.URLError, OSError) as e:
                status, headers, body = 0, {}, str(e).encode()
            finally:
                self._last = time.monotonic()
            self.requests += 1
            if status == 200:
                return body
            if status == 403:
                raise Blocked(url)
            if status == 404:
                raise NotFound(url)
            if status == 429 or status >= 500 or status == 0:
                try:
                    delay = float(headers.get('Retry-After', ''))
                except ValueError:
                    delay = min(2.0 * 2 ** attempt, 60.0)
                print(f'  HTTP {status or "network error"} for {url}; waiting {delay:.0f}s '
                      f'(attempt {attempt + 1}/{self.max_retries})', file=sys.stderr)
                self.sleep(delay)
                continue
            raise RuntimeError(f'HTTP {status} for {url}')
        raise RuntimeError(f'giving up on {url} after {self.max_retries} attempts')


# --- cache ------------------------------------------------------------------

def meta_path(p):
    return p.with_name(p.name[:-len('.json')] + '.meta.json')


def store(path, body, url):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body)
    hc.write_json(meta_path(path), {'url': url, 'retrieved_at': now_iso(), 'sha256': hc.sha256_bytes(body),
                                    'bytes': len(body)})


def one_path(cache, hid, lang):
    return Path(cache) / 'one' / f'{hid}.{lang}.json'


def list_path(cache, cat, page):
    return Path(cache) / 'list' / f'{cat}.ar.p{page}.json'


def cats_path(cache, lang):
    return Path(cache) / f'categories.{lang}.json'


def cached_get(fetcher, path, url, refresh=False, stats=None):
    """Return bytes for url, from the cache when present. NotFound leaves a marker meta file."""
    if path.exists() and not refresh:
        if stats is not None:
            stats['cached'] = stats.get('cached', 0) + 1
        return path.read_bytes()
    body = fetcher.get(url)
    store(path, body, url)
    if stats is not None:
        stats['fetched'] = stats.get('fetched', 0) + 1
    return body


# --- config -----------------------------------------------------------------

def load_config(path=CATS_JSON):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def resolve_values(spec, cfg):
    if spec in (None, '', 'all'):
        return list(cfg['values'])
    vals = [v.strip() for v in spec.split(',') if v.strip()]
    bad = [v for v in vals if v not in cfg['values']]
    if bad:
        sys.exit(f'fetch_hadeethenc: no category mapping for: {", ".join(bad)}')
    return vals


# --- record logic -----------------------------------------------------------

def fold(s):
    """Lower-case, no combining marks, every non-word run -> one space (for token tests)."""
    s = ''.join(c for c in unicodedata.normalize('NFKD', s or '') if unicodedata.category(c) != 'Mn')
    return re.sub(r'[\W_]+', ' ', s.lower()).strip()


_BUKHARI = {'bukhari', 'البخاري', 'بخاري'}
_MUSLIM = {'muslim', 'مسلم'}
_BOTH = {'agreed', 'upon', 'متفق', 'عليه', 'الصحيحين', 'sahihayn', 'sahihain', 'صحيحان'}
_FILLER = {'narrated', 'by', 'and', 'al', 'the', 'in', 'his', 'sahih', 'two', 'books', 'both', 'of', 'ibn',
           'رواه', 'أخرجه', 'اخرجه', 'و', 'في', 'صحيحه', 'صحيحيهما'}


def sahihayn_books(attribution):
    """Map an attribution string to ({'bukhari','muslim'}, other) in any spelling variant.
    `other` is True when anything besides the two compilers (a different collector, prose)
    appears, so a pure Bukhari/Muslim/agreed attribution is the only one that passes."""
    books, other = set(), False
    for tok in fold(attribution).split():
        t = tok
        if t not in _BUKHARI | _MUSLIM | _BOTH | _FILLER and t.startswith('و') and t[1:] in _BUKHARI | _MUSLIM:
            t = t[1:]
        if t in _BUKHARI:
            books.add('bukhari')
        elif t in _MUSLIM:
            books.add('muslim')
        elif t in _BOTH:
            books |= {'bukhari', 'muslim'}
        elif t not in _FILLER:
            other = True
    return books, other


def extract_refs(reference):
    """All 'صحيح البخاري (v/p) (N)' style citations: [{'book': key, 'number': 'N' or None, 'raw': ...}].
    The number is kept only if the last parentheses hold a pure integer (lists are skipped)."""
    out = []
    for m in REF_PAT.finditer(reference or ''):
        out.append({'book': BOOK_BY_AR[m.group(1)], 'number': hc.pure_integer(m.group(3)), 'raw': m.group(0)})
    return out


def pick_book_number(refs, allowed, want_book=None):
    """Choose (book_key, number) from refs restricted to `allowed` books (Bukhari first)."""
    usable = [r for r in refs if r['book'] in allowed and (want_book in (None, r['book']))]
    usable.sort(key=lambda r: (r['number'] is None, r['book'] != 'bukhari'))
    return (usable[0]['book'], usable[0]['number']) if usable else (None, None)


class Corpus:
    """Offline view of the cache."""

    def __init__(self, cache):
        self.cache = Path(cache)
        self.cats = {'ar': {}, 'en': {}}
        self.members = {}
        self.ar, self.en = {}, {}
        for lang in ('ar', 'en'):
            p = cats_path(self.cache, lang)
            if p.exists():
                for c in json.loads(p.read_text(encoding='utf-8')):
                    self.cats[lang][str(c['id'])] = c
        for p in sorted((self.cache / 'list').glob('*.json')) if (self.cache / 'list').is_dir() else []:
            if p.name.endswith('.meta.json'):
                continue
            cat = p.name.split('.')[0]
            for h in json.loads(p.read_text(encoding='utf-8')).get('data', []):
                self.members.setdefault(cat, set()).add(str(h['id']))
        one = self.cache / 'one'
        for p in sorted(one.glob('*.json')) if one.is_dir() else []:
            if p.name.endswith('.meta.json'):
                continue
            hid, lang = p.name[:-len('.json')].split('.')
            (self.ar if lang == 'ar' else self.en)[hid] = json.loads(p.read_text(encoding='utf-8'))

    def meta(self, hid, lang):
        p = meta_path(one_path(self.cache, hid, lang))
        return json.loads(p.read_text(encoding='utf-8')) if p.exists() else {}

    def raw_ok(self, hid, lang):
        """Re-hash the cached bytes against the sha256 in the meta file."""
        p = one_path(self.cache, hid, lang)
        m = self.meta(hid, lang)
        return bool(m) and p.exists() and hc.sha256_file(p) == m.get('sha256')

    def category_title(self, cat, titles):
        c = self.cats['en'].get(str(cat)) or self.cats['ar'].get(str(cat))
        return (c or {}).get('title') or titles.get(str(cat)) or str(cat)

    def ancestors(self, cat):
        seen, cur = set(), str(cat)
        while cur and cur not in seen:
            seen.add(cur)
            c = self.cats['en'].get(cur) or self.cats['ar'].get(cur) or {}
            cur = str(c['parent_id']) if c.get('parent_id') else ''
        return seen

    def categories_of(self, hid):
        """Every category the hadith is in: its own `categories`, their ancestors, and every
        category whose cached list contains it."""
        out = set()
        rec = self.ar.get(hid) or self.en.get(hid) or {}
        for c in rec.get('categories', []) or []:
            out |= self.ancestors(c)
        for cat, ids in self.members.items():
            if hid in ids:
                out.add(cat)
        return out


def keyword_hits(corpus, hid, keywords_en, keywords_ar):
    """(English hits, Arabic hits). English keywords are tested on the cached English title/text (none
    when the record has no English); Arabic keywords are tested on every record's Arabic title and
    matn after hc.normalize_ar on both sides, so a record without English still matches."""
    ar, en = corpus.ar.get(hid, {}), corpus.en.get(hid, {})
    en_text = ' '.join(str(en.get(k, '')) for k in ('title', 'hadeeth', 'hadeeth_intro')).lower()
    ar_text = hc.normalize_ar(' '.join(str(ar.get(k, '')) for k in ('title', 'hadeeth')))
    # English keywords are word-start stems ("patien" matches "patience"), so "lie" no longer matches "believes".
    en_hits = {k for k in keywords_en if re.search(r'(?<!\w)' + re.escape(k.lower()), en_text)}
    ar_hits = {k for k in keywords_ar if hc.normalize_ar(k) and hc.normalize_ar(k) in ar_text}
    return en_hits, ar_hits


def value_keywords_ar(slug, cfg=None):
    """Arabic keywords for a value: `keywords_ar` in hadeethenc_categories.json when present, else the
    child-voice keywords_ar in content/values.json (weaker, used only for ranking then)."""
    own = ((cfg or {}).get('values', {}).get(slug) or {}).get('keywords_ar')
    if own:
        return own
    try:
        for v in json.loads(hc.VALUES_JSON.read_text(encoding='utf-8')):
            if v['slug'] == slug:
                return v.get('keywords_ar', [])
    except (OSError, ValueError):
        pass
    return []


# Relevance of the way a hadith matched a value (lower is better).
MATCH_ORDER = {'category': 0, 'ar_keyword': 1, 'en_keyword': 2}


def evaluate(corpus, hid, cfg, slug=None, max_words=DEFAULT_MAX_WORDS):
    """Return (candidate dict or None, reject reason). With slug=None only the safety gates run
    (grade, attribution, deny-list); with a slug the value membership is checked too."""
    ar = corpus.ar.get(hid)
    if not ar:
        return None, 'no Arabic record in cache'
    if (ar.get('grade') or '').strip() != GRADE_OK:
        return None, f"grade is not exactly {GRADE_OK}"
    books, other = sahihayn_books(ar.get('attribution', ''))
    if other or not books:
        return None, 'attribution is not Bukhari/Muslim/agreed'
    cats = corpus.categories_of(hid)
    denied = sorted(cats & set(cfg['deny_list']))
    if denied:
        return None, 'deny-list category ' + ','.join(denied)
    words = hc.word_count(ar.get('hadeeth', ''))
    refs = extract_refs(ar.get('reference', ''))
    cand = {'id': hid, 'books': books, 'refs': refs, 'words': words, 'cats': cats,
            'attribution': (ar.get('attribution') or '').strip(),
            'has_en': bool(corpus.en.get(hid, {}).get('hadeeth'))}
    if slug is None:
        return cand, ''
    vcfg = cfg['values'][slug]
    en_hits, ar_hits = keyword_hits(corpus, hid, vcfg.get('keywords_en', []), value_keywords_ar(slug, cfg))
    direct = cats & {str(c) for c in vcfg['categories']}
    kwonly = cats & {str(c) for c in vcfg['keyword_only_categories']}
    if direct:
        cand['category'] = sorted(direct, key=lambda c: [str(x) for x in vcfg['categories']].index(c))[0]
        cand['match'] = 'category'
    elif kwonly and (ar_hits or en_hits):
        cand['category'] = sorted(kwonly)[0]
        cand['match'] = 'ar_keyword' if ar_hits else 'en_keyword'
    else:
        return None, 'not in the value\'s categories' if not kwonly else 'category matches but no keyword'
    cand['kw_hits'] = len(en_hits) + len(ar_hits)
    if words > max_words:
        return None, f'longer than {max_words} words'
    cand['book'], cand['number'] = pick_book_number(refs, books)
    if not cand['book'] and len(books) == 1:
        cand['book'] = next(iter(books))     # one named compiler, no number in the reference
    cand['needs_number'] = cand['number'] is None     # the dorar proof step must read the number off the page
    return cand, ''


# --- pull -------------------------------------------------------------------

def pull(cache, cfg, values, fetcher, refresh=False, prefilter=True, max_ids=None, out=None):
    out = out or sys.stdout
    cache = Path(cache)
    stats = {}
    cats = {str(c) for v in values for c in cfg['values'][v]['categories'] + cfg['values'][v]['keyword_only_categories']}
    deny = set(cfg['deny_list'])
    for lang in ('ar', 'en'):
        cached_get(fetcher, cats_path(cache, lang), f'{BASE}/categories/list/?language={lang}', refresh, stats)
    members = {}
    for cat in sorted(cats | deny, key=int):
        page, last = 1, 1
        while page <= last and page <= 200:
            url = f'{BASE}/hadeeths/list/?language=ar&category_id={cat}&page={page}&per_page=100'
            body = cached_get(fetcher, list_path(cache, cat, page), url, refresh, stats)
            doc = json.loads(body)
            members.setdefault(cat, set()).update(str(h['id']) for h in doc.get('data', []))
            last = int(doc.get('meta', {}).get('last_page', 1) or 1)
            page += 1
    denied_ids = set().union(*(members.get(d, set()) for d in deny)) if deny else set()
    wanted = set().union(*(members.get(c, set()) for c in cats)) if cats else set()
    ids = sorted(wanted - denied_ids, key=int)
    print(f'{len(wanted)} hadith in the mapped categories, {len(wanted & denied_ids)} skipped (deny-list); '
          f'fetching {len(ids)}', file=out)
    if max_ids:
        ids = ids[:max_ids]
    skipped = {'grade': 0, 'attribution': 0, 'no_en': 0, 'missing': 0}
    for n, hid in enumerate(ids, 1):
        try:
            ar = json.loads(cached_get(fetcher, one_path(cache, hid, 'ar'),
                                       f'{BASE}/hadeeths/one/?language=ar&id={hid}', refresh, stats))
        except NotFound:
            skipped['missing'] += 1
            continue
        if prefilter:
            if (ar.get('grade') or '').strip() != GRADE_OK:
                skipped['grade'] += 1
                continue
            books, other = sahihayn_books(ar.get('attribution', ''))
            if other or not books:
                skipped['attribution'] += 1
                continue
        if 'translations' in ar and 'en' not in (ar.get('translations') or []):
            skipped['no_en'] += 1
            continue
        try:
            cached_get(fetcher, one_path(cache, hid, 'en'), f'{BASE}/hadeeths/one/?language=en&id={hid}', refresh, stats)
        except NotFound:
            skipped['no_en'] += 1
        if n % 50 == 0:
            print(f'  {n}/{len(ids)}', file=out)
    print(f'done: {stats.get("fetched", 0)} fetched, {stats.get("cached", 0)} from cache; '
          f'skipped {skipped}', file=out)
    return stats


# --- candidates -------------------------------------------------------------

def rank_key(c):
    """Relevance first (category > Arabic keyword > English keyword), then English available, number
    known, more keyword hits, shorter, id."""
    return (MATCH_ORDER[c['match']], not c['has_en'], c['number'] is None, -c['kw_hits'], c['words'], int(c['id']))


def list_candidates(corpus, cfg, slug, max_words=DEFAULT_MAX_WORDS, require_en=False, require_number=False):
    cands, rejects = [], {}
    ids = set(corpus.ar)
    for hid in sorted(ids, key=int):
        c, why = evaluate(corpus, hid, cfg, slug, max_words)
        if c and require_en and not c['has_en']:
            c, why = None, 'no English'
        if c and require_number and c['number'] is None:
            c, why = None, 'no extractable number'
        if c:
            cands.append(c)
        elif why and not why.startswith('not in the value'):
            rejects[why] = rejects.get(why, 0) + 1
    cands.sort(key=rank_key)
    return cands, rejects


def short_title(corpus, hid, n=48):
    t = (corpus.en.get(hid) or {}).get('title') or (corpus.ar.get(hid) or {}).get('title') or ''
    t = ' '.join(t.split())
    return t if len(t) <= n else t[:n - 1] + '…'


def book_label(c):
    return hc.BOOKS[c['book']]['name'] if c['book'] else None


def first_words(text, n=8):
    """First n words of the saying itself (not the narrator clause), to search dorar.net: the words after the
    opening « when it is within the first 30 words, else after a leading narrator clause, else the start."""
    words = text.split()
    for i, w in enumerate(words[:30]):
        if '«' in w:
            rest = ' '.join(words[i:]).split('«', 1)[1].split()
            if rest:
                return ' '.join(rest[:n])
    stripped, changed = hc.strip_narrator_clause(text)
    return ' '.join((stripped if changed else text).split()[:n])


def json_row(corpus, slug, c):
    """One candidates.json record. Only 8 words of the Arabic text: enough to search dorar.net."""
    ar = corpus.ar[c['id']]
    return {'value': slug, 'hadeethenc_id': c['id'], 'book': book_label(c), 'number': c['number'],
            'needs_number': c['needs_number'], 'grade': (ar.get('grade') or '').strip(),
            'attribution': c['attribution'], 'words': c['words'],
            'first_8_words_ar': first_words(ar.get('hadeeth') or ''),
            'hadeethenc_url': PAGE.format(lang='en' if c['has_en'] else 'ar', id=c['id'])}


def cmd_candidates_all(corpus, cfg, args):
    """Count line per value, plus DIR/candidates.json (or --json-file) with every candidate in rank order."""
    out, total = [], 0
    print(f"{'slug':<22} {'cand':>4} {'numbered':>8} {'needs_number':>12}  flags")
    for slug in cfg['values']:
        cands, _ = list_candidates(corpus, cfg, slug, args.max_words, args.require_en, args.require_number)
        out += [json_row(corpus, slug, c) for c in cands]
        need = sum(c['needs_number'] for c in cands)
        total += len(cands)
        print(f"{slug:<22} {len(cands):>4} {len(cands) - need:>8} {need:>12}  {'<2' if len(cands) < 2 else ''}")
    path = Path(args.json_file) if args.json_file else Path(args.cache) / 'candidates.json'
    hc.write_json(path, out)
    print(f'{total} candidates for {len(cfg["values"])} values -> {path}', file=sys.stderr)
    return 0


def cmd_candidates(args):
    cfg = load_config()
    if args.value != 'all' and args.value not in cfg['values']:
        sys.exit(f'fetch_hadeethenc: unknown value {args.value!r}')
    corpus = Corpus(args.cache)
    if not corpus.ar:
        sys.exit(f'fetch_hadeethenc: no cached records in {args.cache}; run `pull` first (needs network)')
    if args.value == 'all':
        return cmd_candidates_all(corpus, cfg, args)
    cands, rejects = list_candidates(corpus, cfg, args.value, args.max_words, args.require_en, args.require_number)
    cands = cands[:args.limit] if args.limit else cands
    rows = []
    for i, c in enumerate(cands, 1):
        book = book_label(c) or '/'.join(sorted(c['books']))
        rows.append({'n': i, 'id': c['id'], 'book': book, 'number': c['number'] or '?', 'words': c['words'],
                     'en': c['has_en'], 'match': c['match'],
                     'category': f"{c.get('category', '')} {corpus.category_title(c.get('category', ''), cfg['category_titles'])}",
                     'title': short_title(corpus, c['id'])})
    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        print(f"{'#':>3} {'id':>6}  {'book':<17} {'number':>6} {'words':>5} {'en':<3} {'match':<10} {'category':<32} title")
        for r in rows:
            print(f"{r['n']:>3} {r['id']:>6}  {r['book']:<17} {r['number']:>6} {r['words']:>5} "
                  f"{'yes' if r['en'] else 'no':<3} {r['match']:<10} {r['category'][:32]:<32} {r['title']}")
    if args.json_file:
        hc.write_json(args.json_file, [json_row(corpus, args.value, c) for c in cands])
    print(f'{len(rows)} shown; rejected by gate: {rejects or "none"}', file=sys.stderr)
    return 0


# --- draft ------------------------------------------------------------------

def cmd_draft(args):
    cfg = load_config()
    if args.value not in cfg['values'] and args.value not in hc.known_values():
        sys.exit(f'fetch_hadeethenc: unknown value {args.value!r}')
    corpus = Corpus(args.cache)
    hid = str(args.id)
    for lang in ('ar', 'en'):
        if hid in getattr(corpus, lang) and not corpus.raw_ok(hid, lang):
            sys.exit(f'fetch_hadeethenc: cached {lang} JSON for {hid} does not match its recorded sha256')
    cand, why = evaluate(corpus, hid, cfg, None)
    if not cand:
        sys.exit(f'fetch_hadeethenc: id {hid} cannot be drafted: {why}')
    ar, en = corpus.ar[hid], corpus.en.get(hid)
    notes = []
    book, number = pick_book_number(cand['refs'], cand['books'], args.book)
    if args.book:
        book = args.book
    elif not book and len(cand['books']) == 1:
        book = next(iter(cand['books']))
    if args.number:
        number = hc.pure_integer(args.number)
        if not number:
            sys.exit('fetch_hadeethenc: --number must be a plain integer')
    if not book:
        sys.exit('fetch_hadeethenc: cannot tell the book from attribution/reference; pass --book bukhari|muslim')
    if book not in cand['books']:
        sys.exit(f'fetch_hadeethenc: attribution does not include {book}')
    if not number:
        notes.append('number is empty: HadeethEnc gave no extractable number; read it off the dorar page and re-run with --number')

    item = {'type': 'hadith', 'values': [args.value], 'arabic_text': ''}
    dorar = None
    arabic_ok = False
    if args.dorar_file:
        entries = fetch_hadith.parse_file(args.dorar_file)[1]
        usable, rejected = fetch_hadith.candidates(entries, book)
        if not usable:
            sys.exit(f'fetch_hadeethenc: no usable {book} entry in {args.dorar_file} '
                     f'({len(rejected)} rejected: {sorted({r["reject"] for r in rejected})})')
        if args.dorar_pick:
            if not 1 <= args.dorar_pick <= len(usable):
                sys.exit(f'fetch_hadeethenc: --dorar-pick out of range 1..{len(usable)}')
            dorar = usable[args.dorar_pick - 1]
        else:
            equal = [e for e in usable if hc.matn_equal(e['text'], ar.get('hadeeth', ''))[0]]
            same = [e for e in usable if number and e['number'] == number]
            pool = equal or same or (usable if len(usable) == 1 else [])
            if not pool:
                sys.exit(f'fetch_hadeethenc: {len(usable)} entries in {args.dorar_file} and none matches; '
                         f'use --dorar-pick N (numbers as in `fetch_hadith.py --list`)')
            dorar = pool[0]
        problems = fetch_hadith.pick_problems(dorar)
        if problems:
            sys.exit('fetch_hadeethenc: the dorar entry cannot be used: ' + '; '.join(problems))
        if number and dorar['number'] != number:
            notes.append(f"dorar number {dorar['number']} differs from HadeethEnc reference {number}; using dorar's")
        number = dorar['number']
        item['arabic_text'] = dorar['text']
        arabic_ok = True
    else:
        notes.append('arabic_text is EMPTY: copy it from the dorar.net page (re-run with --dorar-file), never from HadeethEnc')

    english = (en or {}).get('hadeeth', '') if en else ''
    include_en = bool(english) and arabic_ok     # never attach English before the matn check can run
    if not english:
        notes.append('no English translation cached for this id: english_text left out')
    elif arabic_ok:
        equal, mode = hc.matn_equal(dorar['text'], ar.get('hadeeth', ''))
        if not equal:
            include_en = False
            notes.append('english_text DROPPED: the dorar matn is not equal to the HadeethEnc Arabic matn after '
                         'removing tashkeel, tatweel, punctuation and whitespace (narrator clause stripped on both '
                         'sides or neither). Compare the two texts by hand; the child explanation can cover it.')
        else:
            notes.append(f'matn check passed ({mode})')
    else:
        notes.append('english_text / translation fields NOT attached: the matn-equality check needs the dorar page. '
                     'Re-run with --dorar-file to attach the English if the matns are equal')
    if include_en:
        item['english_text'] = english
        item['translation_name'] = TRANSLATION_NAME
        item['translation_source_url'] = PAGE.format(lang='en', id=hid)
    item['book'] = hc.BOOKS[book]['name']
    item['number'] = number or ''
    if dorar and dorar['narrator']:
        item['narrator'] = dorar['narrator']
    # Grade, grader and source_url are only proven by the dorar page: empty until --dorar-file.
    item['grade'] = dorar['grade'] if dorar else ''
    item['grader'] = dorar['grader'] if dorar else ''
    item['source_site'] = 'dorar.net'      # the intended site
    item['source_url'] = dorar['source_url'] if dorar else ''
    item['verification_status'] = 'unverified'
    if not dorar:
        notes.append('grade, grader and source_url are EMPTY: only the dorar page proves them (re-run with --dorar-file)')
    elif not item['source_url']:
        notes.append('no dorar.net/h/<id> permalink in the dorar file (share link, canonical link or '
                     '"Source URL: https://dorar.net/h/<id>" header): source_url is empty')
    blob = json.dumps([item], ensure_ascii=False, indent=2) + '\n'
    if args.out:
        Path(args.out).write_text(blob, encoding='utf-8')
        print(f'wrote {args.out}', file=sys.stderr)
    else:
        sys.stdout.write(blob)

    if not args.no_provenance:
        key = hc.label(item['book'], number) if number else f'hadeethenc:{hid}'
        rec = {'hadeethenc_id': hid, 'hadeethenc_url': PAGE.format(lang='en', id=hid),
               'english_included': 'english_text' in item}
        for lang in ('ar', 'en'):
            m = corpus.meta(hid, lang)
            if m:
                rec[f'retrieved_at_{lang}'] = m.get('retrieved_at', '')
                rec[f'sha256_{lang}'] = m.get('sha256', '')
        if dorar:
            rec.update(dorar_file=dorar['file'], dorar_sha256=dorar['file_sha256'],
                       dorar_retrieved=dorar['retrieved'], dorar_source_url=dorar['source_url'])
        path = hc.append_provenance(key, rec, args.provenance)
        notes.append(f'provenance: {key} -> {path}')
    for n in notes:
        print('note: ' + n, file=sys.stderr)
    return 0


def cmd_pull(args):
    cfg = load_config()
    values = resolve_values(args.values, cfg)
    fetcher = Fetcher(gap=args.gap)
    try:
        pull(args.cache, cfg, values, fetcher, args.refresh, not args.no_prefilter, args.max_ids)
    except Blocked as e:
        sys.exit(f'fetch_hadeethenc: HTTP 403 from {e}. Stopping: no retry and no workaround. Check the network '
                 f'or ask the organisers (r1 Q3). Everything already pulled stays in {args.cache}.')
    return 0


def build_parser():
    ap = argparse.ArgumentParser(description='HadeethEnc discovery for hadith items (route H).')
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('pull', help='download categories, lists and records into the cache (network)')
    p.add_argument('--values', default='all', help='all or slug,slug')
    p.add_argument('--cache', default=str(DEFAULT_CACHE))
    p.add_argument('--refresh', action='store_true', help='re-download even if cached')
    p.add_argument('--no-prefilter', action='store_true', help='fetch English for every record')
    p.add_argument('--gap', type=float, default=0.15, help='seconds between requests')
    p.add_argument('--max-ids', type=int, help='stop after N records (testing)')
    p.set_defaults(func=cmd_pull)
    c = sub.add_parser('candidates', help='ranked candidates for one value, or counts + candidates.json for all (offline)')
    c.add_argument('--value', required=True, help='a value slug, or all')
    c.add_argument('--limit', type=int, default=20, help='0 = no limit; not applied to --value all')
    c.add_argument('--max-words', type=int, default=DEFAULT_MAX_WORDS)
    c.add_argument('--require-en', action='store_true')
    c.add_argument('--require-number', action='store_true')
    c.add_argument('--json', action='store_true')
    c.add_argument('--json-file', help='write candidates.json here (default for --value all: DIR/candidates.json)')
    c.add_argument('--cache', default=str(DEFAULT_CACHE))
    c.set_defaults(func=cmd_candidates)
    d = sub.add_parser('draft', help='draft item JSON for one HadeethEnc id (offline)')
    d.add_argument('--id', required=True)
    d.add_argument('--value', required=True)
    d.add_argument('--dorar-file')
    d.add_argument('--dorar-pick', type=int)
    d.add_argument('--book', choices=sorted(hc.BOOKS))
    d.add_argument('--number')
    d.add_argument('--out')
    d.add_argument('--no-provenance', action='store_true')
    d.add_argument('--provenance', help=argparse.SUPPRESS)
    d.add_argument('--cache', default=str(DEFAULT_CACHE))
    d.set_defaults(func=cmd_draft)
    return ap


def main(argv=None):
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
