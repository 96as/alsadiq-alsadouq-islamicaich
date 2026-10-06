import re

_MARKS = re.compile('[\u064b-\u065f\u0670\u0640\u06d6-\u06ed\u08f0-\u08f2]')
_MAP = str.maketrans({'أ': 'ا', 'إ': 'ا', 'آ': 'ا', 'ى': 'ي', 'ة': 'ه', '\u0671': 'ا'})


def normalize_ar(text):
    """Strip tashkeel/tatweel, unify alef/ya/ta-marbuta, collapse whitespace."""
    if not text:
        return ''
    return ' '.join(_MARKS.sub('', text).translate(_MAP).split())
