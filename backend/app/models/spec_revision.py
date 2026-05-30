"""Spec revision ORM model."""
from sqlalchemy import ForeignKey, Integer, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class SpecRevision(Base):
    """Read-only snapshot of a superseded accepted spec."""

    __tablename__ = "spec_revisions"

    id: Mapped[int] = mapped_column(primary_key=True)
    spec_id: Mapped[int] = mapped_column(Integer, ForeignKey("specs.id", ondelete="CASCADE"))
    revision_no: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    layer_id: Mapped[int] = mapped_column(Integer, nullable=False)
    disciplines: Mapped[str | None] = mapped_column(Text)
    diagram_src: Mapped[str | None] = mapped_column(Text)
    reason: Mapped[str | None] = mapped_column(Text)
    archived_at: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("datetime('now')"))
