"""Flowger Typer CLI entrypoint."""

import typer

from flowger.application.export_transactions import ExportTransactionsUseCase
from flowger.application.sync_transactions import SyncTransactionsUseCase
from flowger.infrastructure.config import Settings, get_settings
from flowger.infrastructure.enable_banking.provider import EnableBankingProvider
from flowger.infrastructure.exporters.csv import ActualCsvExporter
from flowger.infrastructure.sqlite import (
    SqliteAccountRepository,
    SqliteSessionRepository,
    SqliteTransactionRepository,
    init_db,
)

DEFAULT_BANK = "Imagin"
DEFAULT_COUNTRY = "ES"
DEFAULT_REDIRECT_URL = "http://localhost:8000/callback"
DEFAULT_EXPORT_FILE = "transactions.csv"

app = typer.Typer(help="Flowger - Bank transaction synchronization utility.")


def _create_bank_provider(settings: Settings) -> EnableBankingProvider:
    """Helper to instantiate the BankProvider with current settings."""
    return EnableBankingProvider(
        app_id=settings.enablebanking_app_id,
        private_key_path=settings.enablebanking_key_path,
        environment=settings.enablebanking_environment,
    )


@app.command()
def config() -> None:
    """Verify application configuration is valid."""
    try:
        settings = get_settings()
        typer.echo("Configuration is valid.")
        typer.echo(f"Environment: {settings.enablebanking_environment}")
    except Exception as e:
        typer.secho(f"Configuration error: {e}", fg=typer.colors.RED)
        raise typer.Exit(1)


@app.command()
def login(
    bank: str = typer.Option(DEFAULT_BANK, help=f"Bank name (e.g., '{DEFAULT_BANK}')"),
    country: str = typer.Option(DEFAULT_COUNTRY, help=f"Country code (e.g., '{DEFAULT_COUNTRY}')"),
) -> None:
    """Generate an authorization URL to connect a bank account."""
    settings = get_settings()
    init_db(settings.database_path)

    provider = _create_bank_provider(settings)

    typer.echo(f"Requesting authorization for {bank} ({country})...")
    url = provider.start_authorization(
        bank_name=bank,
        country=country,
        redirect_url=DEFAULT_REDIRECT_URL,
    )
    typer.echo("\nOpen the following URL in your browser to authenticate:")
    typer.echo(f"\n{url}\n")
    typer.echo(
        "After authenticating, run:\n"
        "  flowger authorize --code <CODE> --bank <BANK> --country <COUNTRY>"
    )


@app.command()
def authorize(
    code: str = typer.Option(..., help="Authorization code from the redirect URL"),
    bank: str = typer.Option(DEFAULT_BANK, help="Bank name used during login"),
    country: str = typer.Option(DEFAULT_COUNTRY, help="Country code used during login"),
) -> None:
    """Exchange the redirect code for a session and persist it locally."""
    settings = get_settings()
    init_db(settings.database_path)

    provider = _create_bank_provider(settings)
    session_repo = SqliteSessionRepository(settings.database_path)

    typer.echo(f"Authorizing session for {bank} ({country})...")
    session = provider.authorize_session(code=code, bank_name=bank, country=country)
    session_repo.save_session(session)

    typer.secho(
        f"Session authorized and saved. Session ID: {session.session_id}",
        fg=typer.colors.GREEN,
    )


@app.command()
def sync(
    bank: str = typer.Option(DEFAULT_BANK, help="Bank name to sync"),
    country: str = typer.Option(DEFAULT_COUNTRY, help="Country code"),
) -> None:
    """Fetch accounts from the bank and persist them locally."""
    settings = get_settings()
    init_db(settings.database_path)

    session_repo = SqliteSessionRepository(settings.database_path)
    session = session_repo.get_latest_session(bank_name=bank, country=country)

    if session is None:
        typer.secho(
            f"No session found for {bank} ({country}). Run `flowger login` first.",
            fg=typer.colors.RED,
        )
        raise typer.Exit(1)

    provider = _create_bank_provider(settings)
    account_repo = SqliteAccountRepository(settings.database_path)

    typer.echo(f"Fetching accounts for {bank} ({country})...")
    accounts = provider.fetch_accounts(session_id=session.session_id)
    account_repo.save_accounts(accounts)

    typer.secho(f"Synced {len(accounts)} account(s).", fg=typer.colors.GREEN)


@app.command()
def sync_transactions(
    bank: str = typer.Option(DEFAULT_BANK, help="Bank name to sync transactions for"),
    country: str = typer.Option(DEFAULT_COUNTRY, help="Country code"),
) -> None:
    """Fetch transactions for all synced accounts and persist them locally."""
    settings = get_settings()
    init_db(settings.database_path)

    session_repo = SqliteSessionRepository(settings.database_path)
    session = session_repo.get_latest_session(bank_name=bank, country=country)

    if session is None:
        typer.secho(
            f"No session found for {bank} ({country}). Run `flowger login` first.",
            fg=typer.colors.RED,
        )
        raise typer.Exit(1)

    provider = _create_bank_provider(settings)
    account_repo = SqliteAccountRepository(settings.database_path)
    transaction_repo = SqliteTransactionRepository(settings.database_path)

    use_case = SyncTransactionsUseCase(
        provider=provider,
        account_repository=account_repo,
        transaction_repository=transaction_repo,
    )

    typer.echo(f"Syncing transactions for all accounts in {bank} ({country})...")
    use_case.execute(session_id=session.session_id)

    typer.secho("Transaction sync complete.", fg=typer.colors.GREEN)


@app.command()
def export(
    account_id: str = typer.Option(..., help="The UID of the account to export"),
    output: str = typer.Option(DEFAULT_EXPORT_FILE, help="Path to the output CSV file"),
) -> None:
    """Export transactions for a specific account to a CSV file."""
    settings = get_settings()
    init_db(settings.database_path)

    transaction_repo = SqliteTransactionRepository(settings.database_path)
    exporter = ActualCsvExporter()

    use_case = ExportTransactionsUseCase(
        transaction_repository=transaction_repo,
        export_service=exporter,
    )

    typer.echo(f"Exporting transactions for account {account_id} to {output}...")
    use_case.execute(account_id=account_id, output_path=output)

    typer.secho(f"Export complete. File saved to {output}.", fg=typer.colors.GREEN)


if __name__ == "__main__":
    app()
