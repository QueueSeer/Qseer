from app.core.schemas import RowCount
from ..responses import *
from .schemas import *

get_review_list = {
    HTTP_200_OK: {
        "model": list[ReviewOut],
        "description": "List of reviews",
    },
    **POSSIBLE_JWTCOOKIE_RESPONSE
}

review_detail = {
    HTTP_200_OK: {
        "model": ReviewOut,
        "description": "Review detail",
    },
    HTTP_404_NOT_FOUND: {
        "content": {
            "application/json": {
                "example": {"detail": "Review not found."}
            }
        },
        "description": "Review not found.",
    },
    **POSSIBLE_JWTCOOKIE_RESPONSE
}

review_service = {
    HTTP_201_CREATED: {
        "model": ReviewCreate,
        "description": "Review created",
    },
    HTTP_400_BAD_REQUEST: {
        "content": {
            "application/json": {
                "example": {
                    "detail": "Not client or\
                        Appointment not ended or Already reviewed."
                    }
            }
        },
        "description": "Not client or Appointment not ended or\
            Already reviewed.",
    },
    HTTP_404_NOT_FOUND: {
        "content": {
            "application/json": {
                "example": {"detail": "Appointment not found."}
            }
        },
        "description": "Appointment not found.",
    },
    **POSSIBLE_JWTCOOKIE_RESPONSE
}

remove_review = {
    HTTP_200_OK: {
        "model": RowCount,
        "description": "Review removed",
    },
    HTTP_404_NOT_FOUND: {
        "content": {
            "application/json": {
                "example": {"detail": "Review not found."}
            }
        },
        "description": "Review not found.",
    },
    **POSSIBLE_JWTCOOKIE_RESPONSE
}
