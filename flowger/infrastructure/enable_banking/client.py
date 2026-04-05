import time
from typing import Any

import httpx

from flowger.domain.exceptions import BankProviderError, KeyReadError
from flowger.infrastructure.enable_banking.auth import sign_jwt


class EnableBankingClient:
    """Wrapper around httpx to communicate with EnableBanking API."""

    BASE_URL = "https://api.enablebanking.com"

    def __init__(self, app_id: str, private_key_path: str) -> None:
        self.__app_id = app_id
        # Read the key once at creation to avoid disk IO on every request.
        try:
            with open(private_key_path, "rb") as f:
                self.__private_key = f.read()
        except OSError as e:
            raise KeyReadError(f"Cannot read private key at '{private_key_path}': {e}") from e

        # Token state for auto-refresh
        self.__token: str | None = None
        self.__token_expires_at: float = 0.0

        # Client is reused across requests for connection pooling.
        self.__http = httpx.Client(timeout=30.0)

    def __get_headers(self) -> dict[str, str]:
        # Refresh token if missing or near expiry (5 minute buffer)
        if self.__token is None or time.time() > (self.__token_expires_at - 300):
            # Token is valid for 1 hour (3600s)
            self.__token = sign_jwt(self.__app_id, self.__private_key)
            self.__token_expires_at = time.time() + 3600

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
