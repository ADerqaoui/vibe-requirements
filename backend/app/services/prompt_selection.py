"""Prompt selection data structures."""
from dataclasses import dataclass


@dataclass(frozen=True)
class PromptSelectionContext:
    """Context threaded to the prompt-selection chokepoint.

    Only prompt_id is used in this slice. Parent and layer context are carried
    so a later router can choose prompts without changing service signatures.
    """

    prompt_id: int | None = None
    parent_kind: str | None = None
    parent_id: int | None = None
    layer_id: int | None = None
