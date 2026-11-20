from datetime import timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session, selectinload

from app.core.security import get_current_user, require_roles
from app.db.session import get_db
from app.models import Order, Product, Shop, ShopStaff, Subscription, User
from app.models.auth import utc_now
from app.models.enums import OrderStatus, SubscriptionStatus, UserRole
from app.schemas.order import (
    OrderCreateRequest,
    OrderQrPayload,
    OrderResponse,
    OrderStatusUpdateRequest,
    OrderSummaryResponse,
)
from app.services.orders import (
    create_qr_image_data,
    create_qr_image_bytes,
    create_qr_payload,
    is_shop_staff,
    is_valid_order_transition,
    verify_qr_payload,
)

router = APIRouter(prefix="/orders", tags=["Orders"])


def _order_summary(order: Order) -> OrderSummaryResponse:
    return OrderSummaryResponse(
        id=order.id,
        user_id=order.user_id,
        shop_id=order.shop_id,
        shop_name=order.shop.name,
        product_id=order.product_id,
        product_name=order.product.name,
        subscription_id=order.subscription_id,
        status=order.status,
        customizations=order.customizations,
        created_at=order.created_at,
    )


def _order_with_qr(order: Order) -> OrderResponse:
    payload = create_qr_payload(order)
    return OrderResponse(
        **_order_summary(order).model_dump(),
        qr_payload=payload,
        qr_image_data=create_qr_image_data(payload),
    )


def _load_order(database: Session, order_id: int) -> Order | None:
    return database.scalar(
        select(Order)
        .options(selectinload(Order.shop), selectinload(Order.product))
        .where(Order.id == order_id)
    )


@router.post(
    "",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Place an order and spend one subscription credit",
)
def create_order(
    request: OrderCreateRequest,
    current_user: User = Depends(require_roles(UserRole.CUSTOMER)),
    database: Session = Depends(get_db),
) -> OrderResponse:
    shop = database.get(Shop, request.shop_id)
    if shop is None:
        raise HTTPException(status_code=404, detail="Dükkân bulunamadı.")

    product = database.get(Product, request.product_id)
    if product is None or product.shop_id != shop.id:
        raise HTTPException(
            status_code=404,
            detail="Seçilen ürün bu dükkânın menüsünde bulunamadı.",
        )
    if not product.is_available:
        raise HTTPException(status_code=409, detail="Bu ürün şu anda satışta değil.")

    now = utc_now()
    subscription = database.scalar(
        select(Subscription)
        .where(
            Subscription.user_id == current_user.id,
            Subscription.status == SubscriptionStatus.ACTIVE,
            Subscription.expires_at > now,
        )
        .order_by(Subscription.started_at.desc(), Subscription.id.desc())
        .limit(1)
    )
    if subscription is None:
        raise HTTPException(
            status_code=403,
            detail="Sipariş vermek için geçerli bir aktif aboneliğiniz olmalı.",
        )

    if subscription.remaining_credits != -1:
        credit_update = database.execute(
            update(Subscription)
            .where(
                Subscription.id == subscription.id,
                Subscription.remaining_credits > 0,
            )
            .values(remaining_credits=Subscription.remaining_credits - 1)
            .execution_options(synchronize_session=False)
        )
        if credit_update.rowcount != 1:
            raise HTTPException(
                status_code=409,
                detail="Aboneliğinizde kahve hakkı kalmadı.",
            )

    order = Order(
        user_id=current_user.id,
        shop_id=shop.id,
        product_id=product.id,
        subscription_id=subscription.id,
        status=OrderStatus.PENDING,
        customizations={
            "size": request.size,
            "sugar_level": request.sugar_level,
            "milk_preference": request.milk_preference,
            "extra_shots": request.extra_shots,
        },
        created_at=now.replace(tzinfo=timezone.utc),
    )
    database.add(order)
    database.flush()
    database.commit()
    database.refresh(order)
    database.refresh(subscription)
    return _order_with_qr(order)


@router.get("/history", response_model=list[OrderSummaryResponse], summary="Get my orders")
def read_order_history(
    current_user: User = Depends(get_current_user),
    database: Session = Depends(get_db),
) -> list[OrderSummaryResponse]:
    orders = database.scalars(
        select(Order)
        .options(selectinload(Order.shop), selectinload(Order.product))
        .where(Order.user_id == current_user.id)
        .order_by(Order.created_at.desc(), Order.id.desc())
    ).all()
    return [_order_summary(order) for order in orders]


@router.get(
    "/shop",
    response_model=list[OrderSummaryResponse],
    summary="Get orders for shops assigned to the signed-in shop owner",
)
def read_shop_orders(
    current_user: User = Depends(require_roles(UserRole.SHOP_OWNER)),
    database: Session = Depends(get_db),
) -> list[OrderSummaryResponse]:
    shop_ids = database.scalars(
        select(ShopStaff.shop_id).where(ShopStaff.user_id == current_user.id)
    ).all()
    if not shop_ids:
        return []

    orders = database.scalars(
        select(Order)
        .options(selectinload(Order.shop), selectinload(Order.product))
        .where(Order.shop_id.in_(shop_ids))
        .order_by(Order.created_at.asc(), Order.id.asc())
    ).all()
    return [_order_summary(order) for order in orders]


@router.get("/{order_id}", response_model=OrderResponse, summary="Get order details and QR code")
def read_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    database: Session = Depends(get_db),
) -> OrderResponse:
    order = _load_order(database, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Sipariş bulunamadı.")

    is_customer_order = order.user_id == current_user.id
    is_assigned_shop_owner = (
        current_user.role == UserRole.SHOP_OWNER
        and is_shop_staff(database, current_user.id, order.shop_id)
    )
    if not is_customer_order and not is_assigned_shop_owner:
        raise HTTPException(status_code=403, detail="Bu siparişi görüntüleme yetkiniz yok.")
    return _order_with_qr(order)


@router.get(
    "/{order_id}/qr.png",
    response_class=Response,
    responses={200: {"content": {"image/png": {}}}},
    summary="Download the signed pickup QR as a PNG image",
)
def download_order_qr(
    order_id: int,
    current_user: User = Depends(get_current_user),
    database: Session = Depends(get_db),
) -> Response:
    order = _load_order(database, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Sipariş bulunamadı.")

    is_customer_order = order.user_id == current_user.id
    is_assigned_shop_owner = (
        current_user.role == UserRole.SHOP_OWNER
        and is_shop_staff(database, current_user.id, order.shop_id)
    )
    if not is_customer_order and not is_assigned_shop_owner:
        raise HTTPException(status_code=403, detail="Bu siparişin QR kodunu görüntüleme yetkiniz yok.")

    payload = create_qr_payload(order)
    return Response(
        content=create_qr_image_bytes(payload),
        media_type="image/png",
        headers={"Content-Disposition": f'inline; filename="order-{order.id}-qr.png"'},
    )


@router.patch(
    "/{order_id}/status",
    response_model=OrderSummaryResponse,
    summary="Advance an assigned shop order through preparation",
)
def update_order_status(
    order_id: int,
    request: OrderStatusUpdateRequest,
    current_user: User = Depends(require_roles(UserRole.SHOP_OWNER)),
    database: Session = Depends(get_db),
) -> OrderSummaryResponse:
    order = _load_order(database, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Sipariş bulunamadı.")
    if not is_shop_staff(database, current_user.id, order.shop_id):
        raise HTTPException(status_code=403, detail="Bu dükkânın siparişlerini yönetme yetkiniz yok.")
    if not is_valid_order_transition(order.status, request.status):
        raise HTTPException(
            status_code=409,
            detail=f"Geçersiz durum geçişi: {order.status.value} → {request.status.value}.",
        )

    order.status = request.status
    database.commit()
    database.refresh(order)
    return _order_summary(order)


@router.post(
    "/verify-qr",
    response_model=OrderSummaryResponse,
    summary="Verify signed pickup QR and mark the order delivered",
)
def verify_pickup_qr(
    payload: OrderQrPayload,
    current_user: User = Depends(require_roles(UserRole.SHOP_OWNER)),
    database: Session = Depends(get_db),
) -> OrderSummaryResponse:
    if not verify_qr_payload(payload):
        raise HTTPException(status_code=400, detail="QR imzası geçersiz.")

    try:
        order_id = int(payload.order_id)
        user_id = int(payload.user_id)
        shop_id = int(payload.shop_id)
    except ValueError as error:
        raise HTTPException(status_code=400, detail="QR sipariş bilgisi geçersiz.") from error

    order = _load_order(database, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Sipariş bulunamadı.")
    if (order.user_id, order.shop_id) != (user_id, shop_id):
        raise HTTPException(status_code=400, detail="QR bu siparişle eşleşmiyor.")
    if not is_shop_staff(database, current_user.id, order.shop_id):
        raise HTTPException(status_code=403, detail="Bu dükkânda QR doğrulama yetkiniz yok.")
    if create_qr_payload(order) != payload:
        raise HTTPException(status_code=400, detail="QR içeriği sipariş kaydıyla eşleşmiyor.")
    if order.status != OrderStatus.READY:
        raise HTTPException(
            status_code=409,
            detail="Teslim için sipariş önce Hazır durumuna alınmalı.",
        )

    order.status = OrderStatus.DELIVERED
    database.commit()
    database.refresh(order)
    return _order_summary(order)