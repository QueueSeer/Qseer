from datetime import timedelta
from fastapi import (
    APIRouter,
    HTTPException,
    Request,
    status,
)
from sqlalchemy import delete, select, update

from app.core.deps import UserJWTDep
from app.core.error import BadRequestException, NotFoundException
from app.core.security import (
    create_jwt,
    decode_jwt,
)
from app.core.schemas import Message, UserId
from app.database import SessionDep
from app.database.models import User
from . import responses as res
from .schemas import (
    UserRegister,
    UserOut,
    UserSelectableField,
    UserUpdate,
)
from .service import create_user

router = APIRouter(prefix="/user", tags=["User"])

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
    new_user = await create_user(session, User(**user.model_dump()))
    token = create_jwt({"vrf": new_user.id}, timedelta(days=1))
    # TODO: send email to user
    print(request.url_for("verify_user", token=token)._url)
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


# ติดตามหมอดู
# POST /follow/{seer_id}
@router.post("/follow/{seer_id}", responses=res.get_self_field)
async def get_follow_seer():
    pass

# เลิกติดตามหมอดู
# DELETE /follow/{seer_id}


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
