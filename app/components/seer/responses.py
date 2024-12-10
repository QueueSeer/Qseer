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