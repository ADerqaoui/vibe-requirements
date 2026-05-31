"""Permissive candidate parser for generated specifications."""
import re

HEADER_PREFIXES = ("candidate", "candidates", "specification", "specifications", "here are")
LIST_MARKER = re.compile(r"^\s*(?:[-*]\s+|\d+[\.)]\s+)(?P<text>.+?)\s*$")


class ParseError(Exception):
    """Raised when no generated candidates can be parsed."""


def parse_spec_candidates(text: str, count: int) -> list[str]:
    """Parse numbered, bulleted, or bare-line candidate output."""
    candidates: list[str] = []
    for raw_line in text.splitlines():
        if len(candidates) >= count:
            break
        candidate = _parse_line(raw_line)
        if candidate is None:
            continue
        candidates.append(candidate)
    if not candidates:
        raise ParseError("No specification candidates were parsed from the model response")
    return candidates


def _parse_line(raw_line: str) -> str | None:
    """Parse one candidate line or skip headers/commentary."""
    line = raw_line.strip()
    if line == "" or _is_header(line):
        return None
    marker_match = LIST_MARKER.match(line)
    if marker_match is not None:
        return _clean_candidate(marker_match.group("text"))
    return _clean_candidate(line)


def _is_header(line: str) -> bool:
    """Return true for common non-candidate intro/header lines."""
    normalized_line = line.casefold().rstrip(":")
    return normalized_line.startswith(HEADER_PREFIXES)


def _clean_candidate(value: str) -> str:
    """Normalize candidate text."""
    return value.strip().strip('"').strip()
