import uuid
from datetime import datetime

from pydantic import BaseModel


class OpponentInfo(BaseModel):
    username: str
    player_tag: str
    trophy_level: int | None = None


class PlayerInfo(BaseModel):
    user_id: uuid.UUID
    username: str
    player_tag: str
    trophy_level: int | None = None


class MatchResponse(BaseModel):
    match_id: uuid.UUID
    opponent: OpponentInfo
    bet_amount: float
    status: str
    result: str | None = None
    payout: float | None = None
    created_at: datetime
    completed_at: datetime | None = None


class MatchDetailResponse(BaseModel):
    match_id: uuid.UUID
    player1: PlayerInfo
    player2: PlayerInfo
    bet_amount: float
    status: str
    winner_id: uuid.UUID | None = None
    battle_time: datetime | None = None
    created_at: datetime
    expires_at: datetime
    completed_at: datetime | None = None


class MatchListResponse(BaseModel):
    matches: list[MatchResponse]
    total: int


class DisputeRequest(BaseModel):
    reason: str
