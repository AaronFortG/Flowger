import time
import uuid
from datetime import datetime, timezone

import typer
from croniter import croniter

from flowger.application.sync_transactions import SyncTransactionsUseCase
from flowger.domain.account import Account
from flowger.domain.exceptions import BankProviderError
from flowger.entrypoints.cli.helpers import (
    create_bank_provider,
    get_effective_value,
    validate_bank_country,
)
from flowger.infrastructure.config import Settings, get_settings
from flowger.infrastructure.sqlite import (
    SqliteAccountRepository,
    SqliteSessionRepository,
    SqliteTransactionRepository,
    init_db,
)

# Seconds between polling checks during non-interactive setup
_POLL_INTERVAL = 10


def daemon(
    bank: str | None = typer.Option(None, "--bank", help="Bank name to sync (overrides .env)"),
    country: str | None = typer.Option(None, "--country", help="Country code (overrides .env)"),
    cron: str | None = typer.Option(None, "--cron", help="Cron expression for scheduling"),
) -> None:
    """
    Run Flowger in daemon mode, syncing transactions on a schedule.

    If no accounts exist for the given bank/country, this command will
    automatically guide you through the one-time setup (generate auth URL,
    exchange code, initial sync) before entering the daemon loop.
    """
    settings = get_settings()

    # Resolve bank/country: CLI flag > settings.bank (Docker env) > settings.default_bank (.env)
    resolved_bank = get_effective_value(bank, settings.bank) or settings.default_bank
    resolved_country = get_effective_value(country, settings.country) or settings.default_country
    bank, country = validate_bank_country(resolved_bank, resolved_country)

    # Resolve cron: CLI flag > settings.sync_cron (Docker env)
    resolved_cron = get_effective_value(cron, settings.sync_cron) or "0 */6 * * *"
    if croniter.is_valid(resolved_cron) is False:
        typer.secho(
            f"Error: Invalid cron expression '{resolved_cron}'", fg=typer.colors.RED
        )
        raise typer.Exit(1)

    init_db(settings.database_path)

    account_repo = SqliteAccountRepository(settings.database_path)

    # Check if we already have accounts for this bank/country
    existing_accounts = account_repo.get_accounts(bank_name=bank, country=country)

    if len(existing_accounts) == 0:
        # First run — bootstrap via interactive setup
        try:
            accounts = _run_setup(bank, country, settings)
        except BankProviderError as e:
            typer.secho(
                f"\nSetup failed: {e}\n\n"
                "This usually means your ENABLEBANKING_APP_ID or RSA private key is invalid\n"
                "or mismatched. Check that:\n"
                "  1. ENABLEBANKING_APP_ID matches your Enable Banking application.\n"
                "  2. The RSA key mounted at /keys/private.pem is the one registered there.\n"
                "  3. Your Enable Banking application is active and has AIS permissions.\n",
                fg=typer.colors.RED,
            )
            raise typer.Exit(1)

        if accounts is None:
            typer.secho(
                "\nSetup was not completed. The daemon cannot start without accounts.",
                fg=typer.colors.RED,
            )
            raise typer.Exit(1)
    else:
        accounts = existing_accounts
        typer.echo(f"Found {len(accounts)} account(s) for {bank} ({country}).")

    typer.echo(
        f"Starting Flowger daemon for {bank} ({country}) with schedule: {resolved_cron}"
    )

    # Seed the iterator once to prevent drift from re-calculating from "now"
    cron_iter = croniter(resolved_cron, datetime.now(timezone.utc))

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
            _run_sync(bank, country, settings)

        except KeyboardInterrupt:
            typer.echo("\nDaemon stopped by user.")
            break
        except Exception as e:
            typer.secho(f"\nDaemon error: {e}", fg=typer.colors.RED)
            typer.echo("Retrying in 60 seconds...")
            time.sleep(60)
            # Re-seed from now after an error to ensure we don't try to "catch up"
            # on multiple missed runs if the error persists for a long time.
            cron_iter = croniter(resolved_cron, datetime.now(timezone.utc))


def _run_setup(bank: str, country: str, settings: Settings) -> list[Account] | None:
    """
    First-time setup: generate auth URL, then poll the database until the
    user authorizes via `docker compose exec <service> flowger authorize --code <CODE>`.

    Always uses polling so it works regardless of detached/attached mode.
    """
    typer.secho(
        f"\nNo accounts found for {bank} ({country}). Starting first-time setup...\n",
        fg=typer.colors.YELLOW,
    )

    with create_bank_provider(settings) as provider:
        # Step 1: Generate auth URL
        random_state = uuid.uuid4().hex
        url = provider.start_authorization(
            bank_name=bank,
            country=country,
            redirect_url=settings.default_redirect_url,
            state=random_state,
        )

        typer.echo("Open the following URL in your browser to authenticate:\n")
        typer.secho(url, fg=typer.colors.CYAN)
        typer.echo(
            "\nAfter logging in, you will be redirected to a URL containing '?code=...'."
            "\nCopy the value of the 'code' parameter from the address bar.\n"
        )

        # Step 2: Authorize via docker compose exec — poll until accounts appear
        typer.echo("To complete setup, run this command in another terminal:\n")
        typer.secho(
            f"  docker compose exec flowger-{bank.lower()} flowger authorize --code <CODE>",
            fg=typer.colors.CYAN,
        )
        typer.echo(
            "\nThe daemon will detect the authorized account automatically and start syncing.\n"
        )

        account_repo = SqliteAccountRepository(settings.database_path)
        session_repo = SqliteSessionRepository(settings.database_path)

        while True:
            accounts = account_repo.get_accounts(bank_name=bank, country=country)
            if len(accounts) > 0:
                typer.secho(
                    "✓ Account detected. Proceeding with initial sync...\n",
                    fg=typer.colors.GREEN,
                )
                break

            time.sleep(_POLL_INTERVAL)
            typer.echo("  Waiting for authorization...")

        # Step 3: Run initial sync once accounts appear
        session = session_repo.get_latest_session(bank_name=bank, country=country)
        if session is not None:
            with create_bank_provider(settings) as fresh_provider:
                transaction_repo = SqliteTransactionRepository(settings.database_path)
                sync_use_case = SyncTransactionsUseCase(
                    provider=fresh_provider,
                    account_repository=account_repo,
                    transaction_repository=transaction_repo,
                )
                failures = sync_use_case.execute(
                    session_id=session.session_id, accounts=accounts
                )
                if len(failures) > 0:
                    typer.secho(
                        f"⚠ Initial sync completed with {len(failures)} failure(s).",
                        fg=typer.colors.YELLOW,
                    )
                else:
                    typer.secho("✓ Initial sync complete.", fg=typer.colors.GREEN)

        # Step 4: Print account summary
        typer.echo("\nYour authorized accounts:\n")
        typer.echo(
            f"{'Bank':<15} {'Country':<8} {'ID':<40} {'IBAN':<26} {'Name':<20} Currency"
        )
        typer.echo("-" * 120)
        for acc in accounts:
            typer.echo(
                f"{acc.bank_name:<15} {acc.country:<8} {acc.id:<40} "
                f"{acc.iban:<26} {acc.name:<20} {acc.currency}"
            )

        typer.secho(
            "\n✓ Setup complete. Daemon will now start syncing on schedule.",
            fg=typer.colors.GREEN,
        )

        return accounts


def _run_sync(bank: str, country: str, settings: Settings) -> bool:
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

    if len(accounts) == 0:
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
        if len(failures) > 0:
            typer.secho(f"Sync completed with {len(failures)} failures.", fg=typer.colors.YELLOW)
            return False

    typer.secho("Sync completed successfully.", fg=typer.colors.GREEN)
    return True
