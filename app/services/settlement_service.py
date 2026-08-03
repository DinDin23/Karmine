import logging
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.transaction import Transaction, TransactionType
from app.models.user import User
from app.models.wager import Wager, WagerStatus
from app.services.cr_api_service import get_battlelog

logger = logging.getLogger(__name__)


def _parse_battle_time(battle_time: str) -> datetime:
    return datetime.strptime(battle_time, "%Y%m%dT%H%M%S.%fZ").replace(
        tzinfo=timezone.utc
    )


def _find_result(battlelog: list[dict], opponent_tag: str, after: datetime) -> str | None:
    """Return 'team' or 'opponent' for the crown-winning side, 'draw', or None if no match found."""
    for battle in battlelog:
        if battle.get("type") != "PvP":
            continue
        if _parse_battle_time(battle["battleTime"]) <= after:
            continue
        opponents = battle.get("opponent", [])
        if not any(o.get("tag") == opponent_tag for o in opponents):
            continue

        team_crowns = battle["team"][0]["crowns"]
        opponent_crowns = battle["opponent"][0]["crowns"]
        if team_crowns > opponent_crowns:
            return "team"
        if opponent_crowns > team_crowns:
            return "opponent"
        return "draw"

    return None


def settle_wager(db: Session, wager: Wager) -> None:
    if wager.status == WagerStatus.MATCHED:
        wager.status = WagerStatus.AWAITING_RESULT
        db.commit()

    player1 = db.get(User, wager.player1_id)
    player2 = db.get(User, wager.player2_id)

    battlelog = get_battlelog(player1.cr_player_tag)
    result = _find_result(battlelog, player2.cr_player_tag, wager.created_at)

    if result is None:
        return

    if result == "draw":
        wager.status = WagerStatus.DISPUTED
        db.commit()
        return

    winner = player1 if result == "team" else player2
    wager.status = WagerStatus.SETTLED
    wager.winner_id = winner.id
    wager.settled_at = datetime.now(timezone.utc)

    db.add(
        Transaction(
            user_id=winner.id,
            wager_id=wager.id,
            type=TransactionType.WAGER_PAYOUT,
            amount=wager.stake_amount * Decimal(2),
        )
    )
    db.commit()


def poll_and_settle(db: Session) -> None:
    wagers = (
        db.query(Wager)
        .filter(Wager.status.in_([WagerStatus.MATCHED, WagerStatus.AWAITING_RESULT]))
        .all()
    )
    for wager in wagers:
        try:
            settle_wager(db, wager)
        except Exception:
            db.rollback()
            logger.exception("Failed to settle wager %s", wager.id)
