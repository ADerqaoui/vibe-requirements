"""Cost computation tests."""
import pytest

from app.services.cost import compute_cost_sek


def test_local_provider_cost_is_zero() -> None:
    """Ollama calls are local and cost zero."""
    assert compute_cost_sek(1000, 1000, 99, 99, 11, "ollama") == 0


def test_cloud_provider_cost_uses_formula() -> None:
    """Cloud provider cost uses explicit rates and FX."""
    cost = compute_cost_sek(
        in_tokens=500,
        out_tokens=250,
        input_rate_usd=2,
        output_rate_usd=4,
        fx_rate=10,
        provider="openai",
    )

    assert cost == 20


def test_cost_is_never_negative_for_valid_inputs() -> None:
    """Valid non-negative input combinations never produce negative cost."""
    cases = (
        (0, 0, 0, 0, 0, "openai"),
        (1, 0, 0.1, 0, 10, "anthropic"),
        (0, 1, 0, 0.2, 10, "deepseek"),
        (100000, 250000, 0.03, 0.06, 11.2, "openai"),
    )

    for case in cases:
        assert compute_cost_sek(*case) >= 0


def test_negative_inputs_are_rejected() -> None:
    """Negative rates and token counts are invalid."""
    with pytest.raises(ValueError):
        compute_cost_sek(-1, 0, 0, 0, 1, "openai")
    with pytest.raises(ValueError):
        compute_cost_sek(0, 0, -1, 0, 1, "openai")
    with pytest.raises(ValueError):
        compute_cost_sek(0, 0, 0, 0, -1, "openai")


def test_cost_is_frozen_by_caller_rates() -> None:
    """Changing later rates does not alter a previously computed value."""
    frozen_cost = compute_cost_sek(1000, 1000, 1, 2, 10, "openai")
    later_cost = compute_cost_sek(1000, 1000, 3, 4, 10, "openai")

    assert frozen_cost == 30
    assert later_cost == 70
    assert frozen_cost != later_cost
