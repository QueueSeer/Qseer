from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field

from app.database.models import WdStatus

WITHDRAW_FEE = 20


class WithdrawRequest(BaseModel):
    amount: Decimal = Field(gt=WITHDRAW_FEE, max_digits=15, decimal_places=2)


class WithdrawalOut(BaseModel):
    id: int
    requester_id: int
    amount: Decimal
    bank_name: str
    bank_no: str
    status: WdStatus
    date_created: datetime
    txn_id: int

    model_config = ConfigDict(from_attributes=True)


class WithdrawRequestResult(BaseModel):
    coins: float
    req: WithdrawalOut
