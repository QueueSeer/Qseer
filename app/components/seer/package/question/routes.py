from fastapi import APIRouter
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound

from app.core.deps import SeerJWTDep
from app.core.error import (
    BadRequestException,
    IntegrityException,
    NotFoundException
)
from app.database import SessionDep
from app.database.models import Seer, QuestionPackage
from app.components.seer.service import check_active_seer

from . import responses as res
from .schemas import *
from .service import *

# /seer/me/package/question
router_me = APIRouter(prefix="/question")


@router_me.get("")
async def get_QuestionPackage(payload: SeerJWTDep, session: SessionDep):
    '''
    ดูข้อมูล QuestionPackage
    '''
    user_id = payload.sub
    result = await get_questionpackage(session, user_id)
    if result is None:
        raise NotFoundException("QuestionPackage found.")
    return result


@router_me.put("")
async def put_QuestionPackage(payload: SeerJWTDep, session: SessionDep, data: QuestionPackageIn):
    '''
    Edit Question Package set ค่าครั้งแรกต้องใส่ครบทุกช่อง
    ครั้งต่อๆ ไปใส่แค่บางช่องก็ได้
    '''
    user_id = payload.sub
    try:
        await check_active_seer(user_id, session)
    except NoResultFound:
        raise NotFoundException("Seer not found.")
    pass

    result = await edit_questionpackage(session, user_id, data)
    if result is None:
        raise IntegrityException("Wrong Value")
    return result


router_id = APIRouter(prefix="/question")


@router_id.get("")
async def GetPacket(session: SessionDep, seer_id: int):
    '''
    ดูข้อมูล QuestionPackage seer id
    '''
    result = await get_questionpackage(session, seer_id)
    if result is None:
        raise NotFoundException("QuestionPackage not found.")
    return result
