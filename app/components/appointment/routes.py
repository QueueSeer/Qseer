from datetime import date
import random
from string import ascii_uppercase, digits
from fastapi import APIRouter, Query
from sqlalchemy.exc import NoResultFound

from app.core.deps import UserJWTDep, SeerJWTDep
from app.core.error import (
    BadRequestException,
    NotFoundException,
)
from app.core.schemas import Message, RowCount
from app.database import SessionDep
from app.database.models import ApmtStatus, Seer, TxnType, TxnStatus

from ..transaction.service import change_user_coins
from . import responses as res
from .schemas import *
from .service import *
from .time_slots import get_appointments_in_date_range

router = APIRouter(prefix="/appointment", tags=["Appointment"])


@router.get("/sent", responses=res.get_appointments)
async def get_sent_appointments(
    session: SessionDep,
    payload: UserJWTDep,
    last_id: int = None,
    limit: int = Query(10, ge=1, le=100),
    seer_id: int = None,
    status: ApmtStatus = None,
    direction: SortingOrder = 'desc'
):
    '''
    ดูรายการนัดหมายที่เราเป็นคนจอง (ฝั่งผู้ใช้)

    Parameters:
    ----------
    - **last_id** (int, optional): สำหรับการแบ่งหน้า
        กรอง appointment_id < last_id เมื่อ direction เป็น desc
        และ appointment_id > last_id เมื่อ direction เป็น asc
    - **limit** (int, optional): จำนวนรายการที่ต้องการ
    - **seer_id** (int, optional): กรอง appointment ที่ seer_id ตรงกับที่กำหนด
    - **status** (ApmtStatus, optional): กรอง appointment ที่ status ตรงกับที่กำหนด
    - **direction** ('asc' | 'desc', optional): ทิศทางการเรียงลำดับ
    '''
    return await get_appointments(
        session=session,
        client_id=payload.sub,
        seer_id=seer_id,
        status=status,
        direction=direction,
        last_id=last_id,
        limit=limit
    )

 
@router.get("/received", responses=res.get_appointments)
async def get_received_appointments(
    session: SessionDep,
    payload: SeerJWTDep,
    last_id: int = None,
    limit: int = Query(10, ge=1, le=100),
    client_id: int = None,
    status: ApmtStatus = None,
    direction: SortingOrder = 'desc'
):
    '''
    ดูรายการนัดหมายที่เราเป็นคนถูกจอง (ฝั่งหมอดู)

    Parameters:
    ----------
    - **last_id** (int, optional): สำหรับการแบ่งหน้า
        กรอง appointment_id < last_id เมื่อ direction เป็น desc
        และ appointment_id > last_id เมื่อ direction เป็น asc
    - **limit** (int, optional): จำนวนรายการที่ต้องการ
    - **client_id** (int, optional): กรอง appointment ที่ client_id ตรงกับที่กำหนด
    - **status** (ApmtStatus, optional): กรอง appointment ที่ status ตรงกับที่กำหนด
    - **direction** ('asc' | 'desc', optional): ทิศทางการเรียงลำดับ
    '''
    return await get_appointments(
        session=session,
        client_id=client_id,
        seer_id=payload.sub,
        status=status,
        direction=direction,
        last_id=last_id,
        limit=limit
    )


@router.get("/user-cancelled-count", responses=res.get_cancelled_count)
async def get_user_cancelled_count(
    session: SessionDep,
    payload: UserJWTDep
):
    '''
    ดูจำนวนครั้งที่ผู้ใช้ยกเลิกการนัดหมายในเดือนนี้
    '''
    return RowCount(count=await get_cancelled_count(session, payload.sub))


@router.get("/{apmt_id}", responses=res.get_an_appointment)
async def get_an_appointment(
    session: SessionDep,
    payload: UserJWTDep,
    apmt_id: int
):
    '''
    ดูรายละเอียดของการนัดหมาย โดยระบุ `apmt_id` (appointment_id)
    ดูได้เฉพาะการนัดหมายที่ตัวเองเกี่ยวข้องเท่านั้นหรือเป็น admin
    '''
    user_id = None if payload.is_admin else payload.sub
    try:
        return await get_appointment_by_id(
            session=session,
            apmt_id=apmt_id,
            user_id=user_id
        )
    except NoResultFound:
        raise NotFoundException("Appointment not found.")


@router.patch("/{apmt_id}/status/complete", responses=res.complete_appointment)
async def seer_complete_appointment(
    session: SessionDep,
    payload: SeerJWTDep,
    apmt_id: int
):
    '''
    หมอดูจบการนัดหมาย
    '''
    await complete_appointment(session, apmt_id, payload.sub)
    return Message("Appointment completed.")


@router.patch("/{apmt_id}/status/user-cancel", responses=res.user_cancel)
async def user_cancel_appointment(
    session: SessionDep,
    payload: UserJWTDep,
    apmt_id: int
):
    '''
    ผู้ใช้ยกเลิกการนัดหมาย

    เงื่อนไข:
    - ยกเลิกนัดล่วงหน้าอย่างน้อย 1 ชม.
    - หากยกเลิกเกิน 3 ครั้งในเดือนเดียวกัน จะไม่ได้รับเงินคืน
    '''
    till = await time_till_appointment(session, apmt_id)
    if till.total_seconds() < 3600:
        raise BadRequestException(
            "Cannot cancel within 1 hour of appointment."
        )
    
    cancel = await get_cancelled_count(session, payload.sub)
    await cancel_appointment(
        session,
        apmt_id,
        ApmtStatus.u_cancelled,
        user_id=payload.sub,
        refund=cancel < CANCEL_QUOTA
    )
    return Message("Appointment cancelled.")


@router.patch("/{apmt_id}/status/seer-cancel", responses=res.seer_cancel)
async def seer_cancel_appointment(
    session: SessionDep,
    payload: SeerJWTDep,
    apmt_id: int
):
    '''
    หมอดูยกเลิกการนัดหมาย

    ไม่มีเงื่อนไขในการยกเลิก
    '''
    await cancel_appointment(
        session,
        apmt_id,
        ApmtStatus.s_cancelled,
        seer_id=payload.sub,
        refund=True
    )
    return Message("Appointment cancelled.")


@router.get("/seer/{seer_id}", responses=res.get_seer_appointments)
async def get_seer_appointments(
    session: SessionDep,
    seer_id: int,
    start_date: date = None,
    end_date: date = None,
):
    '''
    ดูรายการนัดหมายของหมอดู
    ในช่วงระหว่างวันที่ `start_date` ถึง `end_date` (inclusive)

    เงื่อนไข:
    - ช่วง `start_date` ถึง `end_date` ห้ามเกิน 90 วัน
    - ถ้าไม่ระบุ `start_date` และ `end_date` จะดึงแค่การนัดหมายของวันนี้
    - ถ้าระบุ `start_date` หรือ `end_date` อย่างใดอย่างหนึ่ง
        จะถือว่าค่าที่ไม่ได้กำหนด มีค่าเท่ากับอีกค่าหนึ่ง
    '''
    if start_date is None and end_date is None:
        start_date = end_date = date.today()
    elif start_date is None:
        start_date = end_date
    elif end_date is None:
        end_date = start_date

    if (end_date - start_date).days + 1 > 90:
        raise BadRequestException("Date range must not exceed 90 days.")
    
    return get_appointments_in_date_range(
        session=session,
        seer_id=seer_id,
        start_date=start_date,
        end_date=end_date,
        exclude_cancelled=True
    )


@router.post(
    "/seer",
    status_code=201,
    responses=res.make_an_appointment
)
async def make_an_appointment(
    session: SessionDep,
    payload: UserJWTDep,
    apmt: AppointmentIn
):
    '''
    ผู้ใช้จองคิวหมอดู
    '''
    if apmt.start_time <= datetime.now(apmt.start_time.tzinfo):
        raise BadRequestException("Cannot book past appointments.")

    stmt = (
        select(
            User.display_name,
            Seer.socials_name,
            Seer.socials_link,
            FortunePackage.name.label('package_name'),
            FortunePackage.duration,
            FortunePackage.price,
            FortunePackage.question_limit
        ).
        join(User.seer).
        join(FortunePackage, FortunePackage.seer_id == User.id).
        where(
            FortunePackage.seer_id == apmt.seer_id,
            FortunePackage.id == apmt.package_id,
            FortunePackage.status == FPStatus.published,
            FortunePackage.duration != None,
            FortunePackage.price != None
        )
    )
    try:
        row = (await session.execute(stmt)).one()
    except NoResultFound:
        raise NotFoundException("Fortune package not found.")
    
    if row.question_limit >= 0 and len(apmt.questions) > row.question_limit:
        raise BadRequestException("Exceeded question limit.")
    
    stmt = (
        select(User.display_name).
        where(
            User.id == payload.sub,
            User.is_active == True,
            User.coins >= row.price
        )
    )
    try:
        user_display_name = (await session.scalars(stmt)).one()
    except NoResultFound:
        raise BadRequestException("Insufficient coins.")
    
    code = ''.join(random.choices(ascii_uppercase + digits, k=6))
    apmt_id = await create_appointment(
        session,
        payload.sub,
        apmt.seer_id,
        apmt.package_id,
        apmt.start_time,
        questions=apmt.questions,
        confirmation_code=code,
        duration=row.duration,
        commit=False
    )

    user_coins, txn_id = await change_user_coins(
        session, payload.sub,
        -row.price,
        TxnType.appointment,
        TxnStatus.hold,
        apmt_id,
    )
    # TODO: Set trigger to send notification
    return AppointmentCreated(
        apmt_id=apmt_id,
        start_time=apmt.start_time,
        code=code,
        seer_id=apmt.seer_id,
        seer_display_name=row.display_name,
        seer_socials_name=row.socials_name,
        seer_socials_link=row.socials_link,
        package_id=apmt.package_id,
        package_name=row.package_name,
        user_display_name=user_display_name,
        total=row.price,
    )
