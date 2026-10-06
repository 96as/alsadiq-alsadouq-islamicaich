"""Offline check (0 API calls): does a spoken reply name a chapter, surah or verse number, and does it match what was served?
Reads out2/<side>/report-llm-*.json. Prints counts and case ids only (no reply text).
Covers:
  - English number words, ASCII digits and Arabic-Indic digits after verse/ayah/surah/chapter/ayat;
  - Arabic digits after آية/سورة/الآية (with or without رقم);
  - Arabic number WORDS (cardinals and ordinals, masculine and feminine, with the definite article and the و conjunction,
    for example a unit plus a ten, or a hundred plus a ten plus a unit) after سورة/السورة/آية/الآية;
  - chapter:verse pairs written as digits.
A bare واحد/واحدة right after the key word is ignored: it reads as "a single verse", not as a number.
Usage: PYTHONUTF8=1 python verse_numbers2.py [--out DIR]
"""
import glob, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out2')
if '--out' in sys.argv:
    OUT = sys.argv[sys.argv.index('--out') + 1]

UNITS = {w: i for i, w in enumerate('zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen'.split())}
TENS = {w: 10 * (i + 2) for i, w in enumerate('twenty thirty forty fifty sixty seventy eighty ninety'.split())}
_WORDS = sorted(list(UNITS) + list(TENS) + ['hundred', 'thousand', 'and'], key=len, reverse=True)
NUMWORD = r'(?:' + '|'.join(_WORDS) + r')\b'
EN_KEY = r'(?:verses?|ayahs?|ayat|ayas?|surahs?|suras?|chapters?)'
PAT_EN_WORDS = re.compile(r'\b' + EN_KEY + r'\s+((?:' + NUMWORD + r'[\s-]*)+)', re.I)
PAT_DIGITS = re.compile(r'\b' + EN_KEY + r'\s*(?:number\s*)?([0-9٠-٩]+)', re.I)
PAT_AR_DIGITS = re.compile(r'(?:آية|الآية|ايه|الاية|سورة|السورة)\s*(?:رقم\s*)?([0-9٠-٩]+)')
PAT_DIGITS_FIRST = re.compile(r'\b([0-9٠-٩]+)\s*:\s*([0-9٠-٩]+)')  # chapter:verse written as digits

# ---- Arabic number words -------------------------------------------------------------------------------------------
_DIACRITICS = re.compile('[ً-ْٰـ]')


def norm_ar(s):
    """Strip diacritics and tatweel, fold alef forms, alef maksura and ta marbuta so one spelling matches all."""
    s = _DIACRITICS.sub('', s)
    for a in 'أإآٱ':
        s = s.replace(a, 'ا')
    return s.replace('ى', 'ي').replace('ة', 'ه')


def _lex(pairs):
    out = {}
    for words, value in pairs:
        for w in words.split():
            out[norm_ar(w)] = value
    return out


# Units, teens' second half and ordinals. Ordinals (الاول, الخامسه ...) lose the definite article before lookup.
AR_UNITS = _lex([
    ('واحد واحده احد احدي حادي حاديه اول اولي', 1),
    ('اثنان اثنين اثنتان اثنتين اثنا اثني ثاني ثانيه ثنتين', 2),
    ('ثلاث ثلاثه ثالث ثالثه', 3),
    ('اربع اربعه رابع رابعه', 4),
    ('خمس خمسه خامس خامسه', 5),
    ('ست سته سادس سادسه', 6),
    ('سبع سبعه سابع سابعه', 7),
    ('ثمان ثماني ثمانيه ثامن ثامنه', 8),
    ('تسع تسعه تاسع تاسعه', 9),
    ('عشر عشره عاشر عاشره', 10),
])
AR_TENS = _lex([
    ('عشرون عشرين', 20), ('ثلاثون ثلاثين', 30), ('اربعون اربعين', 40), ('خمسون خمسين', 50),
    ('ستون ستين', 60), ('سبعون سبعين', 70), ('ثمانون ثمانين', 80), ('تسعون تسعين', 90),
])
AR_HUNDREDS = _lex([
    ('مئه مائه ميه', 100), ('مئتان مئتين مائتان مائتين ميتين', 200),
    ('ثلاثمئه ثلاثمائه ثلاثميه', 300), ('اربعمئه اربعمائه اربعميه', 400), ('خمسمئه خمسمائه خمسميه', 500),
    ('ستمئه ستمائه ستميه', 600), ('سبعمئه سبعمائه سبعميه', 700), ('ثمانمئه ثمانمائه ثمانميه ثمانيمئه ثمانيمائه', 800),
    ('تسعمئه تسعمائه تسعميه', 900),
])
AR_THOUSAND = {norm_ar('الف'), norm_ar('الاف')}
AR_KEY = r'(?:ايه|الايه|سوره|السوره)'
_AR_TOKEN = r'[ء-يً-ْٰ]+'
# key word, optional رقم, then a run of number-word tokens. Tokens are matched loosely here and validated against the lexicon.
# The token run sits in a lookahead so one key word never swallows the next one (a surah name, then a verse word, then the number).
PAT_AR_WORDS = re.compile(r'(?<![ء-ي])' + AR_KEY + r'\s+(?:رقم\s+)?(?=((?:' + _AR_TOKEN + r'\s*){1,8}))')


def _ar_token_value(tok):
    """Return (kind, value) for one normalised token, or None. Tries the bare token first (واحد starts with و), then without و, then without ال."""
    variants = [tok]
    if tok.startswith('و') and len(tok) > 2:
        variants.append(tok[1:])
    more = []
    for v in variants:
        if v.startswith('ال') and len(v) > 3:
            more.append(v[2:])
    variants += more
    for v in variants:
        if v in AR_HUNDREDS:
            return 'h', AR_HUNDREDS[v]
        if v in AR_TENS:
            return 't', AR_TENS[v]
        if v in AR_UNITS:
            return 'u', AR_UNITS[v]
        if v in AR_THOUSAND:
            return 'k', 1000
    return None


def ar_words_to_int(run):
    """Parse a run of Arabic number-word tokens from its start; stop at the first token that is not a number word.
    'بعد' directly before a hundreds word adds the hundreds (the fifty-fifth after the two hundred)."""
    toks = norm_ar(run).split()
    total, cur, n_tokens = 0, 0, 0
    i = 0
    while i < len(toks):
        t = toks[i]
        if t == 'بعد' and n_tokens and i + 1 < len(toks):
            nxt = _ar_token_value(toks[i + 1])
            if nxt and nxt[0] == 'h':
                cur += nxt[1]
                n_tokens += 1
                i += 2
                continue
            break
        v = _ar_token_value(t)
        if v is None:
            break
        kind, val = v
        if kind == 'k':
            total += max(cur, 1) * 1000
            cur = 0
        else:
            cur += val
        n_tokens += 1
        i += 1
    if not n_tokens:
        return None
    # A lone واحد/واحدة right after the key word means "a single verse", not a verse number.
    if n_tokens == 1 and toks[0] in ('واحد', 'واحده'):
        return None
    return total + cur


def to_ascii(s):
    return int(s.translate({0x660 + i: 48 + i for i in range(10)}))


def words_to_int(s):
    toks = [t for t in re.split(r'[\s-]+', s.lower().strip()) if t and t != 'and']
    total, cur = 0, 0
    for t in toks:
        if t in UNITS:
            cur += UNITS[t]
        elif t in TENS:
            cur += TENS[t]
        elif t == 'hundred':
            cur = max(cur, 1) * 100
        elif t == 'thousand':
            total += max(cur, 1) * 1000
            cur = 0
    return total + cur


def numbers_in_kinds(reply):
    """Every chapter, surah or verse number the reply names, as (number, kind). Kinds: en_words, digits, ar_digits, pair, ar_words."""
    found = []
    for m in PAT_EN_WORDS.findall(reply):
        if m.strip():
            found.append((words_to_int(m), 'en_words'))
    for m in PAT_DIGITS.findall(reply):
        found.append((to_ascii(m), 'digits'))
    for m in PAT_AR_DIGITS.findall(reply):
        found.append((to_ascii(m), 'ar_digits'))
    for a, b in PAT_DIGITS_FIRST.findall(reply):
        found.extend([(to_ascii(a), 'pair'), (to_ascii(b), 'pair')])
    for m in PAT_AR_WORDS.finditer(norm_ar(reply)):
        n = ar_words_to_int(m.group(1))
        if n:
            found.append((n, 'ar_words'))
    return found


def numbers_in(reply):
    return [n for n, _ in numbers_in_kinds(reply)]


def check(files):
    n_replies = n_with_verse_served = named = ok = bad = 0
    bad_ids, named_ids = [], []
    kinds_by_id = {}
    for f in files:
        d = json.load(open(f, encoding='utf8'))
        for r in d['results']:
            if not r.get('reply'):
                continue
            n_replies += 1
            served = [x for x in (r.get('served') or []) if str(x).startswith('verse:')]
            if served:
                n_with_verse_served += 1
            found = numbers_in_kinds(r['reply'])
            nums = [n for n, _ in found]
            if not nums:
                continue
            named += 1
            allowed = set()
            for x in served:
                parts = x.split(':')
                allowed.update({int(parts[1]), int(parts[2])})
            named_ids.append(r['case_id'])
            kinds_by_id[r['case_id']] = sorted({k for _, k in found})
            if all(n in allowed for n in nums):
                ok += 1
            else:
                bad += 1
                bad_ids.append((r['case_id'], r['lang'], nums, sorted(allowed)))
    return dict(replies=n_replies, replies_with_verse_served=n_with_verse_served, replies_naming_a_number=named,
                matching_served=ok, not_matching_served=bad, named_ids=named_ids, named_kinds=kinds_by_id, bad=bad_ids)


if __name__ == '__main__':
    summary = {}
    for side in ('before', 'after'):
        files = sorted(glob.glob(os.path.join(OUT, side, 'report-llm-*.json')))
        res = check(files)
        summary[side] = res
        print(f"{side}: replies {res['replies']}; with a served verse {res['replies_with_verse_served']}; "
              f"naming a chapter/surah/verse number {res['replies_naming_a_number']}; "
              f"matching a served verse {res['matching_served']}; NOT matching {res['not_matching_served']}")
        for i in res['bad']:
            print('   not matching:', i)
        print('   ids naming a number:', res['named_ids'])
        print('   kinds:', res['named_kinds'])
    json.dump(summary, open(os.path.join(OUT, 'verse_numbers.json'), 'w'), ensure_ascii=False, indent=1)
