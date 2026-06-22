import uuid
from datetime import datetime
from pydantic import BaseModel
from app.db.models.workspace import MemberRole


class WorkspaceCreate(BaseModel):
    name: str
    slug: str


class WorkspaceUpdate(BaseModel):
    name: str | None = None


class WorkspaceResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    owner_id: uuid.UUID
    profile: dict
    created_at: datetime

    model_config = {"from_attributes": True}


class OnboardingProfile(BaseModel):
    content_types: list[str] = []
    audience: str = ""
    persona: str = ""
    tone: str = "professional"
    topics: list[str] = []
    brand_name: str = ""
    writing_style: str = ""


class MemberResponse(BaseModel):
    user_id: uuid.UUID
    role: MemberRole
    joined_at: datetime
    email: str | None = None
    full_name: str | None = None

    model_config = {"from_attributes": True}


class InviteMemberRequest(BaseModel):
    email: str
    role: MemberRole = MemberRole.viewer


class UpdateMemberRoleRequest(BaseModel):
    role: MemberRole
