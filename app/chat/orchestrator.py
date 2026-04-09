"""Orchestrator - main chat processing pipeline."""
import uuid
import logging
from typing import AsyncIterator, Optional, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ConversationSession, SessionStatus, MessageRole
from app.schemas import MessageCreate, ChatRequest, ChatResponse
from app.chat.session_manager import SessionManager
from app.chat.message_service import MessageService
from app.chat.memory_service import MemoryService
from app.chat.memory_store import MemoryStore, get_memory_store
from app.chat.embedding_service import get_embedding_service
from app.chat.redis_cache import RedisCache
from app.chat.context_manager import ContextManager, get_context_manager
from app.integrations.llm.base import MessageDict
from app.integrations.llm.factory import get_llm_client

logger = logging.getLogger("conversation_ai.orchestrator")


class ChatOrchestrator:
    """Orchestrates the chat processing pipeline.

    Main responsibilities:
    1. Receive user message
    2. Store message (DB + cache)
    3. Retrieve context (recent messages + relevant memories)
    4. Call LLM via factory
    5. Stream response via WebSocket (if enabled)
    6. Store assistant response
    7. Trigger actions (if needed)
    """

    def __init__(
        self,
        db: AsyncSession,
        cache: RedisCache,
        context_manager: Optional[ContextManager] = None
    ):
        """Initialize orchestrator.

        Args:
            db: Database session
            cache: Redis cache
            context_manager: Optional context manager
        """
        self.db = db
        self.cache = cache
        self.context_manager = context_manager or get_context_manager()

        # Services (initialized lazily)
        self._session_manager: Optional[SessionManager] = None
        self._message_service: Optional[MessageService] = None
        self._memory_service: Optional[MemoryService] = None
        self._memory_store: Optional[MemoryStore] = None

    @property
    async def session_manager(self) -> SessionManager:
        """Get session manager (lazy init)."""
        if self._session_manager is None:
            self._session_manager = SessionManager(self.db, self.cache)
        return self._session_manager

    @property
    async def message_service(self) -> MessageService:
        """Get message service (lazy init)."""
        if self._message_service is None:
            self._message_service = MessageService(self.db, self.cache)
        return self._message_service

    @property
    async def memory_service(self) -> MemoryService:
        """Get memory service (lazy init)."""
        if self._memory_service is None:
            embedding_service = await get_embedding_service()
            memory_store = await get_memory_store(self.db)
            self._memory_service = MemoryService(
                self.db, memory_store, embedding_service, self.cache
            )
        return self._memory_service

    async def process_message(
        self,
        request: ChatRequest,
        stream_callback: Optional[callable] = None
    ) -> ChatResponse:
        """Process a user message and generate response.

        Args:
            request: Chat request with session_id and message
            stream_callback: Optional callback for streaming responses

        Returns:
            ChatResponse with the assistant's message
        """
        session_id = request.session_id

        # 1. Get or validate session
        session = await (await self.session_manager).get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        if not session.is_active():
            raise ValueError(f"Session {session_id} is not active")

        # 2. Store user message
        user_message_data = MessageCreate(
            role=MessageRole.USER,
            content=request.message,
        )
        user_message = await (await self.message_service).add_message(
            session_id, user_message_data
        )

        # 3. Build context
        context_window = self.context_manager.get_or_create_window(str(session_id))

        # Add system prompt
        context_window.add_system_message(
            "You are a helpful, accurate, and concise AI assistant. "
            "Provide detailed responses when appropriate."
        )

        # Add recent messages (last 20)
        recent_messages = await (await self.message_service).get_recent_messages(
            session_id, count=20
        )
        for msg in recent_messages:
            if isinstance(msg, dict):
                context_window.add_message(msg.get("role", "user"), msg.get("content", ""))
            else:
                role = msg.role.value if hasattr(msg.role, 'value') else msg.role
                context_window.add_message(role, msg.content)

        # 4. Retrieve relevant context from memory
        try:
            relevant_context, memories, avg_score = await (
                await self.memory_service
            ).retrieve_relevant_context(session_id, request.message, k=5)

            if relevant_context:
                context_window.add_system_message(
                    f"Relevant context from conversation:\n{relevant_context}"
                )
        except Exception as e:
            logger.warning(f"Failed to retrieve context: {e}")

        # 5. Get LLM client and generate response
        llm_client = get_llm_client()
        messages = context_window.to_llm_format()

        # Convert to MessageDict format
        llm_messages = [MessageDict(m["role"], m["content"]) for m in messages]

        full_content = ""

        try:
            if request.stream and stream_callback:
                # Streaming response
                async for chunk in llm_client.stream(
                    llm_messages,
                    temperature=request.temperature or 0.7,
                    max_tokens=request.max_tokens or 4096
                ):
                    full_content += chunk
                    # Send chunk to callback
                    await stream_callback(chunk)

            else:
                # Non-streaming response
                full_content = await llm_client.generate(
                    llm_messages,
                    temperature=request.temperature or 0.7,
                    max_tokens=request.max_tokens or 4096,
                    stream=False
                )
        except Exception as e:
            logger.error(f"LLM API error: {e}")
            # Fallback response for demo mode when LLM API is unavailable
            full_content = "I'm currently running in demo mode and the AI service is unavailable. Please check the API configuration. Your message has been saved and I'll respond when the service is restored."

        # 6. Store assistant message
        assistant_message_data = MessageCreate(
            role=MessageRole.ASSISTANT,
            content=full_content,
            metadata={"finish_reason": "stop"}
        )
        assistant_message = await (await self.message_service).add_message(
            session_id, assistant_message_data
        )

        # 7. Update session activity
        await (await self.session_manager).update_session_activity(session_id)

        # 8. Store important content in memory (if significant conversation)
        if len(recent_messages) % 10 == 0:  # Every 10 messages
            try:
                await (await self.memory_service).add_message_memory(
                    session_id,
                    assistant_message.message_id,
                    full_content[:500],  # Store first 500 chars
                    importance=0.6
                )
            except Exception as e:
                logger.warning(f"Failed to store memory: {e}")

        return ChatResponse(
            session_id=session_id,
            message_id=assistant_message.message_id,
            content=full_content,
            finish_reason="stop"
        )

    async def process_stream(
        self,
        request: ChatRequest
    ) -> AsyncIterator[str]:
        """Process message and yield streaming chunks.

        Args:
            request: Chat request

        Yields:
            Text chunks as they are generated
        """
        session_id = request.session_id

        # Validate session
        session = await (await self.session_manager).get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        # Store user message
        user_message_data = MessageCreate(
            role=MessageRole.USER,
            content=request.message,
        )
        user_message = await (await self.message_service).add_message(
            session_id, user_message_data
        )

        # Build context
        context_window = self.context_manager.get_or_create_window(str(session_id))
        context_window.add_system_message(
            "You are a helpful AI assistant."
        )

        # Add recent messages
        recent_messages = await (await self.message_service).get_recent_messages(
            session_id, count=20
        )
        for msg in recent_messages:
            if isinstance(msg, dict):
                context_window.add_message(msg.get("role", "user"), msg.get("content", ""))
            else:
                role = msg.role.value if hasattr(msg.role, 'value') else msg.role
                context_window.add_message(role, msg.content)

        # Get LLM client and stream
        llm_client = get_llm_client()
        messages = context_window.to_llm_format()
        llm_messages = [MessageDict(m["role"], m["content"]) for m in messages]

        full_content = ""
        async for chunk in llm_client.stream(
            llm_messages,
            temperature=request.temperature or 0.7,
            max_tokens=request.max_tokens or 4096
        ):
            full_content += chunk
            yield chunk

        # Store assistant message after streaming completes
        if full_content:
            assistant_message_data = MessageCreate(
                role=MessageRole.ASSISTANT,
                content=full_content,
            )
            await (await self.message_service).add_message(session_id, assistant_message_data)
            await (await self.session_manager).update_session_activity(session_id)

    async def handle_websocket_message(
        self,
        session_id: uuid.UUID,
        message: str,
        metadata: Optional[dict] = None
    ) -> Dict[str, Any]:
        """Handle WebSocket message with full processing.

        Args:
            session_id: Session UUID
            message: User message content
            metadata: Optional message metadata

        Returns:
            Response dict with message details
        """
        request = ChatRequest(
            session_id=session_id,
            message=message,
            stream=True
        )

        response = await self.process_message(request)
        return {
            "message_id": str(response.message_id),
            "content": response.content,
            "done": True
        }


async def get_orchestrator(
    db: AsyncSession,
    cache: RedisCache
) -> ChatOrchestrator:
    """Factory to create ChatOrchestrator instance."""
    return ChatOrchestrator(db, cache)