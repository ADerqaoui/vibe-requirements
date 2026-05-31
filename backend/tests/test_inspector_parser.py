"""Inspector findings parser tests."""
import pytest

from app.inspector.parser import ParseFindingsError, parse_findings


def test_parser_handles_all_pass_findings() -> None:
    """All criteria parse with normalized PASS verdicts."""
    result = parse_findings(
        """
        Findings:
        - Clarity: pass — Clear and direct.
        - Measurability: PASS - Has a threshold.
        - Testability: PASS: Test can verify it.
        - Atomicity: PASS — Covers one behavior.
        - Ambiguity-free: PASS — No vague words.
        """
    )

    assert [item["verdict"] for item in result["criteria"]] == ["PASS"] * 5
    assert result["criteria"][0]["note"] == "Clear and direct."
    assert result["summary"] is None


def test_parser_handles_mixed_verdicts_and_summary() -> None:
    """Mixed PASS/FAIL verdicts parse case-insensitively."""
    result = parse_findings(
        """
        - Clarity: FAIL — unclear actor.
        - Measurability: pass — measurable.
        Additional reviewer summary.
        - Testability: fail — no observable output.
        - Atomicity: PASS — one behavior.
        - Ambiguity-free: FAIL — says quickly.
        """
    )

    assert [item["verdict"] for item in result["criteria"]] == [
        "FAIL",
        "PASS",
        "FAIL",
        "PASS",
        "FAIL",
    ]
    assert result["summary"] == "Additional reviewer summary."


def test_parser_defaults_missing_criteria_to_unclear() -> None:
    """Known criteria omitted by the model are returned as UNCLEAR."""
    result = parse_findings("- Clarity: PASS — understandable.")

    assert result["criteria"][0]["verdict"] == "PASS"
    assert [item["verdict"] for item in result["criteria"][1:]] == ["UNCLEAR"] * 4


def test_parser_defaults_missing_verdict_to_unclear() -> None:
    """A criterion line without PASS/FAIL still yields an UNCLEAR criterion."""
    result = parse_findings("- Clarity: seems readable but not explicit")

    assert result["criteria"][0] == {
        "name": "Clarity",
        "verdict": "UNCLEAR",
        "note": "seems readable but not explicit",
    }


def test_parser_rejects_unparseable_text_with_clear_error() -> None:
    """Zero parsed criteria raises a clear parser error."""
    with pytest.raises(ParseFindingsError, match="No inspection criteria"):
        parse_findings("The response is fine, but has no criterion lines.")
