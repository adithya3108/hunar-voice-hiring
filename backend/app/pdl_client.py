import httpx

from app.config import get_settings

settings = get_settings()

PDL_SEARCH_URL = "https://api.peopledatalabs.com/v5/person/search"

_MOCK_FIRST_NAMES = ["Aarav", "Priya", "Rohan", "Sneha", "Kabir", "Isha", "Vikram", "Neha"]
_MOCK_LAST_NAMES = ["Sharma", "Iyer", "Reddy", "Nair", "Gupta", "Menon", "Verma", "Rao"]


def _mock_profiles(title: str, skills: list[str], limit: int) -> list[dict]:
    """Deterministic placeholder candidates used when no real search API key is configured.

    Phone numbers are intentionally invalid placeholders (not a real dialable range) so an
    outbound call can never accidentally reach a real stranger who never opted in. Replace a
    candidate's phone_number via PATCH /candidates/{id} with a real, consented number before
    triggering a call.
    """
    profiles = []
    for i in range(min(limit, len(_MOCK_FIRST_NAMES))):
        name = f"{_MOCK_FIRST_NAMES[i]} {_MOCK_LAST_NAMES[i]}"
        profiles.append(
            {
                "full_name": name,
                "job_title": title,
                "skills": skills,
                "phone_numbers": [f"+1000000{i:04d}"],
                "emails": [f"{name.lower().replace(' ', '.')}@example-mock.com"],
                "mock": True,
            }
        )
    return profiles


async def search_people(elasticsearch_query: dict, limit: int = 10, title: str = "", skills: list[str] | None = None) -> list[dict]:
    """Run a person search and return raw profile dicts.

    Falls back to deterministic mock profiles when PDL_API_KEY isn't configured, since PDL/
    Apollo/Proxycurl/Coresignal all gate real search behind paid or approval-gated tiers that
    weren't obtainable within this assignment's window. See README for details.
    """
    if not settings.pdl_api_key or settings.pdl_api_key == "changeme":
        return _mock_profiles(title, skills or [], limit)

    headers = {"X-Api-Key": settings.pdl_api_key}
    payload = {"query": elasticsearch_query, "size": limit}
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(PDL_SEARCH_URL, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        return data.get("data", [])
