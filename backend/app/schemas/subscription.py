import re
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import PaymentStatus, SubscriptionPlan, SubscriptionStatus


class PlanResponse(BaseModel):
    plan_type: SubscriptionPlan
    monthly_price: Decimal
    currency: str
    coffee_credits: int | None
    is_unlimited: bool
    guest_credits: int
    priority_service: bool
    validity_days: int
    eligible_at_all_shops: bool


class PaymentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    subscription_plan: SubscriptionPlan
    card_number: str = Field(min_length=13, max_length=19, repr=False)

    @field_validator("card_number", mode="before")
    @classmethod
    def normalize_card_number(cls, value: object) -> object:
        if isinstance(value, str):
            return re.sub(r"[\s-]", "", value)
        return value

    @field_validator("card_number")
    @classmethod
    def allow_only_simulator_cards(cls, value: str) -> str:
        if value not in {"4242424242424242", "4000000000000002"}:
            raise ValueError("Only the documented Paycell simulation cards are accepted.")
        return value


class SubscriptionResponse(BaseModel):
    id: int
    plan_type: SubscriptionPlan
    status: SubscriptionStatus
    monthly_price: Decimal
    currency: str = "TRY"
    remaining_credits: int
    guest_credits: int
    priority_service: bool
    started_at: datetime
    expires_at: datetime


class PaymentProcessResponse(BaseModel):
    success: bool
    message: str
    transaction_id: str
    amount: Decimal
    currency: str
    status: PaymentStatus
    created_at: datetime
    subscription: SubscriptionResponse | None


class PaymentHistoryItem(BaseModel):
    transaction_id: str
    plan_type: SubscriptionPlan
    amount: Decimal
    currency: str
    status: PaymentStatus
    created_at: datetime


class CancellationResponse(BaseModel):
    message: str
    subscription: SubscriptionResponse