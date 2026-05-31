"""Spec lifecycle decision schemas."""
from typing import Literal

from pydantic import BaseModel


DecisionValue = Literal["accepted", "rejected"]


class DecisionRequest(BaseModel):
    """Request body for deciding a Spec lifecycle status."""

    decision: DecisionValue
