from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    """Application settings loaded from environment variables and root .env file."""

    model_config = SettingsConfigDict(
        env_file=str(ROOT_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Nexora Enterprise Data Intelligence Platform"
    app_env: str = "development"
    app_version: str = "0.2.0"
    log_level: str = "INFO"

    database_url: str = "postgresql+psycopg://nexora_user:nexora_local_dev_password_change_me@localhost:5432/nexora_db"
    test_database_url: str = "postgresql+psycopg://nexora_user:nexora_local_dev_password_change_me@localhost:5432/nexora_test_db"

    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    jwt_secret_key: str = "nexora_local_dev_jwt_secret_key_change_in_production_min_32_chars"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 120
    owner_email: str = "owner@nexora.local"

    max_upload_size_mb: int = 10
    max_export_rows: int = 50000

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
