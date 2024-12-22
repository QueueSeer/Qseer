from typing import Any
from pydantic import BaseModel, Field


class Message(BaseModel):
    '''
    For returning only message.
    '''
    message: str

    def __init__(self, message: str):
        super().__init__(message=message)


class TokenPayload(BaseModel):
    exp: Any
    sub: int
    roles: list[str]


class UserId(BaseModel):
    id: int = Field(examples=[1])


class RowCount(BaseModel):
    count: int
