from fastapi import APIRouter

from app.core.deps import AdminJWTDep, SeerJWTDep, UserJWTDep, SortingOrder


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
    if not payload.is_admin :
        requester_id = payload.sub
    if requester_id == None :
        return []
    return await get_withdrawals_List(
        session = session,
        last_id = last_id,
        limit = limit,
        requester_id = requester_id,
        direction = direction,
        status = status,
    )

@router.post("", responses=res.request_withdrawal)
async def request_withdrawal(
    session: SessionDep,
    payload: SeerJWTDep,
    req: WithdrawRequest
):
    '''
    สร้างคำขอถอนเงิน
    '''
    return await create__withdrawal(
        session=session,
        payload=payload,
        req=req
    )


@router.get("/{wid}", responses=res.get_withdraw_request)
async def get_withdraw_request(
    session: SessionDep,
    payload: UserJWTDep,
    wid: int
):
    '''
    ดูรายละเอียดคำขอถอนเงิน
    '''
    return await get_withdraw(session=session,payload=payload,wid=wid)


@router.patch("/{wid}/status/complete", responses=res.complete_request)
async def complete_withdraw_request(
    session: SessionDep,
    payload: AdminJWTDep,
    wid: int
):
    '''
    ยืนยันคำขอถอนเงิน เปลี่ยนสถานะจาก pending เป็น completed
    '''
    return await complete_withdraw(session=session,payload=payload,wid=wid)


@router.patch("/{wid}/status/reject", responses=res.reject_request)
async def reject_withdraw_request(
    session: SessionDep,
    payload: AdminJWTDep,
    wid: int
):
    '''
    ปฏิเสธคำขอถอนเงิน เปลี่ยนสถานะจาก pending เป็น rejected
    '''
    return reject_withdraw(session=session,payload=payload,wid=wid)


@router.delete("/{wid}", responses=res.cancel_request)
async def cancel_withdraw_request(
    session: SessionDep,
    payload: SeerJWTDep,
    wid: int
):
    '''
    ยกเลิกคำขอถอนเงิน ยกเลิกได้แค่คำขอของตัวเองเท่านั้น
    '''
    return await cancel_withdraw(session=session,payload=payload,wid=wid)
