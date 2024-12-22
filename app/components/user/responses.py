from app.core.schemas import UserId
from ..responses import *
from .schemas import *

register = {
    HTTP_201_CREATED: {
        "model": UserId,
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
    HTTP_403_FORBIDDEN: INVALID_TOKEN_EXAMPLE
}

get_self_info = {
    HTTP_200_OK: {
        "model": UserOut,
        "description": "User information."
    },
    **POSSIBLE_JWTCOOKIE_RESPONSE
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
    **POSSIBLE_JWTCOOKIE_RESPONSE
}

update_self_info = {
    HTTP_200_OK: {
        "model": UserUpdate,
        "description": "User information updated."
    },
    HTTP_404_NOT_FOUND: {
        "content": {
            "application/json": {
                "example": {"detail": "User not found."}
            }
        },
        "description": "The user is likely inactive or has been deleted."
    },
    **POSSIBLE_JWTCOOKIE_RESPONSE
}
