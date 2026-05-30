"""Blacklist entry ORM model."""
from sqlalchemy import CheckConstraint, ForeignKey, Integer, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class BlacklistEntry(Base):
    """Rejected or edited-out text tied to exactly one parent."""

    __tablename__ = "blacklist_entries"
    __table_args__ = (
        CheckConstraint("source IN ('rejected','edited_out')"),
        CheckConstraint("(parent_need_id IS NOT NULL) <> (parent_spec_id IS NOT NULL)"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    parent_need_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("needs.id", ondelete="CASCADE"))
    parent_spec_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("specs.id", ondelete="CASCADE"))
    text: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("datetime('now')"))
