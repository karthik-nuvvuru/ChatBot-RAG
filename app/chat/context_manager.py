"""Context manager for conversation context window management."""
import logging
from typing import List, Dict, Optional
from datetime import datetime, timezone

from app.core.config import settings

logger = logging.getLogger("conversation_ai.context")


class ContextWindow:
    """Manages conversation context window with token budget."""

    def __init__(
        self,
        max_tokens: int = 128000,
        system_prompt: str = "You are a helpful AI assistant."
    ):
        """Initialize context window.

        Args:
            max_tokens: Maximum token budget (default 128k for modern models)
            system_prompt: System prompt to prepend
        """
        self.max_tokens = max_tokens
        self.system_prompt = system_prompt
        self.messages: List[Dict] = []

    def add_message(self, role: str, content: str, metadata: Optional[dict] = None) -> None:
        """Add a message to the context.

        Args:
            role: Message role (system, user, assistant)
            content: Message content
            metadata: Optional metadata
        """
        self.messages.append({
            "role": role,
            "content": content,
            "metadata": metadata or {},
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    def add_user_message(self, content: str) -> None:
        """Add a user message."""
        self.add_message("user", content)

    def add_assistant_message(self, content: str) -> None:
        """Add an assistant message."""
        self.add_message("assistant", content)

    def add_system_message(self, content: str) -> None:
        """Add a system message."""
        self.add_message("system", content)

    def get_messages(self) -> List[Dict]:
        """Get all messages."""
        return self.messages.copy()

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text.

        Rough estimate: ~4 characters per token for English.
        """
        return len(text) // 4

    def get_context_size(self) -> int:
        """Get current estimated token count."""
        total = self.estimate_tokens(self.system_prompt)
        for msg in self.messages:
            total += self.estimate_tokens(msg["content"])
            total += 4  # Overhead per message
        return total

    def fits_in_context(self, additional_tokens: int = 0) -> bool:
        """Check if content fits within context window.

        Args:
            additional_tokens: Additional tokens to add

        Returns:
            True if fits
        """
        return self.get_context_size() + additional_tokens <= self.max_tokens

    def truncate_to_fit(self, priority: str = "recent") -> List[Dict]:
        """Truncate messages to fit within context window.

        Args:
            priority: 'recent' to keep newest, 'oldest' to keep oldest

        Returns:
            Truncated message list
        """
        while not self.fits_in_context() and self.messages:
            if priority == "recent":
                self.messages.pop(0)  # Remove oldest
            else:
                self.messages.pop()  # Remove newest

        return self.messages

    def build_prompt(self) -> str:
        """Build a flat prompt string from messages.

        Returns:
            Formatted prompt string
        """
        parts = [f"System: {self.system_prompt}"]
        for msg in self.messages:
            role = msg["role"].upper()
            parts.append(f"{role}: {msg['content']}")
        return "\n\n".join(parts)

    def to_llm_format(self) -> List[Dict]:
        """Convert to LLM message format.

        Returns:
            List of message dicts for LLM
        """
        result = [{"role": "system", "content": self.system_prompt}]
        result.extend([
            {"role": msg["role"], "content": msg["content"]}
            for msg in self.messages
        ])
        return result

    def clear(self) -> None:
        """Clear all messages."""
        self.messages.clear()


class ContextManager:
    """Manages context windows for multiple sessions."""

    def __init__(self):
        self.windows: Dict[str, ContextWindow] = {}

    def get_or_create_window(
        self,
        session_id: str,
        max_tokens: int = 128000,
        system_prompt: Optional[str] = None
    ) -> ContextWindow:
        """Get or create a context window for a session.

        Args:
            session_id: Session UUID
            max_tokens: Max tokens for this window
            system_prompt: Optional system prompt

        Returns:
            ContextWindow instance
        """
        if session_id not in self.windows:
            prompt = system_prompt or (
                "You are a helpful AI assistant. "
                "Provide accurate, detailed responses."
            )
            self.windows[session_id] = ContextWindow(max_tokens, prompt)

        return self.windows[session_id]

    def get_window(self, session_id: str) -> Optional[ContextWindow]:
        """Get existing window or None.

        Args:
            session_id: Session UUID

        Returns:
            ContextWindow or None
        """
        return self.windows.get(session_id)

    def remove_window(self, session_id: str) -> bool:
        """Remove a context window.

        Args:
            session_id: Session UUID

        Returns:
            True if removed
        """
        if session_id in self.windows:
            del self.windows[session_id]
            return True
        return False

    def clear_all(self) -> None:
        """Clear all context windows."""
        self.windows.clear()

    def get_stats(self) -> dict:
        """Get statistics about context windows."""
        return {
            "active_windows": len(self.windows),
            "window_details": {
                sid: {
                    "messages": len(w.messages),
                    "tokens": w.get_context_size()
                }
                for sid, w in self.windows.items()
            }
        }


# Global context manager
context_manager = ContextManager()


def get_context_manager() -> ContextManager:
    """Get the global context manager."""
    return context_manager