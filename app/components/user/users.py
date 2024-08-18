from typing import Annotated
from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_session

router = APIRouter(prefix="/users", tags=["users"])
security = HTTPBearer(bearerFormat="test", scheme_name="JWT", description="JWT Token")


@router.get("/")
async def read_users():
    return [{"username": "Rick"}, {"username": "Morty"}]


@router.get("/me")
def read_current_user(authorization: Annotated[HTTPAuthorizationCredentials, Depends(security)]):
    return {"scheme": authorization.scheme, "credentials": authorization.credentials}


@router.get("/{username}")
async def read_user(username: str):
    return {"username": username}


@router.get("/items/{item_id}")
def get_item(item_id: str, session: Session = Depends(get_session)):
    pass
