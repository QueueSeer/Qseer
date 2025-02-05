from fastapi import APIRouter, Depends , File, UploadFile, HTTPException
import urllib.parse

from psycopg.errors import UniqueViolation
from sqlalchemy import delete, select, update, insert
from sqlalchemy.exc import NoResultFound, IntegrityError

from app.core.deps import UserJWTDep
from app.core.error import (
    BadRequestException,
    NotFoundException,
    InternalException,
    IntegrityException,
    UnprocessableEntityException,
)

from app.database import SessionDep
from app.database.models import User
from app.database.utils import parse_unique_violation


from .service import *
router = APIRouter(prefix="/image", tags=["Image"])

@router.post("/user")
async def upload_user_profile( payload: UserJWTDep, session: SessionDep, file: UploadFile = File(...)):

    user_id = payload.sub

    local_url = CreateUrl("user",str(user_id))
    stmt = (
        update(User).
        where(User.id == user_id, User.is_active == True).
        values(image = local_url).
        returning(User.id)
    )

    if not await UploadImage("user",str(user_id),file):
        raise HTTPException(status_code=500, detail='Fail To Upload')
    
    result = (await session.execute(stmt)).one_or_none()
    if result is None:
        raise NotFoundException("User not found.")
    await session.commit()
    return [{"filename": file.filename},{"fileType":file.content_type},{"url": local_url}]