"""Layer API schemas."""
from pydantic import BaseModel, ConfigDict


class LayerOut(BaseModel):
    """Seeded V-model layer response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    kind: str
    discipline: str | None
    sort_order: int
