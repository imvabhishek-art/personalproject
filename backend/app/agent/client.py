import anthropic
from functools import lru_cache
from app.config import get_settings


@lru_cache
def get_anthropic_client() -> anthropic.AsyncAnthropic:
    settings = get_settings()
    return anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
