from urllib.parse import quote

import httpx

from app.config import settings


def player_exists(player_tag: str) -> bool:
    """Return whether the Clash Royale API knows this player tag.

    404 means no such player; any other error (bad key, IP not allowlisted,
    CR API down) raises so callers can tell "doesn't exist" from "couldn't check".
    """
    encoded_tag = quote(player_tag, safe="")
    url = f"{settings.cr_api_url}/players/{encoded_tag}"

    response = httpx.get(
        url,
        headers={"Authorization": f"Bearer {settings.cr_api_key}"},
        timeout=10.0,
    )
    if response.status_code == 404:
        return False
    response.raise_for_status()
    return True


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
