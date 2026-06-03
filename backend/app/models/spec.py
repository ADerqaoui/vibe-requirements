"""Spec ORM model."""
from sqlalchemy import CheckConstraint, ForeignKey, Integer, Text, text as sql_text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Spec(Base):
    """Requirement/spec node in the V-model tree."""

    __tablename__ = "specs"
    __table_args__ = (
        CheckConstraint("status IN ('pending','accepted','rejected')"),
        CheckConstraint("source IN ('ai','manual')"),
        CheckConstraint("complexity BETWEEN 1 AND 5"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    need_id: Mapped[int] = mapped_column(Integer, ForeignKey("needs.id", ondelete="CASCADE"))
    parent_spec_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("specs.id", ondelete="CASCADE"))
    layer_id: Mapped[int] = mapped_column(Integer, ForeignKey("layers.id"))
    text: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="pending")
    source: Mapped[str] = mapped_column(Text, nullable=False, server_default="ai")
    complexity: Mapped[int | None] = mapped_column(Integer)
    gen_model_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("models.id"))
    gen_prompt_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("prompts.id"))
    created_at: Mapped[str] = mapped_column(Text, nullable=False, server_default=sql_text("datetime('now')"))
    updated_at: Mapped[str] = mapped_column(Text, nullable=False, server_default=sql_text("datetime('now')"))
    layer: Mapped["Layer"] = relationship("Layer")
