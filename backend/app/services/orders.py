import base64
import hashlib
import hmac
import io
import json
from datetime import datetime, timezone

import qrcode
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import AuthSession, Order, ShopStaff, Subscription, User
from app.models.enums import OrderStatus, SubscriptionStatus
from app.schemas.order import OrderQrPayload


def get_active_subscription(database: Session, user_id: int) -> Subscription | None:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    return database.scalar(
        select(Subscription)
        .where(
            Subscription.user_id == user_id,
            Subscription.status == SubscriptionStatus.ACTIVE,
            Subscription.expires_at > now,
        )
        .order_by(Subscription.started_at.desc(), Subscription.id.desc())
        .limit(1)
    )


def is_shop_staff(database: Session, user_id: int, shop_id: int) -> bool:
    assignment_id = database.scalar(
        select(ShopStaff.id).where(
            ShopStaff.user_id == user_id,
            ShopStaff.shop_id == shop_id,
        )
    )
    return assignment_id is not None


def _qr_signing_key() -> bytes:
    root_secret = settings.jwt_secret_key.get_secret_value().encode("utf-8")
    return hmac.new(root_secret, b"KahveCell:order-qr:v1", hashlib.sha256).digest()


def _order_created_at_iso(order: Order) -> str:
    created_at = order.created_at
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    return created_at.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _canonical_payload(payload: dict[str, str]) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def create_qr_payload(order: Order) -> OrderQrPayload:
    payload = {
        "order_id": str(order.id),
        "user_id": str(order.user_id),
        "shop_id": str(order.shop_id),
        "created_at": _order_created_at_iso(order),
    }
    signature = hmac.new(_qr_signing_key(), _canonical_payload(payload), hashlib.sha256)
    return OrderQrPayload(**payload, signature=signature.hexdigest())


def verify_qr_payload(payload: OrderQrPayload) -> bool:
    unsigned_payload = payload.model_dump(exclude={"signature"})
    expected_signature = hmac.new(
        _qr_signing_key(),
        _canonical_payload(unsigned_payload),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected_signature, payload.signature)


def create_qr_image_data(payload: OrderQrPayload) -> str:
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=7,
        border=4,
    )
    qr.add_data(
        json.dumps(
            payload.model_dump(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    qr.make(fit=True)
    image = qr.make_image(fill_color="#173c35", back_color="white")
    output = io.BytesIO()
    image.save(output, format="PNG")
    encoded_image = base64.b64encode(output.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded_image}"


def create_qr_image_bytes(payload: OrderQrPayload) -> bytes:
    image_data = create_qr_image_data(payload)
    return base64.b64decode(image_data.partition(",")[2])


def is_valid_order_transition(current: OrderStatus, requested: OrderStatus) -> bool:
    allowed_transitions = {
        OrderStatus.PENDING: {OrderStatus.ACCEPTED},
        OrderStatus.ACCEPTED: {OrderStatus.PREPARING},
        OrderStatus.PREPARING: {OrderStatus.READY},
    }
    return requested in allowed_transitions.get(current, set())