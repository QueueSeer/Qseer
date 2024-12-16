from app.core.schemas import UserId
from ..responses import *
from .schemas import *

seer_signup = {
    HTTP_201_CREATED: {
        "model": UserId,
        "description": "Seer created."
    },
    HTTP_409_CONFLICT: {
        "content": {
            "application/json": {
                "example": {
                    "field": "id", "value": "1", "type": "UniqueViolation"
                }
            },
        },
        "description": "User has already signed up as seer."
    },
    **POSSIBLE_JWTCOOKIE_RESPONSE
}

seer_confirm = {
    HTTP_200_OK: {
        "content": {
            "application/json": {
                "example": {"message": "Confirmation successful."}
            },
        },
        "description": "The seer's signup has confirmed successfully."
    },
    HTTP_400_BAD_REQUEST: {
        "content": {
            "application/json": {
                "example": {
                    "message": "Already confirmed."
                }
            },
        },
        "description": "The seer's signup has been confirmed or does not exist."
    },
    HTTP_403_FORBIDDEN: INVALID_TOKEN_EXAMPLE
}

seer_info = {
    HTTP_200_OK: {
        "model": SeerOut,
        "description": "Seer information."
    },
    HTTP_404_NOT_FOUND: {
        "content": {
            "application/json": {
                "example": {
                    "message": "Seer not found."
                }
            },
        },
        "description": "Seer does not exist."
    }
}
