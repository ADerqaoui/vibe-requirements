"""Inspection finding ORM model."""
from sqlalchemy import CheckConstraint, ForeignKey, Integer, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class InspectionFinding(Base):
    """Inspector finding for a spec or archived spec revision."""

    __tablename__ = "inspection_findings"
    __table_args__ = (
        CheckConstraint("severity IN ('critical','major','minor')"),
        CheckConstraint("state IN ('open','dismissed')"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    spec_id: Mapped[int] = mapped_column(Integer, ForeignKey("specs.id", ondelete="CASCADE"))
    spec_revision_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("spec_revisions.id"))
    category: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    suggested_rewrite: Mapped[str | None] = mapped_column(Text)
    state: Mapped[str] = mapped_column(Text, nullable=False, server_default="open")
    not_evaluated: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    inspect_model_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("models.id"))
    archived_at: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("datetime('now')"))
