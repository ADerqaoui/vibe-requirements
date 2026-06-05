"""Project Markdown inspection export rendering tests."""
from sqlalchemy.orm import Session

from app.export.markdown import render_project_markdown
from app.models.layer import Layer
from app.models.model import Model
from app.models.need import Need
from app.models.project import Project
from app.models.prompt import Prompt
from app.models.spec import Spec
from app.models.spec_inspection import SpecInspection


def test_export_markdown_renders_latest_inspection_block(db_session: Session) -> None:
    """Default export includes only the latest inspection summary and criteria."""
    project_id, spec_id, old_model_id, new_model_id = seed_inspected_spec(db_session)
    db_session.add_all([
        SpecInspection(
            spec_id=spec_id,
            model_id=old_model_id,
            findings='{"criteria":[{"name":"Clarity","verdict":"FAIL","note":"old"}],"summary":"Old"}',
            summary="Old",
            created_at="2026-06-04T10:00:00",
        ),
        SpecInspection(
            spec_id=spec_id,
            model_id=new_model_id,
            findings=(
                '{"criteria":['
                '{"name":"Clarity","verdict":"PASS","note":"clear"},'
                '{"name":"Verifiability","verdict":"FAIL","note":"no threshold"},'
                '{"name":"Atomicity","verdict":"UNCLEAR","note":"combines behavior"}'
                '],"summary":"Latest summary"}'
            ),
            summary="Latest summary",
            created_at="2026-06-05T12:00:00",
        ),
    ])
    db_session.commit()

    rendered = render_project_markdown(db_session, project_id)

    assert "Inspection (new-model, 2026-06-05):" in rendered
    assert "Latest summary" in rendered
    assert "- Clarity: PASS\n" in rendered
    assert "- Verifiability: FAIL — no threshold" in rendered
    assert "- Atomicity: UNCLEAR — combines behavior" in rendered
    assert "old-model" not in rendered
    assert "Old" not in rendered


def test_export_markdown_omits_uninspected_specs(db_session: Session) -> None:
    """Specs without inspections render no inspection block."""
    project_id, _spec_id, _old_model_id, _new_model_id = seed_inspected_spec(db_session)

    rendered = render_project_markdown(db_session, project_id)

    assert "Inspection (" not in rendered


def test_export_markdown_handles_empty_and_malformed_findings(db_session: Session) -> None:
    """Empty findings render gracefully and malformed JSON is skipped."""
    project_id, spec_id, _old_model_id, new_model_id = seed_inspected_spec(db_session)
    spec = db_session.get(Spec, spec_id)
    assert spec is not None
    second_spec = Spec(need_id=spec.need_id, layer_id=spec.layer_id, text="Malformed", source="ai")
    db_session.add(second_spec)
    db_session.flush()
    db_session.add_all([
        SpecInspection(
            spec_id=spec_id,
            model_id=new_model_id,
            findings='{"criteria":[],"summary":"Summary only"}',
            summary=None,
            created_at="2026-06-05T12:00:00",
        ),
        SpecInspection(
            spec_id=second_spec.id,
            model_id=new_model_id,
            findings="{not-json",
            summary="Should be skipped",
            created_at="2026-06-05T12:00:00",
        ),
    ])
    db_session.commit()

    rendered = render_project_markdown(db_session, project_id)

    assert "Inspection (new-model, 2026-06-05):" in rendered
    assert "Summary only" in rendered
    assert "Should be skipped" not in rendered


def test_export_markdown_include_inspections_false_matches_old_format(db_session: Session) -> None:
    """include_inspections=false preserves the requirements-only output."""
    project_id, spec_id, _old_model_id, new_model_id = seed_inspected_spec(db_session)
    db_session.add(
        SpecInspection(
            spec_id=spec_id,
            model_id=new_model_id,
            findings='{"criteria":[{"name":"Clarity","verdict":"FAIL","note":"bad"}],"summary":"Summary"}',
            summary="Summary",
            created_at="2026-06-05T12:00:00",
        )
    )
    db_session.commit()

    rendered = render_project_markdown(db_session, project_id, include_inspections=False)

    assert "### Spec: **REQ-SYS-0001** — The system shall brake.\n" in rendered
    assert "Inspection (" not in rendered


def seed_inspected_spec(db_session: Session) -> tuple[int, int, int, int]:
    """Seed one project/spec plus two models for inspection export tests."""
    Prompt.__table__
    project = Project(name="Inspected Project")
    layer = Layer(name="System Requirement", kind="cross_cutting", sort_order=10)
    old_model = Model(provider="ollama", name="old-model", ollama_tag="old", tier="mid")
    new_model = Model(provider="ollama", name="new-model", ollama_tag="new", tier="mid")
    db_session.add_all([project, layer, old_model, new_model])
    db_session.flush()
    need = Need(project_id=project.id, statement="Inspect need")
    db_session.add(need)
    db_session.flush()
    spec = Spec(need_id=need.id, layer_id=layer.id, text="The system shall brake.", source="ai", req_id="REQ-SYS-0001")
    db_session.add(spec)
    db_session.flush()
    db_session.commit()
    return project.id, spec.id, old_model.id, new_model.id
