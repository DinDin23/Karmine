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
        if battle.get("type") != "PvP":
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
                f"({team_hp}-{opponent_hp}) — this shouldn't be possible in a 1v1 ladder match"
            )
        return "team" if team_hp > opponent_hp else "opponent"

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
