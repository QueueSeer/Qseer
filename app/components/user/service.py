from fastapi import HTTPException, status
from psycopg.errors import UniqueViolation, UndefinedTable
from sqlalchemy.exc import IntegrityError, ProgrammingError, OperationalError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.core.error import IntegrityException, InternalException
from app.database.models import User
from app.database.utils import parse_unique_violation
from .schemas import UserRegister


def create_user(session: Session, user: UserRegister) -> User:
    user.password = hash_password(user.password)
    try:
        new_user = User(**user.model_dump(), role="user")
        session.add(new_user)
        session.commit()
        session.refresh(new_user)
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
    return new_user
