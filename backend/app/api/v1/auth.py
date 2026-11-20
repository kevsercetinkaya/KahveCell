import hmac
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_token_pair,
    get_current_user,
    hash_otp,
    hash_refresh_token,
)
from app.db.session import get_db
from app.models import AuthSession, OtpChallenge, User
from app.models.auth import utc_now
from app.models.enums import UserRole
from app.schemas.auth import (
    AuthTokenResponse,
    LogoutResponse,
    OtpRequestResponse,
    PhoneRequest,
    RefreshRequest,
    RegisterRequest,
    UserResponse,
    VerifyOtpRequest,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _issue_otp(
    database: Session,
    phone_number: str,
    purpose: str,
    full_name: str | None = None,
    email: str | None = None,
) -> OtpRequestResponse:
    now = utc_now()
    window_start = now - timedelta(minutes=settings.otp_rate_window_minutes)
    recent_requests = database.scalar(
        select(func.count(OtpChallenge.id)).where(
            OtpChallenge.phone_number == phone_number,
            OtpChallenge.created_at >= window_start,
        )
    )
    if recent_requests >= settings.otp_rate_limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many OTP requests. Try again later.",
        )

    database.execute(
        update(OtpChallenge)
        .where(
            OtpChallenge.phone_number == phone_number,
            OtpChallenge.consumed_at.is_(None),
        )
        .values(consumed_at=now)
    )
    database.add(
        OtpChallenge(
            phone_number=phone_number,
            purpose=purpose,
            code_hash=hash_otp(phone_number, settings.otp_fixed_code),
            full_name=full_name,
            email=email,
            created_at=now,
            expires_at=now + timedelta(minutes=settings.otp_expiry_minutes),
        )
    )
    database.commit()
    return OtpRequestResponse(
        message=f"Simulated OTP sent. Use code {settings.otp_fixed_code}.",
        expires_in_seconds=settings.otp_expiry_minutes * 60,
    )


@router.post(
    "/register",
    response_model=OtpRequestResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Register with a phone number",
)
def register(
    request: RegisterRequest,
    database: Session = Depends(get_db),
) -> OtpRequestResponse:
    existing_user = database.scalar(
        select(User.id).where(User.phone_number == request.phone_number)
    )
    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Phone number is already registered. Use login instead.",
        )

    return _issue_otp(
        database,
        request.phone_number,
        purpose="REGISTER",
        full_name=request.full_name.strip(),
        email=request.email,
    )


@router.post(
    "/login",
    response_model=OtpRequestResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Request a passwordless login OTP",
)
def login(
    request: PhoneRequest,
    database: Session = Depends(get_db),
) -> OtpRequestResponse:
    user_exists = database.scalar(
        select(User.id).where(User.phone_number == request.phone_number)
    )
    if user_exists is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Phone number is not registered. Register first.",
        )
    return _issue_otp(database, request.phone_number, purpose="LOGIN")


@router.post(
    "/verify-otp",
    response_model=AuthTokenResponse,
    summary="Verify OTP and create a session",
)
def verify_otp(
    request: VerifyOtpRequest,
    database: Session = Depends(get_db),
) -> AuthTokenResponse:
    now = utc_now()
    challenge = database.scalar(
        select(OtpChallenge)
        .where(
            OtpChallenge.phone_number == request.phone_number,
            OtpChallenge.consumed_at.is_(None),
            OtpChallenge.expires_at > now,
        )
        .order_by(OtpChallenge.created_at.desc(), OtpChallenge.id.desc())
        .limit(1)
    )
    if challenge is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active OTP challenge. Request a new code.",
        )
    if challenge.attempt_count >= settings.otp_max_attempts:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many verification attempts. Request a new code.",
        )

    submitted_hash = hash_otp(request.phone_number, request.code)
    if not hmac.compare_digest(challenge.code_hash, submitted_hash):
        challenge.attempt_count += 1
        database.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP code.",
        )

    if challenge.purpose == "REGISTER":
        user = database.scalar(
            select(User).where(User.phone_number == request.phone_number)
        )
        if user is not None:
            challenge.consumed_at = now
            database.commit()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Phone number is already registered. Use login instead.",
            )
        user = User(
            phone_number=request.phone_number,
            full_name=challenge.full_name or request.phone_number,
            email=challenge.email,
            role=UserRole.CUSTOMER,
        )
        database.add(user)
        database.flush()
    else:
        user = database.scalar(
            select(User).where(User.phone_number == request.phone_number)
        )
        if user is None:
            challenge.consumed_at = now
            database.commit()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User no longer exists. Register again.",
            )

    challenge.consumed_at = now
    token_data = create_token_pair(database, user)
    database.commit()
    database.refresh(user)
    return AuthTokenResponse(**token_data, user=UserResponse.model_validate(user))


@router.post(
    "/refresh",
    response_model=AuthTokenResponse,
    summary="Rotate the refresh token and issue a new access token",
)
def refresh_tokens(
    request: RefreshRequest,
    database: Session = Depends(get_db),
) -> AuthTokenResponse:
    now = utc_now()
    session = database.scalar(
        select(AuthSession).where(
            AuthSession.refresh_token_hash == hash_refresh_token(request.refresh_token)
        )
    )
    if session is None or session.revoked_at is not None or session.expires_at <= now:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token is invalid, expired or already used.",
        )

    user = database.get(User, session.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer exists.",
        )

    session.revoked_at = now
    token_data = create_token_pair(database, user)
    database.commit()
    return AuthTokenResponse(**token_data, user=UserResponse.model_validate(user))


@router.post("/logout", response_model=LogoutResponse)
def logout(
    request: RefreshRequest,
    database: Session = Depends(get_db),
) -> LogoutResponse:
    session = database.scalar(
        select(AuthSession).where(
            AuthSession.refresh_token_hash == hash_refresh_token(request.refresh_token)
        )
    )
    if session is not None and session.revoked_at is None:
        session.revoked_at = utc_now()
        database.commit()
    return LogoutResponse(message="Session closed.")


@router.get("/me", response_model=UserResponse, summary="Return the signed-in user")
def read_current_user(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    return UserResponse.model_validate(current_user)