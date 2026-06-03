"""Prompt service tests."""
import pytest
from sqlalchemy.orm import Session

from app.models.prompt import Prompt
from app.services.prompt_errors import PromptNotFoundError, PromptVariableMissingError
from app.services.prompt_service import get_active, render


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
