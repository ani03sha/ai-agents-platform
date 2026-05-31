"""JWT mint/verify helpers, shared by the API's auth routes and its auth dependency.

Pure functions: secret, algorithm, and expiry are passed in by the caller (which
reads them from its own settings). The shared library holds no global config.
"""

from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt

ISSUER = "ai-agents-platform"


class TokenError(Exception):
    """Raised when a token in invalid, expired, or of the wrong type."""


def issue_access_token(
    sub: str,
    *,
    secret: str,
    algorithm: str,
    expiry_minutes: int,
    scopes: list[str] | None = None,
) -> str:
    expiry = datetime.now(UTC) + timedelta(minutes=expiry_minutes)
    return jwt.encode(
        {
            "sub": sub,
            "type": "access",
            "scopes": scopes or ["tasks"],
            "exp": expiry,
            "iss": ISSUER,
        },
        secret,
        algorithm=algorithm,
    )


def issue_refresh_token(
    sub: str,
    *,
    secret: str,
    algorithm: str,
    expiry_days: int,
) -> str:
    expiry = datetime.now(UTC) + timedelta(days=expiry_days)
    return jwt.encode(
        {
            "sub": sub,
            "type": "refresh",
            "exp": expiry,
            "iss": ISSUER,
        },
        secret,
        algorithm=algorithm,
    )


def decode_token(
    token: str,
    *,
    secret: str,
    algorithm: str,
    expected_type: str | None = None,
) -> dict:
    try:
        payload = jwt.decode(token, secret, algorithms=[algorithm])
    except JWTError as exc:
        raise TokenError("Invalid or expired token") from exc

    if expected_type is not None and payload.get("type") != expected_type:
        raise TokenError(f"Expected a {expected_type} token")

    return payload
