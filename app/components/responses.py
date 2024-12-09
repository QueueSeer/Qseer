from starlette.status import *

NO_COOKIE_EXAMPLE = {
    "content": {
        "application/json": {
            "example": {"detail": "Shoo! Go away!"}
        }
    },
    "description": "No cookie, no access."
}
INVALID_TOKEN_EXAMPLE = {
    "content": {
        "application/json": {
            "example": {"detail": "Invalid token."}
        }
    },
    "description": "Invalid token."
}
POSSIBLE_JWTCOOKIE_RESPONSE = {
    HTTP_401_UNAUTHORIZED: NO_COOKIE_EXAMPLE,
    HTTP_403_FORBIDDEN: INVALID_TOKEN_EXAMPLE
}
