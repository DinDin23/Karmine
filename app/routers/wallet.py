from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.transaction import Transaction, TransactionType
from app.models.user import User
from app.schemas.wallet import BalanceOut, DepositRequest, TransactionOut, WithdrawRequest

router = APIRouter(prefix="/wallet", tags=["wallet"])


def get_balance(db: Session, user_id: int) -> Decimal:
    total = db.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
        Transaction.user_id == user_id
    ).scalar()
    return Decimal(total)


@router.get("/balance", response_model=BalanceOut)
def balance(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    return BalanceOut(balance=get_balance(db, current_user.id))


@router.post("/deposit", response_model=BalanceOut)
def deposit(
    payload: DepositRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    transaction = Transaction(
        user_id=current_user.id,
        type=TransactionType.DEPOSIT,
        amount=payload.amount,
    )
    db.add(transaction)
    db.commit()
    return BalanceOut(balance=get_balance(db, current_user.id))


@router.post("/withdraw", response_model=BalanceOut)
def withdraw(
    payload: WithdrawRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    current_balance = get_balance(db, current_user.id)
    if payload.amount > current_balance:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient balance",
        )

    transaction = Transaction(
        user_id=current_user.id,
        type=TransactionType.WITHDRAWAL,
        amount=-payload.amount,
    )
    db.add(transaction)
    db.commit()
    return BalanceOut(balance=get_balance(db, current_user.id))


@router.get("/transactions", response_model=list[TransactionOut])
def transactions(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    return (
        db.query(Transaction)
        .filter(Transaction.user_id == current_user.id)
        .order_by(Transaction.created_at.desc())
        .all()
    )
