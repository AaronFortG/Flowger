"""Enable Banking API client.

Enable Banking (https://enablebanking.com) is a PSD2 aggregator that provides
unified access to bank accounts across Europe.

This module contains the skeleton for a real integration.  The API requires:
  1. Application credentials (client certificate + private key or API key).
  2. A PSU (Payment Service User) consent flow before account data can be read.

Because the consent flow is interactive and requires a redirect URI, a full
integration is out of scope for the initial MVP.  This class will raise
``NotImplementedError`` until the integration is implemented.

Configuration (via environment variables / .env):
  PROVIDER=enable_banking
  ENABLE_BANKING_BASE_URL=https://api.enablebanking.com
  ENABLE_BANKING_API_KEY=<your-api-key>
"""

from datetime import date

import httpx

from flowger.domain.models import Account, Transaction
from flowger.domain.ports import BankingProvider


class EnableBankingProvider(BankingProvider):
    """HTTP client for the Enable Banking API.

    TODO (next iteration):
      - Implement OAuth2 / PSU consent management.
      - Implement ``get_accounts`` using GET /accounts.
      - Implement ``get_transactions`` using GET /accounts/{id}/transactions.
      - Handle pagination (continuationKey).
      - Map API response fields to domain models.
    """

    def __init__(self, base_url: str, api_key: str) -> None:
        self._client = httpx.Client(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30.0,
        )

    def get_accounts(self) -> list[Account]:
        raise NotImplementedError(
            "Enable Banking integration is not yet implemented. "
            "Set PROVIDER=stub for local development."
        )

    def get_transactions(
        self, account_id: str, from_date: date, to_date: date
    ) -> list[Transaction]:
        raise NotImplementedError(
            "Enable Banking integration is not yet implemented. "
            "Set PROVIDER=stub for local development."
        )
