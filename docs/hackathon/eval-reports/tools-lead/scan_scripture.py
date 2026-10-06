"""Scan eval report files for Quran text from the bank (Arabic and English translation) and for hadith-like wording.
Usage: PYTHONUTF8=1 python scan_scripture.py <file> [<file> ...] [--redact OUTDIR]
Prints counts and positions only, never the matched text. With --redact, writes copies with matched word runs replaced
by '[source text removed]'. Matching is on normalised word runs (Arabic: no diacritics, alef/ya/ta-marbuta folded).
"""
import glob, html, json, os, re, sys

ROOT = os.environ.get('BANK_ROOT') or os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'agent-quality', 'backend', 'session_moral_context', 'content')
AR_MARKS = re.compile(r'[ؐ-ًؚ-ٰٟۖ-ۭـ]')
WORD = re.compile(r'[؀-ۿA-Za-z0-9\']+')


def norm_ar(s):
    s = AR_MARKS.sub('', s)
    return (s.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا').replace('ى', 'ي').replace('ة', 'ه').replace('ٱ', 'ا'))


def words(s):
    return [norm_ar(w).lower() for w in WORD.findall(s)]


def bank_runs():
    runs = {}
    for f in glob.glob(os.path.join(ROOT, 'items', '*.json')):
        for it in json.load(open(f, encoding='utf8')):
            for key, n in (('arabic_text', 4), ('english_text', 5)):
                w = words(it.get(key) or '')
                for i in range(0, max(0, len(w) - n + 1)):
                    runs.setdefault(tuple(w[i:i + n]), (os.path.basename(f), key, n))
    return runs


def scan_text(text, runs):
    """Return list of (start_word_index, n) matches over the word list."""
    toks = [(m.start(), m.end(), norm_ar(m.group()).lower()) for m in WORD.finditer(text)]
    hits = []
    for n in (4, 5):
        for i in range(0, len(toks) - n + 1):
            key = tuple(t[2] for t in toks[i:i + n])
            if key in runs and runs[key][2] == n:
                hits.append((toks[i][0], toks[i + n - 1][1], runs[key][0], runs[key][1]))
    return hits


def main():
    args = sys.argv[1:]
    redact = None
    if '--redact' in args:
        i = args.index('--redact')
        redact = args[i + 1]
        args = args[:i] + args[i + 2:]
        os.makedirs(redact, exist_ok=True)
    runs = bank_runs()
    print(f'bank word runs: {len(runs)}')
    total = 0
    for f in args:
        raw = open(f, encoding='utf8').read()
        text = raw
        hits = scan_text(text, runs)
        marks = len(AR_MARKS.findall(raw))
        total += len(hits)
        print(f'{os.path.basename(f)}: {len(hits)} bank-text run hits, {marks} Arabic diacritics, {len(raw)} chars')
        for s, e, fn, key in hits[:20]:
            ctx = raw[max(0, s - 60):s]
            tag = re.findall(r'[\w-]{4,}', ctx)[-3:]
            print(f'   hit at {s}-{e} ({e - s} chars) from {fn}:{key}; preceding ids/words: {tag}')
        if redact:
            spans = sorted((s, e) for s, e, _a, _b in hits)
            merged = []
            for s, e in spans:
                if merged and s <= merged[-1][1] + 1:
                    merged[-1] = (merged[-1][0], max(e, merged[-1][1]))
                else:
                    merged.append((s, e))
            out, pos = [], 0
            for s, e in merged:
                out.append(raw[pos:s])
                out.append('[source text removed]')
                pos = e
            out.append(raw[pos:])
            red = ''.join(out)
            red = AR_MARKS.sub('', red) if marks else red
            open(os.path.join(redact, os.path.basename(f)), 'w', encoding='utf8').write(red)
            print(f'   wrote redacted copy ({len(merged)} spans)')
    print('TOTAL hits', total)


if __name__ == '__main__':
    main()
