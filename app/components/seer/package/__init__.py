from fastapi import APIRouter

from .fortune.routes import (
    router as fortune_router,
    router_me as fortune_route_me,
    router_id as fortune_route_id,
)
from .question.routes import (
    router_me as question_route_me,
    router_id as question_route_id,
)

pkg_api = APIRouter(prefix="/package", tags=["Package"])
me_api = APIRouter(prefix="/package", tags=["Package"])
id_api = APIRouter(prefix="/package", tags=["Package"])

pkg_api.include_router(fortune_router)
me_api.include_router(fortune_route_me)
id_api.include_router(fortune_route_id)

me_api.include_router(question_route_me)
id_api.include_router(question_route_id)
