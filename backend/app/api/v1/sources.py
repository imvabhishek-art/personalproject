import uuid
import hashlib
from datetime import datetime, timezone
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.db.session import get_db
from app.db.models.content_source import ContentSource, FetchedContent, SourceType
from app.db.models.workspace import Workspace, WorkspaceMember, MemberRole
from app.dependencies import get_workspace, require_role
from app.schemas.source import SourceCreate, SourceUpdate, SourceResponse, FetchedContentResponse

router = APIRouter(prefix="/workspaces", tags=["sources"])


def _hash(text: str) -> str:
    return hashlib.sha256(text.strip().lower().encode()).hexdigest()[:64]


async def _sync_source(source_id: uuid.UUID) -> None:
    from app.db.session import AsyncSessionLocal
    from app.services.rss import fetch_rss
    from app.services.scraper import fetch_url
    from app.services.twitter import fetch_twitter
    from app.services.linkedin import fetch_linkedin

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(ContentSource).where(ContentSource.id == source_id))
        source = result.scalar_one_or_none()
        if not source:
            return

        fetcher_map = {
            SourceType.rss: fetch_rss,
            SourceType.scrape: fetch_url,
            SourceType.twitter: fetch_twitter,
            SourceType.linkedin: fetch_linkedin,
        }
        fetcher = fetcher_map.get(source.type)
        if not fetcher:
            return

        try:
            items = await fetcher(source)
            for item in items:
                existing = await db.execute(
                    select(FetchedContent).where(
                        and_(
                            FetchedContent.workspace_id == source.workspace_id,
                            FetchedContent.content_hash == item.content_hash,
                        )
                    )
                )
                if not existing.scalar_one_or_none():
                    db.add(item)

            source.last_synced_at = datetime.now(timezone.utc)
            await db.commit()
        except Exception:
            await db.rollback()


@router.get("/{workspace_id}/sources", response_model=list[SourceResponse])
async def list_sources(
    workspace: Annotated[Workspace, Depends(get_workspace)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(ContentSource)
        .where(ContentSource.workspace_id == workspace.id)
        .order_by(ContentSource.created_at.desc())
    )
    return result.scalars().all()


@router.post("/{workspace_id}/sources", response_model=SourceResponse, status_code=201)
async def create_source(
    body: SourceCreate,
    workspace: Annotated[Workspace, Depends(get_workspace)],
    member: Annotated[WorkspaceMember, Depends(require_role(MemberRole.owner, MemberRole.editor))],
    db: Annotated[AsyncSession, Depends(get_db)],
    background_tasks: BackgroundTasks,
):
    source = ContentSource(
        workspace_id=workspace.id,
        type=body.type,
        name=body.name,
        config=body.config,
        fetch_interval_minutes=body.fetch_interval_minutes,
    )
    db.add(source)
    await db.flush()
    background_tasks.add_task(_sync_source, source.id)
    return source


@router.get("/{workspace_id}/sources/{source_id}", response_model=SourceResponse)
async def get_source(
    source_id: uuid.UUID,
    workspace: Annotated[Workspace, Depends(get_workspace)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(ContentSource).where(
            ContentSource.id == source_id, ContentSource.workspace_id == workspace.id
        )
    )
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(404, "Source not found")
    return source


@router.patch("/{workspace_id}/sources/{source_id}", response_model=SourceResponse)
async def update_source(
    source_id: uuid.UUID,
    body: SourceUpdate,
    workspace: Annotated[Workspace, Depends(get_workspace)],
    member: Annotated[WorkspaceMember, Depends(require_role(MemberRole.owner, MemberRole.editor))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(ContentSource).where(
            ContentSource.id == source_id, ContentSource.workspace_id == workspace.id
        )
    )
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(404, "Source not found")

    for field, val in body.model_dump(exclude_none=True).items():
        setattr(source, field, val)
    return source


@router.delete("/{workspace_id}/sources/{source_id}", status_code=204)
async def delete_source(
    source_id: uuid.UUID,
    workspace: Annotated[Workspace, Depends(get_workspace)],
    member: Annotated[WorkspaceMember, Depends(require_role(MemberRole.owner))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(ContentSource).where(
            ContentSource.id == source_id, ContentSource.workspace_id == workspace.id
        )
    )
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(404, "Source not found")
    await db.delete(source)


@router.post("/{workspace_id}/sources/{source_id}/fetch", status_code=202)
async def trigger_fetch(
    source_id: uuid.UUID,
    workspace: Annotated[Workspace, Depends(get_workspace)],
    member: Annotated[WorkspaceMember, Depends(require_role(MemberRole.owner, MemberRole.editor))],
    db: Annotated[AsyncSession, Depends(get_db)],
    background_tasks: BackgroundTasks,
):
    result = await db.execute(
        select(ContentSource).where(
            ContentSource.id == source_id, ContentSource.workspace_id == workspace.id
        )
    )
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(404, "Source not found")
    background_tasks.add_task(_sync_source, source.id)
    return {"status": "fetch_queued", "source_id": str(source_id)}


@router.post("/{workspace_id}/sources/{source_id}/manual", response_model=FetchedContentResponse, status_code=201)
async def add_manual_content(
    source_id: uuid.UUID,
    body: dict,
    workspace: Annotated[Workspace, Depends(get_workspace)],
    member: Annotated[WorkspaceMember, Depends(require_role(MemberRole.owner, MemberRole.editor))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(ContentSource).where(
            ContentSource.id == source_id,
            ContentSource.workspace_id == workspace.id,
            ContentSource.type == SourceType.manual,
        )
    )
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(404, "Manual source not found")

    text = body.get("text", "")
    title = body.get("title", text[:80])
    if not text:
        raise HTTPException(400, "text is required")

    item = FetchedContent(
        source_id=source.id,
        workspace_id=workspace.id,
        title=title,
        body=text,
        summary=text[:500],
        content_hash=_hash(text),
        fetched_at=datetime.now(timezone.utc),
    )
    db.add(item)
    await db.flush()
    return item


@router.get("/{workspace_id}/fetched-content", response_model=list[FetchedContentResponse])
async def list_fetched_content(
    workspace: Annotated[Workspace, Depends(get_workspace)],
    db: Annotated[AsyncSession, Depends(get_db)],
    source_id: uuid.UUID | None = None,
    limit: int = 50,
    offset: int = 0,
):
    query = select(FetchedContent).where(FetchedContent.workspace_id == workspace.id)
    if source_id:
        query = query.where(FetchedContent.source_id == source_id)
    query = query.order_by(FetchedContent.fetched_at.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    return result.scalars().all()
