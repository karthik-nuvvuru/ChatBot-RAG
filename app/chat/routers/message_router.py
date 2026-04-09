"""Message API router."""
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.chat.redis_cache import get_cache, RedisCache
from app.chat.message_service import MessageService
from app.chat.orchestrator import ChatOrchestrator
from app.schemas import (
    MessageCreate, MessageResponse, MessageListResponse,
    MessageThreadResponse, ChatRequest, ChatResponse
)
from app.api.v1.dependencies import get_current_user, rate_limit_dependency

router = APIRouter(tags=["messages"])


async def get_message_service(
    db: AsyncSession = Depends(get_db),
    cache: RedisCache = Depends(get_cache)
) -> MessageService:
    return MessageService(db, cache)


async def get_orchestrator(
    db: AsyncSession = Depends(get_db),
    cache: RedisCache = Depends(get_cache)
) -> ChatOrchestrator:
    return ChatOrchestrator(db, cache)


@router.post(
    "/sessions/{session_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED
)
async def add_message(
    session_id: uuid.UUID,
    message_data: MessageCreate,
    service: MessageService = Depends(get_message_service),
    _: None = Depends(rate_limit_dependency)
):
    """Add a new message to a session."""
    try:
        message = await service.add_message(session_id, message_data)
        return message
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add message"
        )


@router.get("/sessions/{session_id}/messages", response_model=MessageListResponse)
async def get_session_messages(
    session_id: uuid.UUID,
    limit: int = Query(20, ge=1, le=100),
    cursor: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    service: MessageService = Depends(get_message_service),
    _: dict = Depends(get_current_user)
):
    """Get messages for a session with cursor pagination."""
    messages, next_cursor, total = await service.get_session_messages(
        session_id=session_id,
        limit=limit,
        cursor=cursor,
        role_filter=role
    )

    return MessageListResponse(
        messages=[MessageResponse.model_validate(m) for m in messages],
        total=total,
        has_more=next_cursor is not None,
        next_cursor=next_cursor
    )


@router.get("/messages/{message_id}", response_model=MessageResponse)
async def get_message(
    message_id: uuid.UUID,
    service: MessageService = Depends(get_message_service),
    _: dict = Depends(get_current_user)
):
    """Get a specific message by ID."""
    # This is a simplified implementation
    # In production, add proper session access validation
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Direct message lookup not yet implemented"
    )


@router.get("/messages/{message_id}/thread", response_model=MessageThreadResponse)
async def get_message_thread(
    message_id: uuid.UUID,
    service: MessageService = Depends(get_message_service),
    _: dict = Depends(get_current_user)
):
    """Get a message and its thread of replies."""
    try:
        message, replies = await service.get_message_thread(message_id)
        return MessageThreadResponse(
            message=MessageResponse.model_validate(message),
            thread=[MessageResponse.model_validate(r) for r in replies]
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/sessions/{session_id}/messages/search")
async def search_messages(
    session_id: uuid.UUID,
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
    service: MessageService = Depends(get_message_service),
    _: dict = Depends(get_current_user)
):
    """Search messages within a session."""
    messages = await service.search_messages(session_id, q, limit)
    return {
        "messages": [MessageResponse.model_validate(m) for m in messages],
        "query": q,
        "count": len(messages)
    }


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    orchestrator: ChatOrchestrator = Depends(get_orchestrator),
    _: None = Depends(rate_limit_dependency)
):
    """Send a message and get AI response (non-streaming)."""
    try:
        response = await orchestrator.process_message(request, stream_callback=None)
        return response
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process message: {str(e)}"
        )


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Send a message and stream AI response.

    This endpoint returns an async generator for streaming responses.
    """
    from fastapi.responses import StreamingResponse
    from app.db.session import get_db
    from app.chat.redis_cache import get_cache

    async def generate():
        async with await get_db() as db:
            cache = await get_cache()
            orchestrator = ChatOrchestrator(db, cache)

            async for chunk in orchestrator.process_stream(request):
                yield f"data: {chunk}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )