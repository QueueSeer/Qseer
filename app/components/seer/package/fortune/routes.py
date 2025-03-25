from datetime import date
from fastapi import APIRouter, Query
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound

from app.components.appointment.time_slots import get_free_time_slots
from app.core.deps import SeerJWTDep, SortingOrder
from app.core.error import (
    BadRequestException,
    IntegrityException,
    NotFoundException
)
from app.core.schemas import RowCount
from app.database import SessionDep
from app.database.models import FPStatus

from . import responses as res
from .schemas import *
from .service import *

# /seer/package/fortune
router = APIRouter(prefix="/fortune")


@router.get("/search", responses=res.search_fp)
async def search_fortune_packages(
    session: SessionDep,
    last_id: int = 0,
    limit: int = Query(10, ge=1, le=100),
    name: str = None,
    price_min: float = None,
    price_max: float = None,
    duration_min: timedelta = None,
    duration_max: timedelta = None,
    foretell_channel: FPChannel = None,
    reading_type: str = None,
    category: str = None,
    direction: SortingOrder = 'asc',
):
    '''
    [Public] ค้นหาแพ็คเกจดูดวง

    [วิธีการส่งค่า timedelta](https://docs.pydantic.dev/latest/api/standard_library_types/#datetimetimedelta)

    Parameters:
    ----------
    - **last_id** (int, optional): สำหรับการแบ่งหน้า
        กรอง id < last_id เมื่อ direction เป็น desc
        และ id > last_id เมื่อ direction เป็น asc
    - **limit** (int, optional): จำนวนรายการที่ต้องการ
    - **name** (str, optional): กรองชื่อแพ็คเกจ ที่ขึ้นต้นตามที่กำหนด
    - **price_min** (float, optional): กรองราคาต่ำสุดของแพ็คเกจ
    - **price_max** (float, optional): กรองราคาสูงสุดของแพ็คเกจ
    - **duration_min** (timedelta, optional): กรองระยะเวลาต่ำสุดของแพ็คเกจ
    - **duration_max** (timedelta, optional): กรองระยะเวลาสูงสุดของแพ็คเกจ
    - **foretell_channel** (FPChannel, optional): กรองช่องทาย
    - **reading_type** (str, optional): กรองประเภทการอ่าน
    - **category** (str, optional): กรองหมวดหมู่
    - **direction** ('asc' | 'desc', optional): ทิศทางการเรียงลำดับ
    '''
    return await search_fpackage_cards(
        session,
        last_id, limit,
        name,
        price_min, price_max,
        duration_min, duration_max,
        foretell_channel,
        reading_type,
        category,
        direction
    )


# /seer/me/package/fortune
router_me = APIRouter(prefix="/fortune")


@router_me.get("", responses=res.get_self_fortune_package_cards)
async def get_self_fortune_package_cards(
    payload: SeerJWTDep,
    session: SessionDep,
    status: FPStatus = None,
    last_id: int = 0,
    limit: int = Query(10, ge=1, le=100)
):
    '''
    ดูรายการแพ็คเกจดูดวงของตัวเอง
    '''
    return await get_fpackage_cards(
        session, payload.sub,
        status, last_id, limit
    )


@router_me.post("", status_code=201, responses=res.draft_fpackage)
async def draft_fortune_package(
    payload: SeerJWTDep,
    session: SessionDep,
    fortune: FortunePackageDraft
):
    '''
    สร้างแพ็คเกจดูดวงที่มีสถานะเป็น draft

    - **name**: ชื่อแพ็คเกจ ค่าที่จำเป็น
    - **duration**: [วิธีการส่งค่า timedelta](https://docs.pydantic.dev/latest/api/standard_library_types/#datetimetimedelta)
    - **question_limit**: จำนวนคำถามที่ผู้ใช้งานสามารถถามได้ ค่าไม่เกิน 6
        โดยค่าที่น้อยกว่า 0 คือไม่จำกัดจำนวนคำถาม และค่าเท่ากับ 0 คือไม่ให้ส่งคำถาม
    - **foretell_channel**: ค่าที่เป็นไปได้คือ "chat", "phone", "video"
    - **required_data**: เป็น list ชื่อข้อมูลที่ต้องการจากผู้ใช้งาน
    ค่าภายในที่เป็นไปได้คือ "name", "birthdate", "phone_number"
    '''
    return await create_draft_fpackage(session, payload.sub, fortune)


@router_me.get("/{package_id}", responses=res.get_self_fortune_package)
async def get_self_fortune_package(
    payload: SeerJWTDep,
    session: SessionDep,
    package_id: int
):
    '''
    ดูรายละเอียดแพ็คเกจดูดวงของตัวเอง
    '''
    try:
        return FortunePackageOut.model_validate(
            await get_seer_fpackage(session, payload.sub, package_id)
        )
    except NoResultFound:
        raise NotFoundException("Fortune package not found.")


@router_me.patch("/{package_id}", responses=res.edit_draft_fpackage)
async def edit_draft_fortune_package(
    payload: SeerJWTDep,
    session: SessionDep,
    package_id: int,
    fortune: FortunePackageEdit
):
    '''
    แก้ไขแพ็คเกจดูดวงที่มีสถานะเป็น draft
    '''
    count = await update_draft_fpackage(
        session, payload.sub, package_id, fortune
    )
    if count == 0:
        raise NotFoundException("Fortune package not found.")
    return fortune.model_dump(mode='json', exclude_unset=True)


@router_me.patch("/{package_id}/status", responses=res.fpackage_status)
async def change_fortune_package_status(
    payload: SeerJWTDep,
    session: SessionDep,
    package_id: int,
    status: FPStatusChange
):
    '''
    เปลี่ยนสถานะแพ็คเกจดูดวงเป็น `published` หรือ `hidden`

    price และ duration จะต้องไม่เป็น None
    '''
    if status.status == FPStatus.draft:
        raise BadRequestException("Cannot change status to draft.")
    stmt = (
        select(FortunePackage.price, FortunePackage.duration).
        where(
            FortunePackage.seer_id == payload.sub,
            FortunePackage.id == package_id
        )
    )
    try:
        row = (await session.execute(stmt)).one()
    except NoResultFound:
        raise NotFoundException("Fortune package not found.")
    if row.price is None:
        raise IntegrityException({
            "detail": "Price is required.",
            "field": "price"
        })
    if row.duration is None:
        raise IntegrityException({
            "detail": "Duration is required.",
            "field": "duration"
        })
    count = await change_fpackage_status(
        session, payload.sub, package_id, status.status
    )
    if count == 0:
        raise NotFoundException("Fortune package not found.")
    return status


@router_me.delete("/{package_id}", responses=res.delete_self_fortune_package)
async def delete_self_fortune_package(
    payload: SeerJWTDep,
    session: SessionDep,
    package_id: int
):
    '''
    ลบแพ็คเกจดูดวงของตัวเอง
    '''
    count = await delete_fpackage(session, payload.sub, package_id)
    return RowCount(count=count)


# /seer/{seer_id}/package/fortune
router_id = APIRouter(prefix="/fortune")


@router_id.get("", responses=res.get_seer_fortune_package_cards)
async def get_seer_fortune_package_cards(
    session: SessionDep,
    seer_id: int,
    last_id: int = 0,
    limit: int = Query(10, ge=1, le=100)
):
    '''
    ดูรายการแพ็คเกจดูดวงของหมอดู
    '''
    return await get_fpackage_cards(
        session, seer_id,
        FPStatus.published, last_id, limit
    )


@router_id.get("/{package_id}", responses=res.get_seer_fortune_package)
async def get_seer_fortune_package(
    session: SessionDep,
    seer_id: int,
    package_id: int
):
    '''
    ดูรายละเอียดแพ็คเกจดูดวงของหมอดู
    '''
    try:
        return FortunePackageOut.model_validate(
            await get_seer_fpackage(
                session, seer_id,
                package_id, FPStatus.published
            )
        )
    except NoResultFound:
        raise NotFoundException("Fortune package not found.")


@router_id.get("/{package_id}/time-slots", responses=res.get_time_slots)
async def get_seer_fortune_package_time_slots(
    session: SessionDep,
    seer_id: int,
    package_id: int,
    start_date: date = None,
    end_date: date = None,
):
    '''
    ดูรายการเวลาที่หมอดูว่างสำหรับแพ็คเกจดูดวง
    ในช่วงระหว่างวันที่ `start_date` ถึง `end_date` (inclusive)
    '''
    if start_date is None and end_date is None:
        start_date = end_date = date.today()
    elif start_date is None:
        start_date = end_date
    elif end_date is None:
        end_date = start_date

    if (end_date - start_date).days + 1 > 90:
        raise BadRequestException("Date range must not exceed 90 days.")
    
    slots = await get_free_time_slots(
        session,
        seer_id, package_id,
        start_date, end_date
    )
    return [TimeSlot(start_time=s[0], end_time=s[1]) for s in slots]
