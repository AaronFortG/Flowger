import typer

from flowger.application.export_transactions import ExportTransactionsUseCase
from flowger.entrypoints.cli.helpers import validate_bank_country
from flowger.infrastructure.config import get_settings
from flowger.infrastructure.exporters.csv import ActualCsvExporter
from flowger.infrastructure.sqlite import (
    SqliteAccountRepository,
    SqliteTransactionRepository,
    init_db,
)


def export(
    account_id: str = typer.Option(..., help="The UID of the account to export"),
    output: str | None = typer.Option(None, help="Path to the output CSV file"),
    delimiter: str = typer.Option(",", help="CSV value separator"),
    safe: bool = typer.Option(True, help="Sanitize fields (strip quotes and active delimiter)"),
    new_only: bool = typer.Option(
        False, "--new-only", help="Export only unexported transactions and mark them as exported"
    ),
    bank: str | None = typer.Option(None, help="The bank name for scoping"),
    country: str | None = typer.Option(None, help="The country code for scoping"),
) -> None:
    """Export transactions for a specific account to a CSV file."""
    settings = get_settings()
    init_db(settings.database_path)

    output = output or settings.default_export_file
    bank, country = validate_bank_country(
        bank or settings.default_bank, country or settings.default_country
    )

    transaction_repo = SqliteTransactionRepository(settings.database_path)
    exporter = ActualCsvExporter(delimiter=delimiter, safe=safe)

    # Validate that the account exists in the local database
    account_repo = SqliteAccountRepository(settings.database_path)
    if not account_repo.get_accounts(bank_name=bank, country=country):
        typer.secho(
            f"Error: No accounts found for {bank} ({country}).\n"
            "This account ID might exist for a different bank or country.",
            fg=typer.colors.RED,
        )
        raise typer.Exit(1)

    use_case = ExportTransactionsUseCase(
        transaction_repository=transaction_repo,
        export_service=exporter,
    )

    typer.echo(f"Exporting transactions for account {account_id} ({bank}/{country}) to {output}...")
    use_case.execute(
        account_id=account_id,
        bank_name=bank,
        country=country,
        output_path=output,
        new_only=new_only,
    )

    typer.secho(f"Export complete. File saved to {output}.", fg=typer.colors.GREEN)
