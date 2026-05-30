"""Diagram ORM model."""
from sqlalchemy import ForeignKey, Integer, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Diagram(Base):
    """Mermaid diagram associated with one spec."""

    __tablename__ = "diagrams"

    id: Mapped[int] = mapped_column(primary_key=True)
    spec_id: Mapped[int] = mapped_column(Integer, ForeignKey("specs.id", ondelete="CASCADE"), unique=True)
    title: Mapped[str | None] = mapped_column(Text)
    diagram_type: Mapped[str] = mapped_column(Text, nullable=False)
    mermaid_source: Mapped[str] = mapped_column(Text, nullable=False)
    out_of_date: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    created_at: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("datetime('now')"))
    updated_at: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("datetime('now')"))
