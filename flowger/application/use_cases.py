"""Application use cases – the core of what Flowger does.

Each function represents one user-facing action.  Dependencies (provider,
repository, exporter) are injected so the functions are easy to test.
"""

import logging
from datetime import date, timedelta
from pathlib import Path

from flowger.domain.models import Account
from flowger.domain.ports import BankingProvider, TransactionRepository
from flowger.infrastructure.csv_exporter import export_to_csv

logger = logging.getLogger(__name__)


def sync_account_transactions(
    account_id: str,
    provider: BankingProvider,
    repository: TransactionRepository,
    days_back: int = 30,
) -> int:
    """Fetch transactions from the provider and persist new ones.

    If there is a previous sync, only transactions *after* the last known date
    are requested.  Otherwise, ``days_back`` days of history are fetched.

    Returns the number of newly inserted transactions.
    """
    today = date.today()
    last_sync = repository.get_last_sync_date(account_id)

    if last_sync is not None:
        from_date = last_sync + timedelta(days=1)
    else:
        from_date = today - timedelta(days=days_back)

    logger.info(
        "Syncing account %s from %s to %s", account_id, from_date, today
    )

    transactions = provider.get_transactions(account_id, from_date, today)
    new_count = repository.upsert_transactions(transactions)

    logger.info(
        "Saved %d new transaction(s) for account %s", new_count, account_id
    )
    return new_count


def export_account_transactions(
    account: Account,
    repository: TransactionRepository,
    output_dir: Path,
) -> Path:
    """Export all stored transactions for an account to a CSV file.

    The CSV format is compatible with Actual Budget's CSV import.
    Returns the path of the written file.
    """
    transactions = repository.get_transactions(account.id)

    logger.info(
        "Exporting %d transaction(s) for account %s",
        len(transactions),
        account.id,
    )

    filepath = export_to_csv(transactions, account, output_dir)
    logger.info("Exported transactions to %s", filepath)
    return filepath
