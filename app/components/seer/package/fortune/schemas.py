from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Sequence
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.schemas import pydantic_enum_by_name
from app.database.models import FPStatus, FPChannel


@pydantic_enum_by_name
class FPRequiredData(str, Enum):
    name = 1
    birthdate = 2
    phone_number = 4


class FPackageCardOut(BaseModel):
    seer_id: int
    seer_display_name: str
    seer_image: str
    seer_rating: float | None
    seer_review_count: int
    id: int
    name: str
    price: Decimal | None
    duration: timedelta | None
    status: FPStatus
    foretell_channel: FPChannel
    reading_type: str | None
    category: str | None
    image: str
    date_created: datetime

    model_config = ConfigDict(from_attributes=True, ser_json_timedelta='float')


class PackageListOut(BaseModel):
    packages: list[FPackageCardOut]


class FortunePackageOut(BaseModel):
    seer_id: int
    id: int
    name: str
    price: Decimal | None
    duration: timedelta | None
    description: str
    question_limit: int
    status: FPStatus
    foretell_channel: FPChannel
    reading_type: str | None
    category: str | None
    required_data: list[FPRequiredData]
    image: str
    date_created: datetime

    model_config = ConfigDict(from_attributes=True, ser_json_timedelta='float')

    @field_validator("required_data", mode="before")
    @classmethod
    def int_to_list_enum(cls, values):
        if isinstance(values, int):
            return [
                FPRequiredData(str(flag))
                for r in FPRequiredData
                if (flag := values & int(r.value))
            ]
        return values


class FortunePackageDraft(BaseModel):
    name: str = Field(min_length=1, examples=["Fate Seeker"])
    price: Decimal | None = Field(None, max_digits=15, decimal_places=2)
    duration: timedelta | None = Field(None)
    description: str = Field('', examples=["Knowing won't change."])
    question_limit: int = Field(0, le=6)
    foretell_channel: FPChannel = Field(FPChannel.chat)
    reading_type: str | None = Field(None, examples=["tarot"])
    category: str | None = Field(None, examples=["love"])
    required_data: list[FPRequiredData] = Field(default_factory=list)
    image: str = ''

    model_config = ConfigDict(ser_json_timedelta='float')

    @field_validator("required_data", mode="before")
    @classmethod
    def check_length(cls, values):
        if not isinstance(values, Sequence):
            raise ValueError("required_data must be a list")
        if len(values) > len(FPRequiredData):
            raise ValueError("too many required data")
        return values

    @property
    def required_number(self):
        num = 0
        for r in self.required_data:
            num |= int(r.value)
        return num


class FortunePackageEdit(FortunePackageDraft):
    name: str = Field(None, min_length=1, examples=["Fate Peeker"])


class FPStatusChange(BaseModel):
    status: FPStatus = Field(examples=[FPStatus.published])


class TimeSlot(BaseModel):
    start_time: datetime
    end_time: datetime

    model_config = ConfigDict(from_attributes=True)
