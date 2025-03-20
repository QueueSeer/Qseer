from fastapi import APIRouter

from app.core.deps import AdminJWTDep, SeerJWTDep, UserJWTDep, SortingOrder
from app.core.error import (
    BadRequestException,
    NotFoundException,
)
from app.core.schemas import Message
from app.database import SessionDep

from app.database.models import (
    User,
    TxnType,
    TxnStatus,
    WdStatus,
    Withdrawal,
    Seer,
)

from . import responses as res
from .schemas import *
from .service import *

router = APIRouter(prefix="/withdraw", tags=["Withdraw"])


@router.get("", responses=res.list_withdraw_requests)
async def list_withdraw_requests(
    session: SessionDep,
    payload: UserJWTDep,
    last_id: int = None,
    limit: int = 10,
    requester_id: int = None,
    status: WdStatus = None,
    direction: SortingOrder = 'asc'
):
    '''
    ดูรายการคำขอถอนเงิน
    ถ้าเป็น admin จะสามารถดูคำขอของคนอื่นได้
    ถ้าเป็น user จะดูได้เฉพาะของตัวเอง
    
    Parameters:
    ----------
    - **last_id** (int, optional): สำหรับการแบ่งหน้า
        กรอง withdrawal_id < last_id เมื่อ direction เป็น desc
        และ withdrawal_id > last_id เมื่อ direction เป็น asc
    - **limit** (int, optional): จำนวนรายการที่ต้องการ
    - **requester_id** (int, optional): กรองคำขอของ user ที่กำหนด
    - **status** (WdStatus, optional): กรองคำขอที่มีสถานะตามที่กำหนด
    - **direction** ('asc' | 'desc', optional): ทิศทางการเรียงลำดับ
    '''
    # เช็คว่ามี "admin" ใน payload.roles หรือไม่
    # ถ้ามีทำงานตามปกติ
    # ถ้าไม่มี requester_id ต้องเป็น None หรือเท่ากับ payload.sub
    #    ไม่งั้น return []
    # แล้วให้ requester_id เท่ากับ payload.sub
    # ไปสร้าง func ใน service.py ชื่อ get_withdrawals
    # โยนการทำงานไปที่ service ให้หมด api อื่นด้วย
    # ดู get_self_transactions ใน transaction เป็นตัวอย่าง
    # return list of WithdrawalOut
    if not payload.is_admin :
        requester_id = payload.sub
    if requester_id == None :
        return []
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


@router.post("", responses=res.request_withdrawal)
async def request_withdrawal(
    session: SessionDep,
    payload: SeerJWTDep,
    req: WithdrawRequest
):
    '''
    สร้างคำขอถอนเงิน
    '''
    # ดูว่ามีเงินพอถอนหรือไม่
    # ถ้าไม่พอ return BadRequestException("Insufficient balance.")
    # ถ้าพอให้ใช้ change_user_coins ใน transaction/service.py
    # ใช้ TxnType.withdraw และ TxnStatus.hold
    # แล้วสร้าง Withdrawal (ไปเขียน func ใน service)
    # WdStatus.pending
    # status 201: return WithdrawRequestResult
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
    raise NotImplementedError


@router.get("/{wid}", responses=res.get_withdraw_request)
async def get_withdraw_request(
    session: SessionDep,
    payload: UserJWTDep,
    wid: int
):
    '''
    ดูรายละเอียดคำขอถอนเงิน
    '''
    # return WithdrawalOut
    # ถ้าไม่ใช่ admin และ requester_id ไม่ตรงกับ payload.sub
    # หรือหา request ไม่เจอ ให้
    # return NotFoundException("Request not found.")
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


@router.patch("/{wid}/status/complete", responses=res.complete_request)
async def complete_withdraw_request(
    session: SessionDep,
    payload: AdminJWTDep,
    wid: int
):
    '''
    ยืนยันคำขอถอนเงิน เปลี่ยนสถานะจาก pending เป็น completed
    '''
    # เปลี่ยนสถานะ withdrawal จาก pending เป็น completed
    # เปลี่ยนสถานะ transaction จาก hold เป็น completed
    # return Message("Completed.")
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


@router.patch("/{wid}/status/reject", responses=res.reject_request)
async def reject_withdraw_request(
    session: SessionDep,
    payload: AdminJWTDep,
    wid: int
):
    '''
    ปฏิเสธคำขอถอนเงิน เปลี่ยนสถานะจาก pending เป็น rejected
    '''
    # เปลี่ยนสถานะ withdrawal จาก pending เป็น rejected
    # เปลี่ยนสถานะ transaction จาก hold เป็น cancelled
    # แล้วคืนเงินให้ user
    # return Message("Rejected.")
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


@router.delete("/{wid}", responses=res.cancel_request)
async def cancel_withdraw_request(
    session: SessionDep,
    payload: SeerJWTDep,
    wid: int
):
    '''
    ยกเลิกคำขอถอนเงิน ยกเลิกได้แค่คำขอของตัวเองเท่านั้น
    '''
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
    # คืนเงินให้ user แล้วลบ withdrawal ออก
    # return Message("Cancelled.")
