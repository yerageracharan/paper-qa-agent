"""Conservative, opt-in checks for explicit anchors in a question.

These rules are not a general entailment model. They catch a narrow class of
high-specificity questions where the required entity or procedure is absent
from the full paper, even though generic topic words may overlap.
"""
from __future__ import annotations

import re

ACRONYM_RE = re.compile(r"\b(?:[A-Z][A-Z0-9-]{1,}|[A-Z][a-z]+[A-Z][A-Za-z0-9]*)\b")
_HUMAN_EVALUATION_QUESTION_RE = re.compile(
    r"\bhuman\s+(?:evaluation|study|assessment|testing)\b", re.IGNORECASE
)
_HUMAN_EVALUATION_EVIDENCE_RE = re.compile(
    r"\b(?:"
    r"human[- ]?(?:evaluation|study|assessment|testing|subjects?)|"
    r"participants?|interviews?|surveys?|"
    r"user[- ]stud(?:y|ies)|usability[- ](?:study|testing|evaluation)"
    r")\b",
    re.IGNORECASE,
)


def find_missing_question_anchor(question: str, paper_text: str) -> str | None:
    """Return a missing anchor code, or None when this narrow check passes.

    All-caps technical acronyms in the question must occur as whole tokens in
    the paper. A question explicitly asking about a human evaluation/study must
    have human-study evidence (human evaluation/study, participants, interviews,
    surveys, a user study, or a usability study) somewhere in the paper.

    This is a conservative lexical safeguard, not proof of entailment. It is
    opt-in because an author may use a long-form name instead of an acronym,
    or describe a study using terminology outside the recognised alternatives.
    """
    corpus_upper = paper_text.upper()
    for acronym in dict.fromkeys(_ACRONYM_RE.findall(question)):
        if not re.search(rf"\b{re.escape(acronym)}\b", corpus_upper):
            return f"missing_acronym:{acronym}"

    if _HUMAN_EVALUATION_QUESTION_RE.search(question):
        if not _HUMAN_EVALUATION_EVIDENCE_RE.search(paper_text):
            return "missing_human_evaluation_evidence"

    return None
