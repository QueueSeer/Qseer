import datetime as dt
from pydantic import BaseModel, Field


class SeerRegister(BaseModel):
    experience: dt.date | None = None
    description: str = Field('', examples=['I am the doomsayer.'])
    primary_skill: str | None = Field(None, examples=['Super Shotgun'])
