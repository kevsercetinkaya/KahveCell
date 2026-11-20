from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.plans import PLANS
from app.core.security import get_current_user
from app.db.session import get_db
from app.models import Subscription, User
from app.models.auth import utc_now
from app.models.enums import SubscriptionStatus
from app.schemas.subscription import (
    CancellationResponse,
    PaymentProcessResponse,
    PaymentRequest,
    PlanResponse,
    SubscriptionResponse,
)
from app.services.subscriptions import (
    get_active_subscription,
    process_subscription_payment,
    to_subscription_response,
)

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])


@router.get("/plans", response_model=list[PlanResponse], summary="List subscription plans")
def list_plans() -> list[PlanResponse]:
    return [PlanResponse(**plan.public_data()) for plan in PLANS.values()]


@router.get("/me", response_model=SubscriptionResponse, summary="Get active subscription")
def read_my_subscription(
    current_user: User = Depends(get_current_user),
    database: Session = Depends(get_db),
) -> SubscriptionResponse:
    subscription = get_active_subscription(database, current_user.id)
    if subscription is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription.",
        )
    return to_subscription_response(subscription)


@router.patch(
    "/me",
    response_model=PaymentProcessResponse,
    summary="Upgrade or downgrade the active plan",
)
def change_my_subscription(
    request: PaymentRequest,
    current_user: User = Depends(get_current_user),
    database: Session = Depends(get_db),
) -> PaymentProcessResponse:
    result = process_subscription_payment(
        database,
        current_user,
        request,
        require_active_subscription=True,
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription to change.",
        )
    return result


@router.delete(
    "/me",
    response_model=CancellationResponse,
    summary="Cancel the active subscription",
)
def cancel_my_subscription(
    current_user: User = Depends(get_current_user),
    database: Session = Depends(get_db),
) -> CancellationResponse:
    subscription = get_active_subscription(database, current_user.id)
    if subscription is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription to cancel.",
        )

    subscription.status = SubscriptionStatus.CANCELLED
    subscription.expires_at = utc_now()
    database.commit()
    database.refresh(subscription)
    return CancellationResponse(
        message="Subscription cancelled. No refund was processed.",
        subscription=to_subscription_response(subscription),
    )