from datetime import timedelta
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.plans import PLANS, PlanDefinition
from app.db.session import SessionLocal
from app.models import PaymentTransaction, Subscription, User
from app.models.auth import utc_now
from app.models.enums import PaymentStatus, SubscriptionPlan, SubscriptionStatus
from app.schemas.subscription import (
    PaymentProcessResponse,
    PaymentRequest,
    SubscriptionResponse,
)

PAYCELL_SUCCESS_CARD = "4242424242424242"


def get_active_subscription(database: Session, user_id: int) -> Subscription | None:
    return database.scalar(
        select(Subscription)
        .where(
            Subscription.user_id == user_id,
            Subscription.status == SubscriptionStatus.ACTIVE,
        )
        .order_by(Subscription.started_at.desc(), Subscription.id.desc())
        .limit(1)
    )


def to_subscription_response(subscription: Subscription) -> SubscriptionResponse:
    plan = PLANS[subscription.plan_type]
    return SubscriptionResponse(
        id=subscription.id,
        plan_type=subscription.plan_type,
        status=subscription.status,
        monthly_price=plan.monthly_price,
        remaining_credits=subscription.remaining_credits,
        guest_credits=plan.guest_credits,
        priority_service=plan.priority_service,
        started_at=subscription.started_at,
        expires_at=subscription.expires_at,
    )


def process_subscription_payment(
    database: Session,
    user: User,
    request: PaymentRequest,
    *,
    require_active_subscription: bool = False,
) -> PaymentProcessResponse | None:
    plan: PlanDefinition = PLANS[request.subscription_plan]
    active_subscription = get_active_subscription(database, user.id)
    if require_active_subscription and active_subscription is None:
        return None

    now = utc_now()
    succeeded = request.card_number == PAYCELL_SUCCESS_CARD
    transaction_id = str(uuid4())

    if succeeded:
        if active_subscription is None:
            active_subscription = Subscription(
                user_id=user.id,
                plan_type=plan.plan_type,
                remaining_credits=plan.monthly_coffee_credits,
                status=SubscriptionStatus.ACTIVE,
                started_at=now,
                expires_at=now + timedelta(days=30),
            )
            database.add(active_subscription)
            database.flush()
        else:
            active_subscription.plan_type = plan.plan_type
            active_subscription.remaining_credits = plan.monthly_coffee_credits
            active_subscription.status = SubscriptionStatus.ACTIVE
            active_subscription.started_at = now
            active_subscription.expires_at = now + timedelta(days=30)

    payment = PaymentTransaction(
        transaction_id=transaction_id,
        user_id=user.id,
        subscription_id=(
            active_subscription.id if active_subscription is not None else None
        ),
        plan_type=plan.plan_type,
        amount_kurus=plan.monthly_price_kurus,
        currency="TRY",
        status=PaymentStatus.SUCCEEDED if succeeded else PaymentStatus.FAILED,
        failure_code=None if succeeded else "MOCK_CARD_DECLINED",
        created_at=now,
    )
    database.add(payment)
    database.commit()
    if active_subscription is not None:
        database.refresh(active_subscription)

    return PaymentProcessResponse(
        success=succeeded,
        message=(
            "Paycell simulation payment successful. Subscription is active."
            if succeeded
            else "Paycell simulation declined the card. Subscription was not changed."
        ),
        transaction_id=transaction_id,
        amount=plan.monthly_price,
        currency="TRY",
        status=payment.status,
        created_at=now,
        subscription=(
            to_subscription_response(active_subscription)
            if active_subscription is not None
            else None
        ),
    )