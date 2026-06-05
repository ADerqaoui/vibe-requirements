"""Requirement ID service tests."""
from sqlalchemy.orm import Session

from app.models.layer import Layer
from app.models.need import Need
from app.models.project import Project
from app.models.spec import Spec
from app.seed.run import backfill_missing_req_ids, seed_reference_data
from app.services.spec_service import create_spec_for_need, create_spec_for_parent_spec, update_spec_text


def seed_project_need(db_session: Session) -> tuple[Project, Need, Layer, Layer]:
    """Seed a project, need, and two target layers."""
    seed_reference_data(db_session)
    project = Project(name="Demo")
    db_session.add(project)
    db_session.flush()
    need = Need(project_id=project.id, statement="Stop safely")
    db_session.add(need)
    db_session.flush()
    system_req = db_session.query(Layer).filter_by(name="System Requirement").one()
    system_arch = db_session.query(Layer).filter_by(name="System Architecture").one()
    db_session.commit()
    return project, need, system_req, system_arch


def test_req_id_assignment_sequences_per_project_and_layer(db_session: Session) -> None:
    """New specs get stable per-project/layer requirement IDs."""
    _project, need, system_req, system_arch = seed_project_need(db_session)

    first = create_spec_for_need(db_session, need.id, "First", system_req.id)
    second = create_spec_for_need(db_session, need.id, "Second", system_req.id)
    child = create_spec_for_parent_spec(db_session, first.id, "Child", system_arch.id)

    assert first.req_id == "REQ-SYS-0001"
    assert second.req_id == "REQ-SYS-0002"
    assert child.req_id == "REQ-SYSA-0001"


def test_req_id_is_stable_across_text_edit(db_session: Session) -> None:
    """Editing text does not reassign the requirement ID."""
    _project, need, system_req, _system_arch = seed_project_need(db_session)
    spec = create_spec_for_need(db_session, need.id, "Original", system_req.id)

    updated = update_spec_text(db_session, spec.id, "Edited")

    assert updated.req_id == spec.req_id
    assert updated.text == "Edited"
    assert updated.source == "manual"


def test_seed_backfill_assigns_missing_req_ids_idempotently(db_session: Session) -> None:
    """Seed backfill assigns missing IDs by project/layer/id and never reassigns."""
    _project, need, system_req, system_arch = seed_project_need(db_session)
    existing = Spec(need_id=need.id, layer_id=system_req.id, text="Existing", source="ai", req_id="REQ-SYS-0007")
    missing_a = Spec(need_id=need.id, layer_id=system_req.id, text="Missing A", source="ai")
    missing_b = Spec(need_id=need.id, layer_id=system_req.id, text="Missing B", source="ai")
    missing_other_layer = Spec(need_id=need.id, layer_id=system_arch.id, text="Missing C", source="ai")
    db_session.add_all([existing, missing_a, missing_b, missing_other_layer])
    db_session.commit()

    first_count = backfill_missing_req_ids(db_session)
    assigned = {spec.text: spec.req_id for spec in db_session.query(Spec).order_by(Spec.id).all()}
    second_count = backfill_missing_req_ids(db_session)

    assert first_count == 3
    assert second_count == 0
    assert assigned == {
        "Existing": "REQ-SYS-0007",
        "Missing A": "REQ-SYS-0008",
        "Missing B": "REQ-SYS-0009",
        "Missing C": "REQ-SYSA-0001",
    }
