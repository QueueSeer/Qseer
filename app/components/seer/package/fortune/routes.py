from fastapi import APIRouter
from sqlalchemy import delete, insert, select, update
from sqlalchemy.exc import NoResultFound

from app.components.seer.service import check_active_seer
from app.core.deps import SeerJWTDep
from app.core.error import BadRequestException, NotFoundException
from app.database import SessionDep
from app.database.models import FPStatus

from . import responses as res
from .schemas import *
from .service import *

# /seer/package/fortune
router = APIRouter(prefix="/fortune")

# /seer/me/package/fortune
router_me = APIRouter(prefix="/fortune")


@router_me.get("", responses=res.get_self_fpackage_cards)
async def get_self_fpackage_cards(
    payload: SeerJWTDep,
    session: SessionDep,
    status: FPStatus = None,
    last_id: int = 0,
    limit: int = 10
):
    '''
    ดูรายการแพ็คเกจดูดวงของตัวเอง
    '''
    return await get_seer_fpackage_cards(
        session, payload.sub,
        status, last_id, limit
    )


@router_me.post("", status_code=201, responses=res.draft_fpackage)
async def draft_fortune_package(
    payload: SeerJWTDep,
    session: SessionDep,
    fortune: FortunePackageDraft
):
    '''
    สร้างแพ็คเกจดูดวงที่มีสถานะเป็น draft

    - **name**: ชื่อแพ็คเกจ ค่าที่จำเป็น
    - **duration**: [วิธีการส่งค่า timedelta](https://docs.pydantic.dev/latest/api/standard_library_types/#datetimetimedelta)
    - **foretell_channel**: ค่าที่เป็นไปได้คือ "chat", "phone", "video"
    - **required_data**: เป็น list ชื่อข้อมูลที่ต้องการจากผู้ใช้งาน
    ค่าภายในที่เป็นไปได้คือ "name", "birthdate", "phone_number"
    '''
    return await create_draft_fpackage(session, payload.sub, fortune)


@router_me.get("/{package_id}", responses=res.get_self_fortune_package)
async def get_self_fortune_package(
    payload: SeerJWTDep,
    session: SessionDep,
    package_id: int
):
    '''
    ดูรายละเอียดแพ็คเกจดูดวงของตัวเอง
    '''
    try:
        return FortunePackageOut.model_validate(
            await get_seer_fpackage(session, payload.sub, package_id)
        )
    except NoResultFound:
        raise NotFoundException("Fortune package not found.")


@router_me.patch("/{package_id}", responses=res.edit_draft_fpackage)
async def edit_draft_fortune_package(
    payload: SeerJWTDep,
    session: SessionDep,
    package_id: int,
    fortune: FortunePackageDraft
):
    count = await update_fpackage(session, payload.sub, package_id, fortune)
    if count == 0:
        raise NotFoundException("Fortune package not found.")
    return fortune.model_dump(exclude_unset=True)


# /seer/{seer_id}/package/fortune
router_id = APIRouter(prefix="/fortune")


@router_id.get("", responses=res.get_seer_fpackage_cards)
async def get_seer_fpackage_cards(
    session: SessionDep,
    seer_id: int,
    last_id: int = 0,
    limit: int = 10
):
    '''
    ดูรายการแพ็คเกจดูดวงของหมอดู
    '''
    try:
        await check_active_seer(seer_id, session)
    except NoResultFound:
        raise NotFoundException("Seer not found.")

    return await get_seer_fpackage_cards(
        session, seer_id,
        FPStatus.published, last_id, limit
    )
