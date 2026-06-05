"""Variant-scoped prompt storage helpers."""
from sqlalchemy import and_, desc, func, or_, select, update
from sqlalchemy.orm import Session

from app.models.prompt import Prompt
from app.services.prompt_defaults import default_key, read_prompt_defaults, write_prompt_defaults
from app.services.prompt_errors import PromptNotFoundError
from app.services.prompt_store_queries import group_filter, ordered_enabled, ordered_task_versions
from app.services.prompt_validation import validate_template


def list_active(db: Session) -> list[Prompt]:
    """Return the default active prompt per task/layer group."""
    rows = db.scalars(ordered_enabled()).all()
    active_by_group: dict[tuple[str, int | None], Prompt] = {}
    for row in rows:
        active_by_group.setdefault((row.task, row.layer_id), _default_in_group(db, row.task, row.layer_id))
    return list(active_by_group.values())


def list_versions(db: Session, task: str) -> list[Prompt]:
    """Return all prompt versions for one task, grouped by layer and variant."""
    rows = list(db.scalars(ordered_task_versions(task)).all())
    if not rows:
        raise PromptNotFoundError(task)
    return rows


def list_variants(db: Session, task: str, layer_id: int | None) -> list[Prompt]:
    """Return enabled variants for one exact task/layer group."""
    rows = db.scalars(
        select(Prompt)
        .where(group_filter(task, layer_id), Prompt.enabled == 1)
        .order_by(Prompt.name, desc(Prompt.version), desc(Prompt.id))
    ).all()
    variants: dict[str, Prompt] = {}
    for row in rows:
        variants.setdefault(row.name, row)
    return list(variants.values())


def create_version(
    db: Session,
    task: str,
    template: str,
    layer_id: int | None = None,
    name: str | None = None,
    description: str | None = None,
) -> Prompt:
    """Insert a new active immutable version for a task/layer/name variant."""
    source = _version_source(db, task, layer_id, name)
    variant_name = name if name is not None else source.name
    validate_template(task, template)
    row = Prompt(
        task=task,
        name=variant_name,
        description=description if description is not None else source.description,
        layer_id=layer_id,
        discipline_scope=None,
        version=_next_version(db, task, layer_id, variant_name),
        enabled=1,
        template=template,
    )
    try:
        db.execute(update(Prompt).where(_slot_filter(task, layer_id, variant_name)).values(enabled=0))
        db.add(row)
        db.commit()
        db.refresh(row)
    except Exception:
        db.rollback()
        raise
    return row


def promote(db: Session, prompt_id: int) -> Prompt:
    """Promote a historical prompt version and disable its variant siblings."""
    row = db.get(Prompt, prompt_id)
    if row is None:
        raise PromptNotFoundError(str(prompt_id))
    try:
        db.execute(update(Prompt).where(_slot_filter(row.task, row.layer_id, row.name)).values(enabled=0))
        row.enabled = 1
        db.commit()
        db.refresh(row)
    except Exception:
        db.rollback()
        raise
    return row


def get_default_variant_name(db: Session, task: str, layer_id: int | None) -> str | None:
    """Return the configured or deterministic fallback default variant name."""
    configured = read_prompt_defaults(db).get(default_key(task, layer_id))
    if configured is not None and _active_in_slot(db, task, layer_id, configured) is not None:
        return configured
    fallback = _active_in_group(db, task, layer_id)
    return fallback.name if fallback is not None else None


def set_default(db: Session, task: str, layer_id: int | None, name: str) -> str:
    """Persist one default variant for a task/layer group."""
    if _active_in_slot(db, task, layer_id, name) is None:
        raise PromptNotFoundError(name)
    defaults = read_prompt_defaults(db)
    defaults[default_key(task, layer_id)] = name
    write_prompt_defaults(db, defaults)
    db.commit()
    return name


def _default_in_group(db: Session, task: str, layer_id: int | None) -> Prompt:
    name = get_default_variant_name(db, task, layer_id)
    row = _active_in_slot(db, task, layer_id, name) if name is not None else None
    if row is None:
        raise PromptNotFoundError(task)
    return row


def _version_source(db: Session, task: str, layer_id: int | None, name: str | None) -> Prompt:
    if name is not None:
        active = _active_in_slot(db, task, layer_id, name)
        if active is not None:
            return active
    active_group = _active_in_group(db, task, layer_id)
    if active_group is not None:
        return active_group
    global_active = _active_in_group(db, task, None)
    if global_active is None:
        raise PromptNotFoundError(task)
    return global_active

def _best_group_prompt(db: Session, task: str, layer_id: int | None, discipline_scope: str | None) -> Prompt:
    rows = db.scalars(
        select(Prompt).where(
            Prompt.task == task,
            Prompt.enabled == 1,
            or_(Prompt.layer_id == layer_id, Prompt.layer_id.is_(None)),
            or_(Prompt.discipline_scope == discipline_scope, Prompt.discipline_scope.is_(None)),
        )
    ).all()
    row = max(
        rows,
        key=lambda item: (_specificity_score(item, layer_id, discipline_scope), item.version, item.id),
        default=None,
    )
    if row is None:
        raise PromptNotFoundError(task)
    return row


def _next_version(db: Session, task: str, layer_id: int | None, name: str) -> int:
    max_version = db.scalar(select(func.max(Prompt.version)).where(_slot_filter(task, layer_id, name)))
    return int(max_version or 0) + 1


def _active_in_slot(
    db: Session,
    task: str,
    layer_id: int | None,
    name: str,
    discipline_scope: str | None = None,
) -> Prompt | None:
    predicate = _slot_filter(task, layer_id, name)
    if discipline_scope is not None:
        predicate = and_(predicate, Prompt.discipline_scope == discipline_scope)
    return db.scalar(
        select(Prompt)
        .where(predicate, Prompt.enabled == 1)
        .order_by(desc(Prompt.version), desc(Prompt.id))
        .limit(1)
    )


def _active_in_group(db: Session, task: str, layer_id: int | None) -> Prompt | None:
    return db.scalar(
        select(Prompt)
        .where(group_filter(task, layer_id), Prompt.enabled == 1)
        .order_by(desc(Prompt.version), desc(Prompt.id))
        .limit(1)
    )


def _slot_filter(task: str, layer_id: int | None, name: str):
    """Return the task/layer/name variant predicate."""
    return and_(group_filter(task, layer_id), Prompt.name == name)


def _specificity_score(prompt: Prompt, layer_id: int | None, discipline_scope: str | None) -> int:
    layer_score = 2 if prompt.layer_id is not None and prompt.layer_id == layer_id else 0
    discipline_match = prompt.discipline_scope is not None and prompt.discipline_scope == discipline_scope
    return layer_score + (1 if discipline_match else 0)
