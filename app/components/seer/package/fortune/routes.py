from fastapi import APIRouter, status
from sqlalchemy import delete, insert, select, update

from app.core.deps import UserJWTDep, SeerJWTDep
from app.core.error import BadRequestException, NotFoundException
from app.database import SessionDep

# /seer/me/package/fortune
router_me = APIRouter(prefix="/fortune")


@router_me.get("/") 
async def get_fortune(payload: SeerJWTDep, session: SessionDep):
    return "I refuses to brew coffee because I am, permanently, a teapot."


# /seer/{seer_id}/package/fortune
router_id = APIRouter(prefix="/fortune")
