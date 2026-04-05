from collections.abc import Generator
from unittest.mock import MagicMock, patch

import httpx
import pytest

from flowger.domain.exceptions import BankProviderError
from flowger.infrastructure.enable_banking.client import EnableBankingClient


@pytest.fixture
def mock_httpx_client() -> Generator[MagicMock, None, None]:
    with patch("flowger.infrastructure.enable_banking.client.httpx.Client") as mock_cls:
        mock_instance = MagicMock()
        mock_cls.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_jwt() -> Generator[MagicMock, None, None]:
    with patch("flowger.infrastructure.enable_banking.client.generate_bearer_token") as mock:
        mock.return_value = "fake.jwt.token"
        yield mock


def test_client_get_success(mock_httpx_client: MagicMock, mock_jwt: MagicMock) -> None:
    client = EnableBankingClient(app_id="test", private_key_path="path")

    mock_response = MagicMock()
    mock_response.json.return_value = {"a": "b"}
    mock_response.raise_for_status = MagicMock()
    mock_httpx_client.get.return_value = mock_response

    result = client.get("/test")

    assert result == {"a": "b"}
    mock_httpx_client.get.assert_called_once_with(
        "https://api.enablebanking.com/test",
        params=None,
        headers={"Authorization": "Bearer fake.jwt.token", "Content-Type": "application/json"},
    )
    mock_response.raise_for_status.assert_called_once()


def test_client_post_error(mock_httpx_client: MagicMock, mock_jwt: MagicMock) -> None:
    client = EnableBankingClient(app_id="test", private_key_path="path")

    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Auth failed", request=MagicMock(), response=mock_response
    )
    mock_httpx_client.post.return_value = mock_response

    with pytest.raises(BankProviderError, match="POST /test failed"):
        client.post("/test", json={"data": 1})

    mock_httpx_client.post.assert_called_once()


def test_client_get_network_error(mock_httpx_client: MagicMock, mock_jwt: MagicMock) -> None:
    client = EnableBankingClient(app_id="test", private_key_path="path")
    mock_httpx_client.get.side_effect = httpx.RequestError("Timeout", request=MagicMock())

    with pytest.raises(BankProviderError, match="GET /test failed due to network error"):
        client.get("/test", params=None)


def test_client_post_network_error(mock_httpx_client: MagicMock, mock_jwt: MagicMock) -> None:
    client = EnableBankingClient(app_id="test", private_key_path="path")
    mock_httpx_client.post.side_effect = httpx.RequestError("Connection lost", request=MagicMock())

    with pytest.raises(BankProviderError, match="POST /test failed due to network error"):
        client.post("/test", json={"data": 1})
