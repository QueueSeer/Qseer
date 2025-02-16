from datetime import timedelta, timezone
from sqlalchemy import asc, desc, insert, select, update
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import SortingOrder
from app.core.error import BadRequestException, NotFoundException
from app.database.models import (
    Activity,
    Appointment,
    ApmtStatus,
    FPStatus,
)
from .schemas import *
from .time_slots import get_free_time_slots


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

    BKK = timezone(timedelta(hours=7))
    if start_time.tzinfo is None:
        start_time = start_time.replace(tzinfo=BKK)
    else:
        start_time = start_time.astimezone(BKK)
    if end_time.tzinfo is None:
        end_time = end_time.replace(tzinfo=BKK)
    else:
        end_time = end_time.astimezone(BKK)

    slots = await get_free_time_slots(
        session,
        seer_id, package_id,
        start_time.date(), start_time.date(),
        duration
    )
    if (start_time, end_time) not in slots:
        raise BadRequestException("Time slot not available.")

    stmt = insert(Activity).values(type="appointment").returning(Activity.id)
    activity_id = (await session.scalars(stmt)).one()
    stmt = insert(Appointment).values(
        id=activity_id,
        client_id=client_id,
        seer_id=seer_id,
        f_package_id=package_id,
        start_time=start_time,
        end_time=end_time,
        status=status,
        questions=questions,
        confirmation_code=confirmation_code,
    )
    await session.execute(stmt)
    if commit:
        await session.commit()
    return activity_id
