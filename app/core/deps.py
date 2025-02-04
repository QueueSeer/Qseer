from typing import Any, Annotated, Generic, Literal, TypeVar

from fastapi.security import APIKeyCookie, HTTPBearer
from pydantic import AfterValidator, BaseModel, EmailStr
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN
from fastapi import Depends, HTTPException, Request

from app.core.schemas import TokenPayload
from app.core.security import decode_jwt
from .config import settings

COOKIE_NAME = "token"
M = TypeVar('M', bound=BaseModel)


class JWTCookie(APIKeyCookie, Generic[M]):
    def __init__(self, name: str, require: type[M] | tuple[str, ...] = (), **kwargs):
        super().__init__(name=name, **kwargs)
        if isinstance(require, tuple):
            self.token_model = dict
            self.require = require
        else:
            self.token_model = require
            self.require = [
                name for name, field in require.model_fields.items() if field.is_required()
            ]

    async def __call__(self, request: Request) -> M | dict[str, Any] | None:
        api_key = request.cookies.get(self.model.name)
        if not api_key:
            if self.auto_error:
                raise HTTPException(
                    status_code=HTTP_401_UNAUTHORIZED, detail="Shoo! Go away!"
                )
            else:
                return None
        return self.token_model(**decode_jwt(api_key, self.require))


cookie_scheme = JWTCookie(
    name=COOKIE_NAME,
    require=TokenPayload
)


def user_with_seer_permission(token: TokenPayload = Depends(cookie_scheme)):
    if "seer" not in token.roles:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="No permission."
        )
    return token


def user_with_admin_permission(token: TokenPayload = Depends(cookie_scheme)):
    if "admin" not in token.roles:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="No permission."
        )
    return token


UserJWTDep = Annotated[TokenPayload, Depends(cookie_scheme)]
SeerJWTDep = Annotated[TokenPayload, Depends(user_with_seer_permission)]
AdminJWTDep = Annotated[TokenPayload, Depends(user_with_admin_permission)]

EmailLower = Annotated[EmailStr, AfterValidator(str.lower)]
SortingOrder = Literal['asc', 'desc']
NullLiteral = Literal['null']
