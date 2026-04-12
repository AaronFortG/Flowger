import uuid

import typer

from flowger.application.authorize_session import AuthorizeSessionUseCase
from flowger.application.sync_transactions import SyncTransactionsUseCase
from flowger.domain.exceptions import BankProviderError
from flowger.entrypoints.cli.helpers import (
    create_bank_provider,
    get_effective_value,
    validate_bank_country,
)
from flowger.infrastructure.config import get_settings
from flowger.infrastructure.sqlite import (
    SqliteAccountRepository,
    SqliteSessionRepository,
    SqliteTransactionRepository,
    init_db,
)


def setup(
    bank: str | None = typer.Option(None, help="Bank name (e.g., 'Imagin')"),
    country: str | None = typer.Option(None, help="Country code (e.g., 'ES')"),
) -> None:
    """
    Interactive first-time setup: authorize a bank account and run an initial sync.

    This replaces the separate login → authorize → sync flow.
    You will be prompted to open a URL in your browser and paste back the code.
    """
    settings = get_settings()
    # Resolve: CLI flag > Docker env (BANK/COUNTRY) > .env defaults
    resolved_bank = get_effective_value(bank, settings.bank) or settings.default_bank
    resolved_country = get_effective_value(country, settings.country) or settings.default_country
    bank, country = validate_bank_country(resolved_bank, resolved_country)
    init_db(settings.database_path)

    with create_bank_provider(settings) as provider:
        # Step 1: Generate auth URL (reuses the same provider.start_authorization path as login)
        typer.echo(f"\nSetting up {bank} ({country})...")
        random_state = uuid.uuid4().hex
        url = provider.start_authorization(
            bank_name=bank,
            country=country,
            redirect_url=settings.default_redirect_url,
            state=random_state,
        )

        typer.echo("\nOpen the following URL in your browser to authenticate:\n")
        typer.secho(url, fg=typer.colors.CYAN)
        typer.echo(
            "\nAfter logging in, you will be redirected to a URL containing '?code=...'."
            "\nCopy the value of the 'code' parameter from the address bar.\n"
        )

        # Step 2 & 3: Exchange code in a retry loop
        session_repo = SqliteSessionRepository(settings.database_path)
        account_repo = SqliteAccountRepository(settings.database_path)

        authorize_use_case = AuthorizeSessionUseCase(
            provider=provider,
            session_repository=session_repo,
            account_repository=account_repo,
        )

        while True:
            code = typer.prompt(
                "\nPaste your authorization code here (or leave empty to exit)",
                default="",
                show_default=False,
            )
            if len(code.strip()) == 0:
                typer.echo("Exiting setup.")
                raise typer.Exit()

            try:
                typer.echo("\nExchanging code for session...")
                session, accounts = authorize_use_case.execute(
                    code=code.strip(), bank_name=bank, country=country
                )
                break  # Success!
            except BankProviderError as e:
                typer.secho(
                    f"\nError: Authorization failed ({e}).\n"
                    "It's likely the code was pasted incorrectly or has expired.",
                    fg=typer.colors.RED,
                )
                if typer.confirm("Would you like to try again?") is False:
                    raise typer.Exit(1)

        typer.secho(
            f"✓ Session authorized. {len(accounts)} account(s) saved.",
            fg=typer.colors.GREEN,
        )

        # Step 4: Run initial sync — delegates to SyncTransactionsUseCase (same as `sync`)
        typer.echo("\nRunning initial transaction sync...")
        transaction_repo = SqliteTransactionRepository(settings.database_path)
        sync_use_case = SyncTransactionsUseCase(
            provider=provider,
            account_repository=account_repo,
            transaction_repository=transaction_repo,
        )
        failures = sync_use_case.execute(session_id=session.session_id, accounts=accounts)

        if len(failures) > 0:
            typer.secho(
                f"⚠ Sync completed with {len(failures)} failure(s).",
                fg=typer.colors.YELLOW,
            )
        else:
            typer.secho("✓ Initial sync complete.", fg=typer.colors.GREEN)

        # Step 5: Print account summary
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

        typer.echo(
            f"\nSetup complete! Use the account IDs above with:\n"
            f"  `flowger export --account-id <ID> --bank {bank} --country {country}`\n"
            f"to export transactions. If running via Docker, start the "
            f"services with `docker compose up -d`."
        )

        if len(failures) > 0:
            raise typer.Exit(1)
