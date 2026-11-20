from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum as SqlEnum,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.auth import utc_now
from app.models.enums import PaymentStatus, SubscriptionPlan


class PaymentTransaction(Base):
    __tablename__ = "payment_transactions"
    __table_args__ = (
        CheckConstraint("amount_kurus >= 0", name="ck_payment_amount_nonnegative"),
        Index("ix_payment_user_created", "user_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    transaction_id: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    subscription_id: Mapped[int | None] = mapped_column(
        ForeignKey("subscriptions.id", ondelete="SET NULL"),
        nullable=True,
    )
    plan_type: Mapped[SubscriptionPlan] = mapped_column(
        SqlEnum(SubscriptionPlan, name="payment_subscription_plan", native_enum=False),
    )
    amount_kurus: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(3), default="TRY")
    status: Mapped[PaymentStatus] = mapped_column(
        SqlEnum(PaymentStatus, name="payment_status", native_enum=False),
    )
    failure_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(), default=utc_now)

    user: Mapped[User] = relationship(back_populates="payment_transactions")
    subscription: Mapped[Subscription | None] = relationship(
        back_populates="payment_transactions",
    )