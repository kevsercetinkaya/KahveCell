from dataclasses import dataclass
from decimal import Decimal

from app.models.enums import SubscriptionPlan


@dataclass(frozen=True)
class PlanDefinition:
    plan_type: SubscriptionPlan
    monthly_price_kurus: int
    monthly_coffee_credits: int
    guest_credits: int
    priority_service: bool

    @property
    def monthly_price(self) -> Decimal:
        return Decimal(self.monthly_price_kurus) / Decimal(100)

    def public_data(self) -> dict[str, object]:
        return {
            "plan_type": self.plan_type,
            "monthly_price": self.monthly_price,
            "currency": "TRY",
            "coffee_credits": None if self.monthly_coffee_credits == -1 else self.monthly_coffee_credits,
            "is_unlimited": self.monthly_coffee_credits == -1,
            "guest_credits": self.guest_credits,
            "priority_service": self.priority_service,
            "validity_days": 30,
            "eligible_at_all_shops": True,
        }


PLANS = {
    plan.plan_type: plan
    for plan in (
        PlanDefinition(SubscriptionPlan.STARTER, 8999, 10, 0, False),
        PlanDefinition(SubscriptionPlan.PREMIUM, 14999, 20, 2, False),
        PlanDefinition(SubscriptionPlan.UNLIMITED, 24999, -1, 5, True),
    )
}