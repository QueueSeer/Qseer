from sqlalchemy import insert, select, update
from sqlalchemy.exc import (
    NoResultFound,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.error import (
    NotFoundException
)
from app.database.models import User, Transaction, TxnType, TxnStatus


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
