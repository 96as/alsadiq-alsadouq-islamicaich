#!/usr/bin/env python3
"""Extract FAQ items from the Bayyinat PDF (dawa.center/file/7937), kept local.

The PDF's text layer is broken (ligature halves as zero-width letters, spaces drawn over
letters, honorific signs in a symbol font, verses in King Fahd page fonts that carry no
text), so plain pdftotext is not enough. This tool rebuilds every line from glyph positions
with PyMuPDF (`pip install pymupdf`), right to left. The PDF, its text and the page cache
stay in the gitignored tools/.cache/; only the short excerpt of an item is committed.
Nothing is fetched from the network.

Usage:
  python3 extract_faq.py toc PDF [--grep WORD] [--toc-pages N]
      Print the table of contents: "n<TAB>title<TAB>printed page" (and section lines).
      The printed pages in the TOC drift from the page headers (by 22 pages at the end of
      the book), so they are informational: questions are located by counting السؤال
      labels through the book, and the TOC only supplies the title.
  python3 extract_faq.py question PDF N [--render DIR] [--full]
      Show question N block by block (السؤال / عبارات مشابهة للسؤال / مضمون السؤال /
      مختصر الإجابة / الجواب التفصيلي) as numbered paragraphs with the printed page.
      --render DIR also writes DIR/qNNN.txt and one PNG per PDF page, so the lead can
      compare honorifics and paragraph breaks against the printed page.
  python3 extract_faq.py draft PDF N --value SLUG [--paras A-B] [--age-band all|6-9|10-13]
        [--related verse:S:A ...] [--allow-dropped-symbols] [--keep-tashkeel] [--out FILE.json]
      Write a faq item: title_ar = the question, keywords_ar = the similar wordings,
      arabic_text = the chosen paragraphs of مختصر الإجابة (default: all, at most 3),
      number "Q<n> · p.<printed>", source_url https://dawa.center/file/7937#p<printed>
      (#p<printed>-q<n> when another question starts on that PDF page), related only for
      `[surah: ayah]` references whose verse is already in items/*.json.
      A paragraph with verse glyphs has "holes" (the PDF carries no text for them): the
      draft is refused unless every hole gets a bank verse via --related verse:S:A (in
      reading order), and then the hole becomes the machine marker {{verse:S:A}} that the
      runtime fills from the bank. No verse text is ever typed by a human.
      Tashkeel is stripped from the draft (title, keywords, text): the PDF places every
      mark by position only, so a mark can land one letter off, and an unverified mark
      must not be stored as if verbatim. The base letters are what the reviewer checks
      against the page. --keep-tashkeel keeps the marks; the review must then check each.
      When the page prints no question under السؤال, title_ar is the TOC title (warned).
      When the question text is longer than 200 characters (the bank's title_ar limit), or
      has a verse hole, verse marks or a dropped honorific, title_ar is the TOC title too
      (warned); a similar wording with a verse hole is dropped from keywords_ar (warned).
      Known text-layer loss: a lam-alef ligature carrying a mark comes out as the lam
      alone. Where that is certain (لًا at a word end; a standalone لَا, أَلَّا, إِلَّا, وَلَا,
      بِلَا token) the alef is restored and flagged; inside a longer vocalised word it stays
      lost. An alef right before a lam-alef ligature (الادعاء, الاختبار) is dropped by the
      text layer as a duplicate glyph; it is restored from the page's glyph trace, where it
      still is, and flagged the same way. The reviewer reads the excerpt against the page
      in any case.
  python3 extract_faq.py glyphs PDF PDF_PAGE
      Diagnostics for one PDF page (1-based): fonts, multi-character glyphs, dropped
      glyphs, digit glyphs per font and colour. Use it to tune --verse-font /
      --symbol-font / LIGATURE_FIX / BULLET_GLYPHS on the real file.

Common options: --verse-font REGEX (fonts whose glyphs are verse shapes, default
QCF\\d*_Hafs, the King Fahd Complex page fonts), --symbol-font REGEX (honorific/ornament
fonts; KFGQPCArabicSymbols01 holds the honorific signs), --cache-dir DIR, --items-dir DIR.

What it does on purpose: verse glyphs are never turned into text (see the holes above);
symbol-font glyphs (honorifics) are dropped, the paragraph is flagged "sym", and `draft`
refuses it unless --allow-dropped-symbols is passed after the lead has restored them
against `question --render`; the review note must then say so. The Prophet's ﷺ glyph
(U+FDFA in a text font) folds to its words and is kept. Digit-only lines in the bottom 10%
(footer page numbers) are dropped, and a year in the header is not taken as the printed
page. A lone الجواب heading closes the block before it (nothing is read until the next
label). The book's ❋ list marker (drawn as a coloured digit of the heading font) becomes a
bullet, which splits the similar wordings and starts paragraphs; a numbered marker "1)" (the
text layer labels its glyphs in the wrong order, ")1", and the glyph trace puts them right)
starts a paragraph too, while a "-:" is punctuation, not a marker.
"""
import argparse
import hashlib
import json
import re
import statistics
import sys
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import draft_from_page as dfp  # noqa: E402  (shared helpers: age screen, bank verses)

FILE_URL = 'https://dawa.center/file/7937'
BOOK = 'بينات: أسئلة وأجوبة عن الإسلام'
CACHE = HERE / '.cache' / 'faq'
VERSE_FONT_RE = r'QCF\d*_Hafs'      # King Fahd Complex page fonts (QCF4_Hafs_01 ...), no text
SYMBOL_FONT_RE = r'symbol|dingbat|wingding|ornament|KFGQPC'   # honorific signs, no text

LABELS = [
    ('question', 'السؤال'),
    ('similar', 'عبارات مشابهة للسؤال'),
    ('gist', 'مضمون السؤال'),
    ('short', 'مختصر الإجابة'),
    ('detailed', 'الجواب التفصيلي'),
]
HEADINGS = ('الجواب',)        # box headings with no block of their own: they close the block before
# Glyph strings (one glyph, several characters) whose extracted order is known to be wrong.
# Filled in against the real file with the `glyphs` command; plain Arabic multi-character
# glyphs not listed here are reversed (the usual lam-alef style ligature swap).
LIGATURE_FIX = {}
# (font name part, char, fill colour hex) of glyphs that are list markers, not text. Bayyinat
# draws its ❋ as the digit 3 of the heading font in the ornament colour (the page numbers in
# the same font are black). Tune with `glyphs` (digit glyphs by font and colour).
BULLET_GLYPHS = {('Manal', '3', '8d2f45')}

TERMINAL = '.!؟?:؛'
TITLE_MAX = 200               # ContentItem.title_ar max_length
VERSE_HOLE = '⟦VERSE_HOLE⟧'   # machine placeholder where verse glyphs were (the PDF has no text for them)
BULLET = re.compile(r'^\s*(?:[-•–*·▪●○](?![:؛،])|\(?\d{1,2}[).\-]|[٠-٩]{1,2}[).\-])\s*')   # "-:" is punctuation
TASHKEEL = re.compile('[ً-ٰٟـۖ-ۭ]')   # harakat, tatweel, Quranic signs
# The text layer maps a lam-alef ligature that carries a mark to the lam alone (906 lams with
# fathatan in the book, none followed by its alef; the same for لَا, أَلَّا, إِلَّا, وَلَا, بِلَا
# in vocalised text). A lam with fathatan at the end of a word, and a standalone token that is
# a bare marked lam with at most a و/ف/ب and أ/إ prefix, can only be such a ligature, so the
# alef is restored there and flagged. A lost alef inside a longer vocalised word (الْأَذْهَان)
# is not detectable and stays lost: the reviewer reads the excerpt against the page.
MARK, VOWEL = '[\u064b-\u0652]', '[\u064b-\u0651]'     # VOWEL: no sukun, بَلْ / أَلْ are words
LOST_ALEF = re.compile(f'(?:(?<![\u0621-\u0652ـ])(?:[وفب]{MARK}*)?(?:[أإ]{MARK}*)?ل{VOWEL}+'
                       f'|لً{VOWEL}*)(?![\u0621-\u0652ـ])')
RESTORED_ALEF = re.compile(f'ل{VOWEL}+ا(?![\u0621-\u0652ـ])')   # only this tool writes these
DIGITS_AR = dfp.DIGITS_AR
SURAH_NAMES, SURAH_ALIASES = dfp.SURAH_NAMES, dfp.SURAH_ALIASES
norm, surah_number, verse_refs = dfp.norm, dfp.surah_number, dfp.verse_refs

def fail(msg):
    sys.exit(f'extract_faq: {msg}')


def warn(msg):
    print(f'WARNING: {msg}', file=sys.stderr)


def need_pymupdf():
    try:
        import pymupdf
    except ImportError:
        fail('PyMuPDF is missing: pip install pymupdf')
    return pymupdf


# ---------------------------------------------------------------- glyphs and lines

class Glyph:
    __slots__ = ('c', 'x0', 'y0', 'x1', 'y1', 'size', 'font', 'kind', 'restored')

    def __init__(self, c, x0, y0, x1, y1, size=10.0, font='', kind='text', restored=False):
        self.c, self.x0, self.y0, self.x1, self.y1 = c, x0, y0, x1, y1
        self.size, self.font, self.kind = size, font, kind
        self.restored = restored          # recovered from the glyph trace, flag it

    @property
    def xc(self):
        return (self.x0 + self.x1) / 2

    @property
    def yc(self):
        return (self.y0 + self.y1) / 2


def is_mark(c):
    return bool(c) and all(unicodedata.category(ch) in ('Mn', 'Me') for ch in c)


def is_digit(c):
    return len(c) == 1 and (c.isdigit() or c in '٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹')


def is_ltr(c):
    return len(c) == 1 and ((c.isascii() and c.isalnum()) or is_digit(c))


def is_junk(c):
    return (not c or '' <= c[0] <= '' or c[0] == '�'
            or unicodedata.category(c[0]) in ('Cc', 'Cn', 'Co', 'Cs')) and c not in ('\t',)


def fix_glyph_text(c):
    """Text of one glyph: presentation forms folded, reversed multi-char ligatures fixed."""
    if c in LIGATURE_FIX:
        return LIGATURE_FIX[c]
    if len(c) > 1:
        if any('ﭐ' <= ch <= 'ﻼ' for ch in c):
            return unicodedata.normalize('NFKC', c)
        if all('ء' <= ch <= 'ي' for ch in c):
            return c[::-1]
        return c
    if 'ﭐ' <= c <= 'ﻼ':
        return unicodedata.normalize('NFKC', c)
    return c


def classify(c, font, verse_re, symbol_re):
    if verse_re.search(font or ''):
        return 'verse'
    if symbol_re.search(font or '') or is_junk(c):
        return 'sym'
    return 'text'


def is_bullet(font, c, color):
    return any(f in (font or '') and c == ch and f'{color or 0:06x}' == col
               for f, ch, col in BULLET_GLYPHS)


def is_ascii(c):
    return len(c) == 1 and ' ' <= c <= '~'


def trace_glyphs(page):
    """Full-width glyphs of the page's text trace, keyed by round(x0, 1): [(c, bbox, size)].
    The trace has one entry per drawn glyph with that glyph's own box and the first code point
    of its text, so it says which character sits where; the rawdict that the rest of the tool
    reads (the only output with every code point of a ligature) mislabels two kinds of glyph
    in this PDF, which page_glyphs corrects against the trace."""
    by = {}
    for sp in (page.get_texttrace() if hasattr(page, 'get_texttrace') else []):
        for uni, _gid, _origin, bbox in sp.get('chars', []):
            if bbox[2] - bbox[0] > 0.01:
                by.setdefault(round(bbox[0], 1), []).append((chr(uni), bbox, sp.get('size', 10.0)))
    return by


def trace_at(by, x0, yc, size):
    """The traced glyph drawn at x0 on the line around yc, or None."""
    k = round(x0, 1)
    for kk in (k - 0.1, k, k + 0.1):
        for t in by.get(round(kk, 1), []):
            if abs((t[1][1] + t[1][3]) / 2 - yc) < 0.6 * size:
                return t
    return None


def _relabel_ascii(d, by):
    """Digits, spaces and brackets of one visual row get their characters from the trace when
    the rawdict only permuted them: the text layer labels a list marker's glyphs as ")1 " while
    the trace shows "1" drawn right of ")" and the space left of it, i.e. "1) ". The rawdict
    splits such a row into several lines, so rows are regrouped by baseline here."""
    chars = []
    for b in d.get('blocks', []):
        for ln in b.get('lines', []):
            for sp in ln.get('spans', []):
                for ch in sp.get('chars', []):
                    if (is_ascii(ch['c']) and ch['bbox'][2] - ch['bbox'][0] > 0.01
                            and not is_bullet(sp.get('font', ''), ch['c'], sp.get('color'))):
                        chars.append((ch, (ch['bbox'][1] + ch['bbox'][3]) / 2, sp.get('size', 10.0)))
    chars.sort(key=lambda t: t[1])
    row = []
    for ch, yc, size in chars + [(None, None, None)]:
        if row and (ch is None or yc - row[-1][1] > 0.5 * row[-1][2]):
            traced = [trace_at(by, c['bbox'][0], y, sz) for c, y, sz in row]
            if (len(row) > 1 and all(t and is_ascii(t[0]) for t in traced)
                    and sorted(c['c'] for c, _, _ in row) == sorted(t[0] for t in traced)):
                for (c, _, _), t in zip(row, traced):
                    c['c'] = t[0]
            row = []
        row.append((ch, yc, size))


def _dropped_letters(d, by):
    """Alefs the rawdict dropped as duplicates: a lam-alef ligature is unpacked into a hidden
    zero-width alef at the carrier lam's right edge, and an alef drawn right there (الا...) is
    then taken for the same glyph twice. The trace still has it: -> [(c, bbox, size)]. Only
    that shape is restored: a traced full-width alef, a zero-width rawdict alef at its x0 on
    the same line, a full-width rawdict lam ending at that x0, and no full-width alef there."""
    zero, lam, full = {}, {}, {}
    for b in d.get('blocks', []):
        for ln in b.get('lines', []):
            for sp in ln.get('spans', []):
                for ch in sp.get('chars', []):
                    x0, y0, x1, y1 = ch['bbox']
                    if x1 - x0 <= 0.01:
                        if ch['c'] == 'ا':
                            zero.setdefault(round(x0, 1), []).append((y0 + y1) / 2)
                    elif ch['c'] == 'ا':
                        full.setdefault(round(x0, 1), []).append((y0 + y1) / 2)
                    elif ch['c'] == 'ل':
                        lam.setdefault(round(x1, 1), []).append((y0 + y1) / 2)
    out, seen = [], set()
    for ts in by.values():
        for c, bbox, size in ts:
            if c != 'ا':
                continue
            x0, yc = round(bbox[0], 1), (bbox[1] + bbox[3]) / 2
            key = (x0, round(yc))
            same_line = lambda ys: any(abs(y - yc) < 0.6 * size for y in ys)
            if key in seen or same_line(full.get(x0, [])):
                continue
            if not (same_line(zero.get(x0, [])) and same_line(lam.get(x0, []))):
                continue
            seen.add(key)
            out.append((c, bbox, size))
    return out


def page_glyphs(page, verse_re, symbol_re):
    """Glyphs of a page in stream order. A ligature (lam-alef, الله) comes out of this PDF as
    zero-width letters followed by one full-width carrier letter: the carrier is read first,
    the hidden letters after it in reverse stream order, and the glyph's box is split into
    slots so that the letters sort right to left like any other text. Two rawdict defects are
    corrected against the page's glyph trace: permuted labels of digits and brackets
    (_relabel_ascii) and letters dropped as duplicates (_dropped_letters, flagged)."""
    d = page.get_text('rawdict')
    by = trace_glyphs(page)
    if by:
        _relabel_ascii(d, by)
    out = []
    for b in d.get('blocks', []):
        for ln in b.get('lines', []):
            for sp in ln.get('spans', []):
                font, size, color = sp.get('font', ''), sp.get('size', 10.0), sp.get('color')
                pending = []                     # zero-width letters waiting for their carrier
                for ch in sp.get('chars', []):
                    x0, y0, x1, y1 = ch['bbox']
                    c = ch['c']
                    if is_bullet(font, c, color):
                        c = '•'
                    kind = classify(c, font, verse_re, symbol_re)
                    g = Glyph(fix_glyph_text(c) if kind == 'text' else c,
                              x0, y0, x1, y1, size, font, kind)
                    letter = kind == 'text' and c != ' ' and not is_mark(c)
                    if letter and x1 - x0 < 0.01:
                        pending.append(g)
                        continue
                    if kind == 'text' and is_mark(c):   # marks never break a ligature group
                        out.append(g)
                        continue
                    if pending:
                        if letter and abs(x1 - pending[0].x0) < 0.05 * size:
                            group = [g] + pending[::-1]
                            w = (x1 - x0) / len(group)
                            for k, m in enumerate(group):   # slots, right to left
                                m.x1, m.x0 = x1 - k * w, x1 - (k + 1) * w
                            out.extend(group)
                            pending = []
                            continue
                        out.extend(pending)
                        pending = []
                    out.append(g)
                out.extend(pending)
    for c, (x0, y0, x1, y1), size in (_dropped_letters(d, by) if by else []):
        out.append(Glyph(c, x0, y0, x1, y1, size, '', 'text', restored=True))
    return out


class TextLine:
    def __init__(self, text, x0, x1, yc, size, n_sym=0, n_verse=0, n_alef=0):
        self.text, self.x0, self.x1, self.yc, self.size = text, x0, x1, yc, size
        self.n_sym, self.n_verse, self.n_alef = n_sym, n_verse, n_alef   # n_alef: restored letters
        self.page = None
        self.printed = None
        self.first_on_page = False

    def to_dict(self):
        return {k: getattr(self, k) for k in
                ('text', 'x0', 'x1', 'yc', 'size', 'n_sym', 'n_verse', 'n_alef')}


def _group_rows(bases, tol):
    rows = []
    for g in sorted(bases, key=lambda g: g.yc):
        if rows and g.yc - rows[-1]['yc'] <= tol:
            r = rows[-1]
            r['g'].append(g)
            r['yc'] = sum(x.yc for x in r['g']) / len(r['g'])
        else:
            rows.append({'yc': g.yc, 'g': [g]})
    return rows


def _row_text(row_glyphs, marks_by_base, size):
    """Right-to-left text of one row: drop overlapped spaces, add gap spaces, fix LTR runs."""
    letters = [g for g in row_glyphs if g.c != ' ' and g.kind == 'text']
    spaces = [g for g in row_glyphs if g.c == ' ']
    kept_spaces = []
    for s in spaces:
        over = any(l.x0 + 0.15 * (l.x1 - l.x0) < s.xc < l.x1 - 0.15 * (l.x1 - l.x0)
                   for l in letters if (l.x1 - l.x0) > 0)
        if not over:
            kept_spaces.append(s)
    items = [(g.xc, g.x0, g.x1, g.c + ''.join(marks_by_base.get(id(g), []))) for g in letters]
    items += [(s.xc, s.x0, s.x1, ' ') for s in kept_spaces]
    items += [(g.xc, g.x0, g.x1, '\x00V') for g in row_glyphs if g.kind == 'verse']
    items.sort(key=lambda t: (-t[0]))
    pieces = []
    prev_x0 = None
    for xc, x0, x1, t in items:
        if prev_x0 is not None and t != ' ' and pieces and pieces[-1] != ' ':
            if prev_x0 - x1 > 0.25 * size:       # visible gap but no space glyph
                pieces.append(' ')
        pieces.append(t)
        prev_x0 = x0 if t != ' ' else prev_x0
    # collapse double spaces
    text_pieces = []
    for p in pieces:
        if p == ' ' and text_pieces and text_pieces[-1] == ' ':
            continue
        if p == '\x00V':                       # verse glyphs: one hole per run
            while text_pieces and text_pieces[-1] == ' ':
                text_pieces.pop()
            if text_pieces and text_pieces[-1] == VERSE_HOLE:
                continue
            if text_pieces:
                text_pieces.append(' ')
            p = VERSE_HOLE
        text_pieces.append(p)
    # numbers and Latin words read left to right: reverse such runs
    out, i = [], 0
    while i < len(text_pieces):
        if is_ltr(text_pieces[i][:1]) and len(text_pieces[i]) == 1:
            j = i
            while j < len(text_pieces) and (
                    (len(text_pieces[j]) == 1 and is_ltr(text_pieces[j]))
                    or (text_pieces[j] in '.,:/' and 0 < j < len(text_pieces) - 1
                        and is_ltr(text_pieces[j - 1]) and is_ltr(text_pieces[j + 1][:1]))):
                j += 1
            out.extend(reversed(text_pieces[i:j]))
            i = j
        else:
            out.append(text_pieces[i])
            i += 1
    return ''.join(out).strip()


def rebuild_lines(glyphs, size_hint=None):
    """Rebuild visual lines (top to bottom) from glyphs: right to left within a line."""
    if not glyphs:
        return []
    bases = [g for g in glyphs if not (g.kind == 'text' and is_mark(g.c))]
    marks = [g for g in glyphs if g.kind == 'text' and is_mark(g.c)]
    sizes = [g.size for g in bases if g.kind != 'sym'] or [10.0]
    size = size_hint or statistics.median(sizes)
    rows = _group_rows([g for g in bases], 0.5 * size)
    marks_by_base = {}
    dropped = 0
    for m in marks:
        # This PDF draws a mark with zero width exactly at the left edge of its base, which is
        # also the right edge of the next letter: match the edge first, nearest glyph otherwise.
        best, best_d = None, None
        zero_width = m.x1 - m.x0 < 0.01
        for r in rows:
            if abs(m.yc - r['yc']) > 1.6 * size:
                continue
            for g in r['g']:
                if g.c == ' ' or g.kind != 'text':
                    continue
                if zero_width and abs(g.x0 - m.x0) <= 0.05 * size:
                    d = abs(g.x0 - m.x0)
                else:
                    d = 1.0 + (0.0 if g.x0 <= m.xc <= g.x1
                               else min(abs(m.xc - g.x0), abs(m.xc - g.x1)))
                d += abs(m.yc - r['yc']) * 0.01
                if best_d is None or d < best_d:
                    best, best_d = g, d
        if best is None or best_d > size:
            dropped += 1
            continue
        marks_by_base.setdefault(id(best), []).append(m.c)
    lines = []
    for r in rows:
        gl = r['g']
        text = LOST_ALEF.sub(r'\g<0>ا', _row_text(gl, marks_by_base, size))
        n_sym = sum(1 for g in gl if g.kind == 'sym')
        n_verse = sum(1 for g in gl if g.kind == 'verse')
        real = [g for g in gl if g.kind == 'text' and g.c != ' ']
        xs0 = [g.x0 for g in (real or gl)]
        xs1 = [g.x1 for g in (real or gl)]
        lines.append(TextLine(text, min(xs0), max(xs1), r['yc'],
                              statistics.median([g.size for g in gl]), n_sym, n_verse,
                              sum(1 for g in gl if g.restored)))
    return [l for l in lines if l.text or l.n_verse]


def to_int(text):
    t = text.translate(DIGITS_AR)
    t = re.sub(r'[^\d]', '', t)
    return int(t) if t else None


def plausible_page(n):
    """A printed page number; years (Hijri 13xx-14xx, Gregorian 19xx-20xx) are not page numbers."""
    return n is not None and not (1300 <= n <= 1500 or 1900 <= n <= 2100)


def split_header(lines, page_height):
    """Return (body lines, printed page or None, header text). The running header is the
    small-font text in the top band; the printed page number is its digit-only line.
    Digit-only lines in the bottom band (footer page numbers) are dropped from the body."""
    if not lines:
        return lines, None, ''
    body_size = statistics.median([l.size for l in lines])
    band = page_height * 0.10
    digits = r'\W*[\d٠-٩۰-۹]+\W*'
    header = [l for l in lines if l.yc < band and (l.size < 0.9 * body_size
                                                    or re.fullmatch(digits, l.text))]
    footer = [l for l in lines if l.yc > page_height - band and re.fullmatch(digits, l.text)]
    printed = None
    for l in sorted(header, key=lambda l: l.size):
        if re.fullmatch(digits, l.text) and plausible_page(to_int(l.text)):
            printed = to_int(l.text)
            break
    if printed is None:
        for l in header:                                  # number mixed into header text
            for m in re.finditer(r'(?<!\d)([\d٠-٩۰-۹]{1,4})(?!\d)', l.text):
                if plausible_page(to_int(m.group(1))):
                    printed = to_int(m.group(1))
                    break
            if printed is not None:
                break
    body = [l for l in lines if l not in header and l not in footer]
    return body, printed, ' '.join(l.text for l in header)


# ---------------------------------------------------------------- page reader and cache

class Reader:
    def __init__(self, pdf, verse_font=VERSE_FONT_RE, symbol_font=SYMBOL_FONT_RE,
                 cache_dir=None, use_cache=True):
        self.pymupdf = need_pymupdf()
        self.pdf = Path(pdf)
        if not self.pdf.exists():
            fail(f'{pdf}: no such file')
        self.doc = self.pymupdf.open(str(self.pdf))
        self.verse_re = re.compile(verse_font, re.I)
        self.symbol_re = re.compile(symbol_font, re.I)
        st = self.pdf.stat()
        sig = hashlib.sha1(f'v9:{st.st_size}:{st.st_mtime_ns}:{verse_font}:{symbol_font}:'
                           f'{sorted(LIGATURE_FIX.items())}:{sorted(BULLET_GLYPHS)}'
                           .encode()).hexdigest()[:12]
        self.cache = (Path(cache_dir) if cache_dir else CACHE) / f'{self.pdf.stem}-{sig}'
        self.use_cache = use_cache
        self._mem = {}

    def __len__(self):
        return len(self.doc)

    def page(self, i):
        """-> (body TextLines with .page/.printed set, printed, header)"""
        if i in self._mem:
            return self._mem[i]
        f = self.cache / f'p{i + 1:04d}.json'
        if self.use_cache and f.exists():
            d = json.loads(f.read_text(encoding='utf-8'))
            body = []
            for x in d['lines']:
                t = TextLine(x['text'], x['x0'], x['x1'], x['yc'], x['size'], x['n_sym'],
                             x['n_verse'], x.get('n_alef', 0))
                body.append(t)
            printed, header = d['printed'], d['header']
        else:
            pg = self.doc[i]
            lines = rebuild_lines(page_glyphs(pg, self.verse_re, self.symbol_re))
            body, printed, header = split_header(lines, pg.rect.height)
            if self.use_cache:
                self.cache.mkdir(parents=True, exist_ok=True)
                f.write_text(json.dumps({'lines': [l.to_dict() for l in body],
                                         'printed': printed, 'header': header},
                                        ensure_ascii=False), encoding='utf-8')
        for n, l in enumerate(body):
            l.page, l.printed, l.first_on_page = i, printed, n == 0
        self._mem[i] = (body, printed, header)
        return self._mem[i]

    def question_labels(self):
        """[(pdf index, line index)] of every السؤال label in reading order, cached next to
        the page cache. Question n is the n-th entry (the TOC's printed pages drift)."""
        f = self.cache / 'labels.json'
        if self.use_cache and f.exists():
            return [tuple(x) for x in json.loads(f.read_text(encoding='utf-8'))]
        labels = [(i, k) for i in range(len(self.doc))
                  for k, l in enumerate(self.page(i)[0]) if is_question_label(l.text)]
        if self.use_cache:
            self.cache.mkdir(parents=True, exist_ok=True)
            f.write_text(json.dumps(labels), encoding='utf-8')
        return labels


# ---------------------------------------------------------------- labels, TOC, paragraphs

def match_label(text):
    """Block label of a line ('heading' for a bare الجواب box), or None. A label may carry a
    question number: السؤال (57)."""
    t = norm(text)
    t = re.sub(r'[\d]+$', '', t.translate(DIGITS_AR)).strip()
    for key, label in LABELS:
        if t == norm(label):
            return key
    if any(t == norm(h) for h in HEADINGS):
        return 'heading'
    return None


def is_question_label(text):
    return bool(text) and (match_label(text) == 'question'
                           or split_inline_label(text)[0] == 'question')


def split_inline_label(text):
    """'السؤال: ما ...' on one visual line -> ('question', 'ما ...'), else (None, text)."""
    m = re.match(r'^(.{3,30}?)\s*[:：]\s*(\S.*)$', text)
    if m:
        key = match_label(m.group(1))
        if key:
            return key, m.group(2)
    return None, text


def label_number(text):
    m = re.search(r'(\d+)', text.translate(DIGITS_AR))
    return int(m.group(1)) if m else None


# An entry is "(n)- title ..... page" / "(n): title ..... page"; the bracket is required so
# that the running header "4 بينات - ..." on the TOC pages is not read as entry 4.
TOC_END = re.compile(r'(?<=\D)[\s.…·_\-]*([\d٠-٩۰-۹]{1,4})\s*$')
TOC_START = re.compile(r'^[(\[]\s*([\d٠-٩۰-۹]{1,3})\s*[)\]]\s*[-–:：]?\s*(?=\S)')
TOC_SECTION = re.compile(r'^(?:اولا|ثانيا|ثالثا|رابعا|خامسا|سادسا|سابعا|ثامنا|تاسعا|عاشرا)\b')
TOC_SUBSECTION = re.compile(r'^[\d٠-٩۰-۹]{1,2}\s*[-–]\s*\S')     # "1- توحيد الربوبية"


def parse_toc_lines(lines):
    """lines: list of strings in reading order -> (entries, sections).
    entries: [{'n', 'title', 'page'}]; sections: [(index into entries, text)]."""
    entries, sections, buf = [], [], None
    for raw in lines:
        t = raw.strip()
        if not t:
            continue
        end = TOC_END.search(t)
        start = TOC_START.match(t)
        if start and (buf is None or end):
            buf = {'n': to_int(start.group(1)), 'parts': [t[start.end():]]}
        elif buf is not None:
            buf['parts'].append(t)
        elif TOC_SECTION.match(norm(t)) or TOC_SUBSECTION.match(t) or t.startswith(('-', '–')):
            sections.append((len(entries), TOC_END.sub('', t).rstrip(' .…·_-')))
            continue
        else:
            continue
        if end and buf is not None:
            joined = ' '.join(buf['parts'])
            e = TOC_END.search(joined)
            title = joined[:e.start()].strip(' .…·_-') if e else joined
            entries.append({'n': buf['n'], 'title': title, 'page': to_int(end.group(1))})
            buf = None
    return entries, sections


def find_toc(reader, max_pages=60):
    entries, sections, found = [], [], False
    for i in range(min(len(reader), max_pages)):
        body = reader.page(i)[0]
        texts = [l.text for l in body]
        hits = sum(1 for t in texts if TOC_END.search(t) and TOC_START.match(t))
        if hits >= 3:
            found = True
            e, s = parse_toc_lines(texts)
            sections += [(k + len(entries), t) for k, t in s]
            entries += e
        elif found:
            break
    return entries, sections


def _with_text(l, text):
    c = TextLine(text, l.x0, l.x1, l.yc, l.size, l.n_sym, l.n_verse, l.n_alef)
    c.page, c.printed, c.first_on_page = l.page, l.printed, l.first_on_page
    return c


def build_paragraphs(lines):
    """lines: TextLines in reading order (across pages) -> dict block -> [paragraph dicts].
    Starts at the first السؤال label and stops at the next one (the next question)."""
    blocks = {k: [] for k, _ in LABELS}
    block, cur, prev, q_seen, number = None, None, None, 0, None
    by_page = {}
    for l in lines:
        by_page.setdefault(l.page, []).append(l)
    spacing, right = {}, {}
    for pg, ls in by_page.items():
        ys = [b.yc - a.yc for a, b in zip(ls, ls[1:]) if b.yc > a.yc]
        spacing[pg] = statistics.median(ys) if ys else 20.0
        right[pg] = max(l.x1 for l in ls)

    def flush():
        nonlocal cur
        if cur is not None:
            cur['text'] = ' '.join(cur.pop('parts')).strip()
            blocks[cur['block']].append(cur)
        cur = None

    for l in lines:
        label, inline, num = (match_label(l.text) if l.text else None), False, None
        if label:
            num = label_number(l.text)
        elif l.text:
            label, rest = split_inline_label(l.text)
            if label:
                inline, l = True, _with_text(l, rest)
        if label:
            flush()
            prev = None
            if label == 'question':
                q_seen += 1
                if q_seen == 2:
                    break
                number = num
            block = None if label == 'heading' else label
            if not inline:
                continue
        if block is None:
            continue
        if not l.text:
            continue
        starts = BULLET.match(l.text) is not None
        # the lines after a bullet hang by the bullet's width: that is not a new paragraph
        indented = right[l.page] - l.x1 > 1.2 * l.size and not (cur and cur['bullet'])
        if cur is None:
            new = True
        elif prev is not None and prev.page != l.page:
            new = prev.text[-1:] in TERMINAL or starts or indented
        else:
            new = (l.yc - prev.yc > 1.45 * spacing[l.page]) or starts or indented
        if block == 'similar' and cur is not None and starts:
            new = True
        if new:
            flush()
            cur = {'block': block, 'parts': [], 'page': l.page, 'printed': l.printed,
                   'sym': 0, 'verse': 0, 'alef': 0, 'span': set(), 'bullet': starts}
        cur['span'].add((l.page, l.printed))
        cur['parts'].append(BULLET.sub('', l.text) if block == 'similar' and starts else l.text)
        cur['sym'] += l.n_sym
        cur['verse'] += l.n_verse
        cur['alef'] += l.n_alef
        prev = l
    flush()
    return blocks, number


def locate_question(reader, n, entries, max_pages=40):
    """-> (lines in reading order from question n's السؤال label on, toc entry or None).
    Question n is the n-th السؤال label of the book; the TOC only supplies the title."""
    entry = next((e for e in entries if e['n'] == n), None)
    labels = reader.question_labels()
    if not 1 <= n <= len(labels):
        fail(f'question {n} not found: the book has {len(labels)} السؤال labels')
    start = labels[n - 1][0]
    # earlier questions that start on the same PDF page come first on it
    skip = sum(1 for p, _ in labels[:n - 1] if p == start)
    lines, seen_label = [], False
    for i in range(start, min(start + max_pages, len(reader))):
        for l in reader.page(i)[0]:
            if not seen_label:
                if is_question_label(l.text):
                    if skip:
                        skip -= 1
                        continue
                    seen_label = True
                else:
                    continue
            lines.append(l)
        if seen_label:
            # stop once a second question label has been collected
            if sum(1 for l in lines if is_question_label(l.text)) >= 2:
                break
    if not seen_label:
        fail(f'no السؤال label found from PDF page {start + 1} on')
    return lines, entry


def get_question(reader, n, toc_pages=60):
    entries, _ = find_toc(reader, toc_pages)
    if entries and len(entries) != len(reader.question_labels()):
        warn(f'the TOC lists {len(entries)} questions but the book has '
             f'{len(reader.question_labels())} السؤال labels; titles may be off by one')
    lines, entry = locate_question(reader, n, entries)
    blocks, num = build_paragraphs(lines)
    q_text = ' '.join(p['text'] for p in blocks['question'])
    if num is not None and num != n:
        warn(f'the page says question {num}, you asked for {n}; check the label count')
    words = {w for w in norm(entry['title']).split() if len(w) >= 3} if entry else set()
    if words and not words & set(norm(q_text).split()):
        warn('question text shares no word with the TOC title; compare with `question --render`')
    pages = [p for p, _ in reader.question_labels()]
    shared = {p for p in pages if pages.count(p) > 1}   # PDF pages where two questions start
    return {'n': n, 'toc': entry, 'entries': entries, 'blocks': blocks, 'question': q_text,
            'shared_pages': shared}


# ---------------------------------------------------------------- output

def pages_of(q):
    ps = {pp for ps in q['blocks'].values() for p in ps for pp in p['span']}
    return sorted(ps, key=lambda t: t[0])


def render_text(q, full=False):
    out = []
    ps = pages_of(q)
    out.append(f'Q{q["n"]}  pdf pages '
               f'{",".join(str(p + 1) for p, _ in ps)}  printed '
               f'{",".join(str(pr) for _, pr in ps)}')
    for key, label in LABELS:
        paras = q['blocks'][key]
        out.append(f'== {label}')
        shown = paras if (full or key != 'detailed') else paras[:3]
        for i, p in enumerate(shown, 1):
            flags = ''
            if p['sym']:
                flags += f' [sym x{p["sym"]}: honorific dropped, restore only against the rendered page]'
            if p['verse']:
                flags += (f' [{p["text"].count(VERSE_HOLE)} verse hole(s): text not in PDF; '
                          'give --related verse:S:A per hole]')
            n_alef = len(RESTORED_ALEF.findall(p['text'])) + p.get('alef', 0)
            if n_alef:
                flags += (f' [alef x{n_alef}: alef of a marked lam-alef restored (the PDF drops it) '
                          'or of an alef+lam-alef recovered from the glyph trace, check against the page]')
            out.append(f'  [{i}] (p.{p["printed"]}) {p["text"]}{flags}')
        if len(shown) < len(paras):
            out.append(f'  ... {len(paras) - len(shown)} more (use --full)')
    return '\n'.join(out)


def render_pages(reader, q, out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f'q{q["n"]:03d}.txt').write_text(render_text(q, full=True) + '\n', encoding='utf-8')
    for page, printed in pages_of(q):
        pix = reader.doc[page].get_pixmap(dpi=100)
        pix.save(str(out_dir / f'q{q["n"]:03d}-pdf{page + 1:04d}-p{printed}.png'))
    print(f'rendered to {out_dir}', file=sys.stderr)


def build_item(q, args):
    short = q['blocks']['short']
    if not short:
        fail(f'Q{q["n"]} has no مختصر الإجابة block; run `question` to see what was found')
    if args.paras:
        m = re.fullmatch(r'\s*(\d+)\s*(?:-\s*(\d+))?\s*', args.paras)
        if not m:
            fail('--paras must look like 2 or 1-3')
        a, b = int(m.group(1)), int(m.group(2) or m.group(1))
        if not 1 <= a <= b <= len(short):
            fail(f'--paras {args.paras}: the short answer has {len(short)} paragraph(s)')
        if b - a > 2:
            warn('more than 3 paragraphs selected; the plan allows 1-3')
    else:
        if len(short) > 3:
            fail(f'the short answer has {len(short)} paragraphs; choose 1-3 with --paras A-B')
        a, b = 1, len(short)
    sel = short[a - 1:b]
    used = sel + q['blocks']['question'] + q['blocks']['similar']     # paragraphs in the item
    n_sym = sum(p['sym'] for p in used)
    if n_sym:
        if not args.allow_dropped_symbols:
            fail(f'{n_sym} symbol-font glyph(s) (honorifics such as the salla signs) were dropped '
                 'from the chosen paragraphs, the question or the similar wordings, so the item '
                 'would differ from the printed page. Compare with `question --render`; if you '
                 'restore them against the page, rerun with --allow-dropped-symbols')
        warn(f'{n_sym} dropped symbol glyph(s) allowed: the review note must say the honorifics '
             'were restored against the rendered page')
    printed = sel[0]['printed']
    if printed is None:
        fail('no printed page number could be read for the chosen paragraph; check the header '
             'detection with `glyphs` / `question --render`')
    text = '\n\n'.join(p['text'] for p in sel)
    if '﴿' in text or '﴾' in text:
        fail('the chosen text contains verse marks (﴿ ﴾); choose paragraphs without inline verses')
    title, similar = q['question'], [p['text'] for p in q['blocks']['similar']]
    holed = [s for s in similar if VERSE_HOLE in s or '﴿' in s or '﴾' in s]
    if holed:                                   # a keyword cannot carry a verse marker
        similar = [s for s in similar if s not in holed]
        warn(f'{len(holed)} similar wording(s) with a verse hole or verse marks dropped from '
             'keywords_ar (keywords carry no verse text)')
    toc_title = (q.get('toc') or {}).get('title') or ''
    unfit = (VERSE_HOLE in title or '﴿' in title or '﴾' in title
             or any(p['sym'] for p in q['blocks']['question']))
    if not title or unfit:
        why = ('the page prints no question under السؤال (the book does that for some questions)'
               if not title else 'the question text has a verse hole, verse marks or a dropped '
               'honorific, which title_ar cannot carry')
        if not toc_title:
            fail(f'{why}, and there is no TOC title; compare with `question --render`')
        title = toc_title
        warn(f'{why}; title_ar taken from the TOC title, check it against the المسألة heading')
    n_alef = (sum(len(RESTORED_ALEF.findall(s)) for s in (text, title, *similar))
              + sum(p.get('alef', 0) for p in used))
    if n_alef:
        warn(f'{n_alef} alef(s) restored that the PDF text layer drops (marked lam-alef, or alef '
             'before a lam-alef); check each against the rendered page')
    if args.keep_tashkeel:
        warn('tashkeel kept: the PDF places marks by position only, so the review must check '
             'every mark against the rendered page')
    else:
        text, title = TASHKEEL.sub('', text), TASHKEEL.sub('', title)
        similar = [TASHKEEL.sub('', s) for s in similar]
    if len(title) > TITLE_MAX:                  # ContentItem.title_ar is max_length 200
        if not args.keep_tashkeel:
            toc_title = TASHKEEL.sub('', toc_title)
        if not toc_title or len(toc_title) > TITLE_MAX:
            fail(f'the question text is {len(title)} characters (title_ar allows {TITLE_MAX}) '
                 'and the TOC title cannot replace it; this question cannot be drafted')
        warn(f'the question text is {len(title)} characters (title_ar allows {TITLE_MAX}); '
             'title_ar taken from the TOC title, check it against the المسألة heading')
        title = toc_title
    bank = dfp.bank_verses(args.items_dir)
    given = list(args.related or [])
    for lab in given:
        m = re.fullmatch(r'verse:(\d+):(\d+)', lab)
        if not m or (int(m.group(1)), int(m.group(2))) not in bank:
            fail(f'--related {lab}: not a verse:S:A label of a verse in the bank (items/*.json)')
    holes = text.count(VERSE_HOLE)
    if holes:
        if len(given) != holes:
            fail(f'the chosen paragraphs have {holes} verse hole(s) (verse glyphs, no text in the '
                 f'PDF) but {len(given)} --related label(s). Give one bank verse per hole, in '
                 'reading order, or choose other paragraphs. No verse is ever typed by hand.')
        for lab in given:
            text = text.replace(VERSE_HOLE, '{{' + lab + '}}', 1)
    frag = f'p{printed}'
    if sel[0]['page'] in q.get('shared_pages', ()):
        frag += f'-q{q["n"]}'
    refs = list(given)
    for s, a_ in verse_refs(' '.join(p['text'] for ps in q['blocks'].values() for p in ps)):
        if (s, a_) in bank and f'verse:{s}:{a_}' not in refs:
            refs.append(f'verse:{s}:{a_}')
    item = {
        'type': 'faq',
        'values': [args.value],
        'title_ar': title,
        'title_en': '',
        'keywords_ar': similar,
        'arabic_text': text,
        'book': BOOK,
        'number': f'Q{q["n"]} · p.{printed}',
        'source_site': 'dawa.center',
        'source_url': f'{FILE_URL}#{frag}',
    }
    if refs:
        item['related'] = refs
    hits = dfp.age_screen(text + ' ' + q['question'])
    for cat, word in hits:
        warn(f'age screen [{cat}]: "{word}"; check against the deny-list')
    doubt = any(cat in ('jihad', 'sects_disbelief') for cat, _ in hits)
    item['age_band'] = args.age_band or ('10-13' if doubt else 'all')
    if doubt and not args.age_band:
        warn('doubt-type question: age_band defaulted to 10-13')
    item['content_level'] = 'B'
    item['verification_status'] = 'unverified'
    if not item['title_en']:
        warn('title_en is empty; pass it by editing the draft (our own short English title)')
    return item


# ---------------------------------------------------------------- commands

def open_reader(args):
    return Reader(args.pdf, args.verse_font, args.symbol_font, args.cache_dir,
                  use_cache=not args.no_cache)


def cmd_toc(args):
    r = open_reader(args)
    entries, sections = find_toc(r, args.toc_pages)
    if not entries:
        fail('no table of contents found in the first pages (try --toc-pages 120)')
    si = 0
    for k, e in enumerate(entries):
        while si < len(sections) and sections[si][0] <= k:
            print(f'   # {sections[si][1]}')
            si += 1
        if args.grep and norm(args.grep) not in norm(e['title']):
            continue
        print(f'{e["n"]}\t{e["title"]}\t{e["page"]}')
    print(f'# {len(entries)} questions', file=sys.stderr)


def cmd_question(args):
    r = open_reader(args)
    q = get_question(r, args.n, args.toc_pages)
    print(render_text(q, args.full))
    if args.render:
        render_pages(r, q, args.render)


def cmd_draft(args):
    r = open_reader(args)
    q = get_question(r, args.n, args.toc_pages)
    item = build_item(q, args)
    if args.out:
        dfp.merge_out(args.out, item)
    else:
        print(json.dumps([item], ensure_ascii=False, indent=1))


def cmd_glyphs(args):
    r = open_reader(args)
    i = args.page - 1
    if not 0 <= i < len(r):
        fail(f'page must be 1..{len(r)}')
    gl = page_glyphs(r.doc[i], r.verse_re, r.symbol_re)
    fonts = {}
    for g in gl:
        fonts.setdefault((g.font, g.kind), 0)
        fonts[(g.font, g.kind)] += 1
    print('fonts (name, class, glyph count):')
    for (f, k), c in sorted(fonts.items(), key=lambda t: -t[1]):
        print(f'  {f!r:40} {k:6} {c}')
    multi = sorted({g.c for g in gl if len(g.c) > 1 and g.kind == 'text'})
    print('multi-character glyphs (after fix):', multi)
    print('dropped (symbol/junk) glyph codes:',
          sorted({f'U+{ord(g.c[0]):04X}' for g in gl if g.kind == 'sym' and g.c}))
    digits = {}
    for b in r.doc[i].get_text('rawdict').get('blocks', []):
        for ln in b.get('lines', []):
            for sp in ln.get('spans', []):
                for ch in sp.get('chars', []):
                    if is_digit(ch['c']):
                        key = (sp.get('font', ''), f'{sp.get("color") or 0:06x}', ch['c'])
                        digits[key] = digits.get(key, 0) + 1
    print('digit glyphs (font, colour, char, count; a coloured lone digit is a list marker):')
    for (f, col, c), cnt in sorted(digits.items()):
        print(f'  {f!r:40} {col} {c!r} {cnt}')
    print('bullet glyphs replaced:', sum(1 for g in gl if g.c == '•'))
    print('letters restored from the glyph trace:', sum(1 for g in gl if g.restored))
    body, printed, header = r.page(i)
    print(f'printed page: {printed}  header: {header!r}  body lines: {len(body)}')


def make_parser():
    ap = argparse.ArgumentParser(prog='extract_faq.py', description=__doc__.split('\n')[0])
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument('pdf')
    common.add_argument('--verse-font', default=VERSE_FONT_RE)
    common.add_argument('--symbol-font', default=SYMBOL_FONT_RE)
    common.add_argument('--cache-dir')
    common.add_argument('--no-cache', action='store_true')
    common.add_argument('--toc-pages', type=int, default=60)
    common.add_argument('--items-dir', default=str(dfp.ITEMS_DIR))
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('toc', parents=[common])
    p.add_argument('--grep', help='only entries whose title contains this word')
    p.set_defaults(func=cmd_toc)
    p = sub.add_parser('question', parents=[common])
    p.add_argument('n', type=int)
    p.add_argument('--render', metavar='DIR')
    p.add_argument('--full', action='store_true', help='show the whole detailed answer')
    p.set_defaults(func=cmd_question)
    p = sub.add_parser('draft', parents=[common])
    p.add_argument('n', type=int)
    p.add_argument('--value', required=True)
    p.add_argument('--paras', help='paragraphs of مختصر الإجابة: one index (2) or a range (1-3)')
    p.add_argument('--age-band', choices=['all', '6-9', '10-13'])
    p.add_argument('--related', action='append', default=[], metavar='verse:S:A',
                   help='bank verse for each verse hole, in reading order')
    p.add_argument('--allow-dropped-symbols', action='store_true')
    p.add_argument('--keep-tashkeel', action='store_true',
                   help='keep the marks (default: stripped, they are placed by position only)')
    p.add_argument('--out')
    p.set_defaults(func=cmd_draft)
    p = sub.add_parser('glyphs', parents=[common])
    p.add_argument('page', type=int)
    p.set_defaults(func=cmd_glyphs)
    return ap


def main(argv=None):
    args = make_parser().parse_args(argv)
    args.func(args)


if __name__ == '__main__':
    main()
