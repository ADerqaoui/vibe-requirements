"""Spec discipline ORM model."""
from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class SpecDiscipline(Base):
    """Discipline membership for one spec."""

    __tablename__ = "spec_disciplines"

    spec_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("specs.id", ondelete="CASCADE"),
        primary_key=True,
    )
    discipline_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("disciplines.id"),
        primary_key=True,
    )
