import csv

from flowger.application.export import ExportService
from flowger.domain.transaction import Transaction


class ActualCsvExporter(ExportService):
    """
    Export transactions in a CSV format compatible with Actual Budget.
    Format: Date, Payee, Notes, Amount
    """

    def write_transactions(self, transactions: list[Transaction], output_path: str) -> None:
        """Write transactions to a CSV file."""
        # Sort transactions by date (oldest first) for better import experience
        sorted_txs = sorted(transactions, key=lambda tx: tx.date)

        with open(output_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            # Write header
            writer.writerow(["Date", "Payee", "Notes", "Amount"])

            for tx in sorted_txs:
                writer.writerow(
                    [
                        tx.date.isoformat(),
                        tx.description,
                        tx.notes,
                        str(tx.amount),
                    ]
                )
