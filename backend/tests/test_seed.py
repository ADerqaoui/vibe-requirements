"""Reference seed tests."""
from sqlalchemy import text
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
