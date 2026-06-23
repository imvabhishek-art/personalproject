import uuid
from datetime import datetime
from sqlalchemy import Boolean, ForeignKey, Enum as SAEnum, Text, DateTime
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.db.base import Base, TimestampMixin
import enum


class ScheduleStatus(str, enum.Enum):
    pending = "pending"
    sent = "sent"
    failed = "failed"
    cancelled = "cancelled"


class Schedule(Base, TimestampMixin):
    __tablename__ = "schedules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    generated_content_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("generated_content.id", ondelete="SET NULL"), nullable=True
    )
    send_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cron_expression: Mapped[str | None] = mapped_column(Text, nullable=True)
    recipient_list: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[ScheduleStatus] = mapped_column(
        SAEnum(ScheduleStatus), nullable=False, default=ScheduleStatus.pending
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="schedules")
    generated_content: Mapped["GeneratedContent"] = relationship(
        "GeneratedContent", back_populates="schedules"
    )
