from datetime import timedelta
from typing import Annotated
from fastapi import (
    APIRouter,
    HTTPException,
    Request,
    Response,
    status,
    Depends,
)
from sqlalchemy import delete, insert, select, update

from app.core.config import settings
from app.core.deps import UserJWTDep
from app.core.security import (
    create_jwt,
    decode_jwt,
    verify_password,
)
from app.core.schemas import Message, UserId
from app.database import SessionDep
from app.database.models import Seer

from . import responses as res
from .schemas import SeerRegister
from .service import create_seer


router = APIRouter(prefix="/seer", tags=["Seer"])


@router.post("/signup", responses=res.seer_signup)
async def seer_signup(seer_reg: SeerRegister, payload: UserJWTDep, session: SessionDep):
    seer_id = create_seer(session, seer_reg, payload.sub)
    token = create_jwt({"seer_confirm": seer_id}, timedelta(days=1))
    # TODO: send email to user
    print(token)
    return UserId(id=seer_id)


# ยืนยันการสมัครหมอดู
# GET /confirm/{token}


# ดูข้อมูลหมอดู [Public]
# display_name, first_name, last_name, image, experience, description, verified_at, rating, follower_count
# GET /{seer_id}


# ดูรายชื่อผู้ติดตามหมอดู
# display_name, image
# GET /{seer_id}/followers


# ดูตารางเวลาและวันหยุดหมอดู [Public]
# Schedule, DayOff
# GET /{seer_id}/schedule_and_dayoff


# สร้างตารางเวลาหมอดู
# POST /me/schedule


# แก้ไขตารางเวลาหมอดู
# PATCH /me/schedule


# ลบตารางเวลาหมอดู
# DELETE /me/schedule


# เพิ่มหรือแก้ไขวันหยุดหมอดู
# PUT /me/dayoff


# ลบวันหยุดหมอดู
# DELETE /me/dayoff
