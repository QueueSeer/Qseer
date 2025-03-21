from sqlalchemy import asc, desc,delete, insert, select, update ,case
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.error import (
    BadRequestException,
    NotFoundException,
)

from app.core.deps import AdminJWTDep, SeerJWTDep, UserJWTDep, SortingOrder
from app.core.schemas import Message

from app.database import SessionDep


from app.core.error import NotFoundException
from app.database.models import (
    User,
    TxnType,
    TxnStatus,
    WdStatus,
    Withdrawal,
    Seer,
)
from ..transaction.service import change_user_coins , cancel_withdraw_Transaction , complete_withdraw_Transaction
from .schemas import *


async def get_withdrawals_List(
    session: AsyncSession,
    last_id: int = None,
    limit: int = 10,
    requester_id: int = None,
    direction: SortingOrder = 'desc',
    status: WdStatus = None,
):
    order = asc if direction == 'asc' else desc
    stmt = (
        select(
            Withdrawal.id,
            Withdrawal.requester_id,
            Withdrawal.amount,
            case((Withdrawal.bank_name.is_(None), ""), else_=Withdrawal.bank_name).label("bank_name"),
            case((Withdrawal.bank_no.is_(None), ""), else_=Withdrawal.bank_no).label("bank_no"),
            Withdrawal.status,
            Withdrawal.date_created,
            Withdrawal.txn_id
        ).order_by(order(Withdrawal.id)).limit(limit)
    #where(Withdrawal.requester_id == requester_id)
    )
    if last_id is not None:
        if direction == 'asc':
            last_id_cond = Withdrawal.id > last_id
        else:
            last_id_cond = Withdrawal.id < last_id
        stmt = stmt.where(last_id_cond)
    if requester_id is not None:
        stmt = stmt.where(Withdrawal.requester_id == requester_id)
    if status is not None:
        stmt = stmt.where(Withdrawal.status == status)
    return [
        WithdrawalOut.model_validate(t)
        for t in (await session.execute(stmt)).all()
    ]

async def get_withdraw(
    session: SessionDep,
    payload: UserJWTDep,
    wid: int
):
    if payload.is_admin :
        stmt = (
            select(
            Withdrawal.id,
            Withdrawal.requester_id,
            Withdrawal.amount,
            case((Withdrawal.bank_name.is_(None), ""), else_=Withdrawal.bank_name).label("bank_name"),
            case((Withdrawal.bank_no.is_(None), ""), else_=Withdrawal.bank_no).label("bank_no"),
            Withdrawal.status,
            Withdrawal.date_created,
            Withdrawal.txn_id
            )
            .where(Withdrawal.id == wid)
        )
    else:
        stmt = (
            select(
            Withdrawal.id,
            Withdrawal.requester_id,
            Withdrawal.amount,
            case((Withdrawal.bank_name.is_(None), ""), else_=Withdrawal.bank_name).label("bank_name"),
            case((Withdrawal.bank_no.is_(None), ""), else_=Withdrawal.bank_no).label("bank_no"),
            Withdrawal.status,
            Withdrawal.date_created,
            Withdrawal.txn_id
            ).where(Withdrawal.id == wid,Withdrawal.requester_id == payload.sub)
        )
    try:
        W_info = (await session.execute(stmt)).one()
    except NoResultFound:
        raise NotFoundException("Request not found.")
    return WithdrawalOut.model_validate(W_info)

async def create__withdrawal(    
    session: SessionDep,
    payload: SeerJWTDep,
    req: WithdrawRequest
    ):
    user_id = payload.sub
    stmt = (
        select(User.coins).where(User.id == user_id,User.is_active == True)
    )
    try:
        user_coins = (await session.scalars(stmt)).one()
    except NoResultFound:
        raise NotFoundException("User not found.")
    if user_coins < req.amount:
        raise BadRequestException("Insufficient balance.")
    stmt = (
        select(Seer.bank_name,Seer.bank_no).where(Seer.id == user_id,Seer.is_active == True)
    )
    try:
        bank_name , bank_no = (await session.execute(stmt)).one()._tuple()
    except NoResultFound:
        raise NotFoundException("User not found.")
    if bank_name is None or bank_no is None :
        raise BadRequestException("Invalid bank details provided.")
    current_user_coins , txn_id = await change_user_coins(
        session, user_id, -req.amount,
        TxnType.withdraw,
        TxnStatus.hold,
    )
    stmt = (
        insert(Withdrawal).values(
            requester_id = user_id,
            amount = req.amount,
            bank_name = bank_name,
            bank_no = bank_no,
            status = WdStatus.pending,
            txn_id = txn_id
        ).returning(
            Withdrawal.id,
            Withdrawal.requester_id,
            Withdrawal.amount,
            Withdrawal.bank_name,
            Withdrawal.bank_no,
            Withdrawal.status,
            Withdrawal.date_created,
            Withdrawal.txn_id
        )
    )
    result = (await session.execute(stmt)).one_or_none()
    await session.commit()
    return WithdrawRequestResult(
        coins = current_user_coins,
        req = WithdrawalOut.model_validate(result)
    )
    
async def complete_withdraw(
    session: SessionDep,
    payload: AdminJWTDep,
    wid: int       
):
    stmt = (
        update(Withdrawal).
        where(Withdrawal.id == wid,Withdrawal.status == WdStatus.pending).
        values(status = WdStatus.completed).
        returning(Withdrawal.requester_id,Withdrawal.txn_id)
        )   
    try:
        requester_id , txn_id = (await session.execute(stmt)).one()
    except NoResultFound:
        raise NotFoundException("withdrawal request.")
    await complete_withdraw_Transaction(session=session,txn_id=txn_id,commit=True)
    return Message("Completed.")

async def reject_withdraw(    
    session: SessionDep,
    payload: AdminJWTDep,
    wid: int):
    stmt = (
        update(Withdrawal).
        where(Withdrawal.id == wid,Withdrawal.status == WdStatus.pending).
        values(status = WdStatus.rejected).
        returning(Withdrawal.requester_id,Withdrawal.amount,Withdrawal.txn_id)
        )   
    try:
        requester_id , amount , txn_id = (await session.execute(stmt)).one()
    except NoResultFound:
        raise NotFoundException("withdrawal request.")
    await cancel_withdraw_Transaction(
        session=session,
        requester_id=requester_id,
        amount=amount,
        txn_id=txn_id,
        commit=True
    )
    return Message("Rejected.")

async def cancel_withdraw(    
    session: SessionDep,
    payload: SeerJWTDep,
    wid: int):
    stmt = (
            select(
            Withdrawal.requester_id,
            Withdrawal.amount,
            Withdrawal.txn_id
            )
            .where(Withdrawal.id == wid)
        )
    try:
       requester_id , amount , txn_id = (await session.execute(stmt)).one()
    except NoResultFound:
        raise NotFoundException("Request not found.")
    if requester_id != payload.sub :
        raise NotFoundException("Request not found.")
    await cancel_withdraw_Transaction(
        session=session,
        requester_id=requester_id,
        amount=amount,
        txn_id=txn_id,
        commit=False
    )
    # เช็คว่า requester_id ตรงกับ payload.sub
    # ถ้าไม่ raise NotFoundException("Request not found.")
    # เปลี่ยนสถานะ transaction จาก hold เป็น cancelled
    stmt = (
        delete(Withdrawal).where(Withdrawal.id == wid)
    )
    await session.execute(stmt)
    await session.commit()
    return Message("Cancelled.")