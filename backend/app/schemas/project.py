"""Project API schemas."""
from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProjectCreate(BaseModel):
    """Request body for creating a project."""

    name: str = Field(min_length=1)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        """Trim project names and reject blank values."""
        normalized_name = value.strip()
        if normalized_name == "":
            raise ValueError("Project name must not be blank")
        return normalized_name


class ProjectRename(BaseModel):
    """Request body for renaming a project."""

    name: str = Field(min_length=1)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        """Trim project names and reject blank values."""
        normalized_name = value.strip()
        if normalized_name == "":
            raise ValueError("Project name must not be blank")
        return normalized_name


class ProjectRead(BaseModel):
    """Project response body."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    created_at: str


class ProjectDetail(ProjectRead):
    """Project detail response body."""

    needs: list[object] = Field(default_factory=list)
