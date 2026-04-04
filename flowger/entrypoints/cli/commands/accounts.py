import typer

from flowger.infrastructure.config import get_settings
from flowger.infrastructure.sqlite import SqliteAccountRepository, init_db


def accounts() -> None:
    """List all accounts stored in the local database."""
    settings = get_settings()
    init_db(settings.database_path)
    account_repo = SqliteAccountRepository(settings.database_path)
    stored = account_repo.get_accounts()
    
    if not stored:
        typer.echo("No accounts found. Run `flowger authorize` first.")
        raise typer.Exit(0)
        
    typer.echo(f"{'ID':<40} {'IBAN':<26} {'Name':<20} Currency")
    typer.echo("-" * 96)
    for acc in stored:
        typer.echo(f"{acc.id:<40} {acc.iban:<26} {acc.name:<20} {acc.currency}")
