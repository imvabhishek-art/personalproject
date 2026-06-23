from datetime import datetime, timezone, timedelta
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.db.models.content_source import ContentSource, FetchedContent, SourceType


async def fetch_all_sources(ctx: dict) -> dict:
    from app.services.rss import fetch_rss
    from app.services.scraper import fetch_url
    from app.services.twitter import fetch_twitter
    from app.services.linkedin import fetch_linkedin
    from sqlalchemy import and_

    fetcher_map = {
        SourceType.rss: fetch_rss,
        SourceType.scrape: fetch_url,
        SourceType.twitter: fetch_twitter,
        SourceType.linkedin: fetch_linkedin,
    }

    now = datetime.now(timezone.utc)
    synced = 0
    errors = 0

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(ContentSource).where(ContentSource.is_active == True, ContentSource.type != SourceType.manual)
        )
        sources = result.scalars().all()

        for source in sources:
            if source.last_synced_at:
                next_sync = source.last_synced_at + timedelta(minutes=source.fetch_interval_minutes)
                if now < next_sync:
                    continue

            fetcher = fetcher_map.get(source.type)
            if not fetcher:
                continue

            try:
                items = await fetcher(source)
                for item in items:
                    existing = await db.execute(
                        select(FetchedContent).where(
                            and_(
                                FetchedContent.workspace_id == source.workspace_id,
                                FetchedContent.content_hash == item.content_hash,
                            )
                        )
                    )
                    if not existing.scalar_one_or_none():
                        db.add(item)

                source.last_synced_at = now
                synced += 1
            except Exception:
                errors += 1

        await db.commit()

    return {"synced": synced, "errors": errors}
