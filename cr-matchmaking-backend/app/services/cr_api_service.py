from urllib.parse import quote

import httpx

from app.config import settings
from app.utils.exceptions import AppException, InvalidPlayerTag


async def get_player(player_tag: str) -> dict:
    """Fetch a player profile from the Clash Royale API."""
    encoded_tag = quote(player_tag, safe="")
    url = f"{settings.CR_API_URL}/players/{encoded_tag}"

    async with httpx.AsyncClient() as client:
        response = await client.get(
            url,
            headers={"Authorization": f"Bearer {settings.CR_API_KEY}"},
        )

    if response.status_code == 404:
        raise InvalidPlayerTag(player_tag)
    if response.status_code == 403:
        raise AppException(
            code="CR_API_ERROR",
            message="CR API access denied — check API key",
            status_code=502,
        )
    response.raise_for_status()
    return response.json()
