"""Need ORM model."""
from sqlalchemy import CheckConstraint, ForeignKey, Integer, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Need(Base):
    """User need under a project."""

    __tablename__ = "needs"
    __table_args__ = (CheckConstraint("complexity BETWEEN 1 AND 5"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id", ondelete="CASCADE"))
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    context: Mapped[str | None] = mapped_column(Text)
    constraints: Mapped[str | None] = mapped_column(Text)
    complexity: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("datetime('now')"))
    updated_at: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("datetime('now')"))
