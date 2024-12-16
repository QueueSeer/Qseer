import datetime as dt
from pydantic import BaseModel, ConfigDict, Field


class SeerRegister(BaseModel):
    experience: dt.date | None = None
    description: str = Field('', examples=['I am the doomsayer.'])
    primary_skill: str | None = Field(None, examples=['Super Shotgun'])


class SeerOut(BaseModel):
    id: int
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
