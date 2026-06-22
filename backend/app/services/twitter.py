import hashlib
from datetime import datetime, timezone
from app.db.models.content_source import ContentSource, FetchedContent
from app.config import get_settings


def _hash(text: str) -> str:
    return hashlib.sha256(text.strip().lower().encode()).hexdigest()[:64]


async def fetch_twitter(source: ContentSource) -> list[FetchedContent]:
    settings = get_settings()
    if not settings.twitter_bearer_token:
        return []

    import tweepy

    handle = source.config.get("handle", "")
    keywords = source.config.get("keywords", [])
    query = source.config.get("query", "")

    if handle:
        query = f"from:{handle.lstrip('@')} -is:retweet"
    elif keywords:
        query = " OR ".join(keywords) + " -is:retweet lang:en"
    elif not query:
        return []

    client = tweepy.Client(bearer_token=settings.twitter_bearer_token)
    try:
        response = client.search_recent_tweets(
            query=query,
            max_results=20,
            tweet_fields=["created_at", "text", "author_id"],
        )
    except Exception:
        return []

    if not response.data:
        return []

    now = datetime.now(timezone.utc)
    items = []
    for tweet in response.data:
        text = tweet.text
        tweet_url = f"https://twitter.com/i/web/status/{tweet.id}"
        items.append(
            FetchedContent(
                source_id=source.id,
                workspace_id=source.workspace_id,
                title=text[:80] + ("..." if len(text) > 80 else ""),
                url=tweet_url,
                body=text,
                summary=text[:300],
                external_id=str(tweet.id),
                content_hash=_hash(str(tweet.id) + text),
                published_at=tweet.created_at,
                fetched_at=now,
            )
        )
    return items
