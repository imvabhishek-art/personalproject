import uuid
import json
from arq import ArqRedis

from app.db.session import AsyncSessionLocal
from app.db.models.workspace import Workspace
from app.db.models.generated_content import ContentType
from app.agent.orchestrator import run_agent


async def generate_content_task(
    ctx: dict,
    workspace_id: str,
    content_type: str,
    instructions: str,
    topic: str,
    job_key: str,
) -> dict:
    redis: ArqRedis = ctx["redis"]

    async def update_status(status: str, progress: str = "", content_id: str = "", error: str = ""):
        await redis.set(
            job_key,
            json.dumps({
                "status": status,
                "progress": progress,
                "content_id": content_id,
                "error": error,
            }),
            ex=3600,
        )

    await update_status("running", "Starting content generation...")

    try:
        async with AsyncSessionLocal() as db:
            ws_id = uuid.UUID(workspace_id)
            result = await db.execute(
                __import__("sqlalchemy").select(Workspace).where(Workspace.id == ws_id)
            )
            workspace = result.scalar_one_or_none()
            if not workspace:
                await update_status("failed", error="Workspace not found")
                return {"status": "failed"}

            await update_status("running", "Claude is researching and writing...")

            content = await run_agent(
                workspace=workspace,
                content_type=ContentType(content_type),
                instructions=instructions,
                topic=topic,
                db=db,
            )
            await db.commit()

        await update_status("complete", content_id=str(content.id))
        return {"status": "complete", "content_id": str(content.id)}

    except Exception as e:
        await update_status("failed", error=str(e))
        return {"status": "failed", "error": str(e)}
