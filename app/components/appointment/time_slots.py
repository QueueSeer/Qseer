from datetime import date, datetime, time, timedelta
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from app.components.appointment.schemas import AppointmentPublic
from app.components.seer.schemas import SeerSchedule
from app.components.seer.service import get_day_offs, get_schedules
from app.core.error import NotFoundException
from app.database.models import (
    ApmtStatus,
    Appointment,
    AuctionInfo,
    FPStatus,
    FortunePackage,
    Seer,
    User,
)


class TimeRange(BaseModel):
    start_time: datetime
    end_time: datetime

    model_config = ConfigDict(from_attributes=True)


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
            Appointment.end_time > start_date,
            Appointment.start_time < end_date
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


async def get_busy_time_ranges(
    session: AsyncSession,
    seer_id: int,
    start_date: date | datetime,
    end_date: date | datetime
):
    stmt = (
        select(
            AuctionInfo.appoint_start_time.label('start_time'),
            AuctionInfo.appoint_end_time.label('end_time')
        ).
        where(
            AuctionInfo.seer_id == seer_id,
            AuctionInfo.appoint_end_time > start_date,
            AuctionInfo.appoint_start_time < end_date
        )
    )
    return [
        TimeRange.model_validate(a)
        for a in (await get_appointments_in_date_range(
            session, seer_id, start_date, end_date, True
        ))
    ] + [
        TimeRange.model_validate(r)
        for r in (await session.execute(stmt))
    ]


def is_overlapping(
    start1: datetime, end1: datetime,
    start2: datetime, end2: datetime
) -> bool:
    return end1 > start2 and start1 < end2


def daterange(start_date: date, end_date: date):
    days = int((end_date - start_date).days)
    for n in range(days):
        yield start_date + timedelta(n)


def non_overlapping_range(
    start1: datetime, end1: datetime,
    start2: datetime, end2: datetime
) -> list[tuple[datetime, datetime]]:
    non_overlap = []
    if start1 < start2:
        non_overlap.append((start1, min(end1, start2)))
    if end1 > end2:
        non_overlap.append((max(start1, end2), end1))
    return non_overlap


def remaining_slots(
    slot: tuple[datetime, datetime],
    appointments: list[TimeRange]
) -> list[tuple[datetime, datetime]]:
    '''
    รับ time_slot ว่าง 1 ช่องและ list of appointments
    return list of time_slot ว่างที่เหลือ
    '''
    remaining = [slot]
    for appt in appointments:
        new_remaining = []
        for r in remaining:
            non_overlap = non_overlapping_range(
                r[0], r[1],
                appt.start_time, appt.end_time
            )
            new_remaining.extend(non_overlap)
        remaining = new_remaining
    return remaining


async def get_free_time_slots(
    session: AsyncSession,
    seer_id: int,
    package_id: int,
    start_date: date,
    end_date: date,
    package_duration: timedelta = None
):
    stmt = (
        select(Seer.break_duration).
        join(User, Seer.id == User.id).
        where(
            Seer.id == seer_id,
            User.is_active == True,
            Seer.is_active == True
        )
    )
    try:
        break_duration = (await session.scalars(stmt)).one()
    except NoResultFound:
        raise NotFoundException("Seer not found.")

    sch_dict: dict[int, list[SeerSchedule]] = {
        0: [], 1: [], 2: [], 3: [], 4: [], 5: [], 6: []
    }
    # Get weekly schedules, merge overlapping schedules
    for sch in await get_schedules(session, seer_id):
        last = SeerSchedule.model_validate(sch)
        t_ranges = sch_dict[sch.day]
        if t_ranges and t_ranges[-1].end_seconds >= last.start_seconds:
            t_ranges[-1].end_time = max(
                t_ranges[-1].end_time, last.end_time
            )
        else:
            t_ranges.append(last)

    day_offs = await get_day_offs(
        session, seer_id,
        start_date, end_date,
        include_past=True
    )

    appointments = await get_busy_time_ranges(
        session, seer_id, start_date, end_date
    )

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
        if package_duration is None:
            package_duration = (await session.scalars(stmt)).one()
    except NoResultFound:
        raise NotFoundException("Fortune package not found.")

    # Weekly schedules to datetime slots
    slots: list[tuple[datetime, datetime]] = []
    for d in daterange(start_date, end_date + timedelta(1)):
        if d in day_offs:
            continue
        for sch in sch_dict[d.weekday()]:
            start_dt = datetime.combine(
                d, sch.start_time, tzinfo=sch.start_time.tzinfo
            )
            end_dt = datetime.combine(
                d, sch.end_time, tzinfo=sch.end_time.tzinfo
            )
            if sch.end_time == time(0, tzinfo=sch.end_time.tzinfo):
                end_dt += timedelta(days=1)
            slots.append((start_dt, end_dt))

    # Remaining slots after appointments
    remain: list[tuple[datetime, datetime]] = []
    for s in slots:
        remain.extend(remaining_slots(s, appointments))

    # Available slots after sliced by package duration and break duration
    available_slots: list[tuple[datetime, datetime]] = []
    for r in remain:
        slot_start = r[0]
        while (slot_end := slot_start + package_duration) <= r[1]:
            available_slots.append((slot_start, slot_end))
            slot_start = slot_end + break_duration

    return [a for a in available_slots if a[0] >= datetime.now(a[0].tzinfo)]
