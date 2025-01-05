from typing import Mapping
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException


class BadRequestException(HTTPException):
    '''
    For 400 Bad Request.
    '''

    def __init__(self, detail, headers: Mapping[str, str] | None = None):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            headers=headers
        )


class NotFoundException(HTTPException):
    '''
    For 404 Not Found.
    '''

    def __init__(self, detail, headers: Mapping[str, str] | None = None):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            headers=headers
        )


class UnprocessableEntityException(HTTPException):
    '''
    For 422 Unprocessable Entity.
    '''

    def __init__(self, detail, headers: Mapping[str, str] | None = None):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
            headers=headers
        )


class JSONException(HTTPException):
    '''
    For exceptions that should return JSON response.
    '''


class IntegrityException(JSONException):
    '''
    For database integrity exceptions.
    '''

    def __init__(self, detail, headers: Mapping[str, str] | None = None):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
            headers=headers
        )


class InternalException(JSONException):
    '''
    For Internal Server Error.
    '''

    def __init__(self, detail, headers: Mapping[str, str] | None = None):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            headers=headers
        )


async def exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        content=exc.detail,
        status_code=exc.status_code,
        headers=exc.headers
    )


exc_handlers = {
    JSONException: exception_handler,
}
