from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException


class JSONException(HTTPException):
    '''
    For exceptions that should return JSON response.
    '''


class IntegrityException(JSONException):
    '''
    For database integrity exceptions.
    '''

    def __init__(self, detail, headers: dict[str, str] | None = None):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
            headers=headers
        )


class InternalException(JSONException):
    '''
    For Internal Server Error.
    '''

    def __init__(self, detail, headers: dict[str, str] | None = None):
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
