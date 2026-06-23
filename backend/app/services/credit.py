import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from fastapi import HTTPException, status
from app.db.models.credit import CreditAccount, CreditTransaction, TransactionType
from app.db.base import utcnow


class InsufficientCreditsError(HTTPException):
    def __init__(self, balance: int, required: int):
        super().__init__(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Insufficient credits: have {balance}, need {required}",
        )


async def get_or_create_account(workspace_id: uuid.UUID, db: AsyncSession) -> CreditAccount:
    result = await db.execute(
        select(CreditAccount).where(CreditAccount.workspace_id == workspace_id)
    )
    account = result.scalar_one_or_none()
    if not account:
        account = CreditAccount(workspace_id=workspace_id, balance=0)
        db.add(account)
        await db.flush()
    return account


async def get_balance(workspace_id: uuid.UUID, db: AsyncSession) -> int:
    account = await get_or_create_account(workspace_id, db)
    return account.balance


async def check_balance(workspace_id: uuid.UUID, required: int, db: AsyncSession) -> None:
    balance = await get_balance(workspace_id, db)
    if balance < required:
        raise InsufficientCreditsError(balance, required)


async def deduct_credits(
    workspace_id: uuid.UUID,
    amount: int,
    description: str,
    db: AsyncSession,
    generated_content_id: uuid.UUID | None = None,
) -> int:
    result = await db.execute(
        update(CreditAccount)
        .where(
            CreditAccount.workspace_id == workspace_id,
            CreditAccount.balance >= amount,
        )
        .values(balance=CreditAccount.balance - amount, updated_at=utcnow())
        .returning(CreditAccount.id, CreditAccount.balance)
    )
    row = result.one_or_none()
    if row is None:
        balance = await get_balance(workspace_id, db)
        raise InsufficientCreditsError(balance, amount)

    account_id, new_balance = row
    tx = CreditTransaction(
        workspace_id=workspace_id,
        account_id=account_id,
        amount=-amount,
        type=TransactionType.usage,
        description=description,
        balance_after=new_balance,
        generated_content_id=generated_content_id,
    )
    db.add(tx)
    return new_balance


async def add_credits(
    workspace_id: uuid.UUID,
    amount: int,
    description: str,
    db: AsyncSession,
    stripe_payment_intent: str | None = None,
) -> int:
    account = await get_or_create_account(workspace_id, db)
    account.balance += amount
    account.updated_at = utcnow()

    tx = CreditTransaction(
        workspace_id=workspace_id,
        account_id=account.id,
        amount=amount,
        type=TransactionType.purchase,
        description=description,
        balance_after=account.balance,
        stripe_payment_intent=stripe_payment_intent,
    )
    db.add(tx)
    return account.balance
