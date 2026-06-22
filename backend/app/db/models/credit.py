import uuid
from datetime import datetime
from sqlalchemy import Integer, String, Text, ForeignKey, Enum as SAEnum, DateTime
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base, TimestampMixin, utcnow
import enum


class TransactionType(str, enum.Enum):
    purchase = "purchase"
    usage = "usage"
    refund = "refund"


class CreditAccount(Base):
    __tablename__ = "credit_accounts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    balance: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="credit_account")
    transactions: Mapped[list["CreditTransaction"]] = relationship(
        "CreditTransaction", back_populates="account", cascade="all, delete-orphan"
    )


class CreditTransaction(Base):
    __tablename__ = "credit_transactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("credit_accounts.id", ondelete="CASCADE"), nullable=False
    )
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    type: Mapped[TransactionType] = mapped_column(SAEnum(TransactionType), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    balance_after: Mapped[int] = mapped_column(Integer, nullable=False)
    stripe_payment_intent: Mapped[str | None] = mapped_column(String(255), nullable=True)
    generated_content_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    account: Mapped["CreditAccount"] = relationship("CreditAccount", back_populates="transactions")
