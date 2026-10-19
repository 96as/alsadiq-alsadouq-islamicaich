"""Compose the deck's images from the README media screenshots (PIL only).

Every output is sized to the exact aspect of the frame it goes into, so the
deck never stretches or crops an image by surprise. Run by build_deck.py.
"""
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw, ImageFilter

HERE = Path(__file__).parent
IMG = HERE / "img"
OUT = HERE / "img" / "compose"
OUT.mkdir(parents=True, exist_ok=True)
# The README screenshots: next to deck-work in the worktree layout, or three levels up when these
# scripts sit in the repository at docs/hackathon/deliverables/Presentation/deck-src/.
README_AFTER = next((p for p in (HERE.parent / "10-submission" / "docs" / "hackathon" / "readme-media" / "after",
                                 HERE.parents[2] / "readme-media" / "after") if p.exists()),
                    HERE.parents[2] / "readme-media" / "after")

# The home screenshot has the demo bar (dark green, "trial with made-up data") on rows 0..55.
HOME_BAR_ROWS = 56


def load(name):
    return Image.open(IMG / name).convert("RGB")


def crop_aspect(im, aspect, fx=0.5, fy=0.5):
    """Crop to width/height == aspect; fx/fy choose which part to keep (0..1)."""
    w, h = im.size
    if w / h > aspect:
        nw = int(round(h * aspect))
        x = int(round((w - nw) * fx))
        return im.crop((x, 0, x + nw, h))
    nh = int(round(w / aspect))
    y = int(round((h - nh) * fy))
    return im.crop((0, y, w, y + nh))


def rounded(im, r):
    im = im.convert("RGBA")
    mask = Image.new("L", im.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, im.size[0] - 1, im.size[1] - 1), r, fill=255)
    im.putalpha(mask)
    return im


def shadowed(canvas, tile, xy, r, blur=18, alpha=110, off=(0, 10)):
    """Paste a rounded tile with a soft shadow onto an RGBA canvas."""
    x, y = xy
    sh = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(sh)
    d.rounded_rectangle((x + off[0], y + off[1], x + off[0] + tile.size[0], y + off[1] + tile.size[1]), r,
                        fill=(4, 6, 24, alpha))
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    canvas.alpha_composite(sh)
    canvas.alpha_composite(rounded(tile, r), (x, y))


def save_jpg(im, name, maxw=1800):
    if im.width > maxw:
        im = im.resize((maxw, int(im.height * maxw / im.width)), Image.LANCZOS)
    p = OUT / name
    im.convert("RGB").save(p, quality=90, optimize=True)
    return p


def save_png(im, name, maxw=2400):
    if im.width > maxw:
        im = im.resize((maxw, int(im.height * maxw / im.width)), Image.LANCZOS)
    p = OUT / name
    im.save(p, optimize=True)
    return p


def grid(names, cols, aspect, cell_aspect, pad=0.035, r_frac=0.03, width=2400, fx=None):
    """Tiles in a grid on a transparent canvas of the given aspect."""
    W = width
    H = int(round(W / aspect))
    rows = (len(names) + cols - 1) // cols
    gap = int(W * pad)
    cw = (W - gap * (cols + 1)) // cols
    ch = int(cw / cell_aspect)
    # shrink if too tall
    if rows * ch + gap * (rows + 1) > H:
        ch = (H - gap * (rows + 1)) // rows
        cw = int(ch * cell_aspect)
    total_w = cols * cw + (cols - 1) * gap
    total_h = rows * ch + (rows - 1) * gap
    x0 = (W - total_w) // 2
    y0 = (H - total_h) // 2
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for i, n in enumerate(names):
        im = load(n)
        f = fx[i] if fx else 0.5
        tile = crop_aspect(im, cell_aspect, fx=f).resize((cw, ch), Image.LANCZOS)
        cx = x0 + (cols - 1 - (i % cols)) * (cw + gap)   # right-to-left order
        cy = y0 + (i // cols) * (ch + gap)
        shadowed(canvas, tile, (cx, cy), int(cw * r_frac))
    return canvas


def strip(names, aspect, width=2600, height_frac=0.94, gap_frac=0.022, r=22):
    """Phone-like cards side by side (right to left), same scale, top-aligned."""
    W = width
    H = int(round(W / aspect))
    ims = [Image.open(IMG / n).convert("RGB") for n in names]
    maxh = max(i.height for i in ims)
    s = (H * height_frac) / maxh
    gap = int(W * gap_frac)
    tiles = [i.resize((int(i.width * s), int(i.height * s)), Image.LANCZOS) for i in ims]
    total = sum(t.width for t in tiles) + gap * (len(tiles) - 1)
    if total > W * 0.98:
        k = (W * 0.98) / total
        tiles = [t.resize((int(t.width * k), int(t.height * k)), Image.LANCZOS) for t in tiles]
        gap = int(gap * k)
        total = sum(t.width for t in tiles) + gap * (len(tiles) - 1)
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    x = (W + total) // 2
    y0 = int(H * (1 - height_frac) / 2)
    for t in tiles:
        x -= t.width
        shadowed(canvas, t, (x, y0), r, blur=14, alpha=120)
        x -= gap
    return canvas


def faded_top(im, aspect, fade_frac=0.24, r=28):
    """Keep the top of a tall screenshot at the given aspect; fade the bottom edge out to transparent.

    Used for the parent "Sources discussed this week" page, which is taller than any slide frame:
    the header, the trust line and the first row of cards stay fully legible, and the cut is visibly a fade.
    """
    pad = 28   # white margin, so the rounded corners never clip the page heading
    framed = Image.new("RGB", (im.width + 2 * pad, im.height + pad), "white")
    framed.paste(im, (pad, pad))
    top = crop_aspect(framed, aspect, fy=0.0).convert("RGBA")
    w, h = top.size
    fade = Image.new("L", (w, h), 255)
    d = ImageDraw.Draw(fade)
    start = int(h * (1 - fade_frac))
    for y in range(start, h):
        d.line([(0, y), (w, y)], fill=int(255 * (1 - (y - start) / (h - start)) ** 1.6))
    corners = Image.new("L", (w, h), 0)
    ImageDraw.Draw(corners).rounded_rectangle((0, 0, w - 1, h + r), r, fill=255)   # round the top corners only
    top.putalpha(ImageChops.darker(fade, corners))
    return top


def build():
    out = {}
    # Solution: the home screen without the demo bar, at its own aspect (1440 x 844); the frame follows it.
    home = load("after-home-ar.png")
    home = home.crop((0, HOME_BAR_ROWS, home.width, home.height))
    out["solution"] = save_jpg(home, "solution-home-ar.jpg")
    out["solution_aspect"] = home.width / home.height
    # Gallery: three frames 5.21 x 4.69. Every crop starts below the demo bar, and the call crops keep the
    # left edge (AI chip, Voice | Chat switch, level rail) so no control is cut in half.
    a = 5.21 / 4.69

    def below_bar(name):
        im = load(name)
        return im.crop((0, HOME_BAR_ROWS, im.width, im.height))

    out["g_home"] = save_jpg(crop_aspect(home, a, fx=0.0, fy=0.0), "g-home-ar.jpg", 1400)
    out["g_voice"] = save_jpg(crop_aspect(below_bar("after-call-voice-ar.png"), a, fx=0.0), "g-voice-ar.jpg", 1400)
    out["g_chat"] = save_jpg(crop_aspect(below_bar("after-call-chat-verse-ar.png"), a, fx=0.0), "g-chat-verse-ar.jpg", 1400)
    # Source cards strip: large image 17.71 x 7.60
    out["cards"] = save_png(strip(["after-card-verse-ar.png", "after-card-hadith-ar.png", "after-card-term-ar.png",
                                   "after-card-faq-ar.png", "after-card-hadith-en.png"], 17.71 / 7.60), "cards-strip.png")
    # Avatar: the four state frames as separate tiles; build_deck lays them out and covers the
    # English state label burnt into each frame with an Arabic one.
    out["avatar_frames"] = [IMG / f"after-avatar-states-{f}.png" for f in ("f000", "f039", "f059", "f078")]
    # Parent view: the merged "Sources discussed this week" page (Arabic), wide frame 9.17 x 5.16.
    src = Image.open(README_AFTER / "parent-sources-ar.webp").convert("RGB")
    out["parent"] = save_png(faded_top(src, 9.17 / 5.16), "parent-sources-ar-top.png", maxw=1800)
    # Accessibility: wide 9.17 x 5.16, Arabic and English side by side
    acc = grid(["after-home-ar.png", "after-home-en.png", "after-ai-chip-sheet-ar.png", "after-call-chat-hadith-en.png"],
               cols=2, aspect=9.17 / 5.16, cell_aspect=1440 / 900, pad=0.03, r_frac=0.025, width=1800)
    out["access"] = save_png(acc, "access-ar-en-grid.png")
    return out


if __name__ == "__main__":
    for k, v in build().items():
        if isinstance(v, Path):
            im = Image.open(v)
            print(k, v.name, im.size, v.stat().st_size // 1024, "KB")
        else:
            print(k, v)
