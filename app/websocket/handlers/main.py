from typing import Dict, Any
from fastapi import WebSocket
from redis import Redis
from datetime import datetime
import asyncio

from app.websocket.types import MessageType, WebSocketEvent
from app.websocket.handlers.session import SessionHandler
from app.websocket.handlers.audio import AudioHandler
from app.websocket.handlers.conversation import ConversationHandler
from app.websocket.handlers.response import ResponseHandler
from app.db.database import Database
from app.services.chat_state import ChatStateManager
from app.services.llm import LLMService
from app.services.audio import AudioService
from app.utils.errors import WebSocketError
from app.config import settings

from app.utils.logger import logger


class WebSocketHandler:
    """Main WebSocket handler that orchestrates all sub-handlers"""

    def __init__(self, websocket: WebSocket, db: Database):
        """
        Initialize WebSocket handler with all necessary sub-handlers and services
        📝 File: main.py, Line: 28, Function: __init__
        """
        self.websocket = websocket
        self.db = db
        self.redis = Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )

        # Initialize services
        self.llm_service = LLMService()
        self.audio_service = AudioService()

        # Initialize sub-handlers
        self.session_handler = SessionHandler(websocket, self.redis, self.llm_service,
                                              db)
        self.audio_handler = AudioHandler(self.audio_service, websocket, self.redis, self.llm_service, db)
        self.conversation_handler = ConversationHandler(websocket, self.redis, self.llm_service,
                                                        db)
        self.response_handler = ResponseHandler(
            websocket,
            self.redis,
            self.llm_service,
            db
        )

        # Initialize chat state manager
        self.chat_state = ChatStateManager(self.redis, db)

        logger.info("✨ main.py: WebSocket handler initialized with all services")

    async def handle_message(self, event: WebSocketEvent) -> None:
        """
        Main message handling method with validation and routing
        📝 File: main.py, Line: 61, Function: handle_message
        """
        try:
            # Validate session and rate limits
            await self._validate_session(event.data.get("session_id"))
            await self._check_rate_limits(event.data.get("client_id"))

            # Get appropriate handler
            handler = self.handlers.get(event.type.value)
            if not handler:
                raise WebSocketError(f"Unknown event type: {event.type}", code=4000)

            # Handle the message
            await handler(event)

            logger.info(f"✅ main.py: Successfully handled {event.type.value} event")

        except Exception as e:
            logger.error(f"❌ main.py: Error handling message: {str(e)}")
            raise

    async def cleanup(self) -> None:
        """
        Enhanced cleanup with state persistence
        📝 File: main.py, Line: 138, Function: cleanup
        """
        try:
            # Save final state
            if hasattr(self, 'current_session_id'):
                await self.chat_state.persist_state(self.current_session_id)

            # Cleanup handlers
            cleanup_tasks = [
                self.session_handler.cleanup(),
                self.audio_handler.cleanup(),
                self.conversation_handler.cleanup(),
                self.response_handler.cleanup()
            ]

            # Run cleanup tasks concurrently
            await asyncio.gather(*cleanup_tasks, return_exceptions=True)

            # Close connections
            self.redis.close()
            await self.db.disconnect()

            logger.info("🧹 main.py: All handlers and connections cleaned up successfully")

        except Exception as e:
            logger.error(f"❌ main.py: Cleanup failed: {str(e)}")
            raise

    async def _validate_session(self, session_id: str) -> None:
        """
        Enhanced session validation with caching
        📝 File: main.py, Line: 167, Function: _validate_session
        """
        cache_key = f"session_valid:{session_id}"

        # Check cache first
        is_valid = await self.redis.get(cache_key)
        if is_valid:
            return

        # Validate from database
        session = await self.db.get_session(session_id)
        if not session:
            raise WebSocketError("Session not found", code=4004)
        if session["status"] != "active":
            raise WebSocketError("Session is not active", code=4005)

        # Cache validation result
        await self.redis.setex(cache_key, 300, "1")  # Cache for 5 minutes

    async def _check_rate_limits(self, client_id: str) -> None:
        """
        Enhanced rate limiting with token bucket algorithm
        📝 File: main.py, Line: 188, Function: _check_rate_limits
        """
        rate_limits = await self.db.get_session_rate_limits(client_id)
        current_time = datetime.now().timestamp()

        for limit_type, limit in rate_limits.items():
            if current_time >= limit["reset_seconds"]:
                # Reset limits
                await self.db.reset_rate_limits(client_id, limit_type)
            elif limit["remaining"] <= 0:
                raise WebSocketError(
                    f"Rate limit exceeded for {limit_type}",
                    code=4029,
                    data={"reset_in": limit["reset_seconds"] - current_time}
                )

    @property
    def handlers(self) -> Dict[str, callable]:
        """Handler mapping with type checking"""
        return {
            MessageType.SESSION_UPDATE.value: self.session_handler.handle_session_update,
            MessageType.AUDIO_APPEND.value: self.audio_handler.handle_audio_append,
            MessageType.AUDIO_COMMIT.value: self.audio_handler.handle_audio_commit,
            MessageType.AUDIO_CLEAR.value: self.handle_input_audio_buffer_clear,
            MessageType.CONVERSATION_CREATE.value: self.conversation_handler.handle_conversation_create,
            MessageType.CONVERSATION_TRUNCATE.value: self.handle_conversation_item_truncate,
            MessageType.CONVERSATION_DELETE.value: self.handle_conversation_item_delete,
            MessageType.RESPONSE_CREATE.value: self.response_handler.handle_response_create,
            MessageType.RESPONSE_CANCEL.value: self.response_handler.handle_response_cancel,
        }

    def set_model(self, model):
        self.conversation_handler.set_model(model)
