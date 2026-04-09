"""FastAPI application entry point."""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import setup_logging
from app.db.session import engine
from app.db.base import Base
from app.chat.redis_cache import get_redis, close_redis
from app.api.v1.router import api_router
from app.chat.websocket.connection_manager import connection_manager
from app.chat.websocket.chat_endpoint import websocket_chat_endpoint
from app.integrations.llm.factory import close_llm_clients

logger = setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}...")

    # Create database tables
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables verified/created")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")

    # Verify Redis connection
    try:
        redis = await get_redis()
        await redis.ping()
        logger.info("Redis connection established")
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}")

    logger.info(f"LLM Provider: {settings.LLM_PROVIDER.upper()} ({settings.ENV})")

    yield

    # Shutdown
    logger.info("Shutting down...")
    await close_redis()
    await close_llm_clients()
    await engine.dispose()
    logger.info("Shutdown complete")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Production-ready conversational AI platform with memory, vector search, and real-time streaming",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
cors_origins = settings.CORS_ORIGINS.split(",") if settings.CORS_ORIGINS else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error_code": "INTERNAL_ERROR",
            "message": "An internal error occurred",
            "details": None
        }
    )


# Include routers
app.include_router(api_router, prefix="/api/v1")

# WebSocket endpoint
app.add_api_websocket_route(
    "/api/v1/chat/sessions/{session_id}/ws",
    websocket_chat_endpoint
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        redis = await get_redis()
        redis_status = "connected" if await redis.ping() else "disconnected"
    except:
        redis_status = "disconnected"

    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "env": settings.ENV,
        "llm_provider": settings.LLM_PROVIDER,
        "services": {
            "database": "connected",
            "redis": redis_status,
        }
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

    return JSONResponse(
        content=generate_latest().decode("utf-8"),
        media_type=CONTENT_TYPE_LATEST
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )