import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi_pagination import add_pagination
from sqlalchemy.exc import SQLAlchemyError

from core.logging import setup_logger
from core.settings import core_settings

from bootstrap.routers import setup_routers
from bootstrap.admin import setup_admin
from bootstrap.scheduler import setup_schedulers, shutdown_schedulers
from bootstrap.events import setup_events

logger = logging.getLogger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logger(name="main")
    logger.info(msg="Application starting")

    setup_schedulers(app=app, logger=logger)
    setup_events(app=app)

    yield

    shutdown_schedulers(app=app, logger=logger)
    logger.info(msg="Application stopped")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Testing-System UI API",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=core_settings.CORS_ORIGINS,
        allow_credentials=core_settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=core_settings.CORS_ALLOW_METHODS,
        allow_headers=core_settings.CORS_ALLOW_HEADERS,
    )

    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
        logger.error(f"Database error: {exc}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled error: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    @app.get("/health", tags=["system"])
    async def health():
        return {"status": "ok"}

    setup_routers(app)
    setup_admin(app=app)
    add_pagination(parent=app)

    return app


app = create_app()
