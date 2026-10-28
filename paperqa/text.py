"""Small text utilities shared by ingestion, retrieval and answering."""
from __future__ import annotations

import re

# Generic English stop words (kept small on purpose; BM25/TF-IDF handle the rest).
STOP = set(
    """a an the of in on at to for from by with and or but if as is are was were be been being
    this that these those it its we our us you your they their he she his her i not no do does
    did done have has had can could may might will would shall should than then so such into over
    under about between within without per via also very""".split()
)

# Words that appear in questions but carry no topical signal about the paper.
QSTOP = STOP | set(
    """what which who whom whose when where why how many much paper authors author study work
    approach method methods used use using reported report describe described mention mentioned
    state states say says given give value number does""".split()
)

_TOKEN_RE = re.compile(r"[a-z0-9]+(?:\.[0-9]+)?")
_ABBREVIATIONS = ("e.g.", "i.e.", "fig.", "eq.", "et al.", "vs.", "cf.", "no.", "sec.", "tab.")


def stem(word: str) -> str:
    """Very light suffix stripper (plural / -ing / -ed / trailing e). Deterministic and fast."""
    if not word.isalpha():
        return word
    if word.endswith("s") and not word.endswith("ss") and len(word) > 3:
        word = word[:-1]
    for suffix in ("ing", "ed"):
        if word.endswith(suffix) and len(word) > len(suffix) + 3:
            word = word[: -len(suffix)]
            break
    if word.endswith("e") and len(word) > 4:
        word = word[:-1]
    return word


def tokenize(text: str, stop: set[str] | None = STOP) -> list[str]:
    """Lower-case, split on non-alphanumerics (keeping decimals like 80.0), drop stop words, stem."""
    tokens = _TOKEN_RE.findall(text.lower())
    return [stem(t) for t in tokens if not stop or t not in stop]


def normalize_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def squash(text: str) -> str:
    """Lower-case and remove ALL whitespace; used for robust substring matching of evidence."""
    return re.sub(r"\s+", "", text).lower()


_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\[\(\"'])")


def sentence_spans(text: str) -> list[tuple[int, int]]:
    """Return (start, end) character spans of sentences, merging splits after common abbreviations."""
    spans: list[tuple[int, int]] = []
    start = 0
    for match in _SPLIT_RE.finditer(text):
        end = match.start()
        if text[start:end].lower().endswith(_ABBREVIATIONS):
            continue
        spans.append((start, end))
        start = match.end()
    if start < len(text):
        spans.append((start, len(text)))
    return spans


def split_sentences(text: str) -> list[str]:
    return [text[a:b] for a, b in sentence_spans(text) if text[a:b].strip()]
