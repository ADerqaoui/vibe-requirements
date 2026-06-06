"""Spec revision audit service."""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.spec import Spec
from app.models.spec_revision import SpecRevision


def record_spec_revision(db: Session, spec: Spec, change_type: str) -> SpecRevision:
    """Append one immutable snapshot for the current Spec state."""
    revision = SpecRevision(
        spec_id=spec.id,
        revision_number=_next_revision_number(db, spec.id),
        text=spec.text,
        status=spec.status,
        source=spec.source,
        change_type=change_type,
    )
    db.add(revision)
    return revision


def list_spec_revisions(db: Session, spec_id: int) -> list[SpecRevision]:
    """Return Spec revisions in chronological order."""
    statement = (
        select(SpecRevision)
        .where(SpecRevision.spec_id == spec_id)
        .order_by(SpecRevision.revision_number)
    )
    return list(db.scalars(statement).all())


def backfill_missing_spec_revisions(db: Session) -> None:
    """Create baseline revisions for Specs without any history."""
    specs = db.scalars(
        select(Spec)
        .outerjoin(SpecRevision, SpecRevision.spec_id == Spec.id)
        .group_by(Spec.id)
        .having(func.count(SpecRevision.id) == 0)
        .order_by(Spec.id)
    ).all()
    for spec in specs:
        record_spec_revision(db, spec, "created")
    db.commit()


def _next_revision_number(db: Session, spec_id: int) -> int:
    current_max = db.scalar(
        select(func.coalesce(func.max(SpecRevision.revision_number), 0)).where(
            SpecRevision.spec_id == spec_id,
        )
    )
    return int(current_max or 0) + 1
