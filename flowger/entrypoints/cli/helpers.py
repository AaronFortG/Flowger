from typing import overload

import typer

from flowger.infrastructure.config import Settings
from flowger.infrastructure.enable_banking.provider import EnableBankingProvider


def create_bank_provider(settings: Settings) -> EnableBankingProvider:
    """Helper to instantiate the BankProvider with current settings."""
    return EnableBankingProvider(
        app_id=settings.enablebanking_app_id,
        private_key_path=settings.enablebanking_key_path,
    )


@overload
def get_effective_value(val: str | None, default: str) -> str: ...


@overload
def get_effective_value(val: str | None, default: None) -> str | None: ...


@overload
def get_effective_value(val: str | None, default: str | None) -> str | None: ...


def get_effective_value(val: str | None, default: str | None) -> str | None:
    """Return stripped value if it has content, otherwise the default."""
    if val is not None and len(val.strip()) > 0:
        return val.strip()
    return default


def validate_bank_country(bank: str | None, country: str | None) -> tuple[str, str]:
    """Ensure bank and country are specified and normalized, otherwise exit with error."""
    # Normalize inputs (strip whitespace and handle None)
    normalized_bank = (bank if bank is not None else "").strip()
    normalized_country = (country if country is not None else "").strip()

    if len(normalized_bank) == 0 or len(normalized_country) == 0:
        typer.secho(
            "\nError: Bank and Country must be specified.\n\n"
            "  Docker:  set BANK and COUNTRY in your docker-compose.yml environment block.\n"
            "  Local:   use --bank and --country options, or set in your .env file as:\n"
            "             DEFAULT_BANK=...\n"
            "             DEFAULT_COUNTRY=...",
            fg=typer.colors.RED,
        )
        raise typer.Exit(1)
    return normalized_bank, normalized_country
