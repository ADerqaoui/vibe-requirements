"""Classification vote ORM model."""
from sqlalchemy import CheckConstraint, ForeignKey, Integer, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class ClassificationVote(Base):
    """Single model vote for complexity classification."""

    __tablename__ = "classification_votes"
    __table_args__ = (
        CheckConstraint("parent_type IN ('need','spec')"),
        CheckConstraint("vote BETWEEN 1 AND 5"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    parent_type: Mapped[str] = mapped_column(Text, nullable=False)
    parent_id: Mapped[int] = mapped_column(Integer, nullable=False)
    model_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("models.id"))
    vote: Mapped[int | None] = mapped_column(Integer)
    failed: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    created_at: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("datetime('now')"))
