"""Prompt layer-aware lookup tests."""
from sqlalchemy.orm import Session

from app.models.layer import Layer
from app.models.prompt import Prompt
from app.services.prompt_service import get_active


def test_get_active_prefers_layer_specific_prompt_and_falls_back(db_session: Session) -> None:
    """Layer-aware lookup selects exact layer prompts and falls back to NULL."""
    layer_x = Layer(name="Layer X", kind="cross_cutting", sort_order=10)
    layer_y = Layer(name="Layer Y", kind="cross_cutting", sort_order=20)
    db_session.add_all([layer_x, layer_y])
    db_session.flush()
    fallback = Prompt(task="task", name="fallback", version=1, enabled=1, template="fallback")
    layer_prompt = Prompt(
        task="task",
        name="layer",
        layer_id=layer_x.id,
        version=1,
        enabled=1,
        template="layer",
    )
    db_session.add_all([fallback, layer_prompt])
    db_session.commit()

    assert get_active(db_session, "task", layer_id=layer_x.id).template == "layer"
    assert get_active(db_session, "task", layer_id=layer_y.id).template == "fallback"
    assert get_active(db_session, "task").template == "fallback"


def test_get_active_prefers_discipline_and_highest_version_tie(db_session: Session) -> None:
    """Discipline specificity and version tie-breaks are applied."""
    db_session.add_all([
        Prompt(task="task", name="fallback", version=9, enabled=1, template="fallback"),
        Prompt(
            task="task",
            name="sw v1",
            discipline_scope="SW",
            version=1,
            enabled=1,
            template="sw v1",
        ),
        Prompt(
            task="task",
            name="sw v2",
            discipline_scope="SW",
            version=2,
            enabled=1,
            template="sw v2",
        ),
    ])
    db_session.commit()

    prompt = get_active(db_session, "task", discipline_scope="SW")

    assert prompt.template == "sw v2"
