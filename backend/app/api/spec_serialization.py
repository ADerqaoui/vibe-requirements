"""Spec API response serialization helpers."""
from app.models.spec import Spec
from app.schemas.spec import SpecOut, SpecTreeNode


def spec_out(spec: Spec, latest_inspection_id: int | None) -> SpecOut:
    """Map ORM fields to the slice API shape."""
    return SpecOut(
        id=spec.id,
        need_id=spec.need_id,
        parent_spec_id=spec.parent_spec_id,
        layer_id=spec.layer_id,
        layer_name=_layer_name(spec),
        req_id=spec.req_id,
        statement=spec.text,
        source=spec.source,
        complexity=spec.complexity,
        status=spec.status,
        latest_inspection_id=latest_inspection_id,
        created_at=spec.created_at,
        updated_at=spec.updated_at,
    )


def spec_tree(specs: list[Spec], latest_ids: dict[int, int]) -> list[SpecTreeNode]:
    """Build a recursively nested Spec tree from id-ordered rows."""
    nodes = {
        spec.id: SpecTreeNode(
            id=spec.id,
            req_id=spec.req_id,
            statement=spec.text,
            source=spec.source,
            complexity=spec.complexity,
            status=spec.status,
            parent_spec_id=spec.parent_spec_id,
            layer_id=spec.layer_id,
            layer_name=_layer_name(spec),
            latest_inspection_id=latest_ids.get(spec.id),
            children=[],
        )
        for spec in specs
    }
    roots: list[SpecTreeNode] = []
    for spec in specs:
        node = nodes[spec.id]
        if spec.parent_spec_id is None:
            roots.append(node)
            continue
        parent = nodes.get(spec.parent_spec_id)
        if parent is not None:
            parent.children.append(node)
    return roots


def _layer_name(spec: Spec) -> str:
    """Return a display layer name for serialized specs."""
    layer = getattr(spec, "layer", None)
    return layer.name if layer is not None else ""
