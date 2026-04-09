"""Session API router."""
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.chat.redis_cache import get_cache, RedisCache
from app.chat.session_manager import SessionManager
from app.schemas import (
    SessionCreate, SessionUpdate, SessionResponse, SessionListResponse,
    SessionForkRequest
)
from app.models import SessionStatus
from app.api.v1.dependencies import get_current_user, rate_limit_dependency

router = APIRouter(prefix="/sessions", tags=["sessions"])


async def get_session_manager(
    db: AsyncSession = Depends(get_db),
    cache: RedisCache = Depends(get_cache)
) -> SessionManager:
    return SessionManager(db, cache)


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    session_data: SessionCreate,
    manager: SessionManager = Depends(get_session_manager),
    _: None = Depends(rate_limit_dependency)
):
    """Create a new conversation session."""
    try:
        session = await manager.create_session(session_data)
        return session
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create session: {str(e)}"
        )


@router.get("", response_model=SessionListResponse)
async def list_sessions(
    user_id: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    manager: SessionManager = Depends(get_session_manager),
    current_user: dict = Depends(get_current_user)
):
    """List sessions with optional filtering."""
    target_user = user_id or current_user.get("sub")

    sessions, total = await manager.get_user_sessions(
        user_id=target_user,
        status_filter=status_filter,
        limit=limit,
        offset=offset
    )

    return SessionListResponse(
        sessions=[SessionResponse.model_validate(s) for s in sessions],
        total=total,
        has_more=(offset + limit) < total
    )


@router.get("/active/count")
async def get_active_count(
    manager: SessionManager = Depends(get_session_manager),
    current_user: dict = Depends(get_current_user)
):
    """Get count of active sessions for current user."""
    count = await manager.get_active_sessions_count(current_user.get("sub"))
    return {"active_sessions": count}


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: uuid.UUID,
    manager: SessionManager = Depends(get_session_manager),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific session by ID."""
    session = await manager.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    # Access control - users can only access their own sessions
    if session.user_id != current_user.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    return session


@router.patch("/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: uuid.UUID,
    update_data: SessionUpdate,
    manager: SessionManager = Depends(get_session_manager),
    current_user: dict = Depends(get_current_user)
):
    """Update session metadata or status."""
    session = await manager.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    if session.user_id != current_user.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    if update_data.status:
        updated = await manager.update_session_status(
            session_id,
            SessionStatus(update_data.status.value)
        )
    elif update_data.conversation_metadata:
        updated = await manager.update_session_metadata(
            session_id,
            update_data.conversation_metadata
        )
    else:
        updated = session

    return updated


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: uuid.UUID,
    manager: SessionManager = Depends(get_session_manager),
    current_user: dict = Depends(get_current_user)
):
    """Archive a session (soft delete)."""
    session = await manager.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    if session.user_id != current_user.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    await manager.archive_session(session_id)


@router.post("/{session_id}/fork", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def fork_session(
    session_id: uuid.UUID,
    fork_request: SessionForkRequest,
    manager: SessionManager = Depends(get_session_manager),
    current_user: dict = Depends(get_current_user)
):
    """Fork an existing session to create a new one."""
    session = await manager.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    if session.user_id != current_user.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    new_session = await manager.fork_session(
        session_id,
        fork_request.new_user_id
    )

    return new_session