"""Small deterministic text matching helpers shared by retrieval and turn policy.

Pure Python, no network, no DB: a turn is classified in well under 10 ms.
Arabic is normalised with ``normalize_ar`` (tashkeel/tatweel stripped, alef/ya/
ta-marbuta unified) and common clitic prefixes (ال، وال، بال، و، ب ...) are
tolerated, so one keyword matches "الكذب", "بالكذب" and "كذب".
"""
from __future__ import annotations

import itertools
import re
from dataclasses import dataclass, field

from session_moral_context.utils.arabic import normalize_ar

_AR_PREFIXES = ("وال", "فال", "بال", "كال", "لل", "ال", "و", "ف", "ب", "ل", "ك")
_WORD_RE = re.compile(r"[^\W_]+", re.UNICODE)
_APOS_S_RE = re.compile(r"['’]s\b")
_ARABIC_RE = re.compile(r"[\u0600-\u06ff]")
_LATIN_RE = re.compile(r"[a-z]")
# a fused mixed-script token such as "الphoto" or "photoال" is split where the script changes
_SCRIPT_SPLIT_RE = re.compile(r"(?<=[\u0600-\u06ff])(?=[a-z])|(?<=[a-z])(?=[\u0600-\u06ff])")
# The name of Allah with its clitics. Stripping "ال" from it would leave the pronoun له
# ("for him"), so "I bought him a present?" read as a question about Allah.
# Words whose first letter looks like a clitic but is a root letter: stripping it made the
# Kaaba and a game (لعبة) one word, so "the best game in the world?" became a religious question.
_ROOT_FIRST = {
    "كعبه": frozenset({"كعبه"}), "الكعبه": frozenset({"الكعبه", "كعبه"}),
    "بالكعبه": frozenset({"بالكعبه", "كعبه"}), "للكعبه": frozenset({"للكعبه", "كعبه"}),
    "لعبه": frozenset({"لعبه"}), "اللعبه": frozenset({"اللعبه", "لعبه"}),
}
_ALLAH_FORMS = frozenset({"الله", "لله", "والله", "فالله", "بالله", "وبالله", "تالله", "ولله", "فلله"})


def normalize_text(text: str | None) -> str:
    t = normalize_ar(text or "").lower()
    return _APOS_S_RE.sub("", t).replace("'", "").replace("’", "").replace("\ufdfa", "")


def tokenize(text: str | None) -> list[str]:
    out: list[str] = []
    for tok in _WORD_RE.findall(normalize_text(text)):
        if _ARABIC_RE.search(tok) and _LATIN_RE.search(tok):
            out.extend(_SCRIPT_SPLIT_RE.split(tok))
        else:
            out.append(tok)
    return out


def has_both_scripts(tf) -> bool:
    """True when the turn mixes Arabic and Latin words (code-switching)."""
    vocab = getattr(tf, "vocab", None)
    if vocab is None:
        vocab = frozenset().union(*tf) if tf else frozenset()
    has_ar = has_lat = False
    for f in vocab:
        if _ARABIC_RE.search(f):
            has_ar = True
        elif _LATIN_RE.search(f):
            has_lat = True
        if has_ar and has_lat:
            return True
    return False


def qmark_positions(text: str | None) -> list[int]:
    """Index (in ``tokenize(text)``) of the token right before each '?' or '؟'; -1 if none."""
    t = normalize_text(text)
    return [len(tokenize(t[:m.start()])) - 1 for m in re.finditer(r"[?؟]", t)]


def has_arabic(text: str | None) -> bool:
    return bool(_ARABIC_RE.search(text or ""))


def forms(token: str) -> frozenset[str]:
    """All the spellings a token may be matched under (clitics, plurals)."""
    out = {token}
    if token in _ALLAH_FORMS:
        return frozenset((token, "الله", "لله"))
    if token in _ROOT_FIRST:  # the first letter is part of the word, not a clitic
        return _ROOT_FIRST[token]
    if _ARABIC_RE.search(token):
        for p in _AR_PREFIXES:
            if token.startswith(p) and len(token) - len(p) >= 2:
                out.add(token[len(p):])
        # a second one-letter clitic after the first: وبيلمسني -> بيلمسني -> يلمسني
        for v in list(out):
            if len(v) >= 4 and v[0] in "وفبلك":
                out.add(v[1:])
        # dialect plurals drop the final nun: يتطلقون / يتطلقوا
        if len(token) >= 5 and token.endswith("ون"):
            out.add(token[:-1] + "ا")
        # feminine second person: لا تقولين / لا تقولي match لا تقول, and تخبري matches تخبر
        if len(token) >= 5 and token[0] == "ت":
            if token.endswith("ين"):
                out.update((token[:-1], token[:-2]))
            elif token.endswith("ي"):
                out.add(token[:-1])
        # "he does it to me" and "they do it to me" match each other: يضربني / يضربوني / يضربونني
        for v in list(out):
            if len(v) >= 5 and v[0] in "يت":
                if v.endswith("ونني"):
                    out.update((v[:-4] + "ني", v[:-4] + "يني"))
                elif v.endswith("وني"):
                    out.update((v[:-3] + "ني", v[:-3] + "يني"))
                elif v.endswith("يني"):
                    out.update((v[:-3] + "وني", v[:-3] + "ونني"))
                elif v.endswith("ني"):
                    out.update((v[:-2] + "وني", v[:-2] + "ونني"))
        return frozenset(out)
    if len(token) >= 4 and token.endswith("es"):
        out.add(token[:-2])
    if len(token) >= 4 and token.endswith("s"):
        out.add(token[:-1])
    return frozenset(out)


@dataclass(frozen=True)
class Term:
    """A keyword or phrase, pre-tokenised for matching."""
    text: str
    parts: tuple[frozenset[str], ...]

    @property
    def weight(self) -> int:
        return 2 if len(self.parts) > 1 else 1


def make_term(phrase: str) -> Term | None:
    toks = tokenize(phrase)
    if not toks:
        return None
    return Term(" ".join(toks), tuple(forms(t) for t in toks))


class TokenForms(list):
    """``token_forms`` result: the per-token form sets plus their union (``vocab``),
    so a term whose words are not in the turn at all is rejected in one set test."""

    def __init__(self, items=()):
        super().__init__(items)
        self.vocab: frozenset[str] = frozenset().union(*self) if self else frozenset()


def _absent(term: Term, tf) -> bool:
    vocab = getattr(tf, "vocab", None)
    return vocab is not None and any(p.isdisjoint(vocab) for p in term.parts)


def term_spans(term: Term, tf: list[frozenset[str]]) -> list[tuple[int, int]]:
    """(start, end) token positions of every occurrence of the term."""
    n = len(term.parts)
    if n == 0 or n > len(tf) or _absent(term, tf):
        return []
    return [
        (i, i + n)
        for i in range(len(tf) - n + 1)
        if all(term.parts[j] & tf[i + j] for j in range(n))
    ]


def term_in(term: Term, tf: list[frozenset[str]]) -> bool:
    n = len(term.parts)
    if n == 0 or n > len(tf) or _absent(term, tf):
        return False
    for i in range(len(tf) - n + 1):
        if all(term.parts[j] & tf[i + j] for j in range(n)):
            return True
    return False


def token_forms(text: str | None) -> list[frozenset[str]]:
    return TokenForms(forms(t) for t in tokenize(text))


class TermIndex:
    """Terms keyed by every spelling of their first word, so a turn only looks at the
    terms whose first word it actually contains (rule lists hold hundreds of phrases)."""

    __slots__ = ("terms", "_by_form")

    def __init__(self, terms=()):
        self.terms = tuple(terms)
        by_form: dict[str, list[Term]] = {}
        for t in self.terms:
            if t.parts:
                for f in t.parts[0]:
                    by_form.setdefault(f, []).append(t)
        self._by_form = by_form

    def __bool__(self) -> bool:
        return bool(self.terms)

    def candidates(self, tf) -> list[Term]:
        vocab = getattr(tf, "vocab", None)
        if vocab is None:
            return list(self.terms)
        found: dict[int, Term] = {}
        for f in vocab:
            for t in self._by_form.get(f, ()):
                found[id(t)] = t
        return list(found.values())

    def any_in(self, tf) -> bool:
        return any(term_in(t, tf) for t in self.candidates(tf))

    def spans(self, tf) -> list[tuple[int, int]]:
        return sorted({sp for t in self.candidates(tf) for sp in term_spans(t, tf)})


@dataclass(frozen=True)
class Rule:
    """All groups must match; a group matches if any of its terms does.

    ``window`` (tokens, 0 = unlimited) requires one match per group to sit within
    that many tokens of each other, so "my dad ... hit" far apart does not count.
    ``unless`` terms veto the rule ("pillow fight", "by accident").
    """
    id: str
    groups: tuple[tuple[Term, ...], ...]
    meta: str = ""
    unless: tuple[Term, ...] = ()
    window: int = 0
    notify_parent: bool = True
    values: tuple[str, ...] = ()   # level_b: value slugs whose items are served
    before_d: bool = False         # level_c: evaluated before the personal-case rules
    no_items: bool = False         # level_d / level_c: serve no items at all
    mode: str = ""                 # level_c: "REFER" answers the rule as a referral, not a scholars-differ topic
    both_scripts: bool = False     # mixed-language variant: only judged on a turn that mixes Arabic and Latin words
    _group_idx: tuple = field(init=False, repr=False, compare=False, default=())
    _unless_idx: object = field(init=False, repr=False, compare=False, default=None)

    def __post_init__(self):
        object.__setattr__(self, "_group_idx", tuple(TermIndex(g) for g in self.groups))
        object.__setattr__(self, "_unless_idx", TermIndex(self.unless))

    def matches(self, tf: list[frozenset[str]]) -> bool:
        if not self.groups:
            return False
        if self.both_scripts and not has_both_scripts(tf):
            return False
        if self.window:
            per_group = []
            for g in self._group_idx:
                spans = g.spans(tf)
                if not spans:
                    return False
                per_group.append(spans)
            if not any(
                max(e for _, e in combo) - min(st for st, _ in combo) <= self.window
                for combo in itertools.product(*per_group)
            ):
                return False
        elif not all(g.any_in(tf) for g in self._group_idx):
            return False
        return not self._unless_idx.any_in(tf)
