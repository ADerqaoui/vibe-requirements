"""Prompt template validation tests."""
import pytest

from app.services.prompt_errors import PromptTemplateInvalidError
from app.services.prompt_validation import validate_template


def test_valid_template_passes() -> None:
    """Templates with exactly the required variables pass."""
    validate_template("generate_need_to_spec", "Need {parent_statement}\nCount {count}")


@pytest.mark.parametrize(
    ("template", "reason"),
    [
        ("Need {parent_statement}", "missing variables: count"),
        ("Need {parent_statement} {count} {extra}", "unexpected variables: extra"),
        ("Need {parent_statement", "malformed braces"),
        ("Need {}", "positional field"),
        ("Need {0}", "positional field"),
        ("Need {parent_statement!r} {count}", "conversion is not allowed"),
        ("Need {parent_statement:>10} {count}", "format spec is not allowed"),
        ("   ", "template is empty"),
    ],
)
def test_invalid_template_raises_useful_reason(template: str, reason: str) -> None:
    """Invalid templates raise typed errors with actionable reasons."""
    with pytest.raises(PromptTemplateInvalidError, match=reason):
        validate_template("generate_need_to_spec", template)
