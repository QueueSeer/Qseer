from datetime import timedelta
from typing import Annotated
from google.oauth2 import id_token
from google.auth.transport import requests
from fastapi import (
    APIRouter,
    HTTPException,
    Response,
    Form,
)
from sqlalchemy import select

from app.core.config import settings
from app.core.deps import (
    COOKIE_NAME,
    UserJWTDep
)
from app.core.security import (
    create_jwt,
    verify_password
)
from app.core.schemas import Message, UserId
from app.database import SessionDep
from app.database.models import User, Seer, Admin
from ..user.service import create_user
from .schemas import UserLogin
from . import responses as res

router = APIRouter(prefix="/access", tags=["Access"])


@router.post("/google/signin", responses=res.google_signin)
async def google_signin(credential: Annotated[str, Form()], session: SessionDep, response: Response):
    '''
    เข้าสู่ระบบด้วย Google Sign-In ถ้าไม่มีบัญชีในระบบจะสร้างให้อัตโนมัติ
    '''
    try:
        idinfo = id_token.verify_oauth2_token(
            credential,
            requests.Request(),
            settings.GOOGLE_CLIENT_ID
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not idinfo['email_verified']:
        raise HTTPException(status_code=400, detail="Email not verified.")
    stmt = (
        select(User.id, User.is_active, Seer.id.label("seer_id"), Admin.id.label("admin_id")).
        join(User.seer, isouter=True).
        join(Admin, isouter=True).
        where(User.email == idinfo['email'])
    )
    row = session.execute(stmt).one_or_none()
    if row is None:
        user_id = create_user(session, User(
            display_name = idinfo['name'],
            first_name   = idinfo['given_name'],
            last_name    = idinfo['family_name'],
            email        = idinfo['email'],
            password     = None,
            image        = idinfo['picture'],
            is_active    = True
        )).id
        seer_id, admin_id = None, None
    else:
        user_id, seer_id, admin_id = row.id, row.seer_id, row.admin_id
        if not row.is_active:
            raise HTTPException(status_code=404, detail="User not found.")

    set_credential_cookie((user_id, seer_id, admin_id), response)
    return UserId(id=user_id)


@router.post("/login", responses=res.login)
async def login(user: UserLogin, session: SessionDep, response: Response):
    '''
    - **email**: required
    - **password**: required
    '''
    stmt = (
        select(
            User.id,
            User.password,
            Seer.id.label("seer_id"),
            Admin.id.label("admin_id")
        ).
        join(User.seer, isouter=True).
        join(Admin, isouter=True).
        where(User.email == user.email, User.is_active == True)
    )
    row = session.execute(stmt).one_or_none()
    session.commit()
    hashed_password = row.password if row is not None else None
    if not verify_password(user.password, hashed_password):
        raise HTTPException(status_code=404, detail="User not found.")
    set_credential_cookie(row, response)
    return UserId(id=row.id)


@router.delete("/logout", responses=res.logout)
async def logout(response: Response):
    '''
    สั่งลบ Cookie
    '''
    response.delete_cookie(COOKIE_NAME)
    return Message("Logged out.")


@router.post("/refresh", responses=res.refresh)
async def refresh(payload: UserJWTDep, session: SessionDep, response: Response):
    '''
    ใช้ JWT เพื่อเข้าถึงระบบอีกครั้ง ทำให้ข้อมูลใน JWT เป็นปัจจุบัน
    '''
    user_id = payload.sub
    stmt = (
        select(
            User.id,
            Seer.id.label("seer_id"),
            Admin.id.label("admin_id")
        ).
        join(User.seer, isouter=True).
        join(Admin, isouter=True).
        where(User.id == user_id, User.is_active == True)
    )
    row = session.execute(stmt).one_or_none()
    session.commit()
    if row is None:
        response.delete_cookie(COOKIE_NAME)
        raise HTTPException(status_code=404, detail="User not found.")
    set_credential_cookie(row, response)
    return UserId(id=row.id)


@router.get("/check_cookie")
async def check_cookie(payload: UserJWTDep):
    '''
    For testing purpose only.
    '''
    return payload


def set_credential_cookie(row, response: Response):
    user_id, seer_id, admin_id = row
    roles = []
    if seer_id is not None:
        roles.append("seer")
    if admin_id is not None:
        roles.append("admin")
    token = create_jwt(
        {"sub": user_id, "roles": roles},
        timedelta(days=7)
    )
    response.set_cookie(
        COOKIE_NAME, token, max_age=604800, path="/",
        secure=True, httponly=True, samesite="strict"
    )