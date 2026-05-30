"""Model registry ORM model."""
from sqlalchemy import CheckConstraint, Integer, Real, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Model(Base):
    """LLM model registry row."""

    __tablename__ = "models"
    __table_args__ = (CheckConstraint("tier IN ('low','mid','high')"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    provider: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    ollama_tag: Mapped[str | None] = mapped_column(Text)
    api_model_id: Mapped[str | None] = mapped_column(Text)
    tier: Mapped[str] = mapped_column(Text, nullable=False)
    input_cost_per_1k: Mapped[float] = mapped_column(Real, nullable=False, server_default="0")
    output_cost_per_1k: Mapped[float] = mapped_column(Real, nullable=False, server_default="0")
    enabled: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    created_at: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("datetime('now')"))
