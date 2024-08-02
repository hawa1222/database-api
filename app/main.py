import time

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi import Request
from slowapi import Limiter
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.auth import create_admin
from app.database import db_connect
from app.models import auth_models
from app.routes import auth_routes
from app.routes import data_routes
from app.utils.logging import setup_logging

# ------------------------------
# Set up logging
# ------------------------------

logger = setup_logging()

# ------------------------------
# Setting up FastAPI application
# ------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Context manager for lifespan of application.

    Context manager responsible for setting up and shutting down application.
    Creates necessary database tables, creates admin user, and disposes of database engine.

    Parameters:
        app (FastAPI): FastAPI application instance.
    """
    try:
        logger.debug("Starting up app...")

        async with db_connect.engine.begin() as conn:
            await conn.run_sync(auth_models.Base.metadata.create_all, checkfirst=True)
            logger.debug(f"Table '{auth_models.User.__tablename__}' created")

        async with db_connect.SessionLocal() as db:
            await create_admin.create_admin_user(db)

        logger.debug("App started successfully")

        yield

    finally:
        logger.debug("Shutting down app and disposing of engine")
        await db_connect.engine.dispose()
        logger.debug("App shut down successfully")


app = FastAPI(lifespan=lifespan)


# ------------------------------
# Rate limiting configuration
# ------------------------------

limiter = Limiter(key_func=get_remote_address)  # Rate limiter instance for IP address

app.state.limiter = limiter  # Add rate limiter to app state

app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ------------------------------
# API endpoints for authentication
# ------------------------------

app.include_router(auth_routes.router)

# ------------------------------
# API endpoints for database operations
# ------------------------------

app.include_router(data_routes.router)

# ------------------------------
# Middleware for logging
# ------------------------------


@app.middleware("http")
async def log_requests_and_performance(request: Request, call_next):
    """
    Middleware function to log incoming requests, outgoing responses, and execution time.

    Parameters:
        request (Request): incoming request object.
        call_next (Callable): next middleware or endpoint to call.

    Returns:
        Response: outgoing response object.
    """
    start_time = time.perf_counter()  # perf_counter: higher precision timing

    logger.debug(f"Incoming request: {request.method} {request.url}")

    try:
        response = await call_next(request)
    except Exception as e:
        logger.error(
            f"Error processing request: {request.method} " f"{request.url}, Error: {str(e)}"
        )
        raise

    end_time = time.perf_counter()
    execution_time = end_time - start_time

    logger.debug(
        f"Outgoing response: {response.status_code}, Endpoint: "
        f"{request.method} {request.url.path},  Execution Time: {execution_time:.4f} seconds"
    )

    return response
