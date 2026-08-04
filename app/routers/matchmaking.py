from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.database import get_db
from app.dependencies import get_current_user
from app.models.matchmaking_request import MatchmakingRequest, MatchmakingStatus
from app.models.transaction import Transaction, TransactionType
from app.models.user import User
from app.models.wager import Wager
from app.routers.wallet import get_balance
from app.schemas.matchmaking import MatchmakingStatusOut, QueueRequest
from app.services import connection_manager

router = APIRouter(prefix="/matchmaking", tags=["matchmaking"])


def _to_status_out(
    request: MatchmakingRequest, current_user_id: int, db: Session
) -> MatchmakingStatusOut:
    opponent_id = None
    if request.wager_id is not None:
        wager = db.get(Wager, request.wager_id)
        opponent_id = (
            wager.player2_id if wager.player1_id == current_user_id else wager.player1_id
        )

    return MatchmakingStatusOut(
        id=request.id,
        status=request.status,
        stake_amount=request.stake_amount,
        wager_id=request.wager_id,
        opponent_id=opponent_id,
        created_at=request.created_at,
    )


@router.post("/queue", response_model=MatchmakingStatusOut)
def queue(
    payload: QueueRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing = (
        db.query(MatchmakingRequest)
        .filter(
            MatchmakingRequest.user_id == current_user.id,
            MatchmakingRequest.status == MatchmakingStatus.WAITING,
        )
        .first()
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Already in queue",
        )

    if payload.stake_amount > get_balance(db, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient balance for this stake",
        )

    opponent_request = (
        db.query(MatchmakingRequest)
        .filter(
            MatchmakingRequest.status == MatchmakingStatus.WAITING,
            MatchmakingRequest.stake_amount == payload.stake_amount,
            MatchmakingRequest.user_id != current_user.id,
        )
        .order_by(MatchmakingRequest.created_at.asc())
        .with_for_update()
        .first()
    )

    my_request = MatchmakingRequest(
        user_id=current_user.id,
        stake_amount=payload.stake_amount,
        status=MatchmakingStatus.WAITING,
    )
    db.add(my_request)

    if opponent_request is not None and payload.stake_amount <= get_balance(
        db, opponent_request.user_id
    ):
        wager = Wager(
            player1_id=opponent_request.user_id,
            player2_id=current_user.id,
            stake_amount=payload.stake_amount,
        )
        db.add(wager)
        db.flush()

        opponent_request.status = MatchmakingStatus.MATCHED
        opponent_request.wager_id = wager.id
        my_request.status = MatchmakingStatus.MATCHED
        my_request.wager_id = wager.id

        db.add(
            Transaction(
                user_id=opponent_request.user_id,
                wager_id=wager.id,
                type=TransactionType.WAGER_LOCK,
                amount=-payload.stake_amount,
            )
        )
        db.add(
            Transaction(
                user_id=current_user.id,
                wager_id=wager.id,
                type=TransactionType.WAGER_LOCK,
                amount=-payload.stake_amount,
            )
        )

    db.commit()
    db.refresh(my_request)

    if opponent_request is not None and opponent_request.wager_id is not None:
        opponent_payload = MatchmakingStatusOut(
            id=opponent_request.id,
            status=opponent_request.status,
            stake_amount=opponent_request.stake_amount,
            wager_id=opponent_request.wager_id,
            opponent_id=current_user.id,
            created_at=opponent_request.created_at,
        ).model_dump(mode="json")
        connection_manager.notify(opponent_request.user_id, opponent_payload)

    return _to_status_out(my_request, current_user.id, db)


@router.delete("/queue", status_code=status.HTTP_204_NO_CONTENT)
def cancel_queue(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing = (
        db.query(MatchmakingRequest)
        .filter(
            MatchmakingRequest.user_id == current_user.id,
            MatchmakingRequest.status == MatchmakingStatus.WAITING,
        )
        .first()
    )
    if existing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not currently in queue",
        )

    existing.status = MatchmakingStatus.CANCELLED
    db.commit()


@router.get("/status", response_model=MatchmakingStatusOut)
def get_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    latest = (
        db.query(MatchmakingRequest)
        .filter(MatchmakingRequest.user_id == current_user.id)
        .order_by(MatchmakingRequest.created_at.desc())
        .first()
    )
    if latest is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No matchmaking history",
        )

    return _to_status_out(latest, current_user.id, db)


@router.websocket("/ws")
async def matchmaking_ws(websocket: WebSocket, token: str, db: Session = Depends(get_db)):
    try:
        payload = decode_access_token(token)
        user_id = int(payload["sub"])
    except Exception:
        await websocket.close(code=4001)
        return

    user = db.get(User, user_id)
    if user is None:
        await websocket.close(code=4001)
        return

    await websocket.accept()
    connection_manager.register(user_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        connection_manager.unregister(user_id, websocket)
