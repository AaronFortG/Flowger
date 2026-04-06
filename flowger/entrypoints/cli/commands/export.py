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
    output = (
        output
        if (output is not None and len(output.strip()) > 0)
        else settings.default_export_file
    )
    bank, country = validate_bank_country(
        bank if (bank is not None and len(bank.strip()) > 0) else settings.default_bank,
        country if (country is not None and len(country.strip()) > 0) else settings.default_country,
    )
    init_db(settings.database_path)

    transaction_repo = SqliteTransactionRepository(settings.database_path)
    exporter = ActualCsvExporter(delimiter=delimiter, safe=safe)

    # Validate that the requested account exists somewhere (accounts or transactions table)
    account_repo = SqliteAccountRepository(settings.database_path)
    accounts = account_repo.get_accounts(bank_name=bank, country=country)
    account_exists = any(acc.id == account_id for acc in accounts)

    has_transactions = False
    if account_exists is False:
        # Fallback: check if transactions exist even if account metadata is missing
        has_transactions = transaction_repo.has_transactions(account_id, bank, country)

    if (account_exists is False and has_transactions is False):
        typer.secho(
            f"Error: Account ID '{account_id}' not found for {bank} ({country}).\n",
            fg=typer.colors.RED,
        )
        if len(accounts) > 0:
            typer.echo("Available accounts for this bank/country:")
            for a in accounts:
                typer.echo(f"  - {a.id} ({a.name} - {a.iban})")
        else:
            typer.echo(
                "No records for this bank/country found in the local database.\n"
                "Please run `flowger setup` first to authorize your accounts."
            )
        raise typer.Exit(1)

    use_case = ExportTransactionsUseCase(
        transaction_repository=transaction_repo,
        export_service=exporter,
    )

    typer.echo(f"Exporting transactions for account {account_id} ({bank}/{country}) to {output}...")
    count = use_case.execute(
        account_id=account_id,
        bank_name=bank,
        country=country,
        output_path=output,
        new_only=new_only,
    )

    if count > 0:
        typer.secho(
            f"Export complete. {count} transaction(s) saved to {output}.",
            fg=typer.colors.GREEN,
        )
    else:
        msg = f"No {'new ' if new_only is True else ''}transactions found for account {account_id}."
        typer.secho(msg, fg=typer.colors.YELLOW)
