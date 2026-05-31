"""Inspector prompt templates."""

CRITERIA = ("Clarity", "Measurability", "Testability", "Atomicity", "Ambiguity-free")


def make_inspect_prompt(spec_statement: str) -> str:
    """Build a single-model Spec inspection prompt."""
    criteria = "\n".join(f"- {criterion}: PASS | FAIL — <short note>" for criterion in CRITERIA)
    return (
        "Evaluate this requirement specification against the five criteria below.\n"
        "Output exactly one line per criterion in this format:\n"
        "- <Criterion>: PASS | FAIL — <short note>\n\n"
        f"Criteria:\n{criteria}\n\n"
        f"Specification:\n{spec_statement}"
    )
