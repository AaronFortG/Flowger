"""Flowger Typer CLI entrypoint."""

import typer

from flowger.infrastructure.config import get_settings
from flowger.infrastructure.database import init_db
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
    country: str = typer.Option("ES", help="Country code (e.g., 'ES')")
) -> None:
    """Generate an authorization URL to connect a bank account."""
    settings = get_settings()
    
    # Initialize DB (just in case they haven't synced yet)
    init_db(settings.database_path)
    
    provider = EnableBankingProvider(
        app_id=settings.enablebanking_app_id,
        private_key_path=settings.enablebanking_key_path,
        environment=settings.enablebanking_environment,
    )
    
    typer.echo(f"Requesting authorization for {bank} ({country})....")
    url = provider.start_authorization(
        bank_name=bank, 
        country=country, 
        redirect_url="http://localhost:8000/callback"
    )
    
    typer.echo("\nAction Required! Open the following URL in your browser to authenticate:")
    typer.echo(f"\n{url}\n")
    typer.echo("Once authenticated, copy the redirect code parameter.")

if __name__ == "__main__":
    app()
