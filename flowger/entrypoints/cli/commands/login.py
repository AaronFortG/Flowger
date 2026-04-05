import uuid

import typer

from flowger.entrypoints.cli.helpers import create_bank_provider
from flowger.infrastructure.config import get_settings
from flowger.infrastructure.sqlite import init_db


def login(
    bank: str | None = typer.Option(None, help="Bank name (e.g., 'Imagin')"),
    country: str | None = typer.Option(None, help="Country code (e.g., 'ES')"),
) -> None:
    """Generate an authorization URL to connect a bank account."""
    settings = get_settings()
    init_db(settings.database_path)

    bank = bank or settings.default_bank
    country = country or settings.default_country

    with create_bank_provider(settings) as provider:
        typer.echo(f"Requesting authorization for {bank} ({country})...")

        # Generate a random state for the authorization request.
        # Since this is a local CLI, we don't strictly need to persist and validate it 
        # on the 'authorize' step to prevent CSRF, but generating a random one ensures
        # full compliance with OAuth best practices.
        random_state = uuid.uuid4().hex
        
        url = provider.start_authorization(
            bank_name=bank,
            country=country,
            redirect_url=settings.default_redirect_url,
            state=random_state,
        )
        typer.echo("\nOpen the following URL in your browser to authenticate:")
        typer.echo(f"\n{url}\n")
        typer.echo(
            "After authenticating, run:\n"
            "  flowger authorize --code <CODE> --bank <BANK> --country <COUNTRY>"
        )
