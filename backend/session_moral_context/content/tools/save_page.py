#!/usr/bin/env python3
"""Save a source page captured in the browser pane, byte for byte, with a hash check.

Why: Arabic retyped by a model (or saved with the Write tool) can come out with its
combining marks reordered. So the page's own JavaScript returns its text with a sha256
computed in the page, padded so the harness writes the result to a tool-results file.
This script reads that file, recomputes the hash and only then writes the page into the
gitignored cache with the header draft_from_page.py reads. No model retypes the text.

In the browser (javascript_tool, or a javascript_tool step in browser_batch):

    const b = document.body.innerText;
    const x = [...new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(b)))]
              .map(c => c.toString(16).padStart(2, '0')).join('');
    ({u: location.href, x, b, pad: 'x'.repeat(60000)})

Then, with the tool-results path the harness printed:

    python3 save_page.py RESULT_FILE .cache/dorar-tafseer/2-40.md
"""
import hashlib
import json
import sys
from datetime import date
from pathlib import Path


def find_capture(obj):
    """The {u, x, b} object inside a tool-results file (plain or browser_batch wrapper)."""
    if isinstance(obj, dict) and {'u', 'x', 'b'} <= obj.keys():
        return obj
    if isinstance(obj, dict):
        obj = list(obj.values())
    if isinstance(obj, list):
        for v in obj:
            got = find_capture(v)
            if got:
                return got
    if isinstance(obj, str) and '"x"' in obj:
        dec = json.JSONDecoder()
        for i, ch in enumerate(obj):
            if ch == '{':
                try:
                    got = find_capture(dec.raw_decode(obj, i)[0])
                except ValueError:
                    continue
                if got:
                    return got
    return None


def save(result_file, out):
    d = find_capture(json.loads(Path(result_file).read_text(encoding='utf-8')))
    if not d:
        sys.exit(f'{result_file}: no {{u, x, b}} capture found')
    got = hashlib.sha256(d['b'].encode('utf-8')).hexdigest()
    if got != d['x']:
        sys.exit(f'sha256 mismatch: page {d["x"]} vs file {got}; nothing written')
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(f'Source URL: {d["u"]}\nRetrieved: {date.today().isoformat()}\n\n{d["b"]}\n', encoding='utf-8')
    print(f'saved {out} ({len(d["b"])} chars, sha {got[:12]} ok) from {d["u"]}')


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    save(sys.argv[1], sys.argv[2])
