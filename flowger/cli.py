"""Typer CLI entrypoint for Flowger.

Commands:
  flowger accounts        – list locally stored accounts
  flowger discover        – pull account list from the provider and store it
  flowger sync <id>       – sync transactions for one account
  flowger sync-all        – sync transactions for all stored accounts
  flowger export <id>     – export one account's transactions to CSV
  flowger export-all      – export all accounts' transactions to CSV
"""

import logging
import sys
from pathlib import Path

import typer
from sqlmodel import Session

from flowger.application.use_cases import (
    export_account_transactions,
    sync_account_transactions,
)
from flowger.config import settings
from flowger.domain.ports import BankingProvider
from flowger.infrastructure.database import create_tables, make_engine
from flowger.infrastructure.repositories import SQLiteTransactionRepository

app = typer.Typer(
    help="Flowger – sync bank transactions into your ledger.",
    no_args_is_help=True,
)


# ------------------------------------------------------------------
# Provider factory (wiring layer – depends on config, not domain)
# ------------------------------------------------------------------


def _build_provider() -> BankingProvider:
    if settings.provider == "stub":
        from flowger.infrastructure.stub_provider import StubBankingProvider

        return StubBankingProvider()

    if settings.provider == "enable_banking":
        from flowger.infrastructure.enable_banking import EnableBankingProvider

        return EnableBankingProvider(
            base_url=settings.enable_banking_base_url,
            api_key=settings.enable_banking_api_key,
        )

    typer.echo(
        f"Unknown provider '{settings.provider}'. "
        "Set PROVIDER=stub or PROVIDER=enable_banking.",
        err=True,
    )
    raise typer.Exit(1)


def _get_session() -> Session:
    create_tables(settings.database_url)
    engine = make_engine(settings.database_url)
    return Session(engine)


# ------------------------------------------------------------------
# Commands
# ------------------------------------------------------------------


@app.command()
def accounts() -> None:
    """List all accounts stored locally."""
    with _get_session() as session:
        repo = SQLiteTransactionRepository(session)
        accs = repo.get_accounts()

    if not accs:
        typer.echo("No accounts found. Run 'flowger discover' first.")
        return

    for acc in accs:
        iban = f"  IBAN: {acc.iban}" if acc.iban else ""
        typer.echo(
            f"  {acc.id}  |  {acc.name}  |  {acc.currency}"
            f"  |  {acc.provider}{iban}"
        )


@app.command()
def discover() -> None:
    """Discover accounts from the configured banking provider and store them."""
    provider = _build_provider()
    with _get_session() as session:
        repo = SQLiteTransactionRepository(session)
        accs = provider.get_accounts()
        for acc in accs:
            repo.save_account(acc)

    typer.echo(f"Discovered and stored {len(accs)} account(s).")
    for acc in accs:
        typer.echo(f"  {acc.id}  {acc.name}")


@app.command()
def sync(
    account_id: str = typer.Argument(help="Account ID to sync"),
    days_back: int = typer.Option(
        30, help="Days of history to fetch on first sync"
    ),
) -> None:
    """Sync transactions for one account from the provider."""
    provider = _build_provider()
    with _get_session() as session:
        repo = SQLiteTransactionRepository(session)

        if repo.get_account(account_id) is None:
            typer.echo(
                f"Account '{account_id}' not found locally. "
                "Run 'flowger discover' first.",
                err=True,
            )
            raise typer.Exit(1)

        new_count = sync_account_transactions(
            account_id=account_id,
            provider=provider,
            repository=repo,
            days_back=days_back,
        )

    typer.echo(f"Synced {new_count} new transaction(s) for '{account_id}'.")


@app.command("sync-all")
def sync_all(
    days_back: int = typer.Option(
        30, help="Days of history to fetch on first sync"
    ),
) -> None:
    """Sync transactions for all stored accounts."""
    provider = _build_provider()
    with _get_session() as session:
        repo = SQLiteTransactionRepository(session)
        accs = repo.get_accounts()

        if not accs:
            typer.echo("No accounts found. Run 'flowger discover' first.")
            return

        total = 0
        for acc in accs:
            count = sync_account_transactions(
                account_id=acc.id,
                provider=provider,
                repository=repo,
                days_back=days_back,
            )
            total += count
            typer.echo(f"  {acc.id}: {count} new transaction(s)")

    typer.echo(
        f"Total: {total} new transaction(s) across {len(accs)} account(s)."
    )


@app.command()
def export(
    account_id: str = typer.Argument(help="Account ID to export"),
    output_dir: Path = typer.Option(
        None, help="Output directory (defaults to EXPORTS_DIR setting)"
    ),
) -> None:
    """Export transactions for one account to a CSV file."""
    out_dir = output_dir or settings.exports_dir
    with _get_session() as session:
        repo = SQLiteTransactionRepository(session)
        account = repo.get_account(account_id)

        if account is None:
            typer.echo(f"Account '{account_id}' not found locally.", err=True)
            raise typer.Exit(1)

        filepath = export_account_transactions(account, repo, out_dir)

    typer.echo(f"Exported to {filepath}")


@app.command("export-all")
def export_all(
    output_dir: Path = typer.Option(
        None, help="Output directory (defaults to EXPORTS_DIR setting)"
    ),
) -> None:
    """Export transactions for all stored accounts to CSV files."""
    out_dir = output_dir or settings.exports_dir
    with _get_session() as session:
        repo = SQLiteTransactionRepository(session)
        accs = repo.get_accounts()

        if not accs:
            typer.echo("No accounts found. Run 'flowger discover' first.")
            return

        for acc in accs:
            filepath = export_account_transactions(acc, repo, out_dir)
            typer.echo(f"  {acc.id}: exported to {filepath}")

    typer.echo(f"Exported {len(accs)} account(s).")


# ------------------------------------------------------------------
# Entrypoint
# ------------------------------------------------------------------


def main() -> None:
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        stream=sys.stderr,
    )
    app()


if __name__ == "__main__":
    main()
