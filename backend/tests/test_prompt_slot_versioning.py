"""Prompt per-slot versioning tests."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.layer import Layer
from app.models.prompt import Prompt
from app.services.prompt_service import create_version, get_active, list_active, list_versions, promote


def add_layer(db_session: Session, name: str, sort_order: int) -> Layer:
    """Persist a test layer."""
    layer = Layer(name=name, kind="cross_cutting", sort_order=sort_order)
    db_session.add(layer)
    db_session.flush()
    return layer


def enabled_rows(db_session: Session, task: str) -> list[tuple[int, int | None, int]]:
    """Return version/layer/enabled rows for assertions."""
    return list(
        db_session.execute(
            select(Prompt.version, Prompt.layer_id, Prompt.enabled)
            .where(Prompt.task == task)
            .order_by(Prompt.layer_id.is_not(None), Prompt.layer_id, Prompt.version)
        ).all()
    )


def test_layer_slot_creation_and_promote_do_not_disable_global_or_other_slots(
    db_session: Session,
) -> None:
    """Layer variants version independently from the global slot."""
    layer_x = add_layer(db_session, "Layer X", 10)
    layer_y = add_layer(db_session, "Layer Y", 20)
    global_prompt = Prompt(
        task="classify_spec",
        name="Classify",
        version=1,
        enabled=1,
        template="Global {spec_statement}",
    )
    other_slot = Prompt(
        task="classify_spec",
        name="Other",
        layer_id=layer_y.id,
        version=1,
        enabled=1,
        template="Other {spec_statement}",
    )
    db_session.add_all([global_prompt, other_slot])
    db_session.commit()

    layer_v1 = create_version(db_session, "classify_spec", "Layer v1 {spec_statement}", layer_id=layer_x.id)

    assert layer_v1.version == 1
    assert get_active(db_session, "classify_spec", layer_id=layer_x.id).template.startswith("Layer v1")
    assert get_active(db_session, "classify_spec", layer_id=layer_y.id).template.startswith("Other")
    assert get_active(db_session, "classify_spec").template.startswith("Global")
    assert enabled_rows(db_session, "classify_spec") == [
        (1, None, 1),
        (1, layer_x.id, 1),
        (1, layer_y.id, 1),
    ]

    layer_v2 = create_version(db_session, "classify_spec", "Layer v2 {spec_statement}", layer_id=layer_x.id)

    assert layer_v2.version == 2
    assert enabled_rows(db_session, "classify_spec") == [
        (1, None, 1),
        (1, layer_x.id, 0),
        (2, layer_x.id, 1),
        (1, layer_y.id, 1),
    ]

    promote(db_session, layer_v1.id)

    assert enabled_rows(db_session, "classify_spec") == [
        (1, None, 1),
        (1, layer_x.id, 1),
        (2, layer_x.id, 0),
        (1, layer_y.id, 1),
    ]


def test_existing_layer_slot_carries_metadata_from_slot(db_session: Session) -> None:
    """Editing an existing layer slot preserves that slot's metadata."""
    layer = add_layer(db_session, "Layer X", 10)
    db_session.add(
        Prompt(
            task="classify_spec",
            name="Global",
            description="Global description",
            version=1,
            enabled=1,
            template="Global {spec_statement}",
        )
    )
    db_session.commit()
    create_version(
        db_session,
        "classify_spec",
        "Layer v1 {spec_statement}",
        layer_id=layer.id,
        name="X-specific",
        description="X description",
    )

    created = create_version(db_session, "classify_spec", "Layer v2 {spec_statement}", layer_id=layer.id)

    assert created.name == "X-specific"
    assert created.description == "X description"


def test_new_layer_slot_seeds_metadata_from_global(db_session: Session) -> None:
    """Creating a brand-new layer slot defaults metadata from the global slot."""
    layer = add_layer(db_session, "Layer Y", 20)
    db_session.add(
        Prompt(
            task="classify_spec",
            name="Global",
            description="Global description",
            version=1,
            enabled=1,
            template="Global {spec_statement}",
        )
    )
    db_session.commit()

    created = create_version(db_session, "classify_spec", "Layer y {spec_statement}", layer_id=layer.id)

    assert created.name == "Global"
    assert created.description == "Global description"


def test_list_active_returns_one_enabled_row_per_slot_in_layer_order(db_session: Session) -> None:
    """Active prompt listing includes global first, then layer slots."""
    later_layer = add_layer(db_session, "Later", 20)
    earlier_layer = add_layer(db_session, "Earlier", 10)
    db_session.add_all([
        Prompt(task="task_a", name="global", version=1, enabled=1, template="global"),
        Prompt(task="task_a", name="later", layer_id=later_layer.id, version=1, enabled=1, template="later"),
        Prompt(task="task_a", name="old", layer_id=earlier_layer.id, version=1, enabled=0, template="old"),
        Prompt(task="task_a", name="earlier", layer_id=earlier_layer.id, version=2, enabled=1, template="earlier"),
        Prompt(task="task_b", name="global b", version=1, enabled=1, template="global b"),
    ])
    db_session.commit()

    prompts = list_active(db_session)

    assert [(prompt.task, prompt.layer_id, prompt.template) for prompt in prompts] == [
        ("task_a", None, "global"),
        ("task_a", earlier_layer.id, "earlier"),
        ("task_a", later_layer.id, "later"),
        ("task_b", None, "global b"),
    ]


def test_list_versions_returns_all_slots_ordered_by_layer_then_version(db_session: Session) -> None:
    """Version history spans every slot and keeps slot grouping stable."""
    layer = add_layer(db_session, "Layer", 10)
    db_session.add_all([
        Prompt(task="task", name="global v1", version=1, enabled=0, template="global v1"),
        Prompt(task="task", name="global v2", version=2, enabled=1, template="global v2"),
        Prompt(task="task", name="layer v1", layer_id=layer.id, version=1, enabled=0, template="layer v1"),
        Prompt(task="task", name="layer v2", layer_id=layer.id, version=2, enabled=1, template="layer v2"),
    ])
    db_session.commit()

    prompts = list_versions(db_session, "task")

    assert [(prompt.layer_id, prompt.version, prompt.enabled) for prompt in prompts] == [
        (None, 2, 1),
        (None, 1, 0),
        (layer.id, 2, 1),
        (layer.id, 1, 0),
    ]
