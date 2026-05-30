"""Idempotent reference-data seed runner."""
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models.discipline import Discipline
from app.models.layer import Layer
from app.models.layer_parent import LayerParent
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


def main() -> None:
    """Run the reference-data seed."""
    with SessionLocal() as db:
        seed_reference_data(db)


if __name__ == "__main__":
    main()
