"""Router service tests."""
import pytest
from sqlalchemy.orm import Session

from app.models.model import Model
from app.models.setting import Setting
from app.services.router_service import (
    RouterNoModelError,
    RouterTaskNotRoutedError,
    is_router_enabled,
    select_model,
)


def add_model(
    db_session: Session,
    name: str,
    tier: str,
    enabled: int = 1,
    input_cost: float = 0.0,
    output_cost: float = 0.0,
) -> Model:
    """Persist one model for router assertions."""
    model = Model(
        provider="ollama",
        name=name,
        ollama_tag=name,
        tier=tier,
        enabled=enabled,
        input_cost_per_1k=input_cost,
        output_cost_per_1k=output_cost,
    )
    db_session.add(model)
    db_session.flush()
    return model


def test_router_enabled_defaults_false_and_reads_true(db_session: Session) -> None:
    """Router setting is opt-in."""
    assert is_router_enabled(db_session) is False

    db_session.add(Setting(key="router_enabled", value="true"))
    db_session.commit()

    assert is_router_enabled(db_session) is True


def test_select_model_prefers_target_tier(db_session: Session) -> None:
    """Generation tasks pick mid and inspection picks high."""
    low = add_model(db_session, "low", "low")
    mid = add_model(db_session, "mid", "mid")
    high = add_model(db_session, "high", "high")
    db_session.commit()

    assert select_model(db_session, "generate_need_to_spec").id == mid.id
    assert select_model(db_session, "generate_spec_to_child").id == mid.id
    assert select_model(db_session, "inspect_spec").id == high.id
    assert low.id < mid.id < high.id


def test_select_model_prefers_free_over_paid_at_same_tier(db_session: Session) -> None:
    """Free models outrank paid models at the same tier distance."""
    paid = add_model(db_session, "paid", "mid", input_cost=0.1, output_cost=0.1)
    free = add_model(db_session, "free", "mid")
    db_session.commit()

    assert select_model(db_session, "generate_need_to_spec").id == free.id
    assert paid.id < free.id


def test_select_model_chooses_cheapest_paid_then_lowest_id(db_session: Session) -> None:
    """Paid model ranking uses total cost, then id as a stable tie-break."""
    tied = add_model(db_session, "tie-a", "mid", input_cost=0.2, output_cost=0.2)
    add_model(db_session, "expensive", "mid", input_cost=0.5, output_cost=0.5)
    cheap = add_model(db_session, "cheap", "mid", input_cost=0.1, output_cost=0.1)
    db_session.commit()

    assert select_model(db_session, "generate_need_to_spec").id == cheap.id

    cheap.input_cost_per_1k = tied.input_cost_per_1k
    cheap.output_cost_per_1k = tied.output_cost_per_1k
    db_session.commit()

    assert select_model(db_session, "generate_need_to_spec").id == tied.id


def test_select_model_falls_back_by_tier_distance(db_session: Session) -> None:
    """When target tier is absent, router chooses the nearest enabled tier."""
    low = add_model(db_session, "low", "low")
    mid = add_model(db_session, "mid", "mid")
    db_session.commit()

    assert select_model(db_session, "inspect_spec").id == mid.id
    assert low.id < mid.id


def test_select_model_rejects_no_enabled_models_and_unrouted_task(db_session: Session) -> None:
    """Router raises clear errors for no candidates and unsupported tasks."""
    add_model(db_session, "disabled", "mid", enabled=0)
    db_session.commit()

    with pytest.raises(RouterNoModelError, match="No enabled models"):
        select_model(db_session, "generate_need_to_spec")
    with pytest.raises(RouterTaskNotRoutedError, match="Task is not routed"):
        select_model(db_session, "classify_spec")
