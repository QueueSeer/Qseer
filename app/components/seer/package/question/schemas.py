from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import func


class QuestionPackageIn(BaseModel):
    price: Decimal = Field(None, ge=0, max_digits=15, decimal_places=2)
    description: str = Field(None, examples=["Just asking."])
    is_enabled: bool = Field(None)
    stack_limit: int = Field(None, ge=0)
    image: str = Field(None)

    @property
    def enable_at(self):
        return func.now() if self.is_enabled else None


class QuestionPackageOut(BaseModel):
    price: Decimal
    description: str
    is_enabled: bool
    stack_limit: int
    image: str

    model_config = ConfigDict(from_attributes=True)

    @field_validator("is_enabled", mode="before")
    @classmethod
    def date_to_bool(cls, value):
        return not not value

