from datetime import timedelta
from typing import Annotated
from google.oauth2 import id_token
from google.auth.transport import requests
from fastapi import (
    APIRouter,
    HTTPException,
    Request,
    Response,
    status,
    Depends,
    Form,
    Cookie
)
from fastapi.responses import PlainTextResponse
from pydantic import validate_email
from sqlalchemy import delete, select, update

from app.core.config import settings
from app.core.security import (
    create_jwt,
    decode_jwt,
    verify_password,
    JWTCookieDep
)
from app.core.schemas import MessageModel
from app.database import SessionDep
from app.database.models import User
from . import responses as res
from .schemas import (
    UserBase,
    UserRegister,
    UserLogin,
    UserOut,
    UserSelectableField
)
from .service import create_user

router = APIRouter(prefix="/user", tags=["User"])


@router.post("/google/signin")
async def google_signin(credential: Annotated[str, Form()]):
    try:
        idinfo = id_token.verify_oauth2_token(
            credential,
            requests.Request(),
            settings.GOOGLE_CLIENT_ID
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    response = PlainTextResponse(content=idinfo['name'])
    return response


@router.post("/login", responses=res.login)
async def login(user: UserLogin, session: SessionDep, response: Response):
    '''
    - **username**: required เป็น username หรือ email
    - **password**: required
    '''
    try:
        validate_email(user.username)
        is_email = True
    except ValueError:
        is_email = False
    stmt = select(User.id, User.email, User.password, User.role)
    cond = User.email == user.username if is_email else User.username == user.username
    stmt = stmt.where(cond, User.is_active == True)
    row = session.execute(stmt).one_or_none()
    session.commit()
    hashed_password = row.password if row is not None else None
    if not verify_password(user.password, hashed_password):
        raise HTTPException(status_code=404, detail="User not found.")
    token = create_jwt(
        {"sub": row.id, "email": row.email, "role": row.role},
        timedelta(days=7)
    )
    cookie_path = "/" if settings.DEVELOPMENT else "/api"
    response.set_cookie(
        "token", token, max_age=604800, path=cookie_path,
        secure=True, httponly=True, samesite="strict"
    )
    return UserBase.Id(id=row.id)


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    responses=res.register
)
async def register(user: UserRegister, session: SessionDep, request: Request):
    """
    สมัครบัญชีผู้ใช้งานฝั่งลูกค้า:

    - **username**: required
    - **display_name**: required
    - **first_name**: required
    - **last_name**: required
    - **email**: required
    - **phone_number**: ไม่บังคับ เลข 10 หลัก
    - **birthdate**: ไม่บังคับ เป็น timestamp คือมีทั้งวันที่และเวลา
     ควรใส่ timezone ต่อหลัง (+07:00)
    - **password**: required ต้องมีความยาวอย่างน้อย 8 ตัวอักษร
    - **properties**: ไม่บังคับ ระบุคุณสมบัติเพิ่มเติม
     อย่างเช่น **reading_type** (ชนิดการดูดวง) และ **interested_topics** (เรื่องที่สนใจ)
    """
    new_user = create_user(session, user)
    token = create_jwt({"vrf": new_user.id}, timedelta(days=1))
    # TODO: send email to user
    print(request.url_for("verify_user", token=token)._url)
    return UserBase.Id(id=new_user.id)


@router.get("/verify/{token}", responses=res.verify_user)
async def verify_user(token: str, session: SessionDep):
    '''
    ยืนยันตัวตนผู้ใช้งานโดยใช้ token ที่ส่งมาจากอีเมล์

    Response code:
    - **200**: ยืนยันตัวตนผู้ใช้งานสำเร็จ
    - **400**: ส่วนใหญ่คือผู้ใช้งานได้รับการยืนยันตัวตนแล้ว หรือไม่มีผู้ใช้งานนี้
    - **403**: token ไม่ถูกต้อง มักจะเป็นเพราะ token หมดอายุ
    '''
    payload = decode_jwt(token, require=["exp", "vrf"])
    user_id = payload["vrf"]
    stmt = (
        update(User).
        where(User.id == user_id, User.is_active == False).
        values(is_active=True).
        returning(User.id)
    )
    user_id = session.execute(stmt).scalar_one_or_none()
    session.commit()
    if user_id is None:
        raise HTTPException(status_code=400, detail="User has been verified.")
    return MessageModel("User verified.")


@router.get("/me", responses=res.get_self_info)
async def get_self_info(payload: JWTCookieDep, session: SessionDep):
    '''
    ดึงข้อมูลของผู้ใช้งานของตัวเอง แต่ไม่รวม date_created และ properties
    '''
    user_id = payload["sub"]
    user = session.execute(
        select(User).
        where(User.id == user_id, User.is_active == True)
    ).scalar_one_or_none()
    return UserOut.model_validate(user)


@router.get("/me/{field}", responses=res.get_self_field)
async def get_self_field(
    field: UserSelectableField,
    payload: JWTCookieDep,
    session: SessionDep
):
    '''
    ดึงข้อมูลของผู้ใช้งานของตัวเอง เฉพาะ field ที่ต้องการ
    '''
    user_id = payload["sub"]
    stmt = (
        select(User.__dict__[field]).
        where(User.id == user_id, User.is_active == True)
    )
    result = session.execute(stmt).scalar_one_or_none()
    session.commit()
    if result is None:
        raise HTTPException(status_code=404, detail="User not found.")
    return {field: result}


@router.post("/delete")
async def delete_user(id: int = None, session: SessionDep = None):
    '''
    For testing purpose only.
    '''
    stmt = delete(User)
    if id is not None:
        stmt = stmt.where(User.id == id)
    stmt = stmt.returning(User.id)
    result = session.execute(stmt)
    session.commit()
    return {"statement": str(stmt), "result": result.scalars().all()}


@router.get("/check_cookie")
async def check_cookie(payload: JWTCookieDep):
    '''
    For testing purpose only.
    '''
    if payload is None:
        raise HTTPException(status_code=404, detail="Token not found.")
    return payload
