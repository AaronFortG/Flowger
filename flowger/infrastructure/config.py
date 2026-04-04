from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Enable Banking configuration
    enablebanking_app_id: str = Field(..., description="Application ID from Enable Banking")
    enablebanking_environment: str = Field(
        ..., description="Target environment: SANDBOX or PRODUCTION"
    )
    enablebanking_key_path: str = Field(
        ..., description="Path to the RSA private key used for JWT signing"
    )

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


def get_settings() -> Settings:
    """Load and return settings."""
    return Settings()  # type: ignore[call-arg]
