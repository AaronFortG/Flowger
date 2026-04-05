import time
from datetime import datetime, timezone

import typer
from croniter import croniter

from flowger.application.sync_transactions import SyncTransactionsUseCase
from flowger.entrypoints.cli.helpers import create_bank_provider
from flowger.infrastructure.config import get_settings
from flowger.infrastructure.sqlite import (
    SqliteAccountRepository,
    SqliteSessionRepository,
    SqliteTransactionRepository,
    init_db,
)

daemon_app = typer.Typer()


def daemon(
    bank: str = typer.Option(..., "--bank", help="Bank name to sync"),
    country: str = typer.Option(..., "--country", help="Country code"),
    cron: str = typer.Option(..., "--cron", help="Cron expression for scheduling (e.g. '0 3 * * *')"),
) -> None:
    """
    Run Flowger in daemon mode, syncing transactions on a schedule.
    """
    settings = get_settings()
    init_db(settings.database_path)

    typer.echo(f"Starting Flowger daemon for {bank} ({country}) with schedule: {cron}")

    while True:
        try:
            now = datetime.now(timezone.utc)
            iter = croniter(cron, now)
            next_run = iter.get_next(datetime)
            sleep_seconds = (next_run - now).total_seconds()

            if sleep_seconds > 0:
                typer.echo(f"Next sync scheduled for: {next_run.isoformat()} (sleeping {int(sleep_seconds)}s)")
                time.sleep(sleep_seconds)

            typer.echo(f"\n[{datetime.now(timezone.utc).isoformat()}] Running scheduled sync...")
            _run_sync(bank, country, settings)
            typer.echo("Sync completed successfully.")

        except KeyboardInterrupt:
            typer.echo("\nDaemon stopped by user.")
            break
        except Exception as e:
            typer.secho(f"\nDaemon error: {e}", fg=typer.colors.RED)
            typer.echo("Retrying in 60 seconds...")
            time.sleep(60)


def _run_sync(bank: str, country: str, settings: any) -> None:
    session_repo = SqliteSessionRepository(settings.database_path)
    session = session_repo.get_latest_session(bank_name=bank, country=country)

    if session is None:
        typer.secho(
            f"No session found for {bank} ({country}). Run setup first.",
            fg=typer.colors.RED,
        )
        return

    account_repo = SqliteAccountRepository(settings.database_path)
    transaction_repo = SqliteTransactionRepository(settings.database_path)

    # Use bank/country filtering for accounts
    accounts = account_repo.get_accounts(bank_name=bank, country=country)

    with create_bank_provider(settings) as provider:
        use_case = SyncTransactionsUseCase(
            provider=provider,
            account_repository=account_repo,
            transaction_repository=transaction_repo,
        )
        failures = use_case.execute(session_id=session.session_id, accounts=accounts)

    if failures:
        typer.secho(f"Sync completed with {len(failures)} failures.", fg=typer.colors.YELLOW)
