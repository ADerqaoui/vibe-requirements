"""Parent-to-Spec generation service."""
from dataclasses import dataclass
from typing import Literal

from sqlalchemy.orm import Session

from app.generation.parser import ParseError, parse_spec_candidates
from app.gateway.base import Gateway, GatewayError
from app.models.model import Model
from app.models.need import Need
from app.models.spec import Spec
from app.schemas.generation import GenerationCandidate, GenerationResult
from app.services.blacklist_service import BlacklistService
from app.services.gateway_service import GatewayRuntime, complete_model
from app.services.layer_service import resolve_target_layer_for_need, resolve_target_layer_for_spec
from app.services.model_service import ModelNotFoundError, get_model
from app.services.prompt_selection import PromptSelectionContext
from app.services.prompt_service import render_prompt, select_prompt
from app.services.router_service import is_router_enabled, select_model

ParentKind = Literal["need", "spec"]


@dataclass(frozen=True)
class GenerationRuntime:
    """Runtime settings for a generation call."""

    retry_count: int = 2
    timeout_seconds: float = 120.0


class GenerationParentNotFoundError(Exception):
    """Raised when a generation parent does not exist."""


class GenerationModelUnavailableError(Exception):
    """Raised when generation cannot resolve an enabled model."""


def resolve_generation_model(db: Session, task: str, model_id: int | None) -> Model:
    """Resolve the model for generation, using router mode when enabled."""
    if is_router_enabled(db):
        return select_model(db, task)
    if model_id is None:
        raise GenerationModelUnavailableError("Model is required")
    try:
        model = get_model(db, model_id)
    except ModelNotFoundError as error:
        raise GenerationModelUnavailableError("Model not found") from error
    if not bool(model.enabled):
        raise GenerationModelUnavailableError("Model is disabled")
    return model


async def generate_for_parent(
    db: Session,
    parent_kind: ParentKind,
    parent_id: int,
    model: Model,
    gateway: Gateway,
    count: int,
    runtime: GenerationRuntime,
    target_layer_id: int | None = None,
    prompt_id: int | None = None,
    blacklist_service: BlacklistService | None = None,
) -> GenerationResult:
    """Generate stateless child spec candidates from a Need or Spec parent."""
    parent = _parent(db, parent_kind, parent_id)
    target_layer = (
        resolve_target_layer_for_need(db, target_layer_id)
        if parent_kind == "need"
        else resolve_target_layer_for_spec(db, parent.layer_id, target_layer_id)
    )
    parent_statement = parent.statement if isinstance(parent, Need) else parent.text
    task = "generate_need_to_spec" if parent_kind == "need" else "generate_spec_to_child"
    selected_prompt = select_prompt(
        db,
        task,
        layer_id=target_layer.id,
        context=PromptSelectionContext(
            prompt_id=prompt_id,
            parent_kind=parent_kind,
            parent_id=parent_id,
            layer_id=target_layer.id,
        ),
    )
    prompt = render_prompt(
        selected_prompt,
        parent_statement=parent_statement,
        count=count,
    )
    try:
        completion = await complete_model(
            db=db,
            model=model,
            gateway=gateway,
            prompt=prompt.text,
            system=None,
            runtime=GatewayRuntime(
                retry_count=runtime.retry_count,
                timeout_seconds=runtime.timeout_seconds,
            ),
            task=task,
            prompt_id=prompt.prompt_id,
            prompt_version=prompt.prompt_version,
        )
        statements = parse_spec_candidates(completion.text, count)
        if blacklist_service is not None:
            statements = await blacklist_service.filter_against_blacklist(
                parent_kind,
                parent_id,
                statements,
            )
    except GatewayError:
        raise
    except ParseError:
        raise
    return GenerationResult(
        candidates=[
            GenerationCandidate(index=index + 1, statement=statement)
            for index, statement in enumerate(statements)
        ],
        selected_model_id=model.id,
        selected_model_name=model.name,
        selected_prompt_id=prompt.prompt_id,
        selected_prompt_name=prompt.prompt_name,
    )


async def generate_specs_for_need(
    db: Session,
    need: Need,
    model: Model,
    gateway: Gateway,
    count: int,
    runtime: GenerationRuntime,
    target_layer_id: int | None = None,
    prompt_id: int | None = None,
) -> GenerationResult:
    """Generate stateless child spec candidates from a Need."""
    return await generate_for_parent(
        db,
        "need",
        need.id,
        model,
        gateway,
        count,
        runtime,
        target_layer_id=target_layer_id,
        prompt_id=prompt_id,
    )


def _parent(db: Session, parent_kind: ParentKind, parent_id: int) -> Need | Spec:
    """Return the generation parent row."""
    if parent_kind == "need":
        need = db.get(Need, parent_id)
        if need is None:
            raise GenerationParentNotFoundError("Need not found")
        return need
    spec = db.get(Spec, parent_id)
    if spec is None:
        raise GenerationParentNotFoundError("Spec not found")
    return spec
