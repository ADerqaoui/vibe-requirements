"""Spec complexity classification service."""
import asyncio
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.classification.parser import VoteParseError, parse_complexity_vote
from app.classification.prompts import make_complexity_prompt
from app.config import Settings
from app.gateway.base import Gateway
from app.models.model import Model
from app.models.spec import Spec
from app.schemas.classification import ClassificationResult, ClassificationVote
from app.services.gateway_service import GatewayRuntime, complete_model

CLASSIFICATION_TAGS = ("qwen2.5:7b", "llama3.1:8b", "gemma2:9b")


class ClassificationModelError(Exception):
    """Raised when required classification models are not enabled."""


class ClassificationParseError(Exception):
    """Raised when a classification response cannot be parsed."""


@dataclass(frozen=True)
class ClassificationRuntime:
    """Runtime settings for classification calls."""

    retry_count: int = 2
    timeout_seconds: float = 120.0


GatewayFactory = Callable[[Model, Settings], Gateway]


async def classify_spec_complexity(
    db: Session,
    spec: Spec,
    gateway_factory: GatewayFactory,
    settings: Settings,
    runtime: ClassificationRuntime,
) -> ClassificationResult:
    """Classify Spec complexity through three required local model votes."""
    models = _required_models(db)
    prompt = make_complexity_prompt(spec.text)
    try:
        votes = await asyncio.gather(
            *[
                _classify_with_model(db, model, gateway_factory, settings, runtime, prompt)
                for model in models
            ]
        )
    except VoteParseError as error:
        raise ClassificationParseError(str(error)) from error
    complexity = _median_vote([vote.vote for vote in votes])
    spec.complexity = complexity
    spec.updated_at = datetime.now(UTC).isoformat()
    db.commit()
    return ClassificationResult(spec_id=spec.id, votes=votes, complexity=complexity)


def _required_models(db: Session) -> list[Model]:
    """Return enabled required models or raise before gateway calls."""
    models = list(
        db.scalars(
            select(Model).where(
                Model.provider == "ollama",
                Model.ollama_tag.in_(CLASSIFICATION_TAGS),
                Model.enabled == 1,
            )
        ).all()
    )
    models_by_tag = {model.ollama_tag: model for model in models}
    missing_tags = [tag for tag in CLASSIFICATION_TAGS if tag not in models_by_tag]
    if missing_tags:
        raise ClassificationModelError(
            f"Required classification model missing or disabled: {', '.join(missing_tags)}"
        )
    return [models_by_tag[tag] for tag in CLASSIFICATION_TAGS]


async def _classify_with_model(
    db: Session,
    model: Model,
    gateway_factory: GatewayFactory,
    settings: Settings,
    runtime: ClassificationRuntime,
    prompt: str,
) -> ClassificationVote:
    """Call one model through the gateway service and parse its vote."""
    gateway = gateway_factory(model, settings)
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
    return ClassificationVote(model_id=model.id, vote=parse_complexity_vote(completion.text))


def _median_vote(votes: list[int]) -> int:
    """Return the middle vote from exactly three votes."""
    return sorted(votes)[1]
