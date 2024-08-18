from typing import Optional
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi import Request, HTTPException
import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError

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
