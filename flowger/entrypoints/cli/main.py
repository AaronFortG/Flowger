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
        typer.secho(f"Configuration error: {e!r}", fg=typer.colors.RED)
        raise typer.Exit(1)


@app.command()
def login(
    bank: str = typer.Option(None, help="Bank name (e.g., 'Imagin')"),
    country: str = typer.Option(None, help="Country code (e.g., 'ES')"),
) -> None:
    """Generate an authorization URL to connect a bank account."""
    settings = get_settings()
    init_db(settings.database_path)

    bank = bank or settings.default_bank
    country = country or settings.default_country

    provider = _create_bank_provider(settings)

    typer.echo(f"Requesting authorization for {bank} ({country})...")
    url = provider.start_authorization(
        bank_name=bank,
        country=country,
        redirect_url=settings.default_redirect_url,
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
    bank: str = typer.Option(None, help="Bank name used during login"),
    country: str = typer.Option(None, help="Country code used during login"),
) -> None:
    """Exchange the redirect code for a session and persist it locally."""
    settings = get_settings()
    init_db(settings.database_path)

    bank = bank or settings.default_bank
    country = country or settings.default_country

    provider = _create_bank_provider(settings)
    session_repo = SqliteSessionRepository(settings.database_path)

    account_repo = SqliteAccountRepository(settings.database_path)

    typer.echo(f"Authorizing session for {bank} ({country})...")
    session, accounts = provider.authorize_session(code=code, bank_name=bank, country=country)
    
    session_repo.save_session(session)
    account_repo.save_accounts(accounts)

    typer.secho(
        f"Session authorized and {len(accounts)} accounts saved. Session ID: {session.session_id}",
        fg=typer.colors.GREEN,
    )

@app.command()
def accounts() -> None:
    """List all accounts stored in the local database."""
    settings = get_settings()
    init_db(settings.database_path)
    account_repo = SqliteAccountRepository(settings.database_path)
    stored = account_repo.get_accounts()
    if not stored:
        typer.echo("No accounts found. Run `flowger authorize` first.")
        raise typer.Exit(0)
    typer.echo(f"{'ID':<40} {'IBAN':<26} {'Name':<20} Currency")
    typer.echo("-" * 96)
    for acc in stored:
        typer.echo(f"{acc.id:<40} {acc.iban:<26} {acc.name:<20} {acc.currency}")

@app.command()
def sync_transactions(
    bank: str = typer.Option(None, help="Bank name to sync transactions for"),
    country: str = typer.Option(None, help="Country code"),
) -> None:
    """Fetch transactions for all synced accounts and persist them locally."""
    settings = get_settings()
    init_db(settings.database_path)

    bank = bank or settings.default_bank
    country = country or settings.default_country

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
    output: str = typer.Option(None, help="Path to the output CSV file"),
) -> None:
    """Export transactions for a specific account to a CSV file."""
    settings = get_settings()
    init_db(settings.database_path)

    output = output or settings.default_export_file

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
