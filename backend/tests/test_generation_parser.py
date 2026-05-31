"""Generation parser tests."""
import pytest

from app.generation.parser import ParseError, parse_spec_candidates


def test_parser_handles_numbered_output() -> None:
    """Numbered lists are parsed in order."""
    text = "1. The system shall stop.\n2. The system shall alert."

    assert parse_spec_candidates(text, 5) == [
        "The system shall stop.",
        "The system shall alert.",
    ]


def test_parser_handles_bulleted_output() -> None:
    """Dash and star bullets are parsed."""
    text = "- The system shall log events.\n* The system shall show status."

    assert parse_spec_candidates(text, 5) == [
        "The system shall log events.",
        "The system shall show status.",
    ]


def test_parser_handles_bare_lines_and_count_limit() -> None:
    """Bare lines are candidates and count limits are respected."""
    text = "The system shall brake.\nThe system shall steer.\nThe system shall report."

    assert parse_spec_candidates(text, 2) == [
        "The system shall brake.",
        "The system shall steer.",
    ]


def test_parser_skips_headers_in_mixed_output() -> None:
    """Common headers/commentary are skipped."""
    text = "Specifications:\n1) First statement\n- Second statement\nCandidate specs:\nThird statement"

    assert parse_spec_candidates(text, 5) == [
        "First statement",
        "Second statement",
        "Third statement",
    ]


def test_parser_rejects_empty_output() -> None:
    """Empty or header-only output raises a clear parser error."""
    with pytest.raises(ParseError, match="No specification candidates"):
        parse_spec_candidates("Specifications:\n\nCandidates:", 3)
