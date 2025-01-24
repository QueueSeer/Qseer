from fastapi import APIRouter
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


@router.post("/confirm_topup", response=res.confirm_topup)
async def confirm_topup(
    payload: UserJWTDep,
    session: SessionDep,
    topup: TopupConfirm
):
    '''
    ยืนยันการเติมเงิน
    '''
    user_coins = await change_user_coins(session, payload.sub, topup.amount)
    return UserCoins(coins=user_coins)
