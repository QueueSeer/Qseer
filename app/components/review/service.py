from enum import Enum
from psycopg.errors import UniqueViolation
from sqlalchemy import asc, delete, desc, func, insert, select, update
from sqlalchemy.exc import NoResultFound, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.core.deps import SortingOrder
from app.core.error import (
    BadRequestException,
    NotFoundException,
    InternalException,
)
from app.database.models import (
    ApmtStatus,
    Appointment,
    FortunePackage,
    Review,
    Seer,
    User,
)
from .schemas import *


class ReviewOrderBy(str, Enum):
    id = 'id'
    score = 'score'
    date_created = 'date_created'


async def get_reviews(
    session: AsyncSession,
    last_id: int = None,
    limit: int = None,
    seer_id: int = None,
    client_id: int = None,
    review_id: int = None,
    min_score: int = None,
    max_score: int = None,
    order_by: ReviewOrderBy = ReviewOrderBy.id,
    direction: SortingOrder = 'desc'
):
    order = asc if direction == 'asc' else desc
    row_ordering = {
        ReviewOrderBy.id: Review.id,
        ReviewOrderBy.score: Review.score,
        ReviewOrderBy.date_created: Review.date_created,
    }
    client = aliased(User, name='client')
    seer_u = aliased(User, name='seer_u')
    stmt = (
        select(
            Review.id,
            seer_u.id.label('seer_id'),
            seer_u.display_name.label('seer_display_name'),
            client.id.label('client_id'),
            client.display_name.label('client_display_name'),
            FortunePackage.id.label('package_id'),
            FortunePackage.name.label('package_name'),
            Review.score,
            Review.text,
            Review.date_created
        ).
        join(Appointment, Appointment.id == Review.id).
        join(Appointment.package).
        join(seer_u, Appointment.seer_id == seer_u.id).
        join(client, Appointment.client_id == client.id).
        order_by(order(row_ordering[order_by]))
    )
    if limit is not None:
        stmt = stmt.limit(limit)
    if last_id is not None:
        if direction == 'asc':
            stmt = stmt.where(Review.id > last_id)
        else:
            stmt = stmt.where(Review.id < last_id)
    if seer_id is not None:
        stmt = stmt.where(seer_u.id == seer_id)
    if client_id is not None:
        stmt = stmt.where(client.id == client_id)
    if review_id is not None:
        stmt = stmt.where(Review.id == review_id)
    if min_score is not None:
        stmt = stmt.where(Review.score >= min_score)
    if max_score is not None:
        stmt = stmt.where(Review.score <= max_score)
    result = await session.execute(stmt)
    return [ReviewOut.create_from(row) for row in result]


async def update_seer_rating(
    session: AsyncSession,
    seer_id: int,
    *,
    add: bool = True,
    commit: bool = False
):
    CAL_AT = 10
    stmt = (
        select(Seer.rating, Seer.review_count).
        where(Seer.id == seer_id)
    )
    try:
        rating, review_count = (await session.execute(stmt)).one()._tuple()
    except NoResultFound:
        raise NotFoundException("Seer not found.")

    sel_stmt = (
        select(
            func.avg(Review.score).label('rating'),
            func.count(Review.id).label('review_count')
        ).
        join(Appointment, Review.id == Appointment.id).
        where(Appointment.seer_id == seer_id).
        alias('review_stats')
    )

    if add:
        if review_count + 1 < CAL_AT and rating is None:
            rating_change = None
            count_change = Seer.review_count + 1
        else:
            rating_change = sel_stmt.c.rating
            count_change = sel_stmt.c.review_count
    else:
        if review_count - 1 < CAL_AT:
            rating_change = None
            count_change = Seer.review_count - 1
        else:
            rating_change = sel_stmt.c.rating
            count_change = sel_stmt.c.review_count

    stmt = (
        update(Seer).
        where(Seer.id == seer_id).
        values(
            rating=rating_change,
            review_count=count_change
        )
    )
    await session.execute(stmt)
    if commit:
        await session.commit()


async def create_review(
    session: AsyncSession,
    data: ReviewCreate,
    *,
    user_id: int = None
):
    if user_id is not None:
        stmt = (
            select(
                Appointment.client_id,
                Appointment.status,
                Appointment.seer_id
            ).
            where(Appointment.id == data.id)
        )
        try:
            row = (await session.execute(stmt)).one()._tuple()
            client_id, status, seer_id = row
        except NoResultFound:
            raise NotFoundException("Appointment not found.")
        if client_id != user_id:
            raise BadRequestException("Not client.")
        if status != ApmtStatus.completed:
            raise BadRequestException("Appointment not ended.")

    stmt = (
        insert(Review).
        values(
            id=data.id,
            score=data.score,
            text=data.text,
        )
    )
    try:
        await session.execute(stmt)
    except IntegrityError as e:
        if isinstance(e.orig, UniqueViolation):
            raise BadRequestException("Already reviewed.")
        raise InternalException(str(e.orig))

    await update_seer_rating(session, seer_id)
    await session.commit()


async def delete_review(
    session: AsyncSession,
    review_id: int
):
    stmt = (
        delete(Review).
        where(Review.id == review_id)
    )
    rowcount = (await session.execute(stmt)).rowcount
    if rowcount == 0:
        raise NotFoundException("Review not found.")
    stmt = (
        select(Appointment.seer_id).
        where(Appointment.id == review_id)
    )
    try:
        seer_id = (await session.scalars(stmt)).one()
    except NoResultFound:
        raise NotFoundException("Appointment not found.")
    await update_seer_rating(session, seer_id, add=False)
    await session.commit()
    return rowcount
