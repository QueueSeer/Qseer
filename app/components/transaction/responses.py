from ..responses import *
from .schemas import *

confirm_topup = {
    HTTP_200_OK: {
        "model": UserCoins,
        "description": "Topup confirmed."
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
