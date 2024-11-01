import asyncio
from typing import Dict, Optional, Any
from fastapi.websockets import WebSocket, WebSocketDisconnect
from app.websocket.handlers import WebSocketHandler, MessageType, WebSocketEvent
from app.services.chat_state import ChatStateManager
from app.db.database import Database
from app.utils.errors import WebSocketError, handle_websocket_error
from app.config import settings
from datetime import datetime
import json
import uuid
from app.utils.logger import logger


class WebSocketConnection:
    """
    WebSocket connection manager with enhanced error handling, state management,
    and real-time audio/text processing capabilities
    """
    def __init__(self, websocket: WebSocket, db: Database):
        """
        Initialize WebSocket connection with necessary services
        📝 File: connection.py, Line: 22, Function: __init__
        """
        self.websocket = websocket
        self.db = db
        self.client_id = str(uuid.uuid4())
        self.handler = WebSocketHandler(websocket, db)
        self.chat_state = ChatStateManager(self.handler.redis, db)
        self.heartbeat_task: Optional[asyncio.Task] = None
        self.is_connected = False
        self.current_session_id: Optional[str] = None

    async def handle_connection(self) -> None:
        """
        Handle WebSocket connection lifecycle with heartbeat and state management
        📝 File: connection.py, Line: 35, Function: handle_connection
        """
        try:
            await self.websocket.accept()
            self.is_connected = True
            
            # Initialize session with retry logic
            retry_count = 3
            for attempt in range(retry_count):
                try:
                    self.current_session_id = await self._initialize_session()
                    break
                except Exception as e:
                    if attempt == retry_count - 1:
                        raise
                    await asyncio.sleep(1)
            
            logger.info(
                f"🔌 connection.py: New WebSocket connection established - "
                f"Client ID: {self.client_id}, Session: {self.current_session_id}"
            )
            
            # Start heartbeat
            self.heartbeat_task = asyncio.create_task(self._heartbeat())
            
            # Send connection confirmation
            await self._send_connection_confirmed(self.current_session_id)

            while self.is_connected:
                try:
                    message = await self._receive_message()
                    if message:
                        await self.handle_message(message)
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    logger.error(f"❌ connection.py: Message processing error: {str(e)}")
                    await self._send_error(str(e))

        except WebSocketDisconnect:
            logger.info(f"🔌 connection.py: Client {self.client_id} disconnected")
        except Exception as e:
            logger.error(f"❌ connection.py: Connection error: {str(e)}")
        finally:
            await self._cleanup()

    async def handle_message(self, message: Dict[str, Any]) -> None:
        """
        Route messages to appropriate handlers with rate limiting and validation
        📝 File: connection.py, Line: 71, Function: handle_message
        """
        try:
            # Validate message structure and session
            self._validate_message(message)
            if not self.current_session_id:
                raise WebSocketError("No active session", code=4003)
            
            message_type = message["type"]
            logger.info(f"📨 connection.py: Handling message type: {message_type}")

            # Check rate limits
            await self._check_rate_limits()

            # Enrich message with session data
            enriched_message = await self._enrich_message(message)

            # Create WebSocketEvent instance
            event = WebSocketEvent(
                event_id=enriched_message.get("event_id", str(uuid.uuid4())),
                type=MessageType(message_type),
                data=enriched_message
            )

            # Handle the message through main handler
            await self.handler.handle_message(event)

        except WebSocketError as e:
            await self._send_error(e.message, e.code)
        except Exception as e:
            logger.error(f"❌ connection.py: Message handling error: {str(e)}")
            await self._send_error("Internal server error", 500)

    async def _initialize_session(self) -> str:
        """
        Initialize session in database and cache with enhanced configuration
        📝 File: connection.py, Line: 124, Function: _initialize_session
        """
        session_id = str(uuid.uuid4())
        session_data = {
            "id": session_id,
            "client_id": self.client_id,
            "status": "active",
            "model": settings.GPT_MODEL,
            "modalities": ["text"],
            "voice": None,
            "temperature": 0.7,
            "created_at": datetime.utcnow(),
            "metadata": {
                "user_agent": str(self.websocket.headers.get("user-agent")),
                "ip": str(self.websocket.client.host)
            }
        }

        # Add audio modality if enabled
        if settings.TTS_ENGINE:
            session_data["modalities"].append("audio")
            session_data["voice"] = settings.TTS_MODEL

        await self.db.create_session(session_data)
        return session_id

    async def _receive_message(self) -> Optional[Dict[str, Any]]:
        """
        Receive and parse WebSocket message with timeout and validation
        📝 File: connection.py, Line: 140, Function: _receive_message
        """
        try:
            message = await asyncio.wait_for(
                self.websocket.receive_json(),
                timeout=settings.WS_HEARTBEAT_INTERVAL
            )
            
            # Basic JSON schema validation
            if not isinstance(message, dict):
                raise WebSocketError("Invalid message format", code=4000)
                
            return message
        except json.JSONDecodeError as e:
            logger.error(f"❌ connection.py: Invalid JSON received: {str(e)}")
            await self._send_error("Invalid JSON format")
            return None
        except asyncio.TimeoutError:
            return None
        except Exception as e:
            logger.error(f"❌ connection.py: Message receive error: {str(e)}")
            return None

    async def _heartbeat(self) -> None:
        """
        Send periodic heartbeat with enhanced monitoring
        📝 File: connection.py, Line: 157, Function: _heartbeat
        """
        while self.is_connected:
            try:
                current_time = datetime.utcnow()
                await self.websocket.send_json({
                    "type": "heartbeat",
                    "timestamp": current_time.isoformat(),
                    "session_id": self.current_session_id
                })
                
                # Update last activity timestamp
                if self.current_session_id:
                    await self.db.update_session_activity(
                        self.current_session_id,
                        current_time
                    )
                    
                await asyncio.sleep(settings.WS_HEARTBEAT_INTERVAL)
            except Exception as e:
                logger.error(f"❌ connection.py: Heartbeat error: {str(e)}")
                break

    async def _check_rate_limits(self) -> None:
        """
        Check and update rate limits
        📝 File: connection.py, Line: 172, Function: _check_rate_limits
        """
        rate_limits = await self.db.get_rate_limits(self.client_id)
        if rate_limits["requests"]["remaining"] <= 0:
            raise WebSocketError("Rate limit exceeded", code=4029)
        await self.db.update_rate_limits(self.client_id, self.current_session_id)

    def _validate_message(self, message: Dict[str, Any]) -> None:
        """
        Validate message structure
        📝 File: connection.py, Line: 182, Function: _validate_message
        """
        if not isinstance(message, dict):
            raise WebSocketError("Invalid message format", code=4000)
        if "type" not in message:
            raise WebSocketError("Message type is required", code=4001)

    async def _enrich_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich message with session and state data
        📝 File: connection.py, Line: 192, Function: _enrich_message
        """
        state = await self.chat_state.get_chat_state(self.current_session_id)
        return {
            **message,
            "session_id": self.current_session_id,
            "client_id": self.client_id,
            "state": state
        }

    async def _send_connection_confirmed(self, session_id: str) -> None:
        """
        Send connection confirmation with session details
        📝 File: connection.py, Line: 205, Function: _send_connection_confirmed
        """
        await self.websocket.send_json({
            "type": "connected",
            "data": {
                "client_id": self.client_id,
                "session_id": session_id,
                "timestamp": datetime.now(datetime.UTC).isoformat(),
                "config": {
                    "heartbeat_interval": settings.WS_HEARTBEAT_INTERVAL,
                    "rate_limits": {
                        "requests": settings.RATE_LIMIT_REQUESTS,
                        "tokens": settings.RATE_LIMIT_TOKENS
                    }
                }
            }
        })

    async def _send_error(self, message: str, code: int = 400) -> None:
        """
        Send error message to client
        📝 File: connection.py, Line: 227, Function: _send_error
        """
        try:
            error_response = handle_websocket_error(WebSocketError(message, code))
            await self.websocket.send_json(error_response)
        except Exception as e:
            logger.error(f"❌ connection.py: Failed to send error message: {str(e)}")

    async def _cleanup(self) -> None:
        """
        Clean up resources on connection close
        📝 File: connection.py, Line: 238, Function: _cleanup
        """
        try:
            self.is_connected = False
            if self.heartbeat_task:
                self.heartbeat_task.cancel()
            await self.handler.cleanup()
            logger.info(f"🧹 connection.py: Cleanup completed for client {self.client_id}")
        except Exception as e:
            logger.error(f"❌ connection.py: Cleanup failed: {str(e)}")