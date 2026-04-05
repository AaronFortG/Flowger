import time
import uuid

import jwt

from flowger.domain.exceptions import KeyReadError

_ISSUER = "enablebanking.com"
_AUDIENCE = "api.enablebanking.com"


def generate_bearer_token(
    app_id: str, private_key_path: str, expiration_seconds: int = 3600
) -> str:
    """
    Read the private key from disk and generate an RS256 JWT string.
    """
    try:
        with open(private_key_path, "rb") as key_file:
            private_key = key_file.read()
    except OSError as e:
        raise KeyReadError(f"Cannot read private key at '{private_key_path}': {e}") from e

    return sign_jwt(app_id, private_key, expiration_seconds)


def sign_jwt(app_id: str, private_key: bytes, expiration_seconds: int = 3600) -> str:
    """
    Sign an RS256 JWT string as expected by EnableBanking's authorization header.
    """
    now = int(time.time())

    headers = {
        "typ": "JWT",
        "alg": "RS256",
        "kid": app_id,
    }

    payload = {
        "iss": _ISSUER,
        "aud": _AUDIENCE,
        "sub": app_id,
        "iat": now,
        "exp": now + expiration_seconds,
        "jti": str(uuid.uuid4()),
    }

    token = jwt.encode(
        payload=payload,
        key=private_key,
        algorithm="RS256",
        headers=headers,
    )
    return str(token)
