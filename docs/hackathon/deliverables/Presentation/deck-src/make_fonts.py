"""Instantiate static Readex Pro weights from the Google Fonts variable TTF.

LibreOffice in Debian bookworm handles static TTFs more reliably than
variable ones, so the render image gets Regular / Medium / SemiBold / Bold
as separate files with proper family/subfamily names.
"""
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

HERE = Path(__file__).parent / "fonts"
VF = HERE / "ReadexPro-VF.ttf"

WEIGHTS = {
    "Light": 300,
    "Regular": 400,
    "Medium": 500,
    "SemiBold": 600,
    "Bold": 700,
}


def set_names(font, family, sub):
    name = font["name"]
    full = f"{family} {sub}" if sub != "Regular" else family
    ps = f"{family.replace(' ', '')}-{sub}"
    # RIBBI: Regular and Bold share family "Readex Pro"; others get own family
    if sub in ("Regular", "Bold"):
        fam1, sub2 = family, sub
    else:
        fam1, sub2 = f"{family} {sub}", "Regular"
    for rec in list(name.names):
        if rec.nameID in (1, 2, 3, 4, 6, 16, 17, 25):
            name.removeNames(nameID=rec.nameID)
    name.setName(fam1, 1, 3, 1, 0x409)
    name.setName(sub2, 2, 3, 1, 0x409)
    name.setName(f"{ps};static", 3, 3, 1, 0x409)
    name.setName(full, 4, 3, 1, 0x409)
    name.setName(ps, 6, 3, 1, 0x409)
    name.setName(family, 16, 3, 1, 0x409)
    name.setName(sub, 17, 3, 1, 0x409)
    os2 = font["OS/2"]
    head = font["head"]
    if sub == "Bold":
        os2.fsSelection = (os2.fsSelection & ~0b1000000) | 0b100000
        head.macStyle = 1
    else:
        os2.fsSelection = (os2.fsSelection & ~0b100000) | 0b1000000
        head.macStyle = 0


for sub, w in WEIGHTS.items():
    vf = TTFont(VF)
    inst = instancer.instantiateVariableFont(vf, {"wght": w, "HEXP": 0})
    inst["OS/2"].usWeightClass = w
    set_names(inst, "Readex Pro", sub)
    out = HERE / f"ReadexPro-{sub}.ttf"
    inst.save(out)
    print("wrote", out.name)
