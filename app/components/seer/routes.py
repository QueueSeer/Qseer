from datetime import timedelta
from fastapi import (
    APIRouter,
    BackgroundTasks,
    HTTPException,
    Request,
    status,
)
from sqlalchemy import delete, insert, select, update
from sqlalchemy.exc import NoResultFound

from app.core.config import settings
from app.core.deps import UserJWTDep, SeerJWTDep
from app.core.error import BadRequestException, NotFoundException
from app.core.security import (
    create_jwt,
    decode_jwt,
)
from app.core.schemas import Message, UserId, RowCount
from app.database import SessionDep
from app.database.models import Seer, User, Schedule, DayOff
from app.email.service import send_verify_email

from ..user.service import get_user_email
from . import responses as res
from .schemas import *
from .service import *


router = APIRouter(prefix="/seer", tags=["Seer"])


@router.post("/signup", responses=res.seer_signup)
async def seer_signup(
    seer_reg: SeerRegister,
    payload: UserJWTDep,
    session: SessionDep,
    request: Request,
    bg_tasks: BackgroundTasks
):
    '''
    สมัครเป็นหมอดู

    - **experience**: ไม่บังคับ เป็นวันที่ เพื่อบอกประสบการณ์การดูดวง
    - **description**: ไม่บังคับ คำอธิบาย แนะนำตัว
    - **primary_skill**: ไม่บังคับ ศาสตร์ดูดวงหลัก
    '''
    seer_id = await create_seer(session, seer_reg, payload.sub)
    token = create_jwt({"seer_confirm": seer_id}, timedelta(days=1))
    if not settings.DEVELOPMENT:
        bg_tasks.add_task(
            send_verify_email,
            await get_user_email(payload.sub, session),
            request.url_for("seer_confirm", token=token)._url
        )
    else:
        print(token)
    return UserId(id=seer_id)


@router.get("/confirm/{token}", responses=res.seer_confirm)
async def seer_confirm(token: str, session: SessionDep):
    '''
    ยืนยันการสมัครเป็นหมอดู
    '''
    payload = decode_jwt(token, require=["exp", "seer_confirm"])
    seer_id = payload["seer_confirm"]
    stmt = (
        update(Seer).
        where(Seer.id == seer_id, Seer.is_active == False).
        values(is_active=True).
        returning(Seer.id)
    )
    seer_id = (await session.scalars(stmt)).one_or_none()
    await session.commit()
    if seer_id is None:
        raise BadRequestException("Already confirmed.")
    return Message("Confirmation successful.")


@router.get("/{seer_id}", responses=res.seer_info)
async def seer_info(seer_id: int, session: SessionDep):
    '''
    ดูข้อมูลหมอดู
    '''
    try:
        return await get_seer_info(seer_id, session)
    except NoResultFound:
        raise NotFoundException("Seer not found.")


# ดูรายชื่อผู้ติดตามหมอดู
# id, username, display_name, image
# GET /{seer_id}/followers


@router.get("/{seer_id}/calendar", responses=res.seer_calendar)
async def seer_calendar(seer_id: int, session: SessionDep):
    '''
    ดูข้อมูลตารางเวลารายสัปดาห์และวันหยุดของหมอดู
    วันหยุดที่ส่งกลับมาจะไม่มีวันหยุดในอดีต

    day ภายใน schedules คือเลข 0-6 แทนวันจันทร์-อาทิตย์

    API นี้ไม่มีการตรวจสอบว่าหมอดูมีอยู่จริงหรือไม่
    '''
    return await get_calendar(seer_id, session)


@router.post(
    "/me/schedule",
    status_code=status.HTTP_201_CREATED,
    responses=res.seer_schedule
)
async def seer_schedule(schedule: SeerScheduleIn, payload: SeerJWTDep, session: SessionDep):
    '''
    สร้างตารางเวลาหมอดู

    day ภายใน schedules คือเลข 0-6 แทนวันจันทร์-อาทิตย์
    ''' 
    schedule_values = schedule.model_dump()
    schedule_values["seer_id"] = payload.sub
    stmt = (
        insert(Schedule).
        values(schedule_values).
        returning(Schedule.id)
    )
    schedule_id = (await session.scalars(stmt)).one()
    return SeerScheduleId(seer_id=payload.sub, id=schedule_id)


@router.patch("/me/schedule/{schedule_id}", responses=res.update_seer_schedule)
async def update_seer_schedule(
    schedule_id: int,
    schedule: SeerScheduleUpdate,
    payload: SeerJWTDep,
    session: SessionDep
):
    '''
    แก้ไขตารางเวลาหมอดู
    '''
    try:
        return await update_schedule(
            payload.sub,
            schedule_id,
            schedule,
            session
        )
    except NoResultFound:
        raise NotFoundException("Schedule not found.")


@router.delete("/me/schedule/{schedule_id}", responses=res.delete_seer_schedule)
async def delete_seer_schedule(schedule_id: int, payload: SeerJWTDep, session: SessionDep):
    '''
    ลบตารางเวลาหมอดู
    '''
    count = await delete_schedule(payload.sub, schedule_id, session)
    return RowCount(count=count)


@router.post("/me/dayoff", status_code=201, responses=res.seer_dayoff)
async def add_seer_dayoff(day_off: SeerDayOff, payload: SeerJWTDep, session: SessionDep):
    '''
    เพิ่มวันหยุดหมอดู ถ้าเพิ่มวันหยุดที่มีอยู่แล้วจะไม่เกิดอะไรขึ้น
    '''
    return await add_dayoff(day_off, payload.sub, session)


@router.delete("/me/dayoff/{day_off}")
async def delete_seer_dayoff(day_off: dt.date, payload: SeerJWTDep, session: SessionDep):
    '''
    ลบวันหยุดหมอดู
    '''
    count = await delete_dayoff(day_off, payload.sub, session)
    return RowCount(count=count)
