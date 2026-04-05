import typer

from flowger.entrypoints.cli.helpers import create_bank_provider
from flowger.infrastructure.config import get_settings
from flowger.infrastructure.sqlite import (
    SqliteAccountRepository,
    SqliteSessionRepository,
    init_db,
)


def authorize(
    code: str = typer.Option(..., help="Authorization code from the redirect URL"),
    bank: str | None = typer.Option(None, help="Bank name used during login"),
    country: str | None = typer.Option(None, help="Country code used during login"),
) -> None:
    """Exchange the redirect code for a session and persist it locally."""
    settings = get_settings()
    init_db(settings.database_path)

    bank = bank or settings.default_bank
    country = country or settings.default_country

    session_repo = SqliteSessionRepository(settings.database_path)
    account_repo = SqliteAccountRepository(settings.database_path)

    with create_bank_provider(settings) as provider:
        typer.echo(f"Authorizing session for {bank} ({country})...")
        session, accounts = provider.authorize_session(code=code, bank_name=bank, country=country)

        session_repo.save_session(session)
        account_repo.save_accounts(accounts)

        typer.secho(
            f"Session authorized and {len(accounts)} accounts saved. "
            f"Session ID: {session.session_id}",
            fg=typer.colors.GREEN,
        )
