"""Markdown formatting for persisted Spec inspections."""
import json
from typing import Any

from app.models.spec_inspection import SpecInspection


def render_inspection_block(row: SpecInspection, model_name: str) -> list[str]:
    """Return Markdown lines for one inspection, or empty when unusable."""
    findings = _parse_findings(row.findings)
    if findings is None:
        return []
    summary = _summary_from(row, findings)
    criteria_lines = _criteria_lines(findings)
    if summary is None and len(criteria_lines) == 0:
        return []
    lines = [f"Inspection ({model_name}, {row.created_at[:10]}):", ""]
    if summary is not None:
        lines.extend([summary, ""])
    lines.extend(criteria_lines)
    if criteria_lines:
        lines.append("")
    return lines


def _parse_findings(raw_findings: str) -> dict[str, Any] | None:
    try:
        value = json.loads(raw_findings)
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None


def _summary_from(row: SpecInspection, findings: dict[str, Any]) -> str | None:
    value = row.summary if row.summary is not None else findings.get("summary")
    if not isinstance(value, str):
        return None
    summary = value.strip()
    return summary or None


def _criteria_lines(findings: dict[str, Any]) -> list[str]:
    criteria = findings.get("criteria")
    if not isinstance(criteria, list):
        return []
    lines: list[str] = []
    for criterion in criteria:
        line = _criterion_line(criterion)
        if line is not None:
            lines.append(line)
    return lines


def _criterion_line(criterion: object) -> str | None:
    if not isinstance(criterion, dict):
        return None
    name = criterion.get("name")
    verdict = criterion.get("verdict")
    if not isinstance(name, str) or not isinstance(verdict, str):
        return None
    normalized_verdict = verdict.strip().upper()
    if normalized_verdict == "":
        return None
    line = f"- {name.strip()}: {normalized_verdict}"
    note = criterion.get("note")
    if normalized_verdict != "PASS" and isinstance(note, str) and note.strip() != "":
        line = f"{line} — {note.strip()}"
    return line
