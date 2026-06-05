"""Project Markdown export API."""
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.export.markdown import render_project_markdown
from app.export.slug import slugify
from app.services.project_service import ProjectNotFoundError, get_project

router = APIRouter(prefix="/projects", tags=["export"])


@router.get("/{project_id}/export.md")
async def export_project_markdown_route(
    project_id: int,
    inline: bool = False,
    include_inspections: bool = True,
    db: Session = Depends(get_db),
) -> Response:
    """Export one Project tree as Markdown."""
    try:
        project = get_project(db, project_id)
        markdown = render_project_markdown(db, project_id, include_inspections=include_inspections)
    except ProjectNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found") from error

    headers = {}
    if not inline:
        headers["Content-Disposition"] = f'attachment; filename="{slugify(project.name)}.md"'
    return Response(
        content=markdown,
        media_type="text/markdown; charset=utf-8",
        headers=headers,
    )
