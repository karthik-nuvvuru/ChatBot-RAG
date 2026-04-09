"""Pydantic schemas for API request/response validation."""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Any, Dict
from datetime import datetime
from uuid import UUID
from enum import Enum


class AcceleratorTypeEnum(str, Enum):
    BASIC = "basic"
    ADVANCED = "advanced"
    ENTERPRISE = "enterprise"


class SessionStatusEnum(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class MessageRoleEnum(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ActionStatusEnum(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ActionTypeEnum(str, Enum):
    CODE_EXECUTION = "code_execution"
    FILE_OPERATION = "file_operation"
    WEB_SEARCH = "web_search"
    API_CALL = "api_call"
    DATA_PROCESSING = "data_processing"


class MemoryTypeEnum(str, Enum):
    SEMANTIC = "semantic"
    EPISODIC = "episodic"
    PROCEDURAL = "procedural"
    WORKING = "working"


# Session Schemas
class SessionCreate(BaseModel):
    user_id: str
    engagement_id: Optional[str] = None
    project_id: Optional[str] = None
    accelerator_type: AcceleratorTypeEnum = AcceleratorTypeEnum.BASIC
    conversation_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class SessionUpdate(BaseModel):
    status: Optional[SessionStatusEnum] = None
    conversation_metadata: Optional[Dict[str, Any]] = None


class SessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    session_id: UUID
    user_id: str
    engagement_id: Optional[str] = None
    project_id: Optional[str] = None
    accelerator_type: str
    conversation_metadata: Dict[str, Any]
    started_at: datetime
    last_active_at: datetime
    status: str
    created_at: datetime
    updated_at: datetime


class SessionListResponse(BaseModel):
    sessions: List[SessionResponse]
    total: int
    has_more: bool


class SessionForkRequest(BaseModel):
    new_user_id: Optional[str] = None


# Message Schemas
class MessageCreate(BaseModel):
    role: MessageRoleEnum
    content: str = Field(..., min_length=1, max_length=10000)
    message_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    parent_message_id: Optional[UUID] = None


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    message_id: UUID
    session_id: UUID
    role: str
    content: str
    message_metadata: Dict[str, Any]
    parent_message_id: Optional[UUID] = None
    created_at: datetime


class MessageListResponse(BaseModel):
    messages: List[MessageResponse]
    total: int
    has_more: bool
    next_cursor: Optional[str] = None


class MessageThreadResponse(BaseModel):
    message: MessageResponse
    thread: List[MessageResponse]


# Action Schemas
class ActionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    action_id: UUID
    session_id: UUID
    message_id: Optional[UUID] = None
    action_type: str
    action_metadata: Dict[str, Any]
    job_id: Optional[str] = None
    logging_id: Optional[str] = None
    workflow_id: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: str
    result: Dict[str, Any]
    created_at: datetime


class ActionResultResponse(BaseModel):
    action_id: UUID
    status: str
    result: Dict[str, Any]
    completed_at: Optional[datetime] = None


class ActionListResponse(BaseModel):
    actions: List[ActionResponse]
    total: int


# Attachment Schemas
class AttachmentUploadResponse(BaseModel):
    attachment_id: UUID
    filename: str
    content_type: str
    size: int
    storage_path: str
    created_at: datetime


class AttachmentResponse(BaseModel):
    attachment_id: UUID
    filename: str
    content_type: str
    size: int
    storage_path: str
    metadata: Dict[str, Any]
    created_at: datetime


# Memory Schemas
class MemoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    memory_id: UUID
    session_id: UUID
    memory_type: str
    content: str
    memory_metadata: Dict[str, Any]
    created_at: datetime


class MemorySearchResponse(BaseModel):
    memories: List[MemoryResponse]
    similarities: List[float]


# WebSocket Schemas
class WSMessage(BaseModel):
    type: str
    payload: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class WSUserMessage(BaseModel):
    type: str = "user_message"
    content: str
    metadata: Optional[Dict[str, Any]] = None


class WSAssistantMessage(BaseModel):
    type: str = "assistant_message"
    content: str
    metadata: Optional[Dict[str, Any]] = None
    message_id: Optional[UUID] = None


class WSProgressUpdate(BaseModel):
    type: str = "progress_update"
    progress: float
    status: str
    message: Optional[str] = None


class WSTypingIndicator(BaseModel):
    type: str = "typing_indicator"
    is_typing: bool


class WSError(BaseModel):
    type: str = "error"
    code: str
    message: str
    retry_after: Optional[int] = None


# Error Schema
class ErrorResponse(BaseModel):
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    retry_after: Optional[int] = None


class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: datetime
    services: Dict[str, str]


# LLM Chat Schemas
class ChatRequest(BaseModel):
    session_id: UUID
    message: str = Field(..., min_length=1, max_length=10000)
    stream: bool = True
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=4096, ge=1, le=32768)


class ChatResponse(BaseModel):
    session_id: UUID
    message_id: UUID
    content: str
    finish_reason: str
    usage: Optional[Dict[str, int]] = None


class ChatStreamResponse(BaseModel):
    session_id: UUID
    message_id: UUID
    content: str
    done: bool = False