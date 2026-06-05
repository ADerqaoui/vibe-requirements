"""Stable requirement ID assignment."""
import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.layer import Layer
from app.models.need import Need
from app.models.spec import Spec

REQ_ID_WIDTH = 4
REQ_ID_PATTERN = re.compile(r"^REQ-[A-Z]+-(\d{4})$")

LAYER_ABBREVIATIONS = {
    "System Requirement": "SYS",
    "System Architecture": "SYSA",
    "SW Requirement": "SWR",
    "SW Architecture": "SWA",
    "SW Component/Unit": "SWC",
    "Electronic Requirement": "ELR",
    "Electronic Architecture": "ELA",
    "Electronic Component": "ELC",
    "Mechanical Requirement": "MER",
    "Mechanical Architecture": "MEA",
    "Mechanical Component": "MEC",
}


def next_req_id(db: Session, project_id: int, layer: Layer) -> str:
    """Return the next stable requirement ID for one project/layer."""
    sequence = _max_sequence(db, project_id, layer.id) + 1
    return format_req_id(layer.name, sequence)


def format_req_id(layer_name: str, sequence: int) -> str:
    """Format one requirement ID from a layer name and sequence."""
    abbreviation = LAYER_ABBREVIATIONS[layer_name]
    return f"REQ-{abbreviation}-{sequence:0{REQ_ID_WIDTH}d}"


def backfill_missing_req_ids(db: Session) -> int:
    """Assign missing IDs in deterministic project/layer/spec order."""
    rows = db.execute(
        select(Spec, Need.project_id, Layer.name)
        .join(Need, Need.id == Spec.need_id)
        .join(Layer, Layer.id == Spec.layer_id)
        .order_by(Need.project_id, Spec.layer_id, Spec.id)
    ).all()
    counters = _existing_sequences(rows)
    assigned_count = 0
    for spec, project_id, layer_name in rows:
        if spec.req_id is not None:
            continue
        key = (project_id, spec.layer_id)
        counters[key] = counters.get(key, 0) + 1
        spec.req_id = format_req_id(layer_name, counters[key])
        assigned_count += 1
    if assigned_count > 0:
        db.commit()
    return assigned_count


def _max_sequence(db: Session, project_id: int, layer_id: int) -> int:
    req_ids = db.scalars(
        select(Spec.req_id)
        .join(Need, Need.id == Spec.need_id)
        .where(Need.project_id == project_id, Spec.layer_id == layer_id, Spec.req_id.is_not(None))
    ).all()
    return max((_sequence(req_id) for req_id in req_ids), default=0)


def _existing_sequences(rows: list[tuple[Spec, int, str]]) -> dict[tuple[int, int], int]:
    counters: dict[tuple[int, int], int] = {}
    for spec, project_id, _layer_name in rows:
        if spec.req_id is None:
            continue
        key = (project_id, spec.layer_id)
        counters[key] = max(counters.get(key, 0), _sequence(spec.req_id))
    return counters


def _sequence(req_id: str | None) -> int:
    if req_id is None:
        return 0
    match = REQ_ID_PATTERN.match(req_id)
    return int(match.group(1)) if match is not None else 0
