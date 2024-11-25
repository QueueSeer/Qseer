from datetime import timedelta
from typing import Annotated
from google.oauth2 import id_token
from google.auth.transport import requests
from fastapi import (
    APIRouter,
    HTTPException,
    Request,
    status,
    Depends,
    Form,
    Cookie
)
from fastapi.responses import PlainTextResponse
from sqlalchemy import delete, select, update

from app.core.config import settings
from app.core.security import create_jwt, decode_jwt
from app.core.schemas import MessageModel
from app.database import SessionDep
from app.database.models import User
from . import responses as res
from .schemas import UserBase, UserRegister, UserOut
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


@router.post(
    "/",
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


@router.get(
    "/verify/{token}",
    responses=res.verify_user
)
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
    id = session.execute(stmt).scalar_one_or_none()
    session.commit()
    if id is None:
        raise HTTPException(status_code=400, detail="User has been verified.")
    return MessageModel("User verified.")


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
