from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Enable Banking configuration
    enablebanking_app_id: str = Field(..., description="Application ID from Enable Banking")
    enablebanking_key_path: str = Field(
        ..., description="Path to the RSA private key used for JWT signing"
    )

    database_path: str = Field("flowger.db", description="Path to the local SQLite database file")

    # CLI defaults — centralised here so they can be overridden via environment variables
    default_bank: str = Field("Imagin", description="Default bank name for CLI commands")
    default_country: str = Field("ES", description="Default country code for CLI commands")
    default_redirect_url: str = Field(
        "https://enablebanking.com/ais/",
        description="OAuth redirect URL — must be registered in the Enable Banking application",
    )
    default_export_file: str = Field(
        "transactions.csv",
        description="Default output file path for the export command",
    )

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


def get_settings() -> Settings:
    """Load and return settings."""
    return Settings()  # type: ignore[call-arg]
