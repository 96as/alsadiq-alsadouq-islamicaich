"""Shared helpers for the verse-text tools: load a pinned KFGQPC data file.

Used by fetch_verse.py, refresh_arabic.py and verify_arabic.py. Pure standard library,
no network. The Arabic text is never normalised: the only change we ever make to a
KFGQPC `aya_text` is removing the trailing end-of-ayah number: a no-break space or space, optional U+06DD,
then digits (v18) or one presentation-form glyph in U+FC00-U+FDFF (v2-0).

Supported file shapes (see docs/hackathon/research/r4-quran-text-audio.md, section 2.6):
  * a JSON list of rows, or a dict holding one list (e.g. {"verses": [...]});
  * the surah number under `sura_no` (official v2.0 style) or `sora` (v18 mirror);
    the ayah number under `aya_no`; text under `aya_text`; search text under
    `aya_text_emlaey` (optional);
  * a UTF-8 BOM is accepted;
  * numbers may be ints or digit strings.
The open-tanween encoding differs between releases (U+0657/065E/0656 in v18, U+08F0-08F2
in v3.0). It is kept exactly as published; `encoding_report()` tells you which one a file uses.
"""
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

NBSP = ' '
AYAH_MARK = '۝'  # optional end-of-ayah sign before the number
_DIGITS = '0-9٠-٩۰-۹'  # ASCII, Arabic-Indic, extended Arabic-Indic
GLYPHS = '\\uFC00-\\uFDFF'  # v2-0 ends every aya_text with ONE of these (the number as a font glyph)
# The glyph branch requires a separator before it, so a bare trailing ligature is never stripped.
END_NUMBER = re.compile(f'(?:[{NBSP} ]*{AYAH_MARK}?[{NBSP} ]*[{_DIGITS}]+|[{NBSP} ]+[{GLYPHS}])\\s*$')

SURAH_KEYS = ('sura_no', 'sora', 'sura', 'surah')
AYAH_KEYS = ('aya_no', 'aya', 'ayah')


class KfgqpcError(Exception):
    pass


def strip_ayah_number(text):
    """Remove only the trailing NBSP + ayah-number glyphs; everything else is untouched."""
    return END_NUMBER.sub('', text)


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def _first(row, keys):
    for k in keys:
        if k in row and row[k] not in (None, ''):
            return row[k]
    raise KfgqpcError(f'row has none of {keys}: keys are {sorted(row)}')


def guess_release(path):
    """A release label from the file name, e.g. hafsData_v18.json -> v18."""
    m = re.search(r'v[-_]?(\d+(?:[-._]\d+)*)', Path(path).name, re.I)
    return 'v' + m[1].replace('_', '-') if m else 'unknown'


class Kfgqpc:
    """Pinned KFGQPC file: `.text[(s, a)]` and `.search[(s, a)]` (both number-stripped)."""

    def __init__(self, path, sha256=None, release=None):
        self.path = str(path)
        self.sha256 = sha256_of(path)
        if sha256 and self.sha256 != sha256.strip().lower():
            raise KfgqpcError(
                f'sha256 mismatch for {path}: file is {self.sha256}, pin is {sha256.strip().lower()}')
        self.pinned = bool(sha256)
        self.release = release or guess_release(path)
        try:
            raw = json.loads(Path(path).read_text(encoding='utf-8-sig'))
        except (OSError, ValueError) as e:
            raise KfgqpcError(f'cannot read {path}: {e}') from e
        if isinstance(raw, dict):
            lists = [v for v in raw.values() if isinstance(v, list)]
            if len(lists) != 1:
                raise KfgqpcError(f'{path}: expected a list of rows or a dict with exactly one list')
            raw = lists[0]
        self.text, self.search = {}, {}
        for row in raw:
            key = (int(_first(row, SURAH_KEYS)), int(_first(row, AYAH_KEYS)))
            if 'aya_text' not in row:
                raise KfgqpcError(f'{path}: row {key} has no aya_text')
            if key in self.text:
                raise KfgqpcError(f'{path}: duplicate row {key}')
            self.text[key] = strip_ayah_number(row['aya_text'])
            if row.get('aya_text_emlaey'):
                self.search[key] = strip_ayah_number(row['aya_text_emlaey'])
        if not self.text:
            raise KfgqpcError(f'{path}: no rows')

    def edition(self):
        """Value for the `text_edition` field."""
        return f'KFGQPC Hafs {self.release} sha256:{self.sha256[:12]}'

    def get(self, surah, ayah):
        try:
            return self.text[(surah, ayah)]
        except KeyError:
            raise KfgqpcError(f'{surah}:{ayah} is not in {self.path}') from None

    def get_search(self, surah, ayah):
        return self.search.get((surah, ayah))

    def encoding_report(self):
        """Which open-tanween / alef-wasla code points the file uses (counts over all rows)."""
        c = Counter(''.join(self.text.values()))
        names = {0x657: 'U+0657', 0x65E: 'U+065E', 0x656: 'U+0656',
                 0x8F0: 'U+08F0', 0x8F1: 'U+08F1', 0x8F2: 'U+08F2', 0x671: 'U+0671'}
        return {n: c.get(chr(cp), 0) for cp, n in names.items()}


def add_common_args(p, require_pin=False):
    p.add_argument('--kfgqpc', metavar='PATH', help='pinned KFGQPC JSON (hafsData_*.json)')
    p.add_argument('--sha256', metavar='HEX', help='expected sha256 of the --kfgqpc file; abort on mismatch'
                   + ('' if not require_pin else ' (required)'))
    p.add_argument('--release', help='release label for text_edition (default: guessed from the file name)')


def load_from_args(args, require_pin=False):
    """Build a Kfgqpc from parsed args, with a clear error and a pin warning."""
    import sys
    if require_pin and not args.sha256:
        sys.exit('error: --sha256 is required (pin the exact file you downloaded)')
    try:
        k = Kfgqpc(args.kfgqpc, args.sha256, args.release)
    except KfgqpcError as e:
        sys.exit(f'error: {e}')
    if not k.pinned:
        print(f'warning: {args.kfgqpc} is NOT pinned (sha256 {k.sha256}); pass --sha256 in CI',
              file=sys.stderr)
    return k
