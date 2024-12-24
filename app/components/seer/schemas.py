import datetime as dt
from typing import Annotated
from pydantic import BaseModel, ConfigDict, Field

timeTZ = Annotated[dt.time, Field(..., examples=['15:20:30.500+07:00'])]


class SeerRegister(BaseModel):
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

    model_config = ConfigDict(from_attributes=True)


class SeerScheduleId(BaseModel):
    seer_id: int
    id: int


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
    schedules: list[SeerScheduleOut]
    day_offs: list[dt.date]


class Follower(BaseModel):
    id: int
    username: str
    display_name: str
    image: str


class SeerFollowers(BaseModel):
    followers: list[Follower]
