import datetime
from decimal import Decimal
from typing import Any

from flowger.domain.account import Account
from flowger.domain.bank_session import BankSession
from flowger.domain.transaction import Transaction
from flowger.infrastructure.enable_banking.client import EnableBankingClient

_AUTH_ENDPOINT = "/auth"
_SESSIONS_ENDPOINT = "/sessions"
_ACCOUNTS_ENDPOINT = "/accounts"
_TRANSACTIONS_ENDPOINT = "/accounts/{account_id}/transactions"
_AUTH_STATE = "flowger_sync"
_ACCESS_VALID_DAYS = 180


def _compute_valid_until(days: int = _ACCESS_VALID_DAYS) -> str:
    """Return an ISO-8601 UTC timestamp 'days' from now, as required by EnableBanking."""
    until = datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(days=days)
    return until.strftime("%Y-%m-%dT%H:%M:%SZ")


def _resolve_description(tx: dict[str, Any]) -> str:
    """Return the best available description for a transaction."""
    return (
        tx.get("creditor_name")
        or tx.get("debtor_name")
        or tx.get("remittance_information_unstructured")
        or "No description"
    )


class EnableBankingProvider:
    """Adapts EnableBanking HTTP API to the application's BankProvider port."""

    def __init__(
        self,
        app_id: str,
        private_key_path: str,
        environment: str,
        client: EnableBankingClient | None = None,
    ) -> None:
        self.__client = client or EnableBankingClient(
            app_id=app_id,
            private_key_path=private_key_path,
            environment=environment,
        )

    def start_authorization(self, bank_name: str, country: str, redirect_url: str) -> str:
        """
        Initiate an authorization flow.
        Returns the authorization URL that the user must visit in their browser.
        """
        payload = {
            "access": {
                "valid_until": _compute_valid_until(),
                "balances": {},
                "transactions": {},
            },
            "aspsp": {
                "name": bank_name,
                "country": country,
            },
            "state": _AUTH_STATE,
            "redirect_url": redirect_url,
        }
        response = self.__client.post(_AUTH_ENDPOINT, json=payload)
        url: str = response.get("url", "")
        return url

    def authorize_session(self, code: str, bank_name: str, country: str) -> BankSession:
        """
        Exchange the redirect authorization code for a session_id.
        Returns a BankSession ready to be persisted.
        """
        response = self.__client.post(_SESSIONS_ENDPOINT, json={"code": code})
        session_id: str = response["session_id"]
        return BankSession(
            session_id=session_id,
            bank_name=bank_name,
            country=country,
            created_at=datetime.datetime.now(tz=datetime.timezone.utc),
        )

    def fetch_accounts(self, session_id: str) -> list[Account]:
        """Fetch all accounts available under the given authorized session."""
        response = self.__client.get(f"{_ACCOUNTS_ENDPOINT}?session_id={session_id}")
        raw_accounts: list[dict[str, Any]] = response.get("accounts", [])
        return [
            Account(
                id=acc["uid"],
                iban=acc.get("iban", ""),
                name=acc.get("product", "Unknown"),
                currency=acc.get("currency", ""),
            )
            for acc in raw_accounts
        ]

    def fetch_transactions(self, session_id: str, account_id: str) -> list[Transaction]:
        """Fetch transactions for a specific account under an authorized session."""
        endpoint = _TRANSACTIONS_ENDPOINT.format(account_id=account_id)
        response = self.__client.get(f"{endpoint}?session_id={session_id}")
        raw_txs: list[dict[str, Any]] = response.get("transactions", [])
        return [
            Transaction(
                id=tx["uid"],
                account_id=account_id,
                date=datetime.date.fromisoformat(tx["booking_date"]),
                amount=Decimal(str(tx["amount"])),
                currency=tx["currency"],
                description=_resolve_description(tx),
                notes=tx.get("remittance_information_unstructured", ""),
            )
            for tx in raw_txs
        ]
