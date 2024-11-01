from typing import Dict, Optional, Any, List
from fastapi import WebSocket, HTTPException
from redis import Redis
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
from app.websocket.handlers.audio import AudioHandler
from app.websocket.handlers.session import SessionHandler
from app.websocket.handlers.conversation import ConversationHandler
from app.websocket.handlers.response import ResponseHandler
from app.services.audio import AudioService
from app.services.llm import LLMService
from app.db.database import Database
from app.config import settings
from app.utils.logger import logger

class MessageType(Enum):
    """
    Enum for WebSocket message types
    📝 File: handlers.py, Line: 24, Function: MessageType
    """
    SESSION_UPDATE = "session.update"
    AUDIO_APPEND = "input_audio_buffer.append"
    AUDIO_COMMIT = "input_audio_buffer.commit"
    AUDIO_CLEAR = "input_audio_buffer.clear"
    AUDIO_TRANSCRIBED = "audio.transcribed"
    SPEECH_GENERATED = "speech.generated"
    CONVERSATION_CREATE = "conversation.item.create"
    CONVERSATION_TRUNCATE = "conversation.item.truncate"
    CONVERSATION_DELETE = "conversation.item.delete"
    RESPONSE_CREATE = "response.create"
    RESPONSE_CANCEL = "response.cancel"

@dataclass
class WebSocketEvent:
    """
    Data class for WebSocket events
    📝 File: handlers.py, Line: 42, Function: WebSocketEvent
    """
    event_id: str
    type: MessageType
    data: Dict[str, Any]

class WebSocketHandler:
    def __init__(self, websocket: WebSocket, db: Database):
        """
        Initialize WebSocket handler with all necessary sub-handlers and services
        📝 File: handlers.py, Line: 52, Function: __init__
        """
        self.websocket = websocket
        self.db = db
        self.redis = Redis(
            host=settings.REDIS_HOST, 
            port=settings.REDIS_PORT, 
            db=settings.REDIS_DB,
            decode_responses=True
        )
        self._setup_redis_connection()
        
        # Initialize services
        self.llm_service = LLMService()
        self.audio_service = AudioService()
        
        # Initialize sub-handlers
        self.session_handler = SessionHandler(websocket, self.redis, db, self.llm_service)
        self.audio_handler = AudioHandler(websocket, self.redis, db, self.audio_service)
        self.conversation_handler = ConversationHandler(websocket, self.redis, db)
        self.response_handler = ResponseHandler(
            websocket, 
            self.redis, 
            db, 
            self.llm_service,
            self.audio_service
        )
        
        logger.info("✨ handlers.py: WebSocket handler initialized with all sub-handlers")

    def _setup_redis_connection(self) -> None:
        """
        Setup Redis connection with error handling
        📝 File: handlers.py, Line: 85, Function: _setup_redis_connection
        """
        try:
            self.redis.ping()
            logger.info("✅ handlers.py: Redis connection established")
        except Exception as e:
            logger.error(f"❌ handlers.py: Redis connection failed: {str(e)}")
            raise HTTPException(status_code=500, detail="Redis connection failed")

    async def handle_message(self, message: Dict[str, Any]) -> None:
        """
        Route messages to appropriate handlers
        📝 File: handlers.py, Line: 98, Function: handle_message
        """
        message_type = message.get("type")
        
        # Session handling
        if message_type == MessageType.SESSION_UPDATE.value:
            await self.session_handler.handle_session_update(message)
            
        # Audio handling
        elif message_type == MessageType.AUDIO_APPEND.value:
            await self.audio_handler.handle_audio_append(message)
        elif message_type == MessageType.AUDIO_COMMIT.value:
            await self.audio_handler.handle_speech_generate(message)
            
        # Conversation handling
        elif message_type == MessageType.CONVERSATION_CREATE.value:
            await self.conversation_handler.handle_conversation_item_create(message)
        elif message_type == MessageType.CONVERSATION_TRUNCATE.value:
            await self.conversation_handler.handle_conversation_truncate(message)
        elif message_type == MessageType.CONVERSATION_DELETE.value:
            await self.conversation_handler.handle_conversation_delete(message)
            
        # Response handling
        elif message_type == MessageType.RESPONSE_CREATE.value:
            await self.response_handler.handle_response_create(message)
        elif message_type == MessageType.RESPONSE_CANCEL.value:
            await self.response_handler.handle_response_cancel(message)
        
        else:
            logger.error(f"❌ handlers.py: Unknown message type: {message_type}")
            raise HTTPException(status_code=400, detail=f"Unknown message type: {message_type}")

    async def send_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        Helper method to send WebSocket events with logging
        📝 File: handlers.py, Line: 134, Function: send_event
        """
        try:
            await self.websocket.send_json({
                "type": event_type,
                "data": data,
                "timestamp": datetime.utcnow().isoformat()
            })
            logger.info(f"📤 handlers.py: Sent event {event_type}")
        except Exception as e:
            logger.error(f"❌ handlers.py: Failed to send event {event_type}: {str(e)}")
            raise

    async def cleanup(self) -> None:
        """
        Cleanup resources on connection close
        📝 File: handlers.py, Line: 151, Function: cleanup
        """
        try:
            # Cleanup all handlers
            await self.session_handler.cleanup()
            await self.audio_handler.cleanup()
            await self.conversation_handler.cleanup()
            await self.response_handler.cleanup()
            
            # Close Redis connection
            self.redis.close()
            
            logger.info("🧹 handlers.py: Cleanup completed")
            
        except Exception as e:
            logger.error(f"❌ handlers.py: Cleanup failed: {str(e)}")