from app.core.schemas import RowCount, UserId
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

resend_email = {
    HTTP_200_OK: {
        "content": {
            "application/json": {
                "example": {"message": "Email sent."}
            }
        },
        "description": "Email sent."
    },
    HTTP_400_BAD_REQUEST: {
        "content": {
            "application/json": {
                "example": {"detail": "Email sent too soon."}
            }
        },
        "description": "Email sent too soon or user has been verified."
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

set_user_username = {
    HTTP_200_OK: {
        "model": UserUsername,
        "description": "Username set."
    },
    HTTP_400_BAD_REQUEST: {
        "content": {
            "application/json": {
                "example": {"detail": "Username has already been set."}
            }
        },
        "description": "Username has already been set."
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
    },
    HTTP_422_UNPROCESSABLE_ENTITY: {
        "content": {
            "application/json": {
                "example": {"detail": "Bad username"}
            }
        },
        "description": "Bad username."
    },
    **POSSIBLE_JWTCOOKIE_RESPONSE
}

get_following = {
    HTTP_200_OK: {
        "model": UserFollowing,
        "description": "List of following seers."
    },
    **POSSIBLE_JWTCOOKIE_RESPONSE
}

post_follow_seer = {
    HTTP_200_OK: {
        "model": UserId,
        "description": "Followed seer."
    },
    HTTP_404_NOT_FOUND: {
        "content": {
            "application/json": {
                "example": {"detail": "Seer not found."}
            }
        },
        "description": "Seer not found."
    },
    HTTP_409_CONFLICT: {
        "content": {
            "application/json": {
                "example": {"detail": "Already following."}
            }
        },
        "description": "Already following."
    },
    **POSSIBLE_JWTCOOKIE_RESPONSE
}

delete_follow_seer = {
    HTTP_200_OK: {
        "model": RowCount,
        "description": "The number of seers unfollowed."
    },
    **POSSIBLE_JWTCOOKIE_RESPONSE
}

search_users = {
    HTTP_200_OK: {
        "model": list[FollowProfile],
        "description": "List of users."
    },
    **POSSIBLE_JWTCOOKIE_RESPONSE
}

get_user_info = {
    HTTP_200_OK: {
        "model": UserOut,
        "description": "User information."
    },
    HTTP_404_NOT_FOUND: {
        "content": {
            "application/json": {
                "example": {"detail": "User not found."}
            }
        },
        "description": "User not found."
    },
    **POSSIBLE_JWTCOOKIE_RESPONSE
}
