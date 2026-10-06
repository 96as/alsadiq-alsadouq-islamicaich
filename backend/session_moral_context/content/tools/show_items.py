#!/usr/bin/env python3
"""Print the knowledge-bank items per value, readable, or write them as Markdown.

Usage:
    python3 show_items.py                      # every value
    python3 show_items.py --value prayer       # one value
    python3 show_items.py --md /tmp/verses.md  # write a Markdown file instead
Works from any folder. Stdlib only. Read-only: it never changes the bank.
"""
import argparse
import glob
import json
import os
from collections import OrderedDict

CONTENT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")


def load():
    values = json.load(open(os.path.join(CONTENT, "values.json"), encoding="utf-8"))
    items = []
    for f in sorted(glob.glob(os.path.join(CONTENT, "items", "*.json"))):
        items += json.load(open(f, encoding="utf-8"))
    return values, items


def surah_name(item):
    # source_url looks like https://quranpedia.net/tafsir/al-baqara/153
    parts = (item.get("source_url") or "").rstrip("/").split("/")
    return parts[-2] if len(parts) >= 2 else ""


def ref(item):
    return "%s:%s" % (item.get("surah"), item.get("ayah")) if item["type"] == "verse" else item["type"]


def render(values, items, only=None, md=False):
    by_value = OrderedDict((v["slug"], []) for v in values)
    for it in items:
        for s in it.get("values", []):
            by_value.setdefault(s, []).append(it)
    names = {v["slug"]: v for v in values}
    out = []
    for slug, group in by_value.items():
        if only and slug != only:
            continue
        v = names.get(slug, {})
        title = "%s (%s) / %s" % (slug, v.get("name_ar", ""), v.get("name_en", ""))
        out.append(("## %s" if md else "=== %s ===") % title)
        out.append("")
        if not group:
            out.append("(no items)\n")
        for it in group:
            head = "%s  (%s)" % (ref(it), surah_name(it))
            out.append(("### " + head) if md else "--- " + head)
            fields = [
                ("Also values", ", ".join(s for s in it.get("values", []) if s != slug)),
                ("Arabic", it.get("arabic_text")),
                ("English", it.get("english_text")),
                ("Child (ar)", it.get("child_explanation_ar")),
                ("Child (en)", it.get("child_explanation_en")),
                ("Older (en)", it.get("child_explanation_older_en")),
                ("Source", it.get("source_url")),
            ]
            for label, val in fields:
                if val:
                    out.append(("- **%s:** %s" if md else "  %s: %s") % (label, val))
            out.append("")
    if only and not out:
        raise SystemExit("No value '%s'. Slugs: %s" % (only, ", ".join(names)))
    return "\n".join(out)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--value", help="only this value slug, e.g. prayer")
    p.add_argument("--md", metavar="OUT.md", help="write Markdown to this file")
    a = p.parse_args()
    values, items = load()
    if a.md:
        text = "# Bank verses by value\n\n" + render(values, items, a.value, md=True)
        open(a.md, "w", encoding="utf-8").write(text + "\n")
        print("Wrote %s (%d items)" % (a.md, len(items)))
    else:
        print(render(values, items, a.value))


if __name__ == "__main__":
    main()
