from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, field_validator

from app.models.matchmaking_request import MatchmakingStatus
from app.models.wager import WagerStatus

STAKE_TIERS = (Decimal("1"), Decimal("5"), Decimal("10"), Decimal("20"), Decimal("50"))


class QueueRequest(BaseModel):
    stake_amount: Decimal

    @field_validator("stake_amount")
    @classmethod
    def validate_stake_tier(cls, v: Decimal) -> Decimal:
        if v not in STAKE_TIERS:
            tiers = ", ".join(str(tier) for tier in STAKE_TIERS)
            raise ValueError(f"Stake amount must be one of: {tiers}")
        return v


class MatchmakingStatusOut(BaseModel):
    id: int
    status: MatchmakingStatus
    stake_amount: Decimal
    wager_id: int | None
    opponent_id: int | None
    opponent_supercell_link: str | None = None
    wager_status: WagerStatus | None = None
    winner_id: int | None = None
    created_at: datetime

    class Config:
        from_attributes = True
