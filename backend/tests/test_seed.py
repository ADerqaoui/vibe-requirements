"""Reference seed tests."""
import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.seed.reference_data import LAYER_PARENTS
from app.seed.run import seed_reference_data

BASE_TABLES = {
    "disciplines",
    "layers",
    "layer_parents",
    "projects",
    "needs",
    "specs",
    "spec_disciplines",
    "diagrams",
    "blacklist_entries",
    "classification_votes",
    "spec_revisions",
    "inspection_findings",
    "models",
    "prompts",
    "call_logs",
    "settings",
}


def test_seed_reference_data_is_idempotent(db_session: Session) -> None:
    """Seed twice and verify expected reference counts."""
    seed_reference_data(db_session)
    seed_reference_data(db_session)

    discipline_count = db_session.scalar(text("SELECT COUNT(*) FROM disciplines"))
    layer_count = db_session.scalar(text("SELECT COUNT(*) FROM layers"))
    parent_count = db_session.scalar(text("SELECT COUNT(*) FROM layer_parents"))

    assert discipline_count == 3
    assert layer_count == 12
    assert parent_count == sum(len(parent_names) for parent_names in LAYER_PARENTS.values())


def test_seed_reference_data_has_exact_layer_parent_rules(db_session: Session) -> None:
    """Seeded layer-parent pairs match the configured V-model rules exactly."""
    seed_reference_data(db_session)

    rows = db_session.execute(
        text(
            """
            SELECT child.name, parent.name
            FROM layer_parents
            JOIN layers AS child ON child.id = layer_parents.layer_id
            JOIN layers AS parent ON parent.id = layer_parents.parent_layer_id
            """
        )
    ).all()
    actual_pairs = {(child_name, parent_name) for child_name, parent_name in rows}
    expected_pairs = {
        (child_name, parent_name)
        for child_name, parent_names in LAYER_PARENTS.items()
        for parent_name in parent_names
    }

    assert actual_pairs == expected_pairs


def test_blacklist_entry_requires_exactly_one_parent(db_session: Session) -> None:
    """The migrated blacklist_entries CHECK requires one need or spec parent."""
    seed_reference_data(db_session)
    layer_id = db_session.scalar(
        text("SELECT id FROM layers WHERE name = 'System Requirement'")
    )
    project_id = db_session.scalar(
        text("INSERT INTO projects (name) VALUES ('Project') RETURNING id")
    )
    need_id = db_session.scalar(
        text(
            """
            INSERT INTO needs (project_id, statement)
            VALUES (:project_id, 'Need')
            RETURNING id
            """
        ),
        {"project_id": project_id},
    )
    spec_id = db_session.scalar(
        text(
            """
            INSERT INTO specs (need_id, layer_id, text)
            VALUES (:need_id, :layer_id, 'Spec')
            RETURNING id
            """
        ),
        {"need_id": need_id, "layer_id": layer_id},
    )
    db_session.commit()

    with pytest.raises(IntegrityError):
        db_session.execute(
            text("INSERT INTO blacklist_entries (text, source) VALUES ('Bad', 'rejected')")
        )
        db_session.commit()
    db_session.rollback()

    with pytest.raises(IntegrityError):
        db_session.execute(
            text(
                """
                INSERT INTO blacklist_entries (parent_need_id, parent_spec_id, text, source)
                VALUES (:need_id, :spec_id, 'Bad', 'rejected')
                """
            ),
            {"need_id": need_id, "spec_id": spec_id},
        )
        db_session.commit()
    db_session.rollback()

    db_session.execute(
        text(
            """
            INSERT INTO blacklist_entries (parent_need_id, text, source)
            VALUES (:need_id, 'Need parent', 'rejected')
            """
        ),
        {"need_id": need_id},
    )
    db_session.execute(
        text(
            """
            INSERT INTO blacklist_entries (parent_spec_id, text, source)
            VALUES (:spec_id, 'Spec parent', 'edited_out')
            """
        ),
        {"spec_id": spec_id},
    )
    db_session.commit()

    blacklist_count = db_session.scalar(text("SELECT COUNT(*) FROM blacklist_entries"))
    assert blacklist_count == 2


def test_migration_creates_strict_tables_and_blacklist_vec(db_session: Session) -> None:
    """Verify strict base tables and vec virtual table exist."""
    tables = db_session.execute(
        text(
            """
            SELECT name, strict
            FROM pragma_table_list
            WHERE type IN ('table', 'virtual')
              AND name NOT LIKE 'sqlite_%'
            """
        )
    ).all()
    table_strictness = {name: strict for name, strict in tables}

    assert table_strictness["blacklist_vec"] == 0
    assert BASE_TABLES.issubset(table_strictness)
    for table_name in BASE_TABLES:
        assert table_strictness[table_name] == 1, table_name

    foreign_keys_enabled = db_session.scalar(text("PRAGMA foreign_keys"))
    assert foreign_keys_enabled == 1
