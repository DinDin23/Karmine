from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.wager import Wager
from app.schemas.wager import WagerOut

router = APIRouter(prefix="/wagers", tags=["wagers"])


@router.get("", response_model=list[WagerOut])
def list_wagers(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    return (
        db.query(Wager)
        .filter(
            or_(Wager.player1_id == current_user.id, Wager.player2_id == current_user.id)
        )
        .order_by(Wager.created_at.desc())
        .all()
    )


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
    return wager
