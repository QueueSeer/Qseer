from sqlalchemy import delete, func, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.components.seer.schemas import SeerObjectId
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
