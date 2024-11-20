from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.config import settings
from .models import *

engine = create_engine(settings.DATABASE_URL, echo=settings.DEVELOPMENT)


def get_session():
    with Session(engine) as session, session.begin():
        yield session


def create_tables():
    Base.metadata.create_all(engine)
