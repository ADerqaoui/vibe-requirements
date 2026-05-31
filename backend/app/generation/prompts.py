"""Hardcoded generation prompts for slice 06."""


def make_spec_prompt(parent_statement: str, count: int) -> str:
    """Build the default Need-to-Spec generation prompt."""
    return (
        "Generate child specifications for this Need.\n"
        f"Need: {parent_statement}\n"
        f"Output exactly {count} concise child specifications.\n"
        "Use a numbered list. Do not include commentary, headings, or explanations."
    )
