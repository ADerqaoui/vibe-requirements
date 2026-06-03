"""DB-backed prompt lookup and rendering."""
from dataclasses import dataclass

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.prompt import Prompt
from app.services.prompt_errors import PromptNotFoundError, PromptVariableMissingError


@dataclass(frozen=True)
class RenderedPrompt:
    """Rendered prompt text plus audit metadata."""

    text: str
    prompt_id: int
    prompt_version: int


def get_active(db: Session, task: str) -> Prompt:
    """Return the highest enabled prompt version for one task."""
    prompt = db.scalar(
        select(Prompt)
        .where(Prompt.task == task, Prompt.enabled == 1)
        .order_by(desc(Prompt.version), desc(Prompt.id))
        .limit(1)
    )
    if prompt is None:
        raise PromptNotFoundError(task)
    return prompt


def render(db: Session, task: str, **variables: object) -> RenderedPrompt:
    """Render the active task prompt with Python str.format."""
    prompt = get_active(db, task)
    try:
        text = prompt.template.format(**variables)
    except KeyError as error:
        raise PromptVariableMissingError(str(error.args[0])) from error
    return RenderedPrompt(text=text, prompt_id=prompt.id, prompt_version=prompt.version)


def list_active(db: Session) -> list[Prompt]:
    """Return one active prompt per task in stable task order."""
    prompts = db.scalars(
        select(Prompt)
        .where(Prompt.enabled == 1)
        .order_by(Prompt.task, desc(Prompt.version), desc(Prompt.id))
    ).all()
    active_by_task: dict[str, Prompt] = {}
    for prompt in prompts:
        active_by_task.setdefault(prompt.task, prompt)
    return list(active_by_task.values())
