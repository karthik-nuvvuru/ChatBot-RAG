"""WebSocket error handling and circuit breaker pattern."""
import time
import logging
from typing import Dict, Optional
from datetime import datetime, timezone
from enum import Enum

logger = logging.getLogger("conversation_ai.ws.errors")


class ErrorCode(str, Enum):
    """Standard error codes for WebSocket communications."""
    UNKNOWN_MESSAGE_TYPE = "UNKNOWN_MESSAGE_TYPE"
    SESSION_NOT_FOUND = "SESSION_NOT_FOUND"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    AUTHENTICATION_FAILED = "AUTHENTICATION_FAILED"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    CONNECTION_LOST = "CONNECTION_LOST"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"


class CircuitBreakerState(str, Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"           # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """Circuit breaker for external service calls."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        half_open_max_calls: int = 3
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls

        self._state = CircuitBreakerState.CLOSED
        self._failure_count = 0
        self._last_failure_time: Optional[datetime] = None
        self._half_open_calls = 0

    @property
    def state(self) -> CircuitBreakerState:
        """Get current circuit state."""
        if self._state == CircuitBreakerState.OPEN:
            if self._last_failure_time:
                elapsed = (datetime.now(timezone.utc) - self._last_failure_time).total_seconds()
                if elapsed >= self.recovery_timeout:
                    self._state = CircuitBreakerState.HALF_OPEN
                    self._half_open_calls = 0
        return self._state

    def record_success(self) -> None:
        """Record a successful call."""
        self._failure_count = 0
        self._state = CircuitBreakerState.CLOSED

    def record_failure(self) -> None:
        """Record a failed call."""
        self._failure_count += 1
        self._last_failure_time = datetime.now(timezone.utc)

        if self._failure_count >= self.failure_threshold:
            self._state = CircuitBreakerState.OPEN
            logger.warning(f"Circuit breaker opened after {self._failure_count} failures")

    def can_execute(self) -> bool:
        """Check if a call can be executed."""
        if self._state == CircuitBreakerState.CLOSED:
            return True
        elif self._state == CircuitBreakerState.HALF_OPEN:
            return self._half_open_calls < self.half_open_max_calls
        return False

    def on_half_open_call(self) -> None:
        """Record a call in half-open state."""
        self._half_open_calls += 1


class WebSocketErrorHandler:
    """Handles WebSocket errors with retry guidance and metrics."""

    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self._metrics: Dict[str, int] = {}

    def get_circuit_breaker(self, service: str) -> CircuitBreaker:
        """Get or create circuit breaker for a service."""
        if service not in self.circuit_breakers:
            self.circuit_breakers[service] = CircuitBreaker()
        return self.circuit_breakers[service]

    def get_error_response(
        self,
        error_code: ErrorCode,
        message: str,
        retry_after: Optional[int] = None
    ) -> dict:
        """Create a standardized error response.

        Args:
            error_code: Error code enum
            message: Human-readable error message
            retry_after: Seconds to wait before retry

        Returns:
            Error response dict
        """
        return {
            "type": "error",
            "payload": {
                "code": error_code.value,
                "message": message,
                "retry_after": retry_after,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }

    def get_retry_delay(self, attempt: int) -> int:
        """Calculate exponential backoff delay.

        Args:
            attempt: Retry attempt number (1-based)

        Returns:
            Delay in seconds
        """
        return min(2 ** attempt, 60)

    def record_error(self, error_code: str) -> None:
        """Record an error for metrics."""
        if error_code not in self._metrics:
            self._metrics[error_code] = 0
        self._metrics[error_code] += 1

        logger.error(f"Error recorded: {error_code} (total: {self._metrics[error_code]})")

    def get_metrics(self) -> dict:
        """Get error metrics."""
        return self._metrics.copy()

    def should_retry(self, error_code: ErrorCode) -> bool:
        """Determine if an error is retryable."""
        retryable_codes = [
            ErrorCode.RATE_LIMIT_EXCEEDED,
            ErrorCode.CONNECTION_LOST,
            ErrorCode.SERVICE_UNAVAILABLE,
        ]
        return error_code in retryable_codes

    async def handle_service_error(
        self,
        service: str,
        error: Exception,
        websocket
    ) -> bool:
        """Handle an external service error with circuit breaker.

        Args:
            service: Service name
            error: The exception that occurred
            websocket: WebSocket to send error to

        Returns:
            True if error was handled and connection can continue
        """
        breaker = self.get_circuit_breaker(service)
        breaker.record_failure()

        if not breaker.can_execute():
            response = self.get_error_response(
                ErrorCode.SERVICE_UNAVAILABLE,
                f"Service {service} is temporarily unavailable",
                retry_after=breaker.recovery_timeout
            )
            await websocket.send_json(response)
            return False

        return True


error_handler = WebSocketErrorHandler()