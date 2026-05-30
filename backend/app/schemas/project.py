"""Project API schemas."""
from pydantic import BaseModel, ConfigDict, Field


class ProjectCreate(BaseModel):
    """Request body for creating a project."""

    name: str = Field(min_length=1)


class ProjectRename(BaseModel):
    """Request body for renaming a project."""

    name: str = Field(min_length=1)


class ProjectRead(BaseModel):
    """Project response body."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    created_at: str


class ProjectDetail(ProjectRead):
    """Project detail response body."""

    needs: list[object] = Field(default_factory=list)
