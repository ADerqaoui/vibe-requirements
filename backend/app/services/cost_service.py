"""Cost ceiling and summary service."""
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.gateway.base import CostCeilingExceededError
from app.models.call_log import CallLog
from app.models.model import Model
from app.models.setting import Setting
from app.schemas.cost import CostModelSummary, CostProviderSummary, CostSummary

COST_CEILING_KEY = "cost_ceiling_sek"
CURRENCY = "SEK"
SUCCESS_STATUS = "success"
DEFAULT_CEILING_SEK = 50.0


def enforce_cost_ceiling(db: Session, model: Model) -> None:
    """Block paid calls once current-month spend reaches the configured ceiling."""
    if model.input_cost_per_1k <= 0 and model.output_cost_per_1k <= 0:
        return
    spent_sek = current_month_spend_sek(db)
    ceiling_sek = cost_ceiling_sek(db)
    if spent_sek >= ceiling_sek:
        raise CostCeilingExceededError(spent_sek=spent_sek, ceiling_sek=ceiling_sek)


def cost_summary(db: Session) -> CostSummary:
    """Return monthly and all-time successful paid spend summaries."""
    ceiling_sek = cost_ceiling_sek(db)
    month_spent_sek = current_month_spend_sek(db)
    all_time_spent_sek = _sum_cost(db, ())
    return CostSummary(
        currency=CURRENCY,
        ceiling_sek=ceiling_sek,
        month_spent_sek=month_spent_sek,
        month_remaining_sek=max(0.0, ceiling_sek - month_spent_sek),
        all_time_spent_sek=all_time_spent_sek,
        by_provider=_provider_summaries(db),
        by_model=_model_summaries(db),
    )


def current_month_spend_sek(db: Session) -> float:
    """Return successful spend since the UTC month boundary."""
    return _sum_cost(db, (_current_month_condition(),))


def cost_ceiling_sek(db: Session) -> float:
    """Return configured monthly ceiling in SEK."""
    setting = db.get(Setting, COST_CEILING_KEY)
    if setting is None or setting.value is None:
        return DEFAULT_CEILING_SEK
    try:
        return float(setting.value)
    except ValueError:
        return DEFAULT_CEILING_SEK


def start_of_month_utc() -> str:
    """Return the current UTC calendar month boundary."""
    now = datetime.now(UTC)
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()


def _sum_cost(db: Session, conditions: tuple[object, ...]) -> float:
    statement = select(func.coalesce(func.sum(CallLog.cost_sek), 0.0)).where(
        CallLog.status == SUCCESS_STATUS,
        *conditions,
    )
    return float(db.scalar(statement) or 0.0)


def _current_month_condition() -> object:
    return func.datetime(CallLog.created_at) >= func.datetime(start_of_month_utc())


def _provider_summaries(db: Session) -> list[CostProviderSummary]:
    rows = db.execute(
        select(CallLog.provider, func.coalesce(func.sum(CallLog.cost_sek), 0.0))
        .join(Model, Model.id == CallLog.model_id)
        .where(
            CallLog.status == SUCCESS_STATUS,
            _current_month_condition(),
            (Model.input_cost_per_1k > 0) | (Model.output_cost_per_1k > 0),
        )
        .group_by(CallLog.provider)
        .order_by(CallLog.provider)
    ).all()
    return [CostProviderSummary(provider=provider, month_sek=float(total)) for provider, total in rows]


def _model_summaries(db: Session) -> list[CostModelSummary]:
    rows = db.execute(
        select(Model.id, Model.name, func.coalesce(func.sum(CallLog.cost_sek), 0.0))
        .join(CallLog, CallLog.model_id == Model.id)
        .where(
            CallLog.status == SUCCESS_STATUS,
            _current_month_condition(),
            (Model.input_cost_per_1k > 0) | (Model.output_cost_per_1k > 0),
        )
        .group_by(Model.id, Model.name)
        .order_by(Model.id)
    ).all()
    return [
        CostModelSummary(model_id=model_id, model_name=name, month_sek=float(total))
        for model_id, name, total in rows
    ]
