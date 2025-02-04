from sqlalchemy import delete, insert, select, update
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.error import NotFoundException
from app.database.models import (
    TxnType,
    TxnStatus,
    WdStatus,
    Withdrawal,
)
from ..transaction.service import change_user_coins
from .schemas import *
