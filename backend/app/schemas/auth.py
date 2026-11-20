import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import UserRole


class PhoneRequest(BaseModel):
    phone_number: str = Field(min_length=9, max_length=15, pattern=r"^\+?[1-9]\d{7,14}$")

    @field_validator("phone_number", mode="before")
    @classmethod
    def normalize_phone_number(cls, value: object) -> object:
        if isinstance(value, str):
            return re.sub(r"[\s()-]", "", value)
        return value


class RegisterRequest(PhoneRequest):
    full_name: str = Field(min_length=2, max_length=100)
    email: str | None = Field(default=None, max_length=255)


class VerifyOtpRequest(PhoneRequest):
    code: str = Field(min_length=4, max_length=4, pattern=r"^\d{4}$")


class OtpRequestResponse(BaseModel):
    message: str
    expires_in_seconds: int


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    phone_number: str
    full_name: str
    email: str | None
    role: UserRole
    created_at: datetime


class AuthTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=32, max_length=256)


class LogoutResponse(BaseModel):
    message: str