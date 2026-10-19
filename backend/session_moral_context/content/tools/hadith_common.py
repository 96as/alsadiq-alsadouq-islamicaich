"""Shared helpers for fetch_hadeethenc.py and fetch_hadith.py (stdlib only, no Django).

Nothing in here contains hadith text. It holds:
  * the canonical book names and the (book, number) natural-key label,
  * Arabic normalisation for the matn-equality rule (plan section 4.2, route H step 4),
  * `provenance.json` writing (plan section 4.3),
  * small file helpers.
"""
import hashlib
import json
import re
import unicodedata
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
CONTENT = TOOLS.parent
CACHE = TOOLS / '.cache'  # gitignored
PROVENANCE = CONTENT / 'provenance.json'
VALUES_JSON = CONTENT / 'values.json'

UA = 'AlSadiq-curation/0.1 (+https://github.com/96as/Alsadiq-Alsadouq)'

# One canonical English string per book: the unique key is (type, book, number).
BOOKS = {
    'bukhari': {'name': 'Sahih al-Bukhari', 'ar': 'صحيح البخاري', 'grader': 'البخاري', 'dorar_id': 6216},
    'muslim': {'name': 'Sahih Muslim', 'ar': 'صحيح مسلم', 'grader': 'مسلم', 'dorar_id': 3088},
}


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256_file(path):
    return sha256_bytes(Path(path).read_bytes())


def known_values():
    """Value slugs from content/values.json (empty list if the file is missing)."""
    try:
        return [v['slug'] for v in json.loads(VALUES_JSON.read_text(encoding='utf-8'))]
    except (OSError, ValueError, KeyError):
        return []


def label(book_name, number):
    """Natural-key label, identical to utils/review.natural_key: hadith:<book>:<number>."""
    return f'hadith:{book_name}:{number}'


# --- Arabic helpers ---------------------------------------------------------

TATWEEL = 'ـ'
ARABIC_INDIC = str.maketrans('٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹', '01234567890123456789')


def to_ascii_digits(s):
    return s.translate(ARABIC_INDIC)


def strip_marks(s):
    """Remove tashkeel and other combining marks (Mn/Me/Mc), tatweel, format characters,
    punctuation (P*), separators and controls (Z*, C*). Letters, digits and symbols stay.
    Used ONLY to compare texts, never to produce stored text."""
    out = []
    for ch in s:
        if ch == TATWEEL:
            continue
        cat = unicodedata.category(ch)
        if cat[0] in 'MPZC':
            continue
        out.append(ch)
    return ''.join(out)


_AR_FOLD = str.maketrans({'أ': 'ا', 'إ': 'ا', 'آ': 'ا', 'ٱ': 'ا', 'ى': 'ي', 'ة': 'ه'})


def normalize_ar(s):
    """Search form for keyword tests (mirrors utils/arabic.normalize_ar, but keeps word breaks):
    no tashkeel/tatweel/format characters, punctuation and whitespace -> one space, alef/ya/ta-marbuta
    unified. Used ONLY to compare texts, never to produce stored text."""
    out = []
    for ch in s or '':
        cat = unicodedata.category(ch)
        if ch == TATWEEL or cat[0] == 'M' or cat == 'Cf':
            continue
        out.append(' ' if ch.isspace() or cat[0] == 'P' else ch)
    return ' '.join(''.join(out).translate(_AR_FOLD).split())


def word_count(s):
    return len(s.split())


_COLONS = (':', '：')


def strip_narrator_clause(text):
    """Drop a leading narrator clause ("... رضي الله عنه قال:") if there is one.

    Heuristic: the first colon within the first 20 words, with a prefix that starts with
    عن or contains رضي/رضى. Returns (text_without_clause, changed)."""
    cut = -1
    for c in _COLONS:
        i = text.find(c)
        if i != -1 and (cut == -1 or i < cut):
            cut = i
    if cut == -1:
        return text, False
    prefix = text[:cut]
    if word_count(prefix) > 10:
        return text, False
    words = prefix.split()
    if not words:
        return text, False
    first = strip_marks(words[0])
    plain = strip_marks(prefix)
    if first == 'عن' or 'رضي' in plain or 'رضى' in plain:
        return text[cut + 1:].strip(), True
    return text, False


def matn_equal(a, b):
    """The route H rule: equal after removing tashkeel, tatweel, punctuation, whitespace,
    with the narrator clause stripped on BOTH sides or on NEITHER.

    Returns (equal, mode) where mode is 'plain', 'narrator-stripped' or ''. A text that has
    no narrator clause on one side is never stripped on the other side only."""
    if not a or not b:
        return False, ''
    if strip_marks(a) == strip_marks(b):
        return True, 'plain'
    sa, ca = strip_narrator_clause(a)
    sb, cb = strip_narrator_clause(b)
    if ca and cb and strip_marks(sa) and strip_marks(sa) == strip_marks(sb):
        return True, 'narrator-stripped'
    return False, ''


# --- provenance.json --------------------------------------------------------

def append_provenance(key, record, path=None):
    """Add `key` to content/provenance.json (a JSON object keyed like the review ledger).
    An existing record under the same key is updated field by field (so the HadeethEnc and
    the dorar tools can both contribute). Returns the path written."""
    path = Path(path) if path else PROVENANCE
    data = {}
    if path.exists():
        data = json.loads(path.read_text(encoding='utf-8') or '{}')
        if not isinstance(data, dict):
            raise ValueError(f'{path} must hold a JSON object keyed by item label')
    data[key] = {**data.get(key, {}), **record}
    tmp = path.with_suffix('.json.tmp')
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    tmp.replace(path)
    return path


def write_json(path, obj):
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


_NUM_RE = re.compile(r'^\d+$')


def pure_integer(s):
    """'4321' (or Arabic-Indic digits) -> '4321'; anything else -> None."""
    s = to_ascii_digits((s or '').strip())
    return str(int(s)) if _NUM_RE.match(s) else None
