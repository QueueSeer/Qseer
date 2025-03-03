import functools as ft
import importlib
import pkgutil
from fastapi import APIRouter


def get_api_router(*, prefix="/api", **kwargs):
    '''
    Get APIRouter that automatically include routers from each subpackages of `package`.
    Assume that each packages have APIRouter named **router**.

    ------
    The `prefix` and `**kwargs` got passed to APIRouter.

    Read more about it in the
    [FastAPI reference - APIRouter class](https://fastapi.tiangolo.com/reference/apirouter/)

    ------
    Do not name new package with existing name.
    '''
    api_router = APIRouter(prefix=prefix, **kwargs)
    for _, module_name, _ in pkgutil.walk_packages(__path__):
        module = importlib.import_module(f".{module_name}", __package__)
        try:
            api_router.include_router(module.router)
        except AttributeError:
            pass
    return api_router


get_api_router = ft.wraps(get_api_router)(ft.cache(get_api_router))

tags_metadata = [
    {
        "name": "Access",
        "description": "For authentication"
    },
    {
        "name": "User",
        "description": "Register and operations with User."
    },
    {
        "name": "Seer",
        "description": "Operations with Seer."
    },
    {
        "name": "Seer Me",
        "description": "Subset of Seer tag. Start with /me"
    },
    {
        "name": "Seer Id",
        "description": "Subset of Seer tag. Start with /{seer_id}"
    },
    {
        "name": "Package",
        "description": "Operations with Seer Package."
    },
    {
        "name": "Withdraw",
        "description": "CRUD Withdraw request."
    },
    {
        "name": "Transaction",
        "description": "Topup and read transaction."
    },
    {
        "name": "Appointment",
        "description": "Operations with Appointment."
    },
]
