from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.wager import Wager
from app.schemas.wager import WagerOut

router = APIRouter(prefix="/wagers", tags=["wagers"])


def _to_wager_out(wager: Wager, usernames: dict[int, str]) -> WagerOut:
    return WagerOut(
        id=wager.id,
        player1_id=wager.player1_id,
        player2_id=wager.player2_id,
        player1_username=usernames.get(wager.player1_id, "unknown"),
        player2_username=usernames.get(wager.player2_id, "unknown"),
        stake_amount=wager.stake_amount,
        status=wager.status,
        winner_id=wager.winner_id,
        created_at=wager.created_at,
        settled_at=wager.settled_at,
    )


@router.get("", response_model=list[WagerOut])
def list_wagers(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    wagers = (
        db.query(Wager)
        .filter(
            or_(Wager.player1_id == current_user.id, Wager.player2_id == current_user.id)
        )
        .order_by(Wager.created_at.desc())
        .all()
    )
    player_ids = {w.player1_id for w in wagers} | {w.player2_id for w in wagers}
    usernames = {
        u.id: u.username for u in db.query(User).filter(User.id.in_(player_ids)).all()
    }
    return [_to_wager_out(w, usernames) for w in wagers]


@router.get("/{wager_id}", response_model=WagerOut)
def get_wager(
    wager_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    wager = db.get(Wager, wager_id)
    if wager is None or current_user.id not in (wager.player1_id, wager.player2_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Wager not found"
        )
    usernames = {
        u.id: u.username
        for u in db.query(User)
        .filter(User.id.in_({wager.player1_id, wager.player2_id}))
        .all()
    }
    return _to_wager_out(wager, usernames)
