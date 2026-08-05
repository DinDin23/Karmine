from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.matchmaking_request import MatchmakingStatus


class QueueRequest(BaseModel):
    stake_amount: Decimal = Field(gt=0)


class MatchmakingStatusOut(BaseModel):
    id: int
    status: MatchmakingStatus
    stake_amount: Decimal
    wager_id: int | None
    opponent_id: int | None
    opponent_supercell_link: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True
