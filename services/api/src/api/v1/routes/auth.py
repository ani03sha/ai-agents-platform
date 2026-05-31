from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from agents_shared.auth import TokenError, decode_token, issue_access_token, issue_refresh_token

from ....config import settings

router = APIRouter(tags=["auth"])


class TokenRequest(BaseModel):
    api_key: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # access token TTL in seconds
    refresh_expires_in: int  # refresh token TTL in seconds


def _tokens_for(sub: str) -> TokenResponse:
    return TokenResponse(
        access_token=issue_access_token(
            sub,
            secret=settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
            expiry_minutes=settings.jwt_expiry_minutes,
        ),
        refresh_token=issue_refresh_token(
            sub,
            secret=settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
            expiry_days=settings.jwt_refresh_expiry_days,
        ),
        expires_in=settings.jwt_expiry_minutes * 60,
        refresh_expires_in=settings.jwt_refresh_expiry_days * 86400,
    )


@router.post("/auth/token", response_model=TokenResponse)
async def issue_token(request: TokenRequest) -> TokenResponse:
    valid_keys = {k.strip() for k in settings.api_keys.split(",")}
    if request.api_key not in valid_keys:
        raise HTTPException(status_code=401, detail="Invalid API key")

    sub = request.api_key[:8] + "..."
    return _tokens_for(sub)


@router.post("/auth/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshRequest) -> TokenResponse:
    try:
        payload = decode_token(
            request.refresh_token,
            secret=settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
            expected_type="refresh",
        )
    except TokenError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    return _tokens_for(payload["sub"])
