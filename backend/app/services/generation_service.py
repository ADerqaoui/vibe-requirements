"""Parent-to-Spec generation service."""
from dataclasses import dataclass
from typing import Literal

from sqlalchemy.orm import Session

from app.generation.parser import ParseError, parse_spec_candidates
from app.generation.prompts import make_spec_prompt
from app.gateway.base import Gateway, GatewayError
from app.models.model import Model
from app.models.need import Need
from app.models.spec import Spec
from app.schemas.generation import GenerationCandidate, GenerationResult
from app.services.gateway_service import GatewayRuntime, complete_model

ParentKind = Literal["need", "spec"]


@dataclass(frozen=True)
class GenerationRuntime:
    """Runtime settings for a generation call."""

    retry_count: int = 2
    timeout_seconds: float = 120.0


class GenerationParentNotFoundError(Exception):
    """Raised when a generation parent does not exist."""


async def generate_for_parent(
    db: Session,
    parent_kind: ParentKind,
    parent_id: int,
    model: Model,
    gateway: Gateway,
    count: int,
    runtime: GenerationRuntime,
) -> GenerationResult:
    """Generate stateless child spec candidates from a Need or Spec parent."""
    parent_statement = _parent_statement(db, parent_kind, parent_id)
    prompt = make_spec_prompt(parent_statement, count)
    try:
        completion = await complete_model(
            db=db,
            model=model,
            gateway=gateway,
            prompt=prompt,
            system=None,
            runtime=GatewayRuntime(
                retry_count=runtime.retry_count,
                timeout_seconds=runtime.timeout_seconds,
            ),
        )
        statements = parse_spec_candidates(completion.text, count)
    except GatewayError:
        raise
    except ParseError:
        raise
    return GenerationResult(
        candidates=[
            GenerationCandidate(index=index + 1, statement=statement)
            for index, statement in enumerate(statements)
        ]
    )


async def generate_specs_for_need(
    db: Session,
    need: Need,
    model: Model,
    gateway: Gateway,
    count: int,
    runtime: GenerationRuntime,
) -> GenerationResult:
    """Generate stateless child spec candidates from a Need."""
    return await generate_for_parent(db, "need", need.id, model, gateway, count, runtime)


def _parent_statement(db: Session, parent_kind: ParentKind, parent_id: int) -> str:
    """Return the parent statement used by the shared generation prompt."""
    if parent_kind == "need":
        need = db.get(Need, parent_id)
        if need is None:
            raise GenerationParentNotFoundError("Need not found")
        return need.statement
    spec = db.get(Spec, parent_id)
    if spec is None:
        raise GenerationParentNotFoundError("Spec not found")
    return spec.text
