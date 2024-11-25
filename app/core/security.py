from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi import Request, HTTPException
import jwt
from jwt.exceptions import (
    InvalidTokenError,
    ExpiredSignatureError,
    MissingRequiredClaimError
)
import bcrypt
from passlib.context import CryptContext

from .config import settings

ALGORITHM = "HS256"


class JWTBearer(HTTPBearer):
    def __init__(self, **kwargs):
        super(JWTBearer, self).__init__(*kwargs)

    async def __call__(self, request: Request) -> Optional[str]:
        credentials: Optional[HTTPAuthorizationCredentials] = await super(JWTBearer, self).__call__(request)
        if credentials is None:
            return None
        try:
            payload = jwt.decode(
                credentials,
                settings.SECRET_KEY,
                algorithms=[ALGORITHM],
                options={"require": ["exp", "sub"]}
            )
        except ExpiredSignatureError:
            raise HTTPException(status_code=403, detail="Expired token.")
        except InvalidTokenError:
            raise HTTPException(status_code=403, detail="Invalid token.")
        return payload


# Bug fixed: passlib warning when trying to get bcrypt version
disable_warning_obj = (lambda: None)
disable_warning_obj.__version__ = '4.2.1'
bcrypt.__about__ = disable_warning_obj
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password):
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def create_jwt(data: dict, expires_delta: timedelta | None = None):
    '''
    Create JWT token with data and expiration time.

    :param data: dict: Data to be encoded in JWT token.
        data['exp'] will be overwritten if expires_delta is not None.
    :param expires_delta: timedelta: Expiration time of the token.
    :return: str: JWT token.
    '''
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
        data['exp'] = expire
    encoded_jwt = jwt.encode(data, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_jwt(token: str, require=("exp", "sub", "email")) -> dict[str, Any]:
    try:
        return jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"require": require}
        )
    except ExpiredSignatureError:
        raise HTTPException(status_code=403, detail="Expired token.")
    except MissingRequiredClaimError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except InvalidTokenError:
        raise HTTPException(status_code=403, detail="Invalid token.")
