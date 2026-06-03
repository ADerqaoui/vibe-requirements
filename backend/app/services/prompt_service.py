"""DB-backed prompt lookup and rendering."""
from dataclasses import dataclass

from sqlalchemy import desc, func, select, update
from sqlalchemy.orm import Session

from app.models.prompt import Prompt
from app.services.prompt_errors import (
    PromptNotFoundError,
    PromptRenderError,
    PromptVariableMissingError,
)
from app.services.prompt_validation import validate_template


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
    except (ValueError, IndexError) as error:
        raise PromptRenderError(str(error)) from error
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


def list_versions(db: Session, task: str) -> list[Prompt]:
    """Return all prompt versions for one task, newest first."""
    prompts = list(
        db.scalars(
            select(Prompt)
            .where(Prompt.task == task)
            .order_by(desc(Prompt.version), desc(Prompt.id))
        ).all()
    )
    if not prompts:
        raise PromptNotFoundError(task)
    return prompts


def create_version(
    db: Session,
    task: str,
    template: str,
    name: str | None = None,
    description: str | None = None,
) -> Prompt:
    """Insert a new active immutable version for an existing task."""
    current = get_active(db, task)
    validate_template(task, template)
    next_version = _next_version(db, task)
    prompt = Prompt(
        task=task,
        name=name if name is not None else current.name,
        description=description if description is not None else current.description,
        layer_id=current.layer_id,
        discipline_scope=current.discipline_scope,
        version=next_version,
        enabled=1,
        template=template,
    )
    try:
        db.execute(update(Prompt).where(Prompt.task == task).values(enabled=0))
        db.add(prompt)
        db.commit()
        db.refresh(prompt)
    except Exception:
        db.rollback()
        raise
    return prompt


def promote(db: Session, prompt_id: int) -> Prompt:
    """Promote a historical prompt version and disable its siblings."""
    prompt = db.get(Prompt, prompt_id)
    if prompt is None:
        raise PromptNotFoundError(str(prompt_id))
    try:
        db.execute(update(Prompt).where(Prompt.task == prompt.task).values(enabled=0))
        prompt.enabled = 1
        db.commit()
        db.refresh(prompt)
    except Exception:
        db.rollback()
        raise
    return prompt


def _next_version(db: Session, task: str) -> int:
    """Return one more than the current maximum version for a task."""
    max_version = db.scalar(select(func.max(Prompt.version)).where(Prompt.task == task))
    return int(max_version or 0) + 1
