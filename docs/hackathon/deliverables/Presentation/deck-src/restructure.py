"""Restructure the final deck for judges who scan (hk/17, 6 Oct 2026).

    git show 84830269:docs/hackathon/deliverables/Presentation/Al-Sadiq-Al-Sadouq-Final.pptx > base.pptx
    python restructure.py base.pptx      -> ../Al-Sadiq-Al-Sadouq-Final.pptx

Input is the deck build_deck.py made (27 slides on the organisers' template).
New main slides are clones of its slides (background art, logo, footer and
placeholder styles stay the organisers'), filled with at most about 30 words
each; the old detailed slides move to the appendix unchanged except their
section label. No Quran or hadith text is typed here: scripture appears only
inside screenshots of the app's own source cards. Icons come from icons.js.
"""
import sys
import tempfile
from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE

from build_deck import (I, NAVY, PURPLE, TURQ, OFF, BODY, MUTED, CARD, CARDLINE, MIN_PT, EST,
                        clone_slide, ph, by_name, remove, fill, add_text, add_box, add_picture,
                        add_arrow, caption, kicker, fill_table)

HERE = Path(__file__).parent
REPO = HERE.parents[4]
MEDIA = REPO / "docs" / "hackathon" / "readme-media"
ICONS = HERE / "icons"
OUTFILE = HERE.parent / "Al-Sadiq-Al-Sadouq-Final.pptx"
TMP = Path(tempfile.mkdtemp(prefix="deck-v2-"))
BAR = 56          # the demo banner at the top of every 1440x900 app screenshot, in pixels
X0, W0 = 1.54, 16.88


# ---------------------------------------------------------------- images

def shot(rel, aspect, top=BAR, fx=0.5, bottom=0):
    """Crop a screenshot (banner removed) to an exact aspect; returns a PNG path."""
    im = Image.open(MEDIA / rel).convert("RGB")
    im = im.crop((0, top, im.width, im.height - bottom))
    w, h = im.size
    if w / h > aspect:                    # too wide: trim the sides around fx
        nw = int(h * aspect)
        x = int((w - nw) * fx)
        im = im.crop((x, 0, x + nw, h))
    else:                                  # too tall: keep the top
        im = im.crop((0, 0, w, int(w / aspect)))
    out = TMP / (rel.replace("/", "_") + f"-{aspect:.3f}-{top}.jpg")
    im.save(out, quality=88)
    return out


def card(rel, cut=None):
    """A source card PNG; cut = (y0, y1) removes that band (the outdated reciter line)."""
    im = Image.open(MEDIA / rel).convert("RGBA")
    if cut:
        y0, y1 = cut
        top, bot = im.crop((0, 0, im.width, y0)), im.crop((0, y1, im.width, im.height))
        new = Image.new("RGBA", (im.width, top.height + bot.height))
        new.paste(top, (0, 0))
        new.paste(bot, (0, top.height))
        im = new
    out = TMP / Path(rel).name.replace(".png", "-c.png")
    im.save(out)
    return out, im.width / im.height


def icon(slide, name, x, y, d, color="turq", ring=TURQ, ring_alpha=14):
    add_box(slide, x, y, d, d, fill=ring, fill_alpha=ring_alpha, shape=MSO_SHAPE.OVAL)
    pad = d * 0.27
    slide.shapes.add_picture(str(ICONS / f"{name}-{color}.png"), I(x + pad), I(y + pad), I(d - 2 * pad), I(d - 2 * pad))


def notes(slide, text):
    slide.notes_slide.notes_text_frame.text = text


def strip(slide, keep=(0, 1, 2, 12)):
    """Remove the template's sample content placeholders, keep title, kicker, subtitle, number."""
    for s in list(slide.shapes):
        if s.is_placeholder and s.placeholder_format.idx not in keep:
            remove(s)


# ---------------------------------------------------------------- build

def build(src):
    prs = Presentation(src)
    old = {i + 1: s for i, s in enumerate(prs.slides)}
    ids = {i + 1: el for i, el in enumerate(prs.slides._sldIdLst)}
    made = []

    def new(n, dark=True):
        s = clone_slide(prs, old[n])
        made.append(s)
        return s

    def dark(kick, title, sub=None):
        s = new(2)
        strip(s)
        kicker(s, kick)
        fill(s, ph(s, 0), [title])
        if sub:
            fill(s, ph(s, 2), [sub])
        else:
            remove(ph(s, 2))
        return s

    # ---- M2 judge guide ---------------------------------------------------------
    s = dark("دليل اللجنة", "أين تجد كل معيار؟", "كل قسم يحمل اسم المعيار الذي يجيب عنه")
    crit = [("FaBrain", "الجودة التقنية واستخدام الذكاء الاصطناعي", "الشريحتان 13 و14"),
            ("FaServer", "واقعية التشغيل", "الشريحة 18"),
            ("FaStar", "الابتكار", "الشريحتان 4 و5"),
            ("FaChild", "تجربة المستفيد", "الشرائح 6 إلى 9"),
            ("FaHandHoldingHeart", "تحقيق النفع", "الشرائح 3 و10 و16 و17"),
            ("FaCircleCheck", "الوضوح وقابلية التحقق", "الشريحتان 20 و22 والملحق"),
            ("FaShieldHalved", "الموثوقية", "الشرائح 11 و12 و15")]
    cw, ch, gx, gy = 3.97, 2.65, 0.34, 0.3
    for i, (ic, name, where) in enumerate(crit):
        row, col = divmod(i, 4)
        n_in_row = 4 if row == 0 else 3
        off = 0 if row == 0 else (cw + gx) / 2
        x = X0 + W0 - (col + 1) * cw - col * gx - off
        y = 4.15 + row * (ch + gy)
        add_box(s, x, y, cw, ch, fill=CARD, line=CARDLINE, radius=0.08)
        icon(s, ic, x + cw - 1.05, y + 0.25, 0.8)
        add_text(s, x + 0.25, y + 1.1, cw - 0.5, 0.85, [name], size=20, bold=True, color=OFF, anchor="b")
        add_text(s, x + 0.25, y + 2.0, cw - 0.5, 0.45, [where], size=MIN_PT, color=TURQ)
    notes(s, "خريطة المعايير: كل شريحة رئيسية تحمل في أعلاها رقم القسم واسم المعيار. "
             "التفاصيل والأرقام الكاملة بمصادرها في الملحق بعد شريحة الختام.")

    # ---- M3 problem ----------------------------------------------------------------
    s = dark("01 · المشكلة · معيار تحقيق النفع", "الطفل يسأل الذكاء الاصطناعي عن كل شيء")
    pts = [("FaTriangleExclamation", "محتوى لا يناسبه", "يرى ما لا يريده والداه"),
           ("FaCircleQuestion", "دين بلا مصدر", "قد يخترع حديثا أو يفتيه"),
           ("FaEyeSlash", "والدان مشغولان", "لا يتابعان كل ما يراه"),
           ("FaComments", "طفل لا يحكي كل شيء", "لا يخبر والديه بكل ما يمر به")]
    cw, gap = 3.92, 0.4
    for i, (ic, t_, d) in enumerate(pts):
        x = X0 + W0 - (i + 1) * cw - i * gap
        add_box(s, x, 3.55, cw, 4.3, fill=CARD, line=CARDLINE, radius=0.07)
        icon(s, ic, x + cw / 2 - 0.65, 3.9, 1.3)
        add_text(s, x + 0.2, 5.5, cw - 0.4, 0.7, [t_], size=24, bold=True, color=OFF, align="c")
        add_text(s, x + 0.2, 6.3, cw - 0.4, 1.2, [d], size=20, color=BODY, align="c")
    add_box(s, X0, 8.25, W0, 1.25, fill=TURQ, fill_alpha=12, line=TURQ, radius=0.2)
    add_text(s, X0 + 0.4, 8.25, W0 - 0.8, 1.25,
             ["هدفنا: رفيق لكل أسئلته، بروح إسلامية، يعلّم في وقته ويجيب عن دينه بمصدر"],
             size=24, bold=True, color=OFF, align="c", anchor="m")
    notes(s, "الأطفال يستعملون مساعدات الذكاء الاصطناعي العامة لكل شيء، لا للأسئلة الدينية فقط، فيصلون إلى معلومات ومحتوى لا يريده والداهم. "
             "وحين يسألون عن دينهم قد يخترع المساعد حديثا أو يخطئ في آية أو يفتي في مسألة تحتاج عالما. "
             "والوالدان لا يتسع وقتهما لمتابعة كل ما يراه الطفل، والطفل نفسه لا يحكي لهما كل شيء. "
             "لا نريد أن نمنع الطفل من السؤال: نريده أن يسأل رفيقا عاما بروح إسلامية، يجد الوقت المناسب ليعلّم، "
             "ويجيب عن الأسئلة الدينية بدقة ومن مصدر، ويُبقي الوالدين قريبين.")

    # ---- M4 solution -----------------------------------------------------------------
    s = dark("02 · الحل · معيار الابتكار", "الحل: الصديق الصدوق")
    hw, hh = 10.6, 10.6 / 1.75
    add_picture(s, shot("after/home-ar.webp", 1.75), X0, 3.55, hw, hh, radius=0.03)
    add_text(s, X0 + hw + 0.5, 4.2, W0 - hw - 0.5, 4.0,
             ["رفيق صوتي لكل أسئلة الطفل من 6 إلى 13 سنة، بروح إسلامية: يحاوره بمرح، "
              "ويعلّمه القيم بالمهام والأوسمة، ويجيب عن دينه من مصدر، ويُشرك والديه"],
             size=26, color=OFF, spacing=0)
    add_text(s, X0 + hw + 0.5, 8.35, W0 - hw - 0.5, 0.9,
             [[{"text": "«الصديق الصدوق»", "bold": True, "color": TURQ}, {"text": " = الصديق الذي يصدقك"}]],
             size=20, color=BODY)
    notes(s, "الصديق الصدوق تعني الصديق الذي يصدقك. اسم الشخصية في الحوار «الصديق». "
             "الشاشة الرئيسية للطفل بالعربية لعائلة تجريبية ببيانات اصطناعية. "
             "يعمل بالعربية والإنجليزية، صوتا أو كتابة، على الويب (alsadiqai.com). تطبيق الجوال قيد التطوير.")

    # ---- M5 innovation: six tiles and the badges page ------------------------------------------
    s = dark("02 · الحل · معيار الابتكار", "ما الجديد؟", "مقارنة بمساعد ذكاء اصطناعي عام")
    sw_, sh_ = 6.4, 6.4 / (800 / 537)
    add_picture(s, REPO / "docs/hackathon/review/hk18-judge-accounts/5-child-badges.jpg", X0, 4.25, sw_, sh_, radius=0.03)
    add_text(s, X0, 4.25 + sh_ + 0.15, sw_, 0.5, ["صفحة الأوسمة لطفل في حساب تجريبي"], size=MIN_PT, color=MUTED)
    tiles = [("FaComments", "صديق لا واعظ", "يحاور بمرح ولا يقحم درسا"),
             ("FaStar", "تعلّم باللعب", "مهام وأوسمة ونقاط ومستويات"),
             ("FaChild", "شخصية حية", "30 حركة وإيماءات مع الكلام"),
             ("FaIdCard", "مصدر حين يسأل", "بطاقة مراجعة برابطها"),
             ("FaVolumeHigh", "تلاوة لا صوت آلي", "الآيات بصوت الحصري"),
             ("FaPeopleRoof", "الوالدان معه", "ملخصات ومصادر وتنبيهات")]
    area = W0 - sw_ - 0.5
    tw, th, gx, gy = (area - 0.3) / 2, 1.65, 0.3, 0.2
    for i, (ic, t_, d) in enumerate(tiles):
        row, col = divmod(i, 2)
        x = X0 + W0 - (col + 1) * tw - col * gx
        y = 4.05 + row * (th + gy)
        add_box(s, x, y, tw, th, fill=CARD, line=TURQ if i == 1 else CARDLINE, radius=0.08)
        icon(s, ic, x + tw - 1.05, y + 0.38, 0.85)
        add_text(s, x + 0.25, y + 0.22, tw - 1.45, 0.6, [t_], size=22, bold=True, color=OFF)
        add_text(s, x + 0.25, y + 0.86, tw - 1.45, 0.6, [d], size=MIN_PT, color=BODY)
    notes(s, "صديق لا واعظ: يدردش ويفرح مع الطفل، ولا يقحم درسا لم يطلبه. "
             "تعلّم باللعب: مهام يؤكدها الوالدان، وأوسمة للقيم وللأيام المتتالية، ونقاط ومستويات، واحتفال بصري وصوتي عند الإنجاز؛ "
             "المهام والأوسمة بدأت في مشروع التخرج (DISCLOSURE.md). "
             "شخصية حية: 30 حركة في نموذج الشخصية (إنصات بأنواعه، تفكير، كلام، تحية ووداع، احتفال) وإيماءات يد مع الكلمات، ومزامنة الشفاه. "
             "مصدر حين يسأل: بطاقة من البنك المراجع. تلاوة لا صوت آلي: الآيات بتلاوة محمود خليل الحصري (مرتل) من everyayah.com. "
             "الوالدان معه: ملخص لكل جلسة، ومصادر الأسبوع، وتنبيهات السلامة، وأسئلة للنقاش.")

    # ---- M6 child experience -------------------------------------------------------------
    s = dark("03 · تجربة الطفل · معيار تجربة المستفيد", "تجربة الطفل: يتكلم، فيسمع الصديق ويرد")
    sw, gap = 5.4, 0.34
    shh = sw / 1.6
    steps = [("after/home-ar.webp", "١", "يبدأ بزر واحد"),
             ("after/call-voice-ar.webp", "٢", "يتكلم بصوته"),
             ("after/call-chat-hadith-ar.webp", "٣", "يرى المصدر حين يسأل")]
    for i, (img, n, lab) in enumerate(steps):
        x = X0 + W0 - (i + 1) * sw - i * gap
        add_picture(s, shot(img, 1.6, fx=0.0 if "chat" in img else 0.5), x, 3.7, sw, shh, radius=0.04)
        add_box(s, x + sw - 0.75, 7.35, 0.6, 0.6, fill=TURQ, shape=MSO_SHAPE.OVAL)
        add_text(s, x + sw - 0.75, 7.35, 0.6, 0.6, [n], size=20, bold=True, color=NAVY, align="c", anchor="m")
        add_text(s, x, 7.38, sw - 0.95, 0.6, [lab], size=24, bold=True, color=OFF)
    caption(s, "عربي وإنجليزي · صوت أو كتابة · شخصية بـ30 حركة وإيماءات مع الكلام", y=8.75)
    notes(s, "يبدأ الطفل بزر واحد، ثم يحاور الصديق بصوته، والشخصية تنصت وتفكر وتتكلم بمزامنة الشفاه. "
             "حين يسأل عن دينه تظهر بطاقة المصدر بجانب المحادثة. الكتابة بديل كامل للصوت. "
             "فحص axe: 0 مخالفات على 12 صفحة باللغتين (product-web.md).")

    # ---- M7 source cards ---------------------------------------------------------------
    s = dark("03 · تجربة الطفل · معيار تجربة المستفيد", "بطاقة المصدر: ما يراه الطفل حين يسأل")
    # the verse card's reciter line (y 572-614 of 880) still names the old Muallim edition; cut it out
    cards = [card("after/card-verse-ar.png", cut=(572, 614)), card("after/card-hadith-ar.png"),
             card("after/card-term-ar.png"), card("after/card-faq-ar.png")]
    ch = 5.9
    widths = [ch * a for _, a in cards]
    gap = 0.55
    total = sum(widths) + gap * (len(cards) - 1)
    x = X0 + W0 - (W0 - total) / 2
    for (p, a), w in zip(cards, widths):
        x -= w
        add_picture(s, p, x, 3.45, w, ch, radius=0.03)
        x -= gap
    caption(s, "آية · حديث بدرجته · مصطلح · سؤال شائع: كل بطاقة برابط مصدرها", y=9.5)
    notes(s, "من التطبيق: آية بنص مجمع الملك فهد عبر Quranpedia وترجمة صحيح إنترناشونال، وحديث من الدرر السنية بدرجته، "
             "ومصطلح من معجم الجمهرة، وسؤال من بينات. التلاوة لمحمود خليل الحصري (مرتل) من everyayah.com؛ "
             "قصصنا سطر التلاوة من لقطة الآية لأنها التقطت قبل الانتقال من المصحف المعلم إلى المرتل.")

    # ---- M8 parent experience -------------------------------------------------------------
    s = dark("04 · تجربة الوالدين · معيار تجربة المستفيد", "الوالدان يريان ما رآه طفلهما")
    pw, phh = 5.2, 5.0
    add_picture(s, shot("after/parent-sources-ar.webp", pw / phh, top=0), X0 + W0 - pw, 3.6, pw, phh, radius=0.03)
    iw = W0 - pw - 0.5
    add_picture(s, shot("after/parent-insights-ar.webp", iw / phh, fx=1.0), X0, 3.6, iw, phh, radius=0.03)
    add_text(s, X0 + W0 - pw, 8.75, pw, 0.6, ["مصادر الأسبوع، بروابطها"], size=22, bold=True, color=OFF)
    add_text(s, X0, 8.75, iw, 0.6, ["ملخص أسبوعي وتقدم ومهام، بلا نص المحادثة"], size=22, bold=True, color=OFF)
    notes(s, "صفحة «المصادر التي ناقشها هذا الأسبوع» تسجل ما خدمه البنك فعلا لا ما قاله النموذج (PR #59، والبيانات التجريبية PR #58). "
             "صفحة الرؤى: المستوى والتتابع والملخص الأسبوعي ومهام تنتظر تأكيد الوالدين. "
             "التنبيهات تصل الوالدين حين يرصد الصديق خطرا أو أمرا حساسا، ولا يظهر لهما نص المحادثة.")

    # ---- M8b every feature at a glance -------------------------------------------------------
    s = dark("04 · كل الميزات · معيار تجربة المستفيد", "كل ما في الصديق، بلمحة")
    cols = [("FaChild", "للطفل",
             ["محادثة صوتية", "كتابة", "عربي وإنجليزي", "شخصية ثلاثية الأبعاد", "مزامنة الشفاه",
              "30 حركة وإيماءات", "بطاقة المصدر", "تلاوة مسجلة", "آية طمأنة للحزين", "مهام", "أوسمة",
              "نقاط ومستويات", "أيام متتالية", "احتفال بالإنجاز"]),
            ("FaPeopleRoof", "للوالدين",
             ["حساب الوالد", "حسابات الأبناء", "ملخص كل جلسة", "قيم الأسبوع", "أسئلة للنقاش",
              "مصادر الأسبوع", "تأكيد المهام", "تنبيهات السلامة", "تقدم كل طفل", "بلا نص المحادثة"]),
            ("FaShieldHalved", "الأمان والمحتوى",
             ["بنك 273 عنصرا", "حارس الدور", "حراس المخرجات", "إحالة الفتوى", "إفصاح أنه ذكاء اصطناعي",
              "سقف يومي للصوت", "كتابة عند بلوغ السقف", "صفحة الخصوصية", "حسابات للجنة", "تقييم آلي"])]
    pw, gx = (W0 - 0.6) / 3, 0.3
    for i, (ic, head, chips) in enumerate(cols):
        x = X0 + W0 - (i + 1) * pw - i * gx
        add_box(s, x, 3.3, pw, 6.55, fill=CARD, line=CARDLINE, radius=0.05)
        icon(s, ic, x + pw - 1.0, 3.5, 0.78)
        add_text(s, x + 0.2, 3.5, pw - 1.35, 0.78, [f"{head} ({len(chips)})"], size=24, bold=True, color=TURQ, anchor="m")
        cx, cy = x + pw - 0.2, 4.5
        for v in chips:
            w = 0.145 * len(v) + 0.5
            if cx - w < x + 0.15:
                cx, cy = x + pw - 0.2, cy + 0.6
            add_box(s, cx - w, cy, w, 0.5, fill=PURPLE, fill_alpha=35, radius=0.5)
            add_text(s, cx - w, cy, w, 0.5, [v], size=MIN_PT, color=OFF, align="c", anchor="m")
            cx -= w + 0.1
    notes(s, "قائمة بكل ميزات النظام في النسخة المدمجة. للطفل: محادثة صوتية أو كتابة بالعربية والإنجليزية، شخصية ثلاثية الأبعاد بمزامنة الشفاه "
             "و30 حركة وإيماءات يد مع الكلام، بطاقة المصدر، تلاوة مسجلة، آية طمأنة واحدة حين يحزن أو يخاف، ومهام وأوسمة ونقاط ومستويات وأيام متتالية "
             "واحتفال بالإنجاز. للوالدين: حساب الوالد وحسابات الأبناء، ملخص لكل جلسة، قيم الأسبوع، أسئلة للنقاش، مصادر الأسبوع، تأكيد المهام، "
             "تنبيهات السلامة، وتقدم كل طفل، ولا يظهر لهما نص المحادثة. الأمان: البنك المراجع، حارس الدور، حراس المخرجات، إحالة الفتوى، "
             "الإفصاح بأنه ذكاء اصطناعي، سقف يومي لأحرف الصوت وبعده كتابة فقط، صفحة الخصوصية، حسابات للجنة، وتقييم آلي.")

    # ---- M9 values ------------------------------------------------------------------------
    s = dark("05 · القيم · معيار تحقيق النفع", "38 قيمة يعيشها الطفل",
             "لكل قيمة أحاديث ومصادر مراجعة مرتبطة بها، ولـ37 منها آيات")
    groups = [("FaHandsPraying", "الإيمان والعبادة",
               ["الصلاة", "ذكر الله", "التوكل على الله", "محبة النبي ﷺ", "الإخلاص", "الشكر"]),
              ("FaHandshake", "الصدق والأمانة",
               ["الصدق", "الأمانة", "الوفاء بالوعد", "العدل", "الحياء", "ترك الغيبة"]),
              ("FaPeopleRoof", "الأسرة والمجتمع",
               ["بر الوالدين", "صلة الرحم", "توقير الكبير", "الإحسان إلى الجار", "الأخوة", "إفشاء السلام"]),
              ("FaHandHoldingHeart", "الرحمة والعطاء",
               ["الرحمة", "الرفق بالحيوان", "الكرم", "الصدقة", "رعاية اليتيم", "مساعدة الآخرين",
                "عيادة المريض", "التعاون"]),
              ("FaSeedling", "تهذيب النفس",
               ["الصبر", "كظم الغيظ", "العفو", "التواضع", "القناعة", "الشجاعة", "عدم الإسراف"]),
              ("FaStar", "آداب يومية",
               ["النظافة", "آداب الطعام", "الكلمة الطيبة", "حسن الخلق", "طلب العلم"])]
    assert sum(len(v) for _, _, v in groups) == 38
    pw, phh, gx, gy = 5.4, 3.06, 0.34, 0.12
    for i, (ic, name, vals) in enumerate(groups):
        row, col = divmod(i, 3)
        x = X0 + W0 - (col + 1) * pw - col * gx
        y = 3.95 + row * (phh + gy)
        add_box(s, x, y, pw, phh, fill=CARD, line=CARDLINE, radius=0.06)
        icon(s, ic, x + pw - 0.95, y + 0.12, 0.72)
        add_text(s, x + 0.2, y + 0.18, pw - 1.3, 0.6, [f"{name} ({len(vals)})"], size=22, bold=True,
                 color=TURQ, anchor="m")
        # chips flow right to left
        cx, cy = x + pw - 0.18, y + 0.9
        for v in vals:
            w = 0.125 * len(v) + 0.36
            if cx - w < x + 0.15:
                cx, cy = x + pw - 0.18, cy + 0.52
            add_box(s, cx - w, cy, w, 0.48, fill=PURPLE, fill_alpha=35, radius=0.5)
            add_text(s, cx - w, cy, w, 0.48, [v], size=MIN_PT, color=OFF, align="c", anchor="m")
            cx -= w + 0.1
    notes(s, "القيم الثماني والثلاثون من بنك المحتوى (values.json)، ولكل قيمة أحاديث مراجعة، ولـ37 منها آيات (عيادة المريض لها أحاديث فقط)، ومعها تفسير أو مصطلحات أو أسئلة شائعة لكثير منها، وشرح للطفل بلغتين. "
             "التجميع في ستة محاور للعرض فقط. الترتيب داخل المحاور ليس ترتيب أولوية.")

    # ---- M10 no source, no answer: old slide 17 (light key message) ---------------------------
    # moved as is; only its section label changes (done below)

    # ---- M11 approved sources ---------------------------------------------------------------
    s = dark("06 · مصادر موثوقة · معيار الموثوقية", "مصادر معتمدة فقط: 273 عنصرا مراجعا")
    tiles = [("74", "آية", "نص مجمع الملك فهد عبر Quranpedia"),
             ("94", "حديثا", "البخاري 60 ومسلم 34، من الدرر السنية"),
             ("50", "تفسيرا وعقيدة وفقها وسيرة", "موسوعات الدرر السنية"),
             ("32", "مصطلحا", "معجم الجمهرة"),
             ("23", "سؤالا شائعا", "كتاب بينات"),
             (None, "تلاوة مسجلة", "محمود خليل الحصري (مرتل)، everyayah.com")]
    tw, th, gx, gy = 5.4, 2.65, 0.34, 0.34
    for i, (num, what, src_) in enumerate(tiles):
        row, col = divmod(i, 3)
        x = X0 + W0 - (col + 1) * tw - col * gx
        y = 3.75 + row * (th + gy)
        add_box(s, x, y, tw, th, fill=CARD, line=TURQ if num is None else CARDLINE, radius=0.07)
        if num:
            add_text(s, x + tw - 1.85, y + 0.25, 1.6, 1.0, [num], size=44, bold=True, color=TURQ)
            add_text(s, x + 0.25, y + 0.4, tw - 2.2, 0.8, [what], size=22, bold=True, color=OFF, anchor="m")
        else:
            icon(s, "FaVolumeHigh", x + tw - 1.25, y + 0.25, 1.0)
            add_text(s, x + 0.25, y + 0.4, tw - 1.6, 0.8, [what], size=22, bold=True, color=OFF, anchor="m")
        add_text(s, x + 0.25, y + 1.45, tw - 0.5, 1.0, [src_], size=20, color=BODY)
    notes(s, "273 عنصرا كلها مراجعة ومرتبطة بـ38 قيمة. الآيات: نص KFGQPC العثماني عبر Quranpedia، وترجمة صحيح إنترناشونال. "
             "الأحاديث: البخاري 60 ومسلم 34، كلها صحيحة، برابط الدرر، والإنجليزية لـ42 منها من HadeethEnc برابطها. "
             "التفسير 23 والعقيدة 14 والفقه 8 والسيرة 5 من موسوعات الدرر السنية. المصطلحات من الجمهرة، والأسئلة من بينات. "
             "التلاوة: محمود خليل الحصري (مرتل) من everyayah.com، وتمت إعادة تأكيد مراجعة الآيات الـ74 بعد الانتقال (PR #79). "
             "التفاصيل في الملحق.")

    # ---- M12 how it works -----------------------------------------------------------------
    s = dark("07 · كيف يعمل · معيار الجودة التقنية واستخدام الذكاء الاصطناعي", "كيف يعمل الصديق؟")
    nw, gap, nh, top = 2.95, 0.53, 2.75, 3.55
    nodes = [("FaMicrophone", "سؤال الطفل", "صوت أو كتابة"),
             ("FaShieldHalved", "حارس الدور", "أمان، إحالة، لا فتوى"),
             ("FaBrain", "النموذج يبحث", "search_bank في البنك المراجع"),
             ("FaIdCard", "بطاقة بمصدرها", "من البنك، لا من الذاكرة"),
             ("FaFilter", "حراس المخرجات", "يحذف ما لا مصدر له")]
    xs = []
    for i, (ic, t, d) in enumerate(nodes):
        x = X0 + W0 - (i + 1) * nw - i * gap
        xs.append(x)
        hi = i == 2
        add_box(s, x, top, nw, nh, fill=CARD, line=TURQ if hi else CARDLINE, line_w=2.5 if hi else 1.0, radius=0.08)
        icon(s, ic, x + nw / 2 - 0.45, top + 0.22, 0.9)
        add_text(s, x + 0.12, top + 1.2, nw - 0.24, 0.6, [t], size=20, bold=True, color=TURQ if hi else OFF, align="c")
        add_text(s, x + 0.12, top + 1.8, nw - 0.24, 0.8, [d], size=MIN_PT, color=BODY, align="c")
        if i:
            add_arrow(s, x + nw + 0.07, top + nh / 2 - 0.18, gap - 0.14, 0.36)
    top2, nh2 = 7.15, 1.85
    outs = [(3, "FaChartLine", "لوحة الوالدين", "ما خدمه البنك فعلا"),
            (4, "FaVolumeHigh", "الطفل يسمع ويرى", "صوت ElevenLabs وتلاوة مسجلة")]
    for k, ic, t, d in outs:
        x = xs[k]
        add_arrow(s, x + nw / 2 - 0.2, top + nh + 0.08, 0.4, top2 - top - nh - 0.16, kind=MSO_SHAPE.DOWN_ARROW)
        add_box(s, x, top2, nw, nh2, fill=PURPLE, fill_alpha=30, line=PURPLE, radius=0.08)
        add_text(s, x + 0.15, top2 + 0.25, nw - 0.3, 0.6, [t], size=20, bold=True, color=OFF, align="c")
        add_text(s, x + 0.15, top2 + 0.95, nw - 0.3, 0.8, [d], size=MIN_PT, color=BODY, align="c")
    add_text(s, xs[2], 7.6, X0 + W0 - xs[2], 1.2,
             [[{"text": "القاعدة: ", "bold": True, "color": TURQ},
               {"text": "لا يقتبس النموذج آية أو حديثا إلا مما أعاده البنك"}]],
             size=22, color=OFF)
    notes(s, "1) صوت الطفل عبر LiveKit WebRTC، والكلام إلى نص من OpenAI. "
             "2) حارس الدور (turn_policy) يقرر قبل النموذج: الأمان أولا، ثم الإحالة في الفتوى الشخصية، ثم هل يناسب المصدر. "
             "3) النموذج gpt-5.4-mini يستدعي أداة search_bank على البنك المراجع (273 عنصرا، استرجاع في نحو ميلي ثانية). "
             "4) البطاقة تأتي من البنك نفسه بنصها ورابطها ودرجتها. "
             "5) حراس المخرجات يحذفون أي نسبة كلام إلى الله أو النبي ﷺ لا يرخصها البنك، ويبعدون أقواس القرآن عن محول الصوت. "
             "ثم يسمع الطفل الرد بصوت ElevenLabs Flash v2.5، والآيات بتلاوة مسجلة، ويسجل ما خدمه البنك في لوحة الوالدين (sources_used).")

    # ---- M13 technology ----------------------------------------------------------------------
    s = dark("07 · التقنية · معيار الجودة التقنية واستخدام الذكاء الاصطناعي", "التقنية: مكونات مجربة، وضوابط بنيناها")
    cols = [("ما بنيناه", TURQ, ["حارس الدور قبل النموذج", "أداة search_bank على البنك",
                                 "حراس المخرجات", "سجل المصادر للوالدين", "تقييم آلي: 216 تشغيلا"]),
            ("ما استخدمناه", MUTED, ["LiveKit Agents للصوت", "gpt-5.4-mini للحوار", "OpenAI لتحويل الكلام إلى نص",
                                      "ElevenLabs Flash v2.5 للصوت", "Django وPostgres وReact Three Fiber"])]
    cw = (W0 - 0.6) / 2
    for i, (head, col, items) in enumerate(cols):
        x = X0 + W0 - (i + 1) * cw - i * 0.6
        add_text(s, x, 3.5, cw, 0.7, [head], size=26, bold=True, color=col)
        for j, it in enumerate(items):
            y = 4.4 + j * 1.0
            add_box(s, x, y, cw, 0.8, fill=CARD, line=col if i == 0 else CARDLINE, radius=0.2)
            add_text(s, x + 0.3, y, cw - 0.6, 0.8, [it], size=22, color=OFF, anchor="m")
    notes(s, "اخترنا مكونات معروفة للصوت والنموذج، وبنينا الضوابط التي تجعلها مناسبة لطفل: حارس الدور، "
             "وأداة البحث في البنك، وحراس المخرجات، وسجل المصادر للوالدين، وتقييما آليا (72 محادثة × 3 تشغيلات). "
             "الاستضافة: DigitalOcean مع Caddy، وLiveKit Cloud للوسائط. تطبيق الجوال (Expo) قيد التطوير.")

    # ---- M14 safety -------------------------------------------------------------------------
    s = dark("08 · السلامة · معيار الموثوقية", "السلامة: الطفل أولا")
    rules = [("FaBan", "لا فتوى", "يحيل إلى الوالدين أو عالم"),
             ("FaBell", "تنبيه الوالدين", "في 48 من 60 همّا حقيقيا"),
             ("FaHeart", "طمأنة", "للحزن والقلق"),
             ("FaUserShield", "صادق عن نفسه", "يقول إنه ذكاء اصطناعي")]
    rw = 9.6
    for j, (ic, t, d) in enumerate(rules):
        y = 3.55 + j * 1.5
        icon(s, ic, X0 + W0 - 1.1, y, 1.1)
        add_text(s, X0 + W0 - rw, y - 0.05, rw - 1.4, 0.6, [t], size=24, bold=True, color=OFF)
        add_text(s, X0 + W0 - rw, y + 0.55, rw - 1.4, 0.6, [d], size=20, color=BODY)
    for k, (big, lab) in enumerate([("60 من 60", "عبارة همّ حقيقي رصدها"), ("3 من 66", "شعور عادي نبّه الوالدين خطأ")]):
        y = 3.55 + k * 2.75
        add_box(s, X0, y, 6.4, 2.45, fill=CARD, line=CARDLINE, radius=0.07)
        add_text(s, X0 + 0.3, y + 0.25, 5.8, 1.1, [big], size=44, bold=True, color=TURQ, align="c")
        add_text(s, X0 + 0.3, y + 1.45, 5.8, 0.7, [lab], size=20, color=OFF, align="c")
    caption(s, "اختبار آلي · 6 أكتوبر · PR #72", y=9.6)
    notes(s, "اختبار دقة التنبيه (eval-reports/alert-precision، PR #72): 20 عبارة همّ حقيقي و22 شعورا عاديا بالعربية (خليجي، شامي، فصحى) والإنجليزية، "
             "كل منها 3 مرات. رُصدت الهموم 60 من 60 (33 بقاعدة خادم، والباقي بعلامة النموذج)، ووصل منها تنبيه للوالدين في 48 من 60. "
             "المشاعر العادية: 3 تنبيهات خاطئة من 66، كلها تعبير خليجي واحد عن الإحراج (الفشلة). "
             "off_topic يسجل ولا ينبه الوالدين أبدا. اختبار منفصل للخوف من البيت أو من بالغ (8 عبارات × 3): رُصد 23 من 24، لكنه لم ينبه الوالدين في أي منها لأن النموذج يعدها شأنا عائليا (at_home) فتسلك المسار الهادئ؛ هذا حد معلن في شريحة الحدود.")

    # ---- M15 results (clone of the template's metrics slide) ----------------------------------
    s = new(10)
    kicker(s, "09 · النتائج · معيار تحقيق النفع")
    fill(s, ph(s, 0), ["النتائج: مصدر حين يُطلب، وصدق حين لا يوجد"])
    remove(ph(s, 2))
    for (a, b, c), (big, lab, sub) in zip(
            [(3, 4, 5), (6, 7, 8), (9, 13, 14), (15, 16, 17)],
            [("98%", "طلب مصدرا فوجده", "59 من 60"),
             ("97%", "خارج البنك: قال لا أجد", "67 من 69"),
             ("2/462", "نسب كلاما بلا رخصة", "ردان رصدهما التقييم"),
             ("0/216", "تشغيل انتهى بخطأ", "استقرار الوكيل")]):
        fill(s, ph(s, a), [big])
        fill(s, ph(s, b), [lab])
        fill(s, ph(s, c), [sub])
    fill(s, ph(s, 18), ["تقييم آلي · 6 أكتوبر · PR #76 · الجدول في الملحق"])
    notes(s, "تقرير source-timing النهائي (PR #76، commit c8ab33be (dirty)): 72 محادثة × 3 تشغيلات بالصوت، gpt-5.4-mini. "
             "حين طلب الطفل مصدرا خدمه الصديق في 59 من 60. وحين لم يكن الجواب في البنك قال إنه لا يجد مصدرا في 67 من 69. "
             "ردان من 462 نسبا كلاما إلى الله أو النبي ﷺ خارج ما يرخصه البنك، وكلاهما بالعربية؛ نعرضهما كما هما. "
             "ولم يفشل أي تشغيل من 216. نقاط الضعف (عرض المصدر من تلقاء نفسه 34%) في شريحة الحدود.")

    # ---- M16 built in 3 days ---------------------------------------------------------------
    s = dark("10 · ما بنيناه · معيار تحقيق النفع", "ما بنيناه في 3 أيام")
    cw = 7.3
    xr, xl = X0 + W0 - cw, X0
    add_text(s, xr, 3.45, cw, 0.6, ["قبل 4 أكتوبر"], size=24, bold=True, color=MUTED, align="c")
    add_text(s, xl, 3.45, cw, 0.6, ["بعد 6 أكتوبر"], size=24, bold=True, color=TURQ, align="c")
    rows = [("6 موضوعات و19 مرجعا بلا رابط", "273 عنصرا مراجعا و38 قيمة"),
            ("لا بطاقة مصدر", "بطاقة بمصدرها، وصفحة للوالدين"),
            ("صوت xAI، والفك وحده يتحرك", "صوت ElevenLabs، وشفاه و30 حركة"),
            ("بلا تقييم آلي", "حراس وتقييم آلي: 216 تشغيلا")]
    for j, (b, a) in enumerate(rows):
        y = 4.25 + j * 1.3
        add_box(s, xr, y, cw, 1.05, fill=CARD, line=CARDLINE, radius=0.15)
        add_text(s, xr + 0.3, y, cw - 0.6, 1.05, [b], size=22, color=BODY, align="c", anchor="m")
        add_arrow(s, xl + cw + 0.25, y + 0.33, W0 - 2 * cw - 0.5, 0.4)
        add_box(s, xl, y, cw, 1.05, fill=TURQ, fill_alpha=14, line=TURQ, radius=0.15)
        add_text(s, xl + 0.3, y, cw - 0.6, 1.05, [a], size=22, bold=True, color=OFF, align="c", anchor="m")
    caption(s, "الإفصاح الكامل: DISCLOSURE.md", y=9.6)
    notes(s, "قبل التحدي: مشروع تخرج فيه وكيل صوتي بصوت xAI وشخصية ثلاثية الأبعاد يتحرك فكها فقط، و6 موضوعات أخلاقية و19 مرجعا نصيا بلا رابط. "
             "خلال 4 إلى 6 أكتوبر: بنك 273 عنصرا مراجعا و38 قيمة، وسياسة الدور والحراس وبطاقات المصادر، وصفحة المصادر للوالدين، "
             "وصوت ElevenLabs ومزامنة الشفاه، ونموذج شخصية جديد بـ30 حركة (إنصات وتفكير وكلام وتحية واحتفال) وإيماءات يد مع الكلام، والتقييم الآلي. التفاصيل في شريحة الإفصاح بالملحق.")

    # ---- M17 operational realism (metrics clone) -----------------------------------------------
    s = new(10)
    kicker(s, "11 · التشغيل · معيار واقعية التشغيل")
    fill(s, ph(s, 0), ["جاهز للتشغيل، بتكلفة معروفة"])
    remove(ph(s, 2))
    for (a, b, c), (big, lab, sub) in zip(
            [(3, 4, 5), (6, 7, 8), (9, 13, 14), (15, 16, 17)],
            [(EST['session'].split(' إلى ')[1] + "$", "للجلسة، حدا أعلى", f"تقدير: {EST['session']} دولار"),
             ("10", "جلسات متزامنة", "لعامل واحد، مقيس 5 أكتوبر"),
             ("165MB", "ذاكرة لكل جلسة", "و0.1 نواة، مقيس 5 أكتوبر"),
             ({"text": "22 أكتوبر", "size": 48}, "يعمل طوال التحكيم", "نشر آلي وسقف إنفاق")]):
        fill(s, ph(s, a), [big])
        fill(s, ph(s, b), [lab])
        fill(s, ph(s, c), [sub])
    fill(s, ph(s, 18), [f"تقدير: {EST['judges']} دولارا لـ30 محكما طوال التحكيم · المنهج في الملحق"])
    notes(s, "مقيس على نسخة محلية بخدمات OpenAI وElevenLabs الحقيقية في 5 أكتوبر (LOAD-REHEARSAL.md): 10 جلسات صوتية متزامنة على عامل وكيل واحد، "
             "و0.1 نواة و165 ميغابايت لكل جلسة. زمن الخادم حتى أول صوت كان نحو 2.6 ثانية تحت الحمل، وهو يقيس تغير الزمن مع الحمل لا قيمته المطلقة؛ القياس من طرف إلى طرف في latency/RESULTS.md أعلى، فلا نعرضه رقما رئيسيا. "
             f"التكلفة تقدير لا قياس: {EST['session']} دولار للجلسة، من الوحدات المقيسة وأسعار المزودين المعلنة في 6 أكتوبر 2026 (cost_estimate.py). "
             "النشر آلي (deploy.yml): يطبق الترحيلات ويفشل إن لم يرد /api/health/. سقف يومي لأحرف الصوت، وبعده تبدأ الجلسات بالكتابة فقط. "
             "نلتزم بإبقاء alsadiqai.com يعمل حتى 22 أكتوبر؛ هذا التزام لا قياس.")

    # ---- M18 limitations and next steps ----------------------------------------------------------
    s = dark("12 · الحدود والخطوة التالية · معيار الوضوح", "ما نعرف أنه ناقص، وما بعده")
    cw = (W0 - 0.6) / 2
    blocks = [("FaTriangleExclamation", "حدود نعرفها", MUTED,
               ["عرض المصدر تلقائيا أقل مما نريد", "بعض المخاوف الحساسة لا تصل الوالدين بعد",
                "بعض التعبيرات العامية تُفهم خطأ", "راجعه طالب علم شرعي، لا عالم بعد",
                "تطبيق الجوال قيد التطوير"]),
              ("FaRoad", "الخطوة التالية", TURQ,
               ["تنبيهات أدق للوالدين", "مراجعة من عالم أو جهة علمية",
                "فهم أوسع للهجات", "تجربة مع أسر حقيقية", "قيم وتلاوات أكثر"])]
    for i, (ic, head, col, items) in enumerate(blocks):
        x = X0 + W0 - (i + 1) * cw - i * 0.6
        add_box(s, x, 3.45, cw, 6.0, fill=CARD, line=col if i else CARDLINE, radius=0.05)
        icon(s, ic, x + cw - 1.15, 3.7, 0.85, color="turq" if i else "white", ring=col)
        add_text(s, x + 0.3, 3.75, cw - 1.6, 0.8, [head], size=26, bold=True, color=col if i else OFF, anchor="m")
        for j, it in enumerate(items):
            y = 4.85 + j * 0.9
            add_box(s, x + cw - 0.62, y + 0.2, 0.22, 0.22, fill=col, shape=MSO_SHAPE.OVAL)
            add_text(s, x + 0.3, y, cw - 1.1, 0.65, [it], size=21, color=OFF, anchor="m")
    notes(s, "عرض المصدر من تلقاء نفسه: 34% (43 من 126) حين يناسب، و13% فقط للأعمار 6 إلى 9 مقابل 53% للأعمار 10 إلى 13 (PR #76). "
             "الإحالة في غير موضعها حين لا يوجد الجواب في البنك: 23% (16 من 69). "
             "الخوف من البيت أو من بالغ: رُصد 23 من 24 ولم ينبه الوالدين في أي منها (at_home يسلك المسار الهادئ). التنبيه الخاطئ: 3 من 66، تعبير خليجي واحد لم تغيره ثلاث صياغات للتعليمات (PR #72). "
             "راجع المحتوى طالب علم شرعي، ولم يراجعه عالم بعد؛ نقترح مراجعة من عالم أو جهة علمية بعد التحدي (سير المراجعة في الملحق).")

    # ---- M18b family accounts and judge accounts --------------------------------------------------
    s = dark("13 · الحسابات وتجربة اللجنة · معيار الوضوح وقابلية التحقق", "حسابات الأسرة، وحسابات جاهزة للجنة")
    sw_, sh_ = 7.2, 7.2 / (800 / 537)
    add_picture(s, REPO / "docs/hackathon/review/hk18-judge-accounts/1-parent-two-children.jpg", X0, 3.7, sw_, sh_, radius=0.03)
    add_text(s, X0, 3.7 + sh_ + 0.15, sw_, 0.5, ["صفحة الأبناء في حساب والد تجريبي"], size=MIN_PT, color=MUTED)
    rows = [("FaUserShield", "الوالد أولا", "يسجّل الوالد ثم ينشئ حسابات أبنائه؛ الطفل لا يسجّل وحده"),
            ("FaUsers", "حسابات جاهزة للجنة", "والد وطفلان، بأسبوع من الجلسات والمهام والأوسمة"),
            ("FaCircleQuestion", "لماذا؟", "الصديق يبني على كل محادثة، فالحساب الجديد لا يُظهر الأثر")]
    rx = X0 + sw_ + 0.6
    rw = X0 + W0 - rx
    for j, (ic, t_, d) in enumerate(rows):
        y = 3.6 + j * 1.95
        add_box(s, rx, y, rw, 1.7, fill=CARD, line=TURQ if j == 1 else CARDLINE, radius=0.08)
        icon(s, ic, rx + rw - 1.1, y + 0.42, 0.85)
        add_text(s, rx + 0.25, y + 0.2, rw - 1.5, 0.6, [t_], size=24, bold=True, color=OFF)
        add_text(s, rx + 0.25, y + 0.85, rw - 1.5, 0.75, [d], size=20, color=BODY)
    notes(s, "لا يستطيع الطفل إنشاء حساب: التسجيل للوالد فقط، ثم يضيف الوالد أبناءه وينشئ حساباتهم، ويدخل كل طفل بحسابه. "
             "أعددنا للجنة خمسة حسابات والد (judge1 إلى judge5)، لكل منها طفلة عمرها 7 سنوات بالعربية وطفل عمره 11 سنة بالإنجليزية، "
             "بأسبوع اصطناعي من الجلسات: ملخصات ومصادر وأسئلة للنقاش ومهام بكل حالاتها وأوسمة من محرك الأوسمة الحقيقي. "
             "السبب: الصديق يبني على كل محادثة (الذاكرة والملخصات والمستويات والأوسمة)، فلو بدأ المحكم بحساب جديد لما رأى أثرا حقيقيا. "
             "يستطيع المحكم أن يبدأ جلسات جديدة صوتا أو كتابة مع هؤلاء الأطفال. كل الأسماء والبيانات اصطناعية (JUDGE-ACCOUNTS.md، hk-18).")

    # ---- appendix: source timing table (clone of the dark table slide) ---------------------------
    a_timing = new(6)
    kicker(a_timing, "ملحق · النتائج")
    fill(a_timing, ph(a_timing, 0), ["توقيت المصدر: الجدول الكامل"])
    fill(a_timing, ph(a_timing, 2), ["72 محادثة × 3 تشغيلات · gpt-5.4-mini · 6 أكتوبر 2026 · 0 من 216 تشغيلا بخطأ"])
    gf = [sh for sh in a_timing.shapes if sh.has_table][0]
    fill_table(a_timing, gf, [
        ["المقياس", "الكل", "عربي", "إنجليزي"],
        ["عرض المصدر حين يناسب", "34% (43/126)", "32%", "36%"],
        ["مصدر في غير موضعه (الأقل أفضل)", "3% (7/207)", "5%", "2%"],
        ["طلب مصدرا فوجده", "98% (59/60)", "100%", "97%"],
        ["خارج البنك: قال لا أجد", "97% (67/69)", "94%", "100%"],
        ["خارج البنك: إحالة في غير موضعها (الأقل أفضل)", "23% (16/69)", "6%", "39%"],
        ["نسب كلاما بلا رخصة (الأقل أفضل)", "2 من 462", "2 من 222", "0 من 240"],
    ], [8.3, 3.2, 2.6, 2.6], row_h=0.66, size=20, header_size=22)
    fill(a_timing, ph(a_timing, 3), ["eval-reports/source-timing/final/report.md · PR #76 · commit c8ab33be (dirty) · "
                      "عرض المصدر حين يناسب: 13% للأعمار 6 إلى 9، و53% للأعمار 10 إلى 13"])

    # ---- appendix: alert precision table -----------------------------------------------------------
    a_alert = new(6)
    kicker(a_alert, "ملحق · السلامة")
    fill(a_alert, ph(a_alert, 0), ["دقة تنبيه الوالدين"])
    fill(a_alert, ph(a_alert, 2), ["عبارات اصطناعية، كل منها 3 مرات · gpt-5.4-mini · 6 أكتوبر 2026"])
    gf = [sh for sh in a_alert.shapes if sh.has_table][0]
    fill_table(a_alert, gf, [
        ["المجموعة", "عدد العبارات", "رُصدت", "نبّهت الوالدين"],
        ["هموم حقيقية", "20 × 3", "60 من 60", "48 من 60"],
        ["مشاعر عادية", "22 × 3", "6 من 66", "3 من 66"],
        ["تعبيرات محجوزة: هموم", "4 × 3", "12 من 12", "9 من 12"],
        ["تعبيرات محجوزة: مشاعر عادية", "8 × 3", "3 من 24", "3 من 24"],
        ["الخوف من البيت أو من بالغ", "8 × 3", "23 من 24", "0 من 24"],
    ], [6.4, 3.3, 3.5, 3.5], row_h=0.7, size=20, header_size=22)
    fill(a_alert, ph(a_alert, 3), ["eval-reports/alert-precision/README.md · PR #72 · off_topic يسجل ولا ينبه الوالدين · "
                     "كل التنبيهات الخاطئة تعبير خليجي واحد عن الإحراج"])

    # ---- section labels on moved slides -------------------------------------------------------------
    kicker(old[12], "14 · الفريق")
    fill(old[12], ph(old[12], 2), ["فريق الصديق الصدوق"])
    team = old[12]
    fill(team, by_name(team, "TextBox 694"), [{"text": "صاحب الفكرة وقائد الفريق", "size": MIN_PT},
                                             {"text": "المنطق الخلفي وبنك المحتوى", "size": MIN_PT},
                                             {"text": "طالب علم راجع كل المصادر وشروحها", "size": MIN_PT}])
    fill(team, by_name(team, "TextBox 698"), [{"text": "تجربة المستخدم والواجهة كاملة", "size": MIN_PT}])
    fill(team, by_name(team, "TextBox 702"), [{"text": "مساعد في مراجعة أقسام الدرر", "size": MIN_PT},
                                             {"text": "وفي تجربة المستخدم والواجهة", "size": MIN_PT}])
    fill(team, by_name(team, "TextBox 703"),
         ["ملاحظة: كان موسى وطارق في الفريق عند التسجيل، ثم اعتذرا بعد بدء التحدي لظروف العمل والدراسة، "
          "فلم يُذكرا هنا لأنهما لم يشاركا في العمل"])
    notes(team, "عبدالرحمن سلامة: صاحب الفكرة وقائد الفريق، وبنى المنطق الخلفي في الخادم ومنطق بنك المحتوى، "
                "وهو طالب العلم الشرعي الذي راجع المصادر وشروحها عنصرا عنصرا، وأدار الفريق. "
                "مجد عوض: تجربة المستخدم والواجهة كاملة. عبدالرحمن محملجي: مساعد في مراجعة أقسام الدرر السنية وفي تجربة المستخدم والواجهة. "
                "موسى وطارق سُجّلا في الفريق، ثم اعتذرا بعد بدء التحدي لظروف العمل والدراسة، فلم نذكرهما أعضاء لأنهما لم يعملا في المشروع.")
    kicker(old[13], "15 · التحقق · معيار الوضوح وقابلية التحقق")
    fill(old[13], ph(old[13], 2), ["كل رقم بمصدره وتاريخه، والتفاصيل في الملحق"])
    add_text(old[13], 10.40, 9.2, 8.02, 0.8,
             ["بموافقة رواء من فريق التنظيم: ننشر من المستودع الخاص لأسباب أمنية، والعام مطابق له. "
              "للاطلاع على الخاص تواصلوا مع قائد الفريق"],
             size=MIN_PT, color=BODY)
    notes(old[13], "المستودع العام: حصلنا على موافقة رواء من فريق التنظيم على نشر مستودع عام، مع إبقاء النشر على الخادم من المستودع الخاص "
                   "لأسباب أمنية، فلا يمكن النشر من المستودع العام حاليا. النسختان متطابقتان. إن أرادت اللجنة صلاحية اطلاع على المستودع الخاص، "
                   "فليتواصلوا مع قائد الفريق عبدالرحمن سلامة، ليروا أنه لم يتغير شيء بين المستودع العام والخاص منذ التسليم.")
    add_text(old[14], 4.17, 10.15, 11.67, 0.55,
             ["للمزيد من التفاصيل والأرقام بمصادرها: الملحق في الشرائح التالية"],
             size=MIN_PT, color=TURQ, align="c")
    # the key message slide: the decision line moves to the notes
    fill(old[17], ph(old[17], 2), ["القرار 3 في خطة المشروع"])
    # the eval counts a referral as wrong when nothing is in the bank; the slide says what it should do
    fill(old[17], ph(old[17], 1), ["إن لم يجد الصديق عنصرا مراجعا في البنك، يقول إنه لا يجد مصدرا موثوقا، ولا يكتب من ذاكرته"])
    lbl = [sh for sh in old[17].shapes if sh.shape_type == 17 and sh.has_text_frame]
    for sh in lbl:
        if "ملحق" in sh.text_frame.text:
            fill(old[17], sh, ["06 · مصادر موثوقة · معيار الموثوقية"])
    for n, lab in [(5, "ملحق · آلية العمل"), (6, "ملحق · مصادر موثوقة"), (10, "ملحق · نتائج 5 أكتوبر"),
                   (11, "ملحق · التشغيل")]:
        kicker(old[n], lab)
    fill(old[15], by_name(old[15], "TextBox 530"),
         ["آلية العمل · المحتوى · النتائج كاملة · التكلفة · الإفصاح"])
    # cover
    fill(old[1], ph(old[1], 1), ["رفيق صوتي يعلّم الطفل 38 قيمة إسلامية بحوار ممتع ومهام وأوسمة، ويقرّبه من والديه"])

    # ---- order ---------------------------------------------------------------------------------------
    mm = [s for s in made if s not in (a_timing, a_alert)]   # main slides in creation order
    main = [ids[1]] + mm[:9] + [ids[17]] + mm[9:] + [ids[12], ids[13], ids[14]]
    appendix = [ids[15], ids[16], ids[5], ids[6], ids[18], ids[19], ids[20], ids[21],
                a_timing, a_alert, ids[10], ids[22], ids[23], ids[11], ids[24], ids[25], ids[26], ids[27]]
    lst = prs.slides._sldIdLst
    by_id = {int(el.get("id")): el for el in lst}
    order = [by_id[x.slide_id] if hasattr(x, "slide_id") else x for x in main + appendix]
    keep = {id(e) for e in order}
    for el in list(lst):
        lst.remove(el)
        if id(el) not in keep:
            prs.part.drop_rel(el.rId)
    for el in order:
        lst.append(el)
    prs.save(OUTFILE)
    print("wrote", OUTFILE, len(order), "slides; main", len(main))


if __name__ == "__main__":
    build(sys.argv[1])
