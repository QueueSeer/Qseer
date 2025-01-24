from pydantic import BaseModel, Field


class TopupConfirm(BaseModel):
    amount: int = Field(ge=1)


class UserCoins(BaseModel):
    coins: float
