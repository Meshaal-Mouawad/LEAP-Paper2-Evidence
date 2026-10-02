"""Shared executable rules for Paper 2 publication-audit checks.

The functions here are intentionally small and inspectable. They are imported by the
LEAP and external FastAPI audit scripts and by the checker-validation fixtures so that
validation exercises the exact released rule implementation.
"""
from __future__ import annotations

import re
from typing import Iterable, Tuple

_UNIT_TOKENS = {
    "ton", "tons", "kg", "g", "m3", "mm", "cm", "m", "s", "sec", "secs",
    "second", "seconds", "min", "mins", "minute", "minutes", "h", "hr", "hrs",
    "hour", "hours", "day", "days", "pct", "percent", "percentage",
}
_CONTRADICTION_RE = re.compile(
    r"\b(?:no|not|without)\b.{0,28}\b(?:zero|guard|handling|check|protection)\b|"
    r"\b(?:does\s+not|doesn't|is\s+not|isn't)\b.{0,28}\b(?:handle|handled|handling|check|checked|guard|guarded|protect|protected)\b|"
    r"\b(?:zero|guard|handling|check|protection)\b.{0,28}\b(?:disabled|inactive|absent|omitted)\b|"
    r"\b(?:disabled|inactive|absent|omitted)\b.{0,28}\b(?:zero|guard|handling|check|protection)\b",
    re.I,
)
_ZERO_SEMANTICS_RE = re.compile(r"\bzero\b|\bNULLIF\b|division\s+by\s+zero", re.I)
_ACTION_RE = re.compile(r"\b(?:check|checks|checked|return|returns|use|uses|prevent|prevents|avoid|avoids|guards|handle|handles|protect|protects|NULLIF)\b", re.I)
_NONPOSITIVE_RE = re.compile(
    r"non[- ]?positive|less\s+than\s+or\s+equal|<=|zero\s+(?:or|and)\s+negative|negative\s+(?:or|and)\s+zero",
    re.I,
)
_HEADING_ONLY_GUARD_RE = re.compile(
    r"^(?:zero[-\s]*division\s+guard|zero\s+guard|non[-\s]*positive\s+guard|division[-\s]*by[-\s]*zero\s+guard)\s*:?[\s.]*$",
    re.I,
)


def _tokens(value: str) -> list[str]:
    value = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", value or "")
    value = value.replace("_", " ")
    return re.findall(r"[a-z0-9]+", value.lower())


def canonical(value: str) -> str:
    return "".join(_tokens(value))


def variable_matches_label(variable: str, label: str) -> bool:
    """Match a source variable to a reader-facing denominator label.

    Empty labels never match. Unit-only suffix differences are ignored, e.g.
    ``total_gas_m3`` and ``Total Gas M3`` or ``baseline_threshold_mm_s`` and
    ``Baseline Threshold``. Arbitrary substring matching is deliberately rejected.
    """
    vt = _tokens(variable)
    lt = _tokens(label)
    if not vt or not lt:
        return False
    if vt == lt:
        return True
    vb = [t for t in vt if t not in _UNIT_TOKENS]
    lb = [t for t in lt if t not in _UNIT_TOKENS]
    return bool(vb and lb and vb == lb)


def guard_semantics_check(
    guard_variable: str,
    guard_kind: str,
    displayed_denominator: str,
    safeguard_text: str,
) -> Tuple[bool, str]:
    """Check whether a published safeguard faithfully communicates a source guard.

    The check requires all three of: a nonempty denominator, variable correspondence,
    and affirmative handling semantics. A heading alone is not evidence. Contradictory
    text is rejected. Non-positive source guards require non-positive semantics rather
    than zero-only wording.
    """
    if not (displayed_denominator or "").strip():
        return False, "displayed formula denominator is missing"
    if not variable_matches_label(guard_variable, displayed_denominator):
        return False, "guarded variable does not match displayed formula denominator"
    text = (safeguard_text or "").strip()
    if not text:
        return False, "reader-facing safeguard text is missing"
    if _HEADING_ONLY_GUARD_RE.fullmatch(text):
        return False, "reader-facing safeguard contains only a heading and no handling semantics"
    if _CONTRADICTION_RE.search(text):
        return False, "reader-facing safeguard text contradicts the existence of handling"
    if guard_kind == "zero":
        if not _ZERO_SEMANTICS_RE.search(text):
            return False, "reader-facing safeguard does not communicate zero handling"
    elif guard_kind == "nonpositive":
        if not _NONPOSITIVE_RE.search(text):
            return False, "non-positive guard reduced to zero-only wording"
    else:
        return False, "guard semantics outside deterministic zero/non-positive scope"
    if not _ACTION_RE.search(text):
        return False, "reader-facing safeguard states a condition but does not communicate handling"
    return True, "guard, displayed denominator, and handling semantics align"


def compare_published_role(
    expected_location: str,
    expected_name: str,
    published_location: str,
    published_name: str,
) -> Tuple[bool, str]:
    """Compare an independently read source role/name with generated documentation."""
    el = (expected_location or "").strip().lower()
    en = (expected_name or "").strip()
    pl = (published_location or "").strip().lower()
    pn = (published_name or "").strip()
    if not el or not en:
        return False, "source expectation is incomplete"
    if pl != el:
        return False, f"published location {pl!r} != source location {el!r}"
    if pn != en:
        return False, f"published name {pn!r} != source name {en!r}"
    return True, "published role and name match source"


def conflict_routing_check(explicit_conflict: bool, status: str, review_queue_present: bool) -> str:
    if not explicit_conflict:
        return "N/A"
    return "PASS" if status == "Needs Review" and review_queue_present else "FAIL"


def authority_consistency_check(status: str, certification_phrases: Iterable[str]) -> str:
    if status != "Needs Review":
        return "N/A"
    return "FAIL" if any(str(x).strip() for x in certification_phrases) else "PASS"


def comment_role_defect(raw_source: str, published_description: str, executable_prefixes: tuple[str, ...]) -> bool:
    raw = (raw_source or "").strip()
    is_comment = raw.startswith(("#", "//", "--", "*", "'", '"""', "'''"))
    return bool(is_comment and (published_description or "").startswith(executable_prefixes))
