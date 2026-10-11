from datetime import datetime, timedelta, timezone

from jose import jwt
from pwdlib import PasswordHash

from app.core.config import settings
from fastapi import HTTPException, Request, status

from app.cache.redis import check_rate_limit

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    return password_hash.verify(
        plain_password,
        hashed_password,
    )


def create_access_token(user_id: int) -> str:
    expiration_time = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(user_id),
        "exp": expiration_time,
    }

    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def decode_access_token(token: str) -> dict:
    return jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
    )

def rate_limit(
    request: Request,
    action: str,
    limit: int,
    window_seconds: int,
):
    client_ip = request.client.host

    identifier = (
        f"{action}:{client_ip}"
    )

    allowed = check_rate_limit(
        identifier=identifier,
        limit=limit,
        window_seconds=window_seconds,
    )

    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later.",
        )

def login_rate_limit(
    request: Request,
):
    rate_limit(
        request=request,
        action="login",
        limit=5,
        window_seconds=60,
    )

def create_url_rate_limit(
    request: Request,
):
    rate_limit(
        request=request,
        action="create_url",
        limit=20,
        window_seconds=60,
    )
