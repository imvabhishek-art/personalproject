import uuid
from datetime import datetime
from pydantic import BaseModel
from app.db.models.generated_content import ContentType, ContentStatus


class GenerateRequest(BaseModel):
    type: ContentType
    instructions: str = ""
    topic: str = ""
    source_filter: dict = {}


class GenerateJobResponse(BaseModel):
    job_id: str
    status: str
    credits_reserved: int


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    progress: str | None = None
    content_id: uuid.UUID | None = None
    error: str | None = None


class ContentUpdate(BaseModel):
    title: str | None = None
    subject_line: str | None = None
    body_md: str | None = None
    body_html: str | None = None
    status: ContentStatus | None = None


class ContentResponse(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    type: ContentType
    title: str
    subject_line: str | None
    body_md: str
    body_html: str
    source_content_ids: list[uuid.UUID]
    metadata_: dict
    credits_used: int
    status: ContentStatus
    created_at: datetime

    model_config = {"from_attributes": True}
