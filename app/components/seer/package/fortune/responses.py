from app.components.seer.schemas import SeerObjectId
from app.components.responses import *
from app.core.schemas import RowCount
from .schemas import *

search_fp = {
    HTTP_200_OK: {
        "model": PackageListOut,
        "description": "List of fortune packages."
    }
}

get_self_fortune_package_cards = {
    HTTP_200_OK: {
        "model": PackageListOut,
        "description": "List of fortune packages."
    },
    **POSSIBLE_JWTCOOKIE_RESPONSE
}

draft_fpackage = {
    HTTP_201_CREATED: {
        "model": SeerObjectId,
        "description": "Drafted fortune package successfully."
    },
    **POSSIBLE_JWTCOOKIE_RESPONSE
}

get_self_fortune_package = {
    HTTP_200_OK: {
        "model": FortunePackageOut,
        "description": "Fortune package detail."
    },
    HTTP_404_NOT_FOUND: {
        "content": {
            "application/json": {
                "example": {
                    "detail": "Fortune package not found."
                }
            },
        },
        "description": "Fortune package not found."
    },
    **POSSIBLE_JWTCOOKIE_RESPONSE
}

edit_draft_fpackage = {
    HTTP_200_OK: {
        "model": FortunePackageDraft,
        "description": "Edited fortune package successfully."
    },
    HTTP_404_NOT_FOUND: {
        "content": {
            "application/json": {
                "example": {
                    "detail": "Fortune package not found."
                }
            },
        },
        "description": "Fortune package not found or is not a draft."
    },
    **POSSIBLE_JWTCOOKIE_RESPONSE
}

fpackage_status = {
    HTTP_200_OK: {
        "model": FPStatusChange,
        "description": "Changed fortune package status successfully."
    },
    HTTP_400_BAD_REQUEST: {
        "content": {
            "application/json": {
                "example": {
                    "detail": "Cannot change status to draft."
                }
            },
        },
        "description": "Cannot change status to draft."
    },
    HTTP_404_NOT_FOUND: {
        "content": {
            "application/json": {
                "example": {
                    "detail": "Fortune package not found."
                }
            },
        },
        "description": "Fortune package not found."
    },
    HTTP_409_CONFLICT: {
        "content": {
            "application/json": {
                "example": {
                    "detail": "Field is required.",
                    "field": "field"
                }
            },
        },
        "description": "Missing required field."
    },
    **POSSIBLE_JWTCOOKIE_RESPONSE
}

delete_self_fortune_package = {
    HTTP_200_OK: {
        "model": RowCount,
        "description": "The number of fortune package deleted."
    },
    **POSSIBLE_JWTCOOKIE_RESPONSE
}

get_seer_fortune_package_cards = {
    HTTP_200_OK: {
        "model": PackageListOut,
        "description": "List of fortune packages."
    }
}

get_seer_fortune_package = {
    HTTP_200_OK: {
        "model": FortunePackageOut,
        "description": "Fortune package detail."
    },
    HTTP_404_NOT_FOUND: {
        "content": {
            "application/json": {
                "example": {
                    "detail": "Fortune package not found."
                }
            },
        },
        "description": "Fortune package not found."
    }
}

get_time_slots = {
    HTTP_200_OK: {
        "model": list[TimeSlot],
        "description": "List of available time slots."
    },
    HTTP_404_NOT_FOUND: {
        "content": {
            "application/json": {
                "example": {
                    "detail": "Not found."
                }
            },
        },
        "description": "Seer or Fortune package not found."
    }
}