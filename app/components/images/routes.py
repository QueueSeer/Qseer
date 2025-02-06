from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
import urllib.parse

from psycopg.errors import UniqueViolation
from sqlalchemy import delete, select, update, insert
from sqlalchemy.exc import NoResultFound, IntegrityError

from app.core.deps import UserJWTDep
from app.database.models import FPStatus
from app.core.error import (
    BadRequestException,
    NotFoundException,
    InternalException,
    IntegrityException,
    UnprocessableEntityException,
)

from app.database import SessionDep
from app.database.models import User, QuestionPackage, FortunePackage, AuctionInfo
from app.database.utils import parse_unique_violation


from .service import *
router = APIRouter(prefix="/image", tags=["Image"])


@router.post("/user")
async def upload_user_profile_image(payload: UserJWTDep, session: SessionDep, file: UploadFile = File(...)):
    '''
    upload รูป profile
    (PNG or JPG) (Size < 10MB)
    '''
    user_id = payload.sub
    part = "user"
    file_name = str(user_id)

    if not await ValidateFile(file):
        raise HTTPException(
            status_code=400, detail="Only PNG and JPG files are allowed or File too large. Max size is 10MB.")

    local_url = CreateUrl(part, file_name)
    stmt = (
        update(User).
        where(User.id == user_id, User.is_active == True).
        values(image=local_url).
        returning(User.id)
    )

    result = (await session.execute(stmt)).one_or_none()
    if result is None:
        raise NotFoundException("User not found.")

    if not await UploadImage(part, file_name, file):
        raise HTTPException(status_code=500, detail='Fail To Upload')

    await session.commit()
    return {"url": local_url}


@router.post("/package/fortune/{package_id}")
async def upload_fortune_package_image(payload: UserJWTDep, session: SessionDep, package_id: int, file: UploadFile = File(...)):
    '''
    upload รูป fortune package
    (PNG or JPG) (Size < 10MB)
    '''
    user_id = payload.sub
    part = "package/fortune"
    file_name = str(user_id)+"-"+str(1)

    if not await ValidateFile(file):
        raise HTTPException(
            status_code=400, detail="Only PNG and JPG files are allowed or File too large. Max size is 10MB.")

    local_url = CreateUrl(part, file_name)
    stmt = (
        update(FortunePackage).
        where(FortunePackage.id == package_id,
              FortunePackage.seer_id == user_id,
              FortunePackage.status == FPStatus.draft).
        values(image=local_url).
        returning(FortunePackage.id)
    )

    result = (await session.execute(stmt)).one_or_none()
    if result is None:
        raise NotFoundException("Fortune Package not found.")

    if not await UploadImage(part, file_name, file):
        raise HTTPException(status_code=500, detail='Fail To Upload')

    await session.commit()
    return {"url": local_url}


@router.post("/package/question")
async def upload_question_package_image(payload: UserJWTDep, session: SessionDep, file: UploadFile = File(...)):
    '''
    upload รูป question package
    (PNG or JPG) (Size < 10MB)
    '''
    user_id = payload.sub
    part = "package/question"
    file_name = str(user_id)+"-"+str(1)

    if not await ValidateFile(file):
        raise HTTPException(
            status_code=400, detail="Only PNG and JPG files are allowed or File too large. Max size is 10MB.")

    local_url = CreateUrl(part, file_name)
    stmt = (
        update(QuestionPackage).
        where(QuestionPackage.seer_id == user_id, QuestionPackage.id == 1).
        values(image=local_url).
        returning(QuestionPackage.id)
    )

    result = (await session.execute(stmt)).one_or_none()
    if result is None:
        raise NotFoundException("Package Question not found.")

    if not await UploadImage(part, file_name, file):
        raise HTTPException(status_code=500, detail='Fail To Upload')

    await session.commit()
    return {"url": local_url}
