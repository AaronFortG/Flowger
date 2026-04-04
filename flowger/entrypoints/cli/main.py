"""Flowger Typer CLI entrypoint."""

import typer

from flowger.infrastructure.config import get_settings
from flowger.infrastructure.database import (
    SqliteAccountRepository,
    SqliteSessionRepository,
    init_db,
)
from flowger.infrastructure.enable_banking.provider import EnableBankingProvider

app = typer.Typer(help="Flowger - Bank transaction synchronization utility.")


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
    bank: str = typer.Option("Imagin", help="Bank name (e.g., 'Imagin')"),
    country: str = typer.Option("ES", help="Country code (e.g., 'ES')"),
) -> None:
    """Generate an authorization URL to connect a bank account."""
    settings = get_settings()
    init_db(settings.database_path)

    provider = EnableBankingProvider(
        app_id=settings.enablebanking_app_id,
        private_key_path=settings.enablebanking_key_path,
        environment=settings.enablebanking_environment,
    )

    typer.echo(f"Requesting authorization for {bank} ({country})...")
    url = provider.start_authorization(
        bank_name=bank,
        country=country,
        redirect_url="http://localhost:8000/callback",
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
    bank: str = typer.Option("Imagin", help="Bank name used during login"),
    country: str = typer.Option("ES", help="Country code used during login"),
) -> None:
    """Exchange the redirect code for a session and persist it locally."""
    settings = get_settings()
    init_db(settings.database_path)

    provider = EnableBankingProvider(
        app_id=settings.enablebanking_app_id,
        private_key_path=settings.enablebanking_key_path,
        environment=settings.enablebanking_environment,
    )
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
    bank: str = typer.Option("Imagin", help="Bank name to sync"),
    country: str = typer.Option("ES", help="Country code"),
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

    provider = EnableBankingProvider(
        app_id=settings.enablebanking_app_id,
        private_key_path=settings.enablebanking_key_path,
        environment=settings.enablebanking_environment,
    )
    account_repo = SqliteAccountRepository(settings.database_path)

    typer.echo(f"Fetching accounts for {bank} ({country})...")
    accounts = provider.fetch_accounts(session_id=session.session_id)
    account_repo.save_accounts(accounts)

    typer.secho(f"Synced {len(accounts)} account(s).", fg=typer.colors.GREEN)


if __name__ == "__main__":
    app()
