import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.auth import create_admin
from app.database import db_connect
from app.models import auth_models
from app.routes import auth_routes, data_routes

# Custom imports
from app.utils.logging import setup_logging

# ------------------------------
# Set up logging
# ------------------------------

# Initialise logging
logger = setup_logging()

# ------------------------------
# Setting up FastAPI application
# ------------------------------


# Define lifespan event handler FastAPI application
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        logger.info("Starting up app")

        async with db_connect.engine.begin() as conn:
            await conn.run_sync(auth_models.Base.metadata.create_all, checkfirst=True)
            logger.info(f'Table "{auth_models.User.__tablename__}" created')

            # Create new session and pass to create_admin_user
            async with db_connect.SessionLocal() as db:
                try:
                    await create_admin.create_admin_user(db)
                finally:
                    await db.close()

        logger.info("App started successfully")

        yield

    finally:
        logger.info("Shutting down app and disposing of engine")
        await db_connect.engine.dispose()
        logger.info("App shut down successfully")


# Create an instance of FastAPI class with lifespan dependency
app = FastAPI(lifespan=lifespan)

# ------------------------------
# Rate limiting configuration
# ------------------------------

"""
Create Limiter instance
- key_func specifies function that returns unique identifier for each client
- get_remote_address used to identify clients based on their IP address
"""
limiter = Limiter(key_func=get_remote_address)

"""
Attach Limiter instance to FastAPI application's state, allowing
Limiter to be accessed and used throughout application
"""
app.state.limiter = limiter

"""
Register custom exception handler for RateLimitExceeded exception
- this handler is called when client exceeds rate limit
- returns  appropriate error response to client
"""
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


# Middleware decorators used to execute code before & after each request
@app.middleware("http")
async def log_requests_and_performance(request: Request, call_next):
    """
    Middleware function to log incoming requests,
    outgoing responses, and execution time.

    Parameters:
        request (Request): incoming request object.
        call_next (Callable): next middleware or endpoint to call.

    Returns:
        Response: outgoing response object.
    """
    start_time = time.perf_counter()  # perf_counter: higher precision timing

    # Log incoming request
    logger.info(f"Incoming request: {request.method} {request.url}")

    try:
        response = await call_next(request)
    except Exception as e:
        # Log any exceptions that occur during request processing
        logger.error(
            f"Error processing request: {request.method} " f"{request.url}, Error: {str(e)}"
        )
        raise

    end_time = time.perf_counter()
    execution_time = end_time - start_time

    # Log outgoing response and execution time
    logger.info(
        f"Outgoing response: {response.status_code}, Endpoint: "
        f"{request.method} {request.url.path},  Execution Time: "
        f"{execution_time:.4f} seconds"
    )

    return response
