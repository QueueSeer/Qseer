from sqlalchemy import delete, func, insert, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.components.seer.schemas import SeerObjectId
from app.database.models import FPStatus, FortunePackage

from .schemas import *


async def get_seer_fpackage(
    session: AsyncSession,
    seer_id: int,
    status: FPStatus = None,
    last_id: int = 0,
    limit: int = 10
) -> list[FortunePackage]:
    stmt = (
        select(FortunePackage).
        where(
            FortunePackage.seer_id == seer_id,
            FortunePackage.id > last_id
        ).
        order_by(FortunePackage.id).
        limit(limit)
    )
    if status:
        stmt = stmt.where(FortunePackage.status == status)
    return (await session.scalars(stmt)).all()


async def create_draft_fpackage(
    session: AsyncSession,
    seer_id: int,
    package: FortunePackageDraft
) -> SeerObjectId:
    package_data = package.model_dump()
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
