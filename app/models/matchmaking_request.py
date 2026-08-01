import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, func
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class MatchmakingStatus(str, enum.Enum):
    WAITING = "waiting"
    MATCHED = "matched"
    CANCELLED = "cancelled"


class MatchmakingRequest(Base):
    __tablename__ = "matchmaking_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    stake_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    status: Mapped[MatchmakingStatus] = mapped_column(
        SQLEnum(MatchmakingStatus, name="matchmaking_status"),
        default=MatchmakingStatus.WAITING,
    )
    wager_id: Mapped[int | None] = mapped_column(
        ForeignKey("wagers.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
