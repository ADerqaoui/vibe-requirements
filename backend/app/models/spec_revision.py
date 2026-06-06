"""Spec revision ORM model."""
from sqlalchemy import ForeignKey, Integer, Text, UniqueConstraint, text as sql_text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class SpecRevision(Base):
    """Immutable audit snapshot for one Spec change."""

    __tablename__ = "spec_revisions"
    __table_args__ = (UniqueConstraint("spec_id", "revision_number"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    spec_id: Mapped[int] = mapped_column(Integer, ForeignKey("specs.id", ondelete="CASCADE"))
    revision_number: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(Text, nullable=False)
    change_type: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[str] = mapped_column(Text, nullable=False, server_default=sql_text("datetime('now')"))
