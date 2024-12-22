from psycopg.errors import UniqueViolation, UndefinedTable
from sqlalchemy import delete, func, insert, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import IntegrityError, ProgrammingError, OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.error import IntegrityException, InternalException
from app.database.models import User, Seer, Schedule, DayOff
from app.database.utils import parse_unique_violation
from .schemas import *


async def create_seer(session: AsyncSession, seer_reg: SeerRegister, user_id: int) -> int:
    reg_dict = seer_reg.model_dump(exclude_unset=True)
    reg_dict["id"] = user_id
    try:
        stmt = insert(Seer).values(reg_dict).returning(Seer.id)
        seer_id = (await session.scalars(stmt)).one()
        await session.commit()
        return seer_id
    except IntegrityError as e:
        detail = {"type": "IntegrityError", "detail": "Unknown error."}
        if isinstance(e.orig, UniqueViolation):
            detail = parse_unique_violation(e.orig)
        raise IntegrityException(detail=detail)
    except ProgrammingError as e:
        detail = {"detail": "ProgrammingError"}
        if isinstance(e.orig, UndefinedTable):
            detail = {"detail": "Table undefined."}
        raise InternalException(detail=detail)
    except OperationalError as e:
        detail = {"detail": "Connection with database failed."}
        raise InternalException(detail=detail)


async def get_seer_info(seer_id: int, session: AsyncSession) -> SeerOut:
    stmt = (
        select(
            User.id,
            User.username,
            User.display_name,
            User.first_name,
            User.last_name,
            User.image,
            Seer.experience,
            Seer.description,
            Seer.primary_skill,
            Seer.is_available,
            Seer.verified_at
        ).
        join(User.seer).
        where(User.id == seer_id, User.is_active == True)
    )
    seer = (await session.execute(stmt)).one()
    return SeerOut.model_validate(seer)


async def is_seer_exist(seer_id: int, session: AsyncSession):
    stmt = (
        select(Seer.id).
        join(User, Seer.id == User.id).
        where(
            Seer.id == seer_id,
            User.is_active == True,
            Seer.is_active == True
        )
    )
    return (await session.scalars(stmt)).one()


async def get_calendar(seer_id: int, session: AsyncSession):
    stmt = (
        select(Schedule).
        where(Schedule.seer_id == seer_id)
    )
    schedules = (await session.scalars(stmt)).all()
    stmt = (
        select(DayOff.day_off).
        where(DayOff.seer_id == seer_id, DayOff.day_off >= func.now())
    )
    day_offs = (await session.scalars(stmt)).all()
    return SeerCalendar(seer_id=seer_id, schedules=schedules, day_offs=day_offs)


async def update_schedule(
    seer_id: int,
    schedule_id: int,
    schedule: SeerScheduleUpdate,
    session: AsyncSession
):
    schedule_dict = schedule.model_dump(exclude_unset=True)
    stmt = (
        update(Schedule).
        where(Schedule.id == schedule_id, Schedule.seer_id == seer_id).
        values(schedule_dict).
        returning(Schedule)
    )
    updated_schedule = (await session.scalars(stmt)).one()
    await session.commit()
    return SeerScheduleOut.model_validate(updated_schedule)


async def delete_schedule(seer_id: int, schedule_id: int, session: AsyncSession):
    stmt = (
        delete(Schedule).
        where(Schedule.id == schedule_id, Schedule.seer_id == seer_id)
    )
    deleted_count = (await session.execute(stmt)).rowcount
    await session.commit()
    return deleted_count


async def add_dayoff(day_off: SeerDayOff, seer_id: int, session: AsyncSession):
    day_off_dict = day_off.model_dump()
    day_off_dict["seer_id"] = seer_id
    stmt = pg_insert(DayOff).values(day_off_dict).on_conflict_do_nothing()
    await session.execute(stmt)
    await session.commit()
    return day_off


async def delete_dayoff(day_off: dt.date, seer_id: int, session: AsyncSession):
    stmt = (
        delete(DayOff).
        where(DayOff.seer_id == seer_id, DayOff.day_off == day_off)
    )
    deleted_count = (await session.execute(stmt)).rowcount
    await session.commit()
    return deleted_count
