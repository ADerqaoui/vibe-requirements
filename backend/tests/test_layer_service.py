"""Layer service tests."""
import pytest
from sqlalchemy.orm import Session

from app.models.layer import Layer
from app.seed.run import seed_reference_data
from app.services.layer_service import (
    LayerNotFoundError,
    allowed_children_for_layer,
    allowed_children_for_need,
)


def test_allowed_children_for_need_and_system_requirement(db_session: Session) -> None:
    """Allowed children are derived from seeded layer parent rows."""
    seed_reference_data(db_session)
    system_requirement = db_session.query(Layer).filter_by(name="System Requirement").one()

    need_children = allowed_children_for_need(db_session)
    system_children = allowed_children_for_layer(db_session, system_requirement.id)

    assert [layer.name for layer in need_children] == ["System Requirement"]
    assert [layer.name for layer in system_children] == [
        "System Architecture",
        "SW Requirement",
        "Electronic Requirement",
        "Mechanical Requirement",
    ]


def test_allowed_children_unknown_layer_raises(db_session: Session) -> None:
    """Unknown parent layers raise a typed not-found error."""
    seed_reference_data(db_session)

    with pytest.raises(LayerNotFoundError):
        allowed_children_for_layer(db_session, 404)
