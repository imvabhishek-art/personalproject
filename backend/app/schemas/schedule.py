import uuid
from datetime import datetime
from pydantic import BaseModel
from app.db.models.schedule import ScheduleStatus


class ScheduleCreate(BaseModel):
    generated_content_id: uuid.UUID | None = None
    send_at: datetime | None = None
    cron_expression: str | None = None
    recipient_list: dict


class ScheduleUpdate(BaseModel):
    send_at: datetime | None = None
    cron_expression: str | None = None
    recipient_list: dict | None = None
    is_active: bool | None = None


class ScheduleResponse(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    generated_content_id: uuid.UUID | None
    send_at: datetime | None
    cron_expression: str | None
    recipient_list: dict
    is_active: bool
    last_sent_at: datetime | None
    status: ScheduleStatus
    created_at: datetime

    model_config = {"from_attributes": True}
