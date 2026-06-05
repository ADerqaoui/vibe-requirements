"""Project Markdown export rendering tests."""
from pathlib import Path

from sqlalchemy.orm import Session

from app.export.markdown import render_project_markdown
from app.models.layer import Layer
from app.models.model import Model
from app.models.need import Need
from app.models.project import Project
from app.models.prompt import Prompt
from app.models.spec import Spec

GOLDEN_DIR = Path(__file__).parent / "goldens"


def normalize_trailing_whitespace(value: str) -> str:
    """Normalize line-end whitespace for byte-for-byte content comparison."""
    return "\n".join(line.rstrip() for line in value.splitlines()) + "\n"


def seed_basic_export(db_session: Session) -> int:
    """Seed deterministic Project -> Need -> Spec tree."""
    Model.__table__
    Prompt.__table__
    project = Project(name="Brake Controller")
    layer = Layer(name="System Requirement", kind="cross_cutting", sort_order=10)
    db_session.add_all([project, layer])
    db_session.flush()
    need_one = Need(project_id=project.id, statement="Stop vehicle")
    need_two = Need(project_id=project.id, statement="Report diagnostics")
    db_session.add_all([need_one, need_two])
    db_session.flush()
    root_one = Spec(
        need_id=need_one.id,
        layer_id=layer.id,
        text="The system shall apply brakes.",
        complexity=3,
        source="ai",
        req_id="REQ-SYS-0001",
    )
    root_two = Spec(
        need_id=need_one.id,
        layer_id=layer.id,
        text="The system shall alert the driver.",
        source="ai",
        req_id="REQ-SYS-0002",
    )
    root_three = Spec(
        need_id=need_two.id,
        layer_id=layer.id,
        text="The system shall record diagnostic faults.",
        complexity=5,
        source="ai",
        req_id="REQ-SYS-0003",
    )
    db_session.add_all([root_one, root_two, root_three])
    db_session.flush()
    child = Spec(
        need_id=need_one.id,
        parent_spec_id=root_one.id,
        layer_id=layer.id,
        text="The brake actuator shall engage within 100 ms.",
        source="ai",
        req_id="REQ-SYS-0004",
    )
    db_session.add(child)
    db_session.commit()
    return project.id


def test_render_project_markdown_matches_golden(db_session: Session) -> None:
    """Rendered export matches the golden file exactly after whitespace normalization."""
    project_id = seed_basic_export(db_session)
    expected = (GOLDEN_DIR / "export_basic.md").read_text()

    rendered = render_project_markdown(db_session, project_id)

    assert normalize_trailing_whitespace(rendered) == normalize_trailing_whitespace(expected)


def test_render_empty_project(db_session: Session) -> None:
    """Projects without Needs render an empty-state line and zero footer."""
    project = Project(name="Empty")
    db_session.add(project)
    db_session.commit()

    rendered = render_project_markdown(db_session, project.id)

    assert "_No needs yet._" in rendered
    assert "Needs: 0\nSpecs: 0\nClassified: 0 of 0\n" in rendered


def test_render_need_without_specs(db_session: Session) -> None:
    """Needs without Specs render an empty-state line."""
    project = Project(name="Only Needs")
    db_session.add(project)
    db_session.flush()
    db_session.add(Need(project_id=project.id, statement="Need without specs"))
    db_session.commit()

    rendered = render_project_markdown(db_session, project.id)

    assert "## Need: Need without specs\n\n_No specs yet._" in rendered


def test_render_complexity_only_when_present(db_session: Session) -> None:
    """Complexity tags appear only for classified specs."""
    project_id = seed_basic_export(db_session)

    rendered = render_project_markdown(db_session, project_id)

    assert rendered.count("**Complexity:**") == 2
    assert "**Complexity:** 3" in rendered
    assert "**Complexity:** 5" in rendered


def test_export_markdown_renders_grandchild_heading_levels(
    db_session: Session,
) -> None:
    """Recursive Spec headings increase deterministically by depth."""
    Model.__table__
    Prompt.__table__
    project = Project(name="Nested Export")
    layer = Layer(name="System Requirement", kind="cross_cutting", sort_order=10)
    db_session.add_all([project, layer])
    db_session.flush()
    need = Need(project_id=project.id, statement="Nested need")
    db_session.add(need)
    db_session.flush()
    root = Spec(
        need_id=need.id,
        layer_id=layer.id,
        text="Root spec",
        source="ai",
    )
    db_session.add(root)
    db_session.flush()
    child = Spec(
        need_id=need.id,
        parent_spec_id=root.id,
        layer_id=layer.id,
        text="Child spec",
        source="ai",
    )
    db_session.add(child)
    db_session.flush()
    grandchild = Spec(
        need_id=need.id,
        parent_spec_id=child.id,
        layer_id=layer.id,
        text="Grandchild spec",
        source="ai",
    )
    db_session.add(grandchild)
    db_session.commit()

    rendered = render_project_markdown(db_session, project.id)

    headings = [line for line in rendered.splitlines() if "Spec:" in line]
    assert headings == [
        "### Spec: **REQ-UNASSIGNED** — Root spec",
        "#### Spec: **REQ-UNASSIGNED** — Child spec",
        "##### Spec: **REQ-UNASSIGNED** — Grandchild spec",
    ]
