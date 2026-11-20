from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models import PaymentTransaction, User
from app.schemas.subscription import PaymentHistoryItem, PaymentProcessResponse, PaymentRequest
from app.services.subscriptions import process_subscription_payment

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post(
    "/process",
    response_model=PaymentProcessResponse,
    summary="Simulate Paycell payment and activate the selected plan",
)
def process_payment(
    request: PaymentRequest,
    current_user: User = Depends(get_current_user),
    database: Session = Depends(get_db),
) -> PaymentProcessResponse:
    result = process_subscription_payment(database, current_user, request)
    assert result is not None
    return result


@router.get(
    "/history",
    response_model=list[PaymentHistoryItem],
    summary="List the signed-in user's payment history",
)
def read_payment_history(
    limit: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    database: Session = Depends(get_db),
) -> list[PaymentHistoryItem]:
    payments = database.scalars(
        select(PaymentTransaction)
        .where(PaymentTransaction.user_id == current_user.id)
        .order_by(PaymentTransaction.created_at.desc(), PaymentTransaction.id.desc())
        .limit(limit)
    ).all()
    return [
        PaymentHistoryItem(
            transaction_id=payment.transaction_id,
            plan_type=payment.plan_type,
            amount=Decimal(payment.amount_kurus) / Decimal(100),
            currency=payment.currency,
            status=payment.status,
            created_at=payment.created_at,
        )
        for payment in payments
    ]