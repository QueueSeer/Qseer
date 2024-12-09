from psycopg.errors import UniqueViolation, UndefinedTable
from sqlalchemy.exc import IntegrityError, ProgrammingError, OperationalError
from sqlalchemy.orm import Session

from app.core.error import IntegrityException, InternalException
from app.database.models import User
from app.database.utils import parse_unique_violation


def create_user(session: Session, new_user: User) -> User:
    try:
        session.add(new_user)
        session.commit()
        session.refresh(new_user, ["id"])
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
