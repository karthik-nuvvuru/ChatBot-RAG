"""SQLAlchemy ORM Models for the Conversation AI Platform."""
import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum
from typing import Optional, List
from sqlalchemy import (
    Column, String, Text, DateTime, ForeignKey, Enum, Index, JSON
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.db.base import Base


class AcceleratorType(str, PyEnum):
    """Enum for accelerator types."""
    BASIC = "basic"
    ADVANCED = "advanced"
    ENTERPRISE = "enterprise"


class SessionStatus(str, PyEnum):
    """Enum for session status."""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class MessageRole(str, PyEnum):
    """Enum for message roles."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ActionStatus(str, PyEnum):
    """Enum for action status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ActionType(str, PyEnum):
    """Enum for action types."""
    CODE_EXECUTION = "code_execution"
    FILE_OPERATION = "file_operation"
    WEB_SEARCH = "web_search"
    API_CALL = "api_call"
    DATA_PROCESSING = "data_processing"


class MemoryType(str, PyEnum):
    """Enum for memory types."""
    SEMANTIC = "semantic"
    EPISODIC = "episodic"
    PROCEDURAL = "procedural"
    WORKING = "working"


class ConversationSession(Base):
    """Conversation session model."""
    __tablename__ = "conversation_sessions"

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    engagement_id: Mapped[Optional[str]] = mapped_column(
        String(255), ForeignKey("engagements.engagement_id", ondelete="CASCADE"), nullable=True
    )
    project_id: Mapped[Optional[str]] = mapped_column(
        String(255), ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=True
    )
    accelerator_type: Mapped[str] = mapped_column(
        String(50), default="basic"
    )
    conversation_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_active_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    status: Mapped[str] = mapped_column(String(50), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    messages: Mapped[List["ConversationMessage"]] = relationship(
        "ConversationMessage", back_populates="session", cascade="all, delete-orphan"
    )
    actions: Mapped[List["ConversationAction"]] = relationship(
        "ConversationAction", back_populates="session", cascade="all, delete-orphan"
    )
    memories: Mapped[List["ConversationMemory"]] = relationship(
        "ConversationMemory", back_populates="session", cascade="all, delete-orphan"
    )

    def is_active(self) -> bool:
        """Check if session is active."""
        return self.status == SessionStatus.ACTIVE

    def __repr__(self) -> str:
        return f"<ConversationSession(id={self.session_id}, user={self.user_id}, status={self.status})>"


class ConversationMessage(Base):
    """Conversation message model."""
    __tablename__ = "conversation_messages"

    message_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversation_sessions.session_id", ondelete="CASCADE"),
        nullable=False
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    message_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)
    parent_message_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversation_messages.message_id", ondelete="SET NULL"),
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    session: Mapped["ConversationSession"] = relationship(
        "ConversationSession", back_populates="messages"
    )
    parent: Mapped[Optional["ConversationMessage"]] = relationship(
        "ConversationMessage", remote_side=[message_id], back_populates="replies"
    )
    replies: Mapped[List["ConversationMessage"]] = relationship(
        "ConversationMessage", back_populates="parent"
    )

    def __repr__(self) -> str:
        return f"<ConversationMessage(id={self.message_id}, role={self.role})>"


class ConversationAction(Base):
    """Conversation action model."""
    __tablename__ = "conversation_actions"

    action_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversation_sessions.session_id", ondelete="CASCADE"),
        nullable=False
    )
    message_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversation_messages.message_id", ondelete="SET NULL"),
        nullable=True
    )
    action_type: Mapped[str] = mapped_column(String(50), nullable=False)
    action_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)
    job_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    logging_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    workflow_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    result: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    session: Mapped["ConversationSession"] = relationship(
        "ConversationSession", back_populates="actions"
    )

    def __repr__(self) -> str:
        return f"<ConversationAction(id={self.action_id}, type={self.action_type}, status={self.status})>"


class ConversationMemory(Base):
    """Conversation memory model with vector embeddings."""
    __tablename__ = "conversation_memory"

    memory_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversation_sessions.session_id", ondelete="CASCADE"),
        nullable=False
    )
    memory_type: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[Optional[List[float]]] = mapped_column(JSON, nullable=True)
    memory_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    session: Mapped["ConversationSession"] = relationship(
        "ConversationSession", back_populates="memories"
    )

    def __repr__(self) -> str:
        return f"<ConversationMemory(id={self.memory_id}, type={self.memory_type})>"


class Engagement(Base):
    """Engagement model for project associations."""
    __tablename__ = "engagements"

    engagement_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    project_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    extra_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)


class Project(Base):
    """Project model."""
    __tablename__ = "projects"

    project_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    extra_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)


# Database indexes
Index("idx_session_user_active", "user_id", "last_active_at", postgresql_where=Column("status = 'active'"))
Index("idx_session_messages_created", "session_id", "created_at")
Index("idx_action_type", "action_type")
Index("idx_message_parent", "parent_message_id")
Index("idx_memory_session", "session_id")