AGENT_TOOLS = [
    {
        "name": "fetch_recent_content",
        "description": "Fetch recent content items from this workspace's sources. Returns title, summary, and id for each item.",
        "input_schema": {
            "type": "object",
            "properties": {
                "source_types": {
                    "type": "array",
                    "items": {"type": "string", "enum": ["rss", "scrape", "twitter", "linkedin", "manual"]},
                    "description": "Filter by source types. Omit to include all.",
                },
                "since_hours": {
                    "type": "integer",
                    "description": "Only return items fetched within the last N hours.",
                    "default": 168,
                },
                "limit": {
                    "type": "integer",
                    "description": "Max items to return.",
                    "default": 20,
                },
            },
        },
    },
    {
        "name": "search_content",
        "description": "Search fetched content items by keyword or phrase.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query to match against content titles and bodies.",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max results to return.",
                    "default": 10,
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_content_item",
        "description": "Get the full text body of a specific content item by ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "content_id": {
                    "type": "string",
                    "description": "UUID of the fetched content item.",
                },
            },
            "required": ["content_id"],
        },
    },
    {
        "name": "save_draft",
        "description": "Save the completed content as a draft. Call this when you have finished writing the content.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Title of the content piece.",
                },
                "body_md": {
                    "type": "string",
                    "description": "Full content body in Markdown format.",
                },
                "subject_line": {
                    "type": "string",
                    "description": "Email subject line (for newsletters only).",
                },
                "source_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "UUIDs of fetched content items used as sources.",
                },
            },
            "required": ["title", "body_md"],
        },
    },
]
