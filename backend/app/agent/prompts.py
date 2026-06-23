from app.db.models.generated_content import ContentType

CONTENT_INSTRUCTIONS = {
    ContentType.newsletter: """Write a complete newsletter with:
- Engaging subject line
- Brief intro paragraph
- 3-5 curated story sections (each with headline, 2-3 sentence summary, and why it matters)
- A closing call-to-action or thought
Format in clean Markdown.""",

    ContentType.blog: """Write a complete blog post with:
- Compelling headline
- Introduction (hook + thesis)
- 3-5 main sections with subheadings
- Conclusion with key takeaways
Format in clean Markdown.""",

    ContentType.linkedin: """Write a LinkedIn post:
- Strong opening line (no "I'm excited to share")
- 3-5 key insights or observations
- Personal perspective or commentary
- 2-3 relevant hashtags at the end
- Max 1300 characters
No markdown formatting - plain text only.""",

    ContentType.twitter_thread: """Write a Twitter/X thread:
- Tweet 1: Hook (max 280 chars)
- Tweets 2-7: One insight each (max 280 chars)
- Final tweet: Summary + call to action
Format as numbered tweets: 1/, 2/, etc.""",

    ContentType.summary: """Write a concise summary:
- 2-3 sentences overview
- 3-5 bullet points of key takeaways
- One sentence conclusion
Format in clean Markdown.""",
}

LONG_FORM_TYPES = {ContentType.newsletter, ContentType.blog}


def pick_model(content_type: ContentType) -> str:
    if content_type in LONG_FORM_TYPES:
        return "claude-opus-4-8"
    return "claude-sonnet-4-6"


def build_system_prompt(profile: dict) -> list[dict]:
    base = "You are an expert content strategist and writer. Generate high-quality, engaging content tailored to the workspace profile. Always match the specified tone, audience, and style. Never generate generic filler content."

    content_types = ", ".join(profile.get("content_types", [])) or "general content"
    audience = profile.get("audience", "general audience")
    persona = profile.get("persona", "content creator")
    tone = profile.get("tone", "professional")
    topics = ", ".join(profile.get("topics", [])) or "current events and industry news"
    brand_name = profile.get("brand_name", "")
    writing_style = profile.get("writing_style", "")

    profile_text = f"""

## Workspace Profile
- Content types produced: {content_types}
- Target audience: {audience}
- Creator persona: {persona}
- Tone: {tone}
- Core topics: {topics}"""

    if brand_name:
        profile_text += f"\n- Brand name: {brand_name}"
    if writing_style:
        profile_text += f"\n- Writing style notes: {writing_style}"

    return [
        {
            "type": "text",
            "text": base + profile_text,
            "cache_control": {"type": "ephemeral"},
        }
    ]


def build_generation_prompt(content_type: ContentType, instructions: str, topic: str = "") -> str:
    type_instruction = CONTENT_INSTRUCTIONS.get(content_type, "Generate high-quality content.")
    parts = [f"Generate a {content_type.value}."]
    if topic:
        parts.append(f"Topic/focus: {topic}")
    if instructions:
        parts.append(f"Additional instructions: {instructions}")
    parts.append("\n" + type_instruction)
    parts.append("\nUse the fetch_recent_content tool to find relevant content to reference, then search for more if needed. Once you have enough material, call save_draft with your completed content.")
    return "\n\n".join(parts)
