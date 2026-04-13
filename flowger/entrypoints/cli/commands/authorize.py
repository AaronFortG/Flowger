import typer

from flowger.application.authorize_session import AuthorizeSessionUseCase
from flowger.entrypoints.cli.helpers import (
    create_bank_provider,
    get_effective_value,
    validate_bank_country,
)
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
    # Resolve bank/country: CLI flag > Docker env (BANK/COUNTRY) > .env defaults
    resolved_bank = get_effective_value(bank, settings.bank) or settings.default_bank
    resolved_country = get_effective_value(country, settings.country) or settings.default_country
    bank, country = validate_bank_country(resolved_bank, resolved_country)
    init_db(settings.database_path)

    with create_bank_provider(settings) as provider:
        typer.echo(f"Authorizing session for {bank} ({country})...")
        use_case = AuthorizeSessionUseCase(
            provider=provider,
            session_repository=SqliteSessionRepository(settings.database_path),
            account_repository=SqliteAccountRepository(settings.database_path),
        )
        session, accounts = use_case.execute(code=code, bank_name=bank, country=country)

        typer.secho(
            f"Session authorized and {len(accounts)} accounts saved. "
            f"Session ID: {session.session_id}",
            fg=typer.colors.GREEN,
        )
