from flowger.application.banking import BankProvider
from flowger.domain.account import Account
from flowger.infrastructure.enable_banking.client import EnableBankingClient


class EnableBankingProvider(BankProvider):
    """Adapts EnableBanking logic to the application's BankProvider port."""

    def __init__(self, app_id: str, private_key_path: str, environment: str) -> None:
        self.__client = EnableBankingClient(
            app_id=app_id, 
            private_key_path=private_key_path,
            environment=environment
        )

    def fetch_accounts(self) -> list[Account]:
        """
        Fetch accounts from the provider.
        Currently a stub to demonstrate the port hookup.
        Next step: Implement OAuth redirection handling.
        """
        # A full fetch requires authorizing a session first, then using session_id
        # to call GET /accounts. 
        # For this iteration, we return an empty list until the CLI auth flow is built.
        return []

    def start_authorization(self, bank_name: str, country: str, redirect_url: str) -> str:
        """
        Initiate an authorization flow.
        Returns the authorization URL that the user must visit.
        """
        payload = {
            "access": {
                "valid_until": "2026-12-31T23:59:59Z", # Arbitrary future date for now
                "balances": {},
                "transactions": {}
            },
            "aspsp": {
                "name": bank_name,
                "country": country
            },
            "state": "flowger_sync",
            "redirect_url": redirect_url
        }
        
        response = self.__client.post("/auth", json=payload)
        url: str = response.get("url", "")
        return url
