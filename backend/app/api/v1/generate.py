import uuid
import json
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis

from app.db.session import get_db
from app.db.models.workspace import Workspace, WorkspaceMember, MemberRole
from app.db.models.generated_content import ContentType
from app.dependencies import get_workspace, require_role
from app.schemas.content import GenerateRequest, GenerateJobResponse, JobStatusResponse
from app.services.credit import check_balance
from app.agent.orchestrator import CREDIT_COSTS
from app.config import get_settings

router = APIRouter(prefix="/workspaces", tags=["generate"])


def _check_anthropic_key():
    if not get_settings().anthropic_api_key:
        raise HTTPException(
            status_code=503,
            detail="AI generation is not configured yet. Add ANTHROPIC_API_KEY to enable content generation.",
        )


def get_redis():
    settings = get_settings()
    return aioredis.from_url(settings.redis_url, decode_responses=True)


@router.post("/{workspace_id}/generate", response_model=GenerateJobResponse, status_code=202)
async def enqueue_generation(
    body: GenerateRequest,
    workspace: Annotated[Workspace, Depends(get_workspace)],
    member: Annotated[WorkspaceMember, Depends(require_role(MemberRole.owner, MemberRole.editor))],
    db: Annotated[AsyncSession, Depends(get_db)],
    _settings: Annotated[None, Depends(lambda: _check_anthropic_key())],
):
    cost = CREDIT_COSTS.get(body.type, 10)
    await check_balance(workspace.id, cost, db)

    job_id = str(uuid.uuid4())
    job_key = f"gen_job:{job_id}"

    redis_client = await get_redis()
    try:
        await redis_client.set(
            job_key,
            json.dumps({"status": "queued", "progress": "Waiting for worker..."}),
            ex=3600,
        )

        from arq.connections import ArqRedis, RedisSettings
        settings = get_settings()
        arq_redis = await ArqRedis.from_url(settings.redis_url)
        await arq_redis.enqueue_job(
            "generate_content_task",
            workspace_id=str(workspace.id),
            content_type=body.type.value,
            instructions=body.instructions,
            topic=body.topic,
            job_key=job_key,
        )
        await arq_redis.aclose()
    finally:
        await redis_client.aclose()

    return GenerateJobResponse(job_id=job_id, status="queued", credits_reserved=cost)


@router.get("/{workspace_id}/generate/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str,
    workspace: Annotated[Workspace, Depends(get_workspace)],
):
    job_key = f"gen_job:{job_id}"
    redis_client = await get_redis()
    try:
        data = await redis_client.get(job_key)
    finally:
        await redis_client.aclose()

    if not data:
        raise HTTPException(404, "Job not found or expired")

    parsed = json.loads(data)
    content_id = parsed.get("content_id")
    return JobStatusResponse(
        job_id=job_id,
        status=parsed.get("status", "unknown"),
        progress=parsed.get("progress"),
        content_id=uuid.UUID(content_id) if content_id else None,
        error=parsed.get("error"),
    )
