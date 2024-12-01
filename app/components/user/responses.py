from starlette.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_409_CONFLICT
)
from .schemas import *


invalid_token_example = {
    "content": {
        "application/json": {
            "example": {"detail": "Invalid token."}
        }
    },
    "description": "Invalid token."
}

no_cookie_example = {
    "content": {
        "application/json": {
            "example": {"detail": "Shoo! Go away!"}
        }
    },
    "description": "No cookie, no access."
}

possible_JWTCookie_response = {
    HTTP_401_UNAUTHORIZED: no_cookie_example,
    HTTP_403_FORBIDDEN: invalid_token_example
}

login = {
    HTTP_200_OK: {
        "model": UserBase.Id,
        "description": "User logged in."
    },
    HTTP_404_NOT_FOUND: {
        "content": {
            "application/json": {
                "example": {"detail": "User not found."}
            }
        },
        "description": "Login failed."
    }
}

logout = {
    HTTP_200_OK: {
        "content": {
            "application/json": {
                "example": {"message": "Logged out."}
            }
        },
        "description": "User logged out."
    },
    **possible_JWTCookie_response
}

register = {
    HTTP_201_CREATED: {
        "model": UserBase.Id,
        "description": "User created."
    },
    HTTP_409_CONFLICT: {
        "content": {
            "application/json": {
                "example": {
                    "field": "username", "value": "sanfong", "type": "UniqueViolation"
                }
            },
        },
        "description": "Username already exists."
    }
}

verify_user = {
    HTTP_200_OK: {
        "content": {
            "application/json": {
                "example": {"message": "User verified."}
            },
        },
        "description": "User verified."
    },
    HTTP_400_BAD_REQUEST: {
        "content": {
            "application/json": {
                "example": {"detail": "User has been verified."}
            }
        },
        "description": "User has been verified or does not exist."
    },
    HTTP_403_FORBIDDEN: invalid_token_example
}

get_self_info = {
    HTTP_200_OK: {
        "model": UserOut,
        "description": "User information."
    },
    **possible_JWTCookie_response
}

get_self_field = {
    HTTP_200_OK: {
        "content": {
            "application/json": {
                "example": {"field": "result"}
            }
        },
        "description": "User field."
    },
    **possible_JWTCookie_response
}

update_self_info = {
    HTTP_200_OK: {
        "model": UserUpdate,
        "description": "User information updated."
    },
    **possible_JWTCookie_response
}
