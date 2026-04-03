"""Application configuration via environment variables or a .env file."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        # Ignore extra fields so adding new env vars does not break old code.
        extra="ignore",
    )

    # Database
    database_url: str = "sqlite:///./flowger.db"

    # Export
    exports_dir: Path = Path("./exports")

    # Logging
    log_level: str = "INFO"

    # Banking provider: "stub" (default for local dev) or "enable_banking"
    provider: str = "stub"

    # Enable Banking API (only required when provider="enable_banking")
    enable_banking_base_url: str = "https://api.enablebanking.com"
    enable_banking_api_key: str = ""


# Module-level singleton – imported by the CLI and infrastructure wiring.
# Tests create their own dependencies without relying on this object.
settings = Settings()
