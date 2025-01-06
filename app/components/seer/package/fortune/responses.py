from app.core.schemas import RowCount, UserId
from app.components.seer.schemas import SeerObjectId
from app.components.responses import *
from .schemas import *

get_self_fortune_package = {
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
