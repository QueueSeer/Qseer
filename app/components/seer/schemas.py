import datetime as dt
from typing import Annotated, Any
from pydantic import BaseModel, ConfigDict, Field


class SeerIn(BaseModel):
    experience: dt.date | None = None
    description: str = Field('', examples=['I am the doomsayer.'])
    primary_skill: str | None = Field(None, examples=['Super Shotgun'])


class SeerOut(BaseModel):
    id: int
    username: str
    display_name: str
    first_name: str
    last_name: str
    image: str
    experience: dt.date | None
    description: str
    primary_skill: str | None
    is_available: bool
    verified_at: dt.datetime | None
    socials_name: str | None
    socials_link: str | None
    rating: float | None
    review_count: int

    model_config = ConfigDict(from_attributes=True)


class SeerGetMe(SeerOut):
    bank_name: str | None = Field(examples=['PromptPay'])
    bank_no: str | None = Field(examples=['0812345678'])


class SeerUpdate(BaseModel):
    experience: dt.date | None = None
    description: str = None
    primary_skill: str | None = None
    is_available: bool = None
    bank_name: str | None = Field(None, examples=['PromptPay'])
    bank_no: str | None = Field(None, examples=['0818765432'])
    socials_name: str | None = None
    socials_link: str | None = None
    break_duration: dt.timedelta = None


class SeerObjectId(BaseModel):
    seer_id: int
    id: int


class SeerObjectIdList(BaseModel):
    ids: list[SeerObjectId]


class SeerScheduleIn(BaseModel):
    start_time: dt.time
    end_time: dt.time
    day: int = Field(ge=0, le=6)


class SeerScheduleUpdate(BaseModel):
    start_time: dt.time | None = None
    end_time: dt.time | None = None
    day: int | None = Field(None, ge=0, le=6)


class SeerScheduleOut(BaseModel):
    id: int
    start_time: dt.time
    end_time: dt.time
    day: int

    model_config = ConfigDict(from_attributes=True)


class SeerDayOff(BaseModel):
    day: dt.date


class SeerCalendar(BaseModel):
    seer_id: int
    break_duration: dt.timedelta
    schedules: list[SeerScheduleOut]
    day_offs: list[dt.date]

    model_config = ConfigDict(ser_json_timedelta='float')


class Follower(BaseModel):
    id: int
    username: str
    display_name: str
    image: str


class SeerFollowers(BaseModel):
    followers: list[Follower]
