from app.core.schemas import RowCount, UserId
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

get_seer_me = {
    HTTP_200_OK: {
        "model": SeerGetMe,
        "description": "Seer information."
    },
    HTTP_404_NOT_FOUND: {
        "content": {
            "application/json": {
                "example": {
                    "detail": "Seer not found."
                }
            },
        },
        "description": "Seer does not exist."
    }
}

update_seer_me = {
    HTTP_200_OK: {
        "model": SeerUpdate,
        "description": "Seer information updated."
    },
    HTTP_404_NOT_FOUND: {
        "content": {
            "application/json": {
                "example": {
                    "detail": "Seer not found."
                }
            },
        },
        "description": "Seer does not exist."
    }
}

edit_seer_schedule = {
    HTTP_200_OK: {
        "model": list[SeerScheduleIn],
        "description": "Schedules created."
    },
    **POSSIBLE_JWTCOOKIE_RESPONSE
}

seer_dayoff = {
    HTTP_201_CREATED: {
        "content": {
            "application/json": {
                "example": {"message": "Day off added."}
            },
        },
        "description": "Day off added."
    },
    **POSSIBLE_JWTCOOKIE_RESPONSE
}

delete_seer_dayoff = {
    HTTP_200_OK: {
        "model": RowCount,
        "description": "Returned the number of deleted day offs."
    },
    **POSSIBLE_JWTCOOKIE_RESPONSE
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
                    "detail": "Seer not found."
                }
            },
        },
        "description": "Seer does not exist."
    }
}

seer_followers = {
    HTTP_200_OK: {
        "model": SeerFollowers,
        "description": "List of followers."
    }
}

seer_total_followers = {
    HTTP_200_OK: {
        "model": RowCount,
        "description": "Total number of followers."
    }
}

seer_calendar = {
    HTTP_200_OK: {
        "model": SeerCalendar,
        "description": "Seer's calendar."
    },
    HTTP_404_NOT_FOUND: {
        "content": {
            "application/json": {
                "example": {
                    "detail": "Seer not found."
                }
            },
        },
        "description": "Seer does not exist."
    }
}
