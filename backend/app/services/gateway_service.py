"""Gateway orchestration and call logging."""
from dataclasses import dataclass
from time import monotonic

from sqlalchemy.orm import Session

from app.gateway.base import Gateway, GatewayError
from app.gateway.resilience import complete_with_retries
from app.models.call_log import CallLog
from app.models.model import Model
from app.models.setting import Setting
from app.schemas.completion import CompletionResult
from app.services.cost import compute_cost_sek
from app.services.cost_service import enforce_cost_ceiling

MANUAL_TASK = "manual"
DEFAULT_FX_RATE = 0.0
FX_RATE_KEY = "fx_rate_usd_sek"


def register_call_log_reference_tables() -> None:
    """Import models referenced by CallLog foreign keys before ORM flush."""
    from app.models.layer import Layer
    from app.models.need import Need
    from app.models.project import Project
    from app.models.prompt import Prompt
    from app.models.spec import Spec

    for model_class in (Layer, Need, Project, Prompt, Spec):
        model_class.__table__


@dataclass(frozen=True)
class GatewayRuntime:
    """Runtime retry and timeout settings for one call."""

    retry_count: int = 2
    timeout_seconds: float = 120.0


async def complete_model(
    db: Session,
    model: Model,
    gateway: Gateway,
    prompt: str,
    system: str | None,
    runtime: GatewayRuntime,
) -> CompletionResult:
    """Run a manual gateway call and write a call log for success or failure."""
    started_at = monotonic()
    rendered_prompt = _render_prompt(prompt, system)
    fx_rate = _current_fx_rate(db)
    enforce_cost_ceiling(db, model)
    try:
        gateway_result = await complete_with_retries(
            gateway=gateway,
            prompt=prompt,
            system=system,
            retry_count=runtime.retry_count,
            timeout_seconds=runtime.timeout_seconds,
        )
    except GatewayError:
        _write_call_log(
            db=db,
            model=model,
            rendered_prompt=rendered_prompt,
            fx_rate=fx_rate,
            duration_ms=_duration_ms(started_at),
            status="failure",
            in_tokens=0,
            out_tokens=0,
            cost_sek=0.0,
        )
        raise

    cost_sek = compute_cost_sek(
        in_tokens=gateway_result.in_tokens,
        out_tokens=gateway_result.out_tokens,
        input_rate_usd=model.input_cost_per_1k,
        output_rate_usd=model.output_cost_per_1k,
        fx_rate=fx_rate,
        provider=model.provider,
    )
    duration_ms = _duration_ms(started_at)
    _write_call_log(
        db=db,
        model=model,
        rendered_prompt=rendered_prompt,
        fx_rate=fx_rate,
        duration_ms=duration_ms,
        status="success",
        in_tokens=gateway_result.in_tokens,
        out_tokens=gateway_result.out_tokens,
        cost_sek=cost_sek,
    )
    return CompletionResult(
        text=gateway_result.text,
        in_tokens=gateway_result.in_tokens,
        out_tokens=gateway_result.out_tokens,
        cost_sek=cost_sek,
        duration_ms=duration_ms,
    )


def _current_fx_rate(db: Session) -> float:
    """Read the current USD to SEK rate from DB settings."""
    setting = db.get(Setting, FX_RATE_KEY)
    if setting is None or setting.value is None:
        return DEFAULT_FX_RATE
    try:
        return float(setting.value)
    except ValueError:
        return DEFAULT_FX_RATE


def _duration_ms(started_at: float) -> int:
    """Return elapsed milliseconds."""
    return max(0, round((monotonic() - started_at) * 1000))


def _render_prompt(prompt: str, system: str | None) -> str:
    """Record exactly what the manual path sent."""
    if system is None:
        return prompt
    return f"System:\n{system}\n\nUser:\n{prompt}"


def _write_call_log(
    db: Session,
    model: Model,
    rendered_prompt: str,
    fx_rate: float,
    duration_ms: int,
    status: str,
    in_tokens: int,
    out_tokens: int,
    cost_sek: float,
) -> None:
    """Persist one call log row."""
    register_call_log_reference_tables()
    db.add(
        CallLog(
            task=MANUAL_TASK,
            provider=model.provider,
            model_id=model.id,
            in_tokens=in_tokens,
            out_tokens=out_tokens,
            cost_sek=cost_sek,
            fx_rate=fx_rate,
            duration_ms=duration_ms,
            status=status,
            rendered_prompt=rendered_prompt,
        )
    )
    db.commit()
