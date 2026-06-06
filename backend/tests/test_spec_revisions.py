"""Spec revision service tests."""
import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.layer import Layer
from app.models.need import Need
from app.models.project import Project
from app.models.spec_revision import SpecRevision
from app.schemas.decision import DecisionValue
from app.seed.run import seed_reference_data
from app.services.decision_service import decide_spec
from app.services.spec_service import create_spec_for_need, create_spec_for_parent_spec, update_spec_text


def seed_need(db_session: Session) -> tuple[int, int]:
    """Seed one Need and return need/layer ids."""
    seed_reference_data(db_session)
    project = Project(name="Demo")
    db_session.add(project)
    db_session.flush()
    need = Need(project_id=project.id, statement="Stop safely")
    db_session.add(need)
    db_session.flush()
    layer = db_session.query(Layer).filter_by(name="System Requirement").one()
    need_id = need.id
    layer_id = layer.id
    db_session.commit()
    return need_id, layer_id


def revisions(db_session: Session, spec_id: int) -> list[SpecRevision]:
    """Return revision rows for assertions."""
    return list(
        db_session.scalars(
            select(SpecRevision).where(SpecRevision.spec_id == spec_id).order_by(SpecRevision.revision_number)
        ).all()
    )


def test_create_spec_records_created_revision(db_session: Session) -> None:
    """AI-created Specs start with a pending created revision."""
    need_id, _layer_id = seed_need(db_session)

    spec = create_spec_for_need(db_session, need_id, "The system shall brake.")

    history = revisions(db_session, spec.id)
    assert [(row.revision_number, row.change_type) for row in history] == [(1, "created")]
    assert history[0].text == spec.text
    assert history[0].status == "pending"
    assert history[0].source == "ai"


def test_text_edit_records_revision_and_preserves_original(db_session: Session) -> None:
    """Text edits append revision 2 without mutating revision 1."""
    need_id, _layer_id = seed_need(db_session)
    spec = create_spec_for_need(db_session, need_id, "Original")

    update_spec_text(db_session, spec.id, "Edited")

    history = revisions(db_session, spec.id)
    assert [(row.revision_number, row.text, row.change_type) for row in history] == [
        (1, "Original", "created"),
        (2, "Edited", "text_edited"),
    ]
    assert history[0].source == "ai"
    assert history[1].source == "manual"


@pytest.mark.parametrize("decision", ["accepted", "rejected"])
def test_decide_spec_records_status_revision(db_session: Session, decision: DecisionValue) -> None:
    """Accepting or rejecting a Spec appends a status_changed revision."""
    need_id, _layer_id = seed_need(db_session)
    spec = create_spec_for_need(db_session, need_id, "Candidate")

    decide_spec(db_session, spec.id, decision)

    history = revisions(db_session, spec.id)
    assert [(row.revision_number, row.status, row.change_type) for row in history] == [
        (1, "pending", "created"),
        (2, decision, "status_changed"),
    ]


def test_manual_and_ai_accepted_histories_are_distinct(db_session: Session) -> None:
    """Manual create starts accepted; AI create then accept has two revisions."""
    need_id, layer_id = seed_need(db_session)
    manual = create_spec_for_need(db_session, need_id, "Manual", layer_id, source="manual", status="accepted")
    ai = create_spec_for_need(db_session, need_id, "AI")
    decide_spec(db_session, ai.id, "accepted")

    manual_history = revisions(db_session, manual.id)
    ai_history = revisions(db_session, ai.id)
    assert [(row.change_type, row.status, row.source) for row in manual_history] == [
        ("created", "accepted", "manual")
    ]
    assert [(row.change_type, row.status, row.source) for row in ai_history] == [
        ("created", "pending", "ai"),
        ("status_changed", "accepted", "ai"),
    ]


def test_revision_numbering_is_per_spec_and_unique(db_session: Session) -> None:
    """Specs have independent sequential histories and enforce uniqueness."""
    need_id, _layer_id = seed_need(db_session)
    first = create_spec_for_need(db_session, need_id, "First")
    second = create_spec_for_need(db_session, need_id, "Second")
    update_spec_text(db_session, first.id, "First edited")

    assert [row.revision_number for row in revisions(db_session, first.id)] == [1, 2]
    assert [row.revision_number for row in revisions(db_session, second.id)] == [1]
    db_session.add(
        SpecRevision(
            spec_id=first.id,
            revision_number=2,
            text="Duplicate",
            status="pending",
            source="ai",
            change_type="created",
        )
    )
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_child_spec_creation_records_created_revision(db_session: Session) -> None:
    """Child Spec creation also records revision 1."""
    need_id, _layer_id = seed_need(db_session)
    parent = create_spec_for_need(db_session, need_id, "Parent")
    child_layer = db_session.query(Layer).filter_by(name="System Architecture").one()

    child = create_spec_for_parent_spec(db_session, parent.id, "Child", child_layer.id)

    assert [(row.revision_number, row.text, row.change_type) for row in revisions(db_session, child.id)] == [
        (1, "Child", "created")
    ]
