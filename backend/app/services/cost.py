"""Pure cost computation helpers."""


def compute_cost_sek(
    in_tokens: int,
    out_tokens: int,
    input_rate_usd: float,
    output_rate_usd: float,
    fx_rate: float,
    provider: str,
) -> float:
    """Compute frozen SEK cost for one model call."""
    if provider == "ollama":
        return 0.0
    if in_tokens < 0 or out_tokens < 0:
        raise ValueError("Token counts must not be negative")
    if input_rate_usd < 0 or output_rate_usd < 0 or fx_rate < 0:
        raise ValueError("Rates must not be negative")
    return ((in_tokens * input_rate_usd) + (out_tokens * output_rate_usd)) / 1000 * fx_rate
