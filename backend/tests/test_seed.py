"""Reference seed tests."""
import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.prompt import Prompt
from app.seed.prompts_seed import DEFAULT_PROMPT_ROWS, GENERATE_SPEC_TO_CHILD_V2_TEMPLATE
from app.seed.reference_data import LAYER_PARENTS
from app.seed.run import seed_prompts, seed_reference_data

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

EXPECTED_GENERATE_NEED_TO_SPEC = (
    "Generate child specifications for this Need.\n"
    "Need: {parent_statement}\n"
    "Output exactly {count} concise child specifications.\n"
    "Use a numbered list. Do not include commentary, headings, or explanations."
)

EXPECTED_GENERATE_SPEC_TO_CHILD = (
    "Generate child specifications for this parent specification.\n"
    "Parent specification: {parent_statement}\n"
    "Output exactly {count} concise child specifications.\n"
    "Use a numbered list. Do not include commentary, headings, or explanations."
)

EXPECTED_CLASSIFY_SPEC = (
    "Classify the complexity of this specification from 1 to 5.\n"
    "1 = trivial, 2 = simple, 3 = moderate, 4 = complex, 5 = very complex.\n"
    "Return only one integer from 1 to 5 with no commentary.\n"
    "Specification: {spec_statement}"
)

EXPECTED_INSPECT_SPEC = (
    "Evaluate this requirement specification against the five criteria below.\n"
    "Output exactly one line per criterion in this format:\n"
    "- <Criterion>: PASS | FAIL — <short note>\n\n"
    "Criteria:\n"
    "- Clarity: PASS | FAIL — <short note>\n"
    "- Measurability: PASS | FAIL — <short note>\n"
    "- Testability: PASS | FAIL — <short note>\n"
    "- Atomicity: PASS | FAIL — <short note>\n"
    "- Ambiguity-free: PASS | FAIL — <short note>\n\n"
    "Specification:\n"
    "{spec_statement}"
)

EXPECTED_PROMPT_TEMPLATES = {
    "generate_need_to_spec": EXPECTED_GENERATE_NEED_TO_SPEC,
    "generate_spec_to_child": EXPECTED_GENERATE_SPEC_TO_CHILD,
    "classify_spec": EXPECTED_CLASSIFY_SPEC,
    "inspect_spec": EXPECTED_INSPECT_SPEC,
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


def test_seed_prompts_is_idempotent(db_session: Session) -> None:
    """Default prompts seed once and re-running does not duplicate rows."""
    seed_prompts(db_session)
    seed_prompts(db_session)

    prompts = db_session.query(Prompt).order_by(Prompt.task).all()

    assert len(prompts) == 5
    assert [(prompt.task, prompt.version) for prompt in prompts] == [
        ("classify_spec", 1),
        ("generate_need_to_spec", 1),
        ("generate_spec_to_child", 1),
        ("generate_spec_to_child", 2),
        ("inspect_spec", 1),
    ]


def test_seed_prompts_templates_are_byte_identical(db_session: Session) -> None:
    """Seeded prompt templates match the exact pre-registry prompt strings."""
    seed_prompts(db_session)

    active_prompts_by_task = {
        prompt.task: prompt
        for prompt in db_session.query(Prompt).filter(Prompt.enabled == 1).order_by(Prompt.task).all()
    }
    spec_to_child_history = db_session.query(Prompt).filter_by(
        task="generate_spec_to_child",
        version=1,
    ).one()

    assert {
        task: prompt.template
        for task, prompt in active_prompts_by_task.items()
    } == EXPECTED_PROMPT_TEMPLATES
    assert (
        active_prompts_by_task["generate_need_to_spec"].template
        != active_prompts_by_task["generate_spec_to_child"].template
    )
    assert (
        active_prompts_by_task["generate_spec_to_child"].template
        == GENERATE_SPEC_TO_CHILD_V2_TEMPLATE
    )
    assert "Parent specification" in active_prompts_by_task["generate_spec_to_child"].template
    assert (
        active_prompts_by_task["generate_need_to_spec"].template
        == spec_to_child_history.template
    )


def test_seed_prompts_preserves_existing_task_versions(db_session: Session) -> None:
    """Prompt seed matches by task and version without overwriting existing rows."""
    first_task = DEFAULT_PROMPT_ROWS[0]["task"]
    db_session.add_all([
        Prompt(task=first_task, name="Manual v1", version=1, enabled=0, template="edited"),
        Prompt(task=first_task, name="Manual v2", version=2, enabled=1, template="higher"),
    ])
    db_session.commit()

    seed_prompts(db_session)
    seed_prompts(db_session)

    prompts = db_session.query(Prompt).filter(Prompt.task == first_task).order_by(Prompt.version).all()
    assert len(db_session.query(Prompt).all()) == 6
    assert [(prompt.version, prompt.enabled, prompt.template) for prompt in prompts] == [
        (1, 0, "edited"),
        (2, 1, "higher"),
    ]


def test_seed_prompts_corrects_spec_to_child_once(db_session: Session) -> None:
    """Fresh seed creates active corrected v2 and leaves v1 history disabled."""
    seed_prompts(db_session)
    seed_prompts(db_session)

    prompts = db_session.query(Prompt).filter_by(task="generate_spec_to_child").order_by(Prompt.version).all()

    assert len(prompts) == 2
    assert [(prompt.version, prompt.enabled) for prompt in prompts] == [(1, 0), (2, 1)]
    assert prompts[1].template == GENERATE_SPEC_TO_CHILD_V2_TEMPLATE
    assert "parent specification" in prompts[1].template
    assert "Need:" not in prompts[1].template
    need_prompt = db_session.query(Prompt).filter_by(task="generate_need_to_spec", enabled=1).one()
    assert need_prompt.version == 1
    assert need_prompt.template == EXPECTED_GENERATE_NEED_TO_SPEC


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
