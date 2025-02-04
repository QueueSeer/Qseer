from fastapi import APIRouter

from app.core.deps import AdminJWTDep, SeerJWTDep, UserJWTDep, SortingOrder
from app.core.error import (
    BadRequestException,
    NotFoundException,
)
from app.core.schemas import Message
from app.database import SessionDep

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


@router.delete("/{wid}", responses=res.cancel_request)
async def cancel_withdraw_request(
    session: SessionDep,
    payload: SeerJWTDep,
    wid: int
):
    '''
    ยกเลิกคำขอถอนเงิน ยกเลิกได้แค่คำขอของตัวเองเท่านั้น
    '''
    # เช็คว่า requester_id ตรงกับ payload.sub
    # ถ้าไม่ raise NotFoundException("Request not found.")
    # เปลี่ยนสถานะ transaction จาก hold เป็น cancelled
    # คืนเงินให้ user แล้วลบ withdrawal ออก
    # return Message("Cancelled.")