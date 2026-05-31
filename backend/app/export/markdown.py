"""Deterministic Project Markdown rendering."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.need import Need
from app.models.project import Project
from app.models.spec import Spec
from app.services.project_service import ProjectNotFoundError

TOP_SPEC_HEADING = 3
MAX_HEADING = 6


def render_project_markdown(db: Session, project_id: int) -> str:
    """Render a Project tree to deterministic Markdown."""
    project = db.get(Project, project_id)
    if project is None:
        raise ProjectNotFoundError

    needs = list(db.scalars(select(Need).where(Need.project_id == project_id).order_by(Need.id)))
    need_ids = {need.id for need in needs}
    specs = list(db.scalars(select(Spec).where(Spec.need_id.in_(need_ids)).order_by(Spec.id)))
    specs_by_need = _group_specs_by_need(specs)
    specs_by_parent = _group_specs_by_parent(specs)

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
            _append_spec(lines, spec, specs_by_parent, TOP_SPEC_HEADING)

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
    heading_level: int,
) -> None:
    """Append one Spec and its children."""
    heading = "#" * min(heading_level, MAX_HEADING)
    lines.extend([f"{heading} Spec: {spec.text}", ""])
    if spec.complexity is not None:
        lines.extend([f"**Complexity:** {spec.complexity}", ""])
    for child_spec in specs_by_parent.get(spec.id, []):
        _append_spec(lines, child_spec, specs_by_parent, heading_level + 1)


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
