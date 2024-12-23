from pydantic import BaseModel, Field

from app.core.deps import EmailLower


class UserLogin(BaseModel):
    email: EmailLower = Field(examples=["64010972@kmitl.ac.th"])
    password: str = Field(examples=["12345678"])
