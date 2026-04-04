import datetime
from decimal import Decimal

from flowger.application.banking import BankProvider
from flowger.domain.account import Account
from flowger.domain.bank_session import BankSession
from flowger.domain.transaction import Transaction
from flowger.infrastructure.enable_banking.client import EnableBankingClient


class EnableBankingProvider(BankProvider):
    """Adapts EnableBanking HTTP API to the application's BankProvider port."""

    _ENDPOINTS = {
        "AUTH": "/auth",
        "SESSIONS": "/sessions",
        "ACCOUNTS": "/accounts",
        "TRANSACTIONS": "/accounts/{account_id}/transactions",
    }

    def __init__(self, app_id: str, private_key_path: str, environment: str) -> None:
        self.__client = EnableBankingClient(
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
                "valid_until": "2026-12-31T23:59:59Z",
                "balances": {},
                "transactions": {},
            },
            "aspsp": {
                "name": bank_name,
                "country": country,
            },
            "state": "flowger_sync",
            "redirect_url": redirect_url,
        }
        response = self.__client.post(self._ENDPOINTS["AUTH"], json=payload)
        url: str = response.get("url", "")
        return url

    def authorize_session(self, code: str, bank_name: str, country: str) -> BankSession:
        """
        Exchange the redirect authorization code for a session_id.
        Returns a BankSession ready to be persisted.
        """
        response = self.__client.post(self._ENDPOINTS["SESSIONS"], json={"code": code})
        session_id: str = response["session_id"]
        return BankSession(
            session_id=session_id,
            bank_name=bank_name,
            country=country,
            created_at=datetime.datetime.now(tz=datetime.timezone.utc),
        )

    def fetch_accounts(self, session_id: str) -> list[Account]:
        """Fetch all accounts available under the given authorized session."""
        response = self.__client.get(f"{self._ENDPOINTS['ACCOUNTS']}?session_id={session_id}")
        raw_accounts: list[dict[str, str]] = response.get("accounts", [])
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
        endpoint = self._ENDPOINTS["TRANSACTIONS"].format(account_id=account_id)
        response = self.__client.get(f"{endpoint}?session_id={session_id}")
        raw_txs: list[dict[str, str]] = response.get("transactions", [])
        return [
            Transaction(
                id=tx["uid"],
                account_id=account_id,
                date=datetime.date.fromisoformat(tx["booking_date"]),
                amount=Decimal(tx["amount"]),
                currency=tx["currency"],
                description=tx.get("remittance_information_unstructured", "No description"),
            )
            for tx in raw_txs
        ]
