from psycopg.errors import UniqueViolation, UndefinedTable
from sqlalchemy import insert
from sqlalchemy.exc import IntegrityError, ProgrammingError, OperationalError
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.error import IntegrityException, InternalException
from app.database.models import Seer
from app.database.utils import parse_unique_violation
from .schemas import SeerRegister


async def create_seer(session: AsyncSession, seer_reg: SeerRegister, user_id: int) -> int:
    reg_dict = seer_reg.model_dump(exclude_unset=True)
    reg_dict["id"] = user_id
    try:
        stmt = insert(Seer).values(reg_dict).returning(Seer.id)
        seer_id = (await session.scalars(stmt)).one()
        await session.commit()
        return seer_id
    except IntegrityError as e:
        detail = {"type": "IntegrityError", "detail": "Unknown error."}
        if isinstance(e.orig, UniqueViolation):
            detail = parse_unique_violation(e.orig)
        raise IntegrityException(detail=detail)
    except ProgrammingError as e:
        detail = {"detail": "ProgrammingError"}
        if isinstance(e.orig, UndefinedTable):
            detail = {"detail": "Table undefined."}
        raise InternalException(detail=detail)
    except OperationalError as e:
        detail = {"detail": "Connection with database failed."}
        raise InternalException(detail=detail)
