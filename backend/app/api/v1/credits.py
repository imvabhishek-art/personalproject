import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.db.models.workspace import Workspace, WorkspaceMember, MemberRole
from app.db.models.credit import CreditAccount, CreditTransaction
from app.dependencies import get_workspace, require_role
from app.services.credit import get_or_create_account
from app.schemas.credit import CreditBalanceResponse, CreditTransactionResponse, CheckoutRequest, CheckoutResponse
from app.config import get_settings

router = APIRouter(prefix="/workspaces", tags=["credits"])

CREDIT_PACKAGES = {
    "100": ("100 Credits", 100),
    "500": ("500 Credits", 500),
    "2000": ("2000 Credits", 2000),
}


@router.get("/{workspace_id}/credits/balance", response_model=CreditBalanceResponse)
async def get_balance(
    workspace: Annotated[Workspace, Depends(get_workspace)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    account = await get_or_create_account(workspace.id, db)
    return CreditBalanceResponse(balance=account.balance, workspace_id=workspace.id)


@router.get("/{workspace_id}/credits/history", response_model=list[CreditTransactionResponse])
async def get_history(
    workspace: Annotated[Workspace, Depends(get_workspace)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = 50,
    offset: int = 0,
):
    result = await db.execute(
        select(CreditTransaction)
        .where(CreditTransaction.workspace_id == workspace.id)
        .order_by(CreditTransaction.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return result.scalars().all()


@router.post("/{workspace_id}/credits/checkout", response_model=CheckoutResponse)
async def create_checkout(
    body: CheckoutRequest,
    workspace: Annotated[Workspace, Depends(get_workspace)],
    member: Annotated[WorkspaceMember, Depends(require_role(MemberRole.owner))],
):
    settings = get_settings()
    if body.package not in CREDIT_PACKAGES:
        raise HTTPException(400, f"Invalid package. Choose from: {list(CREDIT_PACKAGES.keys())}")

    price_id_map = {
        "100": settings.stripe_price_id_100,
        "500": settings.stripe_price_id_500,
        "2000": settings.stripe_price_id_2000,
    }
    price_id = price_id_map[body.package]
    if not price_id:
        raise HTTPException(500, "Stripe price not configured")

    import stripe
    stripe.api_key = settings.stripe_secret_key

    session = stripe.checkout.Session.create(
        mode="payment",
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=f"{settings.frontend_url}/dashboard/credits?success=1&workspace={workspace.id}",
        cancel_url=f"{settings.frontend_url}/dashboard/credits?cancelled=1",
        metadata={"workspace_id": str(workspace.id), "credit_package": body.package},
    )
    return CheckoutResponse(checkout_url=session.url)
