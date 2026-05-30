"""Idempotent reference-data seed runner."""
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models.discipline import Discipline
from app.models.layer import Layer
from app.models.layer_parent import LayerParent
from app.models.model import Model
from app.models.setting import Setting
from app.seed.models_seed import CORE_SETTINGS, MODEL_SEED_ROWS
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
            continue
        model.ollama_tag = model_data["ollama_tag"]
        model.api_model_id = model_data["api_model_id"]
        model.tier = model_data["tier"]
        model.input_cost_per_1k = model_data["input_cost_per_1k"]
        model.output_cost_per_1k = model_data["output_cost_per_1k"]
        model.enabled = model_data["enabled"]

    for key, value in CORE_SETTINGS.items():
        setting = db.get(Setting, key)
        if setting is None:
            db.add(Setting(key=key, value=value))

    db.commit()


def main() -> None:
    """Run the reference-data seed."""
    with SessionLocal() as db:
        seed_reference_data(db)
        seed_models_and_settings(db)


if __name__ == "__main__":
    main()
