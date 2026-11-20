from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    jwt_secret_key: SecretStr = Field(min_length=32)
    otp_fixed_code: str = "1234"
    otp_expiry_minutes: int = 5
    otp_max_attempts: int = 5
    otp_rate_limit: int = 3
    otp_rate_window_minutes: int = 10
    access_token_minutes: int = 15
    refresh_token_days: int = 30

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()