import uuid
from datetime import datetime
from sqlalchemy import String, ForeignKey, Enum as SAEnum, DateTime, UniqueConstraint
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.db.base import Base, TimestampMixin
import enum


class MemberRole(str, enum.Enum):
    owner = "owner"
    editor = "editor"
    viewer = "viewer"


class Workspace(Base, TimestampMixin):
    __tablename__ = "workspaces"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    profile: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    members: Mapped[list["WorkspaceMember"]] = relationship(
        "WorkspaceMember", back_populates="workspace", cascade="all, delete-orphan"
    )
    content_sources: Mapped[list["ContentSource"]] = relationship(
        "ContentSource", back_populates="workspace", cascade="all, delete-orphan"
    )
    generated_content: Mapped[list["GeneratedContent"]] = relationship(
        "GeneratedContent", back_populates="workspace", cascade="all, delete-orphan"
    )
    credit_account: Mapped["CreditAccount"] = relationship(
        "CreditAccount", back_populates="workspace", cascade="all, delete-orphan", uselist=False
    )
    schedules: Mapped[list["Schedule"]] = relationship(
        "Schedule", back_populates="workspace", cascade="all, delete-orphan"
    )


class WorkspaceMember(Base):
    __tablename__ = "workspace_members"
    __table_args__ = (UniqueConstraint("workspace_id", "user_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[MemberRole] = mapped_column(SAEnum(MemberRole), nullable=False, default=MemberRole.viewer)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="members")
    user: Mapped["User"] = relationship("User", back_populates="workspace_memberships")
