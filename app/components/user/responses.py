from .schemas import *


login = {
    200: {
        "model": UserBase.Id,
        "description": "User logged in."
    },
    404: {
        "content": {
            "application/json": {
                "example": {"detail": "User not found."}
            }
        },
        "description": "Login failed."
    }
}

register = {
    201: {
        "model": UserBase.Id,
        "description": "User created."
    },
    409: {
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
    200: {
        "content": {
            "application/json": {
                "example": {"message": "User verified."}
            },
        },
        "description": "User verified."
    },
    400: {
        "content": {
            "application/json": {
                "example": {"detail": "User has been verified."}
            }
        },
        "description": "User has been verified or does not exist."
    },
    403: {
        "content": {
            "application/json": {
                "example": {"detail": "Invalid token."}
            }
        },
        "description": "Invalid token."
    }
}
