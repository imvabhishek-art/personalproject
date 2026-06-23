import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.db.models.generated_content import GeneratedContent, ContentStatus
from app.db.models.workspace import Workspace, WorkspaceMember, MemberRole
from app.dependencies import get_workspace, require_role
from app.schemas.content import ContentResponse, ContentUpdate
import markdown

router = APIRouter(prefix="/workspaces", tags=["content"])


@router.get("/{workspace_id}/content", response_model=list[ContentResponse])
async def list_content(
    workspace: Annotated[Workspace, Depends(get_workspace)],
    db: Annotated[AsyncSession, Depends(get_db)],
    content_type: str | None = None,
    status: str | None = None,
    limit: int = 20,
    offset: int = 0,
):
    query = select(GeneratedContent).where(GeneratedContent.workspace_id == workspace.id)
    if content_type:
        query = query.where(GeneratedContent.type == content_type)
    if status:
        query = query.where(GeneratedContent.status == status)
    query = query.order_by(GeneratedContent.created_at.desc()).limit(limit).offset(offset)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{workspace_id}/content/{content_id}", response_model=ContentResponse)
async def get_content(
    content_id: uuid.UUID,
    workspace: Annotated[Workspace, Depends(get_workspace)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(GeneratedContent).where(
            GeneratedContent.id == content_id,
            GeneratedContent.workspace_id == workspace.id,
        )
    )
    content = result.scalar_one_or_none()
    if not content:
        raise HTTPException(404, "Content not found")
    return content


@router.patch("/{workspace_id}/content/{content_id}", response_model=ContentResponse)
async def update_content(
    content_id: uuid.UUID,
    body: ContentUpdate,
    workspace: Annotated[Workspace, Depends(get_workspace)],
    member: Annotated[WorkspaceMember, Depends(require_role(MemberRole.owner, MemberRole.editor))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(GeneratedContent).where(
            GeneratedContent.id == content_id,
            GeneratedContent.workspace_id == workspace.id,
        )
    )
    content = result.scalar_one_or_none()
    if not content:
        raise HTTPException(404, "Content not found")

    for field, val in body.model_dump(exclude_none=True).items():
        setattr(content, field, val)

    if body.body_md:
        content.body_html = markdown.markdown(body.body_md, extensions=["tables", "fenced_code"])

    return content


@router.delete("/{workspace_id}/content/{content_id}", status_code=204)
async def delete_content(
    content_id: uuid.UUID,
    workspace: Annotated[Workspace, Depends(get_workspace)],
    member: Annotated[WorkspaceMember, Depends(require_role(MemberRole.owner))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(GeneratedContent).where(
            GeneratedContent.id == content_id,
            GeneratedContent.workspace_id == workspace.id,
        )
    )
    content = result.scalar_one_or_none()
    if not content:
        raise HTTPException(404, "Content not found")
    await db.delete(content)
