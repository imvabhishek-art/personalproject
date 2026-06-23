import uuid
from datetime import datetime
from sqlalchemy import String, Integer, ForeignKey, Enum as SAEnum, Text, DateTime
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from app.db.base import Base, TimestampMixin
import enum


class ContentType(str, enum.Enum):
    newsletter = "newsletter"
    blog = "blog"
    linkedin = "linkedin"
    twitter_thread = "twitter_thread"
    summary = "summary"


class ContentStatus(str, enum.Enum):
    draft = "draft"
    published = "published"
    scheduled = "scheduled"
    archived = "archived"


class GeneratedContent(Base, TimestampMixin):
    __tablename__ = "generated_content"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    type: Mapped[ContentType] = mapped_column(SAEnum(ContentType), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False, default="")
    subject_line: Mapped[str | None] = mapped_column(Text, nullable=True)
    body_md: Mapped[str] = mapped_column(Text, nullable=False, default="")
    body_html: Mapped[str] = mapped_column(Text, nullable=False, default="")
    source_content_ids: Mapped[list[uuid.UUID]] = mapped_column(
        ARRAY(UUID(as_uuid=True)), default=list, nullable=False
    )
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict, nullable=False)
    credits_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[ContentStatus] = mapped_column(
        SAEnum(ContentStatus), nullable=False, default=ContentStatus.draft
    )

    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="generated_content")
    schedules: Mapped[list["Schedule"]] = relationship(
        "Schedule", back_populates="generated_content"
    )
