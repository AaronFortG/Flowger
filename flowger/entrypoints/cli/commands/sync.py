import typer

from flowger.application.sync_transactions import SyncTransactionsUseCase
from flowger.entrypoints.cli.helpers import create_bank_provider, validate_bank_country
from flowger.infrastructure.config import get_settings
from flowger.infrastructure.sqlite import (
    SqliteAccountRepository,
    SqliteSessionRepository,
    SqliteTransactionRepository,
    init_db,
)


def sync(
    bank: str | None = typer.Option(None, help="Bank name to sync transactions for"),
    country: str | None = typer.Option(None, help="Country code"),
) -> None:
    """Fetch transactions for all synced accounts and persist them locally."""
    settings = get_settings()
    init_db(settings.database_path)

    bank, country = validate_bank_country(
        bank or settings.default_bank, country or settings.default_country
    )

    session_repo = SqliteSessionRepository(settings.database_path)
    session = session_repo.get_latest_session(bank_name=bank, country=country)

    if session is None:
        typer.secho(
            f"No session found for {bank} ({country}). "
            "Run `flowger login` AND `flowger authorize` first.",
            fg=typer.colors.RED,
        )
        raise typer.Exit(1)

    account_repo = SqliteAccountRepository(settings.database_path)
    transaction_repo = SqliteTransactionRepository(settings.database_path)

    accounts = account_repo.get_accounts(bank_name=bank, country=country)

    if not accounts:
        typer.secho(
            f"No accounts found for {bank} ({country}). "
            "Sync aborted to avoid a no-op run.",
            fg=typer.colors.RED,
        )
        raise typer.Exit(1)

    with create_bank_provider(settings) as provider:
        use_case = SyncTransactionsUseCase(
            provider=provider,
            account_repository=account_repo,
            transaction_repository=transaction_repo,
        )

        typer.echo(f"Syncing transactions for all accounts in {bank} ({country})...")
        failures = use_case.execute(session_id=session.session_id, accounts=accounts)

    if failures:
        typer.secho(f"\nCompleted with {len(failures)} failures:", fg=typer.colors.YELLOW)
        for account_id, error in failures:
            typer.echo(f"  - Account {account_id}: {error}")
        typer.secho("\nTransaction sync partially failed.", fg=typer.colors.RED)
        raise typer.Exit(1)

    typer.secho("Transaction sync complete.", fg=typer.colors.GREEN)
