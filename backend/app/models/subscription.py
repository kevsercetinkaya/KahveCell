from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, DateTime, Enum as SqlEnum, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.enums import SubscriptionPlan, SubscriptionStatus


class Subscription(Base):
    __tablename__ = "subscriptions"
    __table_args__ = (
        CheckConstraint(
            "remaining_credits >= -1",
            name="ck_subscriptions_remaining_credits",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    plan_type: Mapped[SubscriptionPlan] = mapped_column(
        SqlEnum(SubscriptionPlan, name="subscription_plan", native_enum=False),
    )
    remaining_credits: Mapped[int] = mapped_column(Integer)
    status: Mapped[SubscriptionStatus] = mapped_column(
        SqlEnum(SubscriptionStatus, name="subscription_status", native_enum=False),
        default=SubscriptionStatus.ACTIVE,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    user: Mapped[User] = relationship(back_populates="subscriptions")
    orders: Mapped[list[Order]] = relationship(back_populates="subscription")
    payment_transactions: Mapped[list[PaymentTransaction]] = relationship(
        back_populates="subscription",
    )