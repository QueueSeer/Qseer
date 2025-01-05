import re
from datetime import timedelta
from fastapi import (
    APIRouter,
    BackgroundTasks,
    HTTPException,
    Request,
    status,
)
from psycopg.errors import UniqueViolation
from sqlalchemy import delete, select, update, insert, exists
from sqlalchemy.exc import NoResultFound ,IntegrityError

from app.core.config import settings
from app.core.deps import UserJWTDep
from app.core.error import (
    BadRequestException,
    NotFoundException,
    InternalException,
    IntegrityException,
)
from app.core.security import (
    create_jwt,
    decode_jwt,
)
from app.core.schemas import Message, UserId, RowCount
from app.database import SessionDep
from app.database.models import User, FollowSeer, Seer
from app.database.utils import parse_unique_violation
from app.emails import send_verify_email
from ..seer.service import check_active_seer
from . import responses as res
from .schemas import (
    UserRegister,
    UserOut,
    UserSelectableField,
    UserUpdate,
    UserUsername,
)
from .service import create_user

router = APIRouter(prefix="/user", tags=["User"])


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    responses=res.register
)
async def register(
    user: UserRegister,
    session: SessionDep,
    request: Request,
    bg_tasks: BackgroundTasks
):
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
    new_user = await create_user(session, User(**user.model_dump()))
    token = create_jwt({"vrf": new_user.id}, timedelta(days=1))
    if not settings.DEVELOPMENT:
        bg_tasks.add_task(
            send_verify_email,
            user.email,
            request.url_for("verify_user", token=token)._url
        )
    else:
        print(token)
    return UserId(id=new_user.id)


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
    user_id = (await session.execute(stmt)).scalar_one_or_none()
    await session.commit()
    if user_id is None:
        raise BadRequestException("User has been verified.")
    return Message("User verified.")


# สร้าง token สำหรับการเปลี่ยนรหัสผ่าน
# POST /forgot/password
# TODO: รับ email เข้ามาแล้วหา user id จาก email
# แล้วสร้าง JWT ที่มี claim ที่ชื่อว่า passwd มีค่าเป็น user id
# และมีอายุ 30 นาที แล้วส่งไปที่ email ของ user นั้น
# Return: Message("Password reset email sent.")


# รับ token และ password ใน body แล้วเปลี่ยนรหัสผ่าน
# PATCH /password
# Return: Message("Password changed.")


@router.get("/me", responses=res.get_self_info)
async def get_self_info(payload: UserJWTDep, session: SessionDep):
    '''
    ดึงข้อมูลของผู้ใช้งานของตัวเอง แต่ไม่รวม date_created และ properties
    '''
    user_id = payload.sub
    user = (await session.execute(
        select(User).
        where(User.id == user_id, User.is_active == True)
    )).scalar_one_or_none()
    return UserOut.model_validate(user)


@router.patch("/me", responses=res.update_self_info)
async def update_self_info(user: UserUpdate, payload: UserJWTDep, session: SessionDep):
    '''
    แก้ไขข้อมูลของผู้ใช้งานของตัวเอง

    ส่งข้อมูลที่ต้องการแก้ไขเท่านั้น ข้อมูลที่ไม่ได้ส่งมาจะไม่ถูกเปลี่ยนแปลง

    response จะมีข้อมูลที่ถูกเปลี่ยนแปลงเท่านั้น
    '''
    user_id = payload.sub
    user_values = user.model_dump(exclude_unset=True)
    user_cols = (getattr(User, key) for key in user_values)
    stmt = (
        update(User).
        where(User.id == user_id, User.is_active == True).
        values(**user_values).
        returning(*user_cols)
    )
    result = (await session.execute(stmt)).one_or_none()
    await session.commit()
    if result is None:
        raise NotFoundException("User not found.")
    return result._asdict()


# ใส่ username สำหรับผู้ใช้ที่ไม่มี username
# PATCH /me/username
# if มี username แล้วให้ ไม่ต้องทำอะไร
# Return UserUsername
@router.patch("/me/username")
async def set_user_username(body: UserUsername, payload: UserJWTDep, session: SessionDep):
    user_id = payload.sub
    pattern = r'^[a-zA-Z][a-zA-Z0-9_-]{3,254}$'
    if not bool(re.match(pattern, body.username)) :
        raise BadRequestException("Bad username")
    stmt = (
        update(User).
        where(User.id == user_id, User.is_active == True,User.username == None).
        values(username=body.username)
    )
    try :
        count = (await session.execute(stmt)).rowcount
        if count <= 0 :
            raise BadRequestException("u alreay has username")
        await session.commit()
    except IntegrityError as e:
        detail = {"type": "IntegrityError", "detail": "Unknown error."}
        if isinstance(e.orig, UniqueViolation):
            detail = parse_unique_violation(e.orig)
        raise IntegrityException(detail=detail)
    return body.username
    


@router.get("/me/{field}", responses=res.get_self_field)
async def get_self_field(
    field: UserSelectableField,
    payload: UserJWTDep,
    session: SessionDep
):
    '''
    ดึงข้อมูลของผู้ใช้งานของตัวเอง เฉพาะ field ที่ต้องการ
    '''
    user_id = payload.sub
    stmt = (
        select(User.__dict__[field]).
        where(User.id == user_id, User.is_active == True)
    )
    result = (await session.execute(stmt)).scalar_one_or_none()
    await session.commit()
    if result is None:
        raise NotFoundException("User not found.")
    return {field: result}


@router.post("/me/follow/{seer_id}")
async def post_follow_seer(seer_id: int, payload: UserJWTDep, session: SessionDep):
    '''
    ติดตามหมอดู
    '''
    user_id = payload.sub
    try:
        await check_active_seer(seer_id, session)
    except NoResultFound:
        raise NotFoundException("Seer not found.")
    stmt = (
        insert(FollowSeer).
        values(user_id=user_id, seer_id=seer_id).
        returning(FollowSeer.c.seer_id)
    )
    try:
        result = (await session.scalars(stmt)).one()
    except NoResultFound:
        raise InternalException("Failed to follow seer.")
    await session.commit()
    return UserId(id=result)


@router.delete("/me/follow/{seer_id}")
async def delete_follow_seer(seer_id: int, payload: UserJWTDep, session: SessionDep):
    '''
    เลิกติดตามหมอดู
    '''
    user_id = payload.sub
    delete_stmt = (
        delete(FollowSeer)
        .where(
            FollowSeer.c.seer_id == seer_id,
            FollowSeer.c.user_id == user_id
        )
    )
    count = (await session.execute(delete_stmt)).rowcount
    await session.commit()
    return RowCount(count=count)


@router.post("/delete")
async def delete_user(id: int = None, session: SessionDep = None):
    '''
    For testing purpose only.
    '''
    stmt = delete(User)
    if id is not None:
        stmt = stmt.where(User.id == id)
    stmt = stmt.returning(User.id)
    result = await session.execute(stmt)
    await session.commit()
    return {"statement": str(stmt), "result": result.scalars().all()}
