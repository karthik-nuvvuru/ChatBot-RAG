"""Custom exceptions for the chat module."""


class ChatBaseException(Exception):
    """Base exception for chat module."""

    def __init__(self, message: str, code: str = "CHAT_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class SessionNotFoundError(ChatBaseException):
    """Raised when session doesn't exist."""

    def __init__(self, session_id: str):
        super().__init__(
            message=f"Session '{session_id}' not found",
            code="SESSION_NOT_FOUND"
        )
        self.session_id = session_id


class SessionAccessDeniedError(ChatBaseException):
    """Raised when user doesn't have access to session."""

    def __init__(self, session_id: str, user_id: str):
        super().__init__(
            message=f"User '{user_id}' does not have access to session '{session_id}'",
            code="SESSION_ACCESS_DENIED"
        )
        self.session_id = session_id
        self.user_id = user_id


class SessionLimitExceededError(ChatBaseException):
    """Raised when user exceeds max active sessions."""

    def __init__(self, user_id: str, limit: int):
        super().__init__(
            message=f"User '{user_id}' has reached maximum active sessions ({limit})",
            code="SESSION_LIMIT_EXCEEDED"
        )
        self.user_id = user_id
        self.limit = limit


class MessageNotFoundError(ChatBaseException):
    """Raised when message doesn't exist."""

    def __init__(self, message_id: str):
        super().__init__(
            message=f"Message '{message_id}' not found",
            code="MESSAGE_NOT_FOUND"
        )
        self.message_id = message_id


class ActionNotFoundError(ChatBaseException):
    """Raised when action doesn't exist."""

    def __init__(self, action_id: str):
        super().__init__(
            message=f"Action '{action_id}' not found",
            code="ACTION_NOT_FOUND"
        )
        self.action_id = action_id


class InvalidStatusTransitionError(ChatBaseException):
    """Raised when attempting an invalid status transition."""

    def __init__(self, current_status: str, target_status: str):
        super().__init__(
            message=f"Cannot transition from '{current_status}' to '{target_status}'",
            code="INVALID_STATUS_TRANSITION"
        )
        self.current_status = current_status
        self.target_status = target_status


class CacheError(ChatBaseException):
    """Raised when cache operation fails."""

    def __init__(self, operation: str, details: str = ""):
        super().__init__(
            message=f"Cache operation '{operation}' failed: {details}",
            code="CACHE_ERROR"
        )
        self.operation = operation


class EmbeddingError(ChatBaseException):
    """Raised when embedding generation fails."""

    def __init__(self, message: str = "Embedding generation failed"):
        super().__init__(
            message=message,
            code="EMBEDDING_ERROR"
        )


class VectorStoreError(ChatBaseException):
    """Raised when vector store operation fails."""

    def __init__(self, operation: str, details: str = ""):
        super().__init__(
            message=f"Vector store operation '{operation}' failed: {details}",
            code="VECTOR_STORE_ERROR"
        )
        self.operation = operation


class AttachmentError(ChatBaseException):
    """Raised when attachment operation fails."""

    def __init__(self, operation: str, details: str = ""):
        super().__init__(
            message=f"Attachment operation '{operation}' failed: {details}",
            code="ATTACHMENT_ERROR"
        )
        self.operation = operation


class RateLimitExceededError(ChatBaseException):
    """Raised when rate limit is exceeded."""

    def __init__(self, limit_type: str, retry_after: int = 60):
        super().__init__(
            message=f"Rate limit exceeded for '{limit_type}'",
            code="RATE_LIMIT_EXCEEDED"
        )
        self.limit_type = limit_type
        self.retry_after = retry_after
