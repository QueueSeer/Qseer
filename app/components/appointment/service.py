from datetime import date, timedelta
from sqlalchemy import asc, desc, insert, select, update
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import SortingOrder
from app.core.error import BadRequestException, NotFoundException
from app.database.models import (
    Appointment,
    ApmtStatus,
    coin,
    FPStatus,
)
from ..seer.package.fortune.service import (
    get_fpackage_time_slots,
)
from .schemas import *


async def get_appointments(
    session: AsyncSession,
    client_id: int = None,
    seer_id: int = None,
    status: ApmtStatus = None,
    direction: SortingOrder = 'desc',
    last_id: int = None,
    limit: int = 10,
):
    order = asc if direction == 'asc' else desc
    stmt = (
        AppointmentBrief.select().
        order_by(order(Appointment.id))
    )
    if limit is not None:
        stmt = stmt.limit(limit)
    if last_id is not None:
        if direction == 'asc':
            stmt = stmt.where(Appointment.id > last_id)
        else:
            stmt = stmt.where(Appointment.id < last_id)
    if client_id is not None:
        stmt = stmt.where(Appointment.client_id == client_id)
    if seer_id is not None:
        stmt = stmt.where(Appointment.seer_id == seer_id)
    if status is not None:
        stmt = stmt.where(Appointment.status == status)
    return [
        AppointmentBrief.create_from(r)
        for r in (await session.execute(stmt))
    ]


async def get_appointment_by_id(
    session: AsyncSession,
    apmt_id: int,
    user_id: int = None
):
    stmt = (
        AppointmentOut.select().
        where(Appointment.id == apmt_id)
    )
    if user_id is not None:
        stmt = stmt.where(
            (Appointment.client_id == user_id) |
            (Appointment.seer_id == user_id)
        )
    return AppointmentOut.create_from(
        (await session.execute(stmt)).one()
    )


async def get_appointments_in_date_range(
    session: AsyncSession,
    seer_id: int,
    start_date: date,
    end_date: date,
    exclude_cancelled: bool = False
):
    end_date = end_date + timedelta(days=1)
    stmt = (
        select(
            Appointment.id,
            Appointment.seer_id,
            Appointment.f_package_id.label('package_id'),
            Appointment.start_time,
            Appointment.end_time,
            Appointment.status,
        ).
        where(
            Appointment.seer_id == seer_id,
            (
                (Appointment.start_time >= start_date) &
                (Appointment.start_time < end_date)
            ) | (
                (Appointment.end_time > start_date) &
                (Appointment.end_time <= end_date)
            )
        )
    )
    if exclude_cancelled:
        stmt = stmt.where(
            Appointment.status != ApmtStatus.u_cancelled,
            Appointment.status != ApmtStatus.s_cancelled
        )
    return [
        AppointmentPublic.model_validate(r)
        for r in (await session.execute(stmt))
    ]


async def create_appointment(
    session: AsyncSession,
    client_id: int,
    seer_id: int,
    package_id: int,
    start_time: datetime,
    end_time: datetime = None,
    status: ApmtStatus = ApmtStatus.pending,
    questions: list[str] = None,
    confirmation_code: str = '',
    *,
    duration: timedelta = None,
    commit: bool = True
):
    if questions is None:
        questions = []
    if package_id is None and end_time is None:
        raise ValueError("end_time must be provided if package_id is None")

    stmt = (
        select(FortunePackage.duration).
        where(
            FortunePackage.seer_id == seer_id,
            FortunePackage.id == package_id,
            FortunePackage.status == FPStatus.published,
            FortunePackage.duration != None
        )
    )
    try:
        if duration is None:
            duration = (await session.scalars(stmt)).one()
    except NoResultFound:
        raise NotFoundException("Fortune package not found.")
    
    if package_id is not None and end_time is None:
        end_time = start_time + duration
    elif package_id is not None and end_time is not None:
        if end_time - start_time != duration:
            raise ValueError("end_time does not match package duration")

    slots = await get_fpackage_time_slots(
        session,
        seer_id, package_id,
        start_time.date(), start_time.date(),
        duration
    )
    if (start_time, end_time) not in slots:
        raise BadRequestException("Time slot not available.")

    apmt = Appointment(
        client_id=client_id,
        seer_id=seer_id,
        f_package_id=package_id,
        start_time=start_time,
        end_time=end_time,
        status=status,
        questions=questions,
        confirmation_code=confirmation_code,
    )
    session.add(apmt)
    if commit:
        await session.commit()
    return apmt.id
