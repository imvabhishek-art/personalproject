import uuid
import json
import time
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from app.agent.client import get_anthropic_client
from app.agent.tools import AGENT_TOOLS
from app.agent.prompts import build_system_prompt, build_generation_prompt, pick_model
from app.db.models.content_source import FetchedContent, SourceType
from app.db.models.generated_content import GeneratedContent, ContentType, ContentStatus
from app.db.models.workspace import Workspace
from app.services.credit import check_balance, deduct_credits
import markdown

CREDIT_COSTS = {
    ContentType.newsletter: 10,
    ContentType.blog: 8,
    ContentType.twitter_thread: 4,
    ContentType.linkedin: 3,
    ContentType.summary: 2,
}


async def _execute_tool(name: str, inputs: dict, workspace_id: uuid.UUID, db: AsyncSession) -> dict:
    if name == "fetch_recent_content":
        source_types = inputs.get("source_types")
        since_hours = inputs.get("since_hours", 168)
        limit = min(inputs.get("limit", 20), 50)

        cutoff = datetime.now(timezone.utc) - timedelta(hours=since_hours)
        query = select(FetchedContent).where(
            FetchedContent.workspace_id == workspace_id,
            FetchedContent.fetched_at >= cutoff,
        )
        if source_types:
            from app.db.models.content_source import ContentSource
            query = query.join(ContentSource).where(ContentSource.type.in_(source_types))
        query = query.order_by(FetchedContent.fetched_at.desc()).limit(limit)

        result = await db.execute(query)
        items = result.scalars().all()
        return {
            "items": [
                {"id": str(i.id), "title": i.title, "summary": i.summary, "url": i.url, "published_at": str(i.published_at)}
                for i in items
            ],
            "count": len(items),
        }

    elif name == "search_content":
        query_text = inputs.get("query", "")
        limit = min(inputs.get("limit", 10), 20)

        result = await db.execute(
            select(FetchedContent)
            .where(
                FetchedContent.workspace_id == workspace_id,
                func.lower(FetchedContent.body).contains(query_text.lower()),
            )
            .limit(limit)
        )
        items = result.scalars().all()
        return {
            "items": [
                {"id": str(i.id), "title": i.title, "summary": i.summary[:300], "url": i.url}
                for i in items
            ]
        }

    elif name == "get_content_item":
        content_id_str = inputs.get("content_id", "")
        try:
            content_id = uuid.UUID(content_id_str)
        except ValueError:
            return {"error": "Invalid content_id"}

        result = await db.execute(
            select(FetchedContent).where(
                FetchedContent.id == content_id,
                FetchedContent.workspace_id == workspace_id,
            )
        )
        item = result.scalar_one_or_none()
        if not item:
            return {"error": "Content not found"}
        return {"id": str(item.id), "title": item.title, "url": item.url, "body": item.body[:10000]}

    return {"error": f"Unknown tool: {name}"}


async def run_agent(
    workspace: Workspace,
    content_type: ContentType,
    instructions: str,
    topic: str,
    db: AsyncSession,
) -> GeneratedContent:
    cost = CREDIT_COSTS[content_type]
    await check_balance(workspace.id, cost, db)

    client = get_anthropic_client()
    system = build_system_prompt(workspace.profile)
    user_prompt = build_generation_prompt(content_type, instructions, topic)

    messages = [{"role": "user", "content": user_prompt}]
    start_time = time.time()

    for _ in range(10):
        response = await client.messages.create(
            model=pick_model(content_type),
            max_tokens=16000,
            system=system,
            tools=AGENT_TOOLS,
            thinking={"type": "adaptive"},
            messages=messages,
            betas=["prompt-caching-2024-07-31"],
        )

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            break

        if response.stop_reason == "tool_use":
            tool_results = []
            saved_content = None

            for block in response.content:
                if block.type != "tool_use":
                    continue

                if block.name == "save_draft":
                    inp = block.input
                    body_md = inp.get("body_md", "")
                    body_html = markdown.markdown(body_md, extensions=["tables", "fenced_code"])

                    source_id_strs = inp.get("source_ids", [])
                    source_ids = []
                    for s in source_id_strs:
                        try:
                            source_ids.append(uuid.UUID(s))
                        except ValueError:
                            pass

                    elapsed_ms = int((time.time() - start_time) * 1000)
                    content_obj = GeneratedContent(
                        workspace_id=workspace.id,
                        type=content_type,
                        title=inp.get("title", "Untitled"),
                        subject_line=inp.get("subject_line"),
                        body_md=body_md,
                        body_html=body_html,
                        source_content_ids=source_ids,
                        metadata_={
                            "word_count": len(body_md.split()),
                            "model_used": pick_model(content_type),
                            "generation_ms": elapsed_ms,
                        },
                        credits_used=cost,
                        status=ContentStatus.draft,
                    )
                    db.add(content_obj)
                    await db.flush()

                    await deduct_credits(
                        workspace_id=workspace.id,
                        amount=cost,
                        description=f"Generate {content_type.value}",
                        db=db,
                        generated_content_id=content_obj.id,
                    )

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": "Draft saved successfully.",
                    })
                    saved_content = content_obj
                else:
                    result = await _execute_tool(block.name, block.input, workspace.id, db)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result),
                    })

            messages.append({"role": "user", "content": tool_results})

            if saved_content:
                return saved_content

    raise RuntimeError("Agent did not produce content within iteration limit")
