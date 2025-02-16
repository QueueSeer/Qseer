from ..responses import *
from .schemas import *

get_appointments = {
    HTTP_200_OK: {
        "model": list[AppointmentBrief],
        "description": "List of sent appointments."
    },
    **POSSIBLE_JWTCOOKIE_RESPONSE
}

get_an_appointment = {
    HTTP_200_OK: {
        "model": AppointmentOut,
        "description": "Appointment retrieved."
    },
    HTTP_404_NOT_FOUND: {
        "content": {
            "application/json": {
                "example": {"detail": "Appointment not found."}
            }
        },
        "description": "Appointment not found."
    },
    **POSSIBLE_JWTCOOKIE_RESPONSE
}

get_seer_appointments = {
    HTTP_200_OK: {
        "model": list[AppointmentPublic],
        "description": "List of seer's public appointments."
    },
    HTTP_400_BAD_REQUEST: {
        "content": {
            "application/json": {
                "example": {"detail": "Date range must not exceed 90 days."}
            }
        },
        "description": "Date range must not exceed 90 days."
    },
}

make_an_appointment = {
    HTTP_201_CREATED: {
        "model": AppointmentCreated,
        "description": "Appointment created."
    },
    HTTP_400_BAD_REQUEST: {
        "content": {
            "application/json": {
                "example": {"detail": "Invalid input."}
            }
        },
        "description": "Exceeded question limit, Insufficient coins or Time slot not available."
    },
    HTTP_404_NOT_FOUND: {
        "content": {
            "application/json": {
                "example": {"detail": "Not found."}
            }
        },
        "description": "Seer or Fortune package not found."
    },
    **POSSIBLE_JWTCOOKIE_RESPONSE
}