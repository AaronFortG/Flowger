import time
from datetime import datetime, timezone
from typing import Any

import typer
from croniter import croniter

from flowger.application.sync_transactions import SyncTransactionsUseCase
from flowger.entrypoints.cli.helpers import create_bank_provider, validate_bank_country
from flowger.infrastructure.config import get_settings
from flowger.infrastructure.sqlite import (
    SqliteAccountRepository,
    SqliteSessionRepository,
    SqliteTransactionRepository,
    init_db,
)


def daemon(
    bank: str | None = typer.Option(None, "--bank", help="Bank name to sync (overrides .env)"),
    country: str | None = typer.Option(None, "--country", help="Country code (overrides .env)"),
    cron: str = typer.Option(
        ..., "--cron", help="Cron expression for scheduling (e.g. '0 3 * * *')"
    ),
) -> None:
    """
    Run Flowger in daemon mode, syncing transactions on a schedule.
    """
    settings = get_settings()
    bank, country = validate_bank_country(
        bank or settings.default_bank, country or settings.default_country
    )
    init_db(settings.database_path)

    if not croniter.is_valid(cron):
        typer.secho(f"Error: Invalid cron expression '{cron}'", fg=typer.colors.RED)
        raise typer.Exit(1)

    typer.echo(f"Starting Flowger daemon for {bank} ({country}) with schedule: {cron}")

    # Fail fast if no accounts exist for the given scope
    account_repo = SqliteAccountRepository(settings.database_path)
    if not account_repo.get_accounts(bank_name=bank, country=country):
        typer.secho(
            f"Error: No accounts found for {bank} ({country}) in the local database.\n"
            "Please run `flowger setup` first to authorize your accounts.",
            fg=typer.colors.RED,
        )
        raise typer.Exit(1)

    # Seed the iterator once to prevent drift from re-calculating from "now"
    cron_iter = croniter(cron, datetime.now(timezone.utc))

    while True:
        try:
            next_run = cron_iter.get_next(datetime)
            now = datetime.now(timezone.utc)
            sleep_seconds = (next_run - now).total_seconds()

            if sleep_seconds > 0:
                typer.echo(
                    f"Next sync scheduled: {next_run.isoformat()} "
                    f"(sleeping {int(sleep_seconds)}s)"
                )
                time.sleep(sleep_seconds)

            typer.echo(f"\n[{datetime.now(timezone.utc).isoformat()}] Running scheduled sync...")
            if _run_sync(bank, country, settings):
                typer.echo("Sync completed successfully.")

        except KeyboardInterrupt:
            typer.echo("\nDaemon stopped by user.")
            break
        except Exception as e:
            typer.secho(f"\nDaemon error: {e}", fg=typer.colors.RED)
            typer.echo("Retrying in 60 seconds...")
            time.sleep(60)
            # Re-seed from now after an error to ensure we don't try to "catch up"
            # on multiple missed runs if the error persists for a long time.
            cron_iter = croniter(cron, datetime.now(timezone.utc))


def _run_sync(bank: str, country: str, settings: Any) -> bool:
    session_repo = SqliteSessionRepository(settings.database_path)
    session = session_repo.get_latest_session(bank_name=bank, country=country)

    if session is None:
        typer.secho(
            f"No session found for {bank} ({country}). Run setup first.",
            fg=typer.colors.RED,
        )
        return False

    account_repo = SqliteAccountRepository(settings.database_path)
    transaction_repo = SqliteTransactionRepository(settings.database_path)

    # Use bank/country filtering for accounts
    accounts = account_repo.get_accounts(bank_name=bank, country=country)

    if not accounts:
        typer.secho(
            f"No accounts found for {bank} ({country}). "
            "Sync aborted to avoid a no-op run.",
            fg=typer.colors.RED,
        )
        return False

    with create_bank_provider(settings) as provider:
        use_case = SyncTransactionsUseCase(
            provider=provider,
            account_repository=account_repo,
            transaction_repository=transaction_repo,
        )
        failures = use_case.execute(session_id=session.session_id, accounts=accounts)
        if failures:
            typer.secho(f"Sync completed with {len(failures)} failures.", fg=typer.colors.YELLOW)
            return False

    return True
