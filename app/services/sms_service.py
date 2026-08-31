import logging

from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client

from app.config import settings
from app.models.user import User

logger = logging.getLogger(__name__)

_client = Client(
    settings.twilio_api_key_sid,
    settings.twilio_api_key_secret,
    settings.twilio_account_sid,
)


def send_match_invite(user: User, opponent: User) -> None:
    """Text a user their opponent's Supercell ID friend link after a match.

    No-op unless the user opted in to SMS and has a phone number on file; the
    opponent's friend link is always available in-app regardless.
    """
    if not user.sms_consent or not user.phone_number:
        logger.info(
            "Skipping match invite SMS for user %s (no consent / no phone)", user.id
        )
        return

    body = (
        f"Karmine: You've been matched with {opponent.username}! "
        f"Add them in Clash Royale: {opponent.supercell_id_link}"
    )
    try:
        _client.messages.create(
            to=user.phone_number,
            from_=settings.twilio_from_number,
            body=body,
        )
    except TwilioRestException:
        logger.exception("Failed to send match invite SMS to user %s", user.id)
