"""Layer ORM model."""
from sqlalchemy import CheckConstraint, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Layer(Base):
    """Seeded V-model layer."""

    __tablename__ = "layers"
    __table_args__ = (
        CheckConstraint("kind IN ('cross_cutting','discipline_locked')"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    kind: Mapped[str] = mapped_column(Text, nullable=False)
    discipline: Mapped[str | None] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)
