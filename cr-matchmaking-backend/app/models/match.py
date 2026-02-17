import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import ForeignKey, Index, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

# Match status constants
MATCH_STATUS_ACTIVE = "active"
MATCH_STATUS_COMPLETED = "completed"
MATCH_STATUS_CANCELLED = "cancelled"
MATCH_STATUS_DISPUTED = "disputed"


class Match(Base):
    __tablename__ = "matches"

    match_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    player1_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False
    )
    player2_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False
    )
    player1_tag: Mapped[str] = mapped_column(String(20), nullable=False)
    player2_tag: Mapped[str] = mapped_column(String(20), nullable=False)
    bet_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=MATCH_STATUS_ACTIVE)
    winner_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=True
    )
    battle_time: Mapped[datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    cancellation_reason: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )

    player1: Mapped["User"] = relationship(foreign_keys=[player1_id])
    player2: Mapped["User"] = relationship(foreign_keys=[player2_id])
    winner: Mapped["User | None"] = relationship(foreign_keys=[winner_id])

    __table_args__ = (
        Index("idx_matches_status", "status"),
        Index("idx_matches_players", "player1_id", "player2_id"),
        Index(
            "idx_matches_expires_active",
            "expires_at",
            postgresql_where=(status == MATCH_STATUS_ACTIVE),
        ),
    )
