from datetime import date, datetime, time, timedelta
from sqlalchemy import delete, func, insert, select, update
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from app.components.seer.schemas import SeerObjectId, SeerSchedule
from app.components.seer.service import get_schedules, get_day_offs
from app.components.appointment.schemas import AppointmentPublic
from app.components.appointment.service import (
    get_appointments_in_date_range
)
from app.core.error import NotFoundException
from app.database.models import FPStatus, FortunePackage, Seer, User

from .schemas import *


async def get_seer_fpackage(
    session: AsyncSession,
    seer_id: int,
    package_id: int,
    status: FPStatus = None
) -> FortunePackage:
    stmt = (
        select(FortunePackage).
        where(
            FortunePackage.seer_id == seer_id,
            FortunePackage.id == package_id
        )
    )
    if status:
        stmt = stmt.where(FortunePackage.status == status)
    return (await session.scalars(stmt)).one()


async def get_fpackage_cards(
    session: AsyncSession,
    seer_id: int,
    status: FPStatus = None,
    last_id: int = 0,
    limit: int = 10
):
    stmt = (
        select(
            FortunePackage.id,
            FortunePackage.name,
            FortunePackage.price,
            FortunePackage.duration,
            FortunePackage.status,
            FortunePackage.foretell_channel,
            FortunePackage.reading_type,
            FortunePackage.category,
            FortunePackage.image,
            FortunePackage.date_created,
            FortunePackage.seer_id,
            User.display_name.label("seer_display_name"),
            User.image.label("seer_image"),
            Seer.rating.label("seer_rating"),
            Seer.review_count.label("seer_review_count")
        ).
        join(
            User,
            (User.id == FortunePackage.seer_id) & (User.is_active == True)
        ).
        join(
            Seer,
            (Seer.id == FortunePackage.seer_id) & (Seer.is_active == True)
        ).
        where(
            FortunePackage.seer_id == seer_id,
            FortunePackage.id > last_id
        ).
        order_by(FortunePackage.id).
        limit(limit)
    )
    if status:
        stmt = stmt.where(FortunePackage.status == status)
    return PackageListOut(packages=(await session.execute(stmt)).all())


async def create_draft_fpackage(
    session: AsyncSession,
    seer_id: int,
    package: FortunePackageDraft
) -> SeerObjectId:
    package_data = package.model_dump(exclude_unset=True)
    if "required_data" in package_data:
        package_data["required_data"] = package.required_number
    package_data["seer_id"] = seer_id
    stmt = (
        insert(FortunePackage).
        values(package_data).
        returning(FortunePackage.id)
    )
    fpackage_id = (await session.scalars(stmt)).one()
    await session.commit()
    return SeerObjectId(seer_id=seer_id, id=fpackage_id)


async def update_draft_fpackage(
    session: AsyncSession,
    seer_id: int,
    package_id: int,
    package: FortunePackageDraft
):
    package_data = package.model_dump(exclude_unset=True)
    if "required_data" in package_data:
        package_data["required_data"] = package.required_number
    stmt = (
        update(FortunePackage).
        where(
            FortunePackage.seer_id == seer_id,
            FortunePackage.id == package_id,
            FortunePackage.status == FPStatus.draft
        ).
        values(package_data)
    )
    rowcount = (await session.execute(stmt)).rowcount
    await session.commit()
    return rowcount


async def change_fpackage_status(
    session: AsyncSession,
    seer_id: int,
    package_id: int,
    status: FPStatus
):
    stmt = (
        update(FortunePackage).
        where(
            FortunePackage.seer_id == seer_id,
            FortunePackage.id == package_id
        ).
        values(status=status)
    )
    rowcount = (await session.execute(stmt)).rowcount
    await session.commit()
    return rowcount


async def delete_fpackage(
    session: AsyncSession,
    seer_id: int,
    package_id: int
):
    stmt = (
        delete(FortunePackage).
        where(
            FortunePackage.seer_id == seer_id,
            FortunePackage.id == package_id
        )
    )
    rowcount = (await session.execute(stmt)).rowcount
    await session.commit()
    return rowcount


def daterange(start_date: date, end_date: date):
    days = int((end_date - start_date).days)
    for n in range(days):
        yield start_date + timedelta(n)


def non_overlapping_range(
    start1: datetime,
    end1: datetime,
    start2: datetime,
    end2: datetime
) -> list[tuple[datetime, datetime]]:
    non_overlap = []
    if start1 < start2:
        non_overlap.append((start1, min(end1, start2)))
    if end1 > end2:
        non_overlap.append((max(start1, end2), end1))
    return non_overlap


def remaining_slots(
    slot: tuple[datetime, datetime],
    appointments: list[AppointmentPublic]
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


async def get_fpackage_time_slots(
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

    appointments = await get_appointments_in_date_range(
        session, seer_id, start_date, end_date, True
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

    return available_slots
