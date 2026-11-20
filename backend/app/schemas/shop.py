from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class ProductSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    price: Decimal
    is_available: bool


class ShopSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    address: str
    latitude: float
    longitude: float
    opening_hours: dict[str, object] | None
    products: list[ProductSummary]
    distance_km: float | None = None