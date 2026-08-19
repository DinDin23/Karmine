from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from app.models.wager import WagerStatus


class WagerOut(BaseModel):
    id: int
    player1_id: int
    player2_id: int
    player1_username: str
    player2_username: str
    stake_amount: Decimal
    status: WagerStatus
    winner_id: int | None
    created_at: datetime
    settled_at: datetime | None

    class Config:
        from_attributes = True
