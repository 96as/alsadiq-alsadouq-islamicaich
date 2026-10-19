"""Tile rendered slide PNGs into numbered contact sheets for quick inspection.
Usage: python sheet.py <dir> [cols] [per_sheet] [only=1,2,3]
"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

d = Path(sys.argv[1])
cols = int(sys.argv[2]) if len(sys.argv) > 2 else 2
per = int(sys.argv[3]) if len(sys.argv) > 3 else 6
only = None
if len(sys.argv) > 4:
    only = {int(x) for x in sys.argv[4].split(",")}
files = sorted(d.glob("s-*.png"))
if only:
    files = [f for f in files if int(f.stem.split("-")[1]) in only]
for old in d.glob("sheet-*.png"):
    old.unlink()
for k in range(0, len(files), per):
    chunk = files[k:k + per]
    ims = [Image.open(f).convert("RGB") for f in chunk]
    w, h = ims[0].size
    rows = (len(ims) + cols - 1) // cols
    pad = 24
    sheet = Image.new("RGB", (cols * (w + 8), rows * (h + pad + 8)), "white")
    dr = ImageDraw.Draw(sheet)
    for i, (f, im) in enumerate(zip(chunk, ims)):
        x = (i % cols) * (w + 8)
        y = (i // cols) * (h + pad + 8)
        dr.text((x + 4, y + 4), f.stem, fill="red")
        sheet.paste(im, (x, y + pad))
    out = d / f"sheet-{k // per + 1:02d}.png"
    sheet.save(out)
    print(out)
