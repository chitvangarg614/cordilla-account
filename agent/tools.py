MOCK_ACCOUNT_HISTORY = {
    "ACC-01073": {
        "last_contacted_days_ago": 12,
        "open_opportunities": 1,
        "previous_customer": False,
        "last_contact_outcome": "Positive response",
    },
    "ACC-00533": {
        "last_contacted_days_ago": 75,
        "open_opportunities": 0,
        "previous_customer": True,
        "last_contact_outcome": "No response",
    },
}


def get_account_history(account_id: str) -> dict:
    """Retrieve CRM history for an account."""

    return MOCK_ACCOUNT_HISTORY.get(
        account_id,
        {
            "last_contacted_days_ago": None,
            "open_opportunities": 0,
            "previous_customer": False,
            "last_contact_outcome": None,
        },
    )