from sqlalchemy import delete, func, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import SessionDep
from app.database.models import QuestionPackage

from .schemas import *


async def get_questionpackage(session: AsyncSession, seer_id: int):
    stmt = (
        select(QuestionPackage).where(QuestionPackage.seer_id == seer_id, QuestionPackage.id == 1)
    )
    result = (await session.execute(stmt)).scalar_one_or_none()
    if result == None :
        return result
    return QuestionPackageOut(
        price=result.price,
        description=result.description,
        is_enabled=result.enable_at,
        stack_limit=result.stack_limit,
        image=result.image
    )


def check_field_questionpackagein_first(question_package_in: QuestionPackageIn):
    return all(value is not None for value in question_package_in.__dict__.values())


async def edit_questionpackage(session: SessionDep, user_id: int, qp_data: QuestionPackageIn):
    has_questionpackage = await get_questionpackage(session, user_id)
    if has_questionpackage is None:
        if not check_field_questionpackagein_first(qp_data):
            return None
        data = qp_data.model_dump()
        data["seer_id"] = user_id
        data["id"] = 1
        if "is_enabled" in data:
            del data["is_enabled"]
            data["enable_at"] = qp_data.enable_at
        stmt = (
            insert(QuestionPackage).
            values(data).returning(
                QuestionPackage.price,
                QuestionPackage.description,
                QuestionPackage.enable_at.label("is_enabled"),
                QuestionPackage.stack_limit,
                QuestionPackage.image
            )
        )
        result = (await session.execute(stmt)).one_or_none()
        await session.commit()
        if result is None:
            return None
        return QuestionPackageOut.model_validate(result)
    else:
        data = qp_data.model_dump(exclude_unset=True)
        if "is_enabled" in data:
            del data["is_enabled"]
            data["enable_at"] = qp_data.enable_at
        stmt = (
            update(QuestionPackage).
            where(QuestionPackage.seer_id == user_id, QuestionPackage.id == 1).
            values(data).
            returning(
                QuestionPackage.price,
                QuestionPackage.description,
                QuestionPackage.enable_at.label("is_enabled"),
                QuestionPackage.stack_limit,
                QuestionPackage.image
            )
        )
        result = (await session.execute(stmt)).one_or_none()
        await session.commit()
        if result is None:
            return None
        return QuestionPackageOut.model_validate(result)
