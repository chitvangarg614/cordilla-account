MOCK_EXTERNAL_API_RESPONSE = {
    "ACC-01073": {
        "company_name": "Example Corp",
        "recent_news": [
            {
                "title": "Example Corp announces product expansion",
                "description": "The company plans to expand into new markets.",
                "published_at": "2026-07-28",
                "source": "Mock Business News",
            },
            {
                "title": "Example Corp increases technology hiring",
                "description": "The company is expanding its engineering organization.",
                "published_at": "2026-07-20",
                "source": "Mock Tech News",
            },
        ],
        "open_roles": 37,
        "engineering_roles": 14,
    },
}


def mock_external_api(account_id: str) -> dict:
    """Mock external company intelligence API."""
    return MOCK_EXTERNAL_API_RESPONSE.get(
        account_id,
        {
            "company_name": None,
            "recent_news": [],
            "open_roles": None,
            "engineering_roles": None,
        },
    )


def build_external_context(account_id: str) -> dict:
    """Build sales-relevant external context from the API response."""
    response = mock_external_api(account_id)

    return {
        "company_name": response.get("company_name"),
        "recent_news": response.get("recent_news", []),
        "open_roles": response.get("open_roles"),
        "engineering_roles": response.get("engineering_roles"),
    }
