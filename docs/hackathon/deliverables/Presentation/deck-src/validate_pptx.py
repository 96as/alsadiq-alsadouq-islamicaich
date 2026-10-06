"""Checks that PowerPoint (not just LibreOffice) will open the deck without a repair prompt.

- duplicate cNvPr ids within a slide
- a16:rowId / extLst inside table rows (copied rows would duplicate ids)
- schema order of children in a:rPr and p:spPr (the builder edits both)
"""
import re
import sys
import zipfile
from collections import Counter
from lxml import etree

A = "http://schemas.openxmlformats.org/drawingml/2006/main"
P = "http://schemas.openxmlformats.org/presentationml/2006/main"
RPR_ORDER = ["ln", "noFill", "solidFill", "gradFill", "blipFill", "pattFill", "grpFill", "effectLst", "effectDag",
             "highlight", "uLnTx", "uLn", "uFillTx", "uFill", "latin", "ea", "cs", "sym", "hlinkClick",
             "hlinkMouseOver", "rtl", "extLst"]
SPPR_ORDER = ["xfrm", "custGeom", "prstGeom", "noFill", "solidFill", "gradFill", "blipFill", "pattFill", "grpFill",
              "ln", "effectLst", "effectDag", "scene3d", "sp3d", "extLst"]
FILLS = {"noFill", "solidFill", "gradFill", "blipFill", "pattFill", "grpFill"}


def order_ok(el, order):
    pos = []
    for c in el:
        name = etree.QName(c).localname
        if name not in order:
            return False, f"unknown child {name}"
        pos.append(order.index(name))
    if pos != sorted(pos):
        return False, [etree.QName(c).localname for c in el]
    fills = [etree.QName(c).localname for c in el if etree.QName(c).localname in FILLS]
    if len(fills) > 1:
        return False, f"two fills {fills}"
    return True, None


def main(path):
    z = zipfile.ZipFile(path)
    problems = []
    slides = sorted((n for n in z.namelist() if re.match(r"ppt/slides/slide\d+\.xml$", n)),
                    key=lambda n: int(re.findall(r"\d+", n)[0]))
    for n in slides:
        root = etree.fromstring(z.read(n))
        ids = Counter(e.get("id") for e in root.iter(f"{{{P}}}cNvPr"))
        dup = [i for i, c in ids.items() if c > 1]
        if dup:
            problems.append(f"{n}: duplicate shape ids {dup}")
        for tr in root.iter(f"{{{A}}}tr"):
            if tr.find(f"{{{A}}}extLst") is not None:
                problems.append(f"{n}: extLst (row id) inside a:tr")
        for rpr in list(root.iter(f"{{{A}}}rPr")) + list(root.iter(f"{{{A}}}endParaRPr")):
            ok, why = order_ok(rpr, RPR_ORDER)
            if not ok:
                problems.append(f"{n}: rPr order {why}")
        for sppr in root.iter(f"{{{P}}}spPr"):
            ok, why = order_ok(sppr, SPPR_ORDER)
            if not ok:
                problems.append(f"{n}: spPr order {why}")
    print(f"checked {len(slides)} slides")
    for p in problems[:40]:
        print("  ", p)
    print("problems:", len(problems))
    return len(problems)


if __name__ == "__main__":
    sys.exit(1 if main(sys.argv[1]) else 0)
