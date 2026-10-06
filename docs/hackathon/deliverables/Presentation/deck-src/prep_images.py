"""Convert candidate screenshots (webp/gif/png) into PNGs under deck-work/img/ and
write a labelled contact sheet so they can be reviewed quickly.

Usage: python prep_images.py tour|before|after|idea
"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageSequence

# The worktrees folder that holds deck-work/, 10-submission/ and product-tour/
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "deck-work" / "img"
OUT.mkdir(exist_ok=True)

which = sys.argv[1]
if which == "tour":
    src = sorted((ROOT / "product-tour" / "img").glob("*-1440x900.webp"))
    src += sorted((ROOT / "product-tour" / "img").glob("*-ar-390x844.webp"))
elif which == "before":
    src = sorted((ROOT / "10-submission/docs/hackathon/readme-media/before").glob("*"))
elif which == "after":
    src = sorted((ROOT / "10-submission/docs/hackathon/readme-media/after").glob("*"))
elif which == "idea":
    src = sorted((ROOT / "deck-work" / "idea-media").glob("*"))
else:
    raise SystemExit("unknown set")

thumbs = []
for f in src:
    if f.suffix.lower() not in (".webp", ".png", ".jpg", ".jpeg", ".gif"):
        continue
    im = Image.open(f)
    if f.suffix.lower() == ".gif":
        frames = [fr.convert("RGB") for fr in ImageSequence.Iterator(im)]
        # keep a few frames spread over the animation
        n = len(frames)
        picks = sorted({0, n // 4, n // 2, (3 * n) // 4, n - 1}) if n > 1 else [0]
        for k in picks:
            p = OUT / f"{which}-{f.stem}-f{k:03d}.png"
            frames[k].save(p)
            thumbs.append((p.name, frames[k]))
        print(f.name, "frames", n, im.size)
        continue
    im = im.convert("RGB")
    p = OUT / f"{which}-{f.stem}.png"
    im.save(p)
    thumbs.append((p.name, im))
    print(p.name, im.size)

# contact sheet
tw = 360
rows = []
cols = 4
cells = []
for name, im in thumbs:
    r = tw / im.width
    t = im.resize((tw, max(1, int(im.height * r))))
    cells.append((name, t))
for k in range(0, len(cells), 16):
    chunk = cells[k:k + 16]
    h = max(c[1].height for c in chunk) + 18
    nrows = (len(chunk) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * (tw + 6), nrows * (h + 6)), "white")
    dr = ImageDraw.Draw(sheet)
    for i, (name, t) in enumerate(chunk):
        x = (i % cols) * (tw + 6)
        y = (i // cols) * (h + 6)
        dr.text((x + 2, y + 2), name[:58], fill="red")
        sheet.paste(t, (x, y + 16))
    sp = ROOT / "deck-work" / "img" / f"_sheet-{which}-{k // 16 + 1}.png"
    sheet.save(sp)
    print("sheet", sp)
