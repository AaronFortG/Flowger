import typer

from flowger.infrastructure.config import get_settings
from flowger.infrastructure.sqlite import SqliteAccountRepository, init_db


def accounts(
    bank: str | None = typer.Option(None, help="Filter accounts by bank name"),
    country: str | None = typer.Option(None, help="Filter accounts by country code"),
) -> None:
    """List accounts stored in the local database, optionally filtered by scope."""
    settings = get_settings()
    init_db(settings.database_path)
    account_repo = SqliteAccountRepository(settings.database_path)
    stored = account_repo.get_accounts(bank_name=bank, country=country)

    if len(stored) == 0:
        parts = []
        if bank is not None and len(bank.strip()) > 0:
            parts.append(bank)
        if country is not None and len(country.strip()) > 0:
            parts.append(f"({country})" if (bank is not None and len(bank.strip()) > 0) else country)
        scope_str = f" for {' '.join(parts)}" if len(parts) > 0 else ""

        typer.echo(f"No accounts found{scope_str}. Run `flowger setup` first.")
        raise typer.Exit(0)

    typer.echo(f"{'ID':<40} {'IBAN':<26} {'Name':<20} Currency")
    typer.echo("-" * 96)
    for acc in stored:
        typer.echo(f"{acc.id:<40} {acc.iban:<26} {acc.name:<20} {acc.currency}")
