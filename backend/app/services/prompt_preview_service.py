"""Prompt draft preview orchestration."""
from collections.abc import Callable
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.config import Settings
from app.gateway.base import Gateway
from app.models.model import Model
from app.models.prompt import Prompt
from app.schemas.completion import CompletionResult
from app.services.gateway_service import GatewayRuntime, complete_model
from app.services.model_service import ModelNotFoundError, get_model
from app.services.prompt_errors import PromptVariableMissingError
from app.services.prompt_service import render_prompt
from app.services.prompt_validation import REQUIRED_VARIABLES_BY_TASK, validate_template
from app.services.router_service import select_model

PREVIEW_TASK = "preview"
GatewayFactory = Callable[[Model, Settings], Gateway]


class PromptPreviewModelError(Exception):
    """Raised when preview cannot resolve an enabled model."""


@dataclass(frozen=True)
class PromptPreviewResult:
    """Rendered draft prompt and model completion metadata."""

    rendered_prompt: str
    output: str
    model_id: int
    model_name: str
    cost_sek: float


async def preview_prompt(
    db: Session,
    task: str,
    template: str,
    variables: dict[str, object],
    model_id: int | None,
    gateway_factory: GatewayFactory,
    settings: Settings,
) -> PromptPreviewResult:
    """Validate, render, and run a draft prompt without structural persistence."""
    validate_template(task, template)
    _require_values(task, variables)
    prompt = _draft_prompt(task, template)
    rendered = render_prompt(prompt, **variables)
    model = _resolve_model(db, task, model_id)
    completion = await _complete_preview(
        db=db,
        model=model,
        gateway=gateway_factory(model, settings),
        rendered_prompt=rendered.text,
        runtime=_runtime_for_provider(model.provider, settings),
    )
    return PromptPreviewResult(
        rendered_prompt=rendered.text,
        output=completion.text,
        model_id=model.id,
        model_name=model.name,
        cost_sek=completion.cost_sek,
    )


def _require_values(task: str, variables: dict[str, object]) -> None:
    required = REQUIRED_VARIABLES_BY_TASK.get(task, frozenset())
    for variable_name in sorted(required):
        value = variables.get(variable_name)
        if value is None or str(value).strip() == "":
            raise PromptVariableMissingError(variable_name)


def _draft_prompt(task: str, template: str) -> Prompt:
    return Prompt(
        id=0,
        task=task,
        name="Draft preview",
        version=0,
        template=template,
        enabled=1,
    )


def _resolve_model(db: Session, task: str, model_id: int | None) -> Model:
    if model_id is None:
        return select_model(db, task)
    try:
        model = get_model(db, model_id)
    except ModelNotFoundError as error:
        raise PromptPreviewModelError("Model not found") from error
    if not bool(model.enabled):
        raise PromptPreviewModelError("Model is disabled")
    return model


async def _complete_preview(
    db: Session,
    model: Model,
    gateway: Gateway,
    rendered_prompt: str,
    runtime: GatewayRuntime,
) -> CompletionResult:
    return await complete_model(
        db=db,
        model=model,
        gateway=gateway,
        prompt=rendered_prompt,
        system=None,
        runtime=runtime,
        task=PREVIEW_TASK,
    )


def _runtime_for_provider(provider: str, settings: Settings) -> GatewayRuntime:
    timeout = settings.ollama_timeout_seconds if provider == "ollama" else settings.cloud_timeout_seconds
    return GatewayRuntime(retry_count=settings.llm_retry_count, timeout_seconds=timeout)
