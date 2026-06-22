import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.db.models.schedule import Schedule, ScheduleStatus
from app.db.models.generated_content import GeneratedContent
from app.db.models.workspace import Workspace, WorkspaceMember, MemberRole
from app.dependencies import get_workspace, require_role
from app.schemas.schedule import ScheduleCreate, ScheduleUpdate, ScheduleResponse

router = APIRouter(prefix="/workspaces", tags=["schedules"])


@router.get("/{workspace_id}/schedules", response_model=list[ScheduleResponse])
async def list_schedules(
    workspace: Annotated[Workspace, Depends(get_workspace)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(Schedule)
        .where(Schedule.workspace_id == workspace.id)
        .order_by(Schedule.send_at.asc())
    )
    return result.scalars().all()


@router.post("/{workspace_id}/schedules", response_model=ScheduleResponse, status_code=201)
async def create_schedule(
    body: ScheduleCreate,
    workspace: Annotated[Workspace, Depends(get_workspace)],
    member: Annotated[WorkspaceMember, Depends(require_role(MemberRole.owner, MemberRole.editor))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if body.generated_content_id:
        content_result = await db.execute(
            select(GeneratedContent).where(
                GeneratedContent.id == body.generated_content_id,
                GeneratedContent.workspace_id == workspace.id,
            )
        )
        if not content_result.scalar_one_or_none():
            raise HTTPException(404, "Content not found")

    schedule = Schedule(
        workspace_id=workspace.id,
        generated_content_id=body.generated_content_id,
        send_at=body.send_at,
        cron_expression=body.cron_expression,
        recipient_list=body.recipient_list,
    )
    db.add(schedule)
    await db.flush()
    return schedule


@router.patch("/{workspace_id}/schedules/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(
    schedule_id: uuid.UUID,
    body: ScheduleUpdate,
    workspace: Annotated[Workspace, Depends(get_workspace)],
    member: Annotated[WorkspaceMember, Depends(require_role(MemberRole.owner, MemberRole.editor))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(Schedule).where(Schedule.id == schedule_id, Schedule.workspace_id == workspace.id)
    )
    schedule = result.scalar_one_or_none()
    if not schedule:
        raise HTTPException(404, "Schedule not found")

    for field, val in body.model_dump(exclude_none=True).items():
        setattr(schedule, field, val)
    return schedule


@router.delete("/{workspace_id}/schedules/{schedule_id}", status_code=204)
async def delete_schedule(
    schedule_id: uuid.UUID,
    workspace: Annotated[Workspace, Depends(get_workspace)],
    member: Annotated[WorkspaceMember, Depends(require_role(MemberRole.owner))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(Schedule).where(Schedule.id == schedule_id, Schedule.workspace_id == workspace.id)
    )
    schedule = result.scalar_one_or_none()
    if not schedule:
        raise HTTPException(404, "Schedule not found")
    await db.delete(schedule)


@router.post("/{workspace_id}/schedules/{schedule_id}/send-now", status_code=202)
async def send_now(
    schedule_id: uuid.UUID,
    workspace: Annotated[Workspace, Depends(get_workspace)],
    member: Annotated[WorkspaceMember, Depends(require_role(MemberRole.owner, MemberRole.editor))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(Schedule).where(Schedule.id == schedule_id, Schedule.workspace_id == workspace.id)
    )
    schedule = result.scalar_one_or_none()
    if not schedule:
        raise HTTPException(404, "Schedule not found")

    content_result = await db.execute(
        select(GeneratedContent).where(GeneratedContent.id == schedule.generated_content_id)
    )
    content = content_result.scalar_one_or_none()
    if not content:
        raise HTTPException(400, "No content attached to schedule")

    from app.services.delivery import send_newsletter
    from datetime import datetime, timezone

    await send_newsletter(
        subject=content.subject_line or content.title,
        body_html=content.body_html,
        recipient_list=schedule.recipient_list,
    )
    schedule.last_sent_at = datetime.now(timezone.utc)
    schedule.status = ScheduleStatus.sent
    return {"status": "sent"}
