import datetime as dt
from enum import Enum
from typing import Any
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)

from app.core.security import hash_password
from app.core.deps import EmailLower


class UserUsername(BaseModel):
    username: str = Field(examples=["sanfong"])

class UserEmail(BaseModel):
    email: EmailLower = Field(examples=["64010892@kmitl.ac.th"])

class UserResetpassword(BaseModel):
    token: str = Field(examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"])
    password: str = Field(min_length=8, examples=["87654321"])

class UserRegister(BaseModel):
    username: str = Field(min_length=3, examples=["sanfong"])
    display_name: str = Field(min_length=3, examples=["Sanfong"])
    first_name: str = Field(min_length=1, examples=["Apinyawat"])
    last_name: str = Field(min_length=1, examples=["Khwanpruk"])
    email: EmailLower = Field(examples=["64010972@kmitl.ac.th"])
    phone_number: str | None = (
        Field(None, min_length=10, max_length=10, examples=["0812345678"])
    )
    birthdate: dt.datetime | None = (
        Field(None, examples=["2002-10-03T19:00:00+07:00"])
    )
    password: str = Field(min_length=8, examples=["12345678"])
    properties: dict[str, Any] = (
        Field(
            {},
            examples=[
                {
                    "reading_type": ["palm_read", "physiognomy"],
                    "interested_topics": ["love", "money", "health"],
                }
            ]
        )
    )

    @field_validator("password")
    @classmethod
    def hashing_password(cls, v: str) -> str:
        return hash_password(v)


class UserOut(BaseModel):
    id: int = Field(examples=[1])
    username: str | None = Field(examples=["sanfong"])
    display_name: str = Field(examples=["Sanfong"])
    first_name: str = Field(examples=["Apinyawat"])
    last_name: str = Field(examples=["Khwanpruk"])
    email: EmailLower = Field(examples=["64010972@kmitl.ac.th"])
    birthdate: dt.datetime | None = (
        Field(None, examples=["2002-10-03T19:00:00+07:00"])
    )
    phone_number: str | None = Field(examples=["0812345678"])
    coins: float
    image: str = Field(examples=["https://example.com/image.jpg"])

    model_config = ConfigDict(from_attributes=True)


class UserSelectableField(str, Enum):
    id = "id"
    username = "username"
    display_name = "display_name"
    first_name = "first_name"
    last_name = "last_name"
    email = "email"
    birthdate = "birthdate"
    phone_number = "phone_number"
    coins = "coins"
    image = "image"
    is_active = "is_active"
    date_created = "date_created"
    properties = "properties"


class UserUpdate(BaseModel):
    display_name: str | None = Field(None, min_length=3, examples=["Sanfong"])
    first_name: str | None = Field(None, min_length=1, examples=["Apinyawat"])
    last_name: str | None = Field(None, min_length=1, examples=["Khwanpruk"])
    phone_number: str | None = (
        Field(None, min_length=10, max_length=10, examples=["0812345678"])
    )
    birthdate: dt.datetime | None = (
        Field(None, examples=["2002-10-03T19:00:00+07:00"])
    )
    image: str | None = Field(None, examples=["https://example.com/image.jpg"])
    properties: dict[str, Any] | None = Field(None)
