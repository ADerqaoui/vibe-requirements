"""Prompt registry ORM model."""
from sqlalchemy import ForeignKey, Integer, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Prompt(Base):
    """Prompt template registry row."""

    __tablename__ = "prompts"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    layer_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("layers.id"))
    task: Mapped[str] = mapped_column(Text, nullable=False)
    discipline_scope: Mapped[str | None] = mapped_column(Text)
    version: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    template: Mapped[str] = mapped_column(Text, nullable=False)
    enabled: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    created_at: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("datetime('now')"))
    updated_at: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("datetime('now')"))
