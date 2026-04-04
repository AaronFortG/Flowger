import datetime

from flowger.application.banking import BankProvider
from flowger.domain.account import Account
from flowger.domain.bank_session import BankSession
from flowger.infrastructure.enable_banking.client import EnableBankingClient


class EnableBankingProvider(BankProvider):
    """Adapts EnableBanking HTTP API to the application's BankProvider port."""

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
        response = self.__client.post("/auth", json=payload)
        url: str = response.get("url", "")
        return url

    def authorize_session(self, code: str, bank_name: str, country: str) -> BankSession:
        """
        Exchange the redirect authorization code for a session_id.
        Returns a BankSession ready to be persisted.
        """
        response = self.__client.post("/sessions", json={"code": code})
        session_id: str = response["session_id"]
        return BankSession(
            session_id=session_id,
            bank_name=bank_name,
            country=country,
            created_at=datetime.datetime.now(tz=datetime.timezone.utc),
        )

    def fetch_accounts(self, session_id: str) -> list[Account]:
        """Fetch all accounts available under the given authorized session."""
        response = self.__client.get(f"/accounts?session_id={session_id}")
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
