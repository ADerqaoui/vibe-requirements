"""Deterministic Project Markdown rendering."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.export.inspection_markdown import render_inspection_block
from app.models.model import Model
from app.models.need import Need
from app.models.project import Project
from app.models.spec import Spec
from app.models.spec_inspection import SpecInspection
from app.services.project_service import ProjectNotFoundError

TOP_SPEC_HEADING = 3
MAX_HEADING = 6


def render_project_markdown(db: Session, project_id: int, include_inspections: bool = True) -> str:
    """Render a Project tree to deterministic Markdown."""
    project = db.get(Project, project_id)
    if project is None:
        raise ProjectNotFoundError

    needs = list(db.scalars(select(Need).where(Need.project_id == project_id).order_by(Need.id)))
    need_ids = {need.id for need in needs}
    specs = list(db.scalars(select(Spec).where(Spec.need_id.in_(need_ids)).order_by(Spec.id)))
    specs_by_need = _group_specs_by_need(specs)
    specs_by_parent = _group_specs_by_parent(specs)
    inspection_context = _inspection_context(db, specs) if include_inspections else {}

    lines = [f"# {project.name}", ""]
    description = getattr(project, "description", None)
    if description:
        lines.extend([f"> {description}", ""])
    if not needs:
        lines.extend(["_No needs yet._", ""])
    for need in needs:
        lines.extend([f"## Need: {need.statement}", ""])
        top_specs = specs_by_need.get(need.id, [])
        if not top_specs:
            lines.extend(["_No specs yet._", ""])
            continue
        for spec in top_specs:
            _append_spec(lines, spec, specs_by_parent, inspection_context, TOP_SPEC_HEADING)

    total_specs = len(specs)
    classified_specs = len([spec for spec in specs if spec.complexity is not None])
    lines.extend(
        [
            "---",
            f"Needs: {len(needs)}",
            f"Specs: {total_specs}",
            f"Classified: {classified_specs} of {total_specs}",
        ]
    )
    return "\n".join(lines) + "\n"


def _append_spec(
    lines: list[str],
    spec: Spec,
    specs_by_parent: dict[int, list[Spec]],
    inspection_context: dict[int, tuple[SpecInspection, str]],
    heading_level: int,
) -> None:
    """Append one Spec and its children."""
    heading = "#" * min(heading_level, MAX_HEADING)
    req_id = spec.req_id if spec.req_id is not None else "REQ-UNASSIGNED"
    lines.extend([f"{heading} Spec: **{req_id}** — {spec.text}", ""])
    if spec.complexity is not None:
        lines.extend([f"**Complexity:** {spec.complexity}", ""])
    inspection = inspection_context.get(spec.id)
    if inspection is not None:
        lines.extend(render_inspection_block(inspection[0], inspection[1]))
    for child_spec in specs_by_parent.get(spec.id, []):
        _append_spec(lines, child_spec, specs_by_parent, inspection_context, heading_level + 1)


def _inspection_context(db: Session, specs: list[Spec]) -> dict[int, tuple[SpecInspection, str]]:
    """Return latest inspections and model names keyed by Spec id."""
    latest_rows = _latest_inspections(db, [spec.id for spec in specs])
    model_ids = {row.model_id for row in latest_rows.values()}
    models = db.scalars(select(Model).where(Model.id.in_(model_ids))).all() if model_ids else []
    model_names = {model.id: model.name for model in models}
    return {
        spec_id: (row, model_names.get(row.model_id, f"Model {row.model_id}"))
        for spec_id, row in latest_rows.items()
    }


def _latest_inspections(db: Session, spec_ids: list[int]) -> dict[int, SpecInspection]:
    """Return the latest inspection row for each Spec by created_at then id."""
    if not spec_ids:
        return {}
    rows = db.scalars(
        select(SpecInspection)
        .where(SpecInspection.spec_id.in_(spec_ids))
        .order_by(SpecInspection.spec_id, SpecInspection.created_at.desc(), SpecInspection.id.desc())
    ).all()
    latest: dict[int, SpecInspection] = {}
    for row in rows:
        latest.setdefault(row.spec_id, row)
    return latest


def _group_specs_by_need(specs: list[Spec]) -> dict[int, list[Spec]]:
    """Group root Specs by Need id."""
    grouped_specs: dict[int, list[Spec]] = {}
    for spec in specs:
        if spec.parent_spec_id is not None:
            continue
        grouped_specs.setdefault(spec.need_id, []).append(spec)
    return grouped_specs


def _group_specs_by_parent(specs: list[Spec]) -> dict[int, list[Spec]]:
    """Group child Specs by parent Spec id."""
    grouped_specs: dict[int, list[Spec]] = {}
    for spec in specs:
        if spec.parent_spec_id is None:
            continue
        grouped_specs.setdefault(spec.parent_spec_id, []).append(spec)
    return grouped_specs
