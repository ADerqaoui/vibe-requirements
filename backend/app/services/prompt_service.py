"""DB-backed prompt lookup and rendering."""
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.prompt import Prompt
from app.services.prompt_errors import (
    PromptDisabledError,
    PromptLayerMismatchError,
    PromptNotFoundError,
    PromptRenderError,
    PromptVariableMissingError,
)
from app.services.prompt_selection import PromptSelectionContext
from app.services.prompt_variant_store import (
    _active_in_slot,
    _best_group_prompt,
    _next_version,
    _slot_filter,
    _specificity_score,
    create_version,
    get_default_variant_name,
    list_active,
    list_variants,
    list_versions,
    promote,
    set_default,
)


@dataclass(frozen=True)
class RenderedPrompt:
    """Rendered prompt text plus audit metadata."""

    text: str
    prompt_id: int
    prompt_version: int
    prompt_name: str


def get_active(
    db: Session,
    task: str,
    layer_id: int | None = None,
    discipline_scope: str | None = None,
) -> Prompt:
    """Return the default variant in the most-specific enabled group."""
    group_row = _best_group_prompt(db, task, layer_id, discipline_scope)
    default_name = get_default_variant_name(db, task, group_row.layer_id)
    row = (
        _active_in_slot(db, task, group_row.layer_id, default_name, group_row.discipline_scope)
        if default_name is not None
        else None
    )
    if row is None and group_row.discipline_scope is not None:
        row = group_row
    if row is None:
        raise PromptNotFoundError(task)
    return row


def select_prompt(
    db: Session,
    task: str,
    layer_id: int | None,
    context: PromptSelectionContext,
) -> Prompt:
    """Select a prompt through the prompt-selection chokepoint."""
    if context.prompt_id is None:
        return get_active(db, task, layer_id=layer_id)
    row = db.get(Prompt, context.prompt_id)
    if row is None or row.task != task:
        raise PromptNotFoundError(str(context.prompt_id))
    active_row = _active_in_slot(db, row.task, row.layer_id, row.name, row.discipline_scope)
    if not bool(row.enabled) or active_row is None or active_row.id != row.id:
        raise PromptDisabledError(str(context.prompt_id))
    if row.layer_id is not None and row.layer_id != layer_id:
        raise PromptLayerMismatchError("prompt does not belong to the target layer")
    return row


def render(
    db: Session,
    task: str,
    layer_id: int | None = None,
    discipline_scope: str | None = None,
    **variables: object,
) -> RenderedPrompt:
    """Render the active task prompt with Python str.format."""
    row = get_active(db, task, layer_id=layer_id, discipline_scope=discipline_scope)
    return render_prompt(row, **variables)


def render_prompt(prompt: Prompt, **variables: object) -> RenderedPrompt:
    """Render a selected prompt row with Python str.format."""
    try:
        text = prompt.template.format(**variables)
    except KeyError as error:
        raise PromptVariableMissingError(str(error.args[0])) from error
    except (ValueError, IndexError) as error:
        raise PromptRenderError(str(error)) from error
    return RenderedPrompt(
        text=text,
        prompt_id=prompt.id,
        prompt_version=prompt.version,
        prompt_name=prompt.name,
    )
