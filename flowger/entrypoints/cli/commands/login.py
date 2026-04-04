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

    provider = create_bank_provider(settings)

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
