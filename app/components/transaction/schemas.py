import datetime as dt
from pydantic import BaseModel, ConfigDict, Field

from app.database.models import TxnType, TxnStatus


class TopupConfirm(BaseModel):
    amount: int = Field(ge=1)


class UserCoins(BaseModel):
    coins: float


class TxnOut(BaseModel):
    id: int
    user_id: int
    activity_id: int | None
    activity_type: str | None
    amount: int
    type: TxnType
    status: TxnStatus
    date_created: dt.datetime

    model_config = ConfigDict(from_attributes=True)
