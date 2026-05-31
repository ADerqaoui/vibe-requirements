"""Spec lifecycle decision service."""
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.spec import Spec
from app.schemas.decision import DecisionValue


class SpecNotFoundError(Exception):
    """Raised when a Spec does not exist."""


def decide_spec(db: Session, spec_id: int, decision: DecisionValue) -> Spec:
    """Set a Spec to an accepted or rejected lifecycle status."""
    spec = db.get(Spec, spec_id)
    if spec is None:
        raise SpecNotFoundError
    spec.status = decision
    spec.updated_at = datetime.now(UTC).replace(microsecond=0).isoformat()
    db.commit()
    db.refresh(spec)
    return spec
