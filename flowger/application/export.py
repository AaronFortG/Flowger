from typing import Protocol

from flowger.domain.transaction import Transaction


class ExportService(Protocol):
    """Port for exporting transaction data to external formats."""

    def write_transactions(self, transactions: list[Transaction], output_path: str) -> None:
        """Export a list of transactions to a file at the specified path."""
        pass
