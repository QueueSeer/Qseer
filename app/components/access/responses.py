from app.core.schemas import UserId
from ..responses import *
from .schemas import *

google_signin = {
    HTTP_200_OK: {
        "model": UserId,
        "description": "User signed in."
    },
    HTTP_400_BAD_REQUEST: {
        "content": {
            "application/json": {
                "example": {"detail": "Username is required."}
            }
        },
        "description": "Username is missing."
    },
    HTTP_403_FORBIDDEN: {
        "content": {
            "application/json": {
                "example": {"detail": "Token expired, T < T+1"}
            }
        },
        "description": "Invalid token, e.g. Token expired."
    },
    HTTP_404_NOT_FOUND: {
        "content": {
            "application/json": {
                "example": {"detail": "User not found."}
            }
        },
        "description": "User is inactive."
    }
}

login = {
    HTTP_200_OK: {
        "model": UserId,
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
    **POSSIBLE_JWTCOOKIE_RESPONSE
}

refresh = {
    HTTP_200_OK: {
        "model": UserId,
        "description": "User refreshed."
    },
    HTTP_404_NOT_FOUND: {
        "content": {
            "application/json": {
                "example": {"detail": "User not found."}
            }
        },
        "description": "Refresh failed."
    },
    **POSSIBLE_JWTCOOKIE_RESPONSE
}