from fastapi import APIRouter, Query
from fastapi.responses import PlainTextResponse

from app.core.deps import UserJWTDep
from app.database import SessionDep

from . import responses as res
from .schemas import *
from .service import *

router = APIRouter(prefix="/transaction", tags=["Transaction"])


@router.get("/qr_promptpay", response_class=PlainTextResponse)
async def get_qr_promptpay(_: UserJWTDep, amount: int = ''):
    '''
    สร้าง QR Code สำหรับการโอนเงินผ่าน PromptPay
    '''
    return "https://promptpay.io/0812345678/" + str(amount)


@router.post("/confirm_topup", responses=res.confirm_topup)
async def confirm_topup(
    payload: UserJWTDep,
    session: SessionDep,
    topup: TopupConfirm
):
    '''
    ยืนยันการเติมเงิน
    '''
    user_coins, _ = await change_user_coins(
        session, payload.sub,
        topup.amount, TxnType.topup
    )
    return UserCoins(coins=user_coins)


@router.get("/user/me", responses=res.get_self_transactions)
async def get_self_transactions(
    payload: UserJWTDep,
    session: SessionDep,
    last_id: int = None,
    limit: int = Query(10, ge=1, le=100),
    activity_id: int | NullLiteral = None,
    activity_type: str = None,
    txn_type: TxnType = None,
    txn_status: TxnStatus = None,
    direction: SortingOrder = 'desc'
):
    '''
    ดูรายการธุรกรรมของตัวเอง

    Parameters:
    ----------
    - **last_id** (int, optional): สำหรับการแบ่งหน้า
        กรอง transaction_id < last_id เมื่อ direction เป็น desc
        และ transaction_id > last_id เมื่อ direction เป็น asc
    - **limit** (int, optional): จำนวนรายการที่ต้องการ
    - **activity_id** (int | 'null', optional):
        กรองหา transaction ที่ activity_id ตรงกับที่กำหนด
        สามารถใส่ 'null' เพื่อกรองหา activity_id ที่เป็น null
    - **activity_type** (str, optional):
        กรองหา transaction ที่ activity_type ตรงกับที่กำหนด
    - **txn_type** (TxnType, optional):
        กรอง transaction ที่มี type ตรงกับที่กำหนด
    - **txn_status** (TxnStatus, optional):
        กรอง transaction ที่มี status ตรงกับที่กำหนด
    - **direction** ('asc' | 'desc', optional):
        เรียงลำดับ transaction ตาม id จากน้อยไปมาก หรือมากไปน้อย
    '''
    return await get_transactions(
        session, last_id, limit, payload.sub,
        activity_id, activity_type,
        txn_type, txn_status, direction
    )
