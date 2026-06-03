"""Prompt template validation rules."""
from string import Formatter

from app.services.prompt_errors import PromptTemplateInvalidError

REQUIRED_VARIABLES_BY_TASK: dict[str, frozenset[str]] = {
    "generate_need_to_spec": frozenset({"parent_statement", "count"}),
    "generate_spec_to_child": frozenset({"parent_statement", "count"}),
    "classify_spec": frozenset({"spec_statement"}),
    "inspect_spec": frozenset({"spec_statement"}),
}


def validate_template(task: str, template: str) -> None:
    """Validate one template against the task's required variables."""
    if not template.strip():
        raise PromptTemplateInvalidError("template is empty")
    required = REQUIRED_VARIABLES_BY_TASK.get(task)
    if required is None:
        raise PromptTemplateInvalidError(f"unknown task: {task}")
    used = _parse_used_variables(template)
    missing = sorted(required - used)
    unexpected = sorted(used - required)
    if missing or unexpected:
        parts = []
        if missing:
            parts.append(f"missing variables: {', '.join(missing)}")
        if unexpected:
            parts.append(f"unexpected variables: {', '.join(unexpected)}")
        raise PromptTemplateInvalidError("; ".join(parts))


def _parse_used_variables(template: str) -> set[str]:
    """Return plain named fields, rejecting unsupported format features."""
    used: set[str] = set()
    try:
        parsed = Formatter().parse(template)
        for _literal, field_name, format_spec, conversion in parsed:
            if field_name is None:
                continue
            _validate_field(field_name, format_spec, conversion)
            used.add(field_name)
    except ValueError as error:
        raise PromptTemplateInvalidError("malformed braces") from error
    return used


def _validate_field(field_name: str, format_spec: str, conversion: str | None) -> None:
    """Reject positional fields and non-plain substitutions."""
    if field_name == "" or field_name.isdigit():
        raise PromptTemplateInvalidError(f"positional field is not allowed: {{{field_name}}}")
    if conversion is not None:
        raise PromptTemplateInvalidError(f"conversion is not allowed: {{{field_name}!{conversion}}}")
    if format_spec:
        raise PromptTemplateInvalidError(f"format spec is not allowed: {{{field_name}:{format_spec}}}")
