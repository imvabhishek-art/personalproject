import uuid
from datetime import datetime
from pydantic import BaseModel
from app.db.models.content_source import SourceType


class SourceCreate(BaseModel):
    type: SourceType
    name: str
    config: dict
    fetch_interval_minutes: int = 60


class SourceUpdate(BaseModel):
    name: str | None = None
    config: dict | None = None
    is_active: bool | None = None
    fetch_interval_minutes: int | None = None


class SourceResponse(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    type: SourceType
    name: str
    config: dict
    is_active: bool
    fetch_interval_minutes: int
    last_synced_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class FetchedContentResponse(BaseModel):
    id: uuid.UUID
    source_id: uuid.UUID
    title: str
    url: str | None
    summary: str
    published_at: datetime | None
    fetched_at: datetime

    model_config = {"from_attributes": True}
