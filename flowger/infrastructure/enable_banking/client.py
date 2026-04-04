from typing import Any

import httpx

from flowger.domain.exceptions import BankProviderError
from flowger.infrastructure.enable_banking.auth import generate_bearer_token


class EnableBankingClient:
    """Wrapper around httpx to communicate with EnableBanking API."""

    BASE_URL = "https://api.enablebanking.com"

    def __init__(self, app_id: str, private_key_path: str, environment: str = "SANDBOX") -> None:
        self.__environment = environment
        # Token is generated once per client lifetime — avoid re-reading key on every request.
        self.__token = generate_bearer_token(
            app_id=app_id,
            private_key_path=private_key_path,
        )
        # Client is reused across requests for connection pooling.
        self.__http = httpx.Client()

    def __get_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.__token}",
            "Content-Type": "application/json",
        }

    def post(self, endpoint: str, json: dict[str, Any]) -> dict[str, Any]:
        """Perform a POST request and return the parsed JSON body."""
        url = f"{self.BASE_URL}{endpoint}"
        try:
            response = self.__http.post(url, json=json, headers=self.__get_headers())
            response.raise_for_status()
            data: dict[str, Any] = response.json()
            return data
        except httpx.HTTPStatusError as e:
            raise BankProviderError(
                f"POST {endpoint} failed with status {e.response.status_code}: {e.response.text}"
            ) from e

    def get(self, endpoint: str) -> dict[str, Any]:
        """Perform a GET request and return the parsed JSON body."""
        url = f"{self.BASE_URL}{endpoint}"
        try:
            response = self.__http.get(url, headers=self.__get_headers())
            response.raise_for_status()
            data: dict[str, Any] = response.json()
            return data
        except httpx.HTTPStatusError as e:
            raise BankProviderError(
                f"GET {endpoint} failed with status {e.response.status_code}: {e.response.text}"
            ) from e

    def close(self) -> None:
        """Release the underlying HTTP connection pool."""
        self.__http.close()
