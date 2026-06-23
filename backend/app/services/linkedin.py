"""LinkedIn content fetching via LinkedIn API (requires OAuth token per user)."""
import hashlib
from datetime import datetime, timezone
import httpx
from app.db.models.content_source import ContentSource, FetchedContent


def _hash(text: str) -> str:
    return hashlib.sha256(text.strip().lower().encode()).hexdigest()[:64]


async def fetch_linkedin(source: ContentSource) -> list[FetchedContent]:
    access_token = source.config.get("access_token", "")
    if not access_token:
        return []

    organization_urn = source.config.get("organization_urn", "")
    person_urn = source.config.get("person_urn", "")

    if organization_urn:
        url = f"https://api.linkedin.com/v2/ugcPosts?q=authors&authors=List({organization_urn})&count=20"
    elif person_urn:
        url = f"https://api.linkedin.com/v2/ugcPosts?q=authors&authors=List({person_urn})&count=20"
    else:
        return []

    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-Restli-Protocol-Version": "2.0.0",
    }

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            return []

    now = datetime.now(timezone.utc)
    items = []
    for post in data.get("elements", []):
        text_content = post.get("specificContent", {}).get("com.linkedin.ugc.ShareContent", {})
        commentary = text_content.get("shareCommentary", {}).get("text", "")
        if not commentary:
            continue

        post_id = post.get("id", "")
        items.append(
            FetchedContent(
                source_id=source.id,
                workspace_id=source.workspace_id,
                title=commentary[:80] + ("..." if len(commentary) > 80 else ""),
                url=f"https://www.linkedin.com/feed/update/{post_id}",
                body=commentary,
                summary=commentary[:300],
                external_id=post_id,
                content_hash=_hash(post_id + commentary),
                fetched_at=now,
            )
        )
    return items
