from contextlib import asynccontextmanager

from fastapi import FastAPI, status
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware

from app.core.error import exc_handlers
from app.components import get_api_router, tags_metadata
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


origins = [
    "https://qseer.app",
    "https://seer.qseer.app",
    "https://admin.qseer.app",
    "http://localhost",
    "http://localhost:5173",
    "http://localhost:5500",
    "http://127.0.0.1",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5500",
]

app = FastAPI(
    lifespan=lifespan,
    exception_handlers=exc_handlers,
    openapi_tags=tags_metadata,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
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


if __name__ == "__main__":
    import asyncio
    from fastapi_cli.cli import run
    
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    run()
