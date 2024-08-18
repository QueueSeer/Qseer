import functools as ft
import os
import importlib
from glob import glob

from fastapi import APIRouter


def get_api_router(*, prefix="/api", package="app.components", **kwargs):
    '''
    Get APIRouter that automatically include routers from each subpackages of `package`.
    Assume that each packages have APIRouter named **router**.

    ------
    The `prefix` and `**kwargs` got passed to APIRouter.

    Read more about it in the
    [FastAPI reference - APIRouter class](https://fastapi.tiangolo.com/reference/apirouter/)
    '''
    api_router = APIRouter(prefix=prefix, *kwargs)
    for name in glob(os.path.dirname(__file__) + "/*"):
        basename = os.path.basename(name)
        if basename.endswith(".py") or basename.startswith("_"):
            continue
        module = importlib.import_module(f".{basename}", package)
        try:
            api_router.include_router(module.router)
        except AttributeError:
            pass
    return api_router


get_api_router = ft.wraps(get_api_router)(ft.cache(get_api_router))
