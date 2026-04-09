"""API v1 router aggregation."""
from fastapi import APIRouter

from app.chat.routers.session_router import router as session_router
from app.chat.routers.message_router import router as message_router
from app.chat.routers.action_router import router as action_router
from app.api.v1.auth import router as auth_router

api_router = APIRouter()

api_router.include_router(session_router)
api_router.include_router(message_router)
api_router.include_router(action_router)
api_router.include_router(auth_router)