from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Enable Banking credentials
    enablebanking_app_id: str = Field(
        ..., description="Application ID from Enable Banking"
    )
    enablebanking_key_path: str = Field(
        ..., description="Path to the RSA private key used for JWT signing"
    )

    # Bank scope (required for Docker daemon mode)
    bank: str | None = Field(
        None,
        description="Bank name for this container instance (e.g., 'Imagin')",
    )
    country: str | None = Field(
        None,
        description="Country code for this container instance (e.g., 'ES')",
    )

    # Daemon scheduling
    sync_cron: str = Field(
        "0 */6 * * *",
        description="Cron expression for scheduled syncs (default: every 6 hours)",
    )

    # Storage paths
    database_path: str = Field("flowger.db", description="Path to the local SQLite database file")

    # CLI fallbacks — if not provided in the command line, these are loaded from
    # environment variables (e.g., .env)
    default_bank: str | None = Field(None, description="Default bank name for CLI commands")
    default_country: str | None = Field(None, description="Default country code for CLI commands")
    default_redirect_url: str = Field(
        "https://enablebanking.com/ais/",
        description="OAuth redirect URL — must be registered in the Enable Banking application",
    )
    default_export_file: str = Field(
        "transactions.csv",
        description="Default output file path for the export command",
    )

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


def get_settings() -> Settings:
    """Load and return settings."""
    return Settings()
