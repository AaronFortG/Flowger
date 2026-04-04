import time
import jwt

def generate_bearer_token(app_id: str, private_key_path: str, expiration_seconds: int = 3600) -> str:
    """
    Generate an RS256 JWT string as expected by EnableBanking's authorization header.
    """
    with open(private_key_path, "rb") as key_file:
        private_key = key_file.read()

    now = int(time.time())
    
    headers = {
        "typ": "JWT",
        "alg": "RS256",
        "kid": app_id
    }
    
    payload = {
        "iss": "enablebanking.com",
        "aud": "api.enablebanking.com",
        "iat": now,
        "exp": now + expiration_seconds
    }

    # encode() returns a string in PyJWT >= 2.0.0
    token = jwt.encode(
        payload=payload,
        key=private_key,
        algorithm="RS256",
        headers=headers
    )
    
    return token
