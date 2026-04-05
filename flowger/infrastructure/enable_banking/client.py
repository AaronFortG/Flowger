from typing import Any

import httpx

from flowger.domain.exceptions import BankProviderError
from flowger.infrastructure.enable_banking.auth import generate_bearer_token


class EnableBankingClient:
    """Wrapper around httpx to communicate with EnableBanking API."""

    BASE_URL = "https://api.enablebanking.com"

    def __init__(self, app_id: str, private_key_path: str) -> None:
        # Token is generated once per client lifetime — avoid re-reading key on every request.
        self.__token = generate_bearer_token(
            app_id=app_id,
            private_key_path=private_key_path,
        )
        # Client is reused across requests for connection pooling.
        self.__http = httpx.Client(timeout=30.0)

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
                f"POST {endpoint} failed with status {e.response.status_code}"
            ) from e
        except httpx.RequestError as e:
            raise BankProviderError(f"POST {endpoint} failed due to network error: {e}") from e

    def get(self, endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Perform a GET request and return the parsed JSON body."""
        url = f"{self.BASE_URL}{endpoint}"
        try:
            response = self.__http.get(url, params=params, headers=self.__get_headers())
            response.raise_for_status()
            data: dict[str, Any] = response.json()
            return data
        except httpx.HTTPStatusError as e:
            raise BankProviderError(
                f"GET {endpoint} failed with status {e.response.status_code}"
            ) from e
        except httpx.RequestError as e:
            raise BankProviderError(f"GET {endpoint} failed due to network error: {e}") from e

    def __enter__(self) -> "EnableBankingClient":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()

    def close(self) -> None:
        """Release the underlying HTTP connection pool."""
        self.__http.close()
