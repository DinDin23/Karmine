from urllib.parse import quote

import httpx

from app.config import settings


def get_battlelog(player_tag: str) -> list[dict]:
    """Fetch a player's recent battle history from the Clash Royale API."""
    encoded_tag = quote(player_tag, safe="")
    url = f"{settings.cr_api_url}/players/{encoded_tag}/battlelog"

    response = httpx.get(
        url,
        headers={"Authorization": f"Bearer {settings.cr_api_key}"},
        timeout=10.0,
    )
    response.raise_for_status()
    return response.json()
