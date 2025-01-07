from app.core.schemas import RowCount, UserId
from app.components.seer.schemas import SeerObjectId
from app.components.responses import *
from .schemas import *

get_self_fpackage_cards = {
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

get_seer_fpackage_cards = {
    HTTP_200_OK: {
        "model": PackageListOut,
        "description": "List of fortune packages."
    }
}
