from sqlalchemy import asc, desc,delete, insert, select, update ,case
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import AdminJWTDep, SeerJWTDep, UserJWTDep, SortingOrder

from app.core.error import NotFoundException
from app.database.models import (
    User,
    TxnType,
    TxnStatus,
    WdStatus,
    Withdrawal,
)
from ..transaction.service import change_user_coins , cancel_withdraw_Transaction , complete_withdraw_Transaction
from .schemas import *


# async def get_withdrawals(
#     session: AsyncSession,
#     last_id: int = None,
#     limit: int = 10,
#     user_id: int = None,
#     direction: SortingOrder = 'desc',
#     status: WdStatus = None,
# ):
#     order = asc if direction == 'asc' else desc
#     # stmt = (
#     #     select(
#     #         Transaction.id,
#     #         Transaction.user_id,
#     #         Transaction.activity_id,
#     #         Transaction.amount,
#     #         Transaction.type,
#     #         Transaction.status,
#     #         Transaction.date_created,
#     #         Activity.type.label('activity_type')
#     #     ).
#     #     join(Activity, Transaction.activity_id == Activity.id, isouter=True).
#     #     order_by(order(Transaction.id)).limit(limit)
#     # )