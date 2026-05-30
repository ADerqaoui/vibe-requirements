"""Layer parent ORM model."""
from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class LayerParent(Base):
    """Allowed parent relationship between two V-model layers."""

    __tablename__ = "layer_parents"

    layer_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("layers.id", ondelete="CASCADE"),
        primary_key=True,
    )
    parent_layer_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("layers.id", ondelete="CASCADE"),
        primary_key=True,
    )
