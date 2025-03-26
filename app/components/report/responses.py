from ..responses import *
from .schemas import *

get_report_list = {
    HTTP_200_OK: {
        "model": list[ReportOut],
        "description": "List of reports."
    },
    **POSSIBLE_JWTCOOKIE_RESPONSE
}

get_report_detail = {
    HTTP_200_OK: {
        "model": ReportOut,
        "description": "Report detail."
    },
    HTTP_404_NOT_FOUND: {
        "content": {
            "application/json": {
                "example": {"detail": "Report not found."}
            }
        },
        "description": "Report not found.",
    },
    **POSSIBLE_JWTCOOKIE_RESPONSE
}

make_a_report = {
    HTTP_200_OK: {
        "model": ReportId,
        "description": "Reported."
    },
    **POSSIBLE_JWTCOOKIE_RESPONSE
}
