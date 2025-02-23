import datetime as dt
from typing import Annotated, Any
from pydantic import BaseModel, ConfigDict, Field, model_validator


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


class SeerSchedule(BaseModel):
    start_time: dt.time
    end_time: dt.time
    day: int

    @property
    def start_seconds(self) -> int:
        return (
            self.start_time.hour * 3600 +
            self.start_time.minute * 60 +
            self.start_time.second
        )

    @property
    def end_seconds(self) -> int:
        sec = (
            self.end_time.hour * 3600 +
            self.end_time.minute * 60 +
            self.end_time.second
        )
        if sec == 0:
            return 86400
        return sec
    
    @property
    def day_seconds(self) -> int:
        return self.day * 86400

    model_config = ConfigDict(from_attributes=True)


class SeerScheduleIn(SeerSchedule):
    start_time: dt.time = Field(examples=['09:00:00+07:00'])
    end_time: dt.time = Field(examples=['16:00:00+07:00'])
    day: int = Field(ge=0, le=6)

    @model_validator(mode='after')
    def validate_time(self):
        utc7 = dt.timezone(dt.timedelta(hours=7))
        start_tz = self.start_time.tzinfo
        end_tz = self.end_time.tzinfo
        if ((start_tz is not None and start_tz != utc7) or
                (end_tz is not None and end_tz != utc7)):
            raise ValueError("Time zone must be UTC+7 or None.")
        if start_tz != end_tz:
            raise ValueError("Time zone must be the same.")
        self.start_time = self.start_time.replace(microsecond=0, tzinfo=utc7)
        self.end_time = self.end_time.replace(microsecond=0, tzinfo=utc7)
        if (self.start_time >= self.end_time and
                self.end_time != dt.time(0, tzinfo=utc7)):
            raise ValueError("Start time must be before end time.")
        return self


class SeerDayOff(BaseModel):
    day_off: dt.date


class SeerCalendar(BaseModel):
    seer_id: int
    break_duration: dt.timedelta
    schedules: list[SeerSchedule]
    day_offs: list[dt.date]

    model_config = ConfigDict(ser_json_timedelta='float')


class Follower(BaseModel):
    id: int
    username: str
    display_name: str
    image: str


class SeerFollowers(BaseModel):
    followers: list[Follower]
