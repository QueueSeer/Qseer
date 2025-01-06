from fastapi import APIRouter
from sqlalchemy import delete, insert, select, update
from sqlalchemy.exc import NoResultFound

from app.components.seer.service import check_active_seer
from app.core.deps import UserJWTDep, SeerJWTDep
from app.core.error import BadRequestException, NotFoundException
from app.database import SessionDep
from app.database.models import FPStatus

from . import responses as res
from .schemas import *
from .service import *


# /seer/me/package/fortune
router_me = APIRouter(prefix="/fortune")


@router_me.get("/", responses=res.get_self_fortune_package)
async def get_self_fortune_package(
    payload: SeerJWTDep,
    session: SessionDep,
    status: FPStatus = None,
    last_id: int = 0,
    limit: int = 10
):
    return PackageListOut(
        packages=await get_seer_fpackage(
            session, payload.sub,
            status, last_id, limit
        )
    )


@router_me.post("/", status_code=201, responses=res.draft_fpackage)
async def draft_fortune_package(
    payload: SeerJWTDep,
    session: SessionDep,
    fortune: FortunePackageDraft
):
    '''
    สร้างแพ็คเกจทำนายที่มีสถานะเป็น draft

    - **name**: ชื่อแพ็คเกจ ค่าที่จำเป็น
    - **duration**: [วิธีการส่งค่า timedelta](https://docs.pydantic.dev/latest/api/standard_library_types/#datetimetimedelta)
    - **foretell_channel**: ค่าที่เป็นไปได้คือ "chat", "phone", "video"
    - **required_data**: เป็น list ชื่อข้อมูลที่ต้องการจากผู้ใช้งาน
    ค่าภายในที่เป็นไปได้คือ "name", "birthdate", "phone_number"
    '''
    return await create_draft_fpackage(session, payload.sub, fortune)


# /seer/{seer_id}/package/fortune
router_id = APIRouter(prefix="/fortune")
