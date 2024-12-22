from psycopg.errors import NotNullViolation, UniqueViolation, UndefinedTable
from sqlalchemy.exc import IntegrityError, ProgrammingError, OperationalError
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.error import IntegrityException, InternalException
from app.database.models import User
from app.database.utils import parse_unique_violation, parse_not_null_violation


async def create_user(session: AsyncSession, new_user: User) -> User:
    try:
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user, ["id"])
    except IntegrityError as e:
        detail = {"type": "IntegrityError", "detail": "Unknown error."}
        if isinstance(e.orig, UniqueViolation):
            detail = parse_unique_violation(e.orig)
        elif isinstance(e.orig, NotNullViolation):
            detail = parse_not_null_violation(e.orig)
        raise IntegrityException(detail=detail)
    except ProgrammingError as e:
        detail = {"detail": "ProgrammingError"}
        if isinstance(e.orig, UndefinedTable):
            detail = {"detail": "Table undefined."}
        raise InternalException(detail=detail)
    except OperationalError as e:
        detail = {"detail": "Connection with database failed."}
        raise InternalException(detail=detail)
    return new_user
