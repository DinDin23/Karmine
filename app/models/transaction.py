import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, func
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TransactionType(str, enum.Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    WAGER_LOCK = "wager_lock"
    WAGER_PAYOUT = "wager_payout"
    WAGER_REFUND = "wager_refund"


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    wager_id: Mapped[int | None] = mapped_column(
        ForeignKey("wagers.id"), nullable=True, index=True
    )
    type: Mapped[TransactionType] = mapped_column(
        SQLEnum(TransactionType, name="transaction_type")
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
