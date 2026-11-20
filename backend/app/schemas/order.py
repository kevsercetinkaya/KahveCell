from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import OrderStatus


class OrderCreateRequest(BaseModel):
    shop_id: int = Field(gt=0)
    product_id: int = Field(gt=0)
    size: Literal["S", "M", "L"] = "M"
    sugar_level: int = Field(default=0, ge=0, le=5)
    milk_preference: str | None = Field(default=None, max_length=40)
    extra_shots: int = Field(default=0, ge=0, le=3)


class OrderQrPayload(BaseModel):
    order_id: str = Field(min_length=1, max_length=36)
    user_id: str = Field(min_length=1, max_length=36)
    shop_id: str = Field(min_length=1, max_length=36)
    created_at: str = Field(min_length=20, max_length=40)
    signature: str = Field(pattern=r"^[0-9a-f]{64}$")


class OrderResponse(BaseModel):
    id: int
    user_id: int
    shop_id: int
    shop_name: str
    product_id: int
    product_name: str
    subscription_id: int
    status: OrderStatus
    customizations: dict[str, object]
    created_at: datetime
    qr_payload: OrderQrPayload | None = None
    qr_image_data: str | None = None


class OrderSummaryResponse(BaseModel):
    id: int
    user_id: int
    shop_id: int
    shop_name: str
    product_id: int
    product_name: str
    subscription_id: int
    status: OrderStatus
    customizations: dict[str, object]
    created_at: datetime


class OrderStatusUpdateRequest(BaseModel):
    status: OrderStatus