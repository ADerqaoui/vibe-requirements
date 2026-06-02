"""Parse single-model inspector findings."""
from typing import TypedDict
import re

CRITERIA = ("Clarity", "Measurability", "Testability", "Atomicity", "Ambiguity-free")
KNOWN_CRITERIA = {criterion.casefold(): criterion for criterion in CRITERIA}
VERDICTS = {"PASS", "FAIL"}
DEFAULT_VERDICT = "UNCLEAR"
DEFAULT_NOTE = "Not reported by inspector."
LINE_PATTERN = re.compile(
    r"^\s*(?:[-*]\s*)?(?P<name>[A-Za-z][A-Za-z -]*?)\s*:\s*(?P<body>.+?)\s*$"
)
VERDICT_PATTERN = re.compile(r"\b(pass|fail|unclear)\b", re.IGNORECASE)
NOTE_PREFIX_PATTERN = re.compile(r"^\s*(?:[-–—:]\s*)+")
SKIP_HEADERS = {"findings", "criteria", "inspection", "summary", "specification"}


class ParseFindingsError(Exception):
    """Raised when no inspection criteria can be parsed."""


class FindingCriterion(TypedDict):
    """Parsed verdict for one criterion."""

    name: str
    verdict: str
    note: str


class ParsedFindings(TypedDict):
    """Parsed inspector output."""

    criteria: list[FindingCriterion]
    summary: str | None


def parse_findings(text: str) -> ParsedFindings:
    """Parse inspector output into normalized criteria and optional summary."""
    found: dict[str, FindingCriterion] = {}
    summary_lines: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line == "" or _is_header(line):
            continue
        match = LINE_PATTERN.match(line)
        if match is None:
            summary_lines.append(line)
            continue
        name = _normalize_criterion_name(match.group("name"))
        if name is None:
            summary_lines.append(line)
            continue
        found[name] = _criterion_from_body(name, match.group("body"))

    if len(found) == 0:
        raise ParseFindingsError("No inspection criteria were parsed from the model response")

    criteria = [
        found.get(
            criterion,
            {"name": criterion, "verdict": DEFAULT_VERDICT, "note": DEFAULT_NOTE},
        )
        for criterion in CRITERIA
    ]
    summary = "\n".join(summary_lines).strip()
    return {"criteria": criteria, "summary": summary or None}


def _criterion_from_body(name: str, body: str) -> FindingCriterion:
    """Extract verdict and note from one criterion body."""
    verdict_match = VERDICT_PATTERN.search(body)
    if verdict_match is None:
        return {"name": name, "verdict": DEFAULT_VERDICT, "note": body.strip()}
    verdict = verdict_match.group(1).upper()
    note = body[verdict_match.end() :]
    normalized_note = NOTE_PREFIX_PATTERN.sub("", note).strip()
    return {"name": name, "verdict": verdict, "note": normalized_note}


def _normalize_criterion_name(name: str) -> str | None:
    """Return the canonical criterion name for a parsed line."""
    return KNOWN_CRITERIA.get(name.strip().casefold())


def _is_header(line: str) -> bool:
    """Return whether a line is structural commentary to ignore."""
    normalized = line.rstrip(":").casefold()
    return normalized in SKIP_HEADERS
