import hashlib
from datetime import datetime, timezone
import httpx
from bs4 import BeautifulSoup
from app.db.models.content_source import ContentSource, FetchedContent


def _hash(text: str) -> str:
    return hashlib.sha256(text.strip().lower().encode()).hexdigest()[:64]


async def fetch_url(source: ContentSource) -> list[FetchedContent]:
    page_url = source.config.get("page_url", "")
    css_selector = source.config.get("css_selector", "article, main, .content")
    if not page_url:
        return []

    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        resp = await client.get(
            page_url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; NewsletterBot/1.0)"},
        )
        resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "lxml")

    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    elements = soup.select(css_selector) or [soup.body or soup]
    text = "\n\n".join(el.get_text(separator="\n", strip=True) for el in elements)
    title = soup.title.string if soup.title else page_url
    summary = text[:500]

    if not text.strip():
        return []

    return [
        FetchedContent(
            source_id=source.id,
            workspace_id=source.workspace_id,
            title=title,
            url=page_url,
            body=text[:50000],
            summary=summary,
            external_id=page_url,
            content_hash=_hash(text[:1000]),
            fetched_at=datetime.now(timezone.utc),
        )
    ]
