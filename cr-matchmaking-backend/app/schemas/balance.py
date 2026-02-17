import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class BalanceResponse(BaseModel):
    balance: float
    escrowed: float
    available: float
    lifetime_deposited: float
    lifetime_withdrawn: float
    lifetime_won: float

    model_config = {"from_attributes": True}


class DepositRequest(BaseModel):
    amount: float = Field(gt=0, le=1000)
    payment_method_id: str


class DepositResponse(BaseModel):
    transaction_id: uuid.UUID
    amount: float
    new_balance: float
    status: str


class WithdrawRequest(BaseModel):
    amount: float = Field(gt=0)


class WithdrawResponse(BaseModel):
    transaction_id: uuid.UUID
    amount: float
    new_balance: float
    status: str


class TransactionResponse(BaseModel):
    transaction_id: uuid.UUID
    type: str
    amount: float
    balance_before: float | None = None
    balance_after: float | None = None
    match_id: uuid.UUID | None = None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
