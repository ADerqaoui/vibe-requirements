"""Discipline ORM model."""
from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Discipline(Base):
    """Seeded engineering discipline."""

    __tablename__ = "disciplines"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
