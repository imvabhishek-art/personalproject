import uuid
from datetime import datetime
from pydantic import BaseModel
from app.db.models.credit import TransactionType


class CreditBalanceResponse(BaseModel):
    balance: int
    workspace_id: uuid.UUID


class CreditTransactionResponse(BaseModel):
    id: uuid.UUID
    amount: int
    type: TransactionType
    description: str
    balance_after: int
    created_at: datetime

    model_config = {"from_attributes": True}


class CheckoutRequest(BaseModel):
    package: str  # "100", "500", "2000"


class CheckoutResponse(BaseModel):
    checkout_url: str
