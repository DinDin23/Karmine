import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.match import OpponentInfo


class JoinQueueRequest(BaseModel):
    bet_amount: float = Field(gt=0)


class JoinQueueResponse(BaseModel):
    queue_id: str
    position: int
    estimated_wait_time: int


class QueueStatusResponse(BaseModel):
    in_queue: bool
    bet_amount: float | None = None
    queue_position: int | None = None
    wait_time: int | None = None


class MatchFoundEvent(BaseModel):
    match_id: uuid.UUID
    opponent: OpponentInfo
    bet_amount: float
    expires_at: datetime
