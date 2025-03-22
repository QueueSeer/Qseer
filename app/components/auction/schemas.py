import datetime as dt
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from sqlalchemy import func, select, Row

from app.core.schemas import UserBrief
from app.database.models import AuctionInfo, Seer, User


class AuctionCard(BaseModel):
    id: int
    seer: UserBrief
    name: str
    short_description: str
    image: str
    start_time: dt.datetime
    end_time: dt.datetime
    date_created: dt.datetime

    model_config = ConfigDict(from_attributes=True)

    @staticmethod
    def select(*extras):
        return (
            select(
                AuctionInfo.id,
                AuctionInfo.seer_id,
                User.display_name.label('seer_display_name'),
                AuctionInfo.name,
                AuctionInfo.short_description,
                AuctionInfo.image,
                AuctionInfo.start_time,
                AuctionInfo.end_time,
                AuctionInfo.date_created,
                *extras
            ).
            join(User, AuctionInfo.seer_id == User.id).
            join(Seer, AuctionInfo.seer_id == Seer.id)
        )
    
    @classmethod
    def create_from(cls, obj: Row):
        return cls(
            id=obj.id,
            seer=UserBrief(
                id=obj.seer_id, display_name=obj.seer_display_name
            ),
            name=obj.name,
            short_description=obj.short_description,
            image=obj.image,
            start_time=obj.start_time,
            end_time=obj.end_time,
            date_created=obj.date_created
        )
    

class AuctionDetail(AuctionCard):
    id: int
    seer: UserBrief
    name: str
    short_description: str
    description: str
    image: str
    start_time: dt.datetime
    end_time: dt.datetime
    appoint_start_time: dt.datetime
    appoint_end_time: dt.datetime
    initial_bid: float
    min_increment: float
    date_created: dt.datetime

    @staticmethod
    def select(*extras):
        return (
            select(
                AuctionInfo.id,
                AuctionInfo.seer_id,
                User.display_name.label('seer_display_name'),
                AuctionInfo.name,
                AuctionInfo.short_description,
                AuctionInfo.description,
                AuctionInfo.image,
                AuctionInfo.start_time,
                AuctionInfo.end_time,
                AuctionInfo.appoint_start_time,
                AuctionInfo.appoint_end_time,
                AuctionInfo.initial_bid,
                AuctionInfo.min_increment,
                AuctionInfo.date_created,
                *extras
            ).
            join(User, AuctionInfo.seer_id == User.id)
        )
    
    @classmethod
    def create_from(cls, obj: Row):
        return cls(
            id=obj.id,
            seer=UserBrief(
                id=obj.seer_id, display_name=obj.seer_display_name
            ),
            name=obj.name,
            short_description=obj.short_description,
            description=obj.description,
            image=obj.image,
            start_time=obj.start_time,
            end_time=obj.end_time,
            appoint_start_time=obj.appoint_start_time,
            appoint_end_time=obj.appoint_end_time,
            initial_bid=obj.initial_bid,
            min_increment=obj.min_increment,
            date_created=obj.date_created
        )
    
    def is_valid_time(self):
        return (
            self.start_time < self.end_time and
            self.appoint_start_time < self.appoint_end_time and
            self.end_time < self.appoint_start_time
        )


class Bidder(BaseModel):
    auction_id: int
    user_id: int
    amount: float

    model_config = ConfigDict(from_attributes=True)


class Bidding(BaseModel):
    amount: float


class AuctionId(BaseModel):
    auction_id: int


class AuctionCreate(BaseModel):
    name: str = Field(min_length=1)
    short_description: str
    description: str
    start_time: dt.datetime | Literal['now']
    end_time: dt.datetime
    appoint_start_time: dt.datetime
    appoint_end_time: dt.datetime
    initial_bid: float = Field(ge=0)
    min_increment: float = Field(ge=1)

    @field_validator(
        'start_time', 'end_time', 'appoint_start_time', 'appoint_end_time',
        mode='after'
    )
    @classmethod
    def timezone(cls, value: dt.datetime) -> dt.datetime:
        utc7 = dt.timezone(dt.timedelta(hours=7))
        if value == 'now':
            return dt.datetime.now(utc7)
        if value.tzinfo is None:
            return value.replace(tzinfo=utc7)
        if value.tzinfo != utc7:
            return value.astimezone(utc7)
        return value

    @model_validator(mode='after')
    def valid_time_range(self):
        if self.appoint_start_time >= self.appoint_end_time:
            raise ValueError("Appointment time range is invalid")
        if self.start_time >= self.end_time:
            raise ValueError("Auction time range is invalid")
        if self.end_time >= self.appoint_start_time:
            raise ValueError("Auction time must end before appointment time")
        if self.start_time < dt.datetime.now(self.start_time.tzinfo):
            raise ValueError("Auction start time must be in the future")
        return self


class AuctionCreated(BaseModel):
    id: int
    seer_id: int
    name: str
    short_description: str
    description: str
    start_time: dt.datetime
    end_time: dt.datetime
    appoint_start_time: dt.datetime
    appoint_end_time: dt.datetime
    initial_bid: float
    min_increment: float

    model_config = ConfigDict(from_attributes=True)


class AuctionUpdate(BaseModel):
    name: str = None
    short_description: str = None
    description: str = None
    start_time: dt.datetime | Literal['now'] = None
    end_time: dt.datetime = None
    appoint_start_time: dt.datetime = None
    appoint_end_time: dt.datetime = None
    initial_bid: float = Field(None, ge=0)
    min_increment: float = Field(None, ge=1)

    @field_validator(
        'start_time', 'end_time', 'appoint_start_time', 'appoint_end_time',
        mode='after'
    )
    @classmethod
    def timezone(cls, value: dt.datetime) -> dt.datetime:
        if value is None:
            return value
        utc7 = dt.timezone(dt.timedelta(hours=7))
        if value == 'now':
            return dt.datetime.now(utc7)
        if value.tzinfo is None:
            return value.replace(tzinfo=utc7)
        if value.tzinfo != utc7:
            return value.astimezone(utc7)
        return value

    @model_validator(mode='after')
    def valid_time_range(self):
        if (
            self.start_time and
            self.start_time <= dt.datetime.now(self.start_time.tzinfo) - dt.timedelta(seconds=1)
        ):
            raise ValueError("Auction start time must be in the future")
        return self
