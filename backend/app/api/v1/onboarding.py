from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models.workspace import Workspace, WorkspaceMember, MemberRole
from app.dependencies import get_workspace, require_role
from app.schemas.workspace import OnboardingProfile, WorkspaceResponse

router = APIRouter(prefix="/workspaces", tags=["onboarding"])


@router.get("/{workspace_id}/onboarding", response_model=OnboardingProfile)
async def get_onboarding(
    workspace: Annotated[Workspace, Depends(get_workspace)],
):
    return OnboardingProfile(**workspace.profile)


@router.post("/{workspace_id}/onboarding", response_model=WorkspaceResponse)
async def save_onboarding(
    body: OnboardingProfile,
    workspace: Annotated[Workspace, Depends(get_workspace)],
    member: Annotated[WorkspaceMember, Depends(require_role(MemberRole.owner, MemberRole.editor))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    workspace.profile = body.model_dump()
    return workspace
