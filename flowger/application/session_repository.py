from typing import Protocol

from flowger.domain.bank_session import BankSession


class SessionRepository(Protocol):
    """Port for persisting and retrieving bank sessions."""

    def save_session(self, session: BankSession) -> None:
        """Persist a session. Replaces any existing session for the same bank."""
        ...

    def get_latest_session(self, bank_name: str, country: str) -> BankSession | None:
        """Retrieve the most recently saved session for a given bank and country."""
        ...
