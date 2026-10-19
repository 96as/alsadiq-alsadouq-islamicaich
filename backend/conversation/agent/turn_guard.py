"""Turn guard: the only thing that runs before the model on a child's turn.

``check(text)`` returns a ``GuardHit`` for three kinds of turn, and ``None`` for everything else
(the model then answers alone and nothing is injected):

  1. SAFETY: a serious disclosure (harm at home, grooming, self-harm, ...). The model is told to
     comfort and the caller records the flag, so it is raised even if the model misses it.
  2. REFER, level D: a personal case or a religious ruling (a fatwa).
  3. REFER, level C: creed and topics scholars or people discuss differently.

Pure, no DB, no network, well under 10 ms. The patterns live in
``session_moral_context/content/turn_rules.json`` (lead editable, contains no scripture). The notes
below contain none either.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from .text_match import Rule, TermIndex, make_term, token_forms

RULES_PATH = Path(__file__).resolve().parents[2] / "session_moral_context" / "content" / "turn_rules.json"

SAFETY = "SAFETY"
REFER = "REFER"


@dataclass(frozen=True)
class GuardHit:
    kind: str                   # SAFETY or REFER
    rule_id: str
    level: str                  # "D" for safety and personal rulings, "C" for creed/disputes
    flag_type: str = ""         # SAFETY only: the rule's flag_type ('harmful'|'inappropriate'|'sensitive')
    notify_parent: bool = True  # SAFETY only: the rule's notify_parent value (picks the rule; never routes, hk/12g)
    note: str = ""              # text injected into the model context for this turn


@dataclass(frozen=True)
class _Rules:
    safety: tuple[Rule, ...]
    level_d: tuple[Rule, ...]
    level_c: tuple[Rule, ...]
    family: TermIndex = TermIndex()  # the vocab lists 'family' and 'relative', en + ar (see mentions_family)
    home: TermIndex = TermIndex()    # 'at home' words (see mentions_family)
    outsider: TermIndex = TermIndex()  # strangers and online places: home words then do not count
    secrecy: tuple = ()              # compiled "don't tell my mom" spans that are NOT a family mention


def _expand(group, vocab: dict, lang: str) -> list:
    """Replace '@name' entries of a group with the shared vocabulary list for ``lang``."""
    out: list = []
    for p in group:
        if p.startswith("@"):
            out.extend(vocab.get(p[1:], {}).get(lang, []))
        else:
            out.append(p)
    return out


def _compile_rules(raw_list, with_meta: bool = False, vocab: dict | None = None) -> tuple[Rule, ...]:
    vocab = vocab or {}
    out = []
    for r in raw_list:
        for lang in ("en", "ar"):
            groups = r.get(lang)
            if not groups:
                continue
            cg = tuple(
                tuple(t for t in (make_term(p) for p in _expand(g, vocab, lang)) if t)
                for g in groups)
            unless = tuple(
                t for t in (make_term(p) for p in r.get("unless", {}).get(lang, [])) if t)
            out.append(_build_rule(r, cg, unless, with_meta))
        mixed = _mixed_variant(r, vocab, with_meta)
        if mixed is not None:
            out.append(mixed)
    return tuple(out)


def _build_rule(r, cg, unless, with_meta, both_scripts=False) -> Rule:
    return Rule(id=r["id"], groups=cg, unless=unless,
                window=int(r.get("window", 0)),
                notify_parent=bool(r.get("notify_parent", True)),
                values=tuple(r.get("values", ())),
                before_d=bool(r.get("before_d", False)),
                no_items=bool(r.get("no_items", False)),
                mode=r.get("mode", ""),
                both_scripts=both_scripts,
                meta=r.get("flag_type", "") if with_meta else "")


def _mixed_variant(r, vocab, with_meta) -> Rule | None:
    """A rule marked ``"mixed": true`` also gets a code-switching variant: group by group, the English
    and the Arabic terms are pooled, so "a man online قال لي send photo ولا تقول لاحد" is judged as one
    sentence. It is judged only on a turn that really mixes both scripts, and it only ever ADDS matches
    (the plain en and ar rules are untouched)."""
    en, ar = r.get("en"), r.get("ar")
    if not r.get("mixed") or not en or not ar or len(en) != len(ar):
        return None
    cg = []
    for ge, ga in zip(en, ar):
        seen, terms = set(), []
        for t in (make_term(p) for p in _expand(ge, vocab, "en") + _expand(ga, vocab, "ar")):
            if t and t.text not in seen:
                seen.add(t.text)
                terms.append(t)
        cg.append(tuple(terms))
    unless = []
    seen = set()
    for lang in ("en", "ar"):
        for p in r.get("unless", {}).get(lang, []):
            t = make_term(p)
            if t and t.text not in seen:
                seen.add(t.text)
                unless.append(t)
    return _build_rule(r, tuple(cg), tuple(unless), with_meta, both_scripts=True)


# Carers and outsiders in the safety word lists (coach, teacher, driver, neighbour, a parent's
# friend): harm by them still alerts the parent (lead decision), so mentions_family skips them.
_NOT_FAMILY = re.compile(r"babysitter|tutor|driver|coach|teacher|neighbo|friend|المعلم|الاستاذ|"
                         r"المدرس|السواق|السائق|جار|صديق")


# Words that say the child is AT HOME (fail closed: harm at home may be by family). They do not count
# when the child names an outsider or an online place: a child online at home harmed by a coach or a
# stranger must still reach the parent (review of cfcc12ca).
_HOME_WORDS = {"en": ["at home", "my house", "our house", "in the house"],
               "ar": ["البيت", "بيتنا", "في البيت"]}
# "dont tell my mom": the mom is who the secret is kept FROM, not who did it, so it is not a family
# mention. The vocab 'secrecy_from_parents' phrases plus the child's own telling of such a request.
_FAMILY_WORD = (r"(?:mom|mum|mommy|mummy|mother|dad|daddy|father|parents|parent|family|folks|"
                r"ماما|بابا|امي|امك|ابي|ابوك|ابوي|اهلي|اهلك|والدي|والديك|والدتي|والدتك)")
_SECRECY_TELLING = re.compile(
    r"(?:\b(?:do not|dont|never|not to|cant|wont|shouldnt|must not|mustnt)\s+"
    r"(?:tell|let|say anything to|show|inform)\s+(?:my|your|the|his|her)?\s*|"
    r"(?:لا|ما|متقولش|ما تقولش)\s+(?:تقول|تخبر|تعلم|تحكي|تخبري|تقولي)\s*ل?\s*)"
    + _FAMILY_WORD + r"\b")


def _secrecy_spans(vocab: dict) -> tuple:
    phrases = [p for lang in ("en", "ar") for p in vocab.get("secrecy_from_parents", {}).get(lang, [])]
    phrases.sort(key=len, reverse=True)
    spans = [re.compile(re.escape(p.replace("'", "").lower())) for p in phrases if p.strip()]
    return (*spans, _SECRECY_TELLING)


@lru_cache(maxsize=1)
def load_rules(path: str | None = None) -> _Rules:
    p = Path(path or os.getenv("TURN_RULES_PATH") or RULES_PATH)
    raw = json.loads(p.read_text(encoding="utf-8"))
    vocab = {k: v for k, v in raw.get("vocab", {}).items() if not k.startswith("_")}
    family = [t for name in ("family", "relative") for lang in ("en", "ar")
              for t in (make_term(p) for p in vocab.get(name, {}).get(lang, [])
                        if not _NOT_FAMILY.search(p)) if t]
    return _Rules(
        safety=_compile_rules(raw.get("safety", []), with_meta=True, vocab=vocab),
        level_d=_compile_rules(raw.get("level_d", []), vocab=vocab),
        level_c=_compile_rules(raw.get("level_c", []), vocab=vocab),
        family=TermIndex(family),
        home=TermIndex(t for words in _HOME_WORDS.values() for t in map(make_term, words) if t),
        outsider=TermIndex(t for name in ("unknown_person", "online_place", "stranger_platform")
                           for lang in ("en", "ar")
                           for t in map(make_term, vocab.get(name, {}).get(lang, [])) if t),
        secrecy=_secrecy_spans(vocab),
    )


# What a SAFETY reply must say in plain words, by the kind of situation. Every line is a warm
# reassurance, never a ruling and never a promise; the trusted adult named is never the person
# involved. Group members are rule ids from turn_rules.json.
_SAFETY_GROUPS = {
    "home_harm": (
        ("violence_witnessed_at_home", "hitting_at_home", "hitting_at_home_target", "hitting_at_home_object",
         "hitting_by_adult", "parent_cruelty", "neglect",
         "unsafe_touch", "adult_boundary", "closed_door_visits", "secrecy_by_adult",
         "coerced_silence", "uncomfortable_secret", "undress_request", "fear_at_home",
         "fear_of_family_member", "runaway"),
        "Your reply must say, in plain words, that what is happening is not okay, that it is "
        "NOT THEIR FAULT, and that no child should be treated like that, naming it as the child "
        "did (hit, shut in without food, touched, yelled at and scared). If "
        "someone told them to keep it secret, say telling a safe adult is the right thing to do. "
        "Point to a trusted adult or a teacher today; never send them back to the person "
        "involved and do not name the parents as the way out. Give no ruling on discipline. "
    ),
    "family_conflict": (
        "family_fighting divorce".split(),
        "Your reply must say in plain words that the fighting or the divorce is not their fault, that you take "
        "nobody's side, and that you cannot give a ruling or say who is right. Point to a "
        "trusted adult or a teacher today, and do not tell them to sort it out with their "
        "parents. "
    ),
    "self_harm": (
        ("self_harm", "self_harm_pairs", "self_injury_behaviour"),
        "Your reply must say in plain words, with warmth, that they matter and that they are "
        "loved and cared about; "
        "acknowledge how heavy the feeling is, and that it is good they said it. Point to a "
        "trusted adult or a teacher soon, and tell them to go to a safe adult at once if they "
        "might hurt themselves. No sermon, no sin or haram, no promise of secrecy. "
    ),
    "eating": (
        ("self_induced_vomiting", "purging_after_eating", "restricting_food_for_weight",
         "restricting_food_bare_motive"),
        "Your reply must say in plain words, with warmth, that they matter exactly as they are, that "
        "making yourself throw up or not eating to change your body can really hurt you, and that it "
        "was brave and good to say it out loud. Point to a trusted adult, a parent or a teacher soon, and say a doctor "
        "can help with this. Give no diet, weight, calorie or food-rule advice, no praise for being "
        "thin, no sin or haram, no promise of secrecy. "
    ),
    "bullying_slurs": (
        ("bullying_name_calling", "bullying_violent_urge", "bullying_slur"),
        "Your reply must say in plain words that being called names, or being mocked for who they are "
        "(their religion, where they come from, how they look), is not okay and is never their fault, "
        "and that feeling angry is understandable. Do not agree with the insult and do not repeat it. "
        "Never advise hitting back or putting up with it quietly: point to a teacher or a trusted adult "
        "today who can make it stop. "
    ),
    "bullying": (
        ("bullying",),
        "Your reply must say in plain words that being hit or having their things taken is not okay, that they "
        "deserve to be safe, and that it is not their fault. Point to a teacher or a trusted adult "
        "today, and never advise hitting back or putting up with it quietly. "
    ),
    "online_or_stranger": (
        ("grooming_photos", "grooming_meet", "grooming_secrecy", "grooming_secrecy_parents", "stranger_lure",
         "stranger_meeting", "personal_info_request", "locating_threat",
         "explicit_image_request", "explicit_image_request_family",
         "grooming_media_inducement", "grooming_media_secret", "grooming_media_gift",
         "grooming_media_gift_offer", "grooming_photos_secret", "grooming_stranger_word_asks_media",
         "grooming_stranger_word_secret",
         "grooming_media_explicit", "grooming_unknown_asks_media",
         "grooming_gift_secret_media", "grooming_undress_secret", "grooming_meet_alone",
         "grooming_sextortion", "grooming_gifts", "grooming_isolation", "grooming_isolation_online"),
        "Say clearly what not to do (do not send photos or anything private, do not meet, do not "
        "share where you live), that asking for that or asking for secrecy is not okay and is "
        "never the child's fault, that they did the right thing by saying it, and that they should "
        "not keep it secret. If gifts or threats were part of it, say that is also not okay and that "
        "they are not in trouble. If someone said to trust them more than the child's family, say "
        "that a safe friend never asks that. Point to a trusted adult now. "
    ),
    "drugs": (
        ("drugs_or_adult_content", "substance_offer"),
        "Say you will not explain it, that it can hurt the body and the mind, that you care about "
        "them, and that a trusted adult, a parent or a teacher is the right person to talk to. "
        "No graphic detail and no religious ruling. "
    ),
}
_SAFETY_GROUP_TEXT = {rid: text for members, text in _SAFETY_GROUPS.values() for rid in members}

_SAFETY_NOTE = (
    "The child may be describing a hard or unsafe situation with someone at home or "
    "nearby. This is already recorded; do not call flag_safety_concern for it. Be gentle and "
    "calm: acknowledge their feelings first, tell them it was good and brave to say it, "
    "and encourage them to talk to a trusted adult or a teacher today. Never say that "
    "anyone has been told or will be told, never promise to keep it secret, never blame "
    "the child or their family, and never take sides. Do not ask for details, and give "
    "no religious rulings or scripture. If they may be in danger right now, tell them to "
    "go to a safe adult straight away. "
)

_REFER_D_NOTE = (
    "This is about the child's own situation or a religious ruling. Your reply MUST say plainly, in "
    "the language you reply in, that a parent or a scholar knows best for this question. Be kind "
    "first and say it is good that they asked. Do not give a ruling or say whether something is "
    "valid, allowed, forbidden or a sin for them or anyone, never judge a person or their family, and "
    "add no Islamic fact, reason, verse, hadith or story of your own. Do not call search_bank this "
    "turn. Two short sentences. Everyday manners (be honest, be kind) are still fine."
)

_REFER_C_NOTE = (
    "This is a big question that scholars or people discuss differently. Your reply MUST say "
    "plainly, in the language you reply in, that a parent or a trusted scholar can explain it best. "
    "Say warmly it is a good question and something kind about the people in it. Never list, "
    "describe or guess views, never pick a side, never judge any person or group, and add no Islamic "
    "fact, reason or story of your own. Do not call search_bank this turn. Two short sentences."
)


def _first(rules: tuple[Rule, ...], tf) -> Rule | None:
    return next((r for r in rules if r.matches(tf)), None)


def check(text: str) -> GuardHit | None:
    """The guard's decision for one child turn, or None when the model should answer alone."""
    tf = token_forms(text)
    if not tf:
        return None
    rules = load_rules()

    # Several safety rules can fire on one message. When any of them is a notify_parent=false
    # rule, that one wins, so its (home-harm) reply text is used. Since hk/12g the field only
    # picks the rule: every safety hit alerts the parent (turn_pipeline._flag_safety).
    hits = [x for x in rules.safety if x.matches(tf)]
    r = next((x for x in hits if not x.notify_parent), hits[0] if hits else None)
    if r:
        return GuardHit(SAFETY, r.id, "D", flag_type=r.meta or "sensitive", notify_parent=r.notify_parent,
                        note=_SAFETY_NOTE + _SAFETY_GROUP_TEXT.get(r.id, ""))

    r = _first(tuple(x for x in rules.level_c if x.before_d), tf)
    if r:
        return GuardHit(REFER, r.id, "C", note=_REFER_C_NOTE)
    r = _first(rules.level_d, tf)
    if r:
        return GuardHit(REFER, r.id, "D", note=_REFER_D_NOTE)
    r = _first(rules.level_c, tf)
    if r:
        return GuardHit(REFER, r.id, "C", note=_REFER_C_NOTE)
    return None


def mentions_family(text: str) -> bool:
    """True when the child's words name a family member or say it happens at home (the rules' 'family'
    and 'relative' word lists plus home words, English and Arabic). A mention that is only the person a
    secret is kept FROM ("my coach wants pics, dont tell my mom") does not count. Since hk/12g nothing
    routes on it (every safety concern alerts the parent); it is kept for its tests and any later use."""
    rules = load_rules()
    plain = (text or "").lower().replace("'", "").replace("\u2019", "")
    for span in rules.secrecy:
        plain = span.sub(" ", plain)
    tf = token_forms(plain)
    if not tf:
        return False
    if rules.family.any_in(tf):
        return True
    outsider = rules.outsider.any_in(tf) or bool(_NOT_FAMILY.search(plain))
    return rules.home.any_in(tf) and not outsider


__all__ = ["GuardHit", "check", "load_rules", "mentions_family", "SAFETY", "REFER"]
