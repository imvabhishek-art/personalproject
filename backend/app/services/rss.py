import hashlib
from datetime import datetime, timezone
import httpx
import feedparser
from app.db.models.content_source import ContentSource, FetchedContent


def _hash(text: str) -> str:
    return hashlib.sha256(text.strip().lower().encode()).hexdigest()[:64]


def _parse_date(entry) -> datetime | None:
    for attr in ("published_parsed", "updated_parsed"):
        val = getattr(entry, attr, None)
        if val:
            import time
            return datetime.fromtimestamp(time.mktime(val), tz=timezone.utc)
    return None


async def fetch_rss(source: ContentSource) -> list[FetchedContent]:
    feed_url = source.config.get("feed_url", "")
    if not feed_url:
        return []

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(feed_url, follow_redirects=True)
        resp.raise_for_status()

    feed = feedparser.parse(resp.text)
    items = []
    now = datetime.now(timezone.utc)

    for entry in feed.entries[:50]:
        title = getattr(entry, "title", "")
        link = getattr(entry, "link", "")
        summary = getattr(entry, "summary", "") or getattr(entry, "description", "")
        body = summary

        if not title and not body:
            continue

        content_hash = _hash(title + body[:500])
        items.append(
            FetchedContent(
                source_id=source.id,
                workspace_id=source.workspace_id,
                title=title,
                url=link,
                body=body,
                summary=summary[:500],
                external_id=link,
                content_hash=content_hash,
                published_at=_parse_date(entry),
                fetched_at=now,
            )
        )
    return items
