"""Render the deck to a PDF and per-slide JPGs with Readex Pro (headless LibreOffice, with a timeout).

    python render.py <deck.pptx> <outdir> <fonts_dir>
"""
import os, subprocess, sys, tempfile
from pathlib import Path
deck, out, fonts = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve(), Path(sys.argv[3]).resolve()
out.mkdir(parents=True, exist_ok=True)
conf = out / "fonts.conf"
conf.write_text(f'<?xml version="1.0"?><fontconfig><dir>{fonts}</dir><dir>/System/Library/Fonts</dir>'
                f'<dir>/Library/Fonts</dir><cachedir>{out}/fccache</cachedir></fontconfig>')
env = dict(os.environ, FONTCONFIG_FILE=str(conf))
profile = tempfile.mkdtemp(prefix="lo-profile-")
subprocess.run(["soffice", "--headless", "--norestore", "--nologo", "--nodefault",
                f"-env:UserInstallation=file://{profile}", "--convert-to", "pdf", "--outdir", str(out), str(deck)],
               env=env, check=True, timeout=240, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
pdf = out / (deck.stem + ".pdf")
for f in out.glob("s-*.jpg"):
    f.unlink()
subprocess.run(["pdftoppm", "-jpeg", "-r", "50", str(pdf), str(out / "s")], check=True, timeout=240)
print(pdf)
