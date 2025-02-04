from ..responses import *
from .schemas import *

list_withdraw_requests = {
    HTTP_200_OK: {
        "model": list[WithdrawalOut],
        "description": "Withdrawal requests retrieved."
    },
    **POSSIBLE_JWTCOOKIE_RESPONSE
}

request_withdrawal = {
    HTTP_201_CREATED: {
        "model": WithdrawRequestResult,
        "description": "Withdrawal requested."
    },
    HTTP_400_BAD_REQUEST: {
        "content": {
            "application/json": {
                "example": {"detail": "Insufficient balance."}
            }
        },
        "description": "Insufficient balance."
    },
    **POSSIBLE_JWTCOOKIE_RESPONSE
}

get_withdraw_request = {
    HTTP_200_OK: {
        "model": WithdrawalOut,
        "description": "Withdrawal request retrieved."
    },
    HTTP_404_NOT_FOUND: {
        "content": {
            "application/json": {
                "example": {"detail": "Request not found."}
            }
        },
        "description": "Withdrawal request not found."
    },
    **POSSIBLE_JWTCOOKIE_RESPONSE
}

complete_request = {
    HTTP_200_OK: {
        "content": {
            "application/json": {
                "example": {"message": "Completed."}
            }
        },
        "description": "Withdrawal request completed."
    },
    **POSSIBLE_JWTCOOKIE_RESPONSE
}

reject_request = {
    HTTP_200_OK: {
        "content": {
            "application/json": {
                "example": {"message": "Rejected."}
            }
        },
        "description": "Withdrawal request rejected."
    },
    **POSSIBLE_JWTCOOKIE_RESPONSE
}

cancel_request = {
    HTTP_200_OK: {
        "content": {
            "application/json": {
                "example": {"message": "Cancelled."}
            }
        },
        "description": "Withdrawal request cancelled."
    },
    **POSSIBLE_JWTCOOKIE_RESPONSE
}