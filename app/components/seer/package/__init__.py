from fastapi import APIRouter

from .fortune.routes import (
    router_me as fortune_route_me,
    router_id as fortune_route_id,
)

me_api = APIRouter(prefix="/package", tags=["Package"])
id_api = APIRouter(prefix="/package", tags=["Package"])

me_api.include_router(fortune_route_me)
id_api.include_router(fortune_route_id)
