import datetime as dt
from decimal import Decimal
from typing import Any
from pydantic import BaseModel, Field, EmailStr, ConfigDict


class UserBase:
    class Id(BaseModel):
        id: int = Field(examples=[1])

    class Username(BaseModel):
        username: str = Field(examples=["sanfong"])

    class DisplayName(BaseModel):
        display_name: str = Field(min_length=3, examples=["Sanfong"])

    class FullName(BaseModel):
        first_name: str = Field(min_length=1, examples=["Apinyawat"])
        last_name: str = Field(min_length=1, examples=["Khwanpruk"])

    class Role(BaseModel):
        role: str = Field(examples=["user"])

    class Email(BaseModel):
        email: EmailStr = Field(examples=["64010972@kmitl.ac.th"])

    class Birthdate(BaseModel):
        birthdate: dt.datetime | None = (
            Field(None, examples=["2002-10-03T19:00:00+07:00"])
        )

    class PhoneNumber(BaseModel):
        phone_number: str | None = (
            Field(None, min_length=10, max_length=10, examples=["0812345678"])
        )

    class Coins(BaseModel):
        coins: Decimal = (
            Field(ge=0, max_digits=15, decimal_places=2, examples=[0])
        )

    class Image(BaseModel):
        image: str = Field(examples=["https://example.com/image.jpg"])

    class IsActive(BaseModel):
        is_active: bool = Field(examples=[True])

    class DateCreated(BaseModel):
        date_created: dt.datetime = Field(
            examples=["2024-11-24T00:55:00+07:00"])

    class Properties(BaseModel):
        properties: dict[str, Any] = Field({})


class UserRegister(BaseModel):
    username: str = Field(min_length=3, examples=["sanfong"])
    display_name: str = Field(min_length=3, examples=["Sanfong"])
    first_name: str = Field(min_length=1, examples=["Apinyawat"])
    last_name: str = Field(min_length=1, examples=["Khwanpruk"])
    email: EmailStr = Field(examples=["64010972@kmitl.ac.th"])
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


class UserOut(
    UserBase.Image,
    UserBase.Coins,
    UserBase.PhoneNumber,
    UserBase.Birthdate,
    UserBase.Email,
    UserBase.FullName,
    UserBase.DisplayName,
    UserBase.Username,
    UserBase.Id,
):
    model_config = ConfigDict(from_attributes=True)
