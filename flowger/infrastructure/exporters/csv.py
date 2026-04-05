import csv

from flowger.application.export import ExportService
from flowger.domain.transaction import Transaction


class ActualCsvExporter(ExportService):
    """
    Export transactions in a CSV format compatible with Actual Budget.
    Format: Date, Payee, Notes, Amount
    """

    _HEADERS = ["Date", "Payee", "Notes", "Amount"]
    _FORMULA_PREFIXES = ("=", "+", "-", "@")

    def __init__(self, delimiter: str = ",", safe: bool = True) -> None:
        if len(delimiter) != 1:
            raise ValueError(f"CSV delimiter must be a single character, got: {delimiter!r}")
        self.__delimiter = delimiter
        self.__safe = safe

    def write_transactions(self, transactions: list[Transaction], output_path: str) -> None:
        """Write transactions to a CSV file."""
        # Sort transactions by date (oldest first) for better import experience
        sorted_txs = sorted(transactions, key=lambda tx: tx.date)

        with open(output_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=self.__delimiter)
            # Write header
            writer.writerow(self._HEADERS)

            for tx in sorted_txs:
                if self.__safe:
                    payee_val = (
                        tx.payee.replace('"', "")
                        .replace("'", "")
                        .replace("\n", " ")
                        .replace("\r", " ")
                    )
                    payee_val = payee_val.replace(self.__delimiter, " ")
                    if payee_val.startswith(self._FORMULA_PREFIXES):
                        payee_val = f"'{payee_val}"
                    notes_val = (
                        tx.notes.replace('"', "")
                        .replace("'", "")
                        .replace("\n", " ")
                        .replace("\r", " ")
                    )
                    notes_val = notes_val.replace(self.__delimiter, " ")
                    if notes_val.startswith(self._FORMULA_PREFIXES):
                        notes_val = f"'{notes_val}"
                else:
                    payee_val = tx.payee
                    notes_val = tx.notes
                
                writer.writerow(
                    [
                        tx.date.isoformat(),
                        payee_val,
                        notes_val,
                        str(tx.amount),
                    ]
                )
