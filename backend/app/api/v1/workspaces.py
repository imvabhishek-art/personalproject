import uuid
import re
from datetime import datetime, timezone
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.db.models.user import User
from app.db.models.workspace import Workspace, WorkspaceMember, MemberRole
from app.db.models.credit import CreditAccount
from app.dependencies import get_current_user, get_workspace, require_role
from app.schemas.workspace import (
    WorkspaceCreate, WorkspaceUpdate, WorkspaceResponse,
    MemberResponse, InviteMemberRequest, UpdateMemberRoleRequest,
)

router = APIRouter(prefix="/workspaces", tags=["workspaces"])

SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,48}[a-z0-9]$")


@router.post("", response_model=WorkspaceResponse, status_code=201)
async def create_workspace(
    body: WorkspaceCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if not SLUG_RE.match(body.slug):
        raise HTTPException(400, "Slug must be 3-50 lowercase letters, numbers, or hyphens")

    existing = await db.execute(select(Workspace).where(Workspace.slug == body.slug))
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Slug already taken")

    workspace = Workspace(name=body.name, slug=body.slug, owner_id=current_user.id, profile={})
    db.add(workspace)
    await db.flush()

    member = WorkspaceMember(
        workspace_id=workspace.id,
        user_id=current_user.id,
        role=MemberRole.owner,
        joined_at=datetime.now(timezone.utc),
    )
    db.add(member)

    account = CreditAccount(workspace_id=workspace.id, balance=0)
    db.add(account)

    return workspace


@router.get("", response_model=list[WorkspaceResponse])
async def list_workspaces(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(Workspace)
        .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
        .where(WorkspaceMember.user_id == current_user.id)
    )
    return result.scalars().all()


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace_detail(
    workspace: Annotated[Workspace, Depends(get_workspace)],
):
    return workspace


@router.patch("/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace(
    body: WorkspaceUpdate,
    workspace: Annotated[Workspace, Depends(get_workspace)],
    member: Annotated[WorkspaceMember, Depends(require_role(MemberRole.owner, MemberRole.editor))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if body.name is not None:
        workspace.name = body.name
    return workspace


@router.get("/{workspace_id}/members", response_model=list[MemberResponse])
async def list_members(
    workspace: Annotated[Workspace, Depends(get_workspace)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(WorkspaceMember, User.email, User.full_name)
        .join(User, User.id == WorkspaceMember.user_id)
        .where(WorkspaceMember.workspace_id == workspace.id)
    )
    rows = result.all()
    return [
        MemberResponse(
            user_id=m.user_id,
            role=m.role,
            joined_at=m.joined_at,
            email=email,
            full_name=full_name,
        )
        for m, email, full_name in rows
    ]


@router.post("/{workspace_id}/members/invite", response_model=MemberResponse, status_code=201)
async def invite_member(
    body: InviteMemberRequest,
    workspace: Annotated[Workspace, Depends(get_workspace)],
    member: Annotated[WorkspaceMember, Depends(require_role(MemberRole.owner))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    user_result = await db.execute(select(User).where(User.email == body.email))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")

    existing = await db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace.id,
            WorkspaceMember.user_id == user.id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Already a member")

    new_member = WorkspaceMember(
        workspace_id=workspace.id,
        user_id=user.id,
        role=body.role,
        joined_at=datetime.now(timezone.utc),
    )
    db.add(new_member)
    await db.flush()
    return MemberResponse(
        user_id=new_member.user_id,
        role=new_member.role,
        joined_at=new_member.joined_at,
        email=user.email,
        full_name=user.full_name,
    )


@router.delete("/{workspace_id}/members/{user_id}", status_code=204)
async def remove_member(
    user_id: uuid.UUID,
    workspace: Annotated[Workspace, Depends(get_workspace)],
    requester: Annotated[WorkspaceMember, Depends(require_role(MemberRole.owner))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if user_id == workspace.owner_id:
        raise HTTPException(400, "Cannot remove workspace owner")

    result = await db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace.id,
            WorkspaceMember.user_id == user_id,
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(404, "Member not found")

    await db.delete(member)
