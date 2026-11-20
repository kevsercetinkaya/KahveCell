import hashlib
import hmac
import secrets
from collections.abc import Callable
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models import AuthSession, User
from app.models.auth import utc_now
from app.models.enums import UserRole

bearer_scheme = HTTPBearer(auto_error=False)


def hash_otp(phone_number: str, code: str) -> str:
    secret = settings.jwt_secret_key.get_secret_value().encode("utf-8")
    message = f"{phone_number}:{code}".encode("utf-8")
    return hmac.new(secret, message, hashlib.sha256).hexdigest()


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_access_token(user: User, session_id: int) -> str:
    issued_at = datetime.now(timezone.utc)
    payload = {
        "sub": str(user.id),
        "sid": str(session_id),
        "role": user.role.value,
        "iat": issued_at,
        "exp": issued_at + timedelta(minutes=settings.access_token_minutes),
    }
    return jwt.encode(
        payload,
        settings.jwt_secret_key.get_secret_value(),
        algorithm="HS256",
    )


def create_token_pair(database: Session, user: User) -> dict[str, str | int]:
    now = utc_now()
    refresh_token = secrets.token_urlsafe(48)
    session = AuthSession(
        user_id=user.id,
        refresh_token_hash=hash_refresh_token(refresh_token),
        created_at=now,
        expires_at=now + timedelta(days=settings.refresh_token_days),
    )
    database.add(session)
    database.flush()

    return {
        "access_token": create_access_token(user, session.id),
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.access_token_minutes * 60,
    }


def unauthorized(detail: str = "Invalid or expired access token") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    database: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise unauthorized("Bearer token required")

    try:
        claims = jwt.decode(
            credentials.credentials,
            settings.jwt_secret_key.get_secret_value(),
            algorithms=["HS256"],
        )
        user_id = int(claims["sub"])
        session_id = int(claims["sid"])
    except (jwt.InvalidTokenError, KeyError, TypeError, ValueError) as error:
        raise unauthorized() from error

    session = database.get(AuthSession, session_id)
    now = utc_now()
    if (
        session is None
        or session.user_id != user_id
        or session.revoked_at is not None
        or session.expires_at <= now
    ):
        raise unauthorized("Session expired or revoked")

    user = database.get(User, user_id)
    if user is None:
        raise unauthorized("User no longer exists")
    return user


def require_roles(*allowed_roles: UserRole) -> Callable[..., User]:
    def role_dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient role",
            )
        return current_user

    return role_dependency