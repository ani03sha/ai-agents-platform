from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette import status

from agents_shared.auth import TokenError, decode_token

from ..config import settings

_bearer = HTTPBearer()


async def require_auth(
    credentials: HTTPAuthorizationCredentials = Security(_bearer),
) -> dict:
    """FastAPI dependency for protected routes.

    @router.post("/tasks")
    async def submit(req: TaskRequest, principal: dict = Depends(require_auth)): ...
    """
    try:
        payload = decode_token(
            credentials.credentials,
            secret=settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
            expected_type="access",
        )
    except TokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    return payload
