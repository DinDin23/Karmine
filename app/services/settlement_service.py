import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.config import settings
from app.models.matchmaking_request import MatchmakingRequest
from app.models.transaction import Transaction, TransactionType
from app.models.user import User
from app.models.wager import Wager, WagerStatus
from app.services import connection_manager
from app.services.cr_api_service import get_battlelog
from app.services.matchmaking_status import build_status_out

logger = logging.getLogger(__name__)

# Wagers are 1v1 challenges, so we settle off either a ladder match or a
# friend-challenge ("friendly") battle. Other types (tournaments, clan wars,
# challenges, 2v2, etc.) aren't wagerable and are ignored.
_WAGERABLE_BATTLE_TYPES = {"PvP", "friendly"}


def _parse_battle_time(battle_time: str) -> datetime:
    return datetime.strptime(battle_time, "%Y%m%dT%H%M%S.%fZ").replace(
        tzinfo=timezone.utc
    )


def _remaining_tower_hp(side: dict) -> int:
    """Sum of remaining tower HP. The API omits a tower's HP field entirely once it's destroyed."""
    king_hp = side.get("kingTowerHitPoints", 0)
    princess_hp = sum(side.get("princessTowersHitPoints", []))
    return king_hp + princess_hp


def _find_result(battlelog: list[dict], opponent_tag: str, after: datetime) -> str | None:
    """Return 'team' or 'opponent' for the winning side, or None if no match found yet.

    Crowns decide the winner in regulation. If crowns are tied, the battle went to
    overtime, where remaining tower HP is the real tiebreaker (CR never ends in a true draw).
    """
    for battle in battlelog:
        if battle.get("type") not in _WAGERABLE_BATTLE_TYPES:
            continue
        if _parse_battle_time(battle["battleTime"]) <= after:
            continue
        opponents = battle.get("opponent", [])
        if not any(o.get("tag") == opponent_tag for o in opponents):
            continue

        team, opponent = battle["team"][0], battle["opponent"][0]
        team_crowns, opponent_crowns = team["crowns"], opponent["crowns"]
        if team_crowns != opponent_crowns:
            return "team" if team_crowns > opponent_crowns else "opponent"

        team_hp, opponent_hp = _remaining_tower_hp(team), _remaining_tower_hp(opponent)
        if team_hp == opponent_hp:
            raise ValueError(
                f"Battle at {battle['battleTime']} tied on both crowns "
                f"({team_crowns}-{opponent_crowns}) and tower HP "
                f"({team_hp}-{opponent_hp}) — this shouldn't be possible in a 1v1 battle"
            )
        return "team" if team_hp > opponent_hp else "opponent"

    return None


def _notify_players(db: Session, wager: Wager) -> None:
    """Push the current status to both players' matchmaking widgets, if connected.

    Used once a wager reaches a terminal state (settled or expired/cancelled) so the
    frontend can show the result and revert out of the "matched" panel live, instead
    of only finding out on the next page load.
    """
    requests = (
        db.query(MatchmakingRequest)
        .filter(MatchmakingRequest.wager_id == wager.id)
        .all()
    )
    for request in requests:
        payload = build_status_out(request, request.user_id, db).model_dump(mode="json")
        connection_manager.notify(request.user_id, payload)


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
    _notify_players(db, wager)


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


def _expire_wager(db: Session, wager: Wager) -> None:
    wager.status = WagerStatus.CANCELLED
    wager.settled_at = datetime.now(timezone.utc)

    for player_id in (wager.player1_id, wager.player2_id):
        db.add(
            Transaction(
                user_id=player_id,
                wager_id=wager.id,
                type=TransactionType.WAGER_REFUND,
                amount=wager.stake_amount,
            )
        )
    db.commit()
    _notify_players(db, wager)


def expire_stale_wagers(db: Session) -> None:
    """Cancel + refund matches that were made but never finished within the timeout.

    Runs alongside poll_and_settle on the same worker tick, so a wager that never
    turns up a qualifying battle in the CR API doesn't sit MATCHED/AWAITING_RESULT
    forever.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=settings.match_timeout_minutes)
    wagers = (
        db.query(Wager)
        .filter(
            Wager.status.in_([WagerStatus.MATCHED, WagerStatus.AWAITING_RESULT]),
            Wager.created_at < cutoff,
        )
        .all()
    )
    for wager in wagers:
        try:
            _expire_wager(db, wager)
        except Exception:
            db.rollback()
            logger.exception("Failed to expire wager %s", wager.id)
