"""Persisted single-model Spec inspection."""
from sqlalchemy import ForeignKey, Integer, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class SpecInspection(Base):
    """One persisted inspector result for a Spec."""

    __tablename__ = "spec_inspections"

    id: Mapped[int] = mapped_column(primary_key=True)
    spec_id: Mapped[int] = mapped_column(Integer, ForeignKey("specs.id", ondelete="CASCADE"))
    model_id: Mapped[int] = mapped_column(Integer, ForeignKey("models.id"))
    findings: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    passes: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    created_at: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("datetime('now')"))
