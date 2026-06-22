from fastapi import APIRouter, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import stripe

from app.config import get_settings
from app.db.session import AsyncSessionLocal
from app.db.models.workspace import Workspace
from app.services.credit import add_credits

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

CREDIT_PACKAGE_MAP = {"100": 100, "500": 500, "2000": 2000}


@router.post("/stripe")
async def stripe_webhook(request: Request):
    settings = get_settings()
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")

    try:
        event = stripe.Webhook.construct_event(payload, sig, settings.stripe_webhook_secret)
    except Exception:
        raise HTTPException(400, "Invalid signature")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        metadata = session.get("metadata", {})
        workspace_id_str = metadata.get("workspace_id")
        package = metadata.get("credit_package")
        payment_intent = session.get("payment_intent")

        if workspace_id_str and package:
            credits_to_add = CREDIT_PACKAGE_MAP.get(package, 0)
            if credits_to_add > 0:
                async with AsyncSessionLocal() as db:
                    async with db.begin():
                        import uuid
                        await add_credits(
                            workspace_id=uuid.UUID(workspace_id_str),
                            amount=credits_to_add,
                            description=f"Purchased {credits_to_add} credits",
                            db=db,
                            stripe_payment_intent=payment_intent,
                        )

    return {"status": "ok"}
