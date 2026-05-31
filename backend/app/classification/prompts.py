"""Hardcoded classification prompts for slice 07."""


def make_complexity_prompt(spec_statement: str) -> str:
    """Build the complexity classification prompt."""
    return (
        "Classify the complexity of this specification from 1 to 5.\n"
        "1 = trivial, 2 = simple, 3 = moderate, 4 = complex, 5 = very complex.\n"
        "Return only one integer from 1 to 5 with no commentary.\n"
        f"Specification: {spec_statement}"
    )
