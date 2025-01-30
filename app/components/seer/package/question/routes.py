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
from app.database.models import Seer,QuestionPackage
from app.components.seer.service import check_active_seer

from . import responses as res
from .schemas import *
from .service import *

# /seer/me/package/question
router_me = APIRouter(prefix="/question")


@router_me.get("")
async def get_QuestionPackage(payload: SeerJWTDep, session: SessionDep):
    '''
    200 OK: return QuestionPackageIn ที่ได้รับเข้ามา
    400 Bad Request: BadRequestException("Seer not found.")
    (กรณีล้าง db แต่ token ยังอยู่ / ใช้ 400 front จะได้แยกออกง่าย)
    404 Not Found: NotFoundException("QuestionPackage not found.")
    '''
    user_id = payload.sub
    result = await get_questionpackage(session, user_id)
    if result is None:
        raise NotFoundException("QuestionPackage found.")
    return result
# ดึง QuestionPackageOut ของ Seer ตัวเอง
# Status code:
# 200 OK: return QuestionPackageIn ที่ได้รับเข้ามา
# 400 Bad Request: BadRequestException("Seer not found.")
# ... (กรณีล้าง db แต่ token ยังอยู่ / ใช้ 400 front จะได้แยกออกง่าย)
# 404 Not Found: NotFoundException("QuestionPackage not found.")


@router_me.put("")
async def put_QuestionPackage(payload: SeerJWTDep, session: SessionDep,data : QuestionPackageIn):
    '''
    young mai dy write doc na
    '''
    user_id = payload.sub
    try:
        await check_active_seer(user_id, session)
    except NoResultFound:
        raise NotFoundException("Seer not found.")
    pass
    result = await edit_questionpackage(session, user_id,data)
    if result is None:
        raise IntegrityException("Wrong Value")
    return result
# params ใน QuestionPackageIn ทั้งหมดเป็น optional
# (upsert / insert ... on conflict)
# TODO: รับ QuestionPackageIn เข้ามา
# ถ้าไม่เคยมี QuestionPackage มาก่อนให้สร้างใหม่ ควรจะ error ถ้าใส่ param ไม่ครบ
# ถ้ามี QuestionPackage แล้วให้อัพเดทตามค่าที่ส่งเข้ามา
# สรุปก็คือทำหน้าสร้างและแก้ไขใน api เดียว
# Status code:
# 200 OK: return QuestionPackageIn ที่ได้รับเข้ามา
# 404 Not Found: NotFoundException("Seer not found.")
# 409 Conflict (IntegrityException): error จากการ insert ครั้งแรกแล้วใส่ค่าไม่ครบ


# /seer/{seer_id}/package/question
router_id = APIRouter(prefix="/question")


@router_id.get("")
async def GetPacket(session: SessionDep,seer_id : int):
    result = await get_questionpackage(session,seer_id)
    if result is None:
        raise NotFoundException("QuestionPackage not found.")
    return result
# ดึง QuestionPackageOut ของ Seer ที่ระบุ
# Status code:
# 200 OK: return QuestionPackageIn ที่ได้รับเข้ามา
# 400 Bad Request: BadRequestException("Seer not found.")
# ... (กรณีล้าง db แต่ token ยังอยู่ / ใช้ 400 front จะได้แยกออกง่าย)
# 404 Not Found: NotFoundException("QuestionPackage not found.")
# ไปสร้าง func ใน service ซะไอสาสสส
