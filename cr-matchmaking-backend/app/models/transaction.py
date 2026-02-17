import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import ForeignKey, Index, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

# Transaction type constants
TX_TYPE_DEPOSIT = "deposit"
TX_TYPE_WITHDRAW = "withdraw"
TX_TYPE_BET_PLACED = "bet_placed"
TX_TYPE_WIN = "win"
TX_TYPE_LOSS = "loss"
TX_TYPE_REFUND = "refund"

# Transaction status constants
TX_STATUS_PENDING = "pending"
TX_STATUS_COMPLETED = "completed"
TX_STATUS_FAILED = "failed"


class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False
    )
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    balance_before: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    balance_after: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    match_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("matches.match_id"), nullable=True
    )
    stripe_payment_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(20), default=TX_STATUS_COMPLETED
    )
    metadata_: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata", JSONB, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(foreign_keys=[user_id])
    match: Mapped["Match | None"] = relationship(foreign_keys=[match_id])

    __table_args__ = (
        Index("idx_transactions_user", "user_id"),
        Index("idx_transactions_match", "match_id"),
        Index("idx_transactions_created", "created_at"),
    )
