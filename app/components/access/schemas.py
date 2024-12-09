from pydantic import BaseModel, Field, EmailStr


class UserId(BaseModel):
    id: int = Field(examples=[1])


class UserLogin(BaseModel):
    email: EmailStr = Field(examples=["64010972@kmitl.ac.th"])
    password: str = Field(examples=["12345678"])
