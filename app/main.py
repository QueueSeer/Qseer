from contextlib import asynccontextmanager

from fastapi import FastAPI, status
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware

from app.core.error import exc_handlers
from app.components import get_api_router
from app import (
    database,
    objectStorage
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    # await database.create_tables()
    yield
    # shutdown


app = FastAPI(lifespan=lifespan, exception_handlers=exc_handlers)
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
app.include_router(get_api_router())


@app.get("/", response_class=FileResponse)
async def root():
    return FileResponse('./app/index.html')


@app.get(
    "/brew/coffee",
    status_code=status.HTTP_418_IM_A_TEAPOT,
    response_class=PlainTextResponse,
    response_description="I'm a teapot."
)
async def brew_coffee():
    return "I refuses to brew coffee because I am, permanently, a teapot."
