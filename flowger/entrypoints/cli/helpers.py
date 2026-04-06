import typer

from flowger.infrastructure.config import Settings
from flowger.infrastructure.enable_banking.provider import EnableBankingProvider


def create_bank_provider(settings: Settings) -> EnableBankingProvider:
    """Helper to instantiate the BankProvider with current settings."""
    return EnableBankingProvider(
        app_id=settings.enablebanking_app_id,
        private_key_path=settings.enablebanking_key_path,
    )


def validate_bank_country(bank: str | None, country: str | None) -> tuple[str, str]:
    """Ensure bank and country are specified, otherwise exit with error."""
    if not bank or not country:
        typer.secho(
            "\nError: Bank and Country must be specified.\n\n"
            "Use --bank and --country options, or set them in your .env file as:\n"
            "  DEFAULT_BANK=...\n"
            "  DEFAULT_COUNTRY=...",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(1)
    return bank, country
