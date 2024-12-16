from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine
)

from app.core.config import settings
from .models import *

# engine = create_engine(settings.DATABASE_URL, echo=settings.DEVELOPMENT)
engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEVELOPMENT)
async_session = async_sessionmaker(engine, expire_on_commit=False)


async def get_session():
    async with async_session() as session:
        yield session


async def create_tables():
    async with engine.begin() as conn:
        conn.run_sync(Base.metadata.create_all)
    # Base.metadata.create_all(engine)


SessionDep = Annotated[AsyncSession, Depends(get_session)]
