"""Call log ORM model."""
from sqlalchemy import CheckConstraint, ForeignKey, Integer, Real, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class CallLog(Base):
    """Audit and cost row for one LLM call."""

    __tablename__ = "call_logs"
    __table_args__ = (CheckConstraint("status IN ('success','failure')"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("projects.id", ondelete="SET NULL"))
    spec_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("specs.id", ondelete="SET NULL"))
    parent_type: Mapped[str | None] = mapped_column(Text)
    parent_id: Mapped[int | None] = mapped_column(Integer)
    task: Mapped[str] = mapped_column(Text, nullable=False)
    provider: Mapped[str] = mapped_column(Text, nullable=False)
    model_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("models.id"))
    prompt_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("prompts.id"))
    prompt_version: Mapped[int | None] = mapped_column(Integer)
    in_tokens: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    out_tokens: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    cost_sek: Mapped[float] = mapped_column(Real, nullable=False, server_default="0")
    fx_rate: Mapped[float] = mapped_column(Real, nullable=False, server_default="0")
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    rendered_prompt: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("datetime('now')"))
