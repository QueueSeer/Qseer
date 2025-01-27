from typing import Literal
from sqlalchemy import asc, desc, insert, select, update
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.error import NotFoundException
from app.database.models import (
    User,
    Transaction,
    TxnType,
    TxnStatus,
    Activity
)
from .schemas import *


async def change_user_coins(
    session: AsyncSession,
    user_id: int,
    amount: int
):
    stmt = (
        update(User).
        where(User.id == user_id, User.is_active == True).
        values(coins=User.coins + amount).
        returning(User.coins)
    )
    try:
        user_coins = (await session.scalars(stmt)).one()
    except NoResultFound:
        raise NotFoundException("User not found.")
    stmt = (
        insert(Transaction).
        values(
            user_id=user_id,
            activity_id=None,
            amount=amount,
            type=TxnType.topup,
            status=TxnStatus.completed
        )
    )
    await session.execute(stmt)
    await session.commit()
    return user_coins


async def get_transactions(
    session: AsyncSession,
    last_id: int = None,
    limit: int = 10,
    user_id: int = None,
    activity_id: int | Literal['null'] = None,
    activity_type: str = None,
    txn_type: TxnType = None,
    txn_status: TxnStatus = None,
    direction: Literal['asc', 'desc'] = 'desc'
):
    order = asc if direction == 'asc' else desc
    stmt = (
        select(
            Transaction.id,
            Transaction.user_id,
            Transaction.activity_id,
            Transaction.amount,
            Transaction.type,
            Transaction.status,
            Transaction.date_created,
            Activity.type.label('activity_type')
        ).
        join(Activity, Transaction.activity_id == Activity.id, isouter=True).
        order_by(order(Transaction.id)).limit(limit)
    )
    if last_id is not None:
        if direction == 'asc':
            last_id_cond = Transaction.id > last_id
        else:
            last_id_cond = Transaction.id < last_id
        stmt = stmt.where(last_id_cond)
    if user_id is not None:
        stmt = stmt.where(Transaction.user_id == user_id)
    if activity_id is not None:
        activity_id = None if activity_id == 'null' else activity_id
        stmt = stmt.where(Transaction.activity_id == activity_id)
    if activity_type is not None:
        stmt = stmt.where(Activity.type == activity_type)
    if txn_type is not None:
        stmt = stmt.where(Transaction.type == txn_type)
    if txn_status is not None:
        stmt = stmt.where(Transaction.status == txn_status)
    return [
        TxnOut.model_validate(t)
        for t in (await session.execute(stmt)).all()
    ]
