"""Agent prompt builder unit tests."""

from app.agent.prompts import build_system_prompt, build_generation_prompt
from app.agent.orchestrator import CREDIT_COSTS
from app.db.models.generated_content import ContentType


def test_system_prompt_has_cache_control():
    profile = {"audience": "SaaS founders", "tone": "conversational", "brand_name": "Acme"}
    blocks = build_system_prompt(profile)
    assert len(blocks) >= 1
    assert blocks[0].get("cache_control") == {"type": "ephemeral"}
    assert "SaaS founders" in blocks[0]["text"]


def test_system_prompt_includes_profile_fields():
    profile = {"tone": "witty", "topics": ["AI", "productivity"], "persona": "creator"}
    blocks = build_system_prompt(profile)
    text = blocks[0]["text"]
    assert "witty" in text
    assert "AI" in text


def test_generation_prompt_includes_type():
    prompt = build_generation_prompt(ContentType.newsletter, "", "AI tools")
    assert "newsletter" in prompt.lower()
    assert "AI tools" in prompt


def test_credit_costs_defined():
    for ct in ContentType:
        assert ct in CREDIT_COSTS, f"Missing credit cost for {ct}"
        assert CREDIT_COSTS[ct] > 0
