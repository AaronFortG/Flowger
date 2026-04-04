from pathlib import Path
from typing import Any
import jwt  # type: ignore[import-not-found]
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from flowger.infrastructure.enable_banking.auth import generate_bearer_token


@pytest.fixture
def test_private_key_path(tmp_path: Path) -> str:
    """Generate a temporary RSA private key for testing."""
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    key_path = tmp_path / "test_private.key"
    key_path.write_bytes(pem)
    
    return str(key_path)


def test_generate_bearer_token(test_private_key_path: str) -> None:
    """Verify the generated JWT has exactly the claims EnableBanking expects."""
    token = generate_bearer_token(
        app_id="test-app-id", 
        private_key_path=test_private_key_path
    )
    
    # decode the unverified headers to check 'kid'
    headers = jwt.get_unverified_header(token)
    assert headers["alg"] == "RS256"
    assert headers["typ"] == "JWT"
    assert headers["kid"] == "test-app-id"
    
    # decode the unverified claims
    payload = jwt.decode(token, options={"verify_signature": False})
    
    assert payload["iss"] == "enablebanking.com"
    assert payload["aud"] == "api.enablebanking.com"
    assert "iat" in payload
    assert "exp" in payload
    assert payload["exp"] - payload["iat"] == 3600
