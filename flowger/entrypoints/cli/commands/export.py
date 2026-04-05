import typer

from flowger.application.export_transactions import ExportTransactionsUseCase
from flowger.infrastructure.config import get_settings
from flowger.infrastructure.exporters.csv import ActualCsvExporter
from flowger.infrastructure.sqlite import SqliteTransactionRepository, init_db


def export(
    account_id: str = typer.Option(..., help="The UID of the account to export"),
    output: str | None = typer.Option(None, help="Path to the output CSV file"),
    delimiter: str = typer.Option(",", help="CSV value separator"),
    safe: bool = typer.Option(True, help="Sanitize fields (strip quotes and active delimiter)"),
    new_only: bool = typer.Option(
        False, "--new-only", help="Export only unexported transactions and mark them as exported"
    ),
) -> None:
    """Export transactions for a specific account to a CSV file."""
    settings = get_settings()
    init_db(settings.database_path)

    output = output or settings.default_export_file

    transaction_repo = SqliteTransactionRepository(settings.database_path)
    exporter = ActualCsvExporter(delimiter=delimiter, safe=safe)

    use_case = ExportTransactionsUseCase(
        transaction_repository=transaction_repo,
        export_service=exporter,
    )

    typer.echo(f"Exporting transactions for account {account_id} to {output}...")
    use_case.execute(
        account_id=account_id,
        output_path=output,
        new_only=new_only,
    )

    typer.secho(f"Export complete. File saved to {output}.", fg=typer.colors.GREEN)
