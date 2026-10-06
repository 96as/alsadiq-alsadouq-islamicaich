"""Offline check (0 API calls): how often does an English reply name a verse number that is not one of the served verses?
Reads the live reports; prints counts and case ids only (no reply text)."""
import glob, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
UNITS = {w: i for i, w in enumerate('zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen'.split())}
TENS = {w: 10 * (i + 2) for i, w in enumerate('twenty thirty forty fifty sixty seventy eighty ninety'.split())}
# longest words first so that "fourteen" is not read as "four"
_WORDS = sorted(list(UNITS) + list(TENS) + ['hundred', 'thousand', 'and'], key=len, reverse=True)
NUMWORD = r'(?:' + '|'.join(_WORDS) + r')\b'
PAT = re.compile(r'\bverses?\s+((?:' + NUMWORD + r'[\s-]*)+)', re.I)


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


def check(files):
    n_reply = ok = bad = 0
    bad_ids = []
    for f in files:
        d = json.load(open(f, encoding='utf8'))
        for r in d['results']:
            if r['lang'] != 'en' or not r.get('reply'):
                continue
            served = [x for x in (r.get('served') or []) if str(x).startswith('verse:')]
            ayahs = {int(x.split(':')[2]) for x in served}
            m = PAT.findall(r['reply'])
            if not m:
                continue
            n_reply += 1
            nums = [words_to_int(x) for x in m if x.strip()]
            if nums and all(n in ayahs for n in nums):
                ok += 1
            else:
                bad += 1
                bad_ids.append((r['case_id'], nums, sorted(ayahs)))
    return n_reply, ok, bad, bad_ids


if __name__ == '__main__':
    for side in ('before', 'after'):
        files = sorted(glob.glob(os.path.join(HERE, 'out', side, 'report-llm-*.json')))
        n, ok, bad, ids = check(files)
        print(f'{side}: English replies that name a verse number: {n}; matches a served verse: {ok}; does not match: {bad}')
        for i in ids:
            print('   ', i)
