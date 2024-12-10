from pydantic import BaseModel, Field, EmailStr


class UserLogin(BaseModel):
    email: EmailStr = Field(examples=["64010972@kmitl.ac.th"])
    password: str = Field(examples=["12345678"])
