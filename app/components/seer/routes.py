from datetime import timedelta
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Request,
    status,
    Query,
)
from sqlalchemy import insert, text, update
from sqlalchemy.exc import NoResultFound

from app.core.config import settings
from app.core.deps import AdminJWTDep, SortingOrder, UserJWTDep, SeerJWTDep
from app.core.error import (
    BadRequestException,
    NotFoundException,
    InternalException,
)
from app.core.security import (
    create_jwt,
    decode_jwt,
)
from app.core.schemas import Message, UserId, RowCount
from app.database import SessionDep
from app.database.models import Seer, Schedule
from app.trigger.service import send_verify_seer_email

from ..user.service import get_user_email
from . import responses as res
from .package import pkg_api, me_api, id_api
from .schemas import *
from .service import *


router = APIRouter(prefix="/seer", tags=["Seer"])


@router.get("/search", responses=res.search_seers)
async def search_seers(
    session: SessionDep,
    last_id: int = None,
    limit: int = Query(10, ge=1, le=100),
    display_name: str = None,
    rating: float = None,
    is_available: bool = True,
    direction: SortingOrder = 'asc',
):
    '''
    [Public] ค้นหาหมอดู

    Parameters:
    ----------
    - **last_id** (int, optional): สำหรับการแบ่งหน้า
        กรอง auction_id < last_id เมื่อ direction เป็น desc
        และ auction_id > last_id เมื่อ direction เป็น asc
    - **limit** (int, optional): จำนวนรายการที่ต้องการ
    - **display_name**: กรองชื่อผู้หมอดูที่ขึ้นต้นตามที่กำหนด
    - **rating**: คะแนนขั้นต่ำที่ต้องการ
    - **is_available**: กรองหมอดูที่พร้อมรับงาน
    '''
    return await searching_seers(
        session,
        last_id,
        limit,
        display_name,
        rating,
        is_available,
        direction
    )


@router.post("/signup", responses=res.seer_signup)
async def seer_signup(
    seer_reg: SeerIn,
    payload: UserJWTDep,
    session: SessionDep,
    request: Request,
    bg_tasks: BackgroundTasks
):
    '''
    [User] สมัครเป็นหมอดู

    - **experience**: ไม่บังคับ เป็นวันที่ เพื่อบอกประสบการณ์การดูดวง
    - **description**: ไม่บังคับ คำอธิบาย แนะนำตัว
    - **primary_skill**: ไม่บังคับ ศาสตร์ดูดวงหลัก
    '''
    seer_id = await create_seer(session, seer_reg, payload.sub)
    token = create_jwt({"seer_confirm": seer_id}, timedelta(days=1))
    if not settings.DEVELOPMENT:
        bg_tasks.add_task(
            send_verify_seer_email,
            await get_user_email(payload.sub, session),
            request.url_for("seer_confirm", token=token)._url
        )
    else:
        print(token)
    return UserId(id=seer_id)


@router.post("/signup/resend-email")
async def resend_seer_signup_email(
    payload: UserJWTDep,
    session: SessionDep,
    request: Request,
):
    '''
    [User] ส่ง email สำหรับยืนยันเป็นหมอดูอีกรอบ สำหรับผู้ใช้งานที่ยังไม่ได้ยืนยันเป็นหมอดู
    ส่งใหม่ได้ทุก 5 นาที
    '''
    stmt = (
        update(Seer).
        where(
            Seer.id == payload.sub,
            Seer.is_active == False,
            Seer.date_created < func.now() - text("INTERVAL '5 m'")
        ).
        values(date_created=func.now()).
        returning(Seer.id)
    )
    try:
        seer_id = (await session.scalars(stmt)).one()
    except NoResultFound:
        raise BadRequestException("Email sent too soon.") 
    token = create_jwt({"seer_confirm": seer_id}, timedelta(days=1))
    if not settings.DEVELOPMENT:
        success = await send_verify_seer_email(
            await get_user_email(payload.sub, session),
            request.url_for("seer_confirm", token=token)._url
        )
        if not success:
            raise InternalException({"detail": "Failed to send email."})
    else:
        print(token)
    await session.commit()
    return Message("Email sent.")


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


router_me = APIRouter(prefix="/me", tags=["Seer Me"])


@router_me.get("", responses=res.get_seer_me)
async def get_seer_me(payload: SeerJWTDep, session: SessionDep):
    '''
    [Seer] ดูข้อมูลหมอดูตัวเอง
    '''
    try:
        return await get_self_seer(session, payload.sub)
    except NoResultFound:
        raise NotFoundException("Seer not found.")


@router_me.patch("", responses=res.update_seer_me)
async def update_seer_me(
    seer_update: SeerUpdate,
    payload: SeerJWTDep,
    session: SessionDep
):
    '''
    [Seer] แก้ไขข้อมูลหมอดูตัวเอง ส่งแค่ข้อมูลที่ต้องการแก้ไข
    '''
    rowcount = await update_seer(session, payload.sub, seer_update)
    if rowcount == 0:
        raise NotFoundException("Seer not found.")
    return seer_update.model_dump(exclude_unset=True)

@router_me.put("/schedule", responses=res.edit_seer_schedule)
async def edit_seer_schedule(
    schedules: list[SeerScheduleIn],
    payload: SeerJWTDep,
    session: SessionDep
):
    '''
    [Seer] แก้ไขตารางเวลาหมอดู

    Details:
    - ถ้ามีตารางเวลาที่อยู่ติดกันหรือซ้อนทับกัน จะถือว่าเป็นตารางเวลาเดียวกัน
    - day ภายใน schedules คือเลข 0-6 แทนวันจันทร์-อาทิตย์
    - เมิน microsecond ใน start_time และ end_time
    - ถ้า end_time มีค่าเป็น 00:00:00 จะถือว่าเป็น 24:00:00
    - inclusive start_time, exclusive end_time
    - format เวลา คือ "HH:MM:SS" หรือ "HH:MM:SS+07:00"
    '''
    sch_rows = await get_schedules(session, payload.sub)
    merged = simplify_schedules(schedules)
    to_add = []
    if len(merged) > len(sch_rows):
        to_add = merged[len(sch_rows):]
        merged = merged[:len(sch_rows)]

    change, will_del = sch_rows[:len(merged)], sch_rows[len(merged):]

    if will_del:
        count = await delete_extra_schedules(
            session,
            payload.sub,
            will_del[0].day,
            will_del[0].start_time
        )
        if count != len(will_del):
            raise InternalException("Bug: delet_count != len(will_del)")

    for sch1, sch2 in zip(merged, change):
        sch2.start_time = sch1.start_time
        sch2.end_time = sch1.end_time
        sch2.day = sch1.day

    session.add_all([
        Schedule(
            seer_id=payload.sub,
            start_time=sch.start_time,
            end_time=sch.end_time,
            day=sch.day
        )
        for sch in to_add
    ])

    await session.commit()
    return [
        SeerScheduleIn.model_validate(sch)
        for sch in await get_schedules(session, payload.sub)
    ]


@router_me.post("/dayoff", status_code=201, responses=res.seer_dayoff)
async def add_seer_dayoff(day_off: SeerDayOff, payload: SeerJWTDep, session: SessionDep):
    '''
    [Seer] เพิ่มวันหยุดหมอดู ถ้าเพิ่มวันหยุดที่มีอยู่แล้วจะไม่เกิดอะไรขึ้น
    '''
    return await add_dayoff(day_off, payload.sub, session)


@router_me.delete("/dayoff/{day_off}")
async def delete_seer_dayoff(day_off: dt.date, payload: SeerJWTDep, session: SessionDep):
    '''
    [Seer] ลบวันหยุดหมอดู
    '''
    count = await delete_dayoff(day_off, payload.sub, session)
    return RowCount(count=count)


router_id = APIRouter(prefix="/{seer_id}", tags=["Seer Id"])


@router_id.get("", responses=res.seer_info)
async def seer_info(seer_id: int, session: SessionDep):
    '''
    [Public] ดูข้อมูลหมอดู
    '''
    try:
        return await get_seer_info(session, seer_id)
    except NoResultFound:
        raise NotFoundException("Seer not found.")


@router_id.get("/followers", responses=res.seer_followers)
async def seer_followers(
    session: SessionDep,
    seer_id: int,
    last_id: int = 0,
    limit: int = Query(10, ge=1, le=1000)
):
    '''
    [Public] ดูรายชื่อผู้ติดตามหมอดู (ไม่ได้ตรวจสอบค่า is_active ของผู้ติดตาม)

    Parameters:
    - **last_id**: ไม่บังคับ กรองผู้ติดตามที่มี id มากกว่า last_id
    - **limit**: ไม่บังคับ จำนวนผู้ติดตามที่ส่งกลับ
    '''
    return await get_seer_followers(session, seer_id, last_id, limit)


@router_id.get("/total_followers", responses=res.seer_total_followers)
async def seer_total_followers(seer_id: int, session: SessionDep):
    '''
    [Public] ดูจำนวนผู้ติดตามหมอดู (ไม่ได้ตรวจสอบค่า is_active ของผู้ติดตาม)
    '''
    return RowCount(count=await get_seer_total_followers(session, seer_id))


@router_id.get("/calendar", responses=res.seer_calendar)
async def seer_calendar(seer_id: int, session: SessionDep):
    '''
    [Public] ดูข้อมูลตารางเวลารายสัปดาห์และวันหยุดของหมอดู
    วันหยุดที่ส่งกลับมาจะไม่มีวันหยุดในอดีต และมีไม่เกิน 90 วัน

    day ภายใน schedules คือเลข 0-6 แทนวันจันทร์-อาทิตย์
    '''
    try:
        stmt = (
            select(Seer.break_duration).
            join(User, Seer.id == User.id).
            where(
                Seer.id == seer_id,
                User.is_active == True,
                Seer.is_active == True
            )
        )
        break_duration = (await session.scalars(stmt)).one()
    except NoResultFound:
        raise NotFoundException("Seer not found.")
    schedules = await get_schedules(session, seer_id)
    day_offs = await get_day_offs(session, seer_id, limit=90)
    return SeerCalendar(
        seer_id=seer_id,
        break_duration=break_duration,
        schedules=schedules,
        day_offs=day_offs
    )


@router_id.patch("/verify", responses=res.verify_seer)
async def verify_seer(
    session: SessionDep,
    payload: AdminJWTDep,
    seer_id: int,
):
    '''
    [Admin] ยืนยันหมอดู
    '''
    stmt = (
        update(Seer).
        where(Seer.id == seer_id, Seer.verified_at == None).
        values(verified_at=func.now()).
        returning(Seer.id)
    )
    try:
        seer_id = (await session.scalars(stmt)).one()
    except NoResultFound:
        raise NotFoundException("Seer not found or verified.")
    await session.commit()
    return UserId(id=seer_id)


router_me.include_router(me_api)
router_id.include_router(id_api)
router.include_router(pkg_api)
router.include_router(router_me)
router.include_router(router_id)
