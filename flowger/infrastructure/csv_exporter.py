"""CSV exporter – produces files compatible with Actual Budget's CSV import.

Actual Budget expects columns: Date, Payee, Notes, Amount.
  - Date   : ISO 8601 (YYYY-MM-DD)
  - Payee  : transaction description / merchant name
  - Notes  : optional reference or memo
  - Amount : decimal value with 2 decimal places (negative = expense, positive = income)
"""

import csv
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

from flowger.domain.models import Account, Transaction

# Standard 2-decimal-place format used for financial amounts in CSV exports.
_TWO_PLACES = Decimal("0.01")


def export_to_csv(
    transactions: list[Transaction],
    account: Account,
    output_dir: Path,
) -> Path:
    """Write transactions to a CSV file named after the account ID.

    The output directory is created if it does not exist.
    Returns the path of the written file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    filepath = output_dir / f"{account.id}.csv"

    with filepath.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh, fieldnames=["Date", "Payee", "Notes", "Amount"]
        )
        writer.writeheader()
        for tx in transactions:
            writer.writerow(
                {
                    "Date": tx.date.isoformat(),
                    "Payee": tx.description,
                    "Notes": tx.reference or "",
                    "Amount": str(
                        tx.amount.quantize(_TWO_PLACES, rounding=ROUND_HALF_UP)
                    ),
                }
            )

    return filepath
