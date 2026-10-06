"""Shared by seed_content and content/tools/mark_reviewed.py. Must not import Django."""
import hashlib
import json

# Review status lives in the item files but is not content: excluded from the hash.
STATUS_KEYS = ('verification_status', 'reviewed_by', 'reviewed_at')


def item_hash(item):
    """sha256 of the item dict as written in the items file, minus the status keys."""
    item = {k: v for k, v in item.items() if k not in STATUS_KEYS}
    blob = json.dumps(item, sort_keys=True, ensure_ascii=False, separators=(',', ':'))
    return hashlib.sha256(blob.encode('utf-8')).hexdigest()


def natural_key(data):
    """Return (lookup dict, label) or raise ValueError for missing fields."""
    t = data.get('type')
    names = {'verse': ('surah', 'ayah'), 'hadith': ('book', 'number')}.get(t, ('source_url',))
    if not t or any(not data.get(n) for n in names):
        raise ValueError(f"missing natural key fields (type + {', '.join(names)})")
    lookup = {'type': t, **{n: data[n] for n in names}}
    return lookup, ':'.join(str(v) for v in lookup.values())
