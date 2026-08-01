import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, func
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class WagerStatus(str, enum.Enum):
    MATCHED = "matched"
    AWAITING_RESULT = "awaiting_result"
    SETTLED = "settled"
    DISPUTED = "disputed"
    CANCELLED = "cancelled"


class Wager(Base):
    __tablename__ = "wagers"

    id: Mapped[int] = mapped_column(primary_key=True)
    player1_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    player2_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    stake_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    status: Mapped[WagerStatus] = mapped_column(
        SQLEnum(WagerStatus, name="wager_status"), default=WagerStatus.MATCHED
    )
    winner_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    settled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
