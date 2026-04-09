"""Pydantic schemas for message operations."""
from datetime import datetime
from typing import Optional, List, Any, Dict
from uuid import UUID
from pydantic import BaseModel, Field


class MessageCreate(BaseModel):
    """Schema for creating a message."""
    content: str = Field(..., min_length=1, max_length=100000)
    role: str = Field(default="user")
    parent_message_id: Optional[UUID] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class MessageUpdate(BaseModel):
    """Schema for updating a message."""
    content: Optional[str] = Field(None, min_length=1, max_length=100000)
    metadata: Optional[Dict[str, Any]] = None


class MessageResponse(BaseModel):
    """Schema for message response."""
    message_id: UUID
    session_id: UUID
    role: str
    content: str
    message_metadata: Dict[str, Any] = Field(default_factory=dict)
    parent_message_id: Optional[UUID] = None
    created_at: datetime

    class Config:
        from_attributes = True


class MessageListResponse(BaseModel):
    """Schema for paginated message list."""
    messages: List[MessageResponse]
    total: int
    has_more: bool


class MessageThreadResponse(BaseModel):
    """Schema for message thread response."""
    thread: List[MessageResponse]


class SearchMessagesRequest(BaseModel):
    """Schema for message search request."""
    query: str = Field(..., min_length=1)
    role: Optional[str] = Field(None)
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    limit: int = Field(default=50, ge=1, le=100)


class SearchMessagesResponse(BaseModel):
    """Schema for message search response."""
    messages: List[MessageResponse]
    total: int
    query: str
