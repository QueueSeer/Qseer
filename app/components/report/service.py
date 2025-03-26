from enum import Enum
from psycopg.errors import ForeignKeyViolation
from sqlalchemy import asc, desc, insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import SortingOrder
from app.core.error import InternalException, NotFoundException
from app.database.models import Report
from .schemas import *


class ReportOrderBy(str, Enum):
    id = 'id'
    user_id = 'user_id'
    review_id = 'review_id'
    date_created = 'date_created'


async def get_reports(
    session: AsyncSession,
    last_id: int = None,
    limit: int = None,
    user_id: int = None,
    review_id: int = None,
    report_id: int = None,
    order_by: ReportOrderBy = ReportOrderBy.id,
    direction: SortingOrder = 'desc'
):
    order = asc if direction == 'asc' else desc
    row_ordering = {
        ReportOrderBy.id: Report.id,
        ReportOrderBy.user_id: Report.user_id,
        ReportOrderBy.review_id: Report.review_id,
        ReportOrderBy.date_created: Report.date_created,
    }
    stmt = ReportOut.select().order_by(order(row_ordering[order_by]))
    if limit is not None:
        stmt = stmt.limit(limit)
    if last_id is not None:
        if direction == 'asc':
            stmt = stmt.where(Report.id > last_id)
        else:
            stmt = stmt.where(Report.id < last_id)
    if user_id is not None:
        stmt = stmt.where(Report.user_id == user_id)
    if review_id is not None:
        stmt = stmt.where(Report.review_id == review_id)
    if report_id is not None:
        stmt = stmt.where(Report.id == report_id)
    result = await session.execute(stmt)
    return [ReportOut.create_from(row) for row in result]


async def create_report(
    session: AsyncSession,
    user_id: int,
    review_id: int,
    reason: str
):
    stmt = (
        insert(Report).
        values(
            user_id=user_id,
            review_id=review_id,
            reason=reason,
        ).
        returning(Report.id)
    )
    try:
        report_id = (await session.scalars(stmt)).one()
    except IntegrityError as e:
        if isinstance(e.orig, ForeignKeyViolation):
            raise NotFoundException("Review not found.")
        raise InternalException(str(e.orig))
    await session.commit()
    return report_id
