from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.transaction import TransactionType


class BalanceOut(BaseModel):
    balance: Decimal


class DepositRequest(BaseModel):
    amount: Decimal = Field(gt=0)


class WithdrawRequest(BaseModel):
    amount: Decimal = Field(gt=0)


class TransactionOut(BaseModel):
    id: int
    wager_id: int | None
    type: TransactionType
    amount: Decimal
    created_at: datetime

    class Config:
        from_attributes = True
