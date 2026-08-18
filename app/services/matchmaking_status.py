from sqlalchemy.orm import Session

from app.models.matchmaking_request import MatchmakingRequest
from app.models.user import User
from app.models.wager import Wager
from app.schemas.matchmaking import MatchmakingStatusOut


def build_status_out(
    request: MatchmakingRequest, viewer_id: int, db: Session
) -> MatchmakingStatusOut:
    """Build the status payload for one player's view of a matchmaking request.

    Shared between the /matchmaking router (HTTP responses + the WS push sent to
    the opponent on match) and settlement_service (WS pushes sent when a wager
    settles or expires), so all three call sites stay in sync on shape/fields.
    """
    opponent_id = None
    opponent_supercell_link = None
    wager_status = None
    winner_id = None

    if request.wager_id is not None:
        wager = db.get(Wager, request.wager_id)
        opponent_id = (
            wager.player2_id if wager.player1_id == viewer_id else wager.player1_id
        )
        opponent_supercell_link = db.get(User, opponent_id).supercell_id_link
        wager_status = wager.status
        winner_id = wager.winner_id

    return MatchmakingStatusOut(
        id=request.id,
        status=request.status,
        stake_amount=request.stake_amount,
        wager_id=request.wager_id,
        opponent_id=opponent_id,
        opponent_supercell_link=opponent_supercell_link,
        wager_status=wager_status,
        winner_id=winner_id,
        created_at=request.created_at,
    )
