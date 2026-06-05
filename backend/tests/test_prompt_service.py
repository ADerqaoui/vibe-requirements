"""Prompt service tests."""
import pytest
from sqlalchemy.orm import Session

from app.models.prompt import Prompt
from sqlalchemy import select

from app.services.prompt_errors import (
    PromptDisabledError,
    PromptNotFoundError,
    PromptRenderError,
    PromptTemplateInvalidError,
    PromptVariableMissingError,
)
from app.services.prompt_selection import PromptSelectionContext
from app.services.prompt_service import (
    _next_version,
    create_version,
    get_active,
    get_default_variant_name,
    promote,
    render,
    select_prompt,
    set_default,
)


def test_get_active_returns_highest_enabled_version(db_session: Session) -> None:
    """Active lookup chooses the highest enabled version for a task."""
    db_session.add_all([
        Prompt(task="task", name="v1", version=1, enabled=1, template="old"),
        Prompt(task="task", name="v2 disabled", version=2, enabled=0, template="disabled"),
        Prompt(task="task", name="v3", version=3, enabled=1, template="new"),
    ])
    db_session.commit()

    prompt = get_active(db_session, "task")

    assert prompt.version == 3
    assert prompt.template == "new"


def test_get_active_missing_task_raises(db_session: Session) -> None:
    """Missing prompt tasks raise a typed service error."""
    with pytest.raises(PromptNotFoundError):
        get_active(db_session, "missing")


def test_render_substitutes_and_returns_metadata(db_session: Session) -> None:
    """Render uses str.format and returns prompt audit metadata."""
    prompt = Prompt(task="task", name="Prompt", version=4, enabled=1, template="Hello {name}")
    db_session.add(prompt)
    db_session.commit()

    rendered = render(db_session, "task", name="Ada")

    assert rendered.text == "Hello Ada"
    assert rendered.prompt_id == prompt.id
    assert rendered.prompt_version == 4


def test_render_missing_variable_raises_variable_name(db_session: Session) -> None:
    """Missing format variables raise a typed error with the missing variable name."""
    db_session.add(Prompt(task="task", name="Prompt", version=1, enabled=1, template="{missing}"))
    db_session.commit()

    with pytest.raises(PromptVariableMissingError) as raised:
        render(db_session, "task", name="Ada")

    assert raised.value.variable_name == "missing"


def test_create_version_inserts_next_active_and_carries_metadata(db_session: Session) -> None:
    """Creating a version disables siblings and carries metadata by default."""
    db_session.add(
        Prompt(
            task="generate_need_to_spec",
            name="Generate",
            description="Original",
            version=1,
            enabled=1,
            template="{parent_statement} {count}",
        )
    )
    db_session.commit()

    created = create_version(db_session, "generate_need_to_spec", "New {parent_statement} {count}")

    versions = db_session.scalars(
        select(Prompt).where(Prompt.task == "generate_need_to_spec").order_by(Prompt.version)
    ).all()
    assert created.version == 2
    assert created.name == "Generate"
    assert created.description == "Original"
    assert [(prompt.version, prompt.enabled) for prompt in versions] == [(1, 0), (2, 1)]


def test_create_version_validates_before_writing(db_session: Session) -> None:
    """Invalid creates write no new rows."""
    db_session.add(
        Prompt(
            task="generate_need_to_spec",
            name="Generate",
            version=1,
            enabled=1,
            template="{parent_statement} {count}",
        )
    )
    db_session.commit()

    with pytest.raises(PromptTemplateInvalidError):
        create_version(db_session, "generate_need_to_spec", "Missing {parent_statement}")

    prompts = db_session.scalars(select(Prompt).where(Prompt.task == "generate_need_to_spec")).all()
    assert [(prompt.version, prompt.enabled) for prompt in prompts] == [(1, 1)]


def test_create_version_unknown_task_raises(db_session: Session) -> None:
    """Creating versions for unknown tasks is rejected."""
    with pytest.raises(PromptNotFoundError):
        create_version(db_session, "missing", "{spec_statement}")


def test_promote_flips_enabled_across_siblings(db_session: Session) -> None:
    """Promote makes exactly the selected version active."""
    older = Prompt(task="classify_spec", name="Classify", version=1, enabled=0, template="{spec_statement}")
    newer = Prompt(task="classify_spec", name="Classify", version=2, enabled=1, template="New {spec_statement}")
    db_session.add_all([older, newer])
    db_session.commit()

    promoted = promote(db_session, older.id)

    assert promoted.id == older.id
    prompts = db_session.scalars(select(Prompt).where(Prompt.task == "classify_spec").order_by(Prompt.version)).all()
    assert [(prompt.version, prompt.enabled) for prompt in prompts] == [(1, 1), (2, 0)]


def test_promote_unknown_id_raises(db_session: Session) -> None:
    """Unknown prompt ids raise a typed not-found error."""
    with pytest.raises(PromptNotFoundError):
        promote(db_session, 404)


def test_get_active_returns_enabled_row_when_higher_version_disabled(db_session: Session) -> None:
    """Rollback state returns the enabled row, not the highest version."""
    db_session.add_all([
        Prompt(task="classify_spec", name="v1", version=1, enabled=1, template="{spec_statement}"),
        Prompt(task="classify_spec", name="v2", version=2, enabled=0, template="New {spec_statement}"),
    ])
    db_session.commit()

    prompt = get_active(db_session, "classify_spec")

    assert prompt.version == 1


def test_render_value_error_raises_render_error(db_session: Session) -> None:
    """Malformed stored templates raise typed render errors."""
    db_session.add(Prompt(task="task", name="Prompt", version=1, enabled=1, template="{name"))
    db_session.commit()

    with pytest.raises(PromptRenderError):
        render(db_session, "task", name="Ada")


def test_variant_isolation_for_create_promote_and_next_version(db_session: Session) -> None:
    """Versioning and promote are scoped to one named variant."""
    concise = Prompt(task="classify_spec", name="Concise", version=1, enabled=1, template="{spec_statement}")
    ears = Prompt(task="classify_spec", name="EARS", version=1, enabled=1, template="EARS {spec_statement}")
    old_ears = Prompt(task="classify_spec", name="EARS", version=0, enabled=0, template="Old {spec_statement}")
    db_session.add_all([concise, ears, old_ears])
    db_session.commit()

    created = create_version(db_session, "classify_spec", "New EARS {spec_statement}", name="EARS")
    promoted = promote(db_session, old_ears.id)

    rows = db_session.scalars(select(Prompt).where(Prompt.task == "classify_spec").order_by(Prompt.name, Prompt.version)).all()
    assert created.version == 2
    assert promoted.id == old_ears.id
    assert _next_version(db_session, "classify_spec", None, "EARS") == 3
    assert [(row.name, row.version, row.enabled) for row in rows] == [
        ("Concise", 1, 1),
        ("EARS", 0, 1),
        ("EARS", 1, 0),
        ("EARS", 2, 0),
    ]


def test_default_variant_controls_get_active_with_fallback(db_session: Session) -> None:
    """Default settings select one variant; unset fallback is deterministic."""
    concise = Prompt(task="task", name="Concise", version=1, enabled=1, template="concise")
    ears = Prompt(task="task", name="EARS", version=2, enabled=1, template="ears")
    db_session.add_all([concise, ears])
    db_session.commit()

    assert get_default_variant_name(db_session, "task", None) == "EARS"
    assert get_active(db_session, "task").name == "EARS"

    set_default(db_session, "task", None, "Concise")

    assert get_default_variant_name(db_session, "task", None) == "Concise"
    assert get_active(db_session, "task").template == "concise"


def test_select_prompt_uses_explicit_or_default_and_rejects_bad_ids(db_session: Session) -> None:
    """Prompt selection honors explicit enabled rows and default fallback."""
    default = Prompt(task="task", name="Default", version=1, enabled=1, template="default")
    explicit = Prompt(task="task", name="Explicit", version=1, enabled=1, template="explicit")
    disabled = Prompt(task="task", name="Disabled", version=1, enabled=0, template="disabled")
    db_session.add_all([default, explicit, disabled])
    db_session.commit()
    set_default(db_session, "task", None, "Default")

    assert select_prompt(db_session, "task", None, PromptSelectionContext()).id == default.id
    assert select_prompt(db_session, "task", None, PromptSelectionContext(prompt_id=explicit.id)).id == explicit.id
    with pytest.raises(PromptNotFoundError):
        select_prompt(db_session, "task", None, PromptSelectionContext(prompt_id=404))
    with pytest.raises(PromptDisabledError):
        select_prompt(db_session, "task", None, PromptSelectionContext(prompt_id=disabled.id))
