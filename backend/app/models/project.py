"""Project ORM model."""
from sqlalchemy import Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Project(Base):
    """Top-level project."""

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    created_at: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("datetime('now')"))
