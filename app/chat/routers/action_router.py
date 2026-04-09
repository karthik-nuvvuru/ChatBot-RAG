"""Action API router."""
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.session import get_db
from app.models import ConversationAction, ActionStatus
from app.schemas import ActionResponse, ActionResultResponse, ActionListResponse
from app.api.v1.dependencies import get_current_user

router = APIRouter(prefix="/actions", tags=["actions"])


@router.get("/sessions/{session_id}/actions", response_model=ActionListResponse)
async def list_session_actions(
    session_id: uuid.UUID,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status_filter: Optional[ActionStatus] = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List actions for a session."""
    query = select(ConversationAction).where(
        ConversationAction.session_id == session_id
    )

    if status_filter:
        query = query.where(ConversationAction.status == status_filter)

    query = query.order_by(ConversationAction.created_at.desc())
    query = query.limit(limit).offset(offset)

    result = await db.execute(query)
    actions = result.scalars().all()

    # Get total count
    count_result = await db.execute(
        select(func.count()).select_from(
            select(ConversationAction).where(
                ConversationAction.session_id == session_id
            ).subquery()
        )
    )
    total = count_result.scalar() or 0

    return ActionListResponse(
        actions=[ActionResponse.model_validate(a) for a in actions],
        total=total
    )


@router.get("/actions/{action_id}", response_model=ActionResponse)
async def get_action(
    action_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific action by ID."""
    result = await db.execute(
        select(ConversationAction).where(
            ConversationAction.action_id == action_id
        )
    )
    action = result.scalar_one_or_none()

    if not action:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Action not found"
        )

    return action


@router.get("/actions/{action_id}/result", response_model=ActionResultResponse)
async def get_action_result(
    action_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get the result of an action."""
    result = await db.execute(
        select(ConversationAction).where(
            ConversationAction.action_id == action_id
        )
    )
    action = result.scalar_one_or_none()

    if not action:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Action not found"
        )

    if action.status not in [ActionStatus.COMPLETED, ActionStatus.FAILED]:
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail="Action not yet completed"
        )

    return ActionResultResponse(
        action_id=action.action_id,
        status=action.status.value if hasattr(action.status, 'value') else action.status,
        result=action.result or {},
        completed_at=action.completed_at
    )