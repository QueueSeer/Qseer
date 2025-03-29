import datetime as dt
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, Row

from app.core.schemas import UserBrief
from app.database.models import Report, Review, User


class ReviewBrief(BaseModel):
    id: int
    score: int
    text: str

    model_config = ConfigDict(from_attributes=True)


class ReportCreate(BaseModel):
    review_id: int
    reason: str = Field(min_length=1, max_length=600)


class ReportId(BaseModel):
    report_id: int


class ReportOut(BaseModel):
    id: int
    reporter: UserBrief
    review: ReviewBrief
    reason: str
    date_created: dt.datetime

    @staticmethod
    def select(*extras):
        return (
            select(
                Report.id,
                User.id.label("reporter_id"),
                User.display_name.label("reporter_display_name"),
                User.image.label("reporter_image"),
                Review.id.label("review_id"),
                Review.score.label("review_score"),
                Review.text.label("review_text"),
                Report.reason,
                Report.date_created,
                *extras
            ).
            join(User).
            join(Review)
        )

    @classmethod
    def create_from(cls, obj: Row):
        return cls(
            id=obj.id,
            reporter=UserBrief(
                id=obj.reporter_id,
                display_name=obj.reporter_display_name,
                image=obj.reporter_image
            ),
            review=ReviewBrief(
                id=obj.review_id,
                score=obj.review_score, text=obj.review_text
            ),
            reason=obj.reason,
            date_created=obj.date_created
        )
