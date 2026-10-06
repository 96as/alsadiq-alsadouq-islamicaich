"""Al-Sadiq gesture runtime (T1).  Pure standard library, no imports from the rest of the repo.

Given a reply clause it returns, per sentence, the talk_style and the expression, and per word the gesture anchors,
beats and head gestures (BEHAVIOUR-SPEC sections 2.5-2.9, 4.5-4.7):

    from gesture_runtime import GestureModel
    m = GestureModel.load("gesture_model.json")          # missing or broken file -> lexicon fallback, never raises
    plan = m.plan("Well done! I am proud of you.", lang="en")
    plan["anchors"]   # [{"i": 1, "w": "done!", "id": "clap", "k": 2, "conf": 0.9, "combo": None, "hand": "B"}, ...]

The same module is used for training (train.py imports it), so the features are identical in training and serving.
It also holds the lexicon-only planner (the baseline and the fallback) and the SPEC 8.5 keyword talk_style classifier.

Public API
    GestureModel.load(path=None)  -> GestureModel (mode "model" or "lexicon")
    GestureModel.plan(text, *, lang=None, talk_style_hint=None, used_ids=(), mode=None) -> dict
    GestureModel.plan_clause(text, *, lang=None, talk_style_hint=None, used_ids=(), seed=0)
                                  -> {"anchors": [(word_ix, word_norm, id, k, hand)],
                                      "sentences": [(word_ix, talk_style, expression)]}   (SPEC 8.2 shape)
    keyword_talk_style(text)      -> one of STYLES (SPEC 8.5, no hints)
"""
import json
import math
import os
import re
import zlib

VERSION = "1.0"

SEMANTIC = ("you me heart wide small list shrug wow idea beckon clap cheer think ask present calm round up hug").split()
ONESHOT = ["greet", "wave", "bye"]
HEAD = ["H_Nod", "H_Shake"]
TAGS = ["O", "beat"] + SEMANTIC + HEAD + ONESHOT          # the word-model classes (26)
TAG_ID = {t: i for i, t in enumerate(TAGS)}
SEM_SET = frozenset(SEMANTIC)
ARM_TAGS = frozenset(SEMANTIC + ONESHOT)
STYLES = ["explain", "story", "praise", "question", "gentle"]
EXPRESSIONS = ["neutral", "happy", "proud", "soft", "excited", "curious", "surprised"]
STYLE_DEFAULT_EXPRESSION = {"explain": "neutral", "story": "happy", "praise": "proud", "gentle": "soft",
                            "question": "curious"}
STYLE_SETS = {
    "explain": frozenset("you me heart list small wide present idea round ask think shrug cheer up beckon calm wow".split()),
    "story": frozenset("wide round up small wow present beckon hug idea list think shrug me heart you".split()),
    "praise": frozenset("clap cheer heart you wow hug present".split()),
    "question": frozenset("ask shrug think you me idea present heart".split()),
    "gentle": frozenset("heart calm me you hug".split()),
}
HANDS = {"you": "R", "me": "R", "heart": "R", "list": "R", "present": "R", "ask": "R", "think": "R", "idea": "R",
         "beckon": "R", "up": "R", "wide": "B", "small": "B", "shrug": "B", "wow": "B", "clap": "B", "cheer": "B",
         "calm": "B", "round": "B", "hug": "B", "greet": "R", "wave": "R", "bye": "R"}
PRIORITY = {"wide": 1.2, "small": 1.2, "round": 1.2, "up": 1.2, "ask": 1.3}
ICONIC = frozenset(["wide", "small", "round", "up"])
# registered combos (SPEC 2.9): (first id, second id) -> name
COMBOS = {("heart", "you"): "heart_you", ("think", "idea"): "think_idea", ("wow", "clap"): "wow_clap",
          ("calm", "heart"): "calm_heart", ("wide", "up"): "wide_up"}
SHORT_FILL = frozenset(["ask", "clap", "list"])             # a beat is not added to a phrase these fill
# review fixes 2026-10-05 (Opus T1 review):
# * The gold labels drifted from LABEL-GUIDE rule 3 (k = 2 unless gentle or a soft word): 65% of explain anchors are
#   k = 1, so the learned intensity played most gestures at 0.8 amplitude.  Outside gentle the model's k is floored at
#   this value (set it to 1 to get the raw learned k back).  Gentle sentences keep k = 1.
INTENSITY_FLOOR_OUTSIDE_GENTLE = 2
# * `round` matched بكرة (tomorrow) and فكرة (idea) through the clitic strip (ب/ف + كرة).  The gold labels never put
#   `round` on these words; drop the candidate in both modes.  Matched on the normalised, edge-stripped token.
NOT_ROUND_SUFFIXES = ("بكره", "فكره")

HASH_BITS = 20
MASK = (1 << HASH_BITS) - 1

# ---------------------------------------------------------------------------------------------------------------
# normalisation (SPEC 8.3, identical to train/normalize.py)

_DIACRITICS = re.compile("[ؗ-ًؚ-ْٰ]")
_MAP = str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا",
                      "ى": "ي", "ة": "ه", "ؤ": "و", "ئ": "ي",
                      "’": "'", "‘": "'"})
_WS = re.compile(r"\s+")
_EDGE = re.compile(r"^[^\w']+|[^\w']+$", re.UNICODE)
_TRAIL = re.compile(r"[^\w']+$", re.UNICODE)
_AR = re.compile("[؀-ۿ]")
CLITICS = ("وال", "بال", "فال", "كال",
           "لل", "ال", "و", "ف", "ب", "ل")
_CLAUSE_END = re.compile(r"[.!?؟,،;:—؛]$")
_SENT_END = re.compile(r"[.!?؟]+[\"')\]]*$")


def normalize(text):
    if not text:
        return ""
    s = _DIACRITICS.sub("", text).replace("ـ", "").translate(_MAP).lower()
    return _WS.sub(" ", s).strip()


def strip_clitic(tok):
    for c in CLITICS:
        if tok.startswith(c) and len(tok) - len(c) >= 3:
            return tok[len(c):]
    return tok


def is_arabic(text):
    return bool(_AR.search(text or ""))


NEGATORS = frozenset(normalize(w) for w in ("مو مب مش ما لا ليس "
                                            "لست مهو مافي not no never "
                                            "don't dont isn't wasn't aren't can't won't").split())


def hfeat(f):
    return zlib.crc32(f.encode("utf-8")) & MASK


# ---------------------------------------------------------------------------------------------------------------
# SPEC 8.5 keyword talk_style classifier (no hints) and 8.4 question words

_PRAISE = ("ما شاء الله|ماشاء الله|"
           "تبارك الله|أحسنت|برافو|"
           "يا بطل|يا بطلة|رائع|رائعة|"
           "ممتاز|ممتازة|شاطر|شاطرة|"
           "فخور|فخورة|كفو|جميل جدا|"
           "well done|great job|good job|amazing|awesome|proud of you|brilliant|fantastic|excellent|mashallah|"
           "masha allah|way to go|bravo")
_GENTLE = ("لا بأس|لا تحزن|لا تخاف|"
           "لا تقلق|أفهمك|أفهم شعورك|"
           "أعرف أنه صعب|طبيعي تحس|"
           "قلبي معك|أنا معك|أنا هنا|"
           "خذ نفس|الله يصبرك|"
           "it's okay|it's ok|don't worry|i understand|that sounds hard|that must be hard|i'm sorry|i'm here|"
           "you're not alone|take a deep breath|it's normal to feel")
_STORY = ("كان يا ما كان|في يوم من الأيام|"
          "يحكى أن|ذات يوم|مرة من المرات|"
          "خلني أحكي لك|اسمع هالقصة|"
          "قصة|حكاية|once upon a time|one day|long ago|let me tell you a story|"
          "here's a story|there was once|the story of")
_CURIOUS = ("ليش|ليه|لماذا|كيف|شلون|وش|"
            "ايش|شو|ماذا|متى|وين|أين|"
            "مين|هل|كم|ما هو|ما هي|من هو|"
            "من هي|قل لي|علمني|أبي أعرف|"
            "أريد أن أعرف|سؤال|"
            "why|how|what|when|where|who|which|can you|could you|do you|does|is it|are you|tell me|explain|question|i wonder")


def _marker_list(s):
    return [normalize(x) for x in s.split("|")]


_PRAISE_M = _marker_list(_PRAISE)
_GENTLE_M = _marker_list(_GENTLE)
_STORY_M = _marker_list(_STORY)
_CURIOUS_M = _marker_list(_CURIOUS)
_TOKEN = re.compile(r"[\w']+", re.UNICODE)


def keyword_talk_style(text):
    """SPEC 8.5 without turn hints: praise > gentle > story > question > explain."""
    n = normalize(text)
    toks = _TOKEN.findall(n)
    padded = " " + " ".join(toks) + " "
    for m in _PRAISE_M:
        if " " + m + " " in padded:
            return "praise"
    for m in _GENTLE_M:
        if " " + m + " " in padded:
            return "gentle"
    for m in _STORY_M:
        if " " + m + " " in padded:
            return "story"
    t = text.strip()
    if t.endswith("?") or t.endswith("؟"):
        return "question"
    head = " ".join(toks) + " "
    for m in _CURIOUS_M:
        if head.startswith(m + " "):
            return "question"
    return "explain"


# ---------------------------------------------------------------------------------------------------------------
# lexicon (compiled from the raw lexicon.json structure; same matching as train/lexscan.py)

class Lexicon:
    def __init__(self, raw):
        self.names = set(normalize(n) for n in raw.get("neutral_names", []))
        self.kind = {}
        self.table = {}
        for gid, d in raw["ids"].items():
            self.kind[gid] = d.get("kind")
            neg_ok = set(normalize(c.rstrip("?؟")) for c in d.get("neg_ok", []))
            cand = set(normalize(c.rstrip("?؟")) for c in d.get("candidate_only", []))
            seen = set()
            for lang in ("ar", "en"):
                for cue in d.get(lang, []):
                    qreq = cue.endswith("؟") or cue.endswith("?")
                    toks = tuple(normalize(cue.rstrip("?؟")).split())
                    key = (toks, qreq, gid)
                    if not toks or key in seen:
                        continue
                    seen.add(key)
                    nrm = " ".join(toks)
                    self.table.setdefault(toks[0], []).append((toks, gid, qreq, nrm in neg_ok, nrm in cand))
        for k in self.table:
            self.table[k].sort(key=lambda e: -len(e[0]))

    def scan(self, toks, forms, trail):
        """Hits [{s, e, id, neg, neg_ok, cand}] for the tokens (forms = [(norm, alt)], trail = trailing punctuation)."""
        n = len(forms)
        order = []
        table = self.table
        for i in range(n):
            f0 = forms[i]
            ents = list(table.get(f0[0], ()))
            if f0[1] != f0[0]:
                ents += table.get(f0[1], ())
            if not ents:
                continue
            ents.sort(key=lambda e: -len(e[0]))
            for toks_c, gid, qreq, neg_ok, cand in ents:
                L = len(toks_c)
                if i + L > n:
                    continue
                ok = True
                for j in range(L):
                    f = forms[i + j]
                    if toks_c[j] != f[0] and toks_c[j] != f[1]:
                        ok = False
                        break
                if not ok:
                    continue
                if qreq and not ("?" in trail[i + L - 1] or "؟" in trail[i + L - 1]):
                    continue
                if f0[0] in self.names:
                    continue
                order.append((i, i + L, gid, neg_ok, cand))
        order.sort(key=lambda h: (-(h[1] - h[0]), h[0]))
        kept = []
        for h in order:
            if any(k[0] <= h[0] and h[1] <= k[1] and (k[1] - k[0]) > (h[1] - h[0]) for k in kept):
                continue
            if any(k[0] == h[0] and k[1] == h[1] and k[2] == h[2] for k in kept):
                continue
            kept.append(h)
        kept.sort(key=lambda h: (h[0], h[1]))
        hits = []
        for s, e, gid, neg_ok, cand in kept:
            neg = False
            for j in range(s - 1, max(-1, s - 3), -1):
                if forms[j][0] in NEGATORS and not _CLAUSE_END.search(toks[j]):
                    neg = True
                    break
                if _CLAUSE_END.search(toks[j]):
                    break
            if neg_ok:
                neg = False
            hits.append({"s": s, "e": e, "id": gid, "neg": neg, "neg_ok": neg_ok, "cand": cand,
                         "kind": self.kind[gid]})
        return hits


# ---------------------------------------------------------------------------------------------------------------
# text analysis

class Ctx:
    """Everything the models need about one clause, computed once."""
    __slots__ = ("text", "lang", "toks", "n", "alt", "trail", "forms", "hits", "tok_hits", "phr", "phr_of",
                 "sents", "sent_of", "negnear", "n_tok")


def _phrases(toks, max_words=12):
    out = []
    start = 0
    for i, t in enumerate(toks):
        if _CLAUSE_END.search(t) or i + 1 - start >= max_words:
            out.append((start, i + 1))
            start = i + 1
    if start < len(toks):
        out.append((start, len(toks)))
    return out


def _sentences(toks):
    """Sentence starts: after a token ending . ! ? or the Arabic question mark; a short leading interjection
    (one or two tokens ending in ! or ...) belongs to the sentence that follows it (the teachers' convention)."""
    st = [0]
    for i, t in enumerate(toks[:-1]):
        if _SENT_END.search(t):
            st.append(i + 1)
    if len(st) > 1 and st[1] <= 2 and (toks[st[1] - 1].endswith("!") or toks[st[1] - 1].endswith("...")
                                        or toks[st[1] - 1].endswith("…")):
        del st[1]
    return st


def analyse(lexicon, text, lang=None):
    c = Ctx()
    c.text = text
    toks = text.split()
    c.toks = toks
    c.n_tok = len(toks)
    c.lang = lang or ("ar" if is_arabic(text) else "en")
    n, alt, trail, forms = [], [], [], []
    for t in toks:
        core = _EDGE.sub("", t)
        nn = normalize(core)
        aa = strip_clitic(nn) if is_arabic(nn) else nn
        n.append(nn)
        alt.append(aa)
        forms.append((nn, aa))
        trail.append(t[len(t.rstrip("?؟!.,;:،؛")):])
    c.n, c.alt, c.trail, c.forms = n, alt, trail, forms
    c.hits = lexicon.scan(toks, forms, trail) if toks else []
    th = [[] for _ in toks]
    for h in c.hits:
        for i in range(h["s"], h["e"]):
            th[i].append(h)
    c.tok_hits = th
    c.phr = _phrases(toks)
    po = [0] * len(toks)
    for k, (a, b) in enumerate(c.phr):
        for i in range(a, b):
            po[i] = k
    c.phr_of = po
    c.sents = _sentences(toks)
    so = [0] * len(toks)
    for k, a in enumerate(c.sents):
        b = c.sents[k + 1] if k + 1 < len(c.sents) else len(toks)
        for i in range(a, b):
            so[i] = k
    c.sent_of = so
    nn = [0] * len(toks)
    for i in range(len(toks)):
        for d in (1, 2):
            j = i - d
            if j < 0:
                break
            if _CLAUSE_END.search(toks[j]) and not (forms[j][0] in NEGATORS):
                break
            if forms[j][0] in NEGATORS and not _CLAUSE_END.search(toks[j]):
                nn[i] = d
                break
            if _CLAUSE_END.search(toks[j]):
                break
    c.negnear = nn
    return c


def sent_span(ctx, k):
    a = ctx.sents[k]
    b = ctx.sents[k + 1] if k + 1 < len(ctx.sents) else ctx.n_tok
    return a, b


def _punct_class(tr):
    if not tr:
        return "none"
    if "!" in tr:
        return "!"
    if "?" in tr or "؟" in tr:
        return "?"
    if "..." in tr or "…" in tr:
        return "..."
    if "," in tr or "،" in tr:
        return ","
    if "." in tr:
        return "."
    return "other"


def _len_bucket(n):
    if n <= 1:
        return "1"
    if n <= 2:
        return "2"
    if n <= 3:
        return "3"
    if n <= 5:
        return "4-5"
    if n <= 8:
        return "6-8"
    return "9+"


# ---------------------------------------------------------------------------------------------------------------
# sentence features (talk_style, expression)

def sent_word_feats(w, al):
    """Features of one word that depend on the word only (cacheable): word, char n-grams 1-5, clitic-stripped form."""
    f = ["w=" + w]
    wp = " " + w + " "
    L = len(wp)
    for i in range(L - 2):
        f.append("cw3=" + wp[i:i + 3])
    if al != w:
        f.append("ws=" + al)
    return [hfeat(x) for x in f]


_P1 = frozenset(normalize(x) for x in "i me my we our انا اني نحن ابي ابيك".split())
_P2 = frozenset(normalize(x) for x in "you your you're انت لك عليك معك انتي ابيك".split())
_PAST_EN = frozenset("was were had said went came saw gave made took found thought knew felt got".split())
_PAST_AR = frozenset(normalize(x) for x in "كان كانت قال قالت ذهب جاء راح طلع وجد اخذ صار".split())


def sentence_rest(ctx, a, b, lex_style=None, style=None):
    """Hashed sentence features that are not per-word-only."""
    f = ["bias", "lg=" + ctx.lang]
    words = [w for w in ctx.n[a:b] if w]
    for i in range(len(words) - 1):
        f.append("bg=" + words[i] + "|" + words[i + 1])
    if words:
        f.append("f1=" + words[0])
        f.append("fl=" + words[-1])
        if len(words) > 1:
            f.append("f2=" + words[0] + "|" + words[1])
    pc = _punct_class(ctx.trail[b - 1] if b > a else "")
    f.append("end=" + pc)
    nb = sum(1 for i in range(a, b) if "!" in ctx.trail[i])
    f.append("nbang=%d" % min(nb, 3))
    f.append("len=" + _len_bucket(b - a))
    f.append("lenlg=" + _len_bucket(b - a) + "|" + ctx.lang)
    for h in ctx.hits:
        if a <= h["s"] < b:
            f.append("L=" + h["id"] + ("|neg" if h["neg"] else ""))
    ws = [ctx.n[i] for i in range(a, b)]
    f.append("p1=%d" % min(2, sum(1 for w in ws if w in _P1)))
    f.append("p2=%d" % min(2, sum(1 for w in ws if w in _P2)))
    f.append("neg=%d" % min(2, sum(1 for w in ws if w in NEGATORS)))
    f.append("w0=" + (ws[0] if ws else ""))
    past = _PAST_EN if ctx.lang == "en" else _PAST_AR
    f.append("past=%d" % min(2, sum(1 for w in ws if w in past or (ctx.lang == "en" and w.endswith("ed")))))
    for i in range(a, b):
        if ctx.alt[i] != ctx.n[i]:
            f.append("alt=" + ctx.alt[i])
    if lex_style:
        f.append("kw=" + lex_style)
        f.append("kw|end=" + lex_style + "|" + pc)
    if style:
        f.append("st=" + style)
        f.append("st|end=" + style + "|" + pc)
        f.append("st|lg=" + style + "|" + ctx.lang)
        if nb:
            f.append("st|bang=" + style)
    return [hfeat(x) for x in f]


def sentence_features(ctx, a, b, lex_style=None, style=None):
    """All hashed features of the sentence span [a, b) (training path; the runtime scores the same features with a
    per-word cache).  `style` (the predicted talk_style) is added for the expression model."""
    out = sentence_rest(ctx, a, b, lex_style, style)
    for i in range(a, b):
        if ctx.n[i]:
            out.extend(sent_word_feats(ctx.n[i], ctx.alt[i]))
    return out


# ---------------------------------------------------------------------------------------------------------------
# word features

def _focus(ctx, i, a, b):
    if "!" in ctx.trail[i]:
        return 1.2
    if i == b - 1:
        return 1.2
    if i == a:
        return 0.9
    return 1.0


def hit_priority(h):
    p = PRIORITY.get(h["id"], 1.0)
    if h["cand"]:
        p = min(p, 0.7)
    return p


def static_word_features(ctx, styles):
    """Per token: (word, stripped word, hashed static features not depending on previously predicted tags and
    not word-only; the word-only part comes from tok_word_feats).
    `styles[k]` is the talk_style of sentence k."""
    out = []
    n = ctx.n_tok
    # live hits per phrase and the best one by the guide's scoring
    live_by_phrase = {}
    best = {}
    for h in ctx.hits:
        if h["kind"] != "semantic":
            continue
        k = ctx.phr_of[h["s"]]
        st = styles[ctx.sent_of[h["s"]]]
        if (h["neg"] and not h["neg_ok"]) or h["id"] not in STYLE_SETS[st]:
            continue
        live_by_phrase.setdefault(k, []).append(h)
    for k, hs in live_by_phrase.items():
        a, b = ctx.phr[k]
        top = None
        for h in hs:
            i = h["e"] - 1 if h["id"] in ICONIC else h["s"]
            sc = hit_priority(h) * _focus(ctx, i, a, b)
            if top is None or sc > top[0]:
                top = (sc, h)
        best[k] = top[1]
    for i in range(n):
        s_k = ctx.sent_of[i]
        st = styles[s_k]
        pk = ctx.phr_of[i]
        pa, pb = ctx.phr[pk]
        plen = pb - pa
        w = ctx.n[i]
        al = ctx.alt[i]
        pc = _punct_class(ctx.trail[i])
        pfe = min(pb - 1 - i, 3)
        pf = "first" if i == pa else ("last" if i == pb - 1 else "mid")
        sa, sb = sent_span(ctx, s_k)
        f = ["b", "lg=" + ctx.lang, "pu=" + pc, "pp=" + pf, "pfe=%d" % pfe, "plen=" + _len_bucket(plen),
             "pp|plen=%s|%s" % (pf, _len_bucket(plen)), "st=" + st, "st|pfe=%s|%d" % (st, pfe),
             "st|pu=%s|%s" % (st, pc), "pfe|pu=%d|%s" % (pfe, pc),
             "sp=" + ("first" if i == sa else ("last" if i == sb - 1 else "mid")),
             "st|w=%s|%s" % (st, w), "lg|pfe|plen=%s|%d|%s" % (ctx.lang, pfe, _len_bucket(plen))]
        # neighbours
        for d in (-2, -1, 1, 2):
            j = i + d
            nb = ctx.n[j] if 0 <= j < n else ("<s>" if j < 0 else "</s>")
            f.append("w%+d=%s" % (d, nb))
        f.append("bi-1=" + (ctx.n[i - 1] if i else "<s>") + "|" + w)
        f.append("bi+1=" + w + "|" + (ctx.n[i + 1] if i + 1 < n else "</s>"))
        if ctx.negnear[i]:
            f.append("ng=%d" % ctx.negnear[i])
            f.append("ng|w=" + w)
        # phrase contains live hits
        live = live_by_phrase.get(pk, [])
        live_ids = sorted(set(h["id"] for h in live))
        f.append("nlive=%d" % min(len(live_ids), 3))
        for gid in live_ids[:4]:
            f.append("phL=" + gid)
        # neighbours' lexicon ids
        for d in (-2, -1, 1, 2):
            j = i + d
            if 0 <= j < n and ctx.tok_hits[j]:
                h = ctx.tok_hits[j][0]
                f.append("L%+d=%s%s" % (d, h["id"], "|neg" if (h["neg"] and not h["neg_ok"]) else ""))
        # this token's hits
        for h in ctx.tok_hits[i][:2]:
            gid = h["id"]
            negd = h["neg"] and not h["neg_ok"]
            span = h["e"] - h["s"]
            hp = "single" if span == 1 else ("first" if i == h["s"] else ("last" if i == h["e"] - 1 else "mid"))
            fit = gid in STYLE_SETS[st] or h["kind"] != "semantic"
            f.append("L=" + gid)
            f.append("L|hp=%s|%s" % (gid, hp))
            f.append("L|neg=%s|%d" % (gid, 1 if negd else 0))
            f.append("L|negok=%s|%d" % (gid, 1 if h["neg_ok"] else 0))
            f.append("L|cand=%s|%d" % (gid, 1 if h["cand"] else 0))
            f.append("L|fit=%s|%d" % (gid, 1 if fit else 0))
            f.append("L|st=%s|%s" % (gid, st))
            f.append("L|lg=%s|%s" % (gid, ctx.lang))
            f.append("L|pp=%s|%s" % (gid, pf))
            f.append("L|pfe=%s|%d" % (gid, pfe))
            f.append("L|pu=%s|%s" % (gid, pc))
            f.append("L|w=%s|%s" % (gid, w))
            f.append("L|nlive=%s|%d" % (gid, min(len(live_ids), 3)))
            f.append("L|best=%s|%d" % (gid, 1 if best.get(pk) is h else 0))
            f.append("L|plen=%s|%s" % (gid, _len_bucket(plen)))
            if negd:
                f.append("L|negw=%s|%s" % (gid, w))
            for o in live_ids[:3]:
                if o != gid:
                    f.append("L|other=%s|%s" % (gid, o))
            if best.get(pk) is h:
                f.append("best")
                f.append("best|st=" + st)
        if not ctx.tok_hits[i]:
            f.append("noL")
            f.append("noL|pfe|plen=%d|%s" % (pfe, _len_bucket(plen)))
            f.append("noL|nlive|pfe=%d|%d" % (min(len(live_ids), 3), pfe))
            f.append("noL|st|pfe=%s|%d|%d" % (st, pfe, min(len(live_ids), 3)))
        out.append((w, al, [hfeat(x) for x in f]))
    return out


def tok_word_feats(w, al):
    """Word-only token features (cacheable): word, clitic-stripped form, length, char 2-4 grams, affixes."""
    f = ["w=" + w, "wl=%d" % min(len(al), 8)]
    if al != w:
        f.append("ws=" + al)
    wb = "<" + al + ">"
    for ng in (2, 3, 4):
        for j in range(len(wb) - ng + 1):
            f.append("c%d=%s" % (ng, wb[j:j + ng]))
    for j in (1, 2, 3):
        if len(al) >= j:
            f.append("p%d=%s" % (j, al[:j]))
            f.append("s%d=%s" % (j, al[-j:]))
    return [hfeat(x) for x in f]


def dynamic_features(ctx, i, t1, t2, phr_sem, phr_beats, last_arm_dist, hit_id):
    """Hashed features that depend on the previous predictions."""
    f = ["t-1=" + t1, "t-2=" + t2, "t-1,2=%s|%s" % (t1, t2), "ps=%d" % phr_sem, "pb=%d" % phr_beats,
         "ld=%d" % last_arm_dist, "t-1|w=%s|%s" % (t1, ctx_word(ctx, i))]
    if hit_id:
        f.append("t-1|L=%s|%s" % (t1, hit_id))
        f.append("t-2|L=%s|%s" % (t2, hit_id))
        f.append("ps|L=%d|%s" % (phr_sem, hit_id))
        f.append("ld|L=%d|%s" % (last_arm_dist, hit_id))
    else:
        f.append("ps|noL=%d" % phr_sem)
        f.append("ld|noL=%d" % last_arm_dist)
    return [hfeat(x) for x in f]


def ctx_word(ctx, i):
    return ctx.n[i]


def intensity_features(ctx, i, tag, style):
    w = ctx.n[i]
    pc = _punct_class(ctx.trail[i])
    a, b = ctx.phr[ctx.phr_of[i]]
    f = ["b", "tag=" + tag, "tag|st=%s|%s" % (tag, style), "st=" + style, "pu=" + pc, "tag|pu=%s|%s" % (tag, pc),
         "w=" + w, "tag|w=%s|%s" % (tag, w), "tag|lg=%s|%s" % (tag, ctx.lang),
         "pfe=%d" % min(b - 1 - i, 3), "tag|pfe=%s|%d" % (tag, min(b - 1 - i, 3)),
         "st|pu=%s|%s" % (style, pc), "tag|st|pu=%s|%s|%s" % (tag, style, pc)]
    sa, sb = sent_span(ctx, ctx.sent_of[i])
    if any("!" in ctx.trail[j] for j in range(sa, sb)):
        f.append("sbang")
        f.append("tag|sbang=" + tag)
    if i + 1 < ctx.n_tok and "!" in ctx.trail[i + 1]:
        f.append("nextbang")
    return [hfeat(x) for x in f]


# ---------------------------------------------------------------------------------------------------------------
# linear model container

class Linear:
    """Sparse multiclass linear scorer: W[hash] -> tuple of (class index, weight)."""

    def __init__(self, n_classes, table=None):
        self.n = n_classes
        self.W = table or {}

    @staticmethod
    def from_json(d):
        n = d["n"]
        idx, off, cls, w, scale = d["h"], d["o"], d["c"], d["w"], d["s"]
        table = {}
        for k, h in enumerate(idx):
            a, b = off[k], off[k + 1]
            table[h] = tuple((cls[j], w[j] / scale) for j in range(a, b))
        return Linear(n, table)

    def scores(self, feats, init=None):
        s = list(init) if init is not None else [0.0] * self.n
        W = self.W
        for h in feats:
            e = W.get(h)
            if e:
                for c, v in e:
                    s[c] += v
        return s


def softmax_masked(scores, allowed, temp):
    m = max(scores[c] for c in allowed)
    ex = {}
    z = 0.0
    for c in allowed:
        v = math.exp((scores[c] - m) / temp)
        ex[c] = v
        z += v
    return {c: v / z for c, v in ex.items()}


# ---------------------------------------------------------------------------------------------------------------
# the planner

class GestureModel:
    def __init__(self, lexicon_raw, model=None, reason=None):
        self.lexicon = Lexicon(lexicon_raw)
        self.model = model
        self.mode = "model" if model else "lexicon"
        self.reason = reason
        if model:
            self.style_m = Linear.from_json(model["style"])
            self.expr_m = Linear.from_json(model["expression"])
            self.word_m = Linear.from_json(model["word"])
            self.int_m = Linear.from_json(model["intensity"])
            self.temp = model.get("temperature", 1.0)
            self.tau = model.get("tau", 0.5)
            self.style_temp = model.get("style_temperature", 1.0)
            self.joint_thr = model.get("joint_thr", 0.0)
            self.joint_min2 = model.get("joint_min2", 0.15)
            self.joint_margin = model.get("joint_margin", 0.0)
            self._c_tok, self._c_style, self._c_expr = {}, {}, {}

    # ---- loading ---------------------------------------------------------------------------------------------
    @classmethod
    def load(cls, path=None):
        here = os.path.dirname(os.path.abspath(__file__))
        path = path or os.path.join(here, "gesture_model.json")
        try:
            with open(path, encoding="utf-8") as f:
                d = json.load(f)
            return cls(d["lexicon"], d)
        except Exception as e:                                           # missing or broken: lexicon fallback
            raw = _embedded_lexicon(here)
            if raw is None:
                raise
            return cls(raw, None, reason="model unavailable: %s" % type(e).__name__)

    @classmethod
    def from_dict(cls, d):
        return cls(d["lexicon"], d)

    # ---- per-word score caches (identical scores to the uncached path) -----------------------------------------
    def _tok_base(self, w, al):
        k = (w, al)
        v = self._c_tok.get(k)
        if v is None:
            v = self.word_m.scores(tok_word_feats(w, al))
            if len(self._c_tok) < 20000:
                self._c_tok[k] = v
        return v

    def _sent_base(self, ctx, a, b):
        ss = [0.0] * len(STYLES)
        se = [0.0] * len(EXPRESSIONS)
        for i in range(a, b):
            w = ctx.n[i]
            if not w:
                continue
            k = (w, ctx.alt[i])
            v = self._c_style.get(k)
            if v is None:
                hs = sent_word_feats(w, ctx.alt[i])
                v = (self.style_m.scores(hs), self.expr_m.scores(hs))
                if len(self._c_style) < 20000:
                    self._c_style[k] = v
            for c, x in enumerate(v[0]):
                ss[c] += x
            for c, x in enumerate(v[1]):
                se[c] += x
        return ss, se

    # ---- sentence level --------------------------------------------------------------------------------------
    def sentence_styles(self, ctx, hint=None):
        """[(talk_style, expression, style_conf)] per sentence."""
        out = []
        for k in range(len(ctx.sents)):
            a, b = sent_span(ctx, k)
            kw = keyword_talk_style(" ".join(ctx.toks[a:b]))
            if self.mode == "model":
                bs, be = self._sent_base(ctx, a, b)
                sc = self.style_m.scores(sentence_rest(ctx, a, b, lex_style=kw), bs)
                p = softmax_masked(sc, range(len(STYLES)), self.style_temp)
                ci = max(p, key=p.get)
                style, conf = STYLES[ci], p[ci]
                if hint in STYLES and conf < 0.5:
                    style = hint
                expr = self._expr_for(ctx, a, b, kw, style, be)
            else:
                style, conf, p = (hint if hint in STYLES and kw == "explain" else kw), 1.0, None
                expr = STYLE_DEFAULT_EXPRESSION[style]
            out.append((style, expr, conf, p))
        return out

    def _expr_for(self, ctx, a, b, kw, style, be=None):
        if be is None:
            be = self._sent_base(ctx, a, b)[1]
        se = self.expr_m.scores(sentence_rest(ctx, a, b, lex_style=kw, style=style), be)
        return EXPRESSIONS[max(range(len(EXPRESSIONS)), key=lambda c: se[c])]

    def joint(self, ctx, info):
        """Decode the words; for sentences whose style is uncertain, also decode under the runner-up style and keep
        the style whose (style probability + gesture decisions) is more likely.  Returns (info, tags, raw)."""
        styles = [x[0] for x in info]
        tags, raw = self.decode_raw(ctx, styles)
        thr = self.joint_thr
        if not thr:
            return info, tags, raw
        alt = {}
        for k, x in enumerate(info):
            p = x[3]
            if p is None or x[2] >= thr:
                continue
            order = sorted(p, key=p.get, reverse=True)
            if len(order) > 1 and p[order[1]] >= self.joint_min2:
                alt[k] = order[1]
        if not alt:
            return info, tags, raw
        styles2 = list(styles)
        for k, ci in alt.items():
            styles2[k] = STYLES[ci]
        tags2, raw2 = self.decode_raw(ctx, styles2)
        info = list(info)
        for k, ci in alt.items():
            a, b = sent_span(ctx, k)

            def ll(tg, rw):
                tot = 0.0
                for i in range(a, b):
                    al, sc = rw[i]
                    tot += math.log(max(softmax_masked(sc, al, self.temp)[tg[i]], 1e-9))
                return tot
            p = info[k][3]
            s1 = math.log(max(p[STYLES.index(styles[k])], 1e-9)) + ll(tags, raw)
            s2 = math.log(max(p[ci], 1e-9)) + ll(tags2, raw2)
            if s2 > s1 + self.joint_margin:
                kw = keyword_talk_style(" ".join(ctx.toks[a:b]))
                info[k] = (STYLES[ci], self._expr_for(ctx, a, b, kw, STYLES[ci]), p[ci], p)
                for i in range(a, b):
                    tags[i] = tags2[i]
                    raw[i] = raw2[i]
        return info, tags, raw

    # ---- word level (model) ----------------------------------------------------------------------------------
    def _allowed(self, ctx, i, style, prev_tag):
        al = set(range(len(TAGS)))
        ss = STYLE_SETS[style]
        for t in SEMANTIC:
            if t not in ss:
                al.discard(TAG_ID[t])
        if style == "gentle":
            al.discard(TAG_ID["beat"])
        if prev_tag in ARM_TAGS:
            al.discard(TAG_ID["beat"])
        return al

    def decode(self, ctx, styles, temp=None):
        """Greedy left-to-right decode.  Returns (tag indices, [{class: prob}])."""
        tags, raw = self.decode_raw(ctx, styles)
        t = self.temp if temp is None else temp
        return tags, [softmax_masked(sc, al, t) for al, sc in raw]

    def decode_raw(self, ctx, styles):
        """Greedy decode returning (tag indices, [(allowed set, scores)]) so callers can re-temper the scores."""
        stat = static_word_features(ctx, styles)
        tags = []
        probs = []
        t1 = t2 = "<s>"
        last_arm = -99
        cur_phrase = -1
        phr_sem = phr_beats = 0
        for i in range(ctx.n_tok):
            if ctx.phr_of[i] != cur_phrase:
                cur_phrase = ctx.phr_of[i]
                phr_sem = phr_beats = 0
            hit_id = ctx.tok_hits[i][0]["id"] if ctx.tok_hits[i] else None
            dist = i - last_arm if last_arm >= 0 else 9
            dist = dist if dist < 4 else (4 if dist < 9 else 9)
            w_i, al_i, st_feats = stat[i]
            base = self._tok_base(w_i, al_i)
            feats = st_feats + dynamic_features(ctx, i, t1, t2, min(phr_sem, 2), min(phr_beats, 2), dist, hit_id)
            sc = self.word_m.scores(feats, base)
            al = self._allowed(ctx, i, styles[ctx.sent_of[i]], t1)
            ci = max(al, key=lambda c: sc[c])
            tag = TAGS[ci]
            tags.append(ci)
            probs.append((al, sc))
            t2, t1 = t1, tag
            if tag in SEM_SET or tag in ONESHOT:
                phr_sem += 1
                last_arm = i
            elif tag == "beat":
                phr_beats += 1
                last_arm = i
        return tags, probs

    # ---- policy (SPEC 2.5, 2.6) -----------------------------------------------------------------------------
    def _policy(self, ctx, styles, cands, beat_cands, heads, used_ids):
        """cands: [(i, tag, conf)] semantic candidates; beat_cands: [(i, conf)]; returns the final plan pieces."""
        by_phrase = {}
        for i, t, c in cands:
            by_phrase.setdefault(ctx.phr_of[i], []).append((i, t, c))
        kept = []
        for k in sorted(by_phrase):
            a, b = ctx.phr[k]
            items = by_phrase[k]
            if len(items) > 1:
                items.sort(key=lambda x: x[0])
                pair = None
                for x in range(len(items) - 1):
                    if (items[x][1], items[x + 1][1]) in COMBOS and items[x + 1][0] - items[x][0] <= 3:
                        pair = (items[x], items[x + 1])
                        break
                lists = [it for it in items if it[1] == "list"]
                if pair:
                    kept.extend([(pair[0][0], pair[0][1], pair[0][2], COMBOS[(pair[0][1], pair[1][1])]),
                                 (pair[1][0], pair[1][1], pair[1][2], COMBOS[(pair[0][1], pair[1][1])])])
                    continue
                if len(lists) == len(items):
                    kept.append((lists[0][0], "list", lists[0][2], "list"))
                    continue

                def score(it):
                    pr = PRIORITY.get(it[1], 1.0)
                    return it[2] * pr * _focus(ctx, it[0], a, b)
                top = max(items, key=score)
                kept.append((top[0], top[1], top[2], "list" if top[1] == "list" else None))
            else:
                it = items[0]
                kept.append((it[0], it[1], it[2], "list" if it[1] == "list" else None))
        kept.sort()
        # the same id never in two phrases in a row (a list series counts as one), nor as the previous clause's last id
        final = []
        last_ph = {}
        for i, t, c, combo in kept:
            k = ctx.phr_of[i]
            prev = [x for x in final if ctx.phr_of[x[0]] == k - 1 and x[1] == t]
            if prev and t != "list" and not combo:
                continue
            if not final and t != "list" and used_ids and used_ids[-1] == t:
                continue
            final.append((i, t, c, combo))
        # beats
        arm = set(i for i, t, c, combo in final) | set(i for i, t in heads if t in HEAD)
        fills = {}
        for i, t, c, combo in final:
            if combo or t in SHORT_FILL:
                fills[ctx.phr_of[i]] = True
        beats = []
        for k, (a, b) in enumerate(ctx.phr):
            if b - a <= 2 or fills.get(k):
                continue
            if styles[ctx.sent_of[a]] == "gentle":
                continue
            cs = sorted([(c, i) for i, c in beat_cands if a <= i < b], reverse=True)[:2]
            chosen = []
            for c, i in cs:
                if i - 1 in arm or i + 1 in arm or i in arm:
                    continue
                chosen.append(i)
            beats.extend(sorted(chosen))
        return final, beats

    # ---- the public planner ---------------------------------------------------------------------------------
    def plan(self, text, *, lang=None, talk_style_hint=None, used_ids=(), mode=None):
        """Plan one clause.  Never raises: on any internal error returns an empty plan with a reason."""
        try:
            return self._plan(text, lang, talk_style_hint, tuple(used_ids or ()), mode)
        except Exception as e:                                           # pragma: no cover - defensive
            return {"tokens": (text or "").split(), "sentences": [], "anchors": [], "beats": [], "head": [],
                    "mode": "error", "reason": "%s: %s" % (type(e).__name__, e)}

    def _plan(self, text, lang, hint, used_ids, mode):
        text = text or ""
        mode = mode or self.mode
        if mode == "model" and self.mode != "model":
            mode = "lexicon"
        ctx = analyse(self.lexicon, text, lang)
        if not ctx.toks:
            return {"tokens": [], "sentences": [], "anchors": [], "beats": [], "head": [], "mode": mode,
                    "reason": "empty"}
        info = self.sentence_styles(ctx, hint) if mode == "model" else self._lexicon_styles(ctx, hint)
        if mode == "model":
            info, tags, raw = self.joint(ctx, info)
            styles = [s[0] for s in info]
            probs = [softmax_masked(sc, al, self.temp) for al, sc in raw]
            cands, beat_cands, heads, ones = self.candidates_from_probs(
                ctx, styles, tags, probs, self.tau, self.model.get("tau_beat", 0.0),
                self.model.get("tau_other", self.tau), self.model.get("tau_unc", 0.0))
            # greetings, farewells and head gestures are rare (10 and 13 gold in 700 lines) and every one of them sits
            # in its own paraphrase family, so the learned model cannot see them in held-out data: the lexicon (which
            # is exact for them) fills in whatever the model left empty
            _lc, _lb, lheads, lones = self._lexicon_candidates(ctx, styles)
            if not ones:
                ones = list(lones)
            for hi, ht in lheads:
                if not any(abs(hi - x) <= 1 for x, _t in heads):
                    heads.append((hi, ht))
            heads.sort()
        else:
            styles = [s[0] for s in info]
            cands, beat_cands, heads, ones = self._lexicon_candidates(ctx, styles)
        cands = [x for x in cands
                 if not (x[1] == "round" and normalize(_EDGE.sub("", ctx.toks[x[0]])).endswith(NOT_ROUND_SUFFIXES))]
        final, beats = self._policy(ctx, styles, cands, beat_cands, heads, used_ids)
        anchors = []
        for i, t, c, combo in final:
            st = styles[ctx.sent_of[i]]
            k = self._intensity(ctx, i, t, st) if mode == "model" else (1 if st == "gentle" else 2)
            if st != "gentle" and k is not None and k < INTENSITY_FLOOR_OUTSIDE_GENTLE:
                k = INTENSITY_FLOOR_OUTSIDE_GENTLE
            anchors.append({"i": i, "w": ctx.toks[i], "id": t, "k": k, "conf": round(c, 3), "combo": combo,
                            "hand": HANDS.get(t, "")})
        for i, t, c in ones:
            if not any(a["i"] == i for a in anchors):
                anchors.append({"i": i, "w": ctx.toks[i], "id": t, "k": None, "conf": round(c, 3), "combo": None,
                                "hand": HANDS.get(t, "")})
        anchors.sort(key=lambda a: a["i"])
        bl = []
        for i in beats:
            st = styles[ctx.sent_of[i]]
            k = self._intensity(ctx, i, "beat", st) if mode == "model" else (2 if "!" in ctx.trail[i] else 1)
            bl.append({"i": i, "w": ctx.toks[i], "k": k})
        head = [{"i": i, "id": t} for i, t in heads]
        # H_Tilt by rule: at every question end and with ask
        tilts = set()
        for k in range(len(ctx.sents)):
            a, b = sent_span(ctx, k)
            if "?" in ctx.trail[b - 1] or "؟" in ctx.trail[b - 1]:
                tilts.add(b - 1)
        for a in anchors:
            if a["id"] == "ask":
                tilts.add(a["i"])
        head.extend({"i": i, "id": "H_Tilt"} for i in sorted(tilts))
        head.sort(key=lambda x: x["i"])
        sents = [{"start": ctx.sents[k], "talk_style": info[k][0], "expression": info[k][1],
                  "conf": round(info[k][2], 3)} for k in range(len(ctx.sents))]
        return {"tokens": ctx.toks, "sentences": sents, "anchors": anchors, "beats": bl, "head": head,
                "mode": mode, "reason": self.reason}

    # candidates -------------------------------------------------------------------------------------------------
    def _model_candidates(self, ctx, styles):
        tags, probs = self.decode(ctx, styles)
        return self.candidates_from_probs(ctx, styles, tags, probs, self.tau, self.model.get("tau_beat", 0.0),
                                          self.model.get("tau_other", self.tau), self.model.get("tau_unc", 0.0))

    def candidates_from_probs(self, ctx, styles, tags, probs, tau, tau_beat, tau_other, tau_unc=0.0):
        """Turn per-token decisions into candidates; below-tau semantic decisions fall back to a live lexicon hit
        (k = 1) only when the model is also uncertain overall (best class prob < tau_unc; 0 disables the fallback).
        An unsure token with no usable lexicon hit keeps the model's own decision (review fix 2026-10-05: before, it
        was dropped, so a non-zero tau_unc silently removed beats)."""
        cands, beat_cands, heads, ones = [], [], [], []
        for i, ci in enumerate(tags):
            t = TAGS[ci]
            p = probs[i][ci]
            if tau_unc and p < tau_unc:
                lex_hit = False
                for h in ctx.tok_hits[i]:
                    if (h["kind"] == "semantic" and not (h["neg"] and not h["neg_ok"]) and not h["cand"]
                            and h["id"] in STYLE_SETS[styles[ctx.sent_of[i]]]):
                        cands.append((i, h["id"], p))
                        lex_hit = True
                        break
                if lex_hit:
                    continue
            if t == "O":
                continue
            if t == "beat":
                if p >= tau_beat:
                    beat_cands.append((i, p))
                continue
            if p < (tau_other if (t in HEAD or t in ONESHOT) else tau):
                continue
            if t in SEM_SET:
                # negation guard (SPEC 2.5): a cue the lexicon found negated ("not big") never takes its own gesture
                if any(h["id"] == t and h["neg"] and not h["neg_ok"] for h in ctx.tok_hits[i]):
                    continue
                cands.append((i, t, p))
            elif t in HEAD:
                heads.append((i, t))
            else:
                ones.append((i, t, p))
        return cands, beat_cands, heads, ones

    def _lexicon_styles(self, ctx, hint):
        out = []
        for k in range(len(ctx.sents)):
            a, b = sent_span(ctx, k)
            kw = keyword_talk_style(" ".join(ctx.toks[a:b]))
            s = hint if (hint in STYLES and kw == "explain") else kw
            out.append((s, STYLE_DEFAULT_EXPRESSION[s], 1.0))
        return out

    def _lexicon_candidates(self, ctx, styles, use_candidate_only=False):
        """The lexicon-only planner (SPEC 2.5, 4.7): live hits, one per phrase by the guide's score, k via rules."""
        cands, heads, ones = [], [], []
        for h in ctx.hits:
            gid = h["id"]
            i = h["e"] - 1 if gid in ICONIC else h["s"]
            if h["kind"] == "semantic":
                if h["neg"] and not h["neg_ok"]:
                    continue
                if h["cand"] and not use_candidate_only:
                    continue
                if gid not in STYLE_SETS[styles[ctx.sent_of[i]]]:
                    continue
                cands.append((i, gid, hit_priority(h) / 1.3 + 0.0))
            elif h["kind"] == "head":
                if gid == "H_Shake" and not h["neg"]:
                    # a standalone no only: the cue is the whole clause
                    a, b = ctx.phr[ctx.phr_of[h["s"]]]
                    if b - a <= 2:
                        heads.append((h["s"], gid))
                elif gid == "H_Nod" and not h["neg"]:
                    a, b = ctx.phr[ctx.phr_of[h["s"]]]
                    if b - a <= 2:
                        heads.append((h["s"], gid))
            elif h["kind"] == "oneshot" and not h["neg"]:
                ones.append((h["s"], gid, 1.0))
        # the fallback beats: last content word of each phrase and a word followed by "!"
        beat_cands = []
        for k, (a, b) in enumerate(ctx.phr):
            if b - a <= 2:
                continue
            beat_cands.append((b - 1, 1.0))
        return cands, beat_cands, heads, ones

    def _intensity(self, ctx, i, tag, style):
        sc = self.int_m.scores(intensity_features(ctx, i, tag, style))
        k = 1 + max(range(3), key=lambda c: sc[c])
        if style == "gentle":
            k = 1
        return k

    # ---- the SPEC 8.2 shape ------------------------------------------------------------------------------------
    def plan_clause(self, text, *, lang=None, talk_style_hint=None, used_ids=(), seed=0):
        p = self.plan(text, lang=lang, talk_style_hint=talk_style_hint, used_ids=used_ids)
        anchors = [(a["i"], normalize(_EDGE.sub("", a["w"])), a["id"], a["k"], a["hand"]) for a in p["anchors"]]
        sents = [(s["start"], s["talk_style"], s["expression"]) for s in p["sentences"]]
        return {"anchors": anchors, "sentences": sents, "beats": [(b["i"], b["k"]) for b in p["beats"]],
                "head": [(h["i"], h["id"]) for h in p["head"]], "reason": p.get("reason")}


def _embedded_lexicon(here):
    """Fallback lexicon when the model json is missing: lexicon.json one folder up (the training copy)."""
    for p in (os.path.join(here, "lexicon_fallback.json"), os.path.join(here, "..", "lexicon.json")):
        try:
            with open(p, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            continue
    return None
