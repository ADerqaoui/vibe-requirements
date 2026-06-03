"""Idempotent reference-data seed runner."""
from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models.discipline import Discipline
from app.models.layer import Layer
from app.models.layer_parent import LayerParent
from app.models.model import Model
from app.models.prompt import Prompt
from app.models.setting import Setting
from app.seed.models_seed import CORE_SETTINGS, MODEL_SEED_ROWS
from app.seed.prompts_seed import DEFAULT_PROMPT_ROWS, GENERATE_SPEC_TO_CHILD_V2_TEMPLATE
from app.seed.reference_data import DISCIPLINES, LAYER_PARENTS, LAYERS


def seed_reference_data(db: Session) -> None:
    """Seed disciplines, layers, and allowed parent rules."""
    for discipline_name in DISCIPLINES:
        discipline = db.scalar(select(Discipline).where(Discipline.name == discipline_name))
        if discipline is None:
            db.add(Discipline(name=discipline_name))

    db.flush()

    for layer_data in LAYERS:
        layer = db.scalar(select(Layer).where(Layer.name == layer_data["name"]))
        if layer is None:
            db.add(Layer(**layer_data))
            continue
        layer.kind = layer_data["kind"]
        layer.discipline = layer_data["discipline"]
        layer.sort_order = layer_data["sort_order"]

    db.flush()
    layer_ids = {layer.name: layer.id for layer in db.scalars(select(Layer)).all()}

    db.execute(delete(LayerParent))
    for child_name, parent_names in LAYER_PARENTS.items():
        for parent_name in parent_names:
            db.add(
                LayerParent(
                    layer_id=layer_ids[child_name],
                    parent_layer_id=layer_ids[parent_name],
                )
            )
    db.commit()


def seed_models_and_settings(db: Session) -> None:
    """Seed deterministic model registry rows and core settings."""
    for model_data in MODEL_SEED_ROWS:
        model = db.scalar(
            select(Model).where(
                Model.provider == model_data["provider"],
                Model.name == model_data["name"],
            )
        )
        if model is None:
            db.add(Model(**model_data))

    for key, value in CORE_SETTINGS.items():
        setting = db.get(Setting, key)
        if setting is None:
            db.add(Setting(key=key, value=value))

    db.commit()


def seed_prompts(db: Session) -> None:
    """Seed missing default prompt task/version rows without overwriting edits."""
    for prompt_data in DEFAULT_PROMPT_ROWS:
        prompt = db.scalar(
            select(Prompt).where(
                Prompt.task == prompt_data["task"],
                Prompt.version == prompt_data["version"],
            )
        )
        if prompt is None:
            db.add(Prompt(**prompt_data))
    db.flush()
    _seed_generate_spec_to_child_v2(db)
    db.commit()


def _seed_generate_spec_to_child_v2(db: Session) -> None:
    """Insert the one-time corrected Spec-to-child v2 prompt."""
    existing_v2 = db.scalar(
        select(Prompt).where(Prompt.task == "generate_spec_to_child", Prompt.version == 2)
    )
    if existing_v2 is not None:
        return
    v1 = db.scalar(
        select(Prompt).where(Prompt.task == "generate_spec_to_child", Prompt.version == 1)
    )
    if v1 is None:
        return
    db.execute(update(Prompt).where(Prompt.task == "generate_spec_to_child").values(enabled=0))
    db.add(
        Prompt(
            task="generate_spec_to_child",
            name=v1.name,
            description=v1.description,
            layer_id=v1.layer_id,
            discipline_scope=v1.discipline_scope,
            version=2,
            enabled=1,
            template=GENERATE_SPEC_TO_CHILD_V2_TEMPLATE,
        )
    )


def main() -> None:
    """Run the reference-data seed."""
    with SessionLocal() as db:
        seed_reference_data(db)
        seed_models_and_settings(db)
        seed_prompts(db)


if __name__ == "__main__":
    main()
