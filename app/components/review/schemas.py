import datetime as dt
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Row

from app.core.schemas import UserBrief


class PackageBrief(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class ReviewCreate(BaseModel):
    id: int
    score: int = Field(ge=0, le=5)
    text: str = Field(min_length=1, max_length=1000)


class ReviewOut(BaseModel):
    id: int
    seer: UserBrief
    client: UserBrief
    package: PackageBrief
    score: int
    text: str
    date_created: dt.datetime

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def create_from(cls, obj: Row):
        return cls(
            id=obj.id,
            seer=UserBrief(
                id=obj.seer_id, display_name=obj.seer_display_name,
                image=obj.seer_image
            ),
            client=UserBrief(
                id=obj.client_id, display_name=obj.client_display_name,
                image=obj.client_image
            ),
            package=PackageBrief(
                id=obj.package_id, name=obj.package_name
            ),
            score=obj.score,
            text=obj.text,
            date_created=obj.date_created
        )
