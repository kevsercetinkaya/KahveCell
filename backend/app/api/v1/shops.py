import unicodedata
from math import asin, cos, radians, sin, sqrt

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.session import get_db
from app.models import Product, Shop
from app.schemas.shop import ProductSummary, ShopSummary

router = APIRouter(prefix="/shops", tags=["Shops"])


def _normalize_search(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    without_marks = "".join(character for character in decomposed if not unicodedata.combining(character))
    return without_marks.replace("ı", "i").strip()


def calculate_distance_km(
    origin_latitude: float,
    origin_longitude: float,
    destination_latitude: float,
    destination_longitude: float,
) -> float:
    latitude_delta = radians(destination_latitude - origin_latitude)
    longitude_delta = radians(destination_longitude - origin_longitude)
    haversine_value = (
        sin(latitude_delta / 2) ** 2
        + cos(radians(origin_latitude))
        * cos(radians(destination_latitude))
        * sin(longitude_delta / 2) ** 2
    )
    return 6371 * 2 * asin(sqrt(min(1.0, haversine_value)))


@router.get("", response_model=list[ShopSummary])
def list_shops(
    lat: float | None = Query(default=None, ge=-90, le=90),
    lng: float | None = Query(default=None, ge=-180, le=180),
    radius_km: float = Query(default=25, gt=0, le=200),
    q: str | None = Query(default=None, min_length=1, max_length=120),
    database: Session = Depends(get_db),
) -> list[ShopSummary]:
    if (lat is None) != (lng is None):
        raise HTTPException(
            status_code=400,
            detail="lat and lng must be provided together",
        )

    shops = database.scalars(
        select(Shop)
        .options(selectinload(Shop.products))
        .order_by(Shop.name)
    ).all()

    normalized_query = _normalize_search(q) if q else None
    results: list[ShopSummary] = []
    for shop in shops:
        if normalized_query:
            searchable_text = _normalize_search(f"{shop.name} {shop.address}")
            if normalized_query not in searchable_text:
                continue

        distance = None
        if lat is not None and lng is not None:
            distance = calculate_distance_km(lat, lng, shop.latitude, shop.longitude)
            if distance > radius_km:
                continue

        result = ShopSummary.model_validate(shop)
        results.append(result.model_copy(update={"distance_km": distance}))

    if lat is not None and lng is not None:
        results.sort(key=lambda shop: (shop.distance_km or 0, shop.name.casefold()))
    return results


@router.get("/{shop_id}", response_model=ShopSummary, summary="Get shop details and menu")
def read_shop(
    shop_id: int,
    database: Session = Depends(get_db),
) -> ShopSummary:
    shop = database.scalar(
        select(Shop)
        .options(selectinload(Shop.products))
        .where(Shop.id == shop_id)
    )
    if shop is None:
        raise HTTPException(status_code=404, detail="Shop not found.")
    return ShopSummary.model_validate(shop)


@router.get(
    "/{shop_id}/menu",
    response_model=list[ProductSummary],
    summary="Get a shop's menu",
)
def read_shop_menu(
    shop_id: int,
    database: Session = Depends(get_db),
) -> list[ProductSummary]:
    shop_exists = database.scalar(select(Shop.id).where(Shop.id == shop_id))
    if shop_exists is None:
        raise HTTPException(status_code=404, detail="Shop not found.")

    products = database.scalars(
        select(Product)
        .where(Product.shop_id == shop_id)
        .order_by(Product.name)
    ).all()
    return [ProductSummary.model_validate(product) for product in products]