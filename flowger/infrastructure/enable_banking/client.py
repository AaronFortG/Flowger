from typing import Any

import httpx

from flowger.infrastructure.enable_banking.auth import generate_bearer_token


class EnableBankingClient:
    """Wrapper around httpx to communicate with EnableBanking API."""
    
    BASE_URL = "https://api.enablebanking.com"

    def __init__(self, app_id: str, private_key_path: str, environment: str = "SANDBOX") -> None:
        self.__app_id = app_id
        self.__private_key_path = private_key_path
        self.__environment = environment

    def _get_headers(self) -> dict[str, str]:
        token = generate_bearer_token(
            app_id=self.__app_id, 
            private_key_path=self.__private_key_path
        )
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    def post(self, endpoint: str, json: dict[str, Any]) -> dict[str, Any]:
        """Perform a POST request securely."""
        url = f"{self.BASE_URL}{endpoint}"
        
        with httpx.Client() as client:
            response = client.post(url, json=json, headers=self._get_headers())
            response.raise_for_status()
            # mypy complains about Any return, we know json() is dict
            data: dict[str, Any] = response.json()
            return data

    def get(self, endpoint: str) -> dict[str, Any]:
        """Perform a GET request securely."""
        url = f"{self.BASE_URL}{endpoint}"
        
        with httpx.Client() as client:
            response = client.get(url, headers=self._get_headers())
            response.raise_for_status()
            data: dict[str, Any] = response.json()
            return data
