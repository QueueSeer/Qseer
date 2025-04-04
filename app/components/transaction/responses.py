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

get_self_transactions = {
    HTTP_200_OK: {
        "model": list[TxnOut],
        "description": "Transactions retrieved."
    },
    **POSSIBLE_JWTCOOKIE_RESPONSE
}
